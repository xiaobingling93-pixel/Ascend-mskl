# MindStudio Kernel Launcher安装指南

# 安装说明
MindStudio Kernel Launcher（算子调用，msKL）具有Kernel轻量化调用的功能。使用msKL工具可以利用提供的接口在Python脚本中快速实现Kernel下发代码生成、编译及运行Kernel。本文主要介绍msKL工具的安装方法。  



# 安装步骤

## 打包whl包
```
python setup.py bdist_wheel
注：也可通过执行一键式脚本完成：python build.py
```
构建输出：mindstudio_kl-version-arch.whl

## 安装whl包
```
cd output
pip install mindstudio_kl-xxxxx.whl
```

## 卸载
卸载则通过如下命令卸载：
```
pip uninstall mindstudio_kl-xxxxx.whl 
```

## 升级
如需使用whl包替换运行环境原有已安装的whl包，执行如下安装操作：
```
pip install mindstudio_kl-xxxxx.whl --force-reinstall
```
安装过程中，若提示是否替换原有安装包：
输入"y"，则安装包会自动完成升级操作。


## 测试用例执行，生成覆盖率报告
```
python build.py test // 执行测试用例，生成覆盖率报告
```