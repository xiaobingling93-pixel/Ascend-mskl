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

from mskl import mmad, Tensor, Chip


def my_mmad(gm_x, gm_y, gm_z):
    # 矩阵乘的基本数据通路：
    # 左矩阵x：GM-L1-L0A
    # 右矩阵y：GM-L1-L0B
    # 结果矩阵z： L0C(初始化)-GM
    # 样例数学表达式：z = x @ y + b

    # 定义和分配L1上的变量
    l1_x = Tensor("L1")
    l1_y = Tensor("L1")

    # 定义和分配L0A和L0B上的变量
    x = Tensor("L0A")
    y = Tensor("L0B")

    # 定义和分配在L0C上的偏置项，理论上应该分配在累加器Buffer上，分配在L0C不影响性能
    b = Tensor("L0C", "FP32", [32, 16], format="NC1HWC0")

    # 将GM上的数据移动到L1对应内存空间上
    l1_x.load(gm_x)
    l1_y.load(gm_y)

    # 将L1上的左右矩阵移动到L0A和L0B上
    x.load(l1_x)
    y.load(l1_y)

    # 当前数据已加载到L0A和L0B上，调用指令进行计算，结果保存在L0C上，out是mmad函数内部在L0C中分配的变量
    out = mmad(x, y, b, True)()

    # 将L0C上的数据移动到GM变量gm_z的地址空间上
    gm_z.load(out[0])
    return gm_z


if __name__ == '__main__':
    with Chip("Ascend910B1") as chip:
        chip.enable_trace() # 使能算子模拟流水图的功能，生成trace.json文件
        chip.enable_metrics() # 使能单指令及分PIPE的流水信息，生成Instruction_statistic.csv和Pipe_statistic.csv文件

        # 模拟一个大矩阵被切分成5个小矩阵进行计算
        for _ in range(5):
            # 应用算子进行AICORE计算
            in_x = Tensor("GM", "FP16", [32, 48], format="ND")
            in_y = Tensor("GM", "FP16", [48, 16], format="ND")
            in_z = Tensor("GM", "FP32", [32, 16], format="NC1HWC0")
            my_mmad(in_x, in_y, in_z)
