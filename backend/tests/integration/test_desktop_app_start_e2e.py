# -*- coding: utf-8 -*-
"""集成：真实启动桌面应用（记事本），回归 to_bool 三参数调用崩溃。

用户反馈：用「启动桌面应用」模块启动记事本直接报
    启动应用失败: to_bool() takes from 1 to 2 positional arguments but 3 were given
根因是 to_bool 早先的签名与 to_int / to_float 不一致，
桌面自动化模块整批按 (value, default, context) 调用，每次执行必抛 TypeError。

这里真实启动 notepad.exe 并等待窗口就绪，跑完关掉进程。
需要 Windows + uiautomation；缺任一条件则跳过。
"""
import os

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.name != "nt", reason="仅 Windows 适用"),
]

NOTEPAD = r"C:\Windows\System32\notepad.exe"


def _kill(pid):
    import subprocess
    subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                   capture_output=True, check=False)


@pytest.fixture(autouse=True)
def _require_uiautomation():
    pytest.importorskip("uiautomation", reason="需要 uiautomation 库")
    if not os.path.exists(NOTEPAD):
        pytest.skip("本机没有 notepad.exe")


async def test_启动记事本并等待窗口就绪(make_context):
    """默认配置（waitReady=True）下必须成功拿到窗口句柄。"""
    from app.executors.desktop_automation import DesktopAppStartExecutor

    ctx = make_context()
    result = await DesktopAppStartExecutor().execute(
        {"appPath": NOTEPAD, "waitReady": True, "waitTimeout": 15,
         "saveToVariable": "desktop_app"}, ctx
    )
    pid = (result.data or {}).get("process_id")
    try:
        assert result.success, result.error
        assert pid, "应返回进程 ID"
        saved = ctx.get_variable("desktop_app")
        assert isinstance(saved, dict), f"变量应存为字典，实际 {type(saved).__name__}"
        assert saved.get("handle"), "应拿到窗口句柄"
        assert saved.get("process_id") == pid
    finally:
        if pid:
            _kill(pid)


async def test_不等待就绪也能启动(make_context):
    """waitReady=False 走另一条分支，同样不能因参数转换崩溃。"""
    from app.executors.desktop_automation import DesktopAppStartExecutor

    ctx = make_context()
    result = await DesktopAppStartExecutor().execute(
        {"appPath": NOTEPAD, "waitReady": False}, ctx
    )
    pid = (result.data or {}).get("process_id")
    try:
        assert result.success, result.error
        assert pid
    finally:
        if pid:
            _kill(pid)


async def test_waitReady_传变量字符串也能解析(make_context):
    """waitReady 支持 {变量}：解析成 false 时走不等待分支。"""
    from app.executors.desktop_automation import DesktopAppStartExecutor

    ctx = make_context({"要等待": "false"})
    result = await DesktopAppStartExecutor().execute(
        {"appPath": NOTEPAD, "waitReady": "{要等待}"}, ctx
    )
    pid = (result.data or {}).get("process_id")
    try:
        assert result.success, result.error
        # 未等待就绪时不返回窗口句柄
        assert "handle" not in (result.data or {})
    finally:
        if pid:
            _kill(pid)


async def test_等待应用就绪模块能接上启动结果(make_context):
    """还原用户工作流：启动桌面应用 → 等待应用就绪。"""
    from app.executors.desktop_automation import (
        DesktopAppStartExecutor, DesktopAppWaitReadyExecutor,
    )

    ctx = make_context()
    started = await DesktopAppStartExecutor().execute(
        {"appPath": NOTEPAD, "waitReady": True, "waitTimeout": 15,
         "saveToVariable": "desktop_app"}, ctx
    )
    pid = (started.data or {}).get("process_id")
    try:
        assert started.success, started.error
        ready = await DesktopAppWaitReadyExecutor().execute(
            {"appVariable": "desktop_app", "timeout": 15}, ctx
        )
        assert ready.success, ready.error
    finally:
        if pid:
            _kill(pid)


async def test_应用路径不存在时给出明确错误(make_context):
    from app.executors.desktop_automation import DesktopAppStartExecutor

    ctx = make_context()
    result = await DesktopAppStartExecutor().execute(
        {"appPath": r"C:\不存在的目录\不存在.exe"}, ctx
    )
    assert not result.success
    assert "不存在" in (result.error or "")


async def test_获取窗口列表不再因参数转换崩溃(make_context):
    """同一批 to_bool 误用波及桌面自动化整组模块，这里覆盖另一条不依赖特定应用的路径。"""
    from app.executors.desktop_automation import DesktopWindowListExecutor

    ctx = make_context()
    result = await DesktopWindowListExecutor().execute(
        {"filterVisible": True, "filterEnabled": False, "saveToVariable": "windows"}, ctx
    )
    assert result.success, result.error
    # 桌面上总会有窗口存在（至少资源管理器/终端）
    windows = ctx.get_variable("windows")
    assert isinstance(windows, list), f"应存为列表，实际 {type(windows).__name__}"


async def test_获取窗口列表支持变量开关(make_context):
    from app.executors.desktop_automation import DesktopWindowListExecutor

    ctx = make_context({"只看可见": "false"})
    result = await DesktopWindowListExecutor().execute(
        {"filterVisible": "{只看可见}", "saveToVariable": "windows"}, ctx
    )
    assert result.success, result.error


async def test_获取窗口信息返回可见性字段(make_context):
    """回归 uiautomation 没有 IsVisible 属性导致「获取应用信息」整个模块失败。"""
    from app.executors.desktop_automation import (
        DesktopAppStartExecutor, DesktopAppGetInfoExecutor,
    )

    ctx = make_context()
    started = await DesktopAppStartExecutor().execute(
        {"appPath": NOTEPAD, "waitReady": True, "waitTimeout": 15,
         "saveToVariable": "desktop_app"}, ctx
    )
    pid = (started.data or {}).get("process_id")
    try:
        assert started.success, started.error
        info = await DesktopAppGetInfoExecutor().execute(
            {"appVariable": "desktop_app", "saveToVariable": "win_info"}, ctx
        )
        assert info.success, info.error
        saved = ctx.get_variable("win_info")
        assert isinstance(saved, dict)
        assert isinstance(saved.get("is_visible"), bool), "可见性必须是布尔值"
        assert saved["is_visible"] is True, "刚启动的记事本窗口应当可见"
    finally:
        if pid:
            _kill(pid)
