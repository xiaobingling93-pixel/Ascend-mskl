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

import math
import os
import re
import numpy as np
from ..utils import safe_check, logger
from ..utils.safe_check import FileChecker
from .context import context
from ..utils.launcher_utils import get_cann_path
from ..utils.autotune_utils import (is_torch_tensor_instance, safe_prod, is_torch_or_numpy_tensor, canonical_tensor,
                                    ChainHandler, pad_list_slice, load_json)


class KernelInvokeConfig:
    """
    A configuration descriptor for a possible kernel developed based on an Act example
    """

    def __init__(self, kernel_src_file: str, kernel_name: str):
        safe_check.check_variable_type(kernel_src_file, str)
        safe_check.check_variable_type(kernel_name, str)
        valid_pattern = re.compile(r'^[A-Za-z0-9_]+$')
        if not valid_pattern.match(kernel_name):
            raise ValueError(f"The input kernel_name is invalid, current input : {kernel_name}")
        checker = FileChecker(kernel_src_file, "file")
        if not checker.check_input_file():
            raise Exception("Check kernel_src_file {} permission failed.".format(kernel_src_file))

        self.kernel_src_file = os.path.abspath(kernel_src_file)
        self.kernel_name = kernel_name
        self.type = "Act"


class TilingConfig:
    INT64_MIN = -2 ** 63  # -9223372036854775808
    INT64_MAX = 2 ** 63 - 1  # 9223372036854775807
    FLOAT_MAX = 3.4028235e+38
    LINE_PREFIX = '\n                                '  # for cpp line format
    STR_PATTERN = r'^[a-zA-Z0-9_]+$'  # 验证字符串是否只包含字母、数字和下划线
    DTYPE_TO_GETYPE = {
        "float": "ge::DT_FLOAT",
        "float32": "ge::DT_FLOAT",
        "fp32": "ge::DT_FLOAT",
        "float16": "ge::DT_FLOAT16",
        "fp16": "ge::DT_FLOAT16",
        "int8": "ge::DT_INT8",
        "int32": "ge::DT_INT32",
        "int": "ge::DT_INT32",
        "uint8": "ge::DT_UINT8",
        "int16": "ge::DT_INT16",
        "uint16": "ge::DT_UINT16",
        "uint32": "ge::DT_UINT32",
        "int64": "ge::DT_INT64",
        "uint64": "ge::DT_UINT64",
        "double": "ge::DT_DOUBLE",
        "bool": "ge::DT_BOOL",
        "string": "ge::DT_STRING",
        "dual_sub_int8": "ge::DT_DUAL_SUB_INT8",
        "dual_sub_uint8": "ge::DT_DUAL_SUB_UINT8",
        "complex64": "ge::DT_COMPLEX64",
        "complex128": "ge::DT_COMPLEX128",
        "qint8": "ge::DT_QINT8",
        "qint16": "ge::DT_QINT16",
        "qint32": "ge::DT_QINT32",
        "quint8": "ge::DT_QUINT8",
        "quint16": "ge::DT_QUINT16",
        "bf16": "ge::DT_BF16",
        "bfloat16": "ge::DT_BF16",
        "int4": "ge::DT_INT4",
        "uint1": "ge::DT_UINT1",
        "int2": "ge::DT_INT2",
        "uint2": "ge::DT_UINT2",
        "complex32": "ge::DT_COMPLEX32",
        "hifloat8": "ge::DT_HIFLOAT8",
        "float8_e5m2": "ge::DT_FLOAT8_E5M2",
        "float8_e4m3fn": "ge::DT_FLOAT8_E4M3FN",
        "float8_e8m0": "ge::DT_FLOAT8_E8M0",
        "float6_e3m2": "ge::DT_FLOAT6_E3M2",
        "float6_e2m3": "ge::DT_FLOAT6_E2M3",
        "float4_e2m1": "ge::DT_FLOAT4_E2M1",
        "float4_e1m2": "ge::DT_FLOAT4_E1M2",
        "fp8_e5m2": "ge::DT_FLOAT8_E5M2",
        "fp8_e4m3fn": "ge::DT_FLOAT8_E4M3FN",
        "fp8_e8m0": "ge::DT_FLOAT8_E8M0",
        "fp6_e3m2": "ge::DT_FLOAT6_E3M2",
        "fp6_e2m3": "ge::DT_FLOAT6_E2M3",
        "fp4_e2m1": "ge::DT_FLOAT4_E2M1",
        "fp4_e1m2": "ge::DT_FLOAT4_E1M2",
    }
    GETYPE_SIZE = {
        "ge::DT_FLOAT": 32,
        "ge::DT_FLOAT16": 16,
        "ge::DT_INT8": 8,
        "ge::DT_INT32": 32,
        "ge::DT_UINT8": 8,
        "ge::DT_INT16": 16,
        "ge::DT_UINT32": 32,
        "ge::DT_INT64": 64,
        "ge::DT_UINT64": 64,
        "ge::DT_DOUBLE": 64,
        "ge::DT_BOOL": 8,
        "ge::DT_STRING": 8,
        "ge::DT_DUAL_SUB_INT8": 8,
        "ge::DT_DUAL_SUB_UINT8": 8,
        "ge::DT_COMPLEX64": 64,
        "ge::DT_COMPLEX128": 128,
        "ge::DT_QINT8": 8,
        "ge::DT_QINT16": 16,
        "ge::DT_QINT32": 32,
        "ge::DT_QUINT8": 8,
        "ge::DT_QUINT16": 16,
        "ge::DT_BF16": 16,
        "ge::DT_INT4": 4,
        "ge::DT_UINT1": 1,
        "ge::DT_INT2": 2,
        "ge::DT_UINT2": 2,
        "ge::DT_COMPLEX32": 32,
        "ge::DT_HIFLOAT8": 8,
        "ge::DT_FLOAT8_E5M2": 8,
        "ge::DT_FLOAT8_E4M3FN": 8,
        "ge::DT_FLOAT8_E8M0": 8,
        "ge::DT_FLOAT6_E3M2": 6,
        "ge::DT_FLOAT6_E2M3": 6,
        "ge::DT_FLOAT4_E2M1": 4,
        "ge::DT_FLOAT4_E1M2": 4,
    }
    FMT_TO_GEFMT = {
        "nchw": "ge::FORMAT_NCHW",
        "nhwc": "ge::FORMAT_NHWC",
        "nd": "ge::FORMAT_ND",
        "nc1hwc0": "ge::FORMAT_NC1HWC0",
        "fractal_z": "ge::FORMAT_FRACTAL_Z",
        "nc1c0hwpad": "ge::FORMAT_NC1C0HWPAD",
        "nhwc1c0": "ge::FORMAT_NHWC1C0",
        "fsr_nchw": "ge::FORMAT_FSR_NCHW",
        "fractal_deconv": "ge::FORMAT_FRACTAL_DECONV",
        "c1hwnc0": "ge::FORMAT_C1HWNC0",
        "fractal_deconv_transpose": "ge::FORMAT_FRACTAL_DECONV_TRANSPOSE",
        "fractal_deconv_sp_stride_trans": "ge::FORMAT_FRACTAL_DECONV_SP_STRIDE_TRANS",
        "nc1hwc0_c04": "ge::FORMAT_NC1HWC0_C04",
        "fractal_z_c04": "ge::FORMAT_FRACTAL_Z_C04",
        "chwn": "ge::FORMAT_CHWN",
        "fractal_deconv_sp_stride8_trans": "ge::FORMAT_FRACTAL_DECONV_SP_STRIDE8_TRANS",
        "hwcn": "ge::FORMAT_HWCN",
        "nc1khkwhwc0": "ge::FORMAT_NC1KHKWHWC0",
        "bn_weight": "ge::FORMAT_BN_WEIGHT",
        "filter_hwck": "ge::FORMAT_FILTER_HWCK",
        "hashtable_lookup_lookups": "ge::FORMAT_HASHTABLE_LOOKUP_LOOKUPS",
        "hashtable_lookup_keys": "ge::FORMAT_HASHTABLE_LOOKUP_KEYS",
        "hashtable_lookup_value": "ge::FORMAT_HASHTABLE_LOOKUP_VALUE",
        "hashtable_lookup_output": "ge::FORMAT_HASHTABLE_LOOKUP_OUTPUT",
        "hashtable_lookup_hits": "ge::FORMAT_HASHTABLE_LOOKUP_HITS",
        "c1hwncoc0": "ge::FORMAT_C1HWNCoC0",
        "md": "ge::FORMAT_MD",
        "ndhwc": "ge::FORMAT_NDHWC",
        "fractal_zz": "ge::FORMAT_FRACTAL_ZZ",
        "fractal_nz": "ge::FORMAT_FRACTAL_NZ",
        "ncdhw": "ge::FORMAT_NCDHW",
        "dhwcn": "ge::FORMAT_DHWCN",
        "ndc1hwc0": "ge::FORMAT_NDC1HWC0",
        "fractal_z_3d": "ge::FORMAT_FRACTAL_Z_3D",
        "cn": "ge::FORMAT_CN",
        "nc": "ge::FORMAT_NC",
        "dhwnc": "ge::FORMAT_DHWNC",
        "fractal_z_3d_transpose": "ge::FORMAT_FRACTAL_Z_3D_TRANSPOSE",
        "fractal_zn_lstm": "ge::FORMAT_FRACTAL_ZN_LSTM",
        "fractal_z_g": "ge::FORMAT_FRACTAL_Z_G",
        "reserved": "ge::FORMAT_RESERVED",
        "all": "ge::FORMAT_ALL",
        "null": "ge::FORMAT_NULL",
        "nd_rnn_bias": "ge::FORMAT_ND_RNN_BIAS",
        "fractal_zn_rnn": "ge::FORMAT_FRACTAL_ZN_RNN",
        "nyuv": "ge::FORMAT_NYUV",
        "nyuv_a": "ge::FORMAT_NYUV_A",
        "ncl": "ge::FORMAT_NCL",
        "fractal_z_wino": "ge::FORMAT_FRACTAL_Z_WINO",
        "c1hwc0": "ge::FORMAT_C1HWC0",
    }
    DEFAULT_FORMAT = FMT_TO_GEFMT['nd']

    def __init__(self, op_type: str, inputs: list = None, outputs: list = None, lib_path: str = None,
                 inputs_info: list = None, outputs_info: list = None, attr=None, soc_version: str = None):
        # op_type 做透传处理
        if not self._is_valid_key_str(op_type):
            raise ValueError(f'op_type should be a string composed of [0-9, a-z, A-Z, _]')
        self.op_type = op_type
        self._parse_io_params(inputs, outputs, inputs_info, outputs_info)
        self._parse_attr(attr)
        self._parse_lib_path(lib_path)
        self._parse_soc_version(soc_version)

    @staticmethod
    def _get_attr_prefix(value):
        if isinstance(value, bool):
            return ''
        elif isinstance(value, int):
            return '(int64_t)'
        elif isinstance(value, float):
            return '(float)'
        elif isinstance(value, list):
            if isinstance(value[0], list):
                return 'vector<vector<int64_t>>'
            elif isinstance(value[0], bool):
                return 'vector<bool>'
            elif isinstance(value[0], int):
                return 'vector<int64_t>'
            elif isinstance(value[0], float):
                return 'vector<float>'
            else:
                return 'vector<string>'
        return 'string'

    @staticmethod
    def _check_type(value, t, param_name):
        if not isinstance(value, t):
            raise ValueError(f'{param_name} should be type {t}, but is {value.__class__}')

    @staticmethod
    def _are_all_same_type(lst: list):
        if not lst:
            return True  # 空列表视为类型一致
        return all(x.__class__ is lst[0].__class__ for x in lst)

    @staticmethod
    def _is_not_overflow(value):
        if isinstance(value, int):
            return TilingConfig.INT64_MIN <= value <= TilingConfig.INT64_MAX
        elif isinstance(value, float):
            return math.isfinite(value) and (abs(value) <= TilingConfig.FLOAT_MAX)
        return True

    @staticmethod
    def _is_basic_type(value):
        return isinstance(value, (int, bool, float, str))

    @staticmethod
    def _parse_basic_types_to_str(value) -> str:
        if isinstance(value, bool):
            return 'true' if value else 'false'
        elif isinstance(value, int):
            return f'{value}'
        elif isinstance(value, float):
            return f'{value}'
        return f'{{"{value}"}}'

    @staticmethod
    def _is_valid_key_str(input_str):
        return bool(re.match(TilingConfig.STR_PATTERN, input_str))

    @staticmethod
    def _create_attr_verifier():
        def _verify_bool(v, param_name) -> str:
            TilingConfig._check_type(v, bool, param_name)
            return 'true' if v else 'false'

        def _verify_float(v, param_name) -> str:
            TilingConfig._check_type(v, float, param_name)
            if not TilingConfig._is_not_overflow(v):
                raise OverflowError(f'{param_name} value overflows, maybe value is infinity, NaN '
                                    f'or lager than {TilingConfig.FLOAT_MAX}')
            return f'{v}'

        def _verify_int(v, param_name) -> str:
            TilingConfig._check_type(v, int, param_name)
            if not TilingConfig._is_not_overflow(v):
                raise OverflowError(f'{param_name} value overflows, it should be one of '
                                    f'[{TilingConfig.INT64_MIN}, {TilingConfig.INT64_MAX}]')
            return f'{v}'

        def _verify_str(v, param_name) -> str:
            TilingConfig._check_type(v, str, param_name)
            if v != '' and not TilingConfig._is_valid_key_str(v):
                raise ValueError(f'{param_name} should be a string composed of [0-9, a-z, A-Z, _]')
            return f'"{v}"'

        def _verify_list(v, param_name, do_verify) -> str:
            TilingConfig._check_type(v, list, param_name)
            if not v:
                return "{}"
            if not TilingConfig._are_all_same_type(v):
                raise ValueError(f'{param_name}\'s elements are not all same type')
            if do_verify is not None:
                # 一维数组
                return f"{{{','.join(do_verify(v_val, f'{param_name}[{v_idx}]') for v_idx, v_val in enumerate(v))}}}"
            # 二维数组只支持int
            inner_str_list = []
            for _, v_val in enumerate(v):
                fmt = ','.join(_verify_int(inner_val, f'{param_name}[{inner_idx}]') \
                               for inner_idx, inner_val in enumerate(v_val))
                inner_str_list.append(f"{{{fmt}}}")
            return f"{{{','.join(inner_str_list)}}}"

        return {
            "bool": _verify_bool,
            "float": lambda v, param_name: f'(float){_verify_float(v, param_name)}',
            "float32": lambda v, param_name: f'(float){_verify_float(v, param_name)}',
            "int": lambda v, param_name: f'(int64_t){_verify_int(v, param_name)}',
            "int64": lambda v, param_name: f'(int64_t){_verify_int(v, param_name)}',
            "str": lambda v, param_name: f'string{{{_verify_str(v, param_name)}}}',
            "string": lambda v, param_name: f'string{{{_verify_str(v, param_name)}}}',
            "list_bool": lambda v, param_name: f'vector<bool>{_verify_list(v, param_name, _verify_bool)}',
            "list_float": lambda v, param_name: f'vector<float>{_verify_list(v, param_name, _verify_float)}',
            "list_float32": lambda v, param_name: f'vector<float>{_verify_list(v, param_name, _verify_float)}',
            "list_int": lambda v, param_name: f'vector<int64_t>{_verify_list(v, param_name, _verify_int)}',
            "list_int64": lambda v, param_name: f'vector<int64_t>{_verify_list(v, param_name, _verify_int)}',
            "list_str": lambda v, param_name: f'vector<string>{_verify_list(v, param_name, _verify_str)}',
            "list_string": lambda v, param_name: f'vector<string>{_verify_list(v, param_name, _verify_str)}',
            "list_list_int": lambda v, param_name: f'vector<vector<int64_t>>{_verify_list(v, param_name, None)}',
            "list_list_int64": lambda v, param_name: f'vector<vector<int64_t>>{_verify_list(v, param_name, None)}',
        }

    @staticmethod
    def _verify_tensor(tensors, is_input):
        para = 'inputs' if is_input else 'outputs'
        for idx, t in enumerate(tensors):
            if isinstance(t, list):
                if any((val is not None and not is_torch_or_numpy_tensor(val)) for val in t):
                    raise ValueError(f'{para}[{idx}]: list can only contain torch.Tensor or numpy.ndarray')
            elif (t is not None) and (not is_torch_or_numpy_tensor(t)):
                raise ValueError(f'Type of {para}[{idx}] should be torch.Tensor, numpy.ndarray or the list of above')

    def _parse_lib_path(self, lib_path: str):
        if lib_path is None:
            # load liboptiling.so in cann as default
            cann_path = get_cann_path()
            tiling_so = os.path.join(cann_path, "lib64/liboptiling.so")
            self.lib_path = repr(tiling_so)[1:-1] if os.path.exists(tiling_so) else ''
        elif lib_path == '':
            raise ValueError('lib_path should not be empty')
        else:
            # 透传给runtime接口校验
            self.lib_path = repr(os.path.realpath(lib_path))[1:-1]

    def _parse_attr_list_type(self, k, v) -> str:
        if not self._are_all_same_type(v):
            raise ValueError(f'attr["{k}"]\'s elements are not all same type')
        # 处理二维数组
        if isinstance(v[0], list):
            if not all(all(isinstance(i, int) and self._is_not_overflow(i) for i in inner_list)
                       for inner_list in v):
                raise ValueError(f'attr["{k}"] two-dimensional array only supports int type')
            v_template = ','.join(f"{{{','.join(f'{i}' for i in inner_list)}}}"
                                  for inner_list in v)
            return f'{{{v_template}}}'
        # 处理一维数组
        if not self._is_basic_type(v[0]):
            raise ValueError(f'attr["{k}"] one-dimensional array\'s elements type should be one of '
                             f'{{int, bool, str, float}}')
        return f"{{{','.join(self._parse_basic_types_to_str(i) for i in v)}}}"

    # attr key值必须是str
    # value值可以是int/bool/str/float，或者list[int/bool/str/float]，或者list[list[int]]
    def _parse_attr_dict(self, attr: dict):
        for k, v in attr.items():
            self._check_type(k, str, f'attr["{k}"]')
            if not self._is_valid_key_str(k):
                raise ValueError(f'Key of attr should be a string composed of [0-9, a-z, A-Z, _]')
            if v is None or (isinstance(v, list) and not v):
                raise ValueError(f'attr["{k}"] cannot be None or empty')
            v_template = None
            if self._is_basic_type(v):
                if not self._is_not_overflow(v):
                    raise OverflowError(f'attr["{k}"]\'s int/float value range should be one of '
                                        f'cpp\'s int64_t/float value range')
                if isinstance(v, str) and v != '' and not TilingConfig._is_valid_key_str(v):
                    raise ValueError(f'attr["{k}"]\'s str value should be a string composed of [0-9, a-z, A-Z, _]')
                v_template = self._parse_basic_types_to_str(v)
            elif isinstance(v, list):
                v_template = self._parse_attr_list_type(k, v)
            else:
                raise ValueError(f'attr["{k}"]\'s type should be one of [int, bool, str, float, list]')
            self.attrs += f'{self.LINE_PREFIX}.AddAttr("{k}", {self._get_attr_prefix(v)}{v_template})'

    def _parse_attr_list(self, attr: list):
        dtype_verifier = TilingConfig._create_attr_verifier()
        name_set = set()
        for idx, value in enumerate(attr):
            if not ("name" in value and "dtype" in value and "value" in value):
                raise ValueError(f'attr\'s element must contain {{"name", "dtype", "value"}}, index: {idx}')
            if not self._is_valid_key_str(value["name"]):
                raise ValueError(f'attr[{idx}] "name" should be a string composed of [0-9, a-z, A-Z, _]')
            if name_set.issuperset({value["name"]}):
                raise ValueError(f'attr[{idx}] has same "name": {value["name"]}')
            name_set.add(value["name"])
            verifier = dtype_verifier.get(value["dtype"], None)
            if verifier is None:
                raise ValueError(f'attr[{idx}]["dtype"] should be one of {dtype_verifier.keys()}')
            param = f'attr[{idx}]'
            self.attrs += f'{self.LINE_PREFIX}.AddAttr("{value["name"]}", {verifier(value["value"], param)})'

    def _parse_attr(self, attr=None):
        self.attrs = ''
        if attr is None:
            return
        elif isinstance(attr, dict):
            self._parse_attr_dict(attr)
        elif isinstance(attr, list):
            self._parse_attr_list(attr)
        else:
            raise ValueError(f'attr should be dict or list')

    def _get_cpu_tensor(self, param_name, t):
        def _create_snapshot(tensor_dict) -> dict:
            return {
                'addr': tensor_dict['addr'],
                'tensor': tensor_dict['tensor'],
                'ori_format': tensor_dict['ori_format'],
                'format': tensor_dict['format'],
                'ori_shape': [i for i in tensor_dict['ori_shape']],
                'shape': [i for i in tensor_dict['shape']],
                'dtype': tensor_dict['dtype'],
                'data_path': '',
            }

        if is_torch_tensor_instance(t):
            addr = t.data_ptr()
            if addr in self.tensor_map:
                return _create_snapshot(self.tensor_map[addr])
            t = canonical_tensor(t)
            # 通常会直接拿到torch.int32之类的字符串
            dtype = str(t.dtype).lower().replace('torch.', '')
            self.tensor_map[addr] = {
                'addr': t.data_ptr(),
                'tensor': t,
                'ori_format': self.DEFAULT_FORMAT,  # format默认nd格式
                'format': self.DEFAULT_FORMAT,  # format默认nd格式
                'ori_shape': list(t.shape),
                'shape': list(t.shape),
                'dtype': '' if dtype not in TilingConfig.DTYPE_TO_GETYPE else dtype,  # 和用户输入比较后再转换
                'data_path': '',
            }
            return _create_snapshot(self.tensor_map[addr])
        elif isinstance(t, np.ndarray):
            addr = t.ctypes.data
            if addr in self.tensor_map:
                return _create_snapshot(self.tensor_map[addr])
            t = canonical_tensor(t)
            # 通常会直接拿到float16之类的字符串
            dtype = str(t.dtype).lower().replace('numpy.', '')
            self.tensor_map[addr] = {
                'addr': t.ctypes.data,
                'tensor': t,
                'ori_format': self.DEFAULT_FORMAT,  # format默认nd格式
                'format': self.DEFAULT_FORMAT,  # format默认nd格式
                'ori_shape': list(t.shape),
                'shape': list(t.shape),
                'dtype': '' if dtype not in TilingConfig.DTYPE_TO_GETYPE else dtype,  # 和用户输入比较后再转换
                'data_path': '',
            }
            return _create_snapshot(self.tensor_map[addr])
        raise ValueError(f'{param_name} should be numpy.ndarray or torch.Tensor')

    def _get_one_tensor(self, param_name, info_name, tensor, info):
        if tensor is None:
            return self._get_one_tensor_by_dict(param_name, info_name, info)
        detail = self._get_cpu_tensor(param_name, tensor)
        if info is None:
            info = {}
        return self._update_tensor_info(param_name, info_name, detail, info)

    def _update_tensor_info(self, param_name, info_name, detail, info):
        detail_ori_shape = detail['ori_shape']

        def set_fmt():
            fmt = info.get('format', None)
            if fmt is not None:
                detail['format'] = self.FMT_TO_GEFMT[fmt]
                detail['ori_format'] = self.FMT_TO_GEFMT[fmt]

        def set_ori_format():
            ori_format = info.get('ori_format', None)
            if ori_format is not None:
                detail['ori_format'] = self.FMT_TO_GEFMT[ori_format]

        def cmp_size(shape, d_size):
            if detail['tensor'] is None:
                return 0
            # d_size is count of bits
            size = safe_prod([safe_prod(shape), d_size]) / 8
            if size > detail['tensor'].nbytes:
                return 1
            elif size == detail['tensor'].nbytes:
                return 0
            else:
                return -1

        def set_shape():
            shape = info.get('shape', None)
            if shape is not None:
                dtype = info.get('dtype', '')
                log = f'{info_name} shape is bigger than real tensor, may cause some illegal read'
                if dtype != '' and detail['dtype'] != '':
                    if cmp_size(shape, self.GETYPE_SIZE[self.DTYPE_TO_GETYPE[dtype]]) > 0:
                        logger.warning(log)
                elif safe_prod(shape) > safe_prod(detail['shape']):
                    logger.warning(log)
                detail['shape'] = shape
                detail['ori_shape'] = shape

        def set_ori_shape():
            ori_shape = info.get('ori_shape', None)
            if ori_shape is not None:
                dtype = info.get('dtype', '')
                log = f'{info_name} ori_shape is bigger than real tensor, may cause some illegal read'
                if dtype != '' and detail['dtype'] != '':
                    if cmp_size(ori_shape, self.GETYPE_SIZE[self.DTYPE_TO_GETYPE[dtype]]) > 0:
                        logger.warning(log)
                elif safe_prod(ori_shape) > safe_prod(detail_ori_shape):
                    logger.warning(log)
                detail['ori_shape'] = ori_shape

        def set_dtype():
            dtype = info.get('dtype', '')
            if dtype == '' and detail['dtype'] == '':
                raise Exception(f'Get {param_name} dtype failed, please input it in inputs_info/outputs_info manually')
            elif dtype != '':
                ge_type = self.DTYPE_TO_GETYPE[dtype]
                if detail['dtype'] != '' and self.DTYPE_TO_GETYPE[detail['dtype']] != ge_type:
                    logger.warning(f'{param_name} dtype: {detail["dtype"]} is different from what you specified: '
                                   f'{dtype}, may cause exception')
                detail['dtype'] = ge_type
            else:
                detail['dtype'] = self.DTYPE_TO_GETYPE[detail['dtype']]

        def set_data_path():
            data_path = info.get('data_path', '')
            if data_path != '':
                detail['data_path'] = data_path

        ch = ChainHandler([set_fmt, set_ori_format, set_shape, set_ori_shape, set_dtype, set_data_path])
        ch.run()
        return detail

    def _get_one_tensor_by_dict(self, param_name, info_name, info):
        expect_keys = {"shape", "dtype"}
        if not info or not set(expect_keys).issubset(info.keys()):
            raise ValueError(f'{info_name} must have at least these keys {expect_keys}')
        detail = {
            'addr': 0,
            'tensor': None,
            'ori_format': self.DEFAULT_FORMAT,  # format默认nd格式
            'format': self.DEFAULT_FORMAT,  # format默认nd格式
            'ori_shape': list(info['shape']),
            'shape': list(info['shape']),
            'dtype': info['dtype'],
            'data_path': '',
        }
        return self._update_tensor_info(param_name, info_name, detail, info)

    def _parse_tensor_list(self, param_name, info_name, tensors, infos) -> list:
        if not isinstance(tensors, list):
            tensors = [tensors]
        if not isinstance(infos, list):
            infos = [infos]
        length = max(len(tensors), len(infos))
        tensors = pad_list_slice(tensors, length)
        infos = pad_list_slice(infos, length)
        res = []
        for i, t in enumerate(tensors):
            if t is None and not infos[i]:
                raise ValueError(f'{param_name}[{i}] and {info_name}[{i}] are both None, this is not allowed in '
                                 f'tensor list. When you need two instances, please assign sth like [x1, x2], not '
                                 f'[x1, None, x2]')
            elif t is not None:
                res.append(self._get_one_tensor(f'{param_name}[{i}]',
                                                f'{info_name}[{i}]', t, infos[i]))
            else:
                res.append(self._get_one_tensor_by_dict(f'{param_name}[{i}]',
                                                        f'{info_name}[{i}]', infos[i]))
        return res

    def _parse_tensor(self, tensors, tensor_detail_list, tensor_info, is_input):
        param_name = 'inputs'
        info_name = 'inputs_info'
        if not is_input:
            param_name = 'outputs'
            info_name = 'outputs_info'
        for idx, value in enumerate(tensors):
            tmp_list = []
            info = tensor_info[idx]
            if isinstance(value, list) or isinstance(info, list):
                tmp_list = self._parse_tensor_list(f'{param_name}[{idx}]', f'{info_name}[{idx}]',
                                                   value, info)
            elif value is not None or info:
                tmp_list.append(self._get_one_tensor(f'{param_name}[{idx}]', f'{info_name}[{idx}]',
                                                     value, info))
            tensor_detail_list.append(tmp_list)

    def _verify_one_tensor_info(self, param_name, info):
        expect_keys = {"ori_shape", "shape", "ori_format", "format", "dtype", "data_path"}
        if not set(info.keys()).issubset(expect_keys):
            raise ValueError(f'{param_name} contain invalid keys, valid keys are {expect_keys}')

        def verify_fmt():
            fmt = info.get('format', None)
            if fmt is not None:
                self._check_type(fmt, str, f'{param_name}["format"]')
                fmt = fmt.lower()
                if fmt not in self.FMT_TO_GEFMT:
                    raise ValueError(f'{param_name}["format"] should in {self.FMT_TO_GEFMT.keys()}')
                info['format'] = fmt

        def verify_ori_format():
            ori_format = info.get('ori_format', None)
            if ori_format is not None:
                self._check_type(ori_format, str, f'{param_name}["ori_format"]')
                ori_format = ori_format.lower()
                if ori_format not in self.FMT_TO_GEFMT:
                    raise ValueError(f'{param_name}["ori_format"] {ori_format} should in {self.FMT_TO_GEFMT.keys()}')
                info['ori_format'] = ori_format

        def verify_shape():
            shape = info.get('shape', None)
            if shape is not None:
                self._check_type(shape, list, f'{param_name}["shape"]')
                if not shape or any(True for i in shape if not isinstance(i, int)):
                    raise ValueError(f'{param_name}["shape"] should be a non_empty list[int]')
                elif any(True for i in shape if i <= 0):
                    raise ValueError(f'{param_name}["shape"]\'s can only contain positive integers')
                elif safe_prod(shape) == 0:
                    raise ValueError(f'{param_name}["shape"] size is too large')

        def verify_ori_shape():
            ori_shape = info.get('ori_shape', None)
            if ori_shape is not None:
                self._check_type(ori_shape, list, f'{param_name}["ori_shape"]')
                if not ori_shape or any(True for i in ori_shape if not isinstance(i, int)):
                    raise ValueError(f'{param_name}["ori_shape"] should be a non_empty list[int]')
                if any(True for i in ori_shape if i <= 0):
                    raise ValueError(f'{param_name}["ori_shape"]\'s can only contain positive integers')
                elif safe_prod(ori_shape) == 0:
                    raise ValueError(f'{param_name}["ori_shape"] size is too large')

        def verify_dtype():
            dtype = info.get('dtype', None)
            if dtype is not None:
                self._check_type(dtype, str, f'{param_name}["dtype"]')
                if dtype not in self.DTYPE_TO_GETYPE:
                    raise ValueError(f'{param_name}["dtype"] should in {self.DTYPE_TO_GETYPE.keys()}')

        def verify_data_path():
            data_path = info.get('data_path', None)
            if data_path is not None:
                self._check_type(data_path, str, f'{param_name}["data_path"]')
                # 不会主动读该文件，ascendc接口来读
                checker = FileChecker(data_path, 'file')
                if not checker.check_input_file():
                    raise PermissionError(f'{param_name}["data_path"] check permission failed')
                info['data_path'] = repr(os.path.abspath(data_path))[1:-1]

        ch = ChainHandler([verify_fmt, verify_ori_format, verify_shape, verify_ori_shape, verify_dtype,
                           verify_data_path])
        ch.run()

    def _verify_tensor_info(self, infos, is_input):
        para_info = 'inputs_info'
        if not is_input:
            para_info = 'outputs_info'

        def verify_list():
            for i, v in enumerate(val):
                if v is None:
                    continue
                param_name = f'{para_info}[{idx}][{i}]'
                self._check_type(v, dict, param_name)
                self._verify_one_tensor_info(param_name, v)

        for idx, val in enumerate(infos):
            if isinstance(val, list):
                verify_list()
            elif isinstance(val, dict):
                self._verify_one_tensor_info(f'{para_info}[{idx}]', val)
            elif val is not None:
                raise ValueError(f'Index {idx} of {para_info} should be dict or list[dict]')

    def _gen_tds(self):
        supported_types = {
            'ge::DT_INT8', 'ge::DT_INT16', 'ge::DT_INT32', 'ge::DT_INT64',
            'ge::DT_UINT8', 'ge::DT_UINT16', 'ge::DT_UINT32', 'ge::DT_UINT64',
            'ge::DT_FLOAT', 'ge::DT_DOUBLE'
        }

        def _shape_str(shape) -> str:
            return f"{{{','.join(f'{i}' for i in shape)}}}"

        def _tensor_to_td(is_input, tensor):
            if not is_input:
                return (f"{self.LINE_PREFIX}.AddOutputTd({td_idx}, {t['dtype']}, "
                        f"{t['ori_format']}, {t['format']}, "
                        f"gert::StorageShape{{{_shape_str(t['ori_shape'])}, {_shape_str(t['shape'])}}})")
            last_param = ''
            if tensor['data_path'] != '':
                escaped_path = tensor['data_path'].replace('"', '\\"')
                last_param = f", string{{\"{escaped_path}\"}}"
            elif tensor['dtype'] in supported_types and tensor['addr'] != 0:
                last_param = f", (void*){tensor['addr']}"
            return (f"{self.LINE_PREFIX}.AddInputTd({td_idx}, {tensor['dtype']}, "
                    f"{tensor['ori_format']}, {tensor['format']}, "
                    f"gert::StorageShape{{{_shape_str(tensor['ori_shape'])}, {_shape_str(tensor['shape'])}}}"
                    f"{last_param})")
        td_idx = 0
        for ten in self.inputs_list:
            for t in ten:
                self.tds += _tensor_to_td(True, t)
                td_idx += 1
        td_idx = 0
        for ten in self.outputs_list:
            for t in ten:
                self.tds += _tensor_to_td(False, t)
                td_idx += 1

    def _parse_soc_version(self, soc_version: str):
        self.soc_version = "nullptr"
        if soc_version is not None:
            # soc_version 做透传处理，目前值有问题时plog内会有打印
            # 可以用cann包目录下的linux_platform/data/platform_config/校验
            self._check_type(soc_version, str, "soc_version")
            if not soc_version:
                raise ValueError('soc_version should be None or non-empty str')
            valid_pattern = re.compile(r'^[A-Za-z0-9_]+$')
            if not valid_pattern.match(soc_version):
                raise ValueError(f"The input soc_version is invalid, current input : {soc_version}")
            self.soc_version = f"\"{soc_version}\""

    def _set_node_io_num(self):
        input_num = sum(len(item) for item in self.inputs_list)
        output_num = sum(len(item) for item in self.outputs_list)
        self.node_io_num = f"{input_num}, {output_num}"

    def _set_ir_instance_num(self):
        self.ir_instance_num = ','.join([f'{len(i)}' for i in self.inputs_list])

    def _verify_io_params(self, is_input, tensors, infos):
        para = 'inputs' if is_input else 'outputs'
        para_info = 'inputs_info' if is_input else 'outputs_info'
        max_length = 1e5  # 只是用于限制循环次数，并不会真的有算子的输入这么大
        if tensors is not None:
            self._check_type(tensors, list, para)
            if len(tensors) > max_length:
                raise ValueError(f"Length of {para} is larger than {max_length}")
        if infos is not None:
            self._check_type(infos, list, para_info)
            if len(infos) > max_length:
                raise ValueError(f"Length of {para_info} is larger than {max_length}")
        if not tensors and not infos:
            raise Exception(f"The {para} and {para_info} cannot be None or empty list at same time")
        ten = [i for i in tensors] if tensors is not None else []
        info = [i for i in infos] if infos is not None else []
        length = max(len(ten), len(info))
        ten = pad_list_slice(ten, length)
        info = pad_list_slice(info, length)
        return ten, info

    def _parse_io_params(self, inputs, outputs, inputs_info, outputs_info):
        # 本地临时存储cpu侧tensor，防止tiling函数执行过程中访问野指针，元素为dict
        self.tensor_map = {}
        self.tds = ""
        self.inputs_list = []
        self.outputs_list = []
        inputs, inputs_info = self._verify_io_params(True, inputs, inputs_info)
        outputs, outputs_info = self._verify_io_params(False, outputs, outputs_info)
        self._verify_tensor(inputs, True)
        self._verify_tensor(outputs, False)
        self._verify_tensor_info(inputs_info, True)
        self._verify_tensor_info(outputs_info, False)
        self._parse_tensor(inputs, self.inputs_list, inputs_info, True)
        self._parse_tensor(outputs, self.outputs_list, outputs_info, False)
        self._gen_tds()
        self._set_node_io_num()
        self._set_ir_instance_num()


