# -*- coding: utf-8 -*-
"""接口：浏览器配置同步链路必须把「自动关闭浏览器」开关传达到计划任务。

用户反馈：全局设置里关掉「工作流结束后自动关闭浏览器」，
在没有手动启动自动化浏览器的情况下让计划任务自动执行，跑完照样把浏览器关了。

根因是计划任务收尾曾无条件 cleanup()。修复后它读
browser_config_store 里持久化的 autoCloseBrowser，
因此这条链路必须端到端可用：前端 POST 同步 → 落盘 → 计划任务读取。
"""
import pytest

pytestmark = pytest.mark.api


@pytest.fixture
def 恢复浏览器配置():
    from app.services import browser_config_store

    原配置 = dict(browser_config_store.get_browser_config())
    yield
    browser_config_store.set_browser_config(原配置)


def test_同步关闭开关后计划任务读到的是关闭(client, 恢复浏览器配置):
    from app.services import browser_config_store

    resp = client.post('/api/system/browser-config', json={
        'type': 'msedge', 'autoCloseBrowser': False,
    })
    assert resp.status_code == 200, resp.text

    # 计划任务走的就是这个读取入口
    assert browser_config_store.get_browser_config().get('autoCloseBrowser') is False


def test_同步开启开关后计划任务读到的是开启(client, 恢复浏览器配置):
    from app.services import browser_config_store

    resp = client.post('/api/system/browser-config', json={
        'type': 'msedge', 'autoCloseBrowser': True,
    })
    assert resp.status_code == 200, resp.text
    assert browser_config_store.get_browser_config().get('autoCloseBrowser') is True


def test_读取接口回显同步后的开关(client, 恢复浏览器配置):
    client.post('/api/system/browser-config', json={'type': 'msedge', 'autoCloseBrowser': False})
    resp = client.get('/api/system/browser-config')
    assert resp.status_code == 200
    assert resp.json()['config']['autoCloseBrowser'] is False


def test_未提供该字段时保留默认值不被抹成关闭(client, 恢复浏览器配置):
    """只同步浏览器类型时不能把开关静默改掉，否则用户的选择会被无关操作覆盖。"""
    from app.services import browser_config_store

    client.post('/api/system/browser-config', json={'type': 'msedge', 'autoCloseBrowser': True})
    client.post('/api/system/browser-config', json={'type': 'chrome'})
    cfg = browser_config_store.get_browser_config()
    assert cfg.get('type') == 'chrome'
    assert cfg.get('autoCloseBrowser') is True, '同步其它字段不应改动自动关闭开关'
