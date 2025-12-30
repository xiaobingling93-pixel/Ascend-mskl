#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
from logging.handlers import RotatingFileHandler
import os
import re
import sys

from mskl.utils import safe_check

LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
BACKUP_COUNT = 10
MAX_BYTES = 1024 ** 2
pattern_nblank = re.compile('[\r\f\v\t\b\u007F]')
pattern_blank = re.compile(' {2,}')

log_level = os.getenv('MSKL_LOG_LEVEL')
logging.basicConfig(level=logging.DEBUG if log_level == '0' else logging.INFO,
                    format=LOG_FORMAT,
                    datefmt=DATE_FORMAT,
                    stream=sys.stdout)


class RotatingFileHandlerWithPermission(RotatingFileHandler):
    def doRollover(self):
        super().doRollover()
        os.chmod(self.baseFilename, 0o640)


def init_logging_file(filename):
    file_path = os.path.split(filename)[0]
    if not os.path.exists(file_path):
        os.makedirs(file_path, 0o750)
    else:
        safe_check.check_group_others_w_permission(file_path)
        if not safe_check.check_path_owner_consistent(file_path):
            raise PermissionError(f'Path {file_path} is insecure because it does not belong to you.')


    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler = RotatingFileHandlerWithPermission(filename=filename, encoding="utf-8", maxBytes=MAX_BYTES,
                                                     backupCount=BACKUP_COUNT, mode='a')
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)


def log_format(sep, msg):
    msg = pattern_nblank.sub('', str(msg))
    msg = pattern_blank.sub(' ', str(msg))
    return ' ' * sep + str(msg)


def debug(msg):
    logging.debug(log_format(2, msg))


def info(msg):
    logging.info(log_format(3, msg))


def warning(msg):
    logging.warning(log_format(0, msg))


def error(msg):
    logging.error(log_format(2, msg))


def info_without_format(msg):
    logging.info(str(msg))
