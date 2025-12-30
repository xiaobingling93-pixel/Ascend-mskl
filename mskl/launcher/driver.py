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

import importlib.util
import ctypes
import os
import numpy as np

from .code_generator import is_builtin_basic_type_instance, is_ctypes_class_instance
from ..utils import logger
from ..utils.autotune_utils import (is_torch_or_numpy_tensor, canonical_tensor, ChainHandler, is_tensor_empty,
                                    is_torch_tensor_instance)


def load_mspti_so():
    cann_path = os.getenv('ASCEND_HOME_PATH')
    if cann_path:
        mspti_path = os.path.join(cann_path, "lib64/libmspti.so")
        mspti_real_path = os.path.realpath(mspti_path)
        if mspti_real_path and os.path.exists(mspti_real_path):
            lib = ctypes.CDLL(mspti_real_path, mode=ctypes.RTLD_GLOBAL)


load_mspti_so()


class TensorListHolder:
    """
    create a struct like aclTensorList
    memory layout looks like:
    struct TensorList {
        uint64_t offset;    // offset of TensorList.tensors
        void* tensors[0];   // variant length array, pointers of the real tensor data addr on npu
    };
    maybe some operators will use conflict structs
    """
    def __init__(self, lst: list):
        n = len(lst) + 1
        self.arr = (ctypes.c_void_p * n)()
        for i in range(n):
            self.arr[i] = 0
        self.arr[0] = 8  # 首个tensor地址的偏移
        for i, num in enumerate(lst):
            self.arr[i + 1] = ctypes.cast(num, ctypes.c_void_p).value

    @property
    def addr(self):
        return ctypes.addressof(self.arr)

    @property
    def size(self):
        return len(self.arr) * ctypes.sizeof(ctypes.c_uint64)


