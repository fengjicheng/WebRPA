# -*- coding: utf-8 -*-
"""前后端「模块内置变量」登记一致性测试。

为什么需要跨端断言：
前端的变量名自动补全依赖 frontend/src/lib/moduleDefaultVars.ts 里的 MODULE_DEFAULT_VARS，
而「模块创建即内置某个变量」这件事的真正事实来源在后端执行器——凡是
config.get('xxxVariable', '默认名') 带非空默认值的模块，用户不填也会产生该变量。
两边不同步时，那些变量在补全列表里根本不出现（Word、SAP 会话句柄等就曾整批遗漏）。

前端已有的 moduleDefaultVars.audit.test.ts 只校验「已登记条目的自洽性」，
查不出「漏登记」，所以必须由这条反向审计来守。
"""
import os
import re

import pytest

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_EXECUTORS_DIR = os.path.join(_BACKEND_DIR, "app", "executors")
_MDV_PATH = os.path.join(
    os.path.dirname(_BACKEND_DIR), "frontend", "src", "lib", "moduleDefaultVars.ts"
)

# config.get('xxxVariable', '默认值')
_FIELD_RE = re.compile(
    r"""config\.get\(\s*['"]([A-Za-z0-9_]*[Vv]ariable[A-Za-z0-9_]*)['"]\s*,\s*['"]([^'"]+)['"]"""
)
# (config.get('xxxVariable') or '默认值')
_FIELD_OR_RE = re.compile(
    r"""config\.get\(\s*['"]([A-Za-z0-9_]*[Vv]ariable[A-Za-z0-9_]*)['"]\s*\)\s*or\s*['"]([^'"]+)['"]"""
)
_MODTYPE_RE = re.compile(r"""return\s+['"]([a-z0-9_]+)['"]""")
# config.get('新字段名', config.get('历史字段名', '默认值'))
#
# 这种嵌套兜底链表示「主字段是外层的新字段名，内层只是兼容旧工作流的历史别名」。
# 必须先按这条规则归属，否则内层字段会被下面的 _FIELD_RE 误认为「一个独立的、带默认值的
# 变量字段」，从而误报「前端漏登记该字段」——desktop_app_start 的
# config.get('saveToVariable', config.get('connectionVariable', 'desktop_app'))
# 就是这种写法，行为上完全正确（以 addNode 的 saveToVariable 为主），不该被报为缺口。
_FIELD_NESTED_RE = re.compile(
    r"""config\.get\(\s*['"]([A-Za-z0-9_]*[Vv]ariable[A-Za-z0-9_]*)['"]\s*,\s*"""
    r"""config\.get\(\s*['"]([A-Za-z0-9_]*[Vv]ariable[A-Za-z0-9_]*)['"]\s*,\s*['"]([^'"]+)['"]\s*\)\s*\)"""
)


def _frontend_registered() -> set:
    src = open(_MDV_PATH, encoding="utf-8").read()
    body = src[src.index("MODULE_DEFAULT_VARS"):src.index("export function getModuleDefaultVar")]
    return set(re.findall(r"^\s{2}([a-z0-9_]+):\s*\{", body, re.M))


def _frontend_whitelist() -> set:
    src = open(_MDV_PATH, encoding="utf-8").read()
    block = src[src.index("export const VARIABLE_NAME_FIELDS"):]
    # 从 "= [" 之后开始截，否则会被类型注解 string[] 里的 ] 提前截断
    block = block[block.index("= [") + 3:]
    block = block[: block.index("]")]
    return set(re.findall(r"'([A-Za-z0-9_]+)'", block))


