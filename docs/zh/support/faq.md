# 运行Kernel时提示权限错误

## 问题现象

运行Kernel时出现以下报错：

```text
raise PermissionError(f'Path {path} cannot have write permission of group.')
PermissionError: Path /any_path/_gen_module.so cannot have write permission of group.
```

## 原因分析

当前用户创建的文件的默认权限过大（具有group写权限）。

## 解决方案

先使用umask -S命令查询权限配置，再使用umask 0022命令调整权限配置。

```sh
$ umask -S
$ umask 0022
u=rwx,g=rx,o=rx
```
