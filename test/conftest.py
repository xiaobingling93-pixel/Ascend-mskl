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
import unittest
from unittest.mock import MagicMock


def pytest_configure(config):
    # 全测试例运行生命周期范围的 MagicMock，为了解决下面的问题
    # mskl.launcher.driver.NPUDeviceContext 在被import时会import acl并调用rt.get_device
    sys.modules['acl'] = MagicMock()
    sys.modules['acl'].rt = MagicMock()
    sys.modules['acl'].rt.get_device = MagicMock()
    sys.modules['acl'].rt.set_device = MagicMock()
    sys.modules['acl'].rt.get_device.return_value = (None, 1)
    sys.modules['acl'].rt.set_device.return_value = 0

    sys.modules['mspti'] = MagicMock()

    class MockMsptiResult:
        MSPTI_SUCCESS = 0
        MSPTI_ERROR = 1

    sys.modules['mspti'].MsptiResult = MockMsptiResult