def _frontend_entries() -> dict:
    """{module_type: {field: default}}：解析前端 MODULE_DEFAULT_VARS 的逐字段登记内容"""
    src = open(_MDV_PATH, encoding="utf-8").read()
    body = src[src.index("MODULE_DEFAULT_VARS"):src.index("export function getModuleDefaultVar")]
    entries: dict = {}
    for m in re.finditer(r"^\s{2}([a-z0-9_]+):\s*\{([^}]*)\}", body, re.M | re.S):
        fields = dict(re.findall(r"([A-Za-z0-9_]+):\s*'([^']*)'", m.group(2)))
        entries[m.group(1)] = fields
    return entries


def _backend_defaults() -> dict:
    """{module_type: {field: default}}，只收集带非空默认值的变量名字段"""
    findings: dict = {}
    for name in sorted(os.listdir(_EXECUTORS_DIR)):
        if not name.endswith(".py"):
            continue
        src = open(os.path.join(_EXECUTORS_DIR, name), encoding="utf-8").read()
        marks = [(m.start(), m.group(1)) for m in _MODTYPE_RE.finditer(src)]
        for i, (pos, mtype) in enumerate(marks):
            end = marks[i + 1][0] if i + 1 < len(marks) else len(src)
            seg = src[pos:end]
            hits = {}
            # 先处理嵌套兜底链：默认值归属外层字段，内层历史别名不算独立字段。
            # 处理完把整段匹配文本置为等长空格，避免下面的规则重复命中内层。
            for m in list(_FIELD_NESTED_RE.finditer(seg)):
                outer, _legacy, default = m.group(1), m.group(2), m.group(3)
                if default.strip():
                    hits[outer] = default
            seg = _FIELD_NESTED_RE.sub(lambda m: " " * len(m.group(0)), seg)
            for field, default in _FIELD_RE.findall(seg):
                if default.strip():
                    hits[field] = default
            for field, default in _FIELD_OR_RE.findall(seg):
                if default.strip():
                    hits[field] = default
            if hits:
                findings.setdefault(mtype, {}).update(hits)
    return findings


@pytest.fixture(scope="module")
def backend_defaults():
    data = _backend_defaults()
    assert data, "未从后端执行器扫到任何带默认值的变量字段，说明扫描规则失效"
    return data


def test_every_backend_builtin_var_module_is_registered(backend_defaults):
    """后端「创建即内置变量」的模块必须都登记进前端 MODULE_DEFAULT_VARS"""
    registered = _frontend_registered()
    gaps = {t: f for t, f in backend_defaults.items() if t not in registered}
    detail = "\n".join(
        f"  {t}: " + ", ".join(f"{k}='{v}'" for k, v in sorted(fields.items()))
        for t, fields in sorted(gaps.items())
    )
    assert not gaps, (
        f"以下模块在后端带非空默认变量，但未登记进 frontend/src/lib/moduleDefaultVars.ts 的\n"
        f"MODULE_DEFAULT_VARS，其内置变量不会出现在变量名自动补全里（共 {len(gaps)} 个）：\n{detail}"
    )


def test_every_backend_builtin_var_field_is_registered(backend_defaults):
    """精度到字段：已登记模块也必须把每个带默认值的变量字段都登记齐。

    只按模块粒度比对会漏掉「模块登记了、但少登记一个字段」的情况
    （例如 webhook_request 曾只登记 response/status，漏了 headers/cookies）。
    """
    frontend = _frontend_entries()
    gaps = []
    for mtype, fields in sorted(backend_defaults.items()):
        if mtype not in frontend:
            continue  # 模块级缺口由上一个用例负责报告
        for field, default in sorted(fields.items()):
            if field not in frontend[mtype]:
                gaps.append(f"  {mtype}.{field} = '{default}'")
    assert not gaps, (
        "以下「模块.字段」在后端带非空默认变量，但前端 MODULE_DEFAULT_VARS 中该模块条目里缺失，\n"
        "这些内置变量不会出现在变量名自动补全里：\n" + "\n".join(gaps)
    )


