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

import subprocess
import os
from typing import Generic, TypeVar
import importlib.util
import sysconfig
from .context import context
from .driver import NPULauncher
from ..utils import safe_check, logger
from ..utils.safe_check import FileChecker
from ..utils.launcher_utils import get_cann_path

safe_compile_options = ['-Wall', '-fPIC', '-fstack-protector-all', '-Wl,-z,relro', '-Wl,-z,now', '-Wl,-z,noexecstack',
                        '-s', '-O2', '-D_FORTIFY_SOURCE=2', '-fvisibility=hidden', '-ftrapv', '-fstack-check']
T = TypeVar("T")


class KernelInterface(Generic[T]):
    """
    Kernel interface class, providing a way to launch function in the form: kernel[blockdim](x, y, z)
    """
    launch: T

    def __getitem__(self, blockdim) -> T:
        return lambda *args, **kwargs: self.launch(blockdim=blockdim, *args, **kwargs)


class CompiledKernel(KernelInterface[T]):
    """
    Object class representing a kernel, provides an interface to launching kernel.
    Support kernel invocation in form of "kernel[blockdim](a, b, c)".
    """

    def __init__(self, output_bin_path: str, kernel_name: str):
        self._check_constructor_input(output_bin_path, kernel_name)
        self.module_path = output_bin_path
        self.kernel_name = kernel_name
        self.__run__ = NPULauncher(self.module_path)

    def __call__(self, *args, **kwargs):
        if context.tiling_output is None:
            raise Exception('There are two ways to trigger this exception: '
                            '1.You may want to launch kernel in this form: kernel[blockdim](x, y, z). '
                            '2.Call mskl.tiling_func before launch kernel.')
        self.launch(blockdim=context.tiling_output.blockdim, *args, **kwargs)

    def launch(self, *args, blockdim: int, **kwargs):
        """
        Launch the kernel on NPU device.

        Args:
            blockdim (int): Blocks allocated for the kernel.
            stream (int, optional): Stream that the kernel assigned to.
            device_id (int, optional): Device that launched the kernel.
            timeout (int, optional): Stream synchronization timeout in miliseconds.
            kernel_name (int, optional): Name of the to be launched kernel.
        """
        stream = kwargs.get('stream', None)
        device_id = kwargs.get('device_id', None)
        timeout = kwargs.get('timeout', 300000)  # camodel仿真场景需要默认设置较长超时时间，单位: ms
        kernel_name = kwargs.get('kernel_name', self.kernel_name)
        repeat = kwargs.get('repeat', 1)
        self._check_launch_input(blockdim, stream, device_id, timeout, kernel_name)

        if not context.autotune_in_progress:
            context.blockdim = blockdim
            context.kernel_args = args

        self.__run__(blockdim=blockdim, l2ctrl=0, stream=stream, warmup=None, device_id=device_id,
                     profiling=False, timeout=timeout, kernel_name=kernel_name, repeat=repeat, *args)

    def _check_constructor_input(self, output_bin_path: str, kernel_name: str):
        safe_check.check_variable_type(output_bin_path, str)
        safe_check.check_variable_type(kernel_name, str)
        checker = FileChecker(output_bin_path, "file")
        if not checker.check_input_file():
            raise Exception("Check the output_bin_path {} permission failed.".format(output_bin_path))

    def _check_launch_input(self, blockdim: int, stream: int, device_id: int, timeout: int, kernel_name: str):
        safe_check.check_variable_type(blockdim, int)
        if blockdim <= 0:
            raise Exception(f"Blockdim must be a positive integer but got {blockdim}")
        if stream is not None:
            safe_check.check_variable_type(stream, int)
        if device_id is not None:
            safe_check.check_variable_type(device_id, int)

        safe_check.check_variable_type(timeout, int)
        safe_check.check_variable_type(kernel_name, str)


def _check_compie_input(build_script: str,
                        launch_src_file: str,
                        output_bin_path: str,
                        use_cache: bool):
    safe_check.check_variable_type(build_script, str)
    checker = FileChecker(build_script, "file")
    if not checker.check_input_file():
        raise Exception("Check the build_script {} permission failed.".format(build_script))

    safe_check.check_variable_type(launch_src_file, str)
    checker = FileChecker(launch_src_file, "file")
    if not checker.check_input_file():
        raise Exception("Check the launch_src_file {} permission failed.".format(launch_src_file))

    safe_check.check_variable_type(output_bin_path, str)
    if not output_bin_path.endswith(".so"):
        raise Exception("output_bin_path {} must be ended with .so".format(output_bin_path))

    safe_check.check_variable_type(use_cache, bool)


