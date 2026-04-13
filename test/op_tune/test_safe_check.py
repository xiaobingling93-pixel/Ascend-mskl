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
from unittest.mock import patch, MagicMock


from mskl.utils import logger
from mskl.utils.safe_check import *


class TestCheckPathOwnerConsistent(unittest.TestCase):
    def test_owner_consistent(self):
        with patch("os.stat") as mock_stat, patch("os.getuid") as mock_getuid:
            mock_stat.return_value.st_uid = 1000
            mock_getuid.return_value = 1000
            self.assertTrue(check_path_owner_consistent("/dummy/path"))

    def test_owner_inconsistent(self):
        with patch("os.stat") as mock_stat, patch("os.getuid") as mock_getuid:
            mock_stat.return_value.st_uid = 1001
            mock_getuid.return_value = 1000
            self.assertFalse(check_path_owner_consistent("/dummy/path"))


class TestCheckInputFile(unittest.TestCase):
    def test_invalid_file_path(self):
        with patch("os.path.isfile") as mock_isfile:
            mock_isfile.return_value = False
            with self.assertRaisesRegex(OSError, r"/bad/path.* valid file path"):
                check_input_file("/bad/path")

    def test_unreadable_file(self):
        with patch("os.path.isfile") as mock_isfile, \
                patch("os.access") as mock_access:
            mock_isfile.return_value = True
            mock_access.return_value = False
            with self.assertRaisesRegex(PermissionError, "not readable"):
                check_input_file("/unreadable/path")

    def test_insecure_ownership(self):
        with patch("os.path.isfile") as mock_isfile, \
                patch("os.access") as mock_access, \
                patch("os.path.getsize") as mock_get_size, \
                patch("mskl.utils.safe_check.check_path_owner_consistent") as mock_owner_check, \
                patch("mskl.utils.safe_check.check_group_others_w_permission") as mock_group_perm_check, \
                patch.object(logger, "error") as mock_logger_error, \
                patch.object(logger, "warning") as mock_logger_warning:
            mock_isfile.return_value = True
            mock_access.return_value = True
            mock_owner_check.return_value = False
            mock_get_size.return_value = 1
            check_input_file("/insecure/path")
            mock_logger_warning.assert_called()

    def test_valid_file(self):
        with patch("os.path.isfile") as mock_isfile, \
                patch("os.access") as mock_access, \
                patch("os.path.getsize") as mock_get_size, \
                patch("mskl.utils.safe_check.check_path_owner_consistent") as mock_owner_check, \
                patch("mskl.utils.safe_check.check_group_others_w_permission") as mock_other_w_check, \
                patch.object(logger, "error") as mock_logger_error:
            mock_isfile.return_value = True
            mock_access.return_value = True
            mock_owner_check.return_value = True
            mock_get_size.return_value = 1

            check_input_file("/valid/path")
            mock_logger_error.assert_not_called()


class TestCheckOthersWPermission(unittest.TestCase):
    def test_check_group_w_permission(self):
        with patch("os.stat") as mock_stat, patch.object(logger, "warning") as mock_logger_warning:
            mock_stat.return_value.st_mode = 0o720
            check_group_others_w_permission("/insecure/path")
            mock_logger_warning.assert_called()


    def test_check_other_w_permission(self):
        with patch("os.stat") as mock_stat, patch.object(logger, "warning") as mock_logger_warning:
            mock_stat.return_value.st_mode = 0o702
            check_group_others_w_permission("/insecure/path")
            mock_logger_warning.assert_called()
