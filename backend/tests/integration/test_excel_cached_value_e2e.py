# -*- coding: utf-8 -*-
"""集成：用真实 Excel（COM）生成带缓存计算值的 xlsx，验证值模式读到的是计算结果。

为什么必须用真实 Excel：
openpyxl 只能写公式，写不进公式的缓存计算值。而「读取区域 / 读取单元格」的值模式
依赖的正是 Excel 保存时写入的缓存值。只有让真实 Excel 保存一次，
才能验证「有缓存 → 读到数字」与「无缓存 → 回退公式文本」这两条分支都成立。

需要本机安装 Excel；未安装时整个模块跳过。
"""
import json

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.skipif(
    __import__("importlib").util.find_spec("win32com") is None,
    reason="需要 pywin32",
)]


@pytest.fixture(scope="module")
def excel_saved_xlsx(tmp_path_factory):
    """用真实 Excel 写入公式并保存，生成带缓存计算值的 xlsx。"""
    import pythoncom
    import win32com.client

    path = tmp_path_factory.mktemp("excel_com") / "缓存值.xlsx"
    # 只初始化不反初始化：同一线程里 CoUninitialize 会在 COM 对象尚未完全释放时
    # 触发 RPC_E_DISCONNECTED，且本进程后续可能还有别的 COM 用户。
    pythoncom.CoInitialize()
    try:
        # DispatchEx 强制新建独立实例，避免复用他处正在退出的 Excel 进程
        app = win32com.client.DispatchEx("Excel.Application")
    except Exception as exc:
        pytest.skip(f"本机无法启动 Excel COM，跳过: {exc}")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        wb = app.Workbooks.Add()
        ws = wb.Worksheets(1)
        ws.Range("A1").Value = 1
        ws.Range("A2").Value = 2
        ws.Range("B1").Formula = "=SUM(A1:A2)"
        # 数组公式：Excel 会把它标记为 ArrayFormula，并写入缓存结果
        ws.Range("B2").FormulaArray = "=SUM(A1:A2*2)"
        ws.Range("C1").Value = "2026-08-05"
        wb.SaveAs(str(path), FileFormat=51)  # 51 = xlsx
        wb.Close(SaveChanges=False)
        del ws, wb
    finally:
        app.Quit()
        del app
    return str(path)


async def test_值模式读到excel缓存的计算结果(excel_saved_xlsx, make_context):
    """核心断言：普通公式读出 3，数组公式读出 6，都不是公式文本、不是对象。"""
    from app.executors.advanced_openpyxl import ExcelReadRangeExecutor

    ctx = make_context()
    result = await ExcelReadRangeExecutor().execute(
        {"filePath": excel_saved_xlsx, "range": "A1:B2", "resultVariable": "range_data"}, ctx
    )
    assert result.success, result.error

    grid = ctx.get_variable("range_data")
    assert grid[0][1] == 3, f"普通公式应读到计算结果 3，实际 {grid[0][1]!r}"
    assert grid[1][1] == 6, f"数组公式应读到计算结果 6，实际 {grid[1][1]!r}"
    # 有缓存值时不应触发公式回退提示
    assert "无缓存计算值" not in result.message
    json.dumps(grid, ensure_ascii=False)


async def test_公式模式读到公式文本而非对象(excel_saved_xlsx, make_context):
    """同一份真实文件，公式模式必须读出公式文本，且数组公式不再泄漏 ArrayFormula 对象。"""
    from app.executors.advanced_openpyxl import ExcelReadRangeExecutor

    ctx = make_context()
    result = await ExcelReadRangeExecutor().execute(
        {"filePath": excel_saved_xlsx, "range": "B1:B2", "resultVariable": "f",
         "readContent": "formula"}, ctx
    )
    assert result.success, result.error

    grid = ctx.get_variable("f")
    assert grid[0][0] == "=SUM(A1:A2)"
    assert "SUM(A1:A2*2)" in grid[1][0]
    for row in grid:
        for cell in row:
            assert isinstance(cell, str), f"公式模式仍泄漏了对象: {type(cell).__name__}"
    # 打印日志场景：渲染必须成功
    json.loads(ctx.resolve_value("{f}"))


async def test_真实文件下打印日志全链路不再失败(excel_saved_xlsx, make_context):
    """还原用户工作流：读取区域 → 打印日志 {range_data}。"""
    from app.executors.advanced_openpyxl import ExcelReadRangeExecutor
    from app.executors.basic import PrintLogExecutor

    ctx = make_context()
    read = await ExcelReadRangeExecutor().execute(
        {"filePath": excel_saved_xlsx, "range": "A1:C2", "resultVariable": "range_data"}, ctx
    )
    assert read.success, read.error

    logged = await PrintLogExecutor().execute({"logMessage": "{range_data}"}, ctx)
    assert logged.success, logged.error
    assert json.loads(logged.message)
