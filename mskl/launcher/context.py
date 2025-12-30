#!/usr/bin/python
# -*- coding: UTF-8 -*-
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

class Context:
    """
    Maintain context of modules(code_generator, compile, etc.)
    """

    def __init__(self):
        self._config = None
        self._kernel_name = None
        self._kernel_src_file = None
        self._launch_src_file = None
        self._build_script = None
        self._blockdim = None
        self._tiling_output = None  # mskl.launcher.opgen_workflow.TilingOutput
        self._op_type = None  # str like AddCustom
        self._autotune_in_progress = False
        self._prelaunch_flag = False

        # handle args carefully in autotune scenario
        self._decl_args = None  # decl: void kernel<template_args>(decl_args)
        self._template_args = None
        self._kernel_args = None  # invocation: kernel[blockdim](kernel_args)

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        self._config = value

    @property
    def kernel_name(self):
        return self._kernel_name

    @kernel_name.setter
    def kernel_name(self, value):
        self._kernel_name = value

    @property
    def kernel_src_file(self):
        return self._kernel_src_file

    @kernel_src_file.setter
    def kernel_src_file(self, value):
        self._kernel_src_file = value

    @property
    def kernel_args(self):
        return self._kernel_args

    @kernel_args.setter
    def kernel_args(self, value):
        self._kernel_args = value

    @property
    def launch_src_file(self):
        return self._launch_src_file

    @launch_src_file.setter
    def launch_src_file(self, value):
        self._launch_src_file = value

    @property
    def build_script(self):
        return self._build_script

    @build_script.setter
    def build_script(self, value):
        self._build_script = value

    @property
    def blockdim(self):
        return self._blockdim

    @blockdim.setter
    def blockdim(self, value):
        self._blockdim = value

    @property
    def template_args(self):
        return self._template_args

    @template_args.setter
    def template_args(self, value):
        self._template_args = value

    @property
    def decl_args(self):
        return self._decl_args

    @decl_args.setter
    def decl_args(self, value):
        self._decl_args = value

    @property
    def autotune_in_progress(self):
        return self._autotune_in_progress

    @autotune_in_progress.setter
    def autotune_in_progress(self, value):
        self._autotune_in_progress = value

    @property
    def prelaunch_flag(self):
        return self._prelaunch_flag

    @prelaunch_flag.setter
    def prelaunch_flag(self, value):
        self._prelaunch_flag = value

    @property
    def tiling_output(self):
        return self._tiling_output

    @tiling_output.setter
    def tiling_output(self, value):
        self._tiling_output = value

    @property
    def op_type(self):
        return self._op_type

    @op_type.setter
    def op_type(self, value):
        self._op_type = value

    def reset(self):
        self.__init__()


context = Context()