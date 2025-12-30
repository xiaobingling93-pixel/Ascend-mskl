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
import pathlib
import stat

from test.utils.test_base import TestBase
from mskl.launcher.config import KernelInvokeConfig
from mskl.launcher.code_generator import Launcher


class TestCopy(TestBase):
    TRACE_FILE = 'trace.json'

    def setUp(self):
        self.kernel_file = "./_test_code_generator.cpp"
        self.kernel_name = "BasicMatmul"
        pathlib.Path(self.kernel_file).touch()
        os.chmod(path=self.kernel_file, mode=stat.S_IWUSR | stat.S_IRUSR)

    def tearDown(self):
        os.remove(self.kernel_file)

    def test_launcher_initialization(self):
        config = KernelInvokeConfig(self.kernel_file, self.kernel_name)
        launcher = Launcher(config)


class TestLauncher(unittest.TestCase):
    def test_launcher_raise_due_to_unknown_config(self):
        def func():
            Launcher(None)
        self.assertRaises(Exception, func)
