<h1 align="center">MindStudio Kernel Launcher</h1>

<div align="center">
<h2>昇腾 AI 算子轻量化调用工具</h2>
  
 [![Ascend](https://img.shields.io/badge/Community-MindStudio-blue.svg)](https://www.hiascend.com/developer/software/mindstudio) 
 [![License](https://badgen.net/badge/License/MulanPSL-2.0/blue)](./docs/LICENSE)

</div>

## ✨ 最新消息

* [2025.12.30]：MindStudio Kernel Launcher 项目首次上线

<br>

## ️ ℹ️ 简介

MindStudio Kernel Launcher（算子调用，msKL）具有Kernel轻量化调用的功能。使用msKL工具可以利用提供的接口在Python脚本中快速实现Kernel下发代码生成、编译及运行Kernel。

## ⚙️ 功能介绍

msKL具有调用msOpGen算子工程和基于Ascend C模板库进行自动调优的功能，具体介绍如下：

| 功能名称 | 功能描述  |
|---------|--------|
| **调用msOpGen算子工程** | 提供tiling_func和get_kernel_from_binary接口，可以直接调用msOpGen算子工程。 |
| **自动调优** | 提供模板库Kernel下发代码生成、编译、运行的能力，支持Kernel内代码替换并自动调优。 |

## 🚀 快速入门

以简易加法算子为例，快速体验核心功能，请参见 [《msKL 快速入门》](./docs/zh/quick_start/mskl_quick_start.md)。

## 📦 安装指南

介绍工具的环境依赖与安装方法，请参见 [《msKL 安装指南》](docs/zh/install_guide/mskl_install_guide.md)。

## 📘 使用指南

工具的详细使用方法，请参见 [《msKL 使用指南》](docs/zh/user_guide/mskl_user_guide.md)

## 📚 API参考

请参见 [《msKL 对外接口使用说明》](docs/zh/api_reference/mskl_api_reference.md)。

## ❓ FAQ

常见问题及解决方案，请参见 [《msKL FAQ》](docs/zh/support/faq.md)。

## 🛠️ 贡献指南

若您有意参与项目贡献，请参见 [《贡献指南》](./docs/zh/contributing/contributing_guide.md)。  

## ⚖️ 相关说明

* [《License声明》](./docs/zh/legal/license_notice.md) 
* [《安全声明》](./docs/zh/legal/security_statement.md) 
* [《免责声明》](./docs/zh/legal/disclaimer.md)

## 🤝 建议与交流

欢迎大家为社区做贡献。如果有任何疑问或建议，请提交[Issues](https://gitcode.com/Ascend/mskl/issues)，我们会尽快回复。感谢您的支持。

## 🙏 致谢

本工具由华为公司 **计算产品线** 贡献。    
感谢来自社区的每一个PR，欢迎贡献。
