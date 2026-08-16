# -*- coding: utf-8 -*-
"""addNode 解析器两侧一致性守护（Property 13）。

两份解析器：
  · Python 侧（本目录 addnode_parser.py）——权威实现，跨端一致性审计用它；
  · 前端 vitest 侧（frontend/src/lib/__tests__/helpers/addNodeDefaults.ts）——快速反馈。

为什么不让一侧直接调另一侧：前端那份是 TypeScript 且用了 `@/` 路径别名，node 无法
直接执行；反过来在 vitest 里跑 Python 也不现实。因此改用**共用基线文件**做比对媒介
（frontend/src/lib/__tests__/helpers/addNodeParserBaseline.json）：两侧各自断言自己的
解析结果等于基线，从而间接保证两侧口径一致。

这个方案比「只比对条目总数」更严：除总数外还比对分支数、多类型分支数、module_type
覆盖数、逐字段分布与函数体行范围。任一侧解析器漂移（例如漏展开 `||` 多类型分支、
把注释里的示例当成真实赋值、括号配对被字符串里的花括号带偏）都会立刻失败。

源码正常新增模块时两侧会同时失败，只需更新基线一处；禁止为了变绿而随手改基线数字。
"""
import pytest

from tests.contract.addnode_parser import load_baseline, parse_add_node


@pytest.fixture(scope="module")
def parsed():
    return parse_add_node()


@pytest.fixture(scope="module")
def baseline():
    return load_baseline()


@pytest.mark.contract
def test_add_node_body_does_not_swallow_sibling_actions(parsed, baseline):
    """函数体边界不得吞入相邻的 store 动作。

    不用绝对行号断言：行号会随 workflowStore.ts 任何位置的增删行漂移，锁死它只会制造
    维护负担。改为结构性断言——括号配对一旦被字符串里的花括号带偏，函数体就会延伸到
    后面的 updateNodeData / blockInsertNode 等动作，这里正是检查这一点。
    """
    body = parsed.body_text
    swallowed = [sig for sig in baseline["forbiddenInBody"] if sig in body]
    assert not swallowed, (
        u"addNode 函数体吞入了相邻 store 动作 %s，说明括号配对被带偏（通常是字符串里的花括号）。\n"
        u"函数体起止行号：%s" % (swallowed, parsed.body_lines)
    )


@pytest.mark.contract
def test_branch_count_matches_baseline(parsed, baseline):
    """分支数与多类型分支数必须与基线一致"""
    assert parsed.branch_count == baseline["branchCount"], (
        u"addNode 分支数与基线不一致：实际 %d，基线 %d"
        % (parsed.branch_count, baseline["branchCount"])
    )
    assert parsed.multi_type_branch_count == baseline["multiTypeBranchCount"], (
        u"`||` 多类型分支数与基线不一致：实际 %d，基线 %d"
        % (parsed.multi_type_branch_count, baseline["multiTypeBranchCount"])
    )


@pytest.mark.contract
def test_module_type_coverage_matches_baseline(parsed, baseline):
    """分支覆盖的 module_type 数必须与基线一致（多类型分支必须已展开）"""
    assert len(parsed.module_types) == baseline["moduleTypeCount"], (
        u"分支覆盖的 module_type 数与基线不一致：实际 %d，基线 %d。\n"
        u"少于基线通常是 `||` 连接的多类型分支没有展开，会导致共用分支的模块被漏审。"
        % (len(parsed.module_types), baseline["moduleTypeCount"])
    )
    assert len(set(parsed.module_types)) == len(parsed.module_types), u"module_type 清单不应有重复"


@pytest.mark.contract
def test_var_field_count_matches_baseline(parsed, baseline):
    """Property 13 核心：解析出的「模块.字段」条目数必须与基线一致"""
    actual = len(parsed.var_fields)
    expected = baseline["varFieldCount"]
    assert actual == expected, (
        u"两侧解析器口径不一致或解析规则已漂移。\n"
        u"  Python 侧解析出「模块.字段」条目：%d 条\n"
        u"  共用基线（前端侧同样断言该值）：%d 条\n"
        u"若确认是源码新增模块导致，请在确认两侧解析逻辑仍正确后同步更新基线文件。"
        % (actual, expected)
    )
    assert len(parsed.modules_with_var_fields) == baseline["modulesWithVarFieldsCount"], (
        u"有变量字段的 module_type 数与基线不一致：实际 %d，基线 %d"
        % (len(parsed.modules_with_var_fields), baseline["modulesWithVarFieldsCount"])
    )


@pytest.mark.contract
def test_field_distribution_matches_baseline(parsed, baseline):
    """逐字段分布必须与基线一致——只比总数会漏掉「A 字段多解析、B 字段少解析」的互相抵消"""
    actual = parsed.field_distribution()
    expected = {k: v for k, v in baseline["fieldDistribution"].items()}
    diff = {
        field: (actual.get(field, 0), expected.get(field, 0))
        for field in set(actual) | set(expected)
        if actual.get(field, 0) != expected.get(field, 0)
    }
    detail = u"\n".join(
        u"  %s: 实际 %d / 基线 %d" % (f, a, e) for f, (a, e) in sorted(diff.items())
    )
    assert not diff, u"变量字段分布与基线不一致：\n" + detail


@pytest.mark.contract
def test_computed_var_fields_are_reported(parsed, baseline):
    """运行时计算的变量名必须被单独报出（可见的 skipped），而不是静默漏掉"""
    ai_computed = [
        c for c in parsed.computed_var_fields
        if c["module_type"].startswith("ai_") and c["field"] == "variableName"
    ]
    assert len(ai_computed) >= baseline["computedVarFieldCount"], (
        u"8 个 ai_* 任务的 `variableName: varName` 属运行时计算，应被计入「无法静态确定」，"
        u"实际只报出 %d 条" % len(ai_computed)
    )
    literal_keys = set(parsed.var_fields)
    leaked = [c for c in ai_computed if (c["module_type"], c["field"]) in literal_keys]
    assert not leaked, u"运行时表达式被误判为字符串字面量：%s" % leaked
