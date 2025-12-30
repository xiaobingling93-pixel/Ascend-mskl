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
from unittest.mock import patch
import os
from copy import deepcopy
from mskl.optune.kernel_modifier import Replacer


class TestReplacer(unittest.TestCase):
    def setUp(self):
        # 模拟文件内容
        self.kernel_file_content = [
            "using ArchTag = actlass::arch::AscendV220;\n",
            "    using ElementA = half;\n",
            "    using LayoutA = actlass::layout::RowMajor; // tunable\n",
            "    using ElementB = half;\n",
            "    using LayoutB = actlass::layout::RowMajor;\n",
            "    using ElementC = half;\n",
            "    using LayoutC = actlass::layout::RowMajor;\n",
            "    using ElementAccumulator = float;\n",
            "\n",
            "    using StoreOpClass = actlass::epilogue::process::StoreOp<ArchTag, ElementAccumulator, ElementC, LayoutC,\n",
            "        actlass::epilogue::process::QuantGranularity::NO_QUANT, false>;\n",
            "    using GemmKernel = typename actlass::gemm::kernel::DefaultGemm<\n",
            "        ElementA,\n",
            "        LayoutA,\n",
            "        ElementB,\n",
            "        LayoutB,\n",
            "        ElementC,\n",
            "        LayoutC,\n",
            "        ElementAccumulator,\n",
            "        ArchTag,\n",
            "        actlass::arch::OpClassCube,\n",
            "        actlass::arch::OpMultiplyAdd,\n",
            "        actlass::gemm::GemmShape<128, 256, 256>, // tunable: L0C_Tile_Shape\n",
            "        actlass::gemm::GemmShape<128, 256, 64>,\n",
            "        void,\n",
            "        void,\n",
            "        StoreOpClass,\n",
            "        actlass::epilogue::block::InterimTargetType::GM_DESTINATION,\n",
            "        void,\n",
            "        actlass::epilogue::block::InterimTargetType::UNDEFINED,\n",
            "        void,\n",
            "        void,\n",
            "        typename actlass::gemm::block::GemmIdentityBlockSwizzle<>\n",
            "    >::GemmKernel;\n",
        ]
        # 模拟文件路径
        self.kernel_file_path = "test_kernel.cpp"
        self.output_file_path = "test_output.cpp"
        self.output_file_path_case_2 = "test_output_2.cpp"

    def tearDown(self):
        # 清理生成的测试文件
        if os.path.exists(self.output_file_path):
            os.remove(self.output_file_path)

    @patch("mskl.utils.autotune_utils.get_file_lines")
    def test_replace_config(self, mock_get_file_lines):
        # 模拟 get_file_lines 返回内容
        mock_get_file_lines.return_value = deepcopy(self.kernel_file_content)

        # 创建 Replacer 实例
        replacer = Replacer(self.kernel_file_path)

        # 定义替换节点
        node = {
            "LayoutA": "actlass::xxx",
            "L0C_Tile_Shape": "<128, 128, 128>,",
        }

        # 调用替换方法
        replacer.replace_config(node, self.output_file_path)

        # 验证文件内容是否正确替换
        with open(self.output_file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
            self.assertEqual(lines[2], '    using LayoutA = actlass::xxx;\n')
            self.assertEqual(lines[22], '        <128, 128, 128>,\n')

        # 验证文件权限是否正确
        self.assertEqual(os.stat(self.output_file_path).st_mode & 0o777, 0o640)

    @patch("mskl.utils.autotune_utils.get_file_lines")
    def test_replace_src_with_config(self, mock_get_file_lines):
        # 模拟 get_file_lines 返回内容
        mock_get_file_lines.return_value = deepcopy(self.kernel_file_content)

        # 定义替换节点
        config = {
            "LayoutA": "actlass::xxx",
            "L0C_Tile_Shape": "<128, 128, 128>,",
        }

        # 调用替换方法
        Replacer.replace_src_with_config(self.kernel_file_path, self.output_file_path_case_2, config)

        # 验证文件内容是否正确替换
        with open(self.output_file_path_case_2, "r", encoding="utf-8") as file:
            lines = file.readlines()
            self.assertEqual(lines[2], '    using LayoutA = actlass::xxx;\n')
            self.assertEqual(lines[22], '        <128, 128, 128>,\n')

        # 验证文件权限是否正确
        self.assertEqual(os.stat(self.output_file_path_case_2).st_mode & 0o777, 0o640)

    @patch("mskl.utils.autotune_utils.get_file_lines")
    def test_write_to_file(self, mock_get_file_lines):
        # 模拟 get_file_lines 返回内容
        mock_get_file_lines.return_value = deepcopy(self.kernel_file_content)

        # 创建 Replacer 实例
        replacer = Replacer(self.kernel_file_path)

        # 测试写入文件
        lines = deepcopy(self.kernel_file_content)
        replacer._write_to_file(lines, self.output_file_path)

        # 验证文件内容和权限
        with open(self.output_file_path, "r", encoding="utf-8") as file:
            self.assertEqual(file.readlines(), lines)
        self.assertEqual(os.stat(self.output_file_path).st_mode & 0o777, 0o640)


if __name__ == "__main__":
    unittest.main()