class NPULauncher(object):

    def __init__(self, module: str):
        self._module = module
        self._args_info = []
        self._kernel_meta = []
        self._host_to_gm_map = {}

    def __call__(self, *args,
                 blockdim: int,
                 l2ctrl: int,
                 stream: int,
                 warmup: int,
                 profiling: bool,
                 device_id: int,
                 timeout: int,
                 kernel_name: str,
                 repeat: int = 1
                 ):
        if device_id is not None:
            driver.set_device(device_id)
        elif driver.get_active_device() is None:
            driver.set_device(0)

        self._arg_preprocess(*args)

        if warmup is not None or profiling:
            # not implemented
            pass

        func_name = kernel_name

        module_name = f"_mskl_launcher"
        spec = importlib.util.spec_from_file_location(module_name, self._module)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, func_name):
            self._free_all_dev_ptr()
            raise Exception("Can't find function: {} in module: {}".format(func_name, self._module))

        new_stream_flag = False
        if stream is None:
            stream = driver.create_stream()
            new_stream_flag = True

        func = getattr(module, func_name)

        logger.debug("Repeat = {}".format(repeat))
        for _ in range(repeat):
            func(blockdim, l2ctrl, stream, *self._kernel_meta)
            ret = driver.synchronize_stream(stream, timeout)
            if ret != 0:
                self._free_all_dev_ptr()
                if new_stream_flag is True:
                    driver.destroy_stream(stream)
                raise Exception("Synchronize stream failed, ret={}".format(ret))

        if new_stream_flag is True:
            driver.destroy_stream(stream)

        # args copy from gm back to host
        self._arg_postprocess()
        self._free_all_dev_ptr()

        if self.is_lib_preloaded('libruntime_camodel.so'):
            # 仿真时若set_device/reset_device没有成对使用，仿真器会core dump
            # 但因外部set_device次数不可控，因此此处需要调用 reset_device_force 强制结束
            driver.reset_device_force(driver.get_active_device())

    @staticmethod
    def is_lib_preloaded(lib_name):
        # 获取LD_PRELOAD环境变量
        ld_preload = os.environ.get('LD_PRELOAD', '')

        if not ld_preload:
            return False

        # 分割路径列表
        import re
        preload_paths = re.split(r'[:]+', ld_preload.strip())

        for path in preload_paths:
            if not path:
                continue
            if os.path.basename(path) == lib_name:
                return True
        return False

    def _arg_preprocess(self, *args):
        args_info = []
        kernel_meta = []

        def malloc_and_copy_to_device(addr, size):
            dev_ptr, ret = driver.malloc(size)
            if ret != 0:
                self._free_all_dev_ptr()
                raise Exception("Malloc failed. ret={} size={}".format(ret, size))
            # copy from host to device
            ret = driver.memcpy(dev_ptr, size, addr, size, 1)
            if ret != 0:
                self._free_all_dev_ptr()
                raise Exception("Memcpy failed. ret={}".format(ret))
            return dev_ptr

        def parse_scalar(arg_dict) -> bool:
            if is_builtin_basic_type_instance(arg_dict["value"]) or (is_ctypes_class_instance(arg_dict["value"])):
                # 传递scalar值
                kernel_meta.append(arg_dict["value"])
                return True
            return False

        def parse_c_structure(arg_dict) -> bool:
            if isinstance(arg_dict["value"], ctypes.Structure):
                # 传递arg对象的host内存指针
                kernel_meta.append(ctypes.cast(ctypes.pointer(arg_dict["value"]), ctypes.c_void_p).value)
                return True
            return False

        def parse_numpy_array(arg_dict) -> bool:
            if isinstance(arg_dict["value"], np.ndarray):
                if is_tensor_empty(arg_dict["value"]):
                    arg_dict["value"] = None
                    arg_dict["type"] = type(None)
                    return parse_none(arg_dict)

                # 传递GM内存指针
                if not arg_dict["value"].flags.contiguous:
                    arg_dict["value"] = np.ascontiguousarray(arg_dict["value"])
                addr = arg_dict["addr"] = arg_dict["value"].ctypes.data
                size = arg_dict["size"] = arg_dict["value"].nbytes
                if addr not in self._host_to_gm_map:
                    arg_dict["dev_addr"] = malloc_and_copy_to_device(addr, size)
                    self._host_to_gm_map[addr] = arg_dict["dev_addr"]
                kernel_meta.append(self._host_to_gm_map[addr])
                return True
            return False

        def parse_c_array(arg_dict) -> bool:
            if isinstance(arg_dict["value"], ctypes.Array):
                # 传递GM内存指针
                size = arg_dict["size"] = ctypes.sizeof(arg_dict["value"])
                addr = arg_dict["addr"] = ctypes.addressof(arg_dict["value"])
                if addr not in self._host_to_gm_map:
                    arg_dict["dev_addr"] = malloc_and_copy_to_device(addr, size)
                    self._host_to_gm_map[addr] = arg_dict["dev_addr"]
                kernel_meta.append(self._host_to_gm_map[addr])
                return True
            return False

        def parse_torch_tensor(arg_dict) -> bool:
            if is_torch_tensor_instance(arg_dict["value"]):
                if is_tensor_empty(arg_dict["value"]):
                    arg_dict["value"] = None
                    arg_dict["type"] = type(None)
                    return parse_none(arg_dict)

                # 传递GM内存指针
                if not arg_dict["value"].is_contiguous():
                    arg_dict["value"] = arg_dict["value"].contiguous()
                if arg_dict["value"].device.type == 'npu':
                    # 在npu上的，最后不需要拷贝回host内存
                    kernel_meta.append(arg_dict["value"].data_ptr())
                else:
                    # 统一管理gm内存，不使用.npu()
                    addr = arg_dict["addr"] = arg_dict["value"].data_ptr()
                    size = arg_dict["size"] = arg_dict["value"].nbytes
                    if addr not in self._host_to_gm_map:
                        arg_dict["dev_addr"] = malloc_and_copy_to_device(addr, size)
                        self._host_to_gm_map[addr] = arg_dict["dev_addr"]
                    kernel_meta.append(self._host_to_gm_map[addr])
                return True
            return False

        def parse_tensor_list(arg_dict) -> bool:
            if not (isinstance(arg_dict["value"], list) and
                    all(is_torch_or_numpy_tensor(i) for i in arg_dict["value"])):
                return False

            lst = []
            for t in arg_dict["value"]:
                t = canonical_tensor(t, False)
                t_info = {
                    "type": type(t),
                    "size": None,
                    "value": t,
                    "addr": None,
                    "dev_addr": None
                }
                if is_tensor_empty(t):
                    dev_addr = 0
                elif is_torch_tensor_instance(t):
                    addr = t_info["addr"] = t.data_ptr()
                    size = t_info["size"] = t.nbytes
                    if t.device.type != 'npu' and addr not in self._host_to_gm_map:
                        t_info["dev_addr"] = malloc_and_copy_to_device(addr, size)
                        self._host_to_gm_map[addr] = t_info["dev_addr"]
                    dev_addr = addr if t.device.type == 'npu' else self._host_to_gm_map[addr]
                else:
                    addr = t_info["addr"] = t.ctypes.data
                    size = t_info["size"] = t.nbytes
                    if addr not in self._host_to_gm_map:
                        t_info["dev_addr"] = malloc_and_copy_to_device(addr, size)
                        self._host_to_gm_map[addr] = t_info["dev_addr"]
                    dev_addr = self._host_to_gm_map[addr]
                # 保证对tensor的引用，同时统一管理内存
                args_info.append(t_info)
                lst.append(dev_addr)
            arg_dict["value"] = TensorListHolder(lst)
            arg_dict["addr"] = arg_dict["value"].addr
            arg_dict["size"] = arg_dict["value"].size
            arg_dict["dev_addr"] = malloc_and_copy_to_device(arg_dict["addr"], arg_dict["size"])
            self._host_to_gm_map[arg_dict["addr"]] = arg_dict["dev_addr"]
            kernel_meta.append(arg_dict["dev_addr"])
            return True

        def parse_none(arg_dict) -> bool:
            if arg_dict["value"] is None:
                # 拉起融合算子的场景，部分kernel入参可能需要传None
                kernel_meta.append(0)
                return True
            return False

        ch = ChainHandler([parse_scalar, parse_c_structure, parse_numpy_array, parse_c_array, parse_torch_tensor,
                           parse_tensor_list, parse_none])
        for i, arg in enumerate(args):
            logger.debug(f'Start to parse [{i}] kernel arg')
            new_arg_info = {
                "type": type(arg),
                "size": None,
                "value": arg,
                "addr": None,
                "dev_addr": None
            }
            if not ch.run(new_arg_info):
                self._free_all_dev_ptr()
                raise Exception("unsupported arg type {}".format(type(new_arg_info["value"])))
            args_info.append(new_arg_info)
        self._args_info = args_info
        self._kernel_meta = kernel_meta

    def _arg_postprocess(self):
        for arg_info in self._args_info:
            dev_ptr = arg_info["dev_addr"]
            size = arg_info["size"]
            addr = arg_info["addr"]
            if (dev_ptr is not None) and (addr in self._host_to_gm_map):
                # copy from device back to host
                ret = driver.memcpy(addr, size, dev_ptr, size, 2)
                if ret != 0:
                    self._free_all_dev_ptr()
                    raise Exception("Memcpy failed. ret={}".format(ret))
                driver.free(dev_ptr)
                arg_info["dev_addr"] = None
                self._host_to_gm_map.pop(addr)

    def _free_all_dev_ptr(self):
        for _, dev_ptr in self._host_to_gm_map.items():
            driver.free(dev_ptr)


