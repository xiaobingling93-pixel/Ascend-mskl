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

import os
import inspect
import ctypes
import numpy as np
from .config import KernelInvokeConfig, TilingConfig, KernelBinaryInvokeConfig
from .context import context
from ..utils import logger, safe_check
from ..utils.autotune_utils import is_torch_tensor_instance
from ..utils.safe_check import FileChecker
from ..utils.launcher_utils import check_runtime_impl


def is_builtin_basic_type_instance(obj):
    return isinstance(obj, int) or isinstance(obj, float)


def is_ctypes_class_instance(obj):
    return isinstance(obj, ctypes._SimpleCData)


def has_get_namespace(obj):
    return hasattr(obj, 'get_namespace') and callable(getattr(obj, 'get_namespace'))


def pytype_to_cpp(pytype):
    type_map = {
        # ctypes
        "c_char": "char",
        "c_byte": "char",
        "c_ubyte": "unsigned char",
        "c_short": "short",
        "c_ushort": "unsigned short",
        "c_int": "int",
        "c_uint": "unsigned int",
        "c_long": "long",
        "c_ulong": "unsigned long",
        "c_longlong": "long long",
        "c_ulonglong": "unsigned long long",
        "c_float": "float",
        "c_double": "double",
        "c_size_t": "size_t",
        "c_ssize_t": "ssize_t",
        "c_int8": "int8_t",
        "c_int16": "int16_t",
        "c_int32": "int32_t",
        "c_int64": "int64_t",
        "c_uint8": "uint8_t",
        "c_uint16": "uint16_t",
        "c_uint32": "uint32_t",
        "c_uint64": "uint64_t",

        # py built-in types
        "int": "int",
        "float": "float",
    }
    if pytype in type_map:
        return type_map[pytype]
    else:
        raise Exception("unsupported type")


def format_of(pytype):
    type_map = {
        # ctypes
        "c_char": "c",
        "c_byte": "b",
        "c_ubyte": "B",
        "c_short": "h",
        "c_ushort": "H",
        "c_int": "i",
        "c_uint": "I",
        "c_long": "l",
        "c_ulong": "k",
        "c_longlong": "L",
        "c_ulonglong": "K",
        "c_float": "f",
        "c_double": "d",
        "c_size_t": "n",
        "c_ssize_t": "N",
        "c_int8": "b",
        "c_int16": "h",
        "c_int32": "i",
        "c_int64": "L",
        "c_uint8": "B",
        "c_uint16": "H",
        "c_uint32": "I",
        "c_uint64": "K",

        # py built-in types
        "int": "i",
        "float": "f",
    }
    if pytype in type_map:
        return type_map[pytype]
    else:
        raise Exception("unsupported type")


def parse_kernel_args_by_stack():
    """
    Parse out the kernel args by tracing back the callstack.

    Returns:
        list: A list of arguments from user input.
    """
    current_frame = inspect.currentframe()
    caller_frame = current_frame.f_back.f_back.f_back.f_back
    args, _, _, values = inspect.getargvalues(caller_frame)
    decl_args = tuple(values[arg] for arg in args if arg not in ["template_param", "blockdim", "tiling_key"])
    if not decl_args:
        raise Exception("kernel args not found")
    logger.debug("{} decl_args parsed: {}".format(len(decl_args), decl_args))

    template_args = []
    if "template_param" in args:
        if not isinstance(values["template_param"], list):
            raise Exception("template_param shall be list")

        for arg in values["template_param"]:
            if isinstance(arg, str):
                template_args.append(arg)
            else:
                namespace = arg.get_namespace() if has_get_namespace(arg) else ''
                template_args.append(namespace + arg.__name__)

    logger.debug("{} template_args parsed: {}".format(len(template_args), template_args))
    return decl_args, template_args


