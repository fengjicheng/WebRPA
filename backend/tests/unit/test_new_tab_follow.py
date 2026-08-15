# -*- coding: utf-8 -*-
"""点击后新标签页跟进 / 本机请求不走代理 的单元测试。

背景（用户实机反馈）：
点击链接打开新标签页后，执行上下文仍停留在原页面——因为 switch_to_latest_page
只在当前页被关闭时才切换。于是后续模块全在旧页面上找元素，表现为
「元素明明在新页面上却找不到」，而日志里看不出任何异常。
现在改为：默认行为不变，但会明确提示；勾选「点击后跟进新标签页」则自动切过去。
"""
import pytest

from app.executors.base import ExecutionContext
from app.executors.python_script import _local_no_proxy_env

pytestmark = pytest.mark.unit


class _FakePage:
    def __init__(self, url):
        self.url = url
        self.load_state_waited = False

    async def wait_for_load_state(self, state="load", timeout=None):
        self.load_state_waited = True


class _FakeBrowserContext:
    """只实现监听器与页面列表，其余不涉及。"""

    def __init__(self, pages=None):
        self.pages = list(pages or [])
        self._listeners: dict[str, list] = {}

    def on(self, event, cb):
        self._listeners.setdefault(event, []).append(cb)

    def remove_listener(self, event, cb):
        self._listeners.get(event, []).remove(cb)

    def listener_count(self, event="page"):
        return len(self._listeners.get(event, []))

    def open_page(self, url):
        """模拟浏览器打开新标签页并派发 page 事件。"""
        page = _FakePage(url)
        self.pages.append(page)
        for cb in list(self._listeners.get("page", [])):
            cb(page)
        return page


def _ctx():
    origin = _FakePage("https://example.com/a")
    bc = _FakeBrowserContext([origin])
    ctx = ExecutionContext()
    ctx.browser_context = bc
    ctx.page = origin
    return ctx, bc, origin


async def test_no_new_tab_means_no_side_effect():
    """没有开新标签页时：不切页、不写日志、监听器摘干净"""
    ctx, bc, origin = _ctx()

    watch = ctx.begin_watch_new_tabs()
    assert bc.listener_count() == 1, "必须在交互前挂上监听，否则点击瞬间开的标签页会漏掉"

    extra = await ctx.settle_new_tabs(watch, follow=False)
    assert extra == ""
    assert ctx.page is origin
    assert ctx.get_logs() == []
    assert bc.listener_count() == 0, "收尾后必须摘除监听器，否则循环里会越积越多"


async def test_new_tab_without_follow_keeps_page_but_warns():
    """默认（不跟进）：保持原页面不变，但必须留下一条可执行的警告"""
    ctx, bc, origin = _ctx()

    watch = ctx.begin_watch_new_tabs()
    bc.open_page("https://example.com/b")
    extra = await ctx.settle_new_tabs(watch, follow=False)

    assert extra == "", "不跟进时不应改动模块消息"
    assert ctx.page is origin, "既有行为必须保持：默认不切换页面"
    logs = ctx.get_logs()
    assert len(logs) == 1 and logs[0]["level"] == "warning"
    msg = logs[0]["message"]
    # 提示必须说清「现状 + 两条出路」，否则用户无从自查
    assert "新标签页" in msg
    assert "跟进新标签页" in msg
    assert "切换标签页" in msg
    assert bc.listener_count() == 0


async def test_switch_to_latest_page_warns_about_unfollowed_tab():
    """兜底提示：新标签页事件晚到时，下一个网页模块运行时也要能提示出来

    这是零开销路径——只读 browser_context.pages，不做任何等待。
    """
    ctx, bc, origin = _ctx()
    bc.pages.append(_FakePage("https://example.com/b"))  # 模拟事件未及时投递

    switched = await ctx.switch_to_latest_page()

    assert switched is False, "既有行为不变：当前页有效就不切换"
    assert ctx.page is origin
    warns = [x for x in ctx.get_logs() if x["level"] == "warning"]
    assert len(warns) == 1
    assert "找不到" in warns[0]["message"], "要点明这正是「元素找不到」的原因"


async def test_unfollowed_tab_hint_only_once():
    """密集循环里不能反复刷同一条提示"""
    ctx, bc, origin = _ctx()
    bc.pages.append(_FakePage("https://example.com/b"))

    for _ in range(5):
        await ctx.switch_to_latest_page()

    assert len([x for x in ctx.get_logs() if x["level"] == "warning"]) == 1


async def test_manual_tab_switch_suppresses_hint():
    """用过「切换标签页」模块后，主动停在非最新标签页是合法用法，不该再提示"""
    ctx, bc, origin = _ctx()
    bc.pages.append(_FakePage("https://example.com/b"))
    ctx._manual_tab_switch = True

    await ctx.switch_to_latest_page()

    assert ctx.get_logs() == []


