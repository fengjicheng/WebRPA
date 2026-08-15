# -*- coding: utf-8 -*-
"""值规范化工具：把任意 Python 值转换成 JSON 原生类型。

存在原因
--------
工作流的变量系统按 JSON 类型设计：变量既要能被 ``{变量名}`` 渲染成文本，
也要能通过 WebSocket 推给前端、通过接口返回、传给 Python 脚本子进程。
一旦变量里混入非 JSON 原生对象（Excel 的 ``datetime``/``ArrayFormula``、
``Decimal``、``bytes`` 等），上述任一出口都会抛
``TypeError: Object of type X is not JSON serializable``，
并把整条工作流带崩。

因此提供两个入口：
- :func:`to_json_safe`  递归规范化，用于写入变量、返回接口数据
- :func:`json_default`  给 ``json.dumps(default=...)`` 兜底，用于渲染文本

不在本模块 import openpyxl：Excel 依赖在执行器里是懒加载的，
这里改用鸭子类型（类名 + 属性）识别 openpyxl 的公式与富文本对象。
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

# openpyxl.worksheet.formula 中的公式包装类型，其 text 属性为公式文本（如 "=SUM(A1:A2)"）
_FORMULA_TYPE_NAMES = frozenset({'ArrayFormula', 'DataTableFormula'})

# openpyxl 富文本片段，其 text 属性为该片段的纯文本
_RICH_TEXT_BLOCK_NAMES = frozenset({'TextBlock'})

_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
_DATE_FORMAT = '%Y-%m-%d'
_TIME_FORMAT = '%H:%M:%S'

# 递归深度上限：防御自引用结构与超深嵌套导致的栈溢出
_MAX_DEPTH = 20


def normalize_datetime(value: datetime) -> str:
    """datetime 转文本。零点整的时间视为纯日期，避免给用户多出 " 00:00:00"。"""
    if value.hour == 0 and value.minute == 0 and value.second == 0 and value.microsecond == 0:
        return value.strftime(_DATE_FORMAT)
    return value.strftime(_DATETIME_FORMAT)


def _formula_text(value: Any) -> str:
    """取 openpyxl 公式对象的公式文本，取不到则退化为 str()。"""
    text = getattr(value, 'text', None)
    if isinstance(text, str) and text:
        return text
    return str(value)


def _rich_text_to_plain(value: Any) -> str:
    """把 openpyxl 富文本（CellRichText，list 子类）拼成纯文本。"""
    parts = []
    for block in value:
        if isinstance(block, str):
            parts.append(block)
        else:
            text = getattr(block, 'text', None)
            parts.append(text if isinstance(text, str) else str(block))
    return ''.join(parts)


def _is_rich_text(value: Any) -> bool:
    """识别 openpyxl 的 CellRichText：list 子类且元素含 TextBlock。"""
    if not isinstance(value, list) or type(value) is list:
        return False
    return any(type(block).__name__ in _RICH_TEXT_BLOCK_NAMES for block in value)


def json_default(value: Any) -> Any:
    """``json.dumps(default=...)`` 的兜底转换器。

    只在 json 模块遇到无法直接序列化的对象时被调用，因此这里不做递归，
    返回值仍会交给 json 模块继续处理。
    """
    if isinstance(value, datetime):
        return normalize_datetime(value)
    if isinstance(value, date):
        return value.strftime(_DATE_FORMAT)
    if isinstance(value, time):
        return value.strftime(_TIME_FORMAT)
    if isinstance(value, timedelta):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (bytes, bytearray)):
        return value.decode('utf-8', errors='replace')
    if isinstance(value, (set, frozenset, tuple)):
        return list(value)
    if type(value).__name__ in _FORMULA_TYPE_NAMES:
        return _formula_text(value)
    return str(value)


def to_json_safe(value: Any, _depth: int = 0) -> Any:
    """递归把值规范化成 JSON 原生类型（dict / list / str / int / float / bool / None）。

    - ``datetime`` / ``date`` / ``time`` / ``timedelta`` 转常规日期时间文本
    - openpyxl 公式对象（ArrayFormula / DataTableFormula）转公式文本
    - openpyxl 富文本（CellRichText）转纯文本
    - ``Decimal`` 转 float，``bytes`` 按 UTF-8 解码，``set`` / ``tuple`` 转 list
    - dict 的键统一转成字符串（JSON 对象键只能是字符串）
    - 其余无法识别的对象转 ``str()``，保证结果一定可被 json 序列化

    ``float('nan')`` / ``inf`` 保持原样：标准库 ``json.dumps`` 默认接受它们，
    这里不做改写以免影响既有数值计算模块的行为。
    """
    if _depth > _MAX_DEPTH:
        return str(value)

    if value is None or isinstance(value, (str, bool, int, float)):
        return value

    # datetime 是 date 的子类，必须先判 datetime
    if isinstance(value, datetime):
        return normalize_datetime(value)
    if isinstance(value, date):
        return value.strftime(_DATE_FORMAT)
    if isinstance(value, time):
        return value.strftime(_TIME_FORMAT)
    if isinstance(value, timedelta):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (bytes, bytearray)):
        return value.decode('utf-8', errors='replace')

    if type(value).__name__ in _FORMULA_TYPE_NAMES:
        return _formula_text(value)

    if _is_rich_text(value):
        return _rich_text_to_plain(value)

    if isinstance(value, dict):
        return {
            (key if isinstance(key, str) else str(to_json_safe(key, _depth + 1))):
                to_json_safe(item, _depth + 1)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_json_safe(item, _depth + 1) for item in value]

    return str(value)


def dumps_json_safe(value: Any, **kwargs: Any) -> str:
    """``json.dumps`` 的安全版：默认不转义非 ASCII，并对未知对象兜底。"""
    import json

    kwargs.setdefault('ensure_ascii', False)
    kwargs.setdefault('default', json_default)
    return json.dumps(value, **kwargs)