def test_every_backend_var_field_is_whitelisted(backend_defaults):
    """后端用到的变量名字段必须都在 VARIABLE_NAME_FIELDS 白名单内。

    白名单是「从节点配置里提取已填变量名」的依据；漏收字段会导致用户改填自定义
    变量名后，补全与变量追踪都看不到它（sessionVariable 就曾漏收）。
    """
    whitelist = _frontend_whitelist()
    assert whitelist, "未解析到 VARIABLE_NAME_FIELDS 白名单，说明解析规则失效"
    missing = sorted({f for fields in backend_defaults.values() for f in fields} - whitelist)
    assert not missing, (
        "以下变量名字段被后端使用，但不在 VARIABLE_NAME_FIELDS 白名单内："
        + ", ".join(missing)
    )


# ============================================================================
# 三方默认变量名一致性审计（module-integrity-audit 任务 5 / Property 2、3、4、14）
#
# 三处默认变量名，冲突时以 addNode 为权威（设计决策 1）：
#   1) addNode 默认配置（frontend/src/store/workflowStore.ts）——决定运行时真实行为：
#      用户拖出节点时 addNode 就把值写进了 node.data，执行时后端读到的是这个值；
#   2) MODULE_DEFAULT_VARS（frontend/src/lib/moduleDefaultVars.ts）——补全兜底提示；
#   3) 后端执行器的 config.get 兜底默认值——只在 data 缺该字段时才生效。
#
# 为什么这组用例必须存在：上面三条既有用例只比对「后端 -> 前端」，查不出「addNode 有、
# 前端表没有」和「两处值不同」。而 addNode 才是运行时事实源，它与前端表不一致时，
# 补全会提示一个模块永远不会写入的名字（幽灵变量），用户照着写 {变量} 取不到值。
#
# 事实源解析器复用 backend/tests/contract/addnode_parser.py（Python 侧权威实现），
# 不在这里另写一份，避免两份解析逻辑漂移（Property 13 已守护它与前端侧口径一致）。
# ============================================================================

from tests.contract.addnode_parser import parse_add_node  # noqa: E402


@pytest.fixture(scope="module")
def addnode_fields():
    """{(module_type, field): 默认变量名}，来自 addNode 源码（权威事实源）"""
    parsed = parse_add_node()
    return {key: info["value"] for key, info in parsed.var_fields.items()}


@pytest.fixture(scope="module")
def addnode_computed():
    """{(module_type, field): 表达式}：addNode 里运行时计算的变量名，静态无法确定取值"""
    parsed = parse_add_node()
    return {(c["module_type"], c["field"]): c["expression"] for c in parsed.computed_var_fields}


def test_every_addnode_var_field_is_registered(addnode_fields):
    """Property 2：addNode 里出现的每个「模块.变量字段」都必须登记进 MODULE_DEFAULT_VARS。

    漏登记的后果：该模块拖到画布上时 node.data 里已经有这个变量名了，但补全列表
    读不到（补全的兜底来源是 MODULE_DEFAULT_VARS），用户不知道有这个变量可用。
    """
    frontend = _frontend_entries()
    gaps = []
    for (mtype, field), value in sorted(addnode_fields.items()):
        if field not in frontend.get(mtype, {}):
            gaps.append("  %s.%s = '%s'" % (mtype, field, value))
    assert not gaps, (
        u"以下「模块.字段」在 addNode 里已写入默认变量名，但 MODULE_DEFAULT_VARS 中缺失，\n"
        u"这些内置变量不会出现在变量名自动补全里（共 %d 条，以 addNode 为准补齐）：\n%s"
        % (len(gaps), "\n".join(gaps))
    )


