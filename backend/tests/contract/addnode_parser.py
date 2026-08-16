# -*- coding: utf-8 -*-
"""addNode 默认变量字段解析器（Python 侧权威实现）。

设计决策 2：审计的输入必须来自被测数据源之外。MODULE_DEFAULT_VARS 的一致性审计
不能拿 MODULE_DEFAULT_VARS 自己造输入，必须从 workflowStore.ts 的 addNode 源码里
解析出「模块拖到画布时真正写入 node.data 的默认变量名」作为事实源。

为什么 Python 侧是权威实现：前端 vitest 侧有一份等价实现（
frontend/src/lib/__tests__/helpers/addNodeDefaults.ts）用于快速反馈，但跨端一致性
（前端表 vs 后端执行器）只能在 pytest 里比对，所以以本模块为准。两侧口径由
addNodeParserBaseline.json 守护（Property 13），任一侧漂移都会失败。

防假绿：找不到 addNode、分支数为 0、字段数为 0 一律抛 AssertionError，绝不返回空集合。
"""
import json
import os
import re

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ROOT = os.path.dirname(_BACKEND_DIR)
_FE_SRC = os.path.join(_ROOT, "frontend", "src")
_STORE_PATH = os.path.join(_FE_SRC, "store", "workflowStore.ts")
_MDV_PATH = os.path.join(_FE_SRC, "lib", "moduleDefaultVars.ts")
_BASELINE_PATH = os.path.join(_FE_SRC, "lib", "__tests__", "helpers", "addNodeParserBaseline.json")

#: addNode 的函数签名锚点（zustand store 动作定义写法）
ADD_NODE_ANCHOR = "addNode: (type, position, extraConfig) => {"

_BRANCH_RE = re.compile(r"\bif\s*\(([^()]*)\)\s*\{")
_BRANCH_TYPE_RE = re.compile(r"""\btype\s*===\s*['"]([A-Za-z0-9_]+)['"]""")
_LITERAL_ASSIGN_RE = re.compile(r"""(?:^|[\s{,(])([A-Za-z_]\w*)\s*:\s*(['"])((?:\\.|(?!\2)[^\\])*)\2""")
_COMPUTED_ASSIGN_RE = re.compile(r"""(?:^|[\s{,(])([A-Za-z_]\w*)\s*:\s*([A-Za-z_][\w.\[\]]*)\s*(?=[,\n}])""")


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_baseline():
    """两侧共用的解析口径基线（Property 13 的比对媒介）"""
    return json.loads(_read(_BASELINE_PATH))


def variable_name_fields():
    """从 moduleDefaultVars.ts 解析 VARIABLE_NAME_FIELDS 白名单（不在 Python 侧手写副本）"""
    src = _read(_MDV_PATH)
    block = src[src.index("export const VARIABLE_NAME_FIELDS"):]
    block = block[block.index("= [") + 3:]
    block = block[: block.index("]")]
    fields = set(re.findall(r"'([A-Za-z0-9_]+)'", block))
    if not fields:
        raise AssertionError("未解析到 VARIABLE_NAME_FIELDS 白名单，解析规则已失效")
    return fields


