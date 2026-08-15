# -*- coding: utf-8 -*-
"""契约：静态路由不得被路径参数路由遮蔽。

Starlette 按注册顺序匹配路由。若 ``/api/x/{id}`` 注册在 ``/api/x/静态段`` 之前，
访问静态路径会被路径参数路由抢先捕获，通常表现为莫名其妙的 404，
而且不会有任何启动期警告 —— 只能靠这条契约测试守住。

历史缺陷：``GET/DELETE /api/workflows/global-variables`` 曾被
``/api/workflows/{workflow_id}`` 遮蔽，全局变量接口长期返回 404。
"""
import re

import pytest

pytestmark = pytest.mark.contract


def _path_to_regex(path: str) -> re.Pattern:
    """把带 {参数} 的路由路径转成匹配具体 URL 的正则（参数不跨 /）。"""
    parts = re.split(r'(\{[^}]+\})', path)
    pattern = ''.join('[^/]+' if p.startswith('{') else re.escape(p) for p in parts)
    return re.compile('^' + pattern + '$')


def _collect_routes():
    from app.main import app

    routes = []
    for route in app.routes:
        path = getattr(route, 'path', None)
        methods = getattr(route, 'methods', None)
        if path and methods:
            routes.append((path, set(methods)))
    return routes


def _find_shadowed():
    routes = _collect_routes()
    shadowed = []
    for index, (path, methods) in enumerate(routes):
        if '{' in path:
            continue
        for prev_path, prev_methods in routes[:index]:
            if '{' not in prev_path or not (methods & prev_methods):
                continue
            if _path_to_regex(prev_path).match(path):
                shadowed.append((path, sorted(methods), prev_path))
                break
    return shadowed


def test_正则转换本身可靠():
    assert _path_to_regex('/api/x/{id}').match('/api/x/global-variables')
    assert not _path_to_regex('/api/x/{id}').match('/api/x/a/b')
    assert not _path_to_regex('/api/x/{id}/data').match('/api/x/a/full')


def test_不存在被路径参数遮蔽的静态路由():
    shadowed = _find_shadowed()
    detail = '\n'.join(
        f'  {",".join(methods)} {path}  被 {by} 抢先匹配' for path, methods, by in shadowed
    )
    assert not shadowed, f'存在被遮蔽的静态路由（会返回 404）：\n{detail}'


def test_全局变量接口可正常访问(client):
    """遮蔽缺陷的直接体现：这个接口曾经恒返回 404。"""
    resp = client.get('/api/workflows/global-variables')
    assert resp.status_code == 200
    body = resp.json()
    assert 'variables' in body and 'count' in body
