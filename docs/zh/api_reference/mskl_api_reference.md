# MindStudio Kernel Launcher API接口文档

## 接口列表

msKL工具提供的接口可以调用msOpGen工程中的tiling函数以及用户自定义的Kernel函数，同时提供了autotune系列接口支持开发者可以高效地针对多个调优点进行代码替换、编译、运行以及性能对比。

**表 1**  msKL工具接口列表

<a name="table346304711151"></a>
<table><thead align="left"><tr id="row3463134731515"><th class="cellrowborder" valign="top" width="13.719999999999999%" id="mcps1.2.4.1.1"><p id="p16400184971711"><a name="p16400184971711"></a><a name="p16400184971711"></a>分类</p>
</th>
<th class="cellrowborder" valign="top" width="24.709999999999997%" id="mcps1.2.4.1.2"><p id="p546314712159"><a name="p546314712159"></a><a name="p546314712159"></a>接口</p>
</th>
<th class="cellrowborder" valign="top" width="61.57%" id="mcps1.2.4.1.3"><p id="p846354718154"><a name="p846354718154"></a><a name="p846354718154"></a>简介</p>
</th>
</tr>
</thead>
<tbody><tr id="row164631047141520"><td class="cellrowborder" rowspan="2" valign="top" width="13.719999999999999%" headers="mcps1.2.4.1.1 "><p id="p1740014991719"><a name="p1740014991719"></a><a name="p1740014991719"></a>调用msOpGen工程</p>
</td>
<td class="cellrowborder" valign="top" width="24.709999999999997%" headers="mcps1.2.4.1.2 "><p id="p159641852122517"><a name="p159641852122517"></a><a name="p159641852122517"></a><a href="#tiling_func">tiling_func</a></p>
</td>
<td class="cellrowborder" valign="top" width="61.57%" headers="mcps1.2.4.1.3 "><p id="p10463194791519"><a name="p10463194791519"></a><a name="p10463194791519"></a>调用用户的tiling函数。</p>
</td>
</tr>
<tr id="row646384741519"><td class="cellrowborder" valign="top" headers="mcps1.2.4.1.1 "><p id="p346319478152"><a name="p346319478152"></a><a name="p346319478152"></a><a href="#get_kernel_from_binary">get_kernel_from_binary</a></p>
</td>
<td class="cellrowborder" valign="top" headers="mcps1.2.4.1.2 "><p id="p738182655420"><a name="p738182655420"></a><a name="p738182655420"></a>生成一个可以调用用户Kernel函数的实例。</p>
</td>
</tr>
<tr id="row1146304781520"><td class="cellrowborder" rowspan="5" valign="top" width="13.719999999999999%" headers="mcps1.2.4.1.1 "><p id="p840054919173"><a name="p840054919173"></a><a name="p840054919173"></a>自动调优</p>
</td>
<td class="cellrowborder" valign="top" width="24.709999999999997%" headers="mcps1.2.4.1.2 "><p id="p13463947101520"><a name="p13463947101520"></a><a name="p13463947101520"></a><a href="#autotune">autotune</a></p>
</td>
<td class="cellrowborder" valign="top" width="61.57%" headers="mcps1.2.4.1.3 "><p id="p946344718154"><a name="p946344718154"></a><a name="p946344718154"></a>遍历搜索空间，尝试不同参数组合，展示每个组合的运行耗时与最优组合。</p>
</td>
</tr>
<tr id="row346374791514"><td class="cellrowborder" valign="top" headers="mcps1.2.4.1.1 "><p id="p164631847111511"><a name="p164631847111511"></a><a name="p164631847111511"></a><a href="#code_gen">code_gen</a></p>
</td>
<td class="cellrowborder" valign="top" headers="mcps1.2.4.1.2 "><p id="p08721713202710"><a name="p08721713202710"></a><a name="p08721713202710"></a>根据输入的模板库Kernel信息，生成Kernel下发代码。</p>
</td>
</tr>
<tr id="row20464124714154"><td class="cellrowborder" valign="top" headers="mcps1.2.4.1.1 "><p id="p174641247101518"><a name="p174641247101518"></a><a name="p174641247101518"></a><a href="#code_gen">compile</a></p>
</td>
<td class="cellrowborder" valign="top" headers="mcps1.2.4.1.2 "><p id="p246494721513"><a name="p246494721513"></a><a name="p246494721513"></a>编译Kernel下发代码，返回一个可执行的Kernel对象。</p>
</td>
</tr>
<tr id="row13464104712157"><td class="cellrowborder" valign="top" headers="mcps1.2.4.1.1 "><p id="p346454771512"><a name="p346454771512"></a><a name="p346454771512"></a><a href="#autotune_v2">autotune_v2</a></p>
</td>
<td class="cellrowborder" valign="top" headers="mcps1.2.4.1.2 "><p id="p8464164721515"><a name="p8464164721515"></a><a name="p8464164721515"></a>遍历搜索空间，尝试不同参数组合，展示每个组合的运行耗时与最优组合。</p>
</td>
</tr>
<tr id="row111881548132610"><td class="cellrowborder" valign="top" headers="mcps1.2.4.1.1 "><p id="p218954811261"><a name="p218954811261"></a><a name="p218954811261"></a><a href="#compile_executable">compile_executable</a></p>
</td>
<td class="cellrowborder" valign="top" headers="mcps1.2.4.1.2 "><p id="p11177221143010"><a name="p11177221143010"></a><a name="p11177221143010"></a>编译代码，返回一个可执行的executable对象。</p>
</td>
</tr>
</tbody>
</table>

## 接口详情

## tiling_func

**功能说明**

调用用户的tiling函数。

