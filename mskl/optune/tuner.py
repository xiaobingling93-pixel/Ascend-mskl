#!/usr/bin/python
# -*- coding: UTF-8 -*-
# -------------------------------------------------------------------------
# This file is part of the MindStudio project.
# Copyright (c) 2025 Huawei Technologies Co.,Ltd.
#
# MindStudio is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#
#          http://license.coscl.org.cn/MulanPSL2
#
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
# -------------------------------------------------------------------------

from copy import deepcopy
from math import ceil
from multiprocessing import Manager, Pool
import os
from pathlib import Path
import threading
import shutil
import csv
from typing import List, Dict
from datetime import datetime, timezone, timedelta

from mskl.launcher.compiler import compile, CompiledKernel, compile_executable, CompiledExecutable
from mskl.launcher.config import KernelInvokeConfig
from mskl.launcher.code_generator import Launcher

from mskl.launcher.context import context as launch_context
from mskl.launcher.driver import driver
from mskl.optune.kernel_modifier import Replacer
from mskl.optune.kernel_prof import Monitor
from mskl.utils import logger, autotune_utils, safe_check

from ..utils.safe_check import FileChecker

origin_context = None


class Autotuner:

    def __init__(self):
        self.context = None
        self.kernel_file = ''
        self.replacer = None

    @staticmethod
    def pre_launch(user_func, device_id, *args, **kwargs):
        # pre launch
        launch_context.reset()
        logger.debug('Launch_context = {}'.format(launch_context))
        try:
            driver.set_device(device_id)
            logger.debug('Starting kernel pre-launch...')
            user_func(*args, **kwargs)
            logger.debug('Kernel pre-launch completed...')
            global origin_context
            origin_context = deepcopy(launch_context)
        except Exception as exp:
            raise Exception(f'pre-launch operator failed! Error: {exp}.')

    @staticmethod
    def launch(kernel: CompiledKernel, context, device_id, warmup, repeat):
        kernel_monitor = Monitor()
        kernel_monitor.start(device_id)
        # get single launch time
        kernel[context.blockdim](*context.kernel_args, device_id=device_id)
        kernel_monitor.stop(device_id)
        one_time_duration = kernel_monitor.get_task_duration()
        if one_time_duration <= 0:
            raise ValueError(f'The running time of this operator is less than or equal to 0. The device {device_id} '
                             f'might be occupied by another process. Please use the command `npu-smi info` to '
                             f'check the device status.')

        kernel_monitor.start(device_id)
        if one_time_duration < warmup * 10 ** 3:
            warmup_times = ceil(warmup * 10 ** 3 / one_time_duration)
            # warm up
            kernel[context.blockdim](*context.kernel_args, device_id=device_id, repeat=warmup_times)

        # repeat
        kernel[context.blockdim](*context.kernel_args, device_id=device_id, repeat=repeat)
        kernel_monitor.stop(device_id)
        task_duration = kernel_monitor.get_last_n_task_duration(repeat)
        logger.debug("Task_duration = {}, repeat = {}".format(task_duration, repeat))

        return task_duration / repeat

    @staticmethod
    def clean_files(context):
        if logger.log_level == '0':
            return
        autotun_files = [context.kernel_src_file, context.launch_src_file,
                         Path(context.launch_src_file).with_suffix('.so'),
                         Path(context.launch_src_file).with_suffix('.o')]
        for file in autotun_files:
            if os.path.isfile(file):
                os.remove(file)

    @staticmethod
    def _modify_file_path_with_index(file, index):
        path = Path(file)
        prefix = '' if path.stem.startswith('_gen_') else "_gen_"
        new_name = f'{prefix}{path.stem}_{index}{path.suffix}'
        return os.path.join(os.path.dirname(file), new_name)

    def gen_context(self, index, config):
        # modify kernel src file
        self.context.kernel_src_file = self._modify_file_path_with_index(self.context.kernel_src_file, index)
        self.replacer.replace_config(config, self.context.kernel_src_file)

        # modify code gen file path
        self.context.launch_src_file = self._modify_file_path_with_index(self.context.launch_src_file, index)

    def code_gen(self):
        config = KernelInvokeConfig(self.context.kernel_src_file, self.context.kernel_name)
        launcher = Launcher(config)
        launcher.code_gen(gen_file=self.context.launch_src_file)

    def compile_op(self, index):
        output_so_path = str(Path(self.context.launch_src_file).with_suffix('.so'))
        return compile(self.context.build_script, self.context.launch_src_file, output_so_path)