class KernelLauncher:

    def __init__(self, config: KernelInvokeConfig):
        """
        a class that generates launch source code for a kernel

        Args:
            config (KernelInvokeConfig): A configuration descriptor for a kernel
        """
        self.config = config
        self.decl_args = None
        self.template_args = []
        self.kernel_name = config.kernel_name
        self.kernel_src_file = config.kernel_src_file

        if context.autotune_in_progress:
            # stack parsing will fail in autotune scenario. therefore, use args saved in context instead.
            logger.debug("Autotune in progress")
            self.decl_args = context.decl_args
            self.template_args = context.template_args
        else:
            self.decl_args, self.template_args = parse_kernel_args_by_stack()
            context.decl_args = self.decl_args
            context.template_args = self.template_args
            # save params in context
            context.kernel_name = self.kernel_name
            context.kernel_src_file = self.kernel_src_file

    def code_gen(self, gen_file: str = "_gen_launch.cpp"):
        """
        Generate launch source code (glue code) for a kernel.
        Support the following launch mode: 1. kernel invocation <<<>>>

        Args:
            gen_file (str, optional): Specify the generated launch source code file path for kernel.
                                      Defaults to "__gen_launch.cpp".

        Returns:
            str: The file path of generated launch source file.

        Note:
        """
        def _check_input(file_path: str):
            safe_check.check_variable_type(file_path, str)
            checker = None
            if os.path.isfile(file_path):
                checker = FileChecker(file_path, "file")
            else:
                checker = FileChecker(os.path.dirname(file_path), "dir")
            if not checker.check_input_file():
                raise Exception("Check file_path {} permission failed.".format(file_path))

        _check_input(gen_file)
        context.launch_src_file = gen_file
        new_line = '\n    '
        args_decl = []
        args_deref = []
        arg_parse_list = []
        args_format = ['K', 'K', 'K'] # for blockdim, l2ctrl, stream

        for i, arg in enumerate(self.decl_args):
            # template_param
            arg_parse_list.append(f"&arg{i}")
            if is_builtin_basic_type_instance(arg) or is_ctypes_class_instance(arg):
                # 基础类型，传递scalar值
                pytype = arg.__class__.__name__
                if isinstance(arg, int) and arg.bit_length() > 32:
                    # 认为大整数传递的是指针
                    pytype = "c_ulonglong"
                cpp_type = pytype_to_cpp(pytype)
                args_decl.append(f"{cpp_type} arg{i};")
                args_deref.append(f"arg{i}")
                args_format.append(format_of(pytype))
            elif isinstance(arg, ctypes.Structure):
                # 外部导入Structure数据类型，变量声明时考虑命名空间，形如{namespace}{type} *，传递cpu内存地址
                namespace = arg.get_namespace() if has_get_namespace(arg) else ''
                args_decl.append(namespace + arg.__class__.__name__ + f" *arg{i};")
                args_deref.append(f"*arg{i}")
                args_format.append(f"K")
            elif isinstance(arg, np.ndarray):
                # numpy数组，申请GM空间，传递指针地址
                args_decl.append(f"__gm__ uint8_t *arg{i};")
                args_deref.append(f"arg{i}")
                args_format.append(f"K")
            elif is_torch_tensor_instance(arg):
                # torch tensor，传递指针地址
                args_decl.append(f"__gm__ uint8_t *arg{i};")
                args_deref.append(f"arg{i}")
                args_format.append(f"K")
            elif isinstance(arg, list):
                raise Exception(f"type \"list\" is unsupported yet. use ctypes array instead.")
            else:
                # 用户自定义类型，包括模板库数据类型数组，申请GM空间，传递指针地址
                args_decl.append(f"__gm__ uint8_t *arg{i};")
                args_deref.append(f"arg{i}")
                args_format.append(f"K")

        template_args = '<' + ', '.join(self.template_args) + '>' if len(self.template_args) > 0 else ''

        src = KERNEL_TEMPLATE.format(kernel_src_file=self.kernel_src_file,
                              kernel_name=self.kernel_name,
                              args_decl=new_line.join(e for e in args_decl if e is not None),
                              args_format=''.join(e for e in args_format if e is not None),
                              args_ref=', ' + ', '.join(arg_parse_list) if len(arg_parse_list) > 0 else '',
                              template_args=template_args,
                              args=', '.join(args_deref) if len(args_deref) > 0 else '')

        with os.fdopen(os.open(gen_file, safe_check.OPEN_FLAGS, safe_check.SAVE_DATA_FILE_AUTHORITY), 'w') as f:
            f.truncate()
            f.write(src)
            logger.debug(f"Launch src file generated in {gen_file}")
        return gen_file


class TilingLauncher:

    def __init__(self, config: TilingConfig):
        """
        a class that generates launch source code for a kernel

        Args:
            config (TilingConfig): An configuration descriptor for a kernel's tiling function
        """
        self.config = config

    def code_gen(self, gen_file):
        src = OPGEN_TILING_TEMPLATE.format(node_io_num=self.config.node_io_num,
                                           ir_instance_num=self.config.ir_instance_num,
                                           tds=self.config.tds,
                                           soc_version=self.config.soc_version,
                                           op_type=self.config.op_type,
                                           lib_path=self.config.lib_path,
                                           attrs=self.config.attrs)

        if os.path.exists(gen_file):
            logger.debug(f"{gen_file} exists, will overwrite it")
            if not FileChecker(gen_file, 'file').check_input_file():
                raise PermissionError(f'permission of {gen_file} is invalid, please check and remove it first')
            try:
                os.remove(gen_file)
            except Exception as e:
                raise OSError(f'remove {gen_file} failed, please check permission and remove it manually, '
                              f'err is {e}') from e
        with os.fdopen(os.open(gen_file, safe_check.OPEN_FLAGS, safe_check.SAVE_DATA_FILE_AUTHORITY), 'w') as f:
            f.truncate()
            f.write(src)
            logger.debug(f"Tiling_func invoke file generated in {gen_file}")
        return gen_file


class KernelBinaryLauncher:

    def __init__(self, config: KernelBinaryInvokeConfig):
        """
        a class that generates launch source code for a kernel

        Args:
            config (KernelBinaryInvokeConfig): A configuration descriptor for a kernel's binary file
        """
        self.config = config
        # save params in context
        context.kernel_name = self.config.kernel_name

    def code_gen(self, gen_file):
        if context.op_type is None:
            raise Exception('Cannot generate binary launch file, op_type is None, '
                            'please call mskl.tiling_func first')
        is_runtime_exist = check_runtime_impl()
        template = OPGEN_KERNEL_TEMPLATE_RT if is_runtime_exist else OPGEN_KERNEL_TEMPLATE_ACL_RT
        src = template.format(kernel_name=self.config.kernel_name,
                              kernel_binary_file=self.config.kernel_binary_file,
                              tiling_key=self.config.tiling_key,
                              magic=self.config.magic,
                              op_type=context.op_type,
                              enable_printf=self.config.enable_printf)
        if os.path.exists(gen_file):
            logger.debug(f"{gen_file} exists, will overwrite it")
            if not FileChecker(gen_file, 'file').check_input_file():
                raise PermissionError(f'permission of {gen_file} is invalid, please check and remove it first')
            try:
                os.remove(gen_file)
            except Exception as e:
                raise OSError(f'remove {gen_file} failed, please check permission and remove it manually, '
                              f'err is {e}') from e
        with os.fdopen(os.open(gen_file, safe_check.OPEN_FLAGS, safe_check.SAVE_DATA_FILE_AUTHORITY), 'w') as f:
            f.truncate()
            f.write(src)
            logger.debug(f"Kernel binary launch src file generated in {gen_file}")
        return gen_file


