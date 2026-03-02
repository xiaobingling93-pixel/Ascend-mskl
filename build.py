#!/usr/bin/python3
# -*- coding: utf-8 -*-
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
import argparse
import glob
import logging
import os
import subprocess
import sys
import traceback
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class BuildManager:
    """
    统一构建管理：依赖拉取 → 编译出包 / 单元测试。

    用法:
        python build.py                  完整构建（拉取依赖 + 打包 whl）
        python build.py local            本地构建（跳过依赖拉取, 打包 whl）
        python build.py test             单元测试（拉取依赖 + 执行 pytest）
        python build.py test local       单元测试（跳过依赖拉取, 执行 pytest）
        python build.py -r <revision>    指定依赖的内部源码仓(例如msopcom)的 Git 分支/标签/commit

    参数说明:
        - 参数: command : 构建动作: 为空时为全构建, local 为跳过依赖下载, test 为运行单元测试。
        - 参数: -r, --revision : 指定 Git 修订版本或标签用于依赖检出。
    """

    def __init__(self):
        self.project_root = Path(__file__).resolve().parent
        argument_parser = argparse.ArgumentParser(description='Build the project and optionally run tests.')
        argument_parser.add_argument('command', nargs='*', default=[],
                                     choices=[[], 'local', 'test'],
                                     help='Build action: omit for full build, "local" to skip dependency download, "test" to run unit tests')
        argument_parser.add_argument('-r', '--revision',
                                     help='Specify Git revision for internal dependent repo (e.g., msopcom).')
        self.parsed_arguments = argument_parser.parse_args()

    def _execute_command(self, command_sequence, timeout_seconds=36000, cwd=None, env=None):
        logging.info("Running: %s", " ".join(command_sequence))
        subprocess.run(command_sequence, timeout=timeout_seconds, check=True, cwd=cwd, env=env)

    def _run_unit_tests(self):
        unit_test_build_dir = self.project_root / "build_ut"
        unit_test_build_dir.mkdir(exist_ok=True)
        os.chdir(unit_test_build_dir)

        env = os.environ.copy()
        env['PYTHONPATH'] = str(self.project_root) + os.pathsep + env.get('PYTHONPATH', '')
        env['PYTHONPYCACHEPREFIX'] = str(unit_test_build_dir)

        report_dir = unit_test_build_dir / "report"
        test_cmd = [
            "coverage3", "run", "--branch",
            "--source=" + str(self.project_root),
            "-m", "pytest",
            str(self.project_root / "test" / "launcher"),
            str(self.project_root / "test" / "op_tune"),
            "--junitxml=" + str(report_dir / "final.xml"),
            "-W", "ignore::DeprecationWarning",
        ]

        logging.info("============ start to execute Python code UT test ============")
        self._execute_command(test_cmd, env=env)
        self._execute_command(["coverage3", "xml", "-o", str(report_dir / "coverage.xml")], env=env)
        self._execute_command(["coverage3", "html", "-d", str(report_dir)], env=env)
        self._execute_command(["coverage3", "report", "-m"], env=env)

    def _run_product_build(self):
        output_dir = self.project_root / "output"
        output_dir.mkdir(mode=0o750, exist_ok=True)

        self._execute_command([
            sys.executable, "setup.py", "bdist_wheel",
            "--dist-dir", str(output_dir),
        ])

        for whl in glob.glob(str(output_dir / "mskl*.whl")):
            os.chmod(whl, 0o550)
    
    def run(self):
        os.chdir(self.project_root)

        if 'test' in self.parsed_arguments.command:
            self._run_unit_tests()
        else:
            self._run_product_build()


if __name__ == "__main__":
    try:
        BuildManager().run()
    except Exception:
        logging.error(f"Unexpected error: {traceback.format_exc()}")
        sys.exit(1)
