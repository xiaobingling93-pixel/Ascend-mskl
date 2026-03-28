# MindStudio Kernel Launcher 安装指南

## 1.打包whl包

```sh
python3 build.py
```

构建输出：./output/mindstudio_kl-xxxxx.whl

## 2.安装whl包

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
