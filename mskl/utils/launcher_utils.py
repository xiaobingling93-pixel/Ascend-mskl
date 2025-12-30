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
from mskl.utils.safe_check import FileChecker


def get_cann_path() -> str:
    cann_path = os.getenv('ASCEND_HOME_PATH')
    if cann_path is None or not os.path.isdir(cann_path):
        raise Exception('ASCEND_HOME_PATH is invalid, please check your environment variables')
    return cann_path


def check_runtime_impl():
    cann_path = get_cann_path()
    if os.path.exists(os.path.join(cann_path, "lib64/libruntime.so")):
        import ctypes
        runtime_lib = ctypes.CDLL(os.path.join(cann_path, "lib64/libruntime.so"), mode=ctypes.RTLD_GLOBAL)
        if hasattr(runtime_lib, "rtKernelLaunchWithHandleV2") and callable(getattr(runtime_lib,
                                                                                   "rtKernelLaunchWithHandleV2")):
            return True
    return False