class Executor:
    def __init__(self, configs, device_ids, warmup, repeat, compile_process_num=None):
        self._compile_processes = compile_process_num or self._get_process_num()
        multiprocessing_manager = Manager()
        self.task_queue = multiprocessing_manager.Queue()
        self.logging_queue = multiprocessing_manager.Queue()
        self._warmup = warmup
        self._repeat = repeat
        self._best_config = None
        self._best_index = None
        self._best_execution_time = 0
        self._auto_tuner = Autotuner()
        self._configs = configs
        self._device_id = device_ids[0]

    @staticmethod
    def _get_process_num():
        max_process_num = 32
        try:
            if hasattr(os, 'sched_getaffinity'):
                cpu_count = len(os.sched_getaffinity(0))  # adapt to containerized environments
            else:
                cpu_count = os.cpu_count()
        except Exception as exp:
            logger.warning(f'Failed to detect CPU cores: {exp}. Fallback to default 32.')
            return max_process_num
        return max(min(int(cpu_count / 2), max_process_num), 1)

    def execute(self):
        compile_pool = Pool(min(self._compile_processes, len(self._configs)))

        # start logger monitor
        log_thread = threading.Thread(target=self._log_listener)
        log_thread.start()

        # start compile task and launch task
        compile_tasks = [compile_pool.apply_async(self._compile_task, (index,)) for index in range(len(self._configs))]
        launch_thread = threading.Thread(target=self._launch_task)
        launch_thread.start()

        # wait for compile task finish
        for compile_task in compile_tasks:
            compile_task.get()
        compile_pool.close()
        compile_pool.join()

        self.task_queue.put((None, None, None))

        launch_thread.join()

        self.logging_queue.put((None, None))
        log_thread.join()
        if self._best_index is not None:
            logger.info(f'Best config: No.{self._best_index}')
        logger.debug('Kernel autotune end...')

    def _compile_task(self, index):
        launch_context.autotune_in_progress = True
        self._auto_tuner.context = deepcopy(origin_context)
        self._auto_tuner.replacer = Replacer(origin_context.kernel_src_file)
        config = self._configs[index]
        try:
            self._auto_tuner.gen_context(index, config)
            logger.debug(f'Start to compile op for the {index}th config:{config}.')
            self._auto_tuner.code_gen()
            kernel = self._auto_tuner.compile_op(index)

            # ctypes.sharedctypes.RawArray object should only be shared between processes through inheritance
            # args MUST be set to None before being put into queue
            self._auto_tuner.context.kernel_args = None
            self._auto_tuner.context.decl_args = None
            self._auto_tuner.context.template_args = None

            self.task_queue.put((index, kernel, self._auto_tuner.context))
            logger.debug(f'Successfully compiled op for the {index}th config.')
        except Exception as exp:
            logger.error(f"Compilation failed for the {index}th config {config}: {exp}")
            self.task_queue.put((index, None, None))
            self._auto_tuner.clean_files(self._auto_tuner.context)

    def _launch_task(self):
        while True:
            index, kernel, context = self.task_queue.get()
            if index is None:
                break
            if kernel is None:
                continue
            self._auto_tuner.context = context
            self._auto_tuner.context.kernel_args = origin_context.kernel_args

            logger.debug(f'Start to launch op for the {index}th config on device {self._device_id}.')
            try:
                task_duration = self._auto_tuner.launch(kernel, context, self._device_id, self._warmup,
                                                        self._repeat)
                self.logging_queue.put((index, task_duration))
                logger.debug(f'Successfully launched for {index}th config.')
            except Exception as exp:
                logger.error(f'Failed to launch for {index}th config {self._configs[index]}: {exp}')
                self.logging_queue.put((index, None))
            finally:
                self._auto_tuner.clean_files(context)
                launch_context.autotune_in_progress = False

    def _log_listener(self):
        result_info_dict = {}
        while True:
            index, task_duration = self.logging_queue.get()
            if index is None:
                break
            if task_duration is None:
                continue
            result_info_dict[index] = task_duration
            config = self._configs[index]
            if self._best_config is None or task_duration < self._best_execution_time:
                self._best_config = config
                self._best_index = index
                self._best_execution_time = task_duration
        for index, task_duration in sorted(result_info_dict.items()):
            logger.info(f'No.{index}: {task_duration / 10 ** 3:.3f}μs, {self._configs[index]}')