# some launcher will call parse_context_kernel_args(), which requires specific callstack
class Launcher:

    def __init__(self, config):
        if isinstance(config, KernelInvokeConfig):
            self.launcher = KernelLauncher(config)
        elif isinstance(config, TilingConfig):
            self.launcher = TilingLauncher(config)
        elif isinstance(config, KernelBinaryInvokeConfig):
            self.launcher = KernelBinaryLauncher(config)
        else:
            raise Exception(f"unsupported config type: {type(config)}")

    def code_gen(self, *args, **kwargs):
        return self.launcher.code_gen(*args, **kwargs)


KERNEL_TEMPLATE = """
#include <iostream>
#include <Python.h>

#include "acl/acl.h"

// kernel src file
#include "{kernel_src_file}"

static PyObject* _launch_{kernel_name}(PyObject* self, PyObject* args) {{

    uint64_t blockdim;
    void *l2ctrl;
    void *stream;

    // args decl
    {args_decl}

    // args parse
    if (!PyArg_ParseTuple(args, "{args_format}", &blockdim, &l2ctrl, &stream{args_ref})) {{
        std::cout << "PyArg_ParseTuple failed" << std::endl;
        Py_RETURN_NONE;
    }}

    // launch here
    {kernel_name}{template_args}<<<blockdim, l2ctrl, stream>>>({args});

    Py_RETURN_NONE;
}}

static PyMethodDef ModuleMethods[] = {{
  {{"{kernel_name}", _launch_{kernel_name}, METH_VARARGS, "Entry point for kernel {kernel_name}"}},
  {{NULL, NULL, 0, NULL}} // sentinel
}};

static struct PyModuleDef ModuleDef = {{
  PyModuleDef_HEAD_INIT,
  "_mskl_launcher",
  NULL, //documentation
  -1, //size
  ModuleMethods
}};

#if PY_VERSION_HEX < 0x03090000
extern "C" __attribute__((visibility("default"))) PyObject* PyInit__mskl_launcher(void)
#else
PyMODINIT_FUNC PyInit__mskl_launcher(void)
#endif
{{
  PyObject *m = PyModule_Create(&ModuleDef);
  if(m == NULL) {{
    return NULL;
  }}
  PyModule_AddFunctions(m, ModuleMethods);
  return m;
}}
"""

