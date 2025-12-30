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
import unittest
from unittest.mock import patch, Mock, MagicMock, call
import os
from pathlib import Path
from threading import Thread


# Mock class definition
class MockReplacer:
    replace_config = Mock()


class MockLauncher:
    code_gen = Mock()


class MockCompiledKernel:
    launch = Mock()


class MockMonitor:
    start = Mock()
    stop = Mock()
    get_task_duration = Mock(return_value=1000)
    get_last_n_task_duration = Mock(return_value=1000)


class MockAutoTuner:
    def __init__(self):
        self.context = 'mock_context'

    def gen_context(self, index, search_node):
        return 'mock_context'

    def compile_op(self, index):
        return 'mock_kernel'

    def clean_files(self, context):
        pass

    def code_gen(self):
        pass

    def launch(self, kernel, context, device_id, warmup, repeat):
        return 1500


class MockAutoTunerV2:
    def __init__(self):
        self.context = 'mock_context'

    def gen_src_file(self, index):
        return 'new_src.cpp'

    def compile(self, new_src_file):
        return 'compiled_executable'

    def clean_temp_files(self):
        pass

    def launch(self, kernel):
        return float(20)



from mskl.optune.tuner import Autotuner, Executor, autotune, launch_context, \
    autotune_v2, AutotuneV2Scheduler, AutotunerV2
from mskl.launcher.context import Context, context
from mskl.utils import logger, safe_check

# global mock objects
mock_context = Context()
mock_context.kernel_src_file = "./kernel.cpp"
mock_context.launch_src_file = "./launch.cpp"
mock_context.build_script = "build.sh"
mock_context.blockdim = 256
mock_context.kernel_args = {"arg1": 1}


class TestAutotuner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_context = Autotuner().context
        Autotuner._instance = None  # Reset singleton

    def setUp(self):
        self.autotuner = Autotuner()
        self.autotuner.context = mock_context
        self.autotuner.replacer = MockReplacer()

    @patch('mskl.utils.autotune_utils.get_file_lines')
    def test_pre_launch(self, mock_get_file):
        mock_get_file.return_value = ["test content"]

        def dummy_func():
            pass

        self.autotuner.pre_launch(dummy_func, 0)
        self.assertIsNotNone(self.autotuner.context)

    @patch('mskl.optune.tuner.compile')
    def test_compile_op(self, mock_compile):
        mock_compile.return_value = MockCompiledKernel()
        result = self.autotuner.compile_op(0)
        mock_compile.assert_called_with(
            mock_context.build_script,
            mock_context.launch_src_file,
            "launch.so"
        )
        self.assertIsInstance(result, MockCompiledKernel)

    @patch('mskl.optune.tuner.Monitor', new=MockMonitor)
    def test_launch(self):
        # kernel = MockCompiledKernel()
        kernel = MagicMock()
        kernel.__getitem__.return_value = Mock()
        duration = self.autotuner.launch(
            kernel, mock_context, 0, 300, 2
        )
        self.assertEqual(duration, 500)

    def test_clean_files(self):
        files = [mock_context.kernel_src_file, mock_context.launch_src_file,
                 Path(mock_context.launch_src_file).with_suffix('.so'),
                 Path(mock_context.launch_src_file).with_suffix('.o')]
        for file in files:
            Path(file).touch()
        logger.log_level = '1'
        self.autotuner.clean_files(mock_context)
        for file in files:
            self.assertFalse(os.path.exists(file))