class ThreadSafeSet:
    def __init__(self):
        import threading
        self._set = set()
        self._lock = threading.Lock()

    def add(self, path: str) -> str:
        '''
        if path is not in set, add it to set and return itself.
        if path is in set, add suffix to it, add it to set and return the one with suffix.
        '''
        with self._lock:
            if path not in self._set:
                self._set.add(path)
                return path

            # 名称已被使用过的动态库编译时在名称末尾添加数字后缀以区分
            # 比如：lib_gen_module.so --> lib_gen_module.1.so

            suffix = 1
            candidate = ""
            while True:
                candidate = f"{path[:-3]}.{suffix}.so"  # path后3位字符为 .so
                if candidate not in self._set:
                    break
                suffix += 1

            # 当动态库名为非默认时，提示warning告知用户生成的动态库名已被修改
            if os.path.basename(path) != "_gen_module.so" and not context.autotune_in_progress:
                logger.warning("Repeatedly importing dynamic library with the same name {} will fail in Python. "
                               "Update the name to {}"
                               .format(os.path.basename(path), os.path.basename(candidate)))
            return candidate


# Importing a dynamic library with the same name will cause the cache to not be updated.
# so each compiled dynamic library needs to be named differently. All auto-generated file names
# are maintained in output_bin_path_set.
output_bin_path_set = ThreadSafeSet()


def compile(build_script: str,
            launch_src_file: str,
            output_bin_path: str = "_gen_module.so",
            use_cache: bool = False) -> CompiledKernel:
    """
    Compile a kernel and return a launchable kernel object.

    Args:
        build_script (str): The script for compiling the kernel that requires two input args
        launch_src_file (str): The launch source code file for kernel.
        output_bin_path (str, optional): Specify the output file generated from the build script.
                                         Defaults to "_gen_module.so".
        use_cache (bool, optional): Skip compiling and use the existed compiled module specified
                                    by "output_bin_path" instead.
                                    Defaults to False.

    Returns:
        CompiledKernel: A kernel object that can be launched.
    """
    _check_compie_input(build_script, launch_src_file, output_bin_path, use_cache)
    abs_launch_src_path = os.path.realpath(launch_src_file)
    abs_output_bin_path = os.path.realpath(output_bin_path)

    if use_cache and not context.autotune_in_progress:
        if not os.path.exists(abs_output_bin_path):
            raise Exception("The executable generated from build script does not exist.")
        return CompiledKernel(abs_output_bin_path, context.kernel_name)

    global output_bin_path_set
    abs_output_bin_path = output_bin_path_set.add(abs_output_bin_path)

    context.build_script = build_script
    context.launch_src_file = abs_launch_src_path

    compile_cmd = ["bash", build_script, abs_launch_src_path, abs_output_bin_path]
    result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise Exception("Compile failed.\nCommand info: " + ' '.join(compile_cmd) + "\n{}".format(result.stderr))

    if result.stdout.strip() != "":
        logger.info(f"Compilation output: {result.stdout}")

    return CompiledKernel(abs_output_bin_path, context.kernel_name)


def compile_tiling(cpp_path: str, so_path: str):
    if os.path.exists(so_path):
        try:
            os.remove(so_path)
        except Exception as e:
            raise OSError(f'remove {so_path} failed, you can remove {os.path.dirname(so_path)} manually and try again, '
                          f'error message is {e}') from e

    cann_path = get_cann_path()
    args = ['g++', cpp_path, f'-I{sysconfig.get_path("include")}', '-o', so_path, '-shared',
            f'-I{cann_path}/include', f'-L{cann_path}/lib64', '-ltiling_api', '-ldl',
            '-lgraph_base', '-lgraph', '-lc_sec', '-lregister', '-lopp_registry', '-lascendalog', '-lplatform']
    args.extend(safe_compile_options)
    res = subprocess.run(args, capture_output=True, text=True, timeout=600)
    if res.returncode != 0:
        raise Exception(f'Compile {so_path} failed.\nArgs: {args}\nError info: {res.stderr}')
    os.chmod(so_path, safe_check.SAVE_DATA_FILE_AUTHORITY)

    spec = importlib.util.spec_from_file_location("_mskl_tiling_launcher", so_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "_tiling_func"):
        raise Exception(f'{so_path} does not contain _tiling_func, the compilation process may be faulty')
    return getattr(module, "_tiling_func")


