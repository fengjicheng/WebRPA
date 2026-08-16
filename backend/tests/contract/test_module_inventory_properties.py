# -*- coding: utf-8 -*-
"""审计函数自身的属性化测试（module-integrity-audit 任务 21）。

为什么要测「测试」：本 spec 的价值全部押在审计能真的报出缺口上。如果审计函数在某类
边界输入下静默返回空结果，所有断言都会变成恒绿的假绿——这正是它要替换掉的旧审计的
失效方式（自证闭环）。

因此这里用 hypothesis 对「任意 module_type 子集」生成输入，锁定三件事：
  1. 空集合、含伪类型、含未知 type 时不崩溃；
  2. 差集结果与集合运算的数学定义严格一致（不多报、不漏报）；
  3. 源码解析器遇到畸形输入时抛异常，绝不返回空结果。

前端侧没有配套的 fast-check 用例：项目 devDependencies 里没有 fast-check，为一条
可选任务新增依赖不划算。前端解析器的健壮性由 addNodeDefaults.test.ts 里的「解析失败
必须抛异常」三条用例覆盖，两侧口径一致由 Property 13 守护。
"""
import pytest
from hypothesis import given, settings, strategies as st

from tests.contract.addnode_parser import parse_add_node
from tests.contract.test_module_inventory import (
    PSEUDO_TYPES,
    count_disclosed_modules,
    diff_module_sets,
)

#: 生成 module_type 风格的标识符：既覆盖真实的伪类型，也覆盖任意未知 type
_TYPE_NAMES = st.one_of(
    st.sampled_from(sorted(PSEUDO_TYPES)),
    st.from_regex(r"\A[a-z][a-z0-9_]{0,20}\Z", fullmatch=True),
)
_TYPE_SETS = st.sets(_TYPE_NAMES, max_size=30)


@pytest.mark.contract
@given(frontend=_TYPE_SETS, backend=_TYPE_SETS, exempt=_TYPE_SETS)
@settings(max_examples=200, deadline=None)
def test_diff_module_sets_matches_set_algebra(frontend, backend, exempt):
    """差集结果必须严格等于集合运算的定义，且两个方向互不污染"""
    result = diff_module_sets(frontend, backend, exempt)

    assert set(result["frontend_only"]) == frontend - backend - exempt
    assert set(result["backend_only"]) == backend - frontend - exempt
    # 已排序（报告可读性依赖它）
    assert result["frontend_only"] == sorted(result["frontend_only"])
    assert result["backend_only"] == sorted(result["backend_only"])
    # 豁免项永远不出现在任何一侧
    assert not (set(result["frontend_only"]) & exempt)
    assert not (set(result["backend_only"]) & exempt)
    # 共有项永远不被报为差集
    common = frontend & backend
    assert not (set(result["frontend_only"]) & common)
    assert not (set(result["backend_only"]) & common)


@pytest.mark.contract
@given(types=_TYPE_SETS)
@settings(max_examples=100, deadline=None)
def test_diff_module_sets_is_empty_when_sides_agree(types):
    """两侧完全一致时差集必须为空——这条是「不误报」的下限"""
    result = diff_module_sets(types, types, set())
    assert result["frontend_only"] == []
    assert result["backend_only"] == []


@pytest.mark.contract
@given(frontend=_TYPE_SETS, backend=_TYPE_SETS)
@settings(max_examples=100, deadline=None)
def test_diff_module_sets_detects_every_single_sided_type(frontend, backend):
    """只在一侧出现的 type 必须**全部**被报出——这条是「不漏报」的下限。

    旧审计的失效方式就是漏报：它只在「模块在两边都登记」时才逐字段比对，
    整个模块缺失时反而什么都不报。
    """
    result = diff_module_sets(frontend, backend, set())
    for t in frontend - backend:
        assert t in result["frontend_only"], t
    for t in backend - frontend:
        assert t in result["backend_only"], t


@pytest.mark.contract
def test_diff_module_sets_handles_empty_inputs():
    """空集合不得崩溃，且不得凭空造出差集"""
    assert diff_module_sets(set(), set(), set()) == {"frontend_only": [], "backend_only": []}
    assert diff_module_sets({"a"}, set(), set())["frontend_only"] == ["a"]
    assert diff_module_sets(set(), {"a"}, set())["backend_only"] == ["a"]
    # 全部被豁免时两侧都为空
    assert diff_module_sets({"a"}, {"b"}, {"a", "b"}) == {"frontend_only": [], "backend_only": []}


