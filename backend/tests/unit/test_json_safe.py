# -*- coding: utf-8 -*-
"""值规范化工具单元测试。

覆盖 app/utils/json_safe.py：确保任意值都能被规范化成 JSON 原生类型，
杜绝 "Object of type X is not JSON serializable" 把工作流带崩。
"""
import json
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pytest

from app.utils.json_safe import dumps_json_safe, json_default, to_json_safe

pytestmark = pytest.mark.unit


class _Opaque:
    """模拟任意第三方对象。"""

    def __str__(self):
        return "OPAQUE"


# 按类名模拟 openpyxl 的公式与富文本类型（json_safe 用鸭子类型识别，不硬依赖 openpyxl）
ArrayFormula = type("ArrayFormula", (), {
    "__init__": lambda self, text: setattr(self, "text", text),
    "__str__": lambda self: "<ArrayFormula>",
})
DataTableFormula = type("DataTableFormula", (), {"__str__": lambda self: "<DataTable>"})
TextBlock = type("TextBlock", (), {
    "__init__": lambda self, text: setattr(self, "text", text),
})


def test_datetime_零点整规范化为纯日期():
    assert to_json_safe(datetime(2026, 8, 5)) == "2026-08-05"


def test_datetime_带时间规范化为日期时间():
    assert to_json_safe(datetime(2026, 8, 5, 22, 27, 5)) == "2026-08-05 22:27:05"


def test_date_time_timedelta_均转文本():
    assert to_json_safe(date(2026, 8, 5)) == "2026-08-05"
    assert to_json_safe(time(9, 30)) == "09:30:00"
    assert to_json_safe(timedelta(hours=1, minutes=30)) == "1:30:00"


def test_decimal_转float_bytes_解码():
    assert to_json_safe(Decimal("3.5")) == 3.5
    assert to_json_safe(b"\xe4\xbd\xa0\xe5\xa5\xbd") == "你好"


def test_公式对象取公式文本():
    assert to_json_safe(ArrayFormula("=SUM(A1:A2*2)")) == "=SUM(A1:A2*2)"


def test_公式对象无text属性时退化为str():
    assert to_json_safe(DataTableFormula()) == "<DataTable>"


def test_富文本拼成纯文本():
    rich = type("CellRichText", (list,), {})([TextBlock("加粗"), "普通"])
    assert to_json_safe(rich) == "加粗普通"


def test_普通列表不被误判为富文本():
    assert to_json_safe(["a", "b"]) == ["a", "b"]


def test_嵌套结构递归规范化():
    value = {"日期": datetime(2026, 8, 5, 10, 0), "行": [[1, ArrayFormula("=A1")], (2, Decimal("1.5"))]}
    assert to_json_safe(value) == {"日期": "2026-08-05 10:00:00", "行": [[1, "=A1"], [2, 1.5]]}


def test_dict_非字符串键转字符串():
    assert to_json_safe({1: "a", date(2026, 1, 1): "b"}) == {"1": "a", "2026-01-01": "b"}


def test_set_与_tuple_转列表():
    assert to_json_safe((1, 2)) == [1, 2]
    assert sorted(to_json_safe({1, 2})) == [1, 2]


def test_未知对象退化为str():
    assert to_json_safe(_Opaque()) == "OPAQUE"


@pytest.mark.parametrize("value", [None, True, False, 0, -1, 1.5, "文本"])
def test_基础类型原样返回(value):
    assert to_json_safe(value) == value
    assert type(to_json_safe(value)) is type(value)


def test_超深嵌套不栈溢出():
    deep = current = []
    for _ in range(60):
        nxt = []
        current.append(nxt)
        current = nxt
    # 不抛异常即通过，且结果可序列化
    json.dumps(to_json_safe(deep))


def test_自引用结构不死循环():
    loop = {}
    loop["self"] = loop
    json.dumps(to_json_safe(loop))


def test_规范化结果一定可被json序列化():
    value = {"a": datetime.now(), "b": [ArrayFormula("=1"), _Opaque(), Decimal("2")]}
    json.dumps(to_json_safe(value), ensure_ascii=False)


def test_dumps_json_safe_直接吃下脏值():
    out = dumps_json_safe({"d": datetime(2026, 8, 5, 1, 2, 3)})
    assert out == '{"d": "2026-08-05 01:02:03"}'


def test_dumps_json_safe_默认不转义中文():
    assert dumps_json_safe({"k": "中文"}) == '{"k": "中文"}'


def test_json_default_供dumps兜底():
    assert json.dumps({"d": date(2026, 8, 5)}, default=json_default) == '{"d": "2026-08-05"}'