class TestExecutor(unittest.TestCase):
    def setUp(self):
        # Initialize mock parameters
        self.configs = [{"block_size": 256}, {"block_size": 512}]
        self.device_ids = [0]
        self.warmup = 1
        self.repeat = 1

        # Create Executor instance and replace Autotuner with MagicMock
        self.executor = Executor(
            configs=self.configs,
            device_ids=self.device_ids,
            warmup=self.warmup,
            repeat=self.repeat,
            compile_process_num=2
        )

    @patch('mskl.launcher.context.context', new=mock_context)
    @patch('mskl.utils.autotune_utils.get_file_lines')
    def test_compile_task_success(self, mock_get_file):
        """Test successful compilation scenario"""
        # Mock Autotuner methods
        self.executor._auto_tuner = MockAutoTuner()

        # Execute compilation task
        self.executor._compile_task(0)

        # Verify queue data
        expected_item = (0, "mock_kernel", context)
        self.assertEqual(self.executor.task_queue.get()[:2], expected_item[:2])

    @patch('mskl.utils.autotune_utils.get_file_lines')
    def test_compile_task_failure(self, mock_get_file):
        """Test compilation task failure scenario"""

        # Mock compilation exception
        def code_gen():
            raise RuntimeError()

        self.executor._auto_tuner = MockAutoTuner()
        self.executor._auto_tuner.code_gen = code_gen

        # Execute compilation task
        self.executor._compile_task(0)
        # Verify resource cleanup and queue
        self.assertEqual(self.executor.task_queue.get(), (0, None, None))

    def test_launch_task_normal_execution(self):
        """Test task launch and execution time recording"""
        # Mock task queue data
        self.executor.task_queue.put((0, "mock_kernel", mock_context))
        self.executor.task_queue.put((None, None, None))  # Termination signal

        # Mock Autotuner.launch return value
        self.executor._auto_tuner = MockAutoTuner()

        # Start task thread
        launch_thread = Thread(target=self.executor._launch_task)
        launch_thread.start()
        launch_thread.join()

        self.assertEqual(self.executor.logging_queue.get(), (0, 1500))

    def test_log_listener_updates_best_config(self):
        """Test log listener updating best configuration"""
        # Inject log data (two configurations, second is faster)
        self.executor.logging_queue.put((0, 2000))
        self.executor.logging_queue.put((1, 1800))
        self.executor.logging_queue.put((None, None))  # Termination signal

        # Start listener thread
        log_thread = Thread(target=self.executor._log_listener)
        log_thread.start()
        log_thread.join()

        # Verify best configuration
        self.assertEqual(self.executor._best_config, self.configs[1])
        self.assertEqual(self.executor._best_execution_time, 1800)

    @patch("multiprocessing.Pool")
    @patch('mskl.utils.autotune_utils.get_file_lines')
    def test_execute_full_flow(self, mock_get_file, mock_pool):
        """Test complete execute() workflow"""
        # Mock thread pool and task results
        mock_pool.return_value.__enter__.return_value.apply_async.return_value.get.return_value = None
        self.executor._auto_tuner = MockAutoTuner()

        # Execute main workflow
        self.executor.execute()

        # Verify final state
        self.assertEqual(self.executor._best_execution_time, 1500)