class NPUDeviceContext:

    def __init__(self):
        # 不需要在构造函数中导入acl
        self._acl = None
        self._init_flag = False
        self._active_device = None

    def __exit__(self):
        if not self._init_flag:
            return
        self._do_acl_init()
        if self._active_device is not None:
            self._acl.rt.reset_device(self._active_device)
        self._acl.finalize()

    def set_device(self, devid: int):
        self._do_acl_init()
        if not isinstance(devid, int) or devid < 0:
            raise Exception("Invalid devid, got".format(devid))
        ret = self._acl.rt.set_device(devid)
        if ret != 0:
            raise RuntimeError(f'Set device failed, error code: {ret}')
        self._active_device = devid

    def reset_device_force(self, devid: int):
        self._do_acl_init()
        if not isinstance(devid, int) or devid < 0:
            raise Exception("Invalid devid, got {}".format(devid))
        return self._acl.rt.reset_device_force(self._active_device)

    def get_active_device(self):
        return self._active_device

    def create_stream(self):
        self._do_acl_init()
        stream, ret = self._acl.rt.create_stream()
        if ret != 0:
            raise Exception("Create stream failed. ret={}".format(ret))
        return stream

    def destroy_stream(self, stream: int):
        if stream is None:
            raise Exception("Stream is None")
        self._do_acl_init()
        return self._acl.rt.destroy_stream_force(stream)

    def synchronize_stream(self, stream, timeout: int = -1):
        if stream is None:
            raise Exception("Stream is None")
        self._do_acl_init()
        return self._acl.rt.synchronize_stream_with_timeout(stream, timeout)

    def malloc(self, size: int, policy: int = 0):
        '''
        MemMallocPolicy:
            ACL_MEM_MALLOC_HUGE_FIRST = 0
            ACL_MEM_MALLOC_HUGE_ONLY
            ACL_MEM_MALLOC_NORMAL_ONLY
            ACL_MEM_MALLOC_HUGE_FIRST_P2P
            ACL_MEM_MALLOC_HUGE_ONLY_P2P
            ACL_MEM_MALLOC_NORMAL_ONLY_P2P
        '''
        self._do_acl_init()
        return self._acl.rt.malloc(size, policy)

    def free(self, dev_ptr: int):
        self._do_acl_init()
        return self._acl.rt.free(dev_ptr)

    def memcpy(self, dst: int, dst_size: int, src: int, count: int, direction: int):
        '''
        memcpy mode:
            ACL_MEMCPY_HOST_TO_HOST: 0
            ACL_MEMCPY_HOST_TO_DEVICE: 1
            ACL_MEMCPY_DEVICE_TO_HOST: 2
            ACL_MEMCPY_DEVICE_TO_DEVICE: 3
        '''
        self._do_acl_init()
        return self._acl.rt.memcpy(dst, dst_size, src, count, direction)

    def _do_acl_init(self):
        if self._init_flag:
            return

        if self._acl is None:
            import acl
            self._acl = acl

        device_id, ret = self._acl.rt.get_device()
        if ret != 0:
            self._acl.init()
            self._active_device = None
        else:
            self._active_device = device_id
        self._init_flag = True


driver = NPUDeviceContext()
