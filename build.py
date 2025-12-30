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

import os
import sys
import logging
import subprocess
import argparse
import glob


def exec_cmd(cmd):
    result = subprocess.run(cmd, capture_output=False, text=True, timeout=3600)
    if result.returncode != 0:
        logging.error("execute command %s failed, please check the log", " ".join(cmd))
        sys.exit(result.returncode)


def execute_python_test(test_cmd):
    if test_cmd != "":
        logging.info("============ start to execute Python code UT test ============")
        exec_cmd(test_cmd)
        exec_cmd(["coverage3", "xml", "-o", "report/coverage.xml"])
        exec_cmd(["coverage3", "html", "-d", "report"])
        exec_cmd(["coverage3", "report", "-m"])


def create_arg_parser():
    parser = argparse.ArgumentParser(description='Build script with optional testing')
    parser.add_argument('command', nargs='*', default='[]', 
                    choices=['[]', 'local', 'test'],
                    help='Command to execute (python build.py [ |local|test]):\n')
    parser.add_argument('-r', '--revision',
                        help="Build with specific revision or tag")
    return parser

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = create_arg_parser()
    args = parser.parse_args()
    current_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    os.chdir(current_dir)

    if 'test' in args.command:
         # 执行python代码UT测试
        build_dir = os.path.join(current_dir, "build_ut")
        pythontest_cmd = ["coverage3", "run", "--branch", "--source=" + current_dir, "-m", "pytest",
                            current_dir + "/test/launcher/", current_dir + "/test/op_tune/",
                            "--junitxml=" + build_dir +"/report/final.xml", "-W", "ignore::DeprecationWarning"] 
       
        if not os.path.exists(build_dir):
            os.makedirs(build_dir, mode=0o755)
        os.chdir(build_dir)
        os.environ['PYTHONPATH'] = current_dir + os.pathsep + os.environ.get('PYTHONPATH', '')
        os.environ['PYTHONPYCACHEPREFIX'] = build_dir
        execute_python_test(pythontest_cmd)
    else:
        output_dir = os.path.join(current_dir, "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, mode=0o750)
        python_executable = sys.executable    
        exec_cmd([python_executable, "setup.py", "bdist_wheel", "--dist-dir", "output"])
        for whl in glob.glob(os.path.join(output_dir, "mskl*.whl")):
            os.chmod(whl, 0o550)