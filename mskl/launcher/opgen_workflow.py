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
import numpy as np
from .config import TilingConfig, KernelBinaryInvokeConfig
from .code_generator import Launcher
from .compiler import compile_tiling, compile_kernel_binary, CompiledKernel
from .context import context
from ..utils.safe_check import FileChecker, DATA_DIRECTORY_AUTHORITY
from ..utils import logger

TILING_FUNC_CNT = 0
GET_KERNEL_FROM_BINARY_CNT = 0
TMP_FOLDER = 'mindstudio_mskl_gen'


def init_tmp_folder():
    path = os.path.abspath(TMP_FOLDER)
    if os.path.exists(path):
        checker = FileChecker(path, 'dir')
        if not checker.check_input_file():
            raise PermissionError(f'{path} check permission failed, please delete it first')
    os.makedirs(path, mode=DATA_DIRECTORY_AUTHORITY, exist_ok=True)
    return path


class TilingOutput:
    def __init__(self, tiling_output: dict):
        self.blockdim = tiling_output["blockdim"]
        # for printf
        self.workspace_size = tiling_output["workspace_size"] + 75 * 1024 * 1024
        self.workspace = np.zeros(self.workspace_size).astype(np.uint8)
        self.tiling_data = np.array(tiling_output["tiling_data"], dtype=np.uint8)
        self.tiling_key = tiling_output["tiling_key"]


def tiling_func(op_type: str, inputs: list = None, outputs: list = None, lib_path: str = None,
                inputs_info: list = None, outputs_info: list = None, attr=None,
                soc_version: str = None) -> TilingOutput:
    global TILING_FUNC_CNT
    TILING_FUNC_CNT += 1
    config = TilingConfig(op_type, inputs, outputs, lib_path, inputs_info, outputs_info, attr, soc_version)
    tmp_path = init_tmp_folder()
    cpp_path = os.path.join(tmp_path, f'_mskl_gen_tiling.{TILING_FUNC_CNT}.cpp')
    Launcher(config).code_gen(cpp_path)
    so_path = os.path.join(tmp_path, f'_mskl_gen_tiling.{TILING_FUNC_CNT}.so')
    run_tiling_func = compile_tiling(cpp_path, so_path)
    tiling_output = run_tiling_func()
    if tiling_output is None:
        raise Exception('Call tiling_func failed')
    output = TilingOutput(tiling_output)
    context.tiling_output = output
    context.op_type = config.op_type
    logger.debug(f'Call tiling_func {TILING_FUNC_CNT} success, op_type is {op_type}')
    return output


def get_kernel_from_binary(kernel_binary_file: str, kernel_type: str = None, tiling_key: int = None) -> CompiledKernel:
    """
    :param kernel_binary_file: path of kernel.o
    :param kernel_type: ['mix', 'cube', 'vec']
    :param tiling_key: None will use tiling_func()'s return value
    :return: CompiledKernel
    """
    global GET_KERNEL_FROM_BINARY_CNT
    GET_KERNEL_FROM_BINARY_CNT += 1
    config = KernelBinaryInvokeConfig(kernel_binary_file, kernel_type, tiling_key)
    tmp_path = init_tmp_folder()
    context.opgen_tmp_dir_path = tmp_path
    cpp_path = os.path.join(tmp_path, f'_mskl_gen_binary_launch.{GET_KERNEL_FROM_BINARY_CNT}.cpp')
    Launcher(config).code_gen(cpp_path)
    so_path = os.path.join(tmp_path, f'_mskl_gen_binary_module.{GET_KERNEL_FROM_BINARY_CNT}.so')
    kernel = compile_kernel_binary(cpp_path, so_path)
    logger.debug(f'Call get_kernel_from_binary {GET_KERNEL_FROM_BINARY_CNT} success, '
                 f'kernel path is {kernel_binary_file}')
    return kernel