def autotune(configs: List[Dict], warmup: int = 300, repeat: int = 1, device_ids=None):
    """Decorator for auto-tuning a kernel. Evaluate the configs and present the best one.

    Args:
        configs (List[Dict]): list of multiple key-value pairs.
        warmup (int, optional): Number of warmup iterations before measurement. Defaults to 300μs.
        repeat (int, optional): Number of repetitions for each configuration. Defaults to 1.
        device_ids (List[int], optional): Target device ID list for execution.
        Multi-device parallel execution is not yet supported.
        Only the first device id will be used currently. Defaults to [0].
    """

    if device_ids is None:
        device_ids = [0]

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                logger.debug('Starting kernel autotune... ')
                autotune_utils.check_autotune_params(configs, warmup, repeat, device_ids)
                Autotuner().pre_launch(func, device_ids[0], *args, **kwargs)
                executor = Executor(configs, device_ids, warmup, repeat)
                executor.execute()
            except Exception as exp:
                logger.error(str(exp))

        return wrapper

    return decorator


class AutotuneV2Scheduler:
    def __init__(self, configs: list, warmup_times: int, launch_params: dict):
        self._compile_processes = self._get_process_num()
        multiprocessing_manager = Manager()
        self.task_queue = multiprocessing_manager.Queue()
        self.logging_queue = multiprocessing_manager.Queue()
        self._auto_tuner = AutotunerV2(configs, warmup_times, launch_params)
        self.task_num = len(configs)

    @staticmethod
    def _get_process_num():
        max_process_num = 32
        try:
            if hasattr(os, 'sched_getaffinity'):
                cpu_count = len(os.sched_getaffinity(0))  # adapt to containerized environments
            else:
                cpu_count = os.cpu_count()
        except Exception as exp:
            logger.warning(f'Failed to detect CPU cores: {exp}. Fallback to default 32.')
            return 1
        return max(min(int(cpu_count / 2), max_process_num), 1)

    def execute(self):
        launch_context.autotune_in_progress = True
        compile_pool = Pool(min(self._compile_processes, self.task_num))

        # start logger monitor
        log_thread = threading.Thread(target=self._log_listener)
        log_thread.start()

        # start compile task and launch task
        compile_tasks = [compile_pool.apply_async(self._compile_task, (i,)) for i in range(self.task_num)]
        launch_thread = threading.Thread(target=self._launch_task)
        launch_thread.start()

        # wait for compile task finish
        for compile_task in compile_tasks:
            compile_task.get()
        compile_pool.close()
        compile_pool.join()

        self.task_queue.put((None, None))

        launch_thread.join()

        self.logging_queue.put((None, None))
        log_thread.join()
        launch_context.autotune_in_progress = False
        logger.debug('Kernel autotune end...')

    def _compile_task(self, index):
        try:
            new_src_file = self._auto_tuner.gen_src_file(index)
            logger.debug(f'Start to compile for the config No.{index}')
            executable = self._auto_tuner.compile(new_src_file)
            self.task_queue.put((index, executable))
            logger.debug(f'Successfully compiled for the config No.{index}')
        except Exception as e:
            logger.error(f"Compilation failed for the config No.{index}: {e}")
            self.task_queue.put((index, None))
        finally:
            self._auto_tuner.clean_temp_files()

    def _launch_task(self):
        processed_task_num = 0
        while processed_task_num < self.task_num:
            index, executable = self.task_queue.get()
            if index is None:
                break
            processed_task_num = processed_task_num + 1
            if executable is None:
                continue

            logger.debug(f'Start to launch op for the config No.{index}')
            try:
                task_duration = self._auto_tuner.launch(executable)
                self.logging_queue.put((index, task_duration))
                logger.debug(f'Successfully launched for the config No.{index} runtime={task_duration}')
            except Exception as e:
                self.logging_queue.put((index, None))
                logger.error(f"Failed to launch for the config No.{index}: {e}")
            finally:
                self._auto_tuner.clean_temp_files()

    def _log_listener(self):
        result_info_dict = {}
        while True:
            index, task_duration = self.logging_queue.get()
            if index is None:
                break
            if task_duration is None:
                continue
            result_info_dict[index] = task_duration
        self._auto_tuner.show_result(result_info_dict)
        self._auto_tuner.save_result(result_info_dict)
        self._auto_tuner.remove_temp_dir()