async def test_no_hint_when_already_on_latest_tab():
    """当前就在最新标签页上时不提示"""
    ctx, bc, origin = _ctx()
    newest = _FakePage("https://example.com/b")
    bc.pages.append(newest)
    ctx.page = newest

    await ctx.switch_to_latest_page()

    assert ctx.get_logs() == []


async def test_new_tab_with_follow_switches_page():
    """勾选跟进：切到新标签页，并等过加载状态"""
    ctx, bc, origin = _ctx()

    watch = ctx.begin_watch_new_tabs()
    new_page = bc.open_page("https://example.com/b")
    extra = await ctx.settle_new_tabs(watch, follow=True)

    assert ctx.page is new_page
    assert new_page.load_state_waited is True
    assert "已跟进新标签页" in extra
    assert "https://example.com/b" in extra
    assert any(log["level"] == "info" for log in ctx.get_logs())
    assert bc.listener_count() == 0


async def test_follow_clears_iframe_state():
    """切页时必须清空 iframe 状态，否则后续模块会拿旧页的 frame 去操作"""
    ctx, bc, origin = _ctx()
    ctx._in_iframe = True
    ctx._current_frame = object()
    ctx._iframe_locator = {"type": "index", "value": 0}
    ctx._main_page = origin

    watch = ctx.begin_watch_new_tabs()
    new_page = bc.open_page("https://example.com/b")
    await ctx.settle_new_tabs(watch, follow=True)

    assert ctx.page is new_page
    assert ctx._in_iframe is False
    assert ctx._current_frame is None
    assert ctx._iframe_locator is None
    assert ctx._main_page is None


async def test_follow_waits_for_late_opened_tab():
    """新标签页略晚于点击返回才出现时，跟进模式要能等到它"""
    import asyncio

    ctx, bc, origin = _ctx()
    watch = ctx.begin_watch_new_tabs()

    async def open_later():
        await asyncio.sleep(0.25)
        bc.open_page("https://example.com/late")

    task = asyncio.create_task(open_later())
    extra = await ctx.settle_new_tabs(watch, follow=True, wait_ms=3000)
    await task

    assert "https://example.com/late" in extra
    assert ctx.page.url == "https://example.com/late"


async def test_no_browser_context_is_safe():
    """纯本地流程（没开浏览器）调用这套 API 不能炸"""
    ctx = ExecutionContext()
    watch = ctx.begin_watch_new_tabs()
    assert watch["pages"] == [] and watch["listener"] is None
    assert await ctx.settle_new_tabs(watch, follow=True) == ""


class _FakeLocator:
    def __init__(self, count, visible):
        self._count = count
        self._visible = visible

    @property
    def first(self):
        return self

    async def count(self):
        return self._count

    async def is_visible(self):
        return self._visible


class _FakeLocatorPage:
    def __init__(self, count, visible):
        self._loc = _FakeLocator(count, visible)

    def locator(self, selector):
        return self._loc


async def test_diagnose_element_not_found():
    ctx = ExecutionContext()
    msg = await ctx.describe_element_state(_FakeLocatorPage(0, False), "#nope")
    assert "找不到该选择器匹配的元素" in msg
    assert "iframe" in msg


async def test_diagnose_element_exists_but_hidden():
    """用户实机踩的就是这一条：元素在 DOM 里但不可见，点击白等满超时"""
    ctx = ExecutionContext()
    msg = await ctx.describe_element_state(_FakeLocatorPage(1, False), "//a[text()='百度首页']")
    assert "不可见" in msg
    assert "元素可见判断" in msg, "必须给出可直接照做的替代方案"


async def test_diagnose_element_visible():
    ctx = ExecutionContext()
    msg = await ctx.describe_element_state(_FakeLocatorPage(2, True), "a")
    assert "可见" in msg and "遮挡" in msg


def test_local_no_proxy_appends_local_hosts():
    """开了系统代理时，脚本请求本机后端必须直连"""
    env = _local_no_proxy_env({})
    for host in ("localhost", "127.0.0.1", "::1"):
        assert host in env["NO_PROXY"]
    # 大小写两个键都要写：不同库读的键名不一样
    assert env["NO_PROXY"] == env["no_proxy"]


def test_local_no_proxy_preserves_user_entries():
    """不能覆盖用户已有的绕过列表，也不能重复追加"""
    env = _local_no_proxy_env({"NO_PROXY": "example.com,localhost"})
    items = env["NO_PROXY"].split(",")
    assert "example.com" in items
    assert items.count("localhost") == 1
    assert "127.0.0.1" in items