> [!NOTE]   
> tiling_func不支持调用《[基础数据结构和接口参考](https://www.hiascend.com/document/detail/zh/canncommercial/83RC1/API/basicdataapi/atlasopapi_07_00001.html)》中的GetCompileInfo接口。

**函数原型**

```python
def tiling_func(op_type: str, inputs: list, outputs: list, lib_path: str,
                inputs_info: list = None, outputs_info: list = None, attr=None, soc_version: str = None) -> TilingOutput
```

**参数说明**

<a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_table438764393513"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_row53871743113510"><th class="cellrowborder" valign="top" width="17.16%" id="mcps1.1.5.1.1"><p id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"></a><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="10.05%" id="mcps1.1.5.1.2"><p id="zh-cn_topic_0000001693276536_p1769255516412"><a name="zh-cn_topic_0000001693276536_p1769255516412"></a><a name="zh-cn_topic_0000001693276536_p1769255516412"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="7.5200000000000005%" id="mcps1.1.5.1.3"><p id="p108901947143015"><a name="p108901947143015"></a><a name="p108901947143015"></a>是否必选</p>
</th>
<th class="cellrowborder" valign="top" width="65.27%" id="mcps1.1.5.1.4"><p id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"></a><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_row2038874343514"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p347712308281"><a name="p347712308281"></a><a name="p347712308281"></a>op_type</p>
</td>
<td class="cellrowborder" valign="top" width="10.05%" headers="mcps1.1.5.1.2 "><p id="p1239865692418"><a name="p1239865692418"></a><a name="p1239865692418"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p68900476301"><a name="p68900476301"></a><a name="p68900476301"></a>必选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.27%" headers="mcps1.1.5.1.4 "><p id="p06801243152810"><a name="p06801243152810"></a><a name="p06801243152810"></a>需根据tiling函数的实现填写，例如AddCustom、 MatmulLeakyreluCustom等。msKL工具查找tiling函数的唯一依据，查找逻辑请参见lib_path参数。</p>
<p id="p960565114599"><a name="p960565114599"></a><a name="p960565114599"></a>数据类型：str。</p>
<div class="note" id="note097633611110"><a name="note097633611110"></a><a name="note097633611110"></a><span class="notetitle"> 说明： </span><div class="notebody"><p id="p16976163613117"><a name="p16976163613117"></a><a name="p16976163613117"></a>若CANN中曾经部署过相同类型的算子（op_type），用户修改了tiling函数并重新编译，则需要在CANN环境中重新部署该算子。</p>
</div></div>
</td>
</tr>
<tr id="row6580171015371"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p591114213019"><a name="p591114213019"></a><a name="p591114213019"></a>inputs</p>
</td>
<td class="cellrowborder" valign="top" width="10.05%" headers="mcps1.1.5.1.2 "><p id="p7393552113017"><a name="p7393552113017"></a><a name="p7393552113017"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p1144119163112"><a name="p1144119163112"></a><a name="p1144119163112"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.27%" headers="mcps1.1.5.1.4 "><p id="p1460753613473"><a name="p1460753613473"></a><a name="p1460753613473"></a>按Kernel函数入参顺序填入tensor信息，不使用某个参数的情况，对应位置请传入None占位。</p>
<p id="p3487952194619"><a name="p3487952194619"></a><a name="p3487952194619"></a>数据类型为list，每个元素必须是tensor或者list[tensor]，不在inputs_info中显式指定format或者ori_format时，所有tensor默认为ND格式。</p>
</td>
</tr>
<tr id="row12581151053712"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p7447858316"><a name="p7447858316"></a><a name="p7447858316"></a>outputs</p>
</td>
<td class="cellrowborder" valign="top" width="10.05%" headers="mcps1.1.5.1.2 "><p id="p311131173914"><a name="p311131173914"></a><a name="p311131173914"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p108911747123017"><a name="p108911747123017"></a><a name="p108911747123017"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.27%" headers="mcps1.1.5.1.4 "><p id="p1584018241204"><a name="p1584018241204"></a><a name="p1584018241204"></a>按Kernel函数入参顺序填入tensor信息，不使用某个参数的情况，对应位置请传入None占位。</p>
<p id="p1584002417011"><a name="p1584002417011"></a><a name="p1584002417011"></a>数据类型：list，每个元素必须是tensor或者list[tensor]，不在inputs_info中显式指定format或者ori_format时，所有tensor默认为ND格式。</p>
</td>
</tr>
<tr id="row194484772915"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p1644857162911"><a name="p1644857162911"></a><a name="p1644857162911"></a>inputs_info</p>
</td>
<td class="cellrowborder" valign="top" width="10.05%" headers="mcps1.1.5.1.2 "><p id="p19448137102917"><a name="p19448137102917"></a><a name="p19448137102917"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p4454173572815"><a name="p4454173572815"></a><a name="p4454173572815"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.27%" headers="mcps1.1.5.1.4 "><p id="p78715445203"><a name="p78715445203"></a><a name="p78715445203"></a>按Kernel函数入参顺序填写info信息，不使用某个参数的情况，对应位置请传入空dict或者None占位。</p>
<p id="p13310162672216"><a name="p13310162672216"></a><a name="p13310162672216"></a>数据类型为list，inputs_info参数中元素的数据类型为dict或list[dict]，每个dict的元素说明如下：</p>
<a name="ul2530132811195"></a><a name="ul2530132811195"></a><ul id="ul2530132811195"><li>ori_shape：输入tensor的原始维度信息。</li><li>shape：输入tensor运行时的维度信息。</li><li>dtype：输入tensor的数据类型，具体请参见《<a href="https://www.hiascend.com/document/detail/zh/canncommercial/83RC1/API/aicpuopapi/opdevapi_07_0000.html" target="_blank" rel="noopener noreferrer">TBE&amp;AI CPU算子开发接口</a>》的“AI CPU API &gt; 数据类型描述 &gt; DataType”。</li><li>ori_format：输入tensor的原始数据排布格式，默认为ND，具体请参见《<a href="https://www.hiascend.com/document/detail/zh/canncommercial/83RC1/API/aicpuopapi/opdevapi_07_0000.html" target="_blank" rel="noopener noreferrer">TBE&amp;AI CPU算子开发接口</a>》的“AI CPU API &gt; 数据类型描述 &gt; Format”。</li><li>format：输入tensor的数据排布格式，默认为ND，具体请参见《<a href="https://www.hiascend.com/document/detail/zh/canncommercial/83RC1/API/aicpuopapi/opdevapi_07_0000.html" target="_blank" rel="noopener noreferrer">TBE&amp;AI CPU算子开发接口</a>》的“AI CPU API &gt; 数据类型描述 &gt; Format”。</li><li>data_path：值依赖场景下，输入tensor的bin文件路径。</li></ul>
<p id="p13712155918416"><a name="p13712155918416"></a><a name="p13712155918416"></a>举例如下：</p>
<pre class="screen" id="screen3308253114112"><a name="screen3308253114112"></a><a name="screen3308253114112"></a>[{"ori_shape": [8, 2048], "shape": [8, 2048], "dtype": "float16", "ori_format": "ND", "format": "ND"},
 {"ori_shape": [8, 2048], "shape": [8, 2048], "dtype": "float16", "ori_format": "ND", "format": "ND"}]</pre>
<div class="note" id="note671620416381"><a name="note671620416381"></a><a name="note671620416381"></a><span class="notetitle"> 说明： </span><div class="notebody"><p id="p96594417491"><a name="p96594417491"></a><a name="p96594417491"></a>该输入参数和inputs存在约束关系：</p>
<a name="ul16532149133815"></a><a name="ul16532149133815"></a><ul id="ul16532149133815"><li>inputs为tensor时，inputs_info必须是dict。</li><li>inputs为list[tensor]时，inputs_info必须是list[dict]。</li><li>inputs为None时，inputs_info每个元素至少包含[shape, dtype]。</li></ul>
</div></div>
</td>
</tr>
<tr id="row119971375335"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p11687111419301"><a name="p11687111419301"></a><a name="p11687111419301"></a>outputs_info</p>
</td>
<td class="cellrowborder" valign="top" width="10.05%" headers="mcps1.1.5.1.2 "><p id="p268717140308"><a name="p268717140308"></a><a name="p268717140308"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p1111845113020"><a name="p1111845113020"></a><a name="p1111845113020"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.27%" headers="mcps1.1.5.1.4 "><p id="p177915263323"><a name="p177915263323"></a><a name="p177915263323"></a>存放输出的信息，不使用某个参数的情况，对应位置请传入空dict占位。</p>
<p id="p93662273465"><a name="p93662273465"></a><a name="p93662273465"></a>数据类型为list，outputs_info参数中元素的数据类型为dict或list[dict]，每个dict的元素说明如下：</p>
<a name="ul7773111912299"></a><a name="ul7773111912299"></a><ul id="ul7773111912299"><li>ori_shape：输出tensor的原始维度信息。</li></ul>
<a name="ul35937441232"></a><a name="ul35937441232"></a><ul id="ul35937441232"><li>shape：输出tensor的维度信息。</li><li>dtype：输出tensor的数据类型，具体请参见《<a href="https://www.hiascend.com/document/detail/zh/canncommercial/83RC1/API/aicpuopapi/opdevapi_07_0000.html" target="_blank" rel="noopener noreferrer">TBE&amp;AI CPU算子开发接口</a>》的“AI CPU API &gt; 数据类型描述 &gt; DataType”。</li><li>ori_format：输出tensor的原始数据排布格式，默认为ND，具体请参见《<a href="https://www.hiascend.com/document/detail/zh/canncommercial/83RC1/API/aicpuopapi/opdevapi_07_0000.html" target="_blank" rel="noopener noreferrer">TBE&amp;AI CPU算子开发接口</a>》的“AI CPU API &gt; 数据类型描述 &gt; Format”。</li><li>format：输出tensor的数据排布格式，默认为ND，具体请参见《<a href="https://www.hiascend.com/document/detail/zh/canncommercial/83RC1/API/aicpuopapi/opdevapi_07_0000.html" target="_blank" rel="noopener noreferrer">TBE&amp;AI CPU算子开发接口</a>》的“AI CPU API &gt; 数据类型描述 &gt; Format”。</li><li>data_path：保留参数，不生效。</li></ul>
<p id="p2593344172319"><a name="p2593344172319"></a><a name="p2593344172319"></a>举例如下：</p>
<pre class="screen" id="screen4593204420235"><a name="screen4593204420235"></a><a name="screen4593204420235"></a>[{"shape": [8, 2048], "dtype": "float16", "format": "ND"},
 {"shape": [8, 2048], "dtype": "float16", "format": "ND"}]</pre>
<div class="note" id="note103734543279"><a name="note103734543279"></a><a name="note103734543279"></a><span class="notetitle"> 说明： </span><div class="notebody"><p id="p4177193217280"><a name="p4177193217280"></a><a name="p4177193217280"></a>该输入参数和inputs存在约束关系：</p>
<a name="ul71771332122810"></a><a name="ul71771332122810"></a><ul id="ul71771332122810"><li>outputs为tensor时，outputs_info必须是dict。</li><li>outputs为list[tensor]时，outputs_info必须是list[dict]。</li><li>outputs为None时，outputs_info每个元素至少包含[shape, dtype]。</li></ul>
</div></div>
</td>
</tr>
<tr id="row18424152423119"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p134244248313"><a name="p134244248313"></a><a name="p134244248313"></a>attr</p>
</td>
<td class="cellrowborder" valign="top" width="10.05%" headers="mcps1.1.5.1.2 "><p id="p7424424103114"><a name="p7424424103114"></a><a name="p7424424103114"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p343822113116"><a name="p343822113116"></a><a name="p343822113116"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.27%" headers="mcps1.1.5.1.4 "><p id="p15489104015310"><a name="p15489104015310"></a><a name="p15489104015310"></a>tiling函数使用到的算子属性。</p>
<p id="p153601257151012"><a name="p153601257151012"></a><a name="p153601257151012"></a>数据类型：dict或者list。</p>
<div class="note" id="note098955612145"><a name="note098955612145"></a><a name="note098955612145"></a><span class="notetitle"> 说明： </span><div class="notebody"><a name="ul128741250201618"></a><a name="ul128741250201618"></a><ul id="ul128741250201618"><li>dict格式键值只能包含大小写英文字母、数字、下划线。<pre class="screen" id="screen196732811517"><a name="screen196732811517"></a><a name="screen196732811517"></a>{
  "a1": 1,
  "a2": False,
  "a3": "ssss",
  "a4": 1.2,
  "a5": [111, 222, 333],
  "a6": [111.111, 111.222, 111.333],
  "a7": [True, False],
  "a8": ["asdf", "zxcv"],
  "a9": [[1, 2, 3, 4], [5, 6, 7, 8], [5646, 2345]],
}</pre>
</li><li>list格式，推荐使用。若某个attr需要传空列表时，必须用这种格式（例如下面的"a10"）。<a name="ul1835813329193"></a><a name="ul1835813329193"></a><ul id="ul1835813329193"><li>"name"和"value"的值只能包含大小写英文字母、数字、下划线。</li><li>"dtype"：输入tensor的数据类型。</li></ul>
<pre class="screen" id="screen5163145104812"><a name="screen5163145104812"></a><a name="screen5163145104812"></a>[
  {"name": "a1", "dtype": "int", "value": 1},
  {"name": "a2", "dtype": "bool", "value": False},
  {"name": "a3", "dtype": "str", "value": "ssss"},
  {"name": "a4", "dtype": "float", "value": 1.2},
  {"name": "a5", "dtype": "list_float", "value": [111.111, 111.222, 111.333]},
  {"name": "a6", "dtype": "list_bool", "value": [True, False]},
  {"name": "a7", "dtype": "list_str", "value": ["asdf", "zxcv"]},
  {"name": "a8", "dtype": "list_list_int", "value": [[1, 2, 3, 4], [5, 6, 7, 8], [5646, 2345]]},
  {"name": "a9", "dtype": "list_int", "value": [111, 222, 333]},
  {"name": "a10", "dtype": "list_int", "value": []},
  {"name": "a11", "dtype": "int64", "value": 2},
  {"name": "a12", "dtype": "float32", "value": 1.3},
  {"name": "a13", "dtype": "string", "value": "ssss"},
  {"name": "a14", "dtype": "list_string", "value": ["asdf", "zxcv"]},
]</pre>
</li></ul>
</div></div>
</td>
</tr>
<tr id="row144311943183112"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p7431104393113"><a name="p7431104393113"></a><a name="p7431104393113"></a>lib_path</p>
</td>
<td class="cellrowborder" valign="top" width="10.05%" headers="mcps1.1.5.1.2 "><p id="p611375714315"><a name="p611375714315"></a><a name="p611375714315"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p14829330143515"><a name="p14829330143515"></a><a name="p14829330143515"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.27%" headers="mcps1.1.5.1.4 "><p id="p16858115495219"><a name="p16858115495219"></a><a name="p16858115495219"></a>msOpGen工程编译生成的liboptiling.so文件的路径，可在工程目录下通过<strong id="b8137203510342"><a name="b8137203510342"></a><a name="b8137203510342"></a>find . -name 'liboptiling.so'</strong>进行查找。msKL工具会按已部署算子、<strong id="b1026950296"><a name="b1026950296"></a><a name="b1026950296"></a>.so</strong>文件的查找顺序获取用户tiling函数。</p>
<p id="p2026182761114"><a name="p2026182761114"></a><a name="p2026182761114"></a>数据类型：str。</p>
</td>
</tr>
<tr id="row331912112322"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p18319161123219"><a name="p18319161123219"></a><a name="p18319161123219"></a>soc_version</p>
</td>
<td class="cellrowborder" valign="top" width="10.05%" headers="mcps1.1.5.1.2 "><p id="p0700152183213"><a name="p0700152183213"></a><a name="p0700152183213"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p13705103352112"><a name="p13705103352112"></a><a name="p13705103352112"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.27%" headers="mcps1.1.5.1.4 "><p id="zh-cn_topic_0000001821790281_p106751081205"><a name="zh-cn_topic_0000001821790281_p106751081205"></a><a name="zh-cn_topic_0000001821790281_p106751081205"></a>配置为<span id="zh-cn_topic_0000001821790281_ph667548162017"><a name="zh-cn_topic_0000001821790281_ph667548162017"></a><a name="zh-cn_topic_0000001821790281_ph667548162017"></a>昇腾AI处理器</span>的类型。</p>
<div class="note" id="zh-cn_topic_0000001821790281_note481620356579"><a name="zh-cn_topic_0000001821790281_note481620356579"></a><a name="zh-cn_topic_0000001821790281_note481620356579"></a><span class="notetitle"> 说明： </span><div class="notebody"><a name="ul1553919272419"></a><a name="ul1553919272419"></a><ul id="ul1553919272419"><li>非<span id="zh-cn_topic_0000002015877373_ph4604666416"><a name="zh-cn_topic_0000002015877373_ph4604666416"></a><a name="zh-cn_topic_0000002015877373_ph4604666416"></a><span id="zh-cn_topic_0000002015877373_zh-cn_topic_0000001740005657_ph11939124012202"><a name="zh-cn_topic_0000002015877373_zh-cn_topic_0000001740005657_ph11939124012202"></a><a name="zh-cn_topic_0000002015877373_zh-cn_topic_0000001740005657_ph11939124012202"></a><term id="zh-cn_topic_0000002015877373_zh-cn_topic_0000001312391781_term1253731311225"><a name="zh-cn_topic_0000002015877373_zh-cn_topic_0000001312391781_term1253731311225"></a><a name="zh-cn_topic_0000002015877373_zh-cn_topic_0000001312391781_term1253731311225"></a>Atlas A3 训练系列产品</term>/<term id="zh-cn_topic_0000002015877373_zh-cn_topic_0000001312391781_term131434243115"><a name="zh-cn_topic_0000002015877373_zh-cn_topic_0000001312391781_term131434243115"></a><a name="zh-cn_topic_0000002015877373_zh-cn_topic_0000001312391781_term131434243115"></a>Atlas A3 推理系列产品</term></span></span>：在安装<span id="zh-cn_topic_0000002015877373_ph26061361142"><a name="zh-cn_topic_0000002015877373_ph26061361142"></a><a name="zh-cn_topic_0000002015877373_ph26061361142"></a>昇腾AI处理器</span>的服务器执行<strong id="zh-cn_topic_0000002015877373_b116061067419"><a name="zh-cn_topic_0000002015877373_b116061067419"></a><a name="zh-cn_topic_0000002015877373_b116061067419"></a>npu-smi info</strong>命令进行查询，获取<strong id="zh-cn_topic_0000002015877373_b15606662046"><a name="zh-cn_topic_0000002015877373_b15606662046"></a><a name="zh-cn_topic_0000002015877373_b15606662046"></a>Chip Name</strong>信息。实际配置值为AscendChip Name，例如<strong id="zh-cn_topic_0000002015877373_b186061865415"><a name="zh-cn_topic_0000002015877373_b186061865415"></a><a name="zh-cn_topic_0000002015877373_b186061865415"></a>Chip Name</strong>取值为<em id="zh-cn_topic_0000002015877373_i1560656248"><a name="zh-cn_topic_0000002015877373_i1560656248"></a><a name="zh-cn_topic_0000002015877373_i1560656248"></a>xxxyy</em>，实际配置值为Ascend<em id="zh-cn_topic_0000002015877373_i9606666418"><a name="zh-cn_topic_0000002015877373_i9606666418"></a><a name="zh-cn_topic_0000002015877373_i9606666418"></a>xxxyy</em>。当Ascendxxxyy为代码样例的路径时，需要配置为ascend<em id="zh-cn_topic_0000002015877373_zh-cn_topic_0000002163321669_i111162923510"><a name="zh-cn_topic_0000002015877373_zh-cn_topic_0000002163321669_i111162923510"></a><a name="zh-cn_topic_0000002015877373_zh-cn_topic_0000002163321669_i111162923510"></a>xxxyy</em>。</li><li><span id="zh-cn_topic_0000002015877373_ph31312041180"><a name="zh-cn_topic_0000002015877373_ph31312041180"></a><a name="zh-cn_topic_0000002015877373_ph31312041180"></a><term id="zh-cn_topic_0000002015877373_zh-cn_topic_0000001312391781_term1253731311225_1"><a name="zh-cn_topic_0000002015877373_zh-cn_topic_0000001312391781_term1253731311225_1"></a><a name="zh-cn_topic_0000002015877373_zh-cn_topic_0000001312391781_term1253731311225_1"></a>Atlas A3 训练系列产品</term>/<term id="zh-cn_topic_0000002015877373_zh-cn_topic_0000001312391781_term131434243115_1"><a name="zh-cn_topic_0000002015877373_zh-cn_topic_0000001312391781_term131434243115_1"></a><a name="zh-cn_topic_0000002015877373_zh-cn_topic_0000001312391781_term131434243115_1"></a>Atlas A3 推理系列产品</term></span>：在安装<span id="zh-cn_topic_0000002015877373_ph151115122044"><a name="zh-cn_topic_0000002015877373_ph151115122044"></a><a name="zh-cn_topic_0000002015877373_ph151115122044"></a>昇腾AI处理器</span>的服务器执行<strong id="zh-cn_topic_0000002015877373_b6114127415"><a name="zh-cn_topic_0000002015877373_b6114127415"></a><a name="zh-cn_topic_0000002015877373_b6114127415"></a>npu-smi info -t board -i </strong><em id="zh-cn_topic_0000002015877373_i611191210417"><a name="zh-cn_topic_0000002015877373_i611191210417"></a><a name="zh-cn_topic_0000002015877373_i611191210417"></a>id</em><strong id="zh-cn_topic_0000002015877373_b1612131210413"><a name="zh-cn_topic_0000002015877373_b1612131210413"></a><a name="zh-cn_topic_0000002015877373_b1612131210413"></a> -c </strong><em id="zh-cn_topic_0000002015877373_i191261213417"><a name="zh-cn_topic_0000002015877373_i191261213417"></a><a name="zh-cn_topic_0000002015877373_i191261213417"></a>chip_id</em>命令进行查询，获取<strong id="zh-cn_topic_0000002015877373_b312111217419"><a name="zh-cn_topic_0000002015877373_b312111217419"></a><a name="zh-cn_topic_0000002015877373_b312111217419"></a>Chip Name</strong>和<strong id="zh-cn_topic_0000002015877373_b16123129419"><a name="zh-cn_topic_0000002015877373_b16123129419"></a><a name="zh-cn_topic_0000002015877373_b16123129419"></a>NPU Name</strong>信息，实际配置值为Chip Name_NPU Name。例如<strong id="zh-cn_topic_0000002015877373_b4125121149"><a name="zh-cn_topic_0000002015877373_b4125121149"></a><a name="zh-cn_topic_0000002015877373_b4125121149"></a>Chip Name</strong>取值为Ascend<em id="zh-cn_topic_0000002015877373_i18125121646"><a name="zh-cn_topic_0000002015877373_i18125121646"></a><a name="zh-cn_topic_0000002015877373_i18125121646"></a>xxx</em>，<strong id="zh-cn_topic_0000002015877373_b141218121448"><a name="zh-cn_topic_0000002015877373_b141218121448"></a><a name="zh-cn_topic_0000002015877373_b141218121448"></a>NPU Name</strong>取值为1234，实际配置值为Ascend<em id="zh-cn_topic_0000002015877373_i16128121419"><a name="zh-cn_topic_0000002015877373_i16128121419"></a><a name="zh-cn_topic_0000002015877373_i16128121419"></a>xxx</em><em id="zh-cn_topic_0000002015877373_i13127121247"><a name="zh-cn_topic_0000002015877373_i13127121247"></a><a name="zh-cn_topic_0000002015877373_i13127121247"></a>_</em>1234。当Ascend<em id="zh-cn_topic_0000002015877373_i197021346113814"><a name="zh-cn_topic_0000002015877373_i197021346113814"></a><a name="zh-cn_topic_0000002015877373_i197021346113814"></a>xxx</em><em id="zh-cn_topic_0000002015877373_i2702846173818"><a name="zh-cn_topic_0000002015877373_i2702846173818"></a><a name="zh-cn_topic_0000002015877373_i2702846173818"></a>_</em>1234为代码样例的路径时，需要配置为ascend<em id="zh-cn_topic_0000002015877373_i19348065392"><a name="zh-cn_topic_0000002015877373_i19348065392"></a><a name="zh-cn_topic_0000002015877373_i19348065392"></a>xxx</em><em id="zh-cn_topic_0000002015877373_i734817633911"><a name="zh-cn_topic_0000002015877373_i734817633911"></a><a name="zh-cn_topic_0000002015877373_i734817633911"></a>_</em>1234。<p id="zh-cn_topic_0000002015877373_p2020212342"><a name="zh-cn_topic_0000002015877373_p2020212342"></a><a name="zh-cn_topic_0000002015877373_p2020212342"></a>其中：</p>
<a name="zh-cn_topic_0000002015877373_ul9238121944"></a><a name="zh-cn_topic_0000002015877373_ul9238121944"></a><ul id="zh-cn_topic_0000002015877373_ul9238121944"><li>id：设备id，通过<strong id="zh-cn_topic_0000002015877373_b723412048"><a name="zh-cn_topic_0000002015877373_b723412048"></a><a name="zh-cn_topic_0000002015877373_b723412048"></a>npu-smi info -l</strong>命令查出的NPU ID即为设备id。</li><li>chip_id：芯片id，通过<strong id="zh-cn_topic_0000002015877373_b172310125417"><a name="zh-cn_topic_0000002015877373_b172310125417"></a><a name="zh-cn_topic_0000002015877373_b172310125417"></a>npu-smi info -m</strong>命令查出的Chip ID即为芯片id。</li></ul>
</li></ul>
</div></div>
</td>
</tr>
</tbody>
</table>

**返回值说明**

<a name="table84733587339"></a>
<table><thead align="left"><tr id="row144730589332"><th class="cellrowborder" valign="top" width="20.82%" id="mcps1.1.3.1.1"><p id="p647365853320"><a name="p647365853320"></a><a name="p647365853320"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="79.17999999999999%" id="mcps1.1.3.1.2"><p id="p4473158193314"><a name="p4473158193314"></a><a name="p4473158193314"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="row2047375853319"><td class="cellrowborder" valign="top" width="20.82%" headers="mcps1.1.3.1.1 "><p id="p6900121210341"><a name="p6900121210341"></a><a name="p6900121210341"></a>blockdim</p>
</td>
<td class="cellrowborder" valign="top" width="79.17999999999999%" headers="mcps1.1.3.1.2 "><p id="p467339193415"><a name="p467339193415"></a><a name="p467339193415"></a>用户tiling函数配置的核数。</p>
<p id="p788513743715"><a name="p788513743715"></a><a name="p788513743715"></a>数据类型：int。</p>
</td>
</tr>
<tr id="row9473258193319"><td class="cellrowborder" valign="top" width="20.82%" headers="mcps1.1.3.1.1 "><p id="p1847318589338"><a name="p1847318589338"></a><a name="p1847318589338"></a>workspace_size</p>
</td>
<td class="cellrowborder" valign="top" width="79.17999999999999%" headers="mcps1.1.3.1.2 "><p id="p9719951019"><a name="p9719951019"></a><a name="p9719951019"></a>该值为用户自行申请的workspace大小加上 msKL工具预留的78,643,200Byte。</p>
<p id="p15483103110375"><a name="p15483103110375"></a><a name="p15483103110375"></a>数据类型：int。</p>
</td>
</tr>
<tr id="row4396115123011"><td class="cellrowborder" valign="top" width="20.82%" headers="mcps1.1.3.1.1 "><p id="p1839614511303"><a name="p1839614511303"></a><a name="p1839614511303"></a>workspace</p>
</td>
<td class="cellrowborder" valign="top" width="79.17999999999999%" headers="mcps1.1.3.1.2 "><p id="p16897136163117"><a name="p16897136163117"></a><a name="p16897136163117"></a>msKL工具为用户申请的workspace空间，大小为workspace_size。</p>
<p id="p18971468313"><a name="p18971468313"></a><a name="p18971468313"></a>数据类型：numpy.array。</p>
</td>
</tr>
<tr id="row5474958183312"><td class="cellrowborder" valign="top" width="20.82%" headers="mcps1.1.3.1.1 "><p id="p584352512359"><a name="p584352512359"></a><a name="p584352512359"></a>tiling_data</p>
</td>
<td class="cellrowborder" valign="top" width="79.17999999999999%" headers="mcps1.1.3.1.2 "><p id="p511534133518"><a name="p511534133518"></a><a name="p511534133518"></a>存放tiling_data，用于调用Kernel函数。</p>
<p id="p09351309407"><a name="p09351309407"></a><a name="p09351309407"></a>数据类型：numpy.array。</p>
</td>
</tr>
<tr id="row19474105863312"><td class="cellrowborder" valign="top" width="20.82%" headers="mcps1.1.3.1.1 "><p id="p1649364315351"><a name="p1649364315351"></a><a name="p1649364315351"></a>tiling_key</p>
</td>
<td class="cellrowborder" valign="top" width="79.17999999999999%" headers="mcps1.1.3.1.2 "><p id="p20628155111358"><a name="p20628155111358"></a><a name="p20628155111358"></a>用户tiling函数配置的tiling_key，若用户未设置，msKL工具会默认设置为0。</p>
<p id="p18947182514418"><a name="p18947182514418"></a><a name="p18947182514418"></a>数据类型：int。</p>
</td>
</tr>
</tbody>
</table>

**调用示例**

```python
M = 1024
N = 640
K = 256
input_a = np.random.randint(1, 10, [M, K]).astype(np.float16)
input_b = np.random.randint(1, 10, [K, N]).astype(np.float16)
input_bias = np.random.randint(1, 10, [N]).astype(np.float32)
output = np.zeros([M, N]).astype(np.float32)
# tiling data
tiling_output = mskl.tiling_func(
    op_type="MatmulLeakyreluCustom",
    inputs=[input_a, input_b, input_bias], outputs=[output],
    lib_path="liboptiling.so",  # tiling代码编译产物 
)
```

## get_kernel_from_binary

**功能说明**

生成一个可以调用用户Kernel函数的实例。

**函数原型**

```python
def get_kernel_from_binary(kernel_binary_file: str, kernel_type: str = None, tiling_key: int = None) -> CompiledKernel
```

**参数说明**

<a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_table438764393513"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_row53871743113510"><th class="cellrowborder" valign="top" width="17.16%" id="mcps1.1.5.1.1"><p id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"></a><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="10.07%" id="mcps1.1.5.1.2"><p id="zh-cn_topic_0000001693276536_p1769255516412"><a name="zh-cn_topic_0000001693276536_p1769255516412"></a><a name="zh-cn_topic_0000001693276536_p1769255516412"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="7.5200000000000005%" id="mcps1.1.5.1.3"><p id="p1024820378356"><a name="p1024820378356"></a><a name="p1024820378356"></a>是否必选</p>
</th>
<th class="cellrowborder" valign="top" width="65.25%" id="mcps1.1.5.1.4"><p id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"></a><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_row2038874343514"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p16121639173913"><a name="p16121639173913"></a><a name="p16121639173913"></a>kernel_binary_file</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="p1239865692418"><a name="p1239865692418"></a><a name="p1239865692418"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p224816370358"><a name="p224816370358"></a><a name="p224816370358"></a>必选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="p858655320395"><a name="p858655320395"></a><a name="p858655320395"></a>算子kernel.o路径，可以在工程目录下执行<strong id="b23211229105614"><a name="b23211229105614"></a><a name="b23211229105614"></a>find . -name '*.o'</strong>命令进行查找。</p>
<p id="p960565114599"><a name="p960565114599"></a><a name="p960565114599"></a>数据类型：str。</p>
</td>
</tr>
<tr id="row6693915183815"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p28817133400"><a name="p28817133400"></a><a name="p28817133400"></a>kernel_type</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="zh-cn_topic_0000001693276536_p2076172220574"><a name="zh-cn_topic_0000001693276536_p2076172220574"></a><a name="zh-cn_topic_0000001693276536_p2076172220574"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p17248203712356"><a name="p17248203712356"></a><a name="p17248203712356"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="p1464205919597"><a name="p1464205919597"></a><a name="p1464205919597"></a>算子类型。可设置为vec、 cube或mix。</p>
<p id="p4807856193812"><a name="p4807856193812"></a><a name="p4807856193812"></a>若不配置该参数，msKL工具可能会获取失败。因此，建议手动赋值。</p>
<p id="p16255183291"><a name="p16255183291"></a><a name="p16255183291"></a>数据类型：str。</p>
</td>
</tr>
<tr id="zh-cn_topic_0000001693276536_row7909131293411"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p1383539114018"><a name="p1383539114018"></a><a name="p1383539114018"></a>tiling_key</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="p126964817386"><a name="p126964817386"></a><a name="p126964817386"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p19248143720357"><a name="p19248143720357"></a><a name="p19248143720357"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="p4854114711404"><a name="p4854114711404"></a><a name="p4854114711404"></a>调用用户Kernel函数时使用的tiling_key。若不配置该参数，msKL工具将会使用最近一次调用tiling_func的结果。</p>
<p id="p7992520172918"><a name="p7992520172918"></a><a name="p7992520172918"></a>数据类型：int。</p>
</td>
</tr>
</tbody>
</table>

**返回值说明**

可运行的Kernel对象。

**表 1**  Kernel入参介绍

<a name="table8662130195715"></a>
<table><thead align="left"><tr id="row8662163015575"><th class="cellrowborder" valign="top" width="33.33333333333333%" id="mcps1.2.4.1.1"><p id="p6204175135717"><a name="p6204175135717"></a><a name="p6204175135717"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="33.33333333333333%" id="mcps1.2.4.1.2"><p id="p1120465195716"><a name="p1120465195716"></a><a name="p1120465195716"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="33.33333333333333%" id="mcps1.2.4.1.3"><p id="p22041751155717"><a name="p22041751155717"></a><a name="p22041751155717"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="row1866210304576"><td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.1 "><p id="p96622301571"><a name="p96622301571"></a><a name="p96622301571"></a>device_id</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.2 "><p id="p76621730125717"><a name="p76621730125717"></a><a name="p76621730125717"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.3 "><p id="zh-cn_topic_0000001821790281_p1735018438911"><a name="zh-cn_topic_0000001821790281_p1735018438911"></a><a name="zh-cn_topic_0000001821790281_p1735018438911"></a>NPU设备ID，设置运行ST测试用例的<span id="zh-cn_topic_0000001821790281_ph173501343695"><a name="zh-cn_topic_0000001821790281_ph173501343695"></a><a name="zh-cn_topic_0000001821790281_ph173501343695"></a>昇腾AI处理器</span>的ID。</p>
<p id="p18525496107"><a name="p18525496107"></a><a name="p18525496107"></a>数据类型：int。</p>
<p id="zh-cn_topic_0000001821790281_p1350943597"><a name="zh-cn_topic_0000001821790281_p1350943597"></a><a name="zh-cn_topic_0000001821790281_p1350943597"></a>若未设置此参数，默认为0。</p>
</td>
</tr>
<tr id="row11662530125710"><td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.1 "><p id="p18662153015573"><a name="p18662153015573"></a><a name="p18662153015573"></a>timeout</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.2 "><p id="p1166219306572"><a name="p1166219306572"></a><a name="p1166219306572"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.3 "><p id="p188921897918"><a name="p188921897918"></a><a name="p188921897918"></a>camodel仿真场景需要默认设置较长超时时间，设置为-1时表示不限制。</p>
<p id="p20887821121219"><a name="p20887821121219"></a><a name="p20887821121219"></a>数据类型：int。</p>
<p id="p9662123095717"><a name="p9662123095717"></a><a name="p9662123095717"></a>单位: ms，默认值为300000。</p>
</td>
</tr>
<tr id="row1770213117585"><td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.1 "><p id="p11702181115584"><a name="p11702181115584"></a><a name="p11702181115584"></a>repeat</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.2 "><p id="p67021811135816"><a name="p67021811135816"></a><a name="p67021811135816"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.3 "><p id="p157021311165815"><a name="p157021311165815"></a><a name="p157021311165815"></a>重复运行次数，默认值为1。</p>
<p id="p1241342821215"><a name="p1241342821215"></a><a name="p1241342821215"></a>数据类型：int。</p>
</td>
</tr>
<tr id="row1536114485014"><td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.1 "><p id="p16489135344918"><a name="p16489135344918"></a><a name="p16489135344918"></a>stream</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.2 "><p id="p948945315490"><a name="p948945315490"></a><a name="p948945315490"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.3 "><p id="p2048910536495"><a name="p2048910536495"></a><a name="p2048910536495"></a>预留参数。</p>
</td>
</tr>
<tr id="row936134416501"><td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.1 "><p id="p1920195816498"><a name="p1920195816498"></a><a name="p1920195816498"></a>kernel_name</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.2 "><p id="p79201158154917"><a name="p79201158154917"></a><a name="p79201158154917"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.3 "><p id="p965862817502"><a name="p965862817502"></a><a name="p965862817502"></a>预留参数。</p>
</td>
</tr>
</tbody>
</table>

> [!NOTE]   
> Kernel对象类型为CompiledKernel，支持如下方式调用Kernel：kernel[blockdim](arg1, arg2, ..., timeout=-1, device_id=0, repeat=1)，实际调用时，需保证CompiledKernel函数的入参和调用Kernel时的入参一致。

**调用示例**

- 示例一：

    ```python
    def run_kernel(input_a, input_b, input_bias, output, workspace, tiling_data):
        kernel_binary_file = "MatmulLeakyreluCustom.o"   #不同的硬件和操作系统展示的.o文件的名称稍有不同
        kernel = get_kernel_from_binary(kernel_binary_file)
        return kernel(input_a, input_b, input_bias, output, workspace, tiling_data)
    ```

- 示例二：

    ```python
    def run_kernel(input_a, input_b, input_bias, output, workspace, tiling_data, tiling_key, blockdim):
        kernel_binary_file = "MatmulLeakyreluCustom.o"    #不同的硬件和操作系统展示的.o文件的名称稍有不同
        kernel = get_kernel_from_binary(kernel_binary_file, kernel_type='mix', tiling_key=tiling_key)
        return kernel[blockdim](input_a, input_b, input_bias, output, workspace, tiling_data, device_id=1, timeout=-1) #运行仿真时，需要手动将timeout参数设置为-1
    ```

## autotune

**功能说明**

遍历搜索空间，尝试不同参数组合，展示每个组合的运行耗时与最优组合。

**函数原型**

```python
def autotune(configs: List[Dict], warmup: int = 300, repeat: int = 1, device_ids = [0]):
```

**参数说明**

<a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_table438764393513"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_row53871743113510"><th class="cellrowborder" valign="top" width="17.16%" id="mcps1.1.5.1.1"><p id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"></a><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="10.07%" id="mcps1.1.5.1.2"><p id="zh-cn_topic_0000001693276536_p1769255516412"><a name="zh-cn_topic_0000001693276536_p1769255516412"></a><a name="zh-cn_topic_0000001693276536_p1769255516412"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="7.5200000000000005%" id="mcps1.1.5.1.3"><p id="p13941118163617"><a name="p13941118163617"></a><a name="p13941118163617"></a>是否必选</p>
</th>
<th class="cellrowborder" valign="top" width="65.25%" id="mcps1.1.5.1.4"><p id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"></a><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_row2038874343514"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="zh-cn_topic_0000001693276536_p4761822185716"><a name="zh-cn_topic_0000001693276536_p4761822185716"></a><a name="zh-cn_topic_0000001693276536_p4761822185716"></a>configs</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="p1239865692418"><a name="p1239865692418"></a><a name="p1239865692418"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p174230102515"><a name="p174230102515"></a><a name="p174230102515"></a>必选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="zh-cn_topic_0000001693276536_p8761822125710"><a name="zh-cn_topic_0000001693276536_p8761822125710"></a><a name="zh-cn_topic_0000001693276536_p8761822125710"></a>搜索空间定义。</p>
<p id="p960565114599"><a name="p960565114599"></a><a name="p960565114599"></a>数据类型：list[dict]。</p>
</td>
</tr>
<tr id="row6693915183815"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="zh-cn_topic_0000001693276536_p1676172255719"><a name="zh-cn_topic_0000001693276536_p1676172255719"></a><a name="zh-cn_topic_0000001693276536_p1676172255719"></a>warmup</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="zh-cn_topic_0000001693276536_p2076172220574"><a name="zh-cn_topic_0000001693276536_p2076172220574"></a><a name="zh-cn_topic_0000001693276536_p2076172220574"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p153941818143617"><a name="p153941818143617"></a><a name="p153941818143617"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="p7623626182018"><a name="p7623626182018"></a><a name="p7623626182018"></a>采集性能前的设备预热时间。通常情况下，预热时间越长，采集到的算子性能越稳定。</p>
<p id="p6392151820207"><a name="p6392151820207"></a><a name="p6392151820207"></a>单位：微秒。</p>
<p id="p4807856193812"><a name="p4807856193812"></a><a name="p4807856193812"></a>默认值：1000，取值范围为1~100000之间的整数。</p>
</td>
</tr>
<tr id="zh-cn_topic_0000001693276536_row7909131293411"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p18541126143820"><a name="p18541126143820"></a><a name="p18541126143820"></a>repeat</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="p126964817386"><a name="p126964817386"></a><a name="p126964817386"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p14394131818368"><a name="p14394131818368"></a><a name="p14394131818368"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="p1644464921615"><a name="p1644464921615"></a><a name="p1644464921615"></a>重放次数，会根据多次重放取运行耗时的平均值作为算子耗时。</p>
<p id="p553112623811"><a name="p553112623811"></a><a name="p553112623811"></a>默认值：1，取值范围为1~10000之间的整数。</p>
</td>
</tr>
<tr id="row619616229387"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p11962022103812"><a name="p11962022103812"></a><a name="p11962022103812"></a>device_ids</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="p226994833814"><a name="p226994833814"></a><a name="p226994833814"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p939416182367"><a name="p939416182367"></a><a name="p939416182367"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="p1519610221383"><a name="p1519610221383"></a><a name="p1519610221383"></a>Device ID列表，目前仅支持单Device模式，如果填写多个Device ID，只有第一个会生效。</p>
<p id="p198371282219"><a name="p198371282219"></a><a name="p198371282219"></a>默认值：[0]。</p>
</td>
</tr>
</tbody>
</table>

**返回值说明**

无。

**调用示例**

```python
@mskl.autotune(configs=[
    {'L1TileShape': 'MatmulShape<64, 64, 64>', 'L0TileShape': 'MatmulShape<128, 256, 64>'},
    {'L1TileShape': 'MatmulShape<64, 64, 128>', 'L0TileShape': 'MatmulShape<128, 256, 64>'},
    {'L1TileShape': 'MatmulShape<64, 128, 128>', 'L0TileShape': 'MatmulShape<128, 256, 64>'},
    {'L1TileShape': 'MatmulShape<64, 128, 128>', 'L0TileShape': 'MatmulShape<64, 256, 64>'},
    {'L1TileShape': 'MatmulShape<128, 128, 128>', 'L0TileShape': 'MatmulShape<128, 256, 64>'},
], warmup=500, repeat=10, device_ids=[0])
def basic_matmul(problem_shape, a, layout_a, b, layout_b, c, layout_c):
    kernel = get_kernel()
    blockdim = 20
    return kernel[blockdim](problem_shape, a, layout_a, b, layout_b, c, layout_c)
```

## code_gen

**功能说明**

根据输入的模板库Kernel信息，生成Kernel下发代码。

**函数原型**

```py
gen_file = mskl.Launcher(config).code_gen()
```

**参数说明**

<a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_table438764393513"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_row53871743113510"><th class="cellrowborder" valign="top" width="17.16%" id="mcps1.1.5.1.1"><p id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"></a><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="10.07%" id="mcps1.1.5.1.2"><p id="zh-cn_topic_0000001693276536_p1769255516412"><a name="zh-cn_topic_0000001693276536_p1769255516412"></a><a name="zh-cn_topic_0000001693276536_p1769255516412"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="7.5200000000000005%" id="mcps1.1.5.1.3"><p id="p124405383374"><a name="p124405383374"></a><a name="p124405383374"></a>是否必选</p>
</th>
<th class="cellrowborder" valign="top" width="65.25%" id="mcps1.1.5.1.4"><p id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"></a><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_row2038874343514"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p10267558104819"><a name="p10267558104819"></a><a name="p10267558104819"></a>gen_file</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="p1239865692418"><a name="p1239865692418"></a><a name="p1239865692418"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p1667583410378"><a name="p1667583410378"></a><a name="p1667583410378"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="p115678181496"><a name="p115678181496"></a><a name="p115678181496"></a>指定生成Kernel侧下发代码的文件路径。</p>
<p id="p1244041710497"><a name="p1244041710497"></a><a name="p1244041710497"></a>数据类型：str。</p>
<p id="p15376846501"><a name="p15376846501"></a><a name="p15376846501"></a>默认值为_gen_launch.cpp。</p>
</td>
</tr>
</tbody>
</table>

**返回值说明**

生成代码的文件路径。

**调用示例**

```py
config = mskl.KernelInvokeConfig(kernel_file, kernel_name) 
gen_file = mskl.Launcher(config).code_gen() 
```

**相关类/结构体定义**

```python
class KernelInvokeConfig:
    ...
    A configuration descriptor for a possible kernel developed based on an Act example
    ...
    def __init__(self, kernel_src_file : str, kernel_name : str):
        pass
# 用户仅能传KernelInvokeConfig类型
class Launcher:
    def __init__(self, config: KernelInvokeConfig): 
      ...
        a class that generates launch source code for a kernel

        Args:
            config (KernelInvokeConfig): A configuration descriptor for a kernel
        ...
```

## compile

**功能说明**

编译Kernel下发代码，返回一个可执行的Kernel对象。

**函数原型**

```py
kernel = compile(build_script, gen_file)
```

**参数说明**

<a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_table438764393513"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_row53871743113510"><th class="cellrowborder" valign="top" width="17.16%" id="mcps1.1.5.1.1"><p id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"></a><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="10.07%" id="mcps1.1.5.1.2"><p id="zh-cn_topic_0000001693276536_p1769255516412"><a name="zh-cn_topic_0000001693276536_p1769255516412"></a><a name="zh-cn_topic_0000001693276536_p1769255516412"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="7.5200000000000005%" id="mcps1.1.5.1.3"><p id="p3254165893717"><a name="p3254165893717"></a><a name="p3254165893717"></a>是否必选</p>
</th>
<th class="cellrowborder" valign="top" width="65.25%" id="mcps1.1.5.1.4"><p id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"></a><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_row2038874343514"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p10267558104819"><a name="p10267558104819"></a><a name="p10267558104819"></a>build_script</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="p1239865692418"><a name="p1239865692418"></a><a name="p1239865692418"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p12254195811376"><a name="p12254195811376"></a><a name="p12254195811376"></a>必选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="p1244041710497"><a name="p1244041710497"></a><a name="p1244041710497"></a>用于模板库Kernel编译的脚本。</p>
<p id="p83481217117"><a name="p83481217117"></a><a name="p83481217117"></a>数据类型：str。</p>
</td>
</tr>
<tr id="row21578635315"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p91571169532"><a name="p91571169532"></a><a name="p91571169532"></a>gen_file</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="p149601220152718"><a name="p149601220152718"></a><a name="p149601220152718"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p1625415883718"><a name="p1625415883718"></a><a name="p1625415883718"></a>必选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="p2330112281017"><a name="p2330112281017"></a><a name="p2330112281017"></a>由code_gen接口生成的Kernel下发代码文件路径，一般直接使用code_gen接口返回值。</p>
<p id="p1235517611263"><a name="p1235517611263"></a><a name="p1235517611263"></a>数据类型：str。</p>
</td>
</tr>
<tr id="row2446191225310"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p1844691215313"><a name="p1844691215313"></a><a name="p1844691215313"></a>output_bin_path</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="p648702213274"><a name="p648702213274"></a><a name="p648702213274"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p15254135823713"><a name="p15254135823713"></a><a name="p15254135823713"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="p3877449179"><a name="p3877449179"></a><a name="p3877449179"></a>指定编译生成的可执行文件路径。</p>
<p id="p151642576716"><a name="p151642576716"></a><a name="p151642576716"></a>数据类型：str。</p>
<p id="p862114551676"><a name="p862114551676"></a><a name="p862114551676"></a>默认值：_gen_module.so。</p>
</td>
</tr>
<tr id="row16446912115316"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p1244615127537"><a name="p1244615127537"></a><a name="p1244615127537"></a>use_cache</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="p1279142712719"><a name="p1279142712719"></a><a name="p1279142712719"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p7254858113719"><a name="p7254858113719"></a><a name="p7254858113719"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="p599012311160"><a name="p599012311160"></a><a name="p599012311160"></a>开启后不执行编译，加载output_bin_path所指定的文件。</p>
<p id="p583712186617"><a name="p583712186617"></a><a name="p583712186617"></a>数据类型：bool。</p>
<p id="p19100819617"><a name="p19100819617"></a><a name="p19100819617"></a>默认值：False。</p>
</td>
</tr>
</tbody>
</table>

**返回值说明**

可运行的Kernel对象，类型：CompiledKernel，支持如下方式调用kernel：kernel[blockdim](arg1, arg2, ..., timeout=-1, device_id=0, repeat=1)，其中arg1、arg2、...是Kernel的入参。

**调用示例**

```py
kernel = compile(build_script, gen_file)
kernel[blockdim](arg1, arg2, ..., device_id=0)
```

**表 1**  CompiledKernel可选入参介绍

<a name="table8662130195715"></a>
<table><thead align="left"><tr id="row8662163015575"><th class="cellrowborder" valign="top" width="33.33333333333333%" id="mcps1.2.4.1.1"><p id="p6204175135717"><a name="p6204175135717"></a><a name="p6204175135717"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="33.33333333333333%" id="mcps1.2.4.1.2"><p id="p1120465195716"><a name="p1120465195716"></a><a name="p1120465195716"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="33.33333333333333%" id="mcps1.2.4.1.3"><p id="p22041751155717"><a name="p22041751155717"></a><a name="p22041751155717"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="row1866210304576"><td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.1 "><p id="p96622301571"><a name="p96622301571"></a><a name="p96622301571"></a>device_id</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.2 "><p id="p76621730125717"><a name="p76621730125717"></a><a name="p76621730125717"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.3 "><p id="zh-cn_topic_0000001821790281_p1735018438911"><a name="zh-cn_topic_0000001821790281_p1735018438911"></a><a name="zh-cn_topic_0000001821790281_p1735018438911"></a>NPU设备ID，设置运行ST测试用例的<span id="zh-cn_topic_0000001821790281_ph173501343695"><a name="zh-cn_topic_0000001821790281_ph173501343695"></a><a name="zh-cn_topic_0000001821790281_ph173501343695"></a>昇腾AI处理器</span>的ID。</p>
<p id="p18525496107"><a name="p18525496107"></a><a name="p18525496107"></a>数据类型：int。</p>
<p id="zh-cn_topic_0000001821790281_p1350943597"><a name="zh-cn_topic_0000001821790281_p1350943597"></a><a name="zh-cn_topic_0000001821790281_p1350943597"></a>若未设置此参数，默认为0。</p>
</td>
</tr>
<tr id="row11662530125710"><td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.1 "><p id="p18662153015573"><a name="p18662153015573"></a><a name="p18662153015573"></a>timeout</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.2 "><p id="p1166219306572"><a name="p1166219306572"></a><a name="p1166219306572"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.3 "><p id="p188921897918"><a name="p188921897918"></a><a name="p188921897918"></a>camodel仿真场景需要默认设置较长超时时间，设置为-1时表示不限制。</p>
<p id="p20887821121219"><a name="p20887821121219"></a><a name="p20887821121219"></a>数据类型：int。</p>
<p id="p9662123095717"><a name="p9662123095717"></a><a name="p9662123095717"></a>单位: ms，默认值为300000。</p>
</td>
</tr>
<tr id="row1770213117585"><td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.1 "><p id="p11702181115584"><a name="p11702181115584"></a><a name="p11702181115584"></a>repeat</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.2 "><p id="p67021811135816"><a name="p67021811135816"></a><a name="p67021811135816"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.3 "><p id="p157021311165815"><a name="p157021311165815"></a><a name="p157021311165815"></a>重复运行次数，默认值为1。</p>
<p id="p1241342821215"><a name="p1241342821215"></a><a name="p1241342821215"></a>数据类型：int。</p>
</td>
</tr>
<tr id="row16488653114913"><td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.1 "><p id="p16489135344918"><a name="p16489135344918"></a><a name="p16489135344918"></a>stream</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.2 "><p id="p948945315490"><a name="p948945315490"></a><a name="p948945315490"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.3 "><p id="p2048910536495"><a name="p2048910536495"></a><a name="p2048910536495"></a>预留参数。</p>
</td>
</tr>
<tr id="row5920135874912"><td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.1 "><p id="p1920195816498"><a name="p1920195816498"></a><a name="p1920195816498"></a>kernel_name</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.2 "><p id="p79201158154917"><a name="p79201158154917"></a><a name="p79201158154917"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="33.33333333333333%" headers="mcps1.2.4.1.3 "><p id="p965862817502"><a name="p965862817502"></a><a name="p965862817502"></a>预留参数。</p>
</td>
</tr>
</tbody>
</table>

## autotune_v2

**功能说明**

遍历搜索空间，尝试不同参数组合，展示每个组合的运行耗时与最优组合。

**函数原型**

```python
def autotune_v2(configs: List[Dict], warmup_times = 5)
```

**参数说明**

<a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_table438764393513"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_row53871743113510"><th class="cellrowborder" valign="top" width="17.16%" id="mcps1.1.5.1.1"><p id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"></a><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="10.07%" id="mcps1.1.5.1.2"><p id="zh-cn_topic_0000001693276536_p1769255516412"><a name="zh-cn_topic_0000001693276536_p1769255516412"></a><a name="zh-cn_topic_0000001693276536_p1769255516412"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="7.5200000000000005%" id="mcps1.1.5.1.3"><p id="p9836113793820"><a name="p9836113793820"></a><a name="p9836113793820"></a>是否必选</p>
</th>
<th class="cellrowborder" valign="top" width="65.25%" id="mcps1.1.5.1.4"><p id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"></a><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_row2038874343514"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="zh-cn_topic_0000001693276536_p4761822185716"><a name="zh-cn_topic_0000001693276536_p4761822185716"></a><a name="zh-cn_topic_0000001693276536_p4761822185716"></a>configs</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="p1239865692418"><a name="p1239865692418"></a><a name="p1239865692418"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p3836937123816"><a name="p3836937123816"></a><a name="p3836937123816"></a>必选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="zh-cn_topic_0000001693276536_p8761822125710"><a name="zh-cn_topic_0000001693276536_p8761822125710"></a><a name="zh-cn_topic_0000001693276536_p8761822125710"></a>搜索空间定义。</p>
<p id="p960565114599"><a name="p960565114599"></a><a name="p960565114599"></a>数据类型：list[dict]。</p>
</td>
</tr>
<tr id="row6693915183815"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="zh-cn_topic_0000001693276536_p1676172255719"><a name="zh-cn_topic_0000001693276536_p1676172255719"></a><a name="zh-cn_topic_0000001693276536_p1676172255719"></a>warmup_times</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="zh-cn_topic_0000001693276536_p2076172220574"><a name="zh-cn_topic_0000001693276536_p2076172220574"></a><a name="zh-cn_topic_0000001693276536_p2076172220574"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p283633723813"><a name="p283633723813"></a><a name="p283633723813"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="p7623626182018"><a name="p7623626182018"></a><a name="p7623626182018"></a>采集性能前的设备预热次数。</p>
<p id="p4807856193812"><a name="p4807856193812"></a><a name="p4807856193812"></a>默认值：5，取值范围为1~500之间的整数。</p>
</td>
</tr>
</tbody>
</table>

**返回值说明**

无。

**调用示例**

```python
@mskl.autotune_v2(configs=[
    {'L1TileShape': 'GemmShape<128, 256, 256>', 'L0TileShape': 'GemmShape<128, 256, 64>'},
    {'L1TileShape': 'GemmShape<256, 128, 256>', 'L0TileShape': 'GemmShape<256, 128, 64>'},
    {'L1TileShape': 'GemmShape<128, 128, 256>', 'L0TileShape': 'GemmShape<128, 128, 64>'},
    {'L1TileShape': 'GemmShape<128, 128, 512>', 'L0TileShape': 'GemmShape<128, 128, 64>'},
    {'L1TileShape': 'GemmShape<64, 256, 128>', 'L0TileShape': 'GemmShape<64, 256, 64>'},
], warmup_times=10)
def run_executable(m, n, k, device_id):
    src_file = "./basic_matmul.cpp"
    build_script = "./jit_build_executable.sh" # executable compile script
    executable = mskl.compile_executable(build_script=build_script, src_file=src_file, use_cache=False)
    return executable(m, n, k, device_id)
```

## compile_executable

**功能说明**

编译代码，返回一个可执行的executable对象。

**函数原型**

```py
executable = compile_executable(build_script, src_file)
```

**参数说明**

<a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_table438764393513"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_row53871743113510"><th class="cellrowborder" valign="top" width="17.16%" id="mcps1.1.5.1.1"><p id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"></a><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p1438834363520"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="10.07%" id="mcps1.1.5.1.2"><p id="zh-cn_topic_0000001693276536_p1769255516412"><a name="zh-cn_topic_0000001693276536_p1769255516412"></a><a name="zh-cn_topic_0000001693276536_p1769255516412"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="7.5200000000000005%" id="mcps1.1.5.1.3"><p id="p147749211392"><a name="p147749211392"></a><a name="p147749211392"></a>是否必选</p>
</th>
<th class="cellrowborder" valign="top" width="65.25%" id="mcps1.1.5.1.4"><p id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"></a><a name="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_p173881843143514"></a>说明</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000001693276536_zh-cn_topic_0122830089_row2038874343514"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p10267558104819"><a name="p10267558104819"></a><a name="p10267558104819"></a>build_script</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="p1239865692418"><a name="p1239865692418"></a><a name="p1239865692418"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p187749218396"><a name="p187749218396"></a><a name="p187749218396"></a>必选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="p1244041710497"><a name="p1244041710497"></a><a name="p1244041710497"></a>用于编译被调优应用的脚本文件路径。</p>
<p id="p83481217117"><a name="p83481217117"></a><a name="p83481217117"></a>数据类型：str。</p>
</td>
</tr>
<tr id="row21578635315"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p91571169532"><a name="p91571169532"></a><a name="p91571169532"></a>src_file</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="p149601220152718"><a name="p149601220152718"></a><a name="p149601220152718"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p19618112002"><a name="p19618112002"></a><a name="p19618112002"></a>必选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="p2330112281017"><a name="p2330112281017"></a><a name="p2330112281017"></a>代码文件路径。</p>
<p id="p1235517611263"><a name="p1235517611263"></a><a name="p1235517611263"></a>数据类型：str。</p>
</td>
</tr>
<tr id="row2446191225310"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p1844691215313"><a name="p1844691215313"></a><a name="p1844691215313"></a>output_bin_path</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="p648702213274"><a name="p648702213274"></a><a name="p648702213274"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p577417210399"><a name="p577417210399"></a><a name="p577417210399"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="p3877449179"><a name="p3877449179"></a><a name="p3877449179"></a>指定编译生成的可执行文件路径。</p>
<p id="p151642576716"><a name="p151642576716"></a><a name="p151642576716"></a>数据类型：str。</p>
<p id="p862114551676"><a name="p862114551676"></a><a name="p862114551676"></a>默认值：_gen_executable。</p>
</td>
</tr>
<tr id="row16446912115316"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p1244615127537"><a name="p1244615127537"></a><a name="p1244615127537"></a>use_cache</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="p1279142712719"><a name="p1279142712719"></a><a name="p1279142712719"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p197749212396"><a name="p197749212396"></a><a name="p197749212396"></a>可选参数。</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="p599012311160"><a name="p599012311160"></a><a name="p599012311160"></a>开启后不执行编译，加载output_bin_path所指定的文件。</p>
<p id="p583712186617"><a name="p583712186617"></a><a name="p583712186617"></a>数据类型：bool。</p>
<p id="p19100819617"><a name="p19100819617"></a><a name="p19100819617"></a>默认值：False。</p>
<p id="p427716281"><a name="p427716281"></a><a name="p427716281"></a>注意：当使用msDebug工具拉起compile接口时，需配置use_cache=True。</p>
</td>
</tr>
<tr id="row551982042915"><td class="cellrowborder" valign="top" width="17.16%" headers="mcps1.1.5.1.1 "><p id="p475514217293"><a name="p475514217293"></a><a name="p475514217293"></a>profiling_cmd</p>
</td>
<td class="cellrowborder" valign="top" width="10.07%" headers="mcps1.1.5.1.2 "><p id="p7755621182918"><a name="p7755621182918"></a><a name="p7755621182918"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="7.5200000000000005%" headers="mcps1.1.5.1.3 "><p id="p18774112173919"><a name="p18774112173919"></a><a name="p18774112173919"></a>-</p>
</td>
<td class="cellrowborder" valign="top" width="65.25%" headers="mcps1.1.5.1.4 "><p id="p127552021182913"><a name="p127552021182913"></a><a name="p127552021182913"></a>预留参数。</p>
</td>
</tr>
</tbody>
</table>

**返回值说明**

可执行程序对象executable，类型：CompiledExecutable，支持如下方式调用：executable(arg1, arg2, ...)，其中arg1、arg2、...是程序自定义入参。

**调用示例**

```python
executable = compile_executable(build_script, src_file)
executable(a, b, c)
```