class KernelBinaryInvokeConfig:
    KERNEL_TYPE_TO_MAGIC = {
        'mix': 0x43554245,
        'vec': 0x41415246,
        'cube': 0x41494343,
    }
    UINT64_MAX = 2 ** 64 - 1  # 18446744073709551615

    def __init__(self, kernel_binary_file: str, kernel_type: str = None, tiling_key: int = None):
        self.kernel_name = 'kernel_binary'
        self._check_kernel_binary_file(kernel_binary_file)
        self._try_read_kernel_json()
        self._set_tiling_key(tiling_key)
        self._set_magic(kernel_type)

    def _check_kernel_binary_file(self, kernel_binary_file):
        if kernel_binary_file is None or kernel_binary_file == '':
            raise ValueError('kernel_binary_file should not be None or empty')
        self.kernel_binary_file = os.path.realpath(kernel_binary_file)
        if not FileChecker(self.kernel_binary_file, "file").check_input_file():
            raise Exception(f"Check kernel_binary_file {self.kernel_binary_file} permission failed.")
        self.kernel_binary_file = repr(self.kernel_binary_file)[1:-1]

    def _set_tiling_key(self, tiling_key):
        if context.tiling_output is None and tiling_key is None:
            raise Exception('Please call mskl.tiling_func or assign [tiling_key]')
        # runtime接口校验，非法情况会找不到函数
        if tiling_key is None:
            self.tiling_key = context.tiling_output.tiling_key
        else:
            if tiling_key < 0 or tiling_key > self.UINT64_MAX:
                raise ValueError(f'Param [tiling_key] should in [0, {self.UINT64_MAX}]')
            self.tiling_key = tiling_key

    def _set_magic(self, kernel_type):
        # 优先使用用户填的算子类型判断，310p在生成代码时填固定值
        self.magic = 0
        if kernel_type is not None:
            if kernel_type not in KernelBinaryInvokeConfig.KERNEL_TYPE_TO_MAGIC.keys():
                raise ValueError(f"kernel_type should in {KernelBinaryInvokeConfig.KERNEL_TYPE_TO_MAGIC.keys()}")
            self.magic = self.KERNEL_TYPE_TO_MAGIC[kernel_type]

    def _try_read_kernel_json(self):
        self.enable_printf = 0
        if not self.kernel_binary_file.endswith('.o'):
            return
        json_path = self.kernel_binary_file[:-1] + 'json'
        if not os.path.exists(json_path) or not FileChecker(json_path, "file").check_input_file():
            return
        res, json_data = load_json(json_path)
        if not res:
            logger.warning(f'Read json {json_path} failed, AscendC::printf and AscendC::DumpTensor'
                           f' will be ineffective. {json_data}')
            return
        if not json_data or json_data.get("debugOptions", None) is None:
            return
        debug_options = json_data.get("debugOptions")
        if 'printf' in debug_options:
            logger.info('Enable AscendC::printf and AscendC::DumpTensor')
            self.enable_printf = 1