def compile_kernel_binary(src_file: str, so_path: str) -> CompiledKernel:
    # src_file 是工具生成文件，不受用户直接影响，跳过校验
    if os.path.exists(so_path):
        try:
            os.remove(so_path)
        except Exception as e:
            raise OSError(f'remove {so_path} failed, you can remove {os.path.dirname(so_path)} manually and try again, '
                          f'error message is {e}') from e

    cann_path = get_cann_path()
    args = ['g++', src_file, f'-I{sysconfig.get_path("include")}', f'-I{cann_path}/include',
            f'-L{cann_path}/lib64', '-shared', '-o', so_path, '-ldl', '-lascendcl', '-lruntime',
            '-lascend_dump']
    args.extend(safe_compile_options)
    res = subprocess.run(args, capture_output=True, text=True, timeout=600)
    if res.returncode != 0:
        cmd = ' '.join(args)
        raise Exception(f'Compile {so_path} failed.\nCmd: {cmd}\nError info: {res.stderr}')
    os.chmod(so_path, safe_check.SAVE_DATA_FILE_AUTHORITY)

    return CompiledKernel(so_path, context.kernel_name)


class CompiledExecutable:
    """
    Object class representing an executable file, provides an interface to execute itself in subprocess.
    """

    def __init__(self, _executable_path: str):
        if not context.prelaunch_flag:
            self._check_constructor_input(_executable_path)
        self._executable_path = _executable_path

    def __call__(self, *args, **kwargs):
        return self._launch(*args, **kwargs)

    @staticmethod
    def _check_constructor_input(_executable_path: str):
        safe_check.check_variable_type(_executable_path, str)
        checker = FileChecker(_executable_path, "file")
        if not checker.check_input_file():
            raise Exception("Check the executable file path {} permission failed.".format(_executable_path))

    def get_executable_path(self):
        return self._executable_path

    def _launch(self, *args, **kwargs):
        if not context.autotune_in_progress:
            context.kernel_args = args
            logger.debug('Context.kernel_args saved kernel_args={}'.format(context.kernel_args))
        if context.prelaunch_flag:
            return ""

        profiling_cmd = kwargs.get('profiling_cmd', None)
        args_str = [str(arg) for arg in args]

        cmd = (
            [*profiling_cmd, self._executable_path, *args_str]
            if profiling_cmd is not None
            else [self._executable_path, *args_str]
        )

        logger.debug("The cmd = {}".format(cmd))
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if res.returncode != 0:
            raise Exception('Run executable failed.\ncmd: ' + ' '.join(cmd) + "\n{}".format(res.stderr))

        if context.autotune_in_progress:
            return res.stdout

        if res.stdout.strip() != "":
            logger.info(f"Command output: {res.stdout}")

        return ""


def compile_executable(build_script: str,
                       src_file: str,
                       output_bin_path: str = "_gen_executable",
                       use_cache: bool = False) -> CompiledExecutable:
    """
    Compile and return an executable object.

    Args:
        build_script (str): The script for compiling. It requires two input args: src_file and output_bin_path
        src_file (str): The source code file that needs to be compiled.
        output_bin_path (str, optional): Specify the output file generated from the build script.
                                         Defaults to "_gen_executable".
        use_cache (bool, optional): Skip compiling and use the existed compiled binary specified
                                    by "output_bin_path" instead.
                                    Defaults to False.

    Returns:
        CompiledExecutable: An executable object that can be launched.
    """

    def _check_compile_executable_input(build_script, launch_src_file, output_bin_path, use_cache):
        safe_check.check_variable_type(build_script, str)
        checker = FileChecker(build_script, "file")
        if not checker.check_input_file():
            raise Exception("Check the build_script {} permission failed.".format(build_script))

        safe_check.check_variable_type(launch_src_file, str)
        checker = FileChecker(launch_src_file, "file")
        if not checker.check_input_file():
            raise Exception("Check the launch_src_file {} permission failed.".format(launch_src_file))

        safe_check.check_variable_type(output_bin_path, str)
        safe_check.check_variable_type(use_cache, bool)

    if not context.prelaunch_flag:
        _check_compile_executable_input(build_script, src_file, output_bin_path, use_cache)

    abs_src_path = os.path.realpath(src_file)
    abs_output_bin_path = os.path.realpath(output_bin_path)

    if use_cache and not context.autotune_in_progress:
        if not os.path.exists(abs_output_bin_path):
            raise Exception("The executable generated from build script does not exist.")
        return CompiledExecutable(abs_output_bin_path)

    if context.prelaunch_flag:
        context.build_script = build_script
        context.kernel_src_file = abs_src_path
        return CompiledExecutable(abs_output_bin_path)

    compile_cmd = ["bash", build_script, abs_src_path, abs_output_bin_path]
    result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise Exception("Compile failed.\nCommand info: " + ' '.join(compile_cmd) + "\n{}".format(result.stderr))

    if result.stdout.strip() != "":
        logger.info("Compile command output: {res.stdout}")

    return CompiledExecutable(abs_output_bin_path)