@pytest.mark.contract
@given(types=_TYPE_SETS, excluded=_TYPE_SETS)
@settings(max_examples=100, deadline=None)
def test_count_disclosed_modules_never_negative_and_monotonic(types, excluded):
    """数量统计不得为负，且排除项越多结果越小（不会越算越多）"""
    count = count_disclosed_modules(types, excluded)
    assert 0 <= count <= len(types)
    assert count == len(types) - len(types & excluded)


# ------------------------------------------------- 解析器健壮性：畸形输入必须抛异常

#: 一段结构完整的最小 addNode 源码，用作变形基准
_MINIMAL_SOURCE = (
    "addNode: (type, position, extraConfig) => {\n"
    "  let defaultData = {}\n"
    "  if (type === 'demo_a') {\n"
    "    defaultData = { resultVariable: 'demo_a_result' }\n"
    "  } else if (type === 'demo_b' || type === 'demo_c') {\n"
    "    defaultData = { resultVariable: 'demo_bc_result' }\n"
    "  }\n"
    "}\n"
)


@pytest.mark.contract
def test_minimal_source_parses_as_expected():
    """先证明基准源码能被正确解析——否则下面的变形用例证明不了任何东西"""
    parsed = parse_add_node(_MINIMAL_SOURCE)
    assert parsed.branch_count == 2
    assert parsed.multi_type_branch_count == 1
    assert parsed.module_types == ["demo_a", "demo_b", "demo_c"]
    # 多类型分支必须展开成每个 type 各一条
    assert parsed.var_fields[("demo_b", "resultVariable")]["value"] == "demo_bc_result"
    assert parsed.var_fields[("demo_c", "resultVariable")]["value"] == "demo_bc_result"


@pytest.mark.contract
@given(
    junk=st.text(
        alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="{}`'\"/"),
        max_size=200,
    )
)
@settings(max_examples=100, deadline=None)
def test_parser_raises_on_source_without_add_node(junk):
    """源码里没有 addNode 锚点时必须抛异常，绝不返回空结果。

    生成的 junk 刻意排除花括号、引号与斜杠，避免偶然构造出合法结构；
    锚点本身也不可能出现在这样的字符集里。
    """
    with pytest.raises(AssertionError, match="找不到 addNode 函数签名锚点"):
        parse_add_node(junk)


@pytest.mark.contract
def test_parser_raises_on_structurally_broken_source():
    """结构被破坏的几种典型情况都必须抛异常"""
    # 花括号未配对
    with pytest.raises(AssertionError, match="未配对"):
        parse_add_node("addNode: (type, position, extraConfig) => {\n  if (type === 'a') {\n")
    # 有函数体但没有任何 type 分支
    with pytest.raises(AssertionError, match="未解析出任何"):
        parse_add_node("addNode: (type, position, extraConfig) => {\n  const a = 1\n}\n")
    # 有分支但分支里没有任何白名单变量字段
    with pytest.raises(AssertionError, match="未解析出任何变量名字段赋值"):
        parse_add_node(
            "addNode: (type, position, extraConfig) => {\n"
            "  if (type === 'a') {\n"
            "    defaultData = { timeout: 1000 }\n"
            "  }\n"
            "}\n"
        )


@pytest.mark.contract
@given(indent=st.integers(min_value=0, max_value=8), blank_lines=st.integers(min_value=0, max_value=5))
@settings(max_examples=50, deadline=None)
def test_parser_is_insensitive_to_indent_and_blank_lines(indent, blank_lines):
    """缩进与空行的变化不得影响解析结果——否则源码格式化一次审计就失效"""
    pad = " " * indent
    body = "\n".join(pad + line for line in _MINIMAL_SOURCE.splitlines())
    source = "\n" * blank_lines + body + "\n" * blank_lines
    parsed = parse_add_node(source)
    assert parsed.branch_count == 2
    assert parsed.module_types == ["demo_a", "demo_b", "demo_c"]
    assert len(parsed.var_fields) == 3


@pytest.mark.contract
def test_parser_ignores_comments_and_string_literals_in_structure():
    """注释与字符串里的花括号、分支写法都不得影响结构解析。

    这是「括号配对被字符串里的花括号带偏」这类真实 bug 的回归护栏。
    """
    source = (
        "addNode: (type, position, extraConfig) => {\n"
        "  const tip = 'if (type === \\'fake\\') { resultVariable: \\'fake_result\\' }'\n"
        "  // if (type === 'commented') { resultVariable: 'commented_result' }\n"
        "  if (type === 'real') {\n"
        "    defaultData = { resultVariable: 'real_result' }\n"
        "  }\n"
        "}\n"
    )
    parsed = parse_add_node(source)
    assert parsed.module_types == ["real"]
    assert set(parsed.var_fields) == {("real", "resultVariable")}