OPGEN_TILING_TEMPLATE = """
// 兼容cann的cpp编译版本
#define _GLIBCXX_USE_CXX11_ABI 0
#include <iostream>
#include <Python.h>

#include "register/tilingdata_base.h"
#include "exe_graph/runtime/storage_shape.h"
#include "graph/types.h"
#include "tiling/context/context_builder.h"
#include "tiling/platform/platform_ascendc.h"

using namespace std;
#define LOG(__level, __msg, ...) printf(__level __msg "\\n", ##__VA_ARGS__)
#define LOGI(__msg, ...) LOG("[INFO ] ", __msg, ##__VA_ARGS__)
#define LOGW(__msg, ...) LOG("[WARN ] ", __msg, ##__VA_ARGS__)
#define LOGE(__msg, ...) LOG("[ERROR] ", __msg, ##__VA_ARGS__)

static PyObject* _CallTilingFunc(PyObject* self, PyObject* args)
{{
    auto param = gert::TilingData::CreateCap(131072); // 大小和torch保持一致
    auto workspace_size_holer = gert::ContinuousVector::Create<size_t>(4096);
    auto ws_size = reinterpret_cast<gert::ContinuousVector *>(workspace_size_holer.get());

    auto holder = context_ascendc::ContextBuilder()
                                .NodeIoNum({node_io_num})
                                .IrInstanceNum({{{ir_instance_num}}}){tds}{attrs}
                                .SetOpNameType("name", "{op_type}")
                                .TilingData(param.get())
                                .Workspace(ws_size)
                                .AddPlatformInfo({soc_version})
                                .BuildTilingContext();
    if (holder == nullptr) {{
        LOGE("Create holder failed");
        Py_RETURN_NONE;
    }}
    auto tilingContext = holder->GetContext<gert::TilingContext>();
    if (tilingContext == nullptr) {{
        LOGE("Create tilingContext failed");
        Py_RETURN_NONE;
    }}

    // 默认值配置，防止用户没有主动设置时触发异常，blockdim默认值为0，用户未配置时会在python侧主动抛异常
    tilingContext->SetTilingKey(0);
    size_t *currentWorkspace = tilingContext->GetWorkspaceSizes(1);
    if (currentWorkspace == nullptr) {{
        LOGE("Create currentWorkspace failed");
        Py_RETURN_NONE;
    }}
    currentWorkspace[0] = 0;

    context_ascendc::OpTilingRegistry tmpIns;
    string libPath = "{lib_path}";
    if (!libPath.empty()) {{
        LOGI("Load tiling library %s", libPath.c_str());
        if (!tmpIns.LoadTilingLibrary(libPath.c_str())) {{
            LOGE("load tiling library failed, please ensure %s is valid", libPath.c_str());
            Py_RETURN_NONE;
        }}
    }}
    context_ascendc::TilingFunc tilingFunc = tmpIns.GetTilingFunc("{op_type}");
    if (tilingFunc == nullptr) {{
        LOGE("GetTilingFunc failed, op_type is {op_type}, please ensure mskl.tiling_func.lib_path"
             " contains your tiling func");
        Py_RETURN_NONE;
    }}
    ge::graphStatus ret = tilingFunc(tilingContext);
    if (ret != ge::GRAPH_SUCCESS) {{
        LOGE("TilingFunc execute failed, please enable plog to see details");
        Py_RETURN_NONE;
    }}

    // 创建Python字典
    PyObject* dict = PyDict_New();
    if (!dict) {{
        LOGE("Create python dict failed");
        Py_RETURN_NONE;
    }}

    PyObject* blockdim = PyLong_FromLong(tilingContext->GetBlockDim());
    PyObject* workspace_size = PyLong_FromUnsignedLong(tilingContext->GetWorkspaceSizes(1)[0]);
    PyObject* tiling_key = PyLong_FromUnsignedLong(tilingContext->GetTilingKey());
    auto rawTilingData = tilingContext->GetRawTilingData();
    if (rawTilingData == nullptr) {{
        LOGE("Create rawTilingData failed");
        Py_RETURN_NONE;
    }}
    auto size = rawTilingData->GetDataSize();
    PyObject* tiling_data = PyList_New(size);
    if (!blockdim || !workspace_size || !tiling_key || !tiling_data) {{
        Py_XDECREF(blockdim);
        Py_XDECREF(workspace_size);
        Py_XDECREF(tiling_key);
        Py_XDECREF(tiling_data);
        Py_DECREF(dict);
        LOGE("Create python values of dict failed");
        Py_RETURN_NONE;
    }}

    uint8_t* data = (uint8_t*)tilingContext->GetRawTilingData()->GetData();
    for (int i = 0; i < size; ++i) {{
        PyList_SET_ITEM(tiling_data, i, PyLong_FromUnsignedLong(data[i]));
    }}

    PyDict_SetItemString(dict, "blockdim", blockdim);
    PyDict_SetItemString(dict, "workspace_size", workspace_size);
    PyDict_SetItemString(dict, "tiling_data", tiling_data);
    PyDict_SetItemString(dict, "tiling_key", tiling_key);
    return dict;
}}

static PyMethodDef ModuleMethods[] = {{
    {{"_tiling_func", _CallTilingFunc, METH_VARARGS, "Entry point for tiling function"}},
    {{NULL, NULL, 0, NULL}}
}};

static struct PyModuleDef ModuleDef = {{
    PyModuleDef_HEAD_INIT,
    "_mskl_tiling_launcher",
    NULL,
    -1,
    ModuleMethods
}};

#if PY_VERSION_HEX < 0x03090000
extern "C" __attribute__((visibility("default"))) PyObject* PyInit__mskl_tiling_launcher(void)
#else
PyMODINIT_FUNC PyInit__mskl_tiling_launcher(void)
#endif
{{
    PyObject *m = PyModule_Create(&ModuleDef);
    if(m == NULL) {{
        return NULL;
    }}
    PyModule_AddFunctions(m, ModuleMethods);
    return m;
}}
"""

