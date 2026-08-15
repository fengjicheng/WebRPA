# -*- coding: utf-8 -*-
"""Python脚本模块请求本机后端不受系统代理影响 —— 实机验证。

用户现象：开着 Clash 时，Python脚本 里请求 http://localhost:5241/api/... 报
「连接失败：请确保服务正在运行」，而后端明明在跑。原因是系统代理变量
（HTTP(S)_PROXY）对 localhost 生效：requests 会查 proxy_bypass() 所以能通，
但 urllib / httpx 不查，会把本机地址也发给代理。

这里用 urllib（最能暴露问题的那一类）真跑一次子进程脚本：
故意把代理指向一个不存在的端口，若本机地址仍走代理必然失败。
"""
import os
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler

import pytest

from app.executors.base import ExecutionContext
from app.executors.python_script import PythonScriptExecutor

pytestmark = pytest.mark.integration

# 指向一个几乎不可能有服务在听的端口：一旦请求走了代理就必然连接失败
_DEAD_PROXY = "http://127.0.0.1:9"


@pytest.fixture()
def local_server(tmp_path):
    (tmp_path / "ping.txt").write_text("pong", encoding="utf-8")
    handler = partial(SimpleHTTPRequestHandler, directory=str(tmp_path))
    server = HTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture()
def dead_proxy_env(monkeypatch):
    """模拟用户开着代理软件的环境，并清掉可能已存在的绕过列表。"""
    for key in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"):
        monkeypatch.setenv(key, _DEAD_PROXY)
    for key in ("NO_PROXY", "no_proxy"):
        monkeypatch.delenv(key, raising=False)


async def test_script_can_reach_local_backend_behind_proxy(local_server, dead_proxy_env):
    """脚本用 urllib 请求本机端口应当直连成功（不经过代理）"""
    port = local_server
    script = (
        "import urllib.request\n"
        f"with urllib.request.urlopen('http://localhost:{port}/ping.txt', timeout=10) as r:\n"
        "    print('BODY=' + r.read().decode('utf-8'))\n"
    )

    result = await PythonScriptExecutor().execute(
        {"scriptMode": "content", "scriptContent": script, "timeout": 60},
        ExecutionContext(),
    )

    assert result.success, f"本机请求仍被代理拦截: {result.error}"
    stdout = str((result.data or {}).get("stdout", ""))
    assert "BODY=pong" in stdout, f"未拿到本机后端响应: {stdout!r}"


async def test_public_host_still_uses_system_proxy(dead_proxy_env):
    """边界：公网地址仍应走用户的系统代理（这里代理是死的，所以必须失败）

    这条守住「不要顺手把所有请求都改成直连」——那会破坏用户的代理配置。
    """
    script = (
        "import urllib.request\n"
        "try:\n"
        "    urllib.request.urlopen('http://example.com/', timeout=8)\n"
        "    print('RESULT=direct')\n"
        "except Exception:\n"
        "    print('RESULT=proxied')\n"
    )

    result = await PythonScriptExecutor().execute(
        {"scriptMode": "content", "scriptContent": script, "timeout": 60},
        ExecutionContext(),
    )

    assert result.success, result.error
    stdout = str((result.data or {}).get("stdout", ""))
    assert "RESULT=proxied" in stdout, (
        f"公网请求没有走系统代理，说明绕过范围放得太宽: {stdout!r}")
