# -*- coding: utf-8 -*-
"""契约：to_int / to_float / to_bool 的调用方式必须正确。

历史缺陷：to_bool 早先的签名是 (value, context)，与 to_int / to_float 的
(value, default, context) 不一致。桌面自动化模块按惯例写成
to_bool(x, 默认值, context)，运行时直接抛
"to_bool() takes from 1 to 2 positional arguments but 3 were given"，
「启动桌面应用」等模块整批失效，而且这类错误没有任何静态检查会发现。

同一批还查出 to_int 少传必填的 default（wait_page_load 的 timeout）。

三个函数签名现已统一，本测试用 AST 静态守护调用方式，
让同类错误在测试阶段暴露，而不是等用户运行工作流时才炸。
"""
import ast
import inspect
from pathlib import Path

import pytest

from app.executors import type_utils

pytestmark = pytest.mark.contract

APP_DIR = Path(type_utils.__file__).resolve().parent.parent
CONVERTERS = ("to_int", "to_float", "to_bool")


def _iter_calls():
    """遍历 app 下所有对三个转换函数的调用。"""
    for path in APP_DIR.rglob("*.py"):
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, SyntaxError):
            continue
        lines = source.splitlines()
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id in CONVERTERS):
                snippet = lines[node.lineno - 1].strip() if node.lineno - 1 < len(lines) else ""
                yield path, node, snippet


def test_三个转换函数签名保持一致():
    """value, default, context 顺序一致，否则调用方按惯例写就会传错位置。"""
    for name in CONVERTERS:
        params = list(inspect.signature(getattr(type_utils, name)).parameters)
        assert params[:3] == ["value", "default", "context"], (
            f"{name} 的参数顺序为 {params}，必须与其它转换函数一致（value, default, context）"
        )


def test_context_不得作为第二个位置参数传入():
    """第二个位置参数是 default。把 context 传到这里会让默认值变成 ExecutionContext，
    且变量不再被解析（静默错误，比抛异常更难查）。"""
    offenders = []
    for path, node, snippet in _iter_calls():
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Name) and node.args[1].id == "context":
            offenders.append(f"{path.name}:{node.lineno}  {snippet}")
    assert not offenders, "context 必须用关键字传入（context=context）：\n  " + "\n  ".join(offenders)


def test_调用位置参数个数不超过三个():
    offenders = []
    for path, node, snippet in _iter_calls():
        if len(node.args) > 3:
            offenders.append(f"{path.name}:{node.lineno}  {snippet}")
    assert not offenders, "位置参数超过 (value, default, context) 三个：\n  " + "\n  ".join(offenders)


def test_必须显式提供默认值():
    """default 是必填语义：只传 value 会让 to_int / to_float 抛 TypeError，
    to_bool 则静默退化成 False，两者都是缺陷。"""
    offenders = []
    for path, node, snippet in _iter_calls():
        has_default = len(node.args) >= 2 or any(k.arg == "default" for k in node.keywords)
        if not has_default:
            offenders.append(f"{path.name}:{node.lineno}  {snippet}")
    assert not offenders, "缺少默认值参数：\n  " + "\n  ".join(offenders)


def test_config默认值与转换默认值一致():
    """两处默认值必须相同，否则配置项留空时会拿到另一个默认值。

    例如 to_bool(config.get("hidden", True), False)：键不存在得到 True，
    键存在但为空串却得到 False —— 同一个配置项有两种默认行为。
    """
    offenders = []
    for path, node, snippet in _iter_calls():
        value = node.args[0] if node.args else None
        if not (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
                and value.func.attr == "get" and len(value.args) == 2
                and isinstance(value.args[1], ast.Constant)):
            continue
        inner = value.args[1].value
        if len(node.args) < 2 or not isinstance(node.args[1], ast.Constant):
            offenders.append(f"{path.name}:{node.lineno}  {snippet}")
            continue
        outer = node.args[1].value
        # bool 必须严格同型（True != 1）；数值按值比较，容许 1 与 1.0
        same = (outer is inner) if isinstance(inner, bool) or isinstance(outer, bool) else (outer == inner)
        if not same:
            offenders.append(f"{path.name}:{node.lineno}  {snippet}")
    assert not offenders, "config.get 默认值与转换默认值不一致：\n  " + "\n  ".join(offenders)


class _Ctx:
    """最小上下文替身，只提供 resolve_value。"""

    def __init__(self, mapping):
        self.mapping = mapping

    def resolve_value(self, value):
        return self.mapping.get(value, value)


def test_to_bool_三参数调用可用():
    """回归「启动桌面应用」的报错形态。"""
    assert type_utils.to_bool(None, True, None) is True
    assert type_utils.to_bool("{开关}", True, _Ctx({"{开关}": "false"})) is False
    assert type_utils.to_bool("{开关}", False, _Ctx({"{开关}": "true"})) is True


def test_to_bool_空值与未知值退回默认():
    assert type_utils.to_bool("", True) is True
    assert type_utils.to_bool("   ", True) is True
    assert type_utils.to_bool(None, True) is True
    assert type_utils.to_bool(object(), True) is True
    assert type_utils.to_bool("", False) is False


def test_to_bool_常规取值不受默认值影响():
    for truthy in (True, 1, "true", "YES", "1", "on", "Enabled"):
        assert type_utils.to_bool(truthy, False) is True
    for falsy in (False, 0, "false", "no", "off", "disabled"):
        assert type_utils.to_bool(falsy, True) is False


def test_to_bool_关键字传_context_仍解析变量():
    assert type_utils.to_bool("{开关}", context=_Ctx({"{开关}": "true"})) is True