def get_params_from_pre_launch(user_func, *args, **kwargs) -> dict:
    # pre launch
    launch_context.reset()
    try:
        logger.debug('Starting kernel pre-launch...')
        launch_context.prelaunch_flag = True
        user_func(*args, **kwargs)
        launch_context.prelaunch_flag = False
        logger.debug('Kernel pre-launch completed...')
        return {'src_file': launch_context.kernel_src_file,
                'build_script': launch_context.build_script,
                'args': launch_context.kernel_args}
    except Exception as e:
        raise Exception(f'pre-launch operator failed') from e


class AutotunerV2:
    '''
    Autotuner for actlass device-layer API
    '''

    def __init__(self, configs: list, warmup_times: int, launch_params: dict):
        self.configs = configs
        self.warmup_times = warmup_times
        self.launch_params = launch_params
        self.temp_files = []
        self.temp_dir = self._create_temp_dir()

    @staticmethod
    def _create_temp_dir():
        local_time = datetime.now(tz=timezone.utc) + timedelta(hours=8)
        timestamp = local_time.strftime("%Y%m%d%H%M%S")
        temp_dir = f'./.mskl_temp_{timestamp}'
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            os.chmod(temp_dir, safe_check.DATA_DIRECTORY_AUTHORITY)
        else:
            raise OSError('temp dir {} already exists'.format(temp_dir))
        return temp_dir

    def gen_src_file(self, index):

        def _modify_file_path_with_index(file, index):
            # 为避免因更改代码文件路径可能导致的include头文件失败
            # 选择在相同目录下生成新代码文件
            path = Path(file)
            prefix = '' if path.stem.startswith('_gen_') else "_gen_"
            new_name = f'{prefix}{path.stem}_{index}{path.suffix}'
            return os.path.join(os.path.dirname(file), new_name)

        src_file = self.launch_params['src_file']
        new_src_file = _modify_file_path_with_index(src_file, index)
        Replacer.replace_src_with_config(src_file, new_src_file, self.configs[index])
        self.mark_as_temp_file(new_src_file)
        return new_src_file

    def mark_as_temp_file(self, file):
        self.temp_files.append(file)

    def clean_temp_files(self):
        if logger.log_level == '0':
            return
        for path in self.temp_files:
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)  # 发生错误后继续执行，不抛出异常
            elif os.path.isfile(path):
                os.remove(path)
        self.temp_files = []

    def remove_temp_dir(self):
        if logger.log_level == '0':
            return
        path = self.temp_dir
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)  # 发生错误后继续执行，不抛出异常

    def compile(self, new_src_file):
        build_script = self.launch_params['build_script']
        executable_file_name = str(Path(new_src_file).with_suffix('.bin').name)
        executable_file_path = os.path.join(self.temp_dir, executable_file_name)
        return compile_executable(build_script, new_src_file, executable_file_path)

    def launch(self, executable: CompiledExecutable):

        def extract_profile_path(stdout: str) -> str:
            """从 stdout 中提取 Profiling 结果路径"""
            for line in stdout.splitlines():
                if "Profiling results saved in " in line:
                    # 分割字符串提取路径
                    result = line.split("Profiling results saved in ", 1)[1].strip()
                    if os.path.basename(result).startswith('OPPROF_'):
                        return result
            raise Exception('no profiling results found. maybe profiling failed. info: {}'.format(stdout))

        def read_task_duration_from_profiling_dir(profiling_dir: str):
            file_path = os.path.join(profiling_dir, 'OpBasicInfo.csv')
            if not os.path.exists(file_path):
                raise OSError('profiling file {} does not exist'.format(file_path))

            # 检查 OpBasicInfo.csv 的文件权限
            checker = FileChecker(file_path, "file")
            if not checker.check_input_file():
                raise Exception("Check the file {} permission failed.".format(file_path))

            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if len(rows) >= 2 and len(rows[1]) >= 3:
                    # 获取第二行第三列的Task Duration（索引从0开始）
                    target_value = rows[1][2]  # 第二行是索引1，第三列是索引2
                    try:
                        task_duration = float(target_value)
                    except ValueError as exp:
                        raise Exception(
                            'Task duration {} in OpBasicInfo.csv is not a float. '
                            'error info: {}'.format(target_value, exp))
                    if task_duration <= float(0):
                        raise ValueError('The value of task_duration {} is not positive'.format(task_duration))
                    return task_duration
                else:
                    raise Exception('OpBasicInfo.csv does not have the expected content')

        args = self.launch_params['args']
        cmd = ['msprof', 'op', f'--warm-up={self.warmup_times}', f'--output={self.temp_dir}']
        stdout = executable(*args, profiling_cmd=cmd)
        self.mark_as_temp_file(executable.get_executable_path())

        # 获取耗时
        profiling_dir = extract_profile_path(stdout)
        self.mark_as_temp_file(profiling_dir)
        task_duration = read_task_duration_from_profiling_dir(profiling_dir)
        return task_duration

    def show_result(self, result: dict):
        best_runtime = None
        best_index = None
        for index, task_duration in sorted(result.items()):
            logger.info(f'No.{index}: {task_duration:.3f} us, {self.configs[index]}')
            if best_runtime is None or task_duration < best_runtime:
                best_runtime = task_duration
                best_index = index
        logger.info(f'Best config: No.{best_index}')

    def save_result(self, result: dict):
        if not result:
            logger.info('No result needs to be saved')
            return

        import re

        head = ['No.', 'Config', 'TaskDuration(us)', 'Args']
        local_time = datetime.now(tz=timezone.utc) + timedelta(hours=8)
        timestamp = local_time.strftime("%Y%m%d%H%M%S")
        filename = f"MSKL_AUTOTUNE_RESULTS_{timestamp}.csv"
        file_checker = FileChecker(filename, "csv")
        if not file_checker.check_output_file():
            logger.error(f"Result file {filename} check failed")
            return

        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(head)
            args_list = [str(arg) for arg in self.launch_params['args']]
            args_str = ' '.join(args_list)
            for idx, config in enumerate(self.configs):
                if idx not in result:
                    continue
                temp_list = []
                for _, v in config.items():
                    filtered_val = re.sub(r',\s*', '_', v)
                    temp_list.append(filtered_val)
                config_str = '|'.join(temp_list)
                writer.writerow([idx, config_str, result[idx], args_str])
        os.chmod(filename, safe_check.SAVE_DATA_FILE_AUTHORITY)
        logger.info("Autotune results saved in {}".format(filename))


def autotune_v2(configs: list, warmup_times: int = 5):
    """Decorator for auto-tuning an executable. Evaluate the configs and present the best one.

    Args:
        configs (List[Dict]): list of multiple key-value pairs.
        warmup_times (int, optional): Number of warmup times before measurement. Defaults to 5.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                logger.debug('Starting autotune_v2...')
                autotune_utils.check_autotune_v2_params(configs, warmup_times)
                launch_params = get_params_from_pre_launch(func, *args, **kwargs)
                scheduler = AutotuneV2Scheduler(configs, warmup_times, launch_params)
                scheduler.execute()
            except Exception as e:
                raise Exception(f'autotune_v2 failed') from e

        return wrapper

    return decorator
