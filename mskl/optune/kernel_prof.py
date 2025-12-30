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

from mskl.utils import logger


class Monitor:
    """A context manager for monitoring kernel execution via MSPTI."""

    def __init__(self):
        import mspti
        self._mspti = mspti
        self._monitor = self._mspti.KernelMonitor()
        self._durations = []

    def get_task_duration(self):
        logger.debug("Self._durations = {}".format(self._durations))
        return sum(self._durations)

    def get_last_n_task_duration(self, n: int):
        logger.debug("Self._durations = {}".format(self._durations))
        logger.debug("Last {} task durations = {}".format(n, self._durations[-n:]))
        return sum(self._durations[-n:])

    def start(self, device_id):
        import acl
        self._durations.clear()
        acl.init()
        ret = acl.rt.set_device(device_id)
        if ret != 0:
            raise RuntimeError(f'Set device failed, error code: {ret}')
        result = self._monitor.start(self._kernel_callback)
        if result != self._mspti.MsptiResult.MSPTI_SUCCESS:
            raise RuntimeError(f'failed to start mspti monitor, error code: {result}.')

    def stop(self, device_id):
        import acl
        acl.finalize()
        self._monitor.flush_all()
        result = self._monitor.stop()
        if result != self._mspti.MsptiResult.MSPTI_SUCCESS:
            raise RuntimeError(f'failed to stop mspti monitor, error code: {result}')

    def _kernel_callback(self, data):
        duration = data.end - data.start
        self._durations.append(duration)
