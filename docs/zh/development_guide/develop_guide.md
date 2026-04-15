# MindStudio Kernel Launcher 开发指南

<br>

## 1. 开发环境准备

请按照以下文档进行环境配置：《[算子工具开发环境安装指导](https://gitcode.com/Ascend/msot/blob/master/docs/zh/common/dev_env_setup.md)》。

## 2. 编译打包

```shell
python build.py
```

## 3. 执行UT测试

```shell
python build.py test
```

如果输出类似如下，且运行的用例数和通过用例数相同，即表示成功：

```text
[----------] 59 tests from CoreApi (8ms total) 
```

```text
========== 59 passed in 2.05s ==========
```