def _blank(source, blank_strings):
    """逐字符把注释（可选：字符串字面量内容）置为空格，保留换行。

    输出长度与行号与原文完全一致，因此报错行号可直接定位源码。

    blank_strings 的取舍：
      · 结构扫描（括号配对、分支切分）必须置空字符串内容，否则字符串里的花括号
        会破坏配对，导致函数体边界判错、分支数量失真；
      · 字段值提取必须保留字符串内容，因为默认变量名本身就写在字符串里。
    """
    out = []
    i = 0
    n = len(source)
    while i < n:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ""
        if ch == "/" and nxt == "/":
            while i < n and source[i] != "\n":
                out.append(" ")
                i += 1
            continue
        if ch == "/" and nxt == "*":
            out.append("  ")
            i += 2
            while i < n and not (source[i] == "*" and i + 1 < n and source[i + 1] == "/"):
                out.append("\n" if source[i] == "\n" else " ")
                i += 1
            if i < n:
                out.append("  ")
                i += 2
            continue
        if ch in ("'", '"', "`"):
            out.append(ch)
            i += 1
            while i < n and source[i] != ch:
                if source[i] == "\\":
                    out.append(" " if blank_strings else source[i])
                    i += 1
                    if i < n:
                        out.append(" " if blank_strings else source[i])
                        i += 1
                    continue
                if blank_strings:
                    out.append("\n" if source[i] == "\n" else " ")
                else:
                    out.append(source[i])
                i += 1
            if i < n:
                out.append(source[i])
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _match_block(text, open_index):
    """取 open_index（指向左花括号）配对的块区间 (内容起点, 内容终点)；不配对返回 None"""
    depth = 0
    for i in range(open_index, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return open_index + 1, i
    return None


def _find_add_node_body(structural):
    """定位 addNode 函数体，返回 (起点, 终点)。找不到或括号不配对时抛异常"""
    at = structural.find(ADD_NODE_ANCHOR)
    if at < 0:
        raise AssertionError(
            u"在 frontend/src/store/workflowStore.ts 中找不到 addNode 函数签名锚点"
            u"「%s」，解析规则需随源码同步更新（不要让审计静默通过）" % ADD_NODE_ANCHOR
        )
    brace_at = at + len(ADD_NODE_ANCHOR) - 1
    block = _match_block(structural, brace_at)
    if block is None:
        raise AssertionError(u"addNode 函数体的花括号未配对，解析规则需更新")
    return block


def parse_branches(source):
    """切分 addNode 的全部 `if / else if` 分支。

    返回 [{"module_types": [...], "start": int, "end": int}]，区间是分支体在整份源码中的偏移。
    只收条件里含 `type === '字面量'` 的分支：分支体内层还有 `if (globalConfig.x)` 这类
    与 module_type 无关的判断，它们提取不到 type，自然被跳过，不会产生重复条目。
    """
    structural = _blank(source, blank_strings=True)
    # 结构定位（括号配对、分支切分）在 structural 上做，避免字符串里的花括号带偏配对；
    # 但分支条件里的 `type === '字面量'` 必须从保留字符串内容的版本取，两者长度一致，偏移可互换。
    literal = _blank(source, blank_strings=False)
    body_start, body_end = _find_add_node_body(structural)
    branches = []
    for m in _BRANCH_RE.finditer(structural, body_start, body_end):
        module_types = _BRANCH_TYPE_RE.findall(literal[m.start(1):m.end(1)])
        if not module_types:
            continue
        brace_at = m.end() - 1
        block = _match_block(structural, brace_at)
        if block is None:
            raise AssertionError(
                u"addNode 分支「%s」的花括号未配对，解析规则需更新" % u" | ".join(module_types)
            )
        branches.append({"module_types": module_types, "start": block[0], "end": block[1]})
    if not branches:
        raise AssertionError(
            u"addNode 中未解析出任何 `type === '字面量'` 分支，解析规则已失效——"
            u"禁止在此返回空结果，否则依赖本解析器的审计会退化成假绿"
        )
    return branches, (body_start, body_end)


def _line_of(source, offset):
    return source.count("\n", 0, offset) + 1


class AddNodeParseResult(object):
    """addNode 一次解析的完整结果"""

    def __init__(self, branch_count, multi_type_branch_count, module_types, var_fields,
                 computed_var_fields, body_lines, body_text=""):
        #: addNode 函数体文本（已剥离注释），用于结构性边界断言
        self.body_text = body_text
        #: 含 `type === '字面量'` 的分支数
        self.branch_count = branch_count
        #: 其中 `||` 连接多个 module_type 的分支数
        self.multi_type_branch_count = multi_type_branch_count
        #: 分支覆盖到的 module_type（去重，按出现顺序）
        self.module_types = module_types
        #: {(module_type, field): {"value": str, "line": int}}
        self.var_fields = var_fields
        #: [{"module_type", "field", "expression", "line"}] 运行时计算、静态无法确定取值
        self.computed_var_fields = computed_var_fields
        #: addNode 函数体的起止行号，便于人工核对解析边界
        self.body_lines = body_lines

    @property
    def modules_with_var_fields(self):
        return sorted({t for t, _ in self.var_fields})

    def field_distribution(self):
        dist = {}
        for _, field in self.var_fields:
            dist[field] = dist.get(field, 0) + 1
        return dist


def parse_add_node(source=None):
    """解析 addNode，返回 AddNodeParseResult。结果为空时抛异常，禁止返回空集合。"""
    if source is None:
        source = _read(_STORE_PATH)
    whitelist = variable_name_fields()
    literal_source = _blank(source, blank_strings=False)
    branches, body = parse_branches(source)

    module_types = []
    seen = set()
    var_fields = {}
    computed = []

    for branch in branches:
        for module_type in branch["module_types"]:
            if module_type not in seen:
                seen.add(module_type)
                module_types.append(module_type)
        segment = literal_source[branch["start"]:branch["end"]]

        for m in _LITERAL_ASSIGN_RE.finditer(segment):
            field = m.group(1)
            if field not in whitelist:
                continue
            line = _line_of(literal_source, branch["start"] + m.start(1))
            for module_type in branch["module_types"]:
                # 同一分支体内同一字段出现多次时以最后一次为准（对象字面量后写覆盖前写）
                var_fields[(module_type, field)] = {"value": m.group(3), "line": line}

        for m in _COMPUTED_ASSIGN_RE.finditer(segment):
            field = m.group(1)
            if field not in whitelist:
                continue
            line = _line_of(literal_source, branch["start"] + m.start(1))
            for module_type in branch["module_types"]:
                computed.append({
                    "module_type": module_type,
                    "field": field,
                    "expression": m.group(2),
                    "line": line,
                })

    if not var_fields:
        raise AssertionError(
            u"addNode 的 %d 个分支里未解析出任何变量名字段赋值，解析规则已失效"
            u"（白名单字段名或赋值写法可能已变更）——禁止返回空结果" % len(branches)
        )

    return AddNodeParseResult(
        branch_count=len(branches),
        multi_type_branch_count=len([b for b in branches if len(b["module_types"]) > 1]),
        module_types=module_types,
        var_fields=var_fields,
        computed_var_fields=computed,
        body_lines=(_line_of(literal_source, body[0]), _line_of(literal_source, body[1])),
        body_text=literal_source[body[0]:body[1]],
    )