def test_default_var_values_match_addnode(addnode_fields):
    """Property 3：同时存在于 addNode 与 MODULE_DEFAULT_VARS 的字段，默认值必须相同。

    不一致的后果：补全提示的名字和节点里实际写入的名字是两个，用户按提示写引用取不到值，
    同时全局变量面板会多出一个模块永远不会写入的幽灵变量。
    """
    frontend = _frontend_entries()
    diffs = []
    for (mtype, field), addnode_value in sorted(addnode_fields.items()):
        frontend_value = frontend.get(mtype, {}).get(field)
        if frontend_value is None:
            continue  # 缺失由 Property 2 负责报告
        if frontend_value != addnode_value:
            diffs.append("  %s.%s: addNode='%s' / MODULE_DEFAULT_VARS='%s'"
                         % (mtype, field, addnode_value, frontend_value))
    assert not diffs, (
        u"以下「模块.字段」的默认变量名在 addNode 与 MODULE_DEFAULT_VARS 之间不一致，\n"
        u"应以 addNode 为准修正前端表（共 %d 条）：\n%s" % (len(diffs), "\n".join(diffs))
    )


def test_backend_default_var_values_match_frontend(backend_defaults):
    """Property 4：同时存在于后端 config.get 兜底与 MODULE_DEFAULT_VARS 的字段，默认值必须相同。

    不一致的后果：老工作流的 data 里缺该字段时后端按自己的兜底名写变量，而补全提示的是
    另一个名字，用户排查不出为什么引用取不到值。
    """
    frontend = _frontend_entries()
    diffs = []
    for mtype, fields in sorted(backend_defaults.items()):
        for field, backend_value in sorted(fields.items()):
            frontend_value = frontend.get(mtype, {}).get(field)
            if frontend_value is None:
                continue  # 缺失由既有的 test_every_backend_builtin_var_field_is_registered 负责
            if frontend_value != backend_value:
                diffs.append("  %s.%s: 后端='%s' / MODULE_DEFAULT_VARS='%s'"
                             % (mtype, field, backend_value, frontend_value))
    assert not diffs, (
        u"以下「模块.字段」的默认变量名在后端执行器与 MODULE_DEFAULT_VARS 之间不一致（共 %d 条）。\n"
        u"逐条判定：addNode 有该字段时改后端对齐 addNode；仅后端兜底时改前端表对齐后端：\n%s"
        % (len(diffs), "\n".join(diffs))
    )


def test_no_phantom_default_vars(addnode_fields, addnode_computed, backend_defaults):
    """Property 14：MODULE_DEFAULT_VARS 里的每个默认值都必须在 addNode 或后端某一处真实存在。

    只在补全里出现、两个事实源都写不出来的名字就是幽灵变量：用户看到提示、写了引用，
    运行时永远取不到值。

    「无法静态确定」的处理：addNode 里形如 `variableName: varName` 的运行时计算取值
    （8 个 ai_* 任务）不参与判定，但计入 skipped 并在断言消息里打印数量，使跳过量可见，
    而不是悄悄放过。
    """
    frontend = _frontend_entries()
    phantoms = []
    skipped = []
    for mtype, fields in sorted(frontend.items()):
        for field, value in sorted(fields.items()):
            if (mtype, field) in addnode_computed:
                skipped.append("  %s.%s（addNode 里取值为运行时表达式 %s）"
                               % (mtype, field, addnode_computed[(mtype, field)]))
                continue
            sources = set()
            if addnode_fields.get((mtype, field)) == value:
                sources.add("addNode")
            if backend_defaults.get(mtype, {}).get(field) == value:
                sources.add("backend")
            if not sources:
                phantoms.append("  %s.%s = '%s'" % (mtype, field, value))

    message = (
        u"以下 %d 条 MODULE_DEFAULT_VARS 条目的默认变量名在 addNode 与后端执行器里都找不到"
        u"相同取值，属幽灵变量（补全会提示一个模块永远不会写入的名字）：\n%s"
        % (len(phantoms), "\n".join(phantoms))
    )
    if skipped:
        message += (
            u"\n\n另有 %d 条因取值为运行时表达式而无法静态确定，已跳过（可见的 skipped）：\n%s"
            % (len(skipped), "\n".join(skipped))
        )
    assert not phantoms, message
