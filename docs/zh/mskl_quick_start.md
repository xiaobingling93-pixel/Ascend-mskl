# MindStudio Kernel Launcher快速入门

## 简介

本文以单算子00\_basic\_matmul为例，帮助用户快速上手msKL工具的Kernel级自动调优功能。

**环境准备<a name="section78691140142819"></a>**

- 准备Atlas A2 训练系列产品/Atlas 800I A2 推理产品的服务器，并安装对应的驱动和固件，具体安装过程请参见《[CANN 软件安装指南](https://www.hiascend.com/document/detail/zh/canncommercial/83RC1/softwareinst/instg/instg_quick.html?Mode=PmIns&InstallType=local&OS=openEuler&Software=cannToolKit)》中的“安装NPU驱动和固件”章节。
- 安装Ascend-cann-toolkit和ops算子包，请参见《[CANN 软件安装指南](https://www.hiascend.com/document/detail/zh/canncommercial/83RC1/softwareinst/instg/instg_quick.html?Mode=PmIns&InstallType=local&OS=openEuler&Software=cannToolKit)》。
- 若要使用MindStudio Insight进行查看时，需要单独安装MindStudio Insight软件包，具体下载链接请参见《[MindStudio Insight工具用户指南](https://www.hiascend.com/document/detail/zh/mindstudio/82RC1/GUI_baseddevelopmenttool/msascendinsightug/Insight_userguide_0002.html)》的“安装与卸载”章节。

## 操作步骤

1. 执行以下命令，下载[Link](https://gitcode.com/cann/catlass/tree/catlass-v1-stable)中的Ascend C模板库。

    ```shell
    git clone https://gitcode.com/cann/catlass.git -b catlass-v1-stable
    ```

2. 进入模板库中的00_basic_matmul样例代码目录。

    ```shell
    cd catlass/examples/00_basic_matmul
    ```

3. 修改basic_matmul.cpp文件，在L1TileShape、L0TileShape变量声明的行末尾添加注释 （// tunable）。

    ```cpp
    // basic_matmul.cpp
    ...
    51 using L1TileShape = GemmShape<128, 256, 256>; // tunable
    52 using L0TileShape = GemmShape<128, 256, 64>; // tunable
    ...
    ```

4. 将Python脚本文件[basic_matmul_autotune.py](./mskl_user_guide.md/#basic_matmul_autotunepy)与编译脚本文件[jit_build.sh](./mskl_user_guide.md/#jit_buildsh)保存至00_basic_matmul目录中。
5. 运行样例脚本basic_matmul_autotune.py。

    ```python
    $ python3 basic_matmul_autotune.py 
    No.0: 22.562μs, {'L1TileShape': 'GemmShape<128, 256, 256>', 'L0TileShape': 'GemmShape<128, 256, 64>'}
    No.1: 22.109μs, {'L1TileShape': 'GemmShape<128, 256, 128>', 'L0TileShape': 'GemmShape<128, 256, 64>'}
    No.2: 17.778μs, {'L1TileShape': 'GemmShape<128, 128, 256>', 'L0TileShape': 'GemmShape<128, 128, 64>'}
    No.3: 15.378μs, {'L1TileShape': 'GemmShape<64, 128, 128>', 'L0TileShape': 'GemmShape<64, 128, 128>'}
    No.4: 14.982μs, {'L1TileShape': 'GemmShape<64, 128, 256>', 'L0TileShape': 'GemmShape<64, 128, 128>'}
    No.5: 15.671μs, {'L1TileShape': 'GemmShape<64, 128, 512>', 'L0TileShape': 'GemmShape<64, 128, 128>'}
    No.6: 19.592μs, {'L1TileShape': 'GemmShape<64, 64, 128>', 'L0TileShape': 'GemmShape<64, 64, 128>'}
    No.7: 18.340μs, {'L1TileShape': 'GemmShape<64, 64, 256>', 'L0TileShape': 'GemmShape<64, 64, 128>'}
    No.8: 18.541μs, {'L1TileShape': 'GemmShape<64, 64, 512>', 'L0TileShape': 'GemmShape<64, 64, 128>'}
    No.9: 20.652μs, {'L1TileShape': 'GemmShape<128, 128, 128>', 'L0TileShape': 'GemmShape<128, 128, 128>'}
    No.10: 17.728μs, {'L1TileShape': 'GemmShape<128, 128, 256>', 'L0TileShape': 'GemmShape<128, 128, 128>'}
    No.11: 17.637μs, {'L1TileShape': 'GemmShape<128, 128, 512>', 'L0TileShape': 'GemmShape<128, 128, 128>'}
    Best config: No.4
    compare success.
    ```

    以上打印数据表示在算子代码basic_matmul.cpp中，L1TileShape定义为GemmShape<64, 128, 256>且L0TileShape定义为GemmShape<64, 128, 128>时，性能最优。