OPGEN_KERNEL_TEMPLATE_RT = """
#include <cstdlib>
#include <climits>
#include <iostream>
#include <vector>
#include <unordered_map>
#include <fstream>
#include <getopt.h>
#include <Python.h>
#include <dlfcn.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include "acl/acl.h"

using namespace std;

constexpr int rtDevBinaryMagicElf = 0x43554245U;
constexpr int rtDevBinaryMagicElfAivec = 0x41415246U;
constexpr int rtDevBinaryMagicElfAicube = 0x41494343U;
#define CHECK_RT_RESULT(result) if (!(result)) {{return false;}}
#define LOG(__level, __msg, ...) printf(__level __msg "\\n", ##__VA_ARGS__)
#define LOGI(__msg, ...) LOG("[INFO ] ", __msg, ##__VA_ARGS__)
#define LOGW(__msg, ...) LOG("[WARN ] ", __msg, ##__VA_ARGS__)
#define LOGE(__msg, ...) LOG("[ERROR] ", __msg, ##__VA_ARGS__)

typedef uint32_t rtError_t;
typedef void *rtStream_t;

typedef struct tagRtDevBinary {{
    uint32_t magic;
    uint32_t version;
    const void *data;
    uint64_t length;
}} rtDevBinary_t;

typedef struct tagRtSmData {{
    uint64_t L2_mirror_addr;          // preload or swap source addr
    uint32_t L2_data_section_size;    // every data size
    uint8_t L2_preload;               // 1 - preload from mirrorAddr, 0 - no preload
    uint8_t modified;                 // 1 - data will be modified by kernel, 0 - no modified
    uint8_t priority;                 // data priority
    int8_t prev_L2_page_offset_base;  // remap source section offset
    uint8_t L2_page_offset_base;      // remap destination section offset
    uint8_t L2_load_to_ddr;           // 1 - need load out, 0 - no need
    uint8_t reserved[2];              // reserved
}} rtSmData_t;

typedef struct rtHostInputInfo {{
    uint32_t addrOffset;
    uint32_t dataOffset;
}} rtHostInputInfo_t;

typedef struct tagRtArgsEx {{
    void *args;                     // args host mem addr
    rtHostInputInfo_t *hostInputInfoPtr;     // nullptr means no host mem input
    uint32_t argsSize;              // input + output + tiling addr size + tiling data size + host mem
    uint32_t tilingAddrOffset;      // tiling addr offset
    uint32_t tilingDataOffset;      // tiling data offset
    uint16_t hostInputInfoNum;      // hostInputInfo num
    uint8_t hasTiling;              // if has tiling: 0 means no tiling
    uint8_t isNoNeedH2DCopy;        // is no need host to device copy: 0 means need H2D copy,
    // others means doesn't need H2D copy.
    uint8_t reserved[4];
}} rtArgsEx_t;

typedef struct tagRtTaskCfgInfo {{
    uint8_t qos;
    uint8_t partId;
    uint8_t schemMode; // rtschemModeType_t 0:normal;1:batch;2:sync
    uint8_t res[1]; // res
}} rtTaskCfgInfo_t;

typedef struct tagRtSmCtrl {{
    rtSmData_t data[8];  // data description
    uint64_t size;       // max page Num
    uint8_t remap[64];   /* just using for static remap mode, default:0xFF
                            array index: virtual l2 page id, array value: physic l2 page id */
    uint8_t l2_in_main;  // 0-DDR, 1-L2, default:0xFF
    uint8_t reserved[3];
}} rtSmDesc_t;

struct OpgenKernelConfig {{
    uint64_t tilingKey {{0}};
    int blockDim {{0}};
    void *stream{{nullptr}};
    string kernelBinaryPath; // .o路径
    vector<void *> kernelArgs;
}};

extern "C" {{
rtError_t rtDevBinaryUnRegister(void *hdl);
rtError_t rtRegisterAllKernel(const rtDevBinary_t *bin, void **hdl);
rtError_t rtKernelLaunchWithHandleV2(void *hdl, const uint64_t tilingKey, uint32_t blockDim,
                                     rtArgsEx_t *argsInfo, rtSmDesc_t *smDesc, rtStream_t stm,
                                     const rtTaskCfgInfo_t *cfgInfo);
rtError_t rtGetC2cCtrlAddr(uint64_t *addr, uint32_t *fftsLen);
rtError_t rtGetSocVersion(char *version, const uint32_t maxLen);
}}
 
namespace Adx {{
void AdumpPrintWorkSpace(const void *workSpaceAddr, const size_t dumpWorkSpaceSize,
                         rtStream_t stream, const char *opType);
}}

size_t GetFileSize(const string &filePath)
{{
    struct stat fileStat;
    if (stat(filePath.c_str(), &fileStat) != 0 || !S_ISREG(fileStat.st_mode)) {{
        return 0;
    }}
    return static_cast<size_t>(fileStat.st_size);
}}

size_t ReadBinary(string const &filename, vector<char> &data)
{{
    ifstream ifs(filename, ios::binary);
    if (!ifs.is_open()) {{
        return 0;
    }}
    ifs.seekg(0, ifstream::end);
    int64_t length = ifs.tellg();
    if (length < 0) {{
        return 0;
    }}
    ifs.seekg(0, ifstream::beg);
    data.resize(length);
    ifs.read(data.data(), length);
    return length;
}}

bool PipeCall(vector<string> const &cmd, string &output)
{{
    int pipeStdout[2];
    if (pipe(pipeStdout) != 0) {{
        return false;
    }}
    pid_t pid = fork();
    if (pid < 0) {{
        return false;
    }} else if (pid == 0) {{
        unsetenv("LD_PRELOAD");
        dup2(pipeStdout[1], STDOUT_FILENO);
        dup2(STDOUT_FILENO, STDERR_FILENO);
        close(pipeStdout[0]);
        close(pipeStdout[1]);

        std::vector<char *> rawArgv;
        for (auto const &arg: cmd) {{
            rawArgv.emplace_back(const_cast<char *>(arg.data()));
        }}
        rawArgv.emplace_back(nullptr);
        execvp(cmd[0].c_str(), rawArgv.data());
        _exit(EXIT_FAILURE);
    }} else {{
        close(pipeStdout[1]);

        constexpr std::size_t bufLen = 256UL;
        char buf[bufLen] = {{'\\0'}};
        ssize_t nBytes = 0L;
        for (; (nBytes = read(pipeStdout[0], buf, bufLen)) > 0L;) {{
            output.append(buf, static_cast<std::size_t>(nBytes));
        }}
        close(pipeStdout[0]);

        int status;
        waitpid(pid, &status, 0);
        return WIFEXITED(status) && WEXITSTATUS(status) == 0;
    }}
}}

class KernelRunner {{
public:
    KernelRunner()
    {{
        constexpr uint64_t socVersionBufLen = 64UL;
        char socVersion[socVersionBufLen] = "";
        if (CheckRtResult(rtGetSocVersion(socVersion, sizeof(socVersion)), "rtGetSocVersion")) {{
            soc = socVersion;
            if (soc.empty()) {{
                LOGE("rtGetSocVersion failed, soc-version is empty");
            }}
        }}
        if (magic == 0) {{
            string fixStr = "input [kernel_type] in [mskl.get_kernel_from_binary] manually.";
            if (!soc.empty() && soc.find("Ascend310P") != string::npos) {{
                LOGI("Set kernel_type as mix, you can change this value by %s", fixStr.c_str());
                magic = rtDevBinaryMagicElf;
            }} else {{
                string mixTag = "_mix_";
                vector<string> cmd = {{"llvm-objdump", "-t", "{kernel_binary_file}"}};
                string output;
                if (!PipeCall(cmd, output)) {{
                    LOGE("Get magic from [kernel_binary_file] failed, please %s", fixStr.c_str());
                }} else if (output.find(mixTag, output.find("SYMBOL TABLE:")) != string::npos) {{ // 避免文件名的影响
                    LOGI("Set kernel_type as mix, you can change this value by %s", fixStr.c_str());
                    magic = rtDevBinaryMagicElf;
                }} else {{
                    LOGI("Set kernel_type as vec, you can change this value by %s", fixStr.c_str());
                    magic = rtDevBinaryMagicElfAivec;
                }}
            }}
        }}
    }}

    bool PyRun(const OpgenKernelConfig& config)
    {{
        if (!needUnRegisterDevBinary_) {{
            // register kernel
            size_t fileSize = GetFileSize(config.kernelBinaryPath);
            vector<char> bin;
            if (ReadBinary(config.kernelBinaryPath, bin) == 0) {{
                return false;
            }}
            if (!RegisterKernel(config, bin, fileSize)) {{
                return false;
            }}
        }}
        if (!LaunchKernel(config)) {{
            return false;
        }}
        return true;
    }}

    ~KernelRunner()
    {{
        if (needUnRegisterDevBinary_) {{
            CheckRtResult(rtDevBinaryUnRegister(binHandle_), "rtDevBinaryUnRegister");
        }}
    }}

private:
    bool RegisterKernel(const OpgenKernelConfig &kernelConfig, const vector<char> &data, uint64_t fileSize)
    {{
        rtDevBinary_t deviceBinary {{}};
        deviceBinary.version = 0;
        deviceBinary.data = data.data();
        deviceBinary.magic = magic;
        deviceBinary.length = fileSize;
        CHECK_RT_RESULT(CheckRtResult(rtRegisterAllKernel(&deviceBinary, &binHandle_), "rtRegisterAllKernel"));
        needUnRegisterDevBinary_ = true;
        return true;
    }}

    bool LaunchKernel(const OpgenKernelConfig &kernelConfig)
    {{
        kernelArgs_.clear();
        if (soc.find("Ascend910B") != string::npos && (magic != rtDevBinaryMagicElfAivec)) {{
            // 910B非vec算子，需要在第一个入参传入ffts地址
            InitFftsAddr();
        }}


        if (soc.find("Ascend310P") != string::npos) {{
            // 310P关闭overflow
            int err = aclrtSetStreamOverflowSwitch(kernelConfig.stream, 0);
            if (err != 0) {{
                LOGE("Call aclrtSetStreamOverflowSwitch failed, error code: %d", err);
                return false;
            }}
        }}

        kernelArgs_.insert(kernelArgs_.end(), kernelConfig.kernelArgs.begin(), kernelConfig.kernelArgs.end());
        rtArgsEx_t argsEx {{}};
        argsEx.args = kernelArgs_.data();
        argsEx.hostInputInfoPtr = nullptr;
        argsEx.argsSize = kernelArgs_.size() * sizeof(void*);
        argsEx.hasTiling = 0;
        argsEx.isNoNeedH2DCopy = 0; // args指针本身指向host，依然需要h2dcopy
        CHECK_RT_RESULT(CheckRtResult(
            rtKernelLaunchWithHandleV2(binHandle_, kernelConfig.tilingKey,
                                       kernelConfig.blockDim, &argsEx, nullptr,
                                       kernelConfig.stream, nullptr),
            "rtKernelLaunchWithHandleV2"));

        if ({enable_printf}) {{
            if (kernelArgs_.size() < 2) {{
                LOGW("kernel args smaller than 2, disable ASCENDC::printf ability.");
                return true;
            }}
            void *workspace = kernelArgs_[kernelArgs_.size() - 2U];
            uint32_t debugBufferSize = 75 * 1024 * 1024;
            Adx::AdumpPrintWorkSpace(workspace, debugBufferSize, kernelConfig.stream, "{op_type}");
        }}
        return true;
    }}

    bool InitFftsAddr()
    {{
        uint64_t addr;
        uint32_t addrLen;
        CHECK_RT_RESULT(CheckRtResult(rtGetC2cCtrlAddr(&addr, &addrLen), "rtGetC2cCtrlAddr"))
        kernelArgs_.emplace_back(reinterpret_cast<void *>(addr));
        return true;
    }}

    bool CheckRtResult(rtError_t result, const string &apiName)
    {{
        if (result == 0) {{
            return true;
        }}
        LOGE("Runtime API call %s() failed. error code: %d", apiName.c_str(), result);
        return false;
    }}

    void *binHandle_ = nullptr;
    bool needUnRegisterDevBinary_ = false;
    vector<void *> kernelArgs_;
    string soc;
    uint32_t magic = {magic};
}};

static PyObject* _launch_kernel(PyObject* self, PyObject* args)
{{
    Py_ssize_t size = PyTuple_Size(args);
    if (size < 3) {{
        // 至少传入blockdim, l2ctrl, stream 3个入参
        std::string errorStr = "size of args is " + std::to_string(size) + ". it must be not less than 3";
        PyErr_SetString(PyExc_ValueError, errorStr.c_str());
        Py_RETURN_NONE;
    }}
    std::vector<void *> pyArgs;
    pyArgs.reserve(size);

    for (Py_ssize_t i = 0; i < size; i++) {{
        PyObject* item = PyTuple_GetItem(args, i);
        if (!PyLong_Check(item)) {{
            PyErr_SetString(PyExc_TypeError, "All arguments must be integers");
            Py_RETURN_NONE;
        }}
        void *temp = PyLong_AsVoidPtr(item);
        pyArgs.push_back(temp);
    }}

    OpgenKernelConfig kernelConfig;
    kernelConfig.tilingKey = {tiling_key};
    kernelConfig.blockDim = (uint64_t)pyArgs[0];
    kernelConfig.stream = pyArgs[2];

    kernelConfig.kernelBinaryPath = "{kernel_binary_file}";
    std::vector<void *> kernelArgs(pyArgs.begin() + 3, pyArgs.end());
    kernelConfig.kernelArgs = kernelArgs;
    static KernelRunner kernelRunner;

    kernelRunner.PyRun(kernelConfig);
    Py_RETURN_NONE;
}}

static PyMethodDef ModuleMethods[] = {{
    {{"{kernel_name}", _launch_kernel, METH_VARARGS, "Entry point for kernel {kernel_name}"}},
    {{NULL, NULL, 0, NULL}}
}};

static struct PyModuleDef ModuleDef = {{
    PyModuleDef_HEAD_INIT,
    "_mskl_launcher",
    NULL,
    -1,
    ModuleMethods
}};

#if PY_VERSION_HEX < 0x03090000
extern "C" __attribute__((visibility("default"))) PyObject* PyInit__mskl_launcher(void)
#else
PyMODINIT_FUNC PyInit__mskl_launcher(void)
#endif
{{
    PyObject *m = PyModule_Create(&ModuleDef);
    if(m == NULL) {{
        return NULL;
    }}
    PyModule_AddFunctions(m, ModuleMethods);
    return m;
}}
"""

