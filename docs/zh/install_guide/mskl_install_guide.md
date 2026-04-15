# MindStudio Kernel Launcher 安装指南

<br>

## 1. 二进制安装

MindStudio工具链是集成到CANN包中发布的，可通过以下方式完成安装：

### 方式一：依据 CANN 官方文档安装

请参考《[CANN 官方安装指南](https://www.hiascend.com/cann/download)》，按文档逐步完成安装与配置。

### 方式二：使用 CANN 官方容器镜像

请访问《[CANN 官方镜像仓库](https://www.hiascend.com/developer/ascendhub/detail/17da20d1c2b6493cb38765adeba85884)》，按仓库中的指引完成镜像拉取及容器启动。

## 2. 源码安装

如需使用最新代码的功能，或对源码进行修改以增强功能，可下载本仓库代码，自行编译、打包工具并完成安装。

### 2.1 环境准备

请按照以下文档进行环境配置：《[算子工具开发环境安装指导](https://gitcode.com/Ascend/msot/blob/master/docs/zh/common/dev_env_setup.md)》。

### 2.2 打包whl包

```sh
python3 build.py
```

构建输出：./output/mindstudio_kl-xxxxx.whl

## 2.3 安装whl包

```sh
cd output
pip3 install mindstudio_kl-xxxxx.whl
```

## 3.升级

如需使用whl包替换运行环境原有已安装的whl包，执行如下安装操作：

```sh
pip3 install mindstudio_kl-xxxxx.whl --force-reinstall
```

安装过程中，若提示是否替换原有安装包：
输入"y"，则安装包会自动完成升级操作。

## 4.卸载

卸载则通过如下命令卸载：

```sh
pip3 uninstall mindstudio_kl-xxxxx.whl 
```
