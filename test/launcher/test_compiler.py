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
import os
import unittest
from unittest.mock import Mock, patch

from mskl.launcher import compiler
from mskl.launcher.context import context


class TempTilingFunc:
    def __init__(self):
        self._tiling_func = 1234


class Spec:
    class Loader:
        @staticmethod
        def exec_module(_):
            pass

    def __init__(self):
        self.loader = Spec.Loader()


class ReturnCode:
    def __init__(self):
        self.returncode = 0
        self.stdout = 'done'


class TestCompiler(unittest.TestCase):
    def test_compile_tiling(self):
        with patch("subprocess.run") as mock_run, \
                patch("importlib.util.spec_from_file_location") as mock_location, \
                patch("importlib.util.module_from_spec") as mock_spec, \
                patch("os.chmod") as mock_chmod, \
                patch("os.getenv") as mock_getenv:
            mock_run.return_value = ReturnCode()
            mock_location.return_value = Spec()
            mock_spec.return_value = TempTilingFunc()
            mock_chmod.return_value = True
            mock_getenv.return_value = os.getcwd()
            self.assertEqual(compiler.compile_tiling('_gen_tiling.cpp', '_gen_tiling.so'),
                             TempTilingFunc()._tiling_func)

    def test_compile_kernel_binary(self):
        with patch("subprocess.run") as mock_run, \
                patch("os.getenv") as mock_getenv, \
                patch("os.chmod") as mock_chmod, \
                patch("mskl.launcher.compiler.CompiledKernel._check_constructor_input") as mock_check:
            mock_run.return_value = ReturnCode()
            mock_getenv.return_value = os.getcwd()
            mock_chmod.return_value = True
            mock_check.return_value = True

            context.kernel_name = 'kernel_binary'
            # 验证流程能够正常执行结束
            compiler.compile_kernel_binary('_gen_binary_launch.cpp', '_gen_binary_module.so')
            self.assertEqual(mock_run.call_count, 1)
            self.assertEqual(mock_getenv.call_count, 1)
            self.assertEqual(mock_check.call_count, 1)

    def test_compile_executable(self):
        with patch("subprocess.run") as mock_run, \
                patch("os.path.realpath") as mock_realpath, \
                patch("os.path.exists") as mock_exists, \
                patch("os.chmod") as mock_chmod, \
                patch("mskl.utils.safe_check.check_variable_type") as mock_check_variable_type, \
                patch("mskl.utils.safe_check.FileChecker.check_input_file") as mock_check_input_file, \
                patch("mskl.launcher.compiler.CompiledExecutable._check_constructor_input") as mock_check:

            mock_run.return_value = ReturnCode()
            mock_realpath.return_value = '_gen_binary_launch.cpp'
            mock_exists.return_value = True
            mock_chmod.return_value = True
            mock_check_variable_type.return_value = True
            mock_check_input_file.return_value = True
            mock_check.return_value = True



            context.prelaunch_flag = False
            # 验证流程能够正常执行结束
            compiler.compile_executable('jit_build.sh', '_gen_binary_launch.cpp')
            self.assertEqual(mock_run.call_count, 1)
            self.assertEqual(mock_check.call_count, 1)

            context.prelaunch_flag = True
            compiler.compile_executable('jit_build.sh', '_gen_binary_launch.cpp')

            context.prelaunch_flag = False
            compiler.compile_executable('jit_build.sh', '_gen_binary_launch.cpp', use_cache=True)

            mock_run.return_value.returncode = 1
            self.assertRaises(Exception, compiler.compile_executable,
                'jit_build.sh', '_gen_binary_launch.cpp')