OPGEN_KERNEL_TEMPLATE_ACL_RT = """
#include <cstdlib>
#include <climits>
#include <iostream>
#include <vector>
#include <unordered_map>
#include <fstream>
#include <getopt.h>
#include <Python.h>
#include <dlfcn.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include "acl/acl.h"

using namespace std;

constexpr int rtDevBinaryMagicElf = 0x43554245U;
constexpr int rtDevBinaryMagicElfAivec = 0x41415246U;
constexpr int rtDevBinaryMagicElfAicube = 0x41494343U;
#define CHECK_RT_RESULT(result) if (!(result)) {{return false;}}
#define LOG(__level, __msg, ...) printf(__level __msg "\\n", ##__VA_ARGS__)
#define LOGI(__msg, ...) LOG("[INFO ] ", __msg, ##__VA_ARGS__)
#define LOGW(__msg, ...) LOG("[WARN ] ", __msg, ##__VA_ARGS__)
#define LOGE(__msg, ...) LOG("[ERROR] ", __msg, ##__VA_ARGS__)

typedef int aclError;
typedef void* aclrtStream;
typedef void* aclrtBinHandle;
typedef void* aclrtFuncHandle;
typedef void* aclrtArgsHandle;
typedef void* aclrtParamHandle;

struct OpgenKernelConfig {{
    uint64_t tilingKey {{0}};
    int blockDim {{0}};
    void *stream{{nullptr}};
    string kernelBinaryPath; // .o路径
    vector<void *> kernelArgs;
}};

extern "C" {{
const char *aclrtGetSocName();

aclError aclrtBinaryUnLoad(aclrtBinHandle binHandle);

aclError aclrtBinaryLoadFromFile(const char* binPath, aclrtBinaryLoadOptions *options, aclrtBinHandle *binHandle);

aclError aclrtLaunchKernelWithConfig(aclrtFuncHandle funcHandle, uint32_t blockDim, aclrtStream stream, 
                                         aclrtLaunchKernelCfg *cfg, aclrtArgsHandle argsHandle, void *reserve);

aclError aclrtKernelArgsInit(aclrtFuncHandle funcHandle, aclrtArgsHandle *argsHandle);

aclError aclrtBinaryGetFunctionByEntry(aclrtBinHandle binHandle, uint64_t funcEntry, aclrtFuncHandle *funcHandle);

aclError aclrtKernelArgsAppend(aclrtArgsHandle argsHandle, void *param, size_t paramSize, 
                                   aclrtParamHandle *paramHandle);

aclError aclrtKernelArgsFinalize(aclrtArgsHandle argsHandle);
}}
 
namespace Adx {{
void AdumpPrintWorkSpace(const void *workSpaceAddr, const size_t dumpWorkSpaceSize,
                         aclrtStream stream, const char *opType);
}}

class KernelRunner {{
public:
    KernelRunner()
    {{
        const char *socVersion = aclrtGetSocName();
        soc_ = (socVersion == nullptr) ? "" : socVersion;
        if (soc_.empty()) {{
            LOGE("aclrtGetSocName failed, soc version is empty");
        }}
    }}

    bool PyRun(const OpgenKernelConfig& config)
    {{
        if (!needUnRegisterDevBinary_) {{
            // register kernel
            if (!RegisterKernel(config, config.kernelBinaryPath)) {{
                return false;
            }}
        }}
        if (!LaunchKernel(config)) {{
            return false;
        }}
        return true;
    }}

    ~KernelRunner()
    {{
        if (needUnRegisterDevBinary_) {{
            CheckResult(aclrtBinaryUnLoad(binHandle_), "aclrtBinaryUnLoad");
        }}
    }}

private:
    bool RegisterKernel(const OpgenKernelConfig& kernelConfig, std::string const &filename)
    {{
        // 1 magic，ffts不用配置，ffts會通過meta段（aclnn）或者json文件获取
        CHECK_RT_RESULT(CheckResult(aclrtBinaryLoadFromFile(filename.c_str(), nullptr, &binHandle_), 
                                    "aclrtBinaryLoadFromFile"))
        // 2 kernelName 不能加_mix_aic/_mix_aiv
        CHECK_RT_RESULT(CheckResult(aclrtBinaryGetFunctionByEntry(binHandle_, kernelConfig.tilingKey, &funcHandle_), 
                                    "aclrtBinaryGetFunctionByEntry"))
        CHECK_RT_RESULT(CheckResult(aclrtKernelArgsInit(funcHandle_, &argsHandle_), "aclrtKernelArgsInit"))
        return true;
    }}

    bool LaunchKernel(const OpgenKernelConfig &kernelConfig)
    {{
        kernelArgs_.clear();
        if (soc_.find("Ascend310P") != string::npos) {{
            // 310P关闭overflow
            int err = aclrtSetStreamOverflowSwitch(kernelConfig.stream, 0);
            if (err != 0) {{
                LOGE("Call aclrtSetStreamOverflowSwitch failed, error code: %d", err);
                return false;
            }}
        }}

        kernelArgs_.insert(kernelArgs_.end(), kernelConfig.kernelArgs.begin(), kernelConfig.kernelArgs.end());
        aclrtParamHandle paramHandle;
        aclrtKernelArgsAppend(argsHandle_, kernelArgs_.data(), kernelArgs_.size() * 8, &paramHandle);
        aclrtKernelArgsFinalize(argsHandle_);
        CHECK_RT_RESULT(CheckResult(aclrtLaunchKernelWithConfig(funcHandle_, kernelConfig.blockDim, 
                                                                    kernelConfig.stream, nullptr, argsHandle_, nullptr), 
                                    "aclrtLaunchKernelWithConfig"))

        if ({enable_printf}) {{
            if (kernelArgs_.size() < 2) {{
                LOGW("kernel args smaller than 2, disable ASCENDC::printf ability.");
                return true;
            }}
            void *workspace = kernelArgs_[kernelArgs_.size() - 2U];
            uint32_t debugBufferSize = 75 * 1024 * 1024;
            Adx::AdumpPrintWorkSpace(workspace, debugBufferSize, kernelConfig.stream, "{op_type}");
        }}
        return true;
    }}

    bool CheckResult(aclError result, const string &apiName)
    {{
        if (result == 0) {{
            return true;
        }}
        LOGE("Runtime API call %s() failed. error code: %d", apiName.c_str(), result);
        return false;
    }}

    void *binHandle_ = nullptr;
    aclrtFuncHandle funcHandle_;
    aclrtArgsHandle argsHandle_;
    bool needUnRegisterDevBinary_ = false;
    vector<void *> kernelArgs_;
    string soc_;
    uint32_t magic_ = {magic};
}};

static PyObject* _launch_kernel(PyObject* self, PyObject* args)
{{
    Py_ssize_t size = PyTuple_Size(args);
    if (size < 3) {{
        // 至少传入blockdim, l2ctrl, stream 3个入参
        std::string errorStr = "size of args is " + std::to_string(size) + ". it must be not less than 3";
        PyErr_SetString(PyExc_ValueError, errorStr.c_str());
        Py_RETURN_NONE;
    }}
    std::vector<void *> pyArgs;
    pyArgs.reserve(size);

    for (Py_ssize_t i = 0; i < size; i++) {{
        PyObject* item = PyTuple_GetItem(args, i);
        if (!PyLong_Check(item)) {{
            PyErr_SetString(PyExc_TypeError, "All arguments must be integers");
            Py_RETURN_NONE;
        }}
        void *temp = PyLong_AsVoidPtr(item);
        pyArgs.push_back(temp);
    }}

    OpgenKernelConfig kernelConfig;
    kernelConfig.tilingKey = {tiling_key};
    kernelConfig.blockDim = (uint64_t)pyArgs[0];
    kernelConfig.stream = pyArgs[2];

    kernelConfig.kernelBinaryPath = "{kernel_binary_file}";
    std::vector<void *> kernelArgs(pyArgs.begin() + 3, pyArgs.end());
    kernelConfig.kernelArgs = kernelArgs;
    static KernelRunner kernelRunner;

    kernelRunner.PyRun(kernelConfig);
    Py_RETURN_NONE;
}}

static PyMethodDef ModuleMethods[] = {{
    {{"{kernel_name}", _launch_kernel, METH_VARARGS, "Entry point for kernel {kernel_name}"}},
    {{NULL, NULL, 0, NULL}}
}};

static struct PyModuleDef ModuleDef = {{
    PyModuleDef_HEAD_INIT,
    "_mskl_launcher",
    NULL,
    -1,
    ModuleMethods
}};

#if PY_VERSION_HEX < 0x03090000
extern "C" __attribute__((visibility("default"))) PyObject* PyInit__mskl_launcher(void)
#else
PyMODINIT_FUNC PyInit__mskl_launcher(void)
#endif
{{
    PyObject *m = PyModule_Create(&ModuleDef);
    if(m == NULL) {{
        return NULL;
    }}
    PyModule_AddFunctions(m, ModuleMethods);
    return m;
}}
"""
