# msKL 算子 Kernel 轻量化调用快速入门
<br>

## 1. 概述
使用 msKL 工具可以利用其提供的接口在 Python 脚本中快速实现 Kernel 下发的代码生成、编译及运行。
本文档基于入门教程中开发的简易加法算子，演示 msKL 工具的核心功能，帮助初学者直观感受其为算子开发过程带来的高效性与便捷性。

### 1.1 建议
本章节以您已完成<a href="https://gitcode.com/Ascend/msot/blob/master/docs/zh/quick_start/op_tool_quick_start.md" target="_blank">《昇腾算子开发工具链快速入门》</a>的全流程操作为前提；若尚未体验，建议先完成该指南以获得更佳的学习效果。

### 1.2 环境准备
请严格按照<a href="https://gitcode.com/Ascend/msot/blob/master/docs/zh/quick_start/installation_guide.md" target="_blank">《昇腾 AI 算子开发工具链学习环境安装指南》</a>完成环境安装与工作区配置。
即使您已具备类似环境，也需按该指南重新执行一遍，以确保所有依赖组件、环境变量等完整且一致。

## 2. 操作步骤

### 2.1 【环境】运行环境预检

#### 2.1.1 确认 Python 依赖包已安装
执行以下命令，若输出"All is OK"，则表明所需 Python 包及其版本均满足规范：
```shell
python3 -c "import numpy, sympy, scipy, attrs, psutil, decorator; from packaging import version; assert version.parse(numpy.__version__) <= version.parse('1.26.4'); print('All is OK')"
```
若报错，请参照[第 1.2 节](#12-环境准备)进行正确安装。

### 2.2 【前提】算子工程准备完成
按照<a href="https://gitcode.com/Ascend/msot/blob/master/docs/zh/quick_start/op_tool_quick_start.md" target="_blank">《昇腾算子开发工具链快速入门》</a>中的指导，完成2.1节和2.3节。

### 2.3 【轻量调用】Python 脚本中 Kernel 轻量化调用（msKL）

>[!NOTE]说明   
>**知识点：msKPP 接口调用机制简介**   
>1. `mskpp.tiling_func` 接口   
>通过此接口，开发者可指定 Tiling 动态库（.so 文件）与算子类型（op_type），精准调用目标 Tiling 函数；同时，通过传入 inputs_shape、attr 等参数，可灵活构造 TilingContext，实现无需依赖 ACLNN 框架的轻量化 Tiling 调用。   
>Tiling 函数的执行结果包含 blockdim（核函数启动数量）、workspace（工作空间内存）以及序列化的 tiling_data 结构体数据，既可用于 Tiling 逻辑验证，也可作为后续 Kernel 调用的必要输入。      
>2. `mskpp.get_kernel_from_binary` 接口   
>通过此接口，开发者可指定算子的 Kernel 二进制文件（.o 文件）及其函数签名参数，实现 Kernel 的快速加载与调用。
>Kernel 所需的输入/输出张量可直接传入 numpy.array，执行完成后，可立即读取输出张量内容，用于精度比对或功能验证。   
>3. 与其他算子工具链无缝集成   
>开发者仅需通过工具命令直接启动 mskpp Python 脚本即可，例如：`msprof op python3 mskl_demo.py`

#### 2.3.1 开发 Python 调用脚本
执行如下命令：
```shell
cd ~/ot_demo/workspace/src/AddCustom
vi mskl_demo.py
```
按如下内容创建文件 `mskl_demo.py`：
```python
import numpy as np
import mskpp

# 编译生成的 kernel 二进制.o文件在 CANN 中的路径，请更换为实际路径
KERNEL_BINARY_PATH = "/usr/local/Ascend/cann-8.5.0/opp/vendors/customize/op_impl/ai_core/tbe/kernel/ascend910b/add_custom/AddCustom_ab1b6750d7f510985325b603cb06dc8b.o"

# tiling 库在 CANN 中的路径，请更换为实际路径
TILING_LIB_PATH = "/usr/local/Ascend/cann-8.5.0/opp/vendors/customize/op_impl/ai_core/tbe/op_tiling/liboptiling.so"

# 张量形状、数据类型、NPU卡ID
TENSOR_SHAPE = (8, 4096)
TENSOR_DTYPE = np.float16
NPU_ID = 0

def add_custom(a, b, c, workspace, tiling_data):
    kernel = mskpp.get_kernel_from_binary(KERNEL_BINARY_PATH)
    return kernel(a, b, c, workspace, tiling_data, device_id=NPU_ID)


def main():
    """主函数：执行 AddCustom 算子并验证结果正确性。"""

    # 1. 准备输入/输出张量
    a = np.random.randint(1, 5, TENSOR_SHAPE).astype(TENSOR_DTYPE)
    b = np.random.randint(1, 5, TENSOR_SHAPE).astype(TENSOR_DTYPE)
    c = np.zeros(TENSOR_SHAPE, dtype=TENSOR_DTYPE)
    golden = (a + b).astype(TENSOR_DTYPE)

    # 2. 调用 TilingFunc 获取分块策略和工作空间
    tiling_output = mskpp.tiling_func(
        op_type="AddCustom",
        inputs=[a, b],
        outputs=[c],
        lib_path=TILING_LIB_PATH,
    )

    # 3. 执行算子 Kernel
    add_custom(a, b, c, tiling_output.workspace, tiling_output.tiling_data)

    # 4. 验证结果正确性
    result = "success" if np.array_equal(c, golden) else "failed"
    print(f"compare {result}.")


if __name__ == "__main__":
    main()

```

#### 2.3.2 对脚本进行适配
执行如下命令，将查询到的 .o 文件绝对路径填入 `KERNEL_BINARY_PATH` 变量中：
```shell
find $ASCEND_HOME_PATH -name *AddCustom*o
```
执行以下命令，将查询到的 .so 文件绝对路径填入 `TILING_LIB_PATH` 变量中：
```shell
find $ASCEND_HOME_PATH -name liboptiling.so
```

#### 2.3.3 执行脚本，调用算子
>[!CAUTION] 注意   
>请在成功部署算子到 CANN 后再调用，否则会报错。

```shell
python3 mskl_demo.py
```
如果执行成功，输出如下：
```text
root@ubuntu122:~/ot_demo/workspace/src/AddCustom# python3 mskl_demo.py 
[INFO ] Load tiling library /usr/local/Ascend/cann-8.5.0/opp/vendors/customize/op_impl/ai_core/tbe/op_tiling/lib/linux/aarch64/libcust_opmaster_rt2.0.so
[INFO ] Set kernel_type as vec, you can change this value by input [kernel_type] in [mskpp.get_kernel_from_binary] manually.
compare success.
```
如果执行失败或卡住，可能默认的0卡异常，可以尝试修改`mskl_demo.py`中的`NPU_ID`改用其他可用卡。