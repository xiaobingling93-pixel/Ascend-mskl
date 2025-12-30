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

from mskl import vadd, Tensor, Chip


def my_vadd(gm_x, gm_y, gm_z):
    # 向量Add的基本数据通路：
    # 被加数x：GM-UB
    # 加数y：GM-UB
    # 结果向量z： UB-GM

    # 定义和分配UB上的变量
    x = Tensor("UB")
    y = Tensor("UB")
    z = Tensor("UB")

    # 将GM上的数据移动到UB对应内存空间上
    x.load(gm_x)
    y.load(gm_y)

    # 当前数据已加载到UB上，调用指令进行计算，结果保存在UB上
    out = vadd(x, y, z)()

    # 将UB上的数据移动到GM变量gm_z的地址空间上
    gm_z.load(out[0])


if __name__ == '__main__':
    with Chip("Ascend910B1") as chip:
        chip.enable_trace()
        chip.enable_metrics()

        # 应用算子进行AICORE计算
        in_x = Tensor("GM", "FP16", [32, 48], format="ND")
        in_y = Tensor("GM", "FP16", [32, 48], format="ND")
        in_z = Tensor("GM", "FP16", [32, 48], format="ND")
        my_vadd(in_x, in_y, in_z)
