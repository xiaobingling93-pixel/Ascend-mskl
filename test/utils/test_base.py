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
import re
import os
import shutil

from mskl.utils import logger


class TestBase(unittest.TestCase):
    work_dir = '.'
    def setUp(self):
        self.clean()

    def tearDown(self):
        self.clean()

    def clean(self):
        self.batch_delete_folders(self.work_dir, '^MSKL_*')

    def batch_delete_folders(self, directory, pattern):
        for root, dirs, files in os.walk(directory):
            for dir in dirs:
                if re.match(pattern, dir):
                    dir_path = os.path.join(root, dir)
                    try:
                        shutil.rmtree(dir_path)
                        logger.debug(f"Folder {dir_path} has been deleted")
                    except OSError as e:
                        logger.error(f"Fail to delete {dir_path} : {e}")
        logger.info("Delete folder success")