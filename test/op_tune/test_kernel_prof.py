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
from unittest.mock import MagicMock, patch, Mock

from mskl.optune.kernel_prof import Monitor


class TestMonitor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mock_kernel_data = MagicMock()
        cls.mock_kernel_data.end = 100
        cls.mock_kernel_data.start = 20

        sys.modules['mspti'].KernelMonitor = MagicMock()

        # mock acl
        sys.modules['acl'].init = MagicMock()
        sys.modules['acl'].rt.set_device = MagicMock()
        sys.modules['acl'].rt.reset_device = MagicMock()

    def setUp(self):
        self.monitor = Monitor()
        self.monitor._monitor = sys.modules['mspti'].KernelMonitor.return_value
        # reset mock
        sys.modules['acl'].init.reset_mock()
        sys.modules['acl'].rt.set_device.reset_mock()
        sys.modules['acl'].rt.reset_device.reset_mock()
        self.monitor._monitor.start.reset_mock()
        self.monitor._monitor.stop.reset_mock()

    def test_start_failure(self):
        self.monitor._monitor.start.return_value = 1

        with patch('acl.rt.set_device', return_value=0):
            with self.assertRaises(RuntimeError) as cm:
                self.monitor.start(device_id=0)

        self.assertIn("failed to start mspti monitor", str(cm.exception))

    def test_kernel_callback_updates_duration(self):
        test_data = MagicMock()
        test_data.end = 200
        test_data.start = 50

        self.monitor._kernel_callback(test_data)
        self.assertEqual(self.monitor.get_task_duration(), 150)
