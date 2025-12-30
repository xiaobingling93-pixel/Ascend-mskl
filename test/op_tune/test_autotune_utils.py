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
import sys
import unittest
from unittest.mock import MagicMock
from mskl.utils.safe_check import OPEN_FLAGS, SAVE_DATA_FILE_AUTHORITY


class TestAutotuneUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        mock_mspti = MagicMock()
        mock_mspti.KernelData = MagicMock()
        mock_mspti.KernelMonitor = MagicMock()
        mock_mspti.MsptiResult = MagicMock()
        sys.modules['mspti'] = mock_mspti
        from mskl.utils import autotune_utils
        cls.autotune_utils = autotune_utils

    def test_check_configs(self):
        nodes1 = {'L1TileShape': 'MatmulShape<256, 256, 256>', 'L0TileShape': 'MatmulShape<256, 256, 64>'}
        self.assertRaises(ValueError, self.autotune_utils.check_configs, nodes1)
        nodes2 = [{'L1TileShape': 'MatmulShape<256, 256, 256>', 'L0TileShape': 'MatmulShape<256, 256, 64>'}]
        self.assertEqual(self.autotune_utils.check_configs(nodes2), None)
        nodes3 = [{'L1TileShape': 'MatmulShape<256, 256, 256>', 'L0TileShape': 'MatmulShape<256, 256, 64>'},
                  {'L1TileShape': 'MatmulShape<256, 256, 256>', 1: 'MatmulShape<256, 256, 64>'}, ]
        self.assertRaises(ValueError, self.autotune_utils.check_configs, nodes3)

    def test_check_warmup(self):
        self.assertEqual(self.autotune_utils.check_warmup(100), None)
        self.assertEqual(self.autotune_utils.check_warmup(600), None)
        self.assertRaises(ValueError, self.autotune_utils.check_warmup, 0)
        self.assertRaises(ValueError, self.autotune_utils.check_warmup, 10 ** 5 + 1)

    def test_check_device_ids(self):
        self.assertEqual(self.autotune_utils.check_device_ids([0]), None)
        self.assertEqual(self.autotune_utils.check_device_ids([0,1]), None)
        self.assertRaises(ValueError, self.autotune_utils.check_device_ids, [0,1] * 200)

    def test_check_repeat(self):
        self.assertEqual(self.autotune_utils.check_repeat(10), None)
        self.assertRaises(ValueError, self.autotune_utils.check_repeat, 0)
        self.assertRaises(ValueError, self.autotune_utils.check_repeat, 10 ** 4 + 1)

    def test_check_autotune_params(self):
        nodes = [{'L1TileShape': 'MatmulShape<256, 256, 256>', 'L0TileShape': 'MatmulShape<256, 256, 64>'}]
        self.assertEqual(self.autotune_utils.check_autotune_params(nodes, 300, 10, [2]), None)

    def test_check_autotune_v2_params(self):
        normal_configs = [{'L1TileShape': 'MatmulShape<256, 256, 256>', 'L0TileShape': 'MatmulShape<256, 256, 64>'}]
        self.assertEqual(self.autotune_utils.check_autotune_v2_params(normal_configs, 5), None)
        self.assertRaises(ValueError, self.autotune_utils.check_autotune_v2_params, normal_configs, 501)
        self.assertRaises(ValueError, self.autotune_utils.check_autotune_v2_params, normal_configs, -1)
        self.assertRaises(ValueError, self.autotune_utils.check_autotune_v2_params, 1, 5)
        self.assertRaises(ValueError, self.autotune_utils.check_autotune_v2_params, [1], 5)
        self.assertRaises(ValueError, self.autotune_utils.check_autotune_v2_params, [{1: '1'}], 5)
        self.assertRaises(ValueError, self.autotune_utils.check_autotune_v2_params, [{None: '1'}], 5)
        self.assertRaises(ValueError, self.autotune_utils.check_autotune_v2_params, [{'1': 1}], 5)
        self.assertRaises(ValueError, self.autotune_utils.check_autotune_v2_params, [{'1': None}], 5)

    def test_get_file_lines(self):
        not_exist_file = '/test/not_exist_file.cpp'
        self.assertRaises(OSError, self.autotune_utils.get_file_lines, not_exist_file)
        file_name = 'test.cpp'
        with os.fdopen(os.open(file_name, OPEN_FLAGS, SAVE_DATA_FILE_AUTHORITY), 'w', encoding='utf-8') as f:
            f.write('''__global__[aicore] void Gemm(__gm__ uint8_t *gm_a, __gm__ uint8_t *gm_b, __gm__ uint8_t *gm_c) {
    using ArchTag = actlass::arch::AscendV220;
    using ElementA = half;
    using LayoutA = actlass::layout::RowMajor; // tunable
    using ElementB = half;
    using LayoutB = actlass::layout::RowMajor;
    using ElementC = half;
    using LayoutC = actlass::layout::RowMajor;
    using ElementAccumulator = float;

    using StoreOpClass = actlass::epilogue::process::StoreOp<ArchTag, ElementAccumulator, ElementC, LayoutC,
        actlass::epilogue::process::QuantGranularity::NO_QUANT, false>;
    using GemmKernel = typename actlass::gemm::kernel::DefaultGemm<
        ElementA,
        LayoutA, // tunable
        ElementB,
        LayoutB,
        ElementC,
        LayoutC,
        ElementAccumulator,
        ArchTag,
        actlass::arch::OpClassCube,
        actlass::arch::OpMultiplyAdd,
        actlass::gemm::GemmShape<128, 256, 256>, // tunable: L0C_Tile_Shape
        actlass::gemm::GemmShape<128, 256, 64>,
        void,
        void,
        StoreOpClass,
        actlass::epilogue::block::InterimTargetType::GM_DESTINATION,
        void,
        actlass::epilogue::block::InterimTargetType::UNDEFINED,
        void,
        void,
        typename actlass::gemm::block::GemmIdentityBlockSwizzle<>
    >::GemmKernel;


    using GemmKernel = typename actlass::gemm::kernel::DefaultGemm<
        ElementA,
        LayoutA, // tunable
        actlass::gemm::GemmShape<128, 256, 256>, // tunable: L0C_Tile_Shape
        actlass::gemm::GemmShape<128, 256, 64>,
    >::GemmKernel;

    using GemmKernel = typename actlass::gemm::kernel::DefaultGemm<
        ElementA,
        LayoutA, // tunable
        actlass::gemm::GemmShape<128, 256, 256>, // tunable: L0C_Tile_Shape
        actlass::gemm::GemmShape<128, 256, 64>>
        ::GemmKernel;

    GemmKernel gemmKernel;

    actlass::gemm::GemmCoord problemSize(length_m, length_n, length_k);
    typename GemmKernel::LayoutA layoutA(length_m, length_k, length_k);
    typename GemmKernel::LayoutB layoutB(length_k, length_n, length_n);
    typename GemmKernel::LayoutC layoutC(length_m, length_n, length_n);
    typename GemmKernel::Params params{ problemSize, gm_a, layoutA, gm_b, layoutB, { gm_c, layoutC } };
    gemmKernel(params);

}''')
        with open(file_name, 'r', encoding='utf-8') as file_handler:
            lines = file_handler.readlines()
        self.assertEqual(self.autotune_utils.get_file_lines(file_name), lines)
        os.remove(file_name)
