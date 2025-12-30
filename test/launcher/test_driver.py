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

import sys
import ctypes
import numpy as np
import unittest
from unittest.mock import patch, Mock, MagicMock

sys.modules['acl'].rt.malloc = MagicMock()
sys.modules['acl'].rt.malloc.return_value = (0, 0)
sys.modules['acl'].rt.memcpy = MagicMock()
sys.modules['acl'].rt.memcpy.return_value = 0
sys.modules['acl'].rt.free = MagicMock()
sys.modules['acl'].rt.free.return_value = 0

from mskl.launcher.driver import NPULauncher


class Point(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int),
        ("y", ctypes.c_int)
    ]


class TestDriver(unittest.TestCase):

    def test_arg_preprocess(self):
        launcher = NPULauncher('test_module')
        a = np.zeros([128]).astype(np.float16)
        b = np.zeros([128]).astype(np.float16)
        lst = [a, b]
        arr = (ctypes.c_int * 5)(1, 2, 3, 4, 5)
        p = Point(1, 2)
        self.assertRaises(Exception, launcher._arg_preprocess, 1, a, None, arr, p, lst, 'abc')
