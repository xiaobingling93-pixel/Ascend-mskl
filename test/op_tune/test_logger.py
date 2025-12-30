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

import logging
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock

from mskl.utils.logger import (
    RotatingFileHandlerWithPermission,
    init_logging_file,
    error,
    info_without_format
)


class TestRotatingFileHandler(unittest.TestCase):
    @patch("os.chmod")
    def test_do_rollover_permission(self, mock_chmod):
        handler = RotatingFileHandlerWithPermission("test.log", mode='a')
        with patch.object(handler, "baseFilename", "test.log"):
            handler.doRollover()
            mock_chmod.assert_called_once_with("test.log", 0o640)
        handler.close()


class TestLoggingFunctions(unittest.TestCase):
    def setUp(self):
        self.log_stream = StringIO()
        self.original_handlers = logging.getLogger().handlers.copy()
        logging.getLogger().handlers = []
        handler = logging.StreamHandler(self.log_stream)
        logging.getLogger().addHandler(handler)
        global progress_info
        progress_info = ''

    def tearDown(self):
        logging.getLogger().handlers = self.original_handlers

    @patch("logging.error")
    def test_error_logging(self, mock_error):
        error("Test error")
        mock_error.assert_called_once()
        args = mock_error.call_args[0][0]
        self.assertTrue(args.startswith('  '))


class TestInitLoggingFile(unittest.TestCase):
    @patch("os.makedirs")
    @patch("logging.getLogger")
    @patch("builtins.open", new_callable=MagicMock)  # 新增文件操作mock
    def test_init_logging_file(self, mock_open, mock_get_logger, mock_makedirs):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # 使用真实路径验证逻辑
        test_path = "/var/log/test/app.log"

        # 执行初始化
        init_logging_file(test_path)

        # 验证目录创建
        mock_makedirs.assert_called_once_with("/var/log/test", 0o750)

        # 验证处理器添加
        mock_logger.addHandler.assert_called_once()
        handler = mock_logger.addHandler.call_args[0][0]

        # 验证处理器类型和参数
        self.assertIsInstance(handler, RotatingFileHandlerWithPermission)
        self.assertEqual(handler.baseFilename, test_path)
        self.assertEqual(handler.mode, 'a')
        self.assertEqual(handler.encoding, 'utf-8')
        self.assertEqual(handler.maxBytes, 1024 ** 2)
        self.assertEqual(handler.backupCount, 10)


class TestInfoWithoutFormat(unittest.TestCase):
    @patch("logging.info")
    def test_direct_logging(self, mock_info):
        info_without_format("Raw message")
        mock_info.assert_called_once_with("Raw message")
