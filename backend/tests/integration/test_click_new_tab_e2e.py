# -*- coding: utf-8 -*-
"""点击元素 → 新标签页 的实机验证（真实浏览器）。

复现用户反馈的原始场景：点击 target="_blank" 链接后，后续模块该在哪个页面上操作。
默认跳过，需要真实浏览器时用环境变量开启：

    $env:WEBRPA_BROWSER_E2E='1'
    ..\Python313\python.exe -m pytest tests/integration/test_click_new_tab_e2e.py -v
"""
import os
import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

_ENABLED = os.environ.get("WEBRPA_BROWSER_E2E", "").strip() in ("1", "true", "yes")
pytest_skip_reason = "需真实浏览器：设置 WEBRPA_BROWSER_E2E=1 后运行"

A_HTML = """<!doctype html><html><body>
<a id="news" href="b.html" target="_blank">新闻</a>
<!-- 复现「DOM 里存在但不可见」的元素：点击它会一直等可见直到超时 -->
<a id="hidden-home" style="display:none">回首页</a>
</body></html>"""

B_HTML = """<!doctype html><html><body><a id="home" href="a.html">回首页</a></body></html>"""

XP_NEWS = "xpath=//a[normalize-space(text())='新闻']"
XP_HOME = "xpath=//a[normalize-space(text())='回首页']"


def _make_pages() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="webrpa_e2e_"))
    (tmp / "a.html").write_text(A_HTML, encoding="utf-8")
    (tmp / "b.html").write_text(B_HTML, encoding="utf-8")
    return tmp


async def _open(pw, tmp):
    from app.executors.base import ExecutionContext

    browser = await pw.chromium.launch(headless=True, channel="msedge")
    bc = await browser.new_context()
    page = await bc.new_page()
    await page.goto((tmp / "a.html").as_uri())
    ctx = ExecutionContext()
    ctx.browser_context = bc
    ctx.page = page
    return browser, ctx


@pytest.mark.skipif(not _ENABLED, reason=pytest_skip_reason)
async def test_follow_new_tab_makes_next_module_work():
    """勾选跟进后：点击新闻 → 自动切到新标签页 → 后续点击「回首页」成功"""
    from playwright.async_api import async_playwright
    from app.executors.basic import ClickElementExecutor

    tmp = _make_pages()
    click = ClickElementExecutor()
    async with async_playwright() as pw:
        browser, ctx = await _open(pw, tmp)
        try:
            r = await click.execute(
                {"selector": XP_NEWS, "timeout": 10, "followNewTab": True}, ctx)
            assert r.success, r.error
            assert "已跟进新标签页" in (r.message or "")
            assert ctx.page.url.endswith("b.html"), "必须切到新标签页"

            # 新标签页上的「回首页」是可见的，这一步应当成功
            r2 = await click.execute({"selector": XP_HOME, "timeout": 10}, ctx)
            assert r2.success, f"跟进后后续模块应能操作新页面: {r2.error}"
        finally:
            await browser.close()


@pytest.mark.skipif(not _ENABLED, reason=pytest_skip_reason)
async def test_default_keeps_original_page_and_warns():
    """不勾选（既有行为）：仍留在原页面，但要留下明确提示"""
    from playwright.async_api import async_playwright
    from app.executors.basic import ClickElementExecutor

    tmp = _make_pages()
    click = ClickElementExecutor()
    async with async_playwright() as pw:
        browser, ctx = await _open(pw, tmp)
        try:
            r = await click.execute({"selector": XP_NEWS, "timeout": 10}, ctx)
            assert r.success, r.error
            assert ctx.page.url.endswith("a.html"), "默认行为不变：不切换页面"

            # 下一个网页模块运行时兜底提示（新标签页事件可能晚于点击返回才投递）
            r2 = await click.execute({"selector": XP_NEWS, "timeout": 3}, ctx)
            warns = [x for x in ctx.get_logs() if x["level"] == "warning"]
            assert warns, "开了新标签页却始终不提示，用户无法自查"
            assert "跟进新标签页" in warns[0]["message"]
            assert ctx.page.url.endswith("a.html"), "提示不应改变页面"
        finally:
            await browser.close()


@pytest.mark.skipif(not _ENABLED, reason=pytest_skip_reason)
async def test_hidden_element_click_gives_diagnosis():
    """元素存在但不可见时，报错要说清原因而不是只丢一句 Timeout"""
    from playwright.async_api import async_playwright
    from app.executors.basic import ClickElementExecutor

    tmp = _make_pages()
    click = ClickElementExecutor()
    async with async_playwright() as pw:
        browser, ctx = await _open(pw, tmp)
        try:
            # a.html 上的「回首页」是 display:none 的
            r = await click.execute({"selector": XP_HOME, "timeout": 3}, ctx)
            assert not r.success
            assert "不可见" in (r.error or ""), f"缺少可行动的诊断: {r.error}"
            assert "元素可见判断" in (r.error or "")
        finally:
            await browser.close()
