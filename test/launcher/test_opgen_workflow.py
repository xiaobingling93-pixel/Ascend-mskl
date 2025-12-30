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
import shutil
import numpy as np
import unittest
from unittest.mock import patch, Mock

from mskl.launcher.opgen_workflow import TilingOutput, tiling_func, get_kernel_from_binary, TMP_FOLDER
from mskl.utils import safe_check
from mskl.launcher.context import context

tiling_dict = {
    "blockdim": 8,
    "workspace_size": 64,
    "tiling_data": [1,2,3,4],
    "tiling_key": 1111,
}


def mock_tiling_func():
    return tiling_dict


class TestOpgenWorkflow(unittest.TestCase):
    LIB = 'test_tiling.so'
    CPP = '_mskl_gen_tiling.cpp'
    TIL_LIB = '_mskl_gen_tiling.so'
    KERNEL_CPP = '_mskl_gen_binary_launch.cpp'
    KERNEL_LIB = '_mskl_gen_binary_module.so'
    KERNEL_BINARY_PATH = 'kernel.o'

    @classmethod
    def setUpClass(cls):
        with os.fdopen(os.open(TestOpgenWorkflow.LIB,
                               safe_check.OPEN_FLAGS,
                               safe_check.SAVE_DATA_FILE_AUTHORITY),
                       'w') as f:
            f.truncate()
            f.write('this is a test so')
        with os.fdopen(os.open(TestOpgenWorkflow.KERNEL_BINARY_PATH,
                               safe_check.OPEN_FLAGS,
                               safe_check.SAVE_DATA_FILE_AUTHORITY),
                       'w') as f:
            f.truncate()
            f.write('this is a test kernel binary file')

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TMP_FOLDER):
            shutil.rmtree(TMP_FOLDER, ignore_errors=True)
        if os.path.exists(TestOpgenWorkflow.LIB):
            os.remove(TestOpgenWorkflow.LIB)
        if os.path.exists(TestOpgenWorkflow.CPP):
            os.remove(TestOpgenWorkflow.CPP)
        if os.path.exists(TestOpgenWorkflow.TIL_LIB):
            os.remove(TestOpgenWorkflow.LIB)
        if os.path.exists(TestOpgenWorkflow.KERNEL_BINARY_PATH):
            os.remove(TestOpgenWorkflow.KERNEL_BINARY_PATH)
        if os.path.exists(TestOpgenWorkflow.KERNEL_CPP):
            os.remove(TestOpgenWorkflow.KERNEL_CPP)
        if os.path.exists(TestOpgenWorkflow.KERNEL_LIB):
            os.remove(TestOpgenWorkflow.KERNEL_LIB)

    @patch("mskl.launcher.opgen_workflow.compile_tiling")
    def test_tiling_func_execute_success(self, mock_compile_tiling):
        # 消除对cann的编译依赖
        mock_compile_tiling.return_value = mock_tiling_func

        a = np.random.uniform(1, 100, [2, 32]).astype(np.float16)
        b = np.random.uniform(1, 100, [2, 32]).astype(np.float16)
        c = np.zeros([2, 32]).astype(np.float16)
        inputs_info = [{"shape": [2, 32], "dtype": "float16", "format": "ND"},
                       {"shape": [2, 32], "dtype": "float16", "format": "ND"}]
        outputs_info = [{"shape": [2, 32], "dtype": "float16", "format": "ND"}]
        output = tiling_func(
            op_type="AddCustom",
            inputs_info=inputs_info, outputs_info=outputs_info,
            inputs=[a, b], outputs=[c],
            attr={
                "a1": 1,
                "a2": False,
                "a3": "ssss",
                "a4": 1.2,
                "a5": [111.111, 111.222, 111.333],
                "a6": [True, False],
                "a7": ["asdf", "zxcv"],
                "a8": [[1, 2, 3, 4], [5, 6, 7, 8], [5646, 2345]],
                "a9": [111, 222, 333]
            },
            lib_path=TestOpgenWorkflow.LIB
        )
        mock_compile_tiling.assert_called_once()
        self.assertEqual(output.blockdim, TilingOutput(tiling_dict).blockdim)

    @patch("mskl.launcher.opgen_workflow.compile_tiling")
    def test_tiling_func_with_list_attr_tensor_list_execute_success(self, mock_compile_tiling):
        # 消除对cann的编译依赖
        mock_compile_tiling.return_value = mock_tiling_func

        a = np.random.uniform(1, 100, [2, 32]).astype(np.float16)
        b = np.random.uniform(1, 100, [2, 32]).astype(np.float16)
        c = np.zeros([2, 32]).astype(np.float16)
        inputs_info = [[{"shape": [2, 32], "dtype": "float16", "format": "ND"},
                        {"shape": [2, 32], "dtype": "float16", "format": "ND"},
                        {"shape": [2, 32], "dtype": "float16", "format": "ND"}],
                       {"shape": [2, 32], "dtype": "float16", "format": "ND"},
                       ]
        outputs_info = [{"shape": [2, 32], "dtype": "float16", "format": "ND"}]
        output = tiling_func(
            op_type="AddCustom",
            inputs_info=inputs_info, outputs_info=outputs_info,
            inputs=[[a, a, b], b], outputs=[c],
            attr=[
                {"name": "a1", "dtype": "int", "value": 1},
                {"name": "a2", "dtype": "bool", "value": False},
                {"name": "a3", "dtype": "str", "value": "ssss"},
                {"name": "a3_1", "dtype": "string", "value": "ssss"},
                {"name": "a4", "dtype": "float", "value": 1.2},
                {"name": "a5", "dtype": "list_float", "value": [111.111, 111.222, 111.333]},
                {"name": "a6", "dtype": "list_bool", "value": [True, False]},
                {"name": "a7", "dtype": "list_str", "value": ["asdf", "zxcv"]},
                {"name": "a7_1", "dtype": "list_string", "value": ["asdf", "zxcv"]},
                {"name": "a8", "dtype": "list_list_int", "value": [[1, 2, 3, 4], [5, 6, 7, 8], [5646, 2345]]},
                {"name": "a9", "dtype": "list_int", "value": [111, 222, 333]},
                {"name": "a10", "dtype": "list_int", "value": []},
                {"name": "a11", "dtype": "int64", "value": 2},
                {"name": "a12", "dtype": "float32", "value": 1.3},
            ],
            lib_path=TestOpgenWorkflow.LIB
        )
        mock_compile_tiling.assert_called_once()
        self.assertEqual(output.blockdim, TilingOutput(tiling_dict).blockdim)

    @patch("mskl.launcher.opgen_workflow.compile_kernel_binary")
    def test_get_kernel_from_binary_execute_success(self, mock_compile_kernel_binary):
        with patch('mskl.utils.launcher_utils.check_runtime_impl', return_value=True):
            with patch('mskl.utils.launcher_utils.get_cann_path', return_value=""):
                mock_compile_kernel_binary.return_value = None
                context.tiling_output = TilingOutput(tiling_dict)
                context.op_type = 'TestOpType'

                kernel = get_kernel_from_binary(TestOpgenWorkflow.KERNEL_BINARY_PATH, 'mix')
                mock_compile_kernel_binary.assert_called_once()
                self.assertEqual(kernel, None)