class TestAutotuneV2(unittest.TestCase):
    PROF_DIR = 'OPPROF_MOCK'
    CSV_PATH = PROF_DIR + '/OpBasicInfo.csv'
    TASK_DURATION = 13.9

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(TestAutotuneV2.PROF_DIR):
            os.mkdir(TestAutotuneV2.PROF_DIR, safe_check.DATA_DIRECTORY_AUTHORITY)

        with os.fdopen(os.open(TestAutotuneV2.CSV_PATH, safe_check.OPEN_FLAGS,
            safe_check.SAVE_DATA_FILE_AUTHORITY), 'w') as f:
            f.truncate()
            f.write('Op Name,Op Type,Task Duration(us),Block Dim,Mix Block Dim,Device Id,Pid,Current Freq,Rated Freq,')
            f.write('\nkernel,mix,{},20,40,1,621627,1650,1650,'.format(TestAutotuneV2.TASK_DURATION))


    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TestAutotuneV2.CSV_PATH):
            os.remove(TestAutotuneV2.CSV_PATH)
        if os.path.exists(TestAutotuneV2.PROF_DIR):
            os.rmdir(TestAutotuneV2.PROF_DIR)


    @patch.object(AutotunerV2, '_create_temp_dir')
    def setUp(self, mock_create_temp_dir):
        # Initialize mock parameters

        self.configs = [
            {'L1TileShape': 'GemmShape<256, 128, 256>', 'L0TileShape': 'GemmShape<256, 128, 64>'},
            {'L1TileShape': 'GemmShape<128, 128, 256>', 'L0TileShape': 'GemmShape<128, 128, 64>'},
            {'L1TileShape': 'GemmShape<128, 128, 512>', 'L0TileShape': 'GemmShape<128, 128, 64>'},
        ]
        self.warmup_times = 1
        self.launch_params = {
            'src_file': 'a.cpp',
            'build_script': 'b.sh',
            'args': (1, 2, 3)
        }
        mock_create_temp_dir.return_value = "mocked_dir"
        self.autotuner = AutotunerV2(
            configs=self.configs,
            warmup_times=self.warmup_times,
            launch_params=self.launch_params,
        )

    @patch('mskl.optune.tuner.compile_executable')
    def test_compile_success(self, mock_compile_executable):
        mock_compile_executable.return_value = 'mocked_executable'

        self.assertEqual(self.autotuner.compile('a.cpp'), 'mocked_executable')
        mock_compile_executable.assert_called_once()

    @patch('mskl.optune.tuner.CompiledExecutable')
    def test_launch_success(self, mock_CompiledExecutable):
        mock_compiled_executable = mock_CompiledExecutable()
        mock_compiled_executable.return_value = 'Profiling results saved in {}'.format(TestAutotuneV2.PROF_DIR)

        self.assertEqual(self.autotuner.launch(mock_compiled_executable), TestAutotuneV2.TASK_DURATION)

    @patch('mskl.optune.tuner.CompiledExecutable')
    def test_launch_failed_due_to_no_opprof_dir(self, mock_CompiledExecutable):
        mock_compiled_executable = mock_CompiledExecutable()
        mock_compiled_executable.return_value = 'no prof data\nno prof data'

        # 未找到 OPPROF 目录
        self.assertRaises(Exception, self.autotuner.launch, mock_compiled_executable)

    def test_show_result_success(self):
        result = {}
        self.autotuner.show_result(result)
        result = {0: 10, 1: 20, 2:30}
        self.autotuner.show_result(result)

    @patch('mskl.optune.tuner.datetime')
    def test_save_result_success(self, mock_datetime):
        filename = 'MSKL_AUTOTUNE_RESULTS_20770101200000.csv'

        from datetime import datetime, timezone
        fixed_utc_time = datetime(2077, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_utc_time

        result = {0: 10, 1: 20}
        self.autotuner.save_result(result)
        self.assertTrue(os.path.exists(filename))
        os.remove(filename)

    @patch('mskl.utils.logger')
    def test_clean_temp_files_when_log_level_is_debug(self, mock_logger):
        mock_logger.log_level = '0'
        self.autotuner.clean_temp_files()

    @patch('mskl.utils.logger')
    def test_clean_temp_files_success(self, mock_logger):
        mock_logger.log_level = '1'
        self.autotuner.temp_files = []
        self.autotuner.clean_temp_files()

        mock_temp_files = ['./test_mock_dir_1', './test_mock_dir_2']

        self.autotuner.temp_files = mock_temp_files
        for file in mock_temp_files:
            if not os.path.exists(file):
                os.mkdir(file)

        self.autotuner.clean_temp_files()
        self.assertFalse(os.path.exists(mock_temp_files[0]))
        self.assertFalse(os.path.exists(mock_temp_files[1]))

    @patch('mskl.utils.logger')
    def test_remove_temp_dir_when_log_level_is_debug(self, mock_logger):
        mock_logger.log_level = '0'
        self.autotuner.remove_temp_dir()

    @patch('mskl.utils.logger')
    def test_remove_temp_dir_success(self, mock_logger):
        mock_logger.log_level = '1'
        mock_temp_dir = './mock_temp_dir'
        self.autotuner.temp_dir = mock_temp_dir
        if not os.path.exists(mock_temp_dir):
            os.mkdir(self.autotuner.temp_dir)
        self.autotuner.remove_temp_dir()

        self.assertFalse(os.path.exists(mock_temp_dir))


class TestAutotuneV2Scheduler(unittest.TestCase):

    @patch.object(AutotunerV2, '_create_temp_dir')
    def setUp(self, mock_create_temp_dir):
        # Initialize mock parameters
        self.configs = [{"L1TileShape": 256}, {"L0TileShape": 512}]
        self.warmup_times = 1
        self.launch_params = {
            'src_file': 'a.cpp',
            'build_script': 'b.sh',
            'args': (1, 2, 3)
        }

        # Create Executor instance and replace Autotuner with MagicMock
        mock_create_temp_dir.return_value = "mocked_value"
        self.executor = AutotuneV2Scheduler(
            configs=self.configs,
            warmup_times=self.warmup_times,
            launch_params=self.launch_params,
        )

        # 注入模拟的AutotunerV2
        self.mock_autotuner_v2 = MagicMock()
        self.executor._auto_tuner = self.mock_autotuner_v2
        self.executor.task_num = 1

    def test_compile_task_success(self):
        self.executor._auto_tuner.gen_src_file.return_value = 'a.cpp'
        self.executor._auto_tuner.compile.return_value = 'compiled_executable'

        self.executor._compile_task(0)

        expected_item = (0, "compiled_executable")
        self.assertEqual(self.executor.task_queue.get()[:], expected_item[:])

    def test_compile_task_failure(self):
        def go_wrong():
            raise Exception('test exception')
        self.executor._auto_tuner.compile = go_wrong

        self.executor._compile_task(0)
        self.assertEqual(self.executor.task_queue.get(), (0, None))

    def test_launch_task_success(self):
        # Mock task queue data
        self.executor.task_queue.put((0, "mock_kernel"))
        self.executor.task_queue.put((None, None))  # Termination signal

        # Mock Autotuner.launch return value
        mock_task_duration = float(20)
        self.executor._auto_tuner.launch.return_value = mock_task_duration
        self.executor._auto_tuner.clean_temp_files.return_value = None

        # Start task thread
        launch_thread = Thread(target=self.executor._launch_task)
        launch_thread.start()
        launch_thread.join()

        self.assertEqual(self.executor.logging_queue.get(), (0, mock_task_duration))

    def test_launch_task_exception_due_to_launch_failed(self):
        # Mock Autotuner.launch raise exception
        def go_wrong():
            raise Exception('test exception')
        self.executor._auto_tuner.launch = go_wrong
        self.executor._auto_tuner.clean_temp_files.return_value = None

        # Mock task queue data
        self.executor.task_queue.put((0, "mock_kernel"))
        self.executor.task_queue.put((None, None))  # Termination signal

        # Start task thread
        launch_thread = Thread(target=self.executor._launch_task)
        launch_thread.start()
        launch_thread.join()

        self.assertEqual(self.executor.logging_queue.get(), (0, None))

    def test_log_listener_success(self):
        self.executor._auto_tuner.show_result.return_value = None
        self.executor._auto_tuner.save_result.return_value = None
        self.executor._auto_tuner.remove_temp_dir.return_value = None

        self.executor.logging_queue.put((0, 20))
        self.executor.logging_queue.put((1, 18))
        self.executor.logging_queue.put((None, None))  # Termination signal

        # Start listener thread
        log_thread = Thread(target=self.executor._log_listener)
        log_thread.start()
        log_thread.join()

        # Verify best configuration
        self.executor._auto_tuner.show_result.assert_called_once()
        self.executor._auto_tuner.save_result.assert_called_once()
        self.executor._auto_tuner.remove_temp_dir.assert_called_once()


class TestAutotuneDecorator(unittest.TestCase):
    @patch('mskl.utils.autotune_utils.check_autotune_params')
    @patch('mskl.optune.tuner.Executor')
    @patch('mskl.optune.tuner.Autotuner')
    def test_autotune_decorator(self, mock_autotuner, mock_executor, mock_check):
        mock_autotuner.return_value.pre_launch.return_value = None
        mock_executor.return_value.execute.return_value = None

        @autotune([{"param": 1}], warmup=300)
        def test_func():
            pass

        test_func()
        mock_autotuner.return_value.pre_launch.assert_called_once()
        mock_executor.return_value.execute.assert_called_once()


class TestAutotuneV2Decorator(unittest.TestCase):
    @patch('mskl.utils.autotune_utils.check_autotune_v2_params')
    @patch('mskl.optune.tuner.AutotuneV2Scheduler')
    @patch('mskl.optune.tuner.get_params_from_pre_launch')
    def test_autotune_v2_decorator(self, mock_pre_launch, mock_scheduler, mock_check):
        mock_check.return_value = None
        mock_pre_launch.return_value = {
            'src_file': 'a.cpp',
            'build_script': 'b.sh',
            'args': (1, 2, 3)
        }
        mock_scheduler.return_value.execute.return_value = None

        @autotune_v2([{"param": 1}], warmup_times=5)
        def test_func():
            pass

        test_func()
        mock_pre_launch.assert_called_once()
        mock_scheduler.return_value.execute.assert_called_once()


# Context tests
class TestContext(unittest.TestCase):
    def test_context_properties(self):
        ctx = Context()
        ctx.kernel_src_file = "/test/path"
        self.assertEqual(ctx.kernel_src_file, "/test/path")
        ctx.blockdim = 512
        self.assertEqual(ctx.blockdim, 512)
        ctx.prelaunch_flag = True
        self.assertEqual(ctx.prelaunch_flag, True)
        ctx.autotune_in_progress = True
        self.assertEqual(ctx.autotune_in_progress, True)
        ctx.reset()
