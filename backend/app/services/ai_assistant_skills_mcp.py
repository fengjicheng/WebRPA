"""WebRPA AI 小助手 - MCP 管理 Skills

让 AI 小助手能直接为用户配置/管理 MCP（Model Context Protocol）服务器：
- 列出当前所有 MCP server 状态
- 添加 / 更新 / 删除 server 配置（自动持久化到 mcp_config.json）
- 启用 / 禁用 server
- 重新连接（让配置改动生效）
- 测试单个 server（短连接 + 拉 tools 列表，不影响全局状态）

设计要点：
- 所有写操作（add/update/delete/disable/enable）都自动调 mcp_manager.reload()
  让用户立刻在前端 MCP 配置面板和 AI 自身的 tools 列表里看到变化
- requires_approval=True 让用户对涉及配置文件改动的操作有最后一道确认
"""
from __future__ import annotations

import asyncio
from typing import Any

from app.services.ai_assistant_skills import Skill, registry
from app.services.mcp_manager import (
    load_mcp_config,
    save_mcp_config,
    mcp_manager,
    MCPConnection,
)


# =============================================================================
# Handler 实现
# =============================================================================

async def skill_list_mcp_servers() -> dict:
    """列出所有 MCP server 的配置 + 当前连接状态"""
    cfg = load_mcp_config()
    status = mcp_manager.status()
    status_map = {s["name"]: s for s in status.get("servers", [])}

    servers = []
    for name, server_cfg in (cfg.get("mcpServers") or {}).items():
        st = status_map.get(name) or {}
        servers.append({
            "name": name,
            "transport": server_cfg.get("transport") or ("stdio" if server_cfg.get("command") else "http"),
            "disabled": bool(server_cfg.get("disabled", False)),
            "connected": bool(st.get("connected", False)),
            "tool_count": int(st.get("tool_count", 0)),
            "last_error": st.get("last_error"),
            "auto_approve": server_cfg.get("autoApprove") or [],
            "config_summary": _summarize_server(server_cfg),
        })

    return {
        "total": len(servers),
        "servers": servers,
        "tools_injected": status.get("total_tools_injected", 0),
        "hint": (
            "用户配置 MCP 后必须调 reload_mcp 才生效（add/update/delete/toggle 已自动 reload）。"
            "已连接的 MCP 工具命名空间为 mcp__<server>__<tool>，已注入到 skill registry，可直接调用。"
        ),
    }


def _summarize_server(c: dict) -> str:
    """生成单行摘要"""
    t = (c.get("transport") or "").lower() or ("stdio" if c.get("command") else "")
    if t == "stdio" or c.get("command"):
        cmd = c.get("command") or ""
        args = " ".join(c.get("args") or [])
        return f"stdio: {cmd} {args}".strip()
    url = c.get("url") or ""
    return f"{t or 'http'}: {url}"


async def skill_get_mcp_server(name: str) -> dict:
    """读取单个 server 完整配置"""
    cfg = load_mcp_config()
    server_cfg = (cfg.get("mcpServers") or {}).get(name)
    if not server_cfg:
        return {"error": f"未找到 MCP 服务器：{name}", "available": list((cfg.get('mcpServers') or {}).keys())}

    status = mcp_manager.status()
    st = next((s for s in status.get("servers", []) if s["name"] == name), None)
    return {
        "name": name,
        "config": server_cfg,
        "status": st or {"connected": False, "note": "尚未连接（调 reload_mcp 让配置生效）"},
    }


async def skill_add_mcp_server(
    name: str,
    transport: str = "stdio",
    command: str | None = None,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
    cwd: str | None = None,
    url: str | None = None,
    headers: dict[str, str] | None = None,
    auto_approve: list[str] | None = None,
    disabled: bool = False,
    overwrite: bool = False,
) -> dict:
    """新增一个 MCP 服务器并自动 reload"""
    name = (name or "").strip()
    if not name:
        return {"error": "name 不能为空"}
    if " " in name:
        return {"error": "name 不能含空格，建议用连字符或下划线（例如 my-fs）"}

    transport = (transport or "stdio").lower()
    if transport not in ("stdio", "sse", "http", "streamable_http", "streamable-http"):
        return {"error": f"transport 仅支持 stdio / sse / http，当前：{transport}"}

    # 校验关键字段
    if transport == "stdio":
        if not command:
            return {"error": "stdio 模式必须提供 command（如 'npx' / 'node' / 'python'）"}
    else:
        if not url:
            return {"error": f"{transport} 模式必须提供 url"}

    cfg = load_mcp_config()
    servers = cfg.setdefault("mcpServers", {})
    if name in servers and not overwrite:
        return {
            "error": f"MCP 服务器 '{name}' 已存在",
            "hint": "传 overwrite=true 可覆盖；或先调 update_mcp_server 修改",
        }

    server_cfg: dict[str, Any] = {"transport": transport, "disabled": bool(disabled)}
    if transport == "stdio":
        server_cfg["command"] = command
        if args:
            server_cfg["args"] = list(args)
        if env:
            server_cfg["env"] = dict(env)
        if cwd:
            server_cfg["cwd"] = cwd
    else:
        server_cfg["url"] = url
        if headers:
            server_cfg["headers"] = dict(headers)
    if auto_approve:
        server_cfg["autoApprove"] = list(auto_approve)

    servers[name] = server_cfg
    save_mcp_config(cfg)

    # 自动 reload，让 AI 立刻能用上工具
    reload_summary = await mcp_manager.reload()
    server_status = next((s for s in reload_summary.get("connected", []) if s["name"] == name), None)
    failed_status = next((s for s in reload_summary.get("failed", []) if s["name"] == name), None)

    return {
        "success": True,
        "added": name,
        "config": server_cfg,
        "connected": bool(server_status),
        "tool_count": (server_status or {}).get("tool_count", 0),
        "connect_error": (failed_status or {}).get("error"),
        "hint": "已自动重连。前端「全局配置 → MCP」面板会同步显示新服务器。" + (
            f" 该服务器暴露 {server_status['tool_count']} 个工具，已注入 skill registry。"
            if server_status else " 但服务器连接失败，请检查 connect_error。"
        ),
    }


async def skill_update_mcp_server(
    name: str,
    updates: dict,
) -> dict:
    """部分更新某个 MCP 服务器配置（只覆盖传入的字段）"""
    cfg = load_mcp_config()
    servers = cfg.setdefault("mcpServers", {})
    if name not in servers:
        return {"error": f"MCP 服务器 '{name}' 不存在", "available": list(servers.keys())}

    server_cfg = dict(servers[name])
    # 字段白名单防误传
    allowed = {"transport", "command", "args", "env", "cwd", "url", "headers", "autoApprove", "auto_approve", "disabled"}
    ignored = []
    for k, v in (updates or {}).items():
        if k not in allowed:
            ignored.append(k)
            continue
        # 兼容 snake_case
        key = "autoApprove" if k == "auto_approve" else k
        server_cfg[key] = v
    servers[name] = server_cfg
    save_mcp_config(cfg)

    # 自动 reload
    reload_summary = await mcp_manager.reload()
    connected = next((s for s in reload_summary.get("connected", []) if s["name"] == name), None)
    failed = next((s for s in reload_summary.get("failed", []) if s["name"] == name), None)

    return {
        "success": True,
        "updated": name,
        "config": server_cfg,
        "connected": bool(connected),
        "tool_count": (connected or {}).get("tool_count", 0),
        "connect_error": (failed or {}).get("error"),
        "ignored_keys": ignored,
    }


async def skill_delete_mcp_server(name: str) -> dict:
    """删除一个 MCP 服务器配置（高危）"""
    cfg = load_mcp_config()
    servers = cfg.setdefault("mcpServers", {})
    if name not in servers:
        return {"error": f"MCP 服务器 '{name}' 不存在"}
    removed = servers.pop(name)
    save_mcp_config(cfg)
    await mcp_manager.reload()
    return {"success": True, "deleted": name, "removed_config": removed}


async def skill_toggle_mcp_server(name: str, disabled: bool | None = None) -> dict:
    """启用 / 禁用 MCP 服务器（不传 disabled 则切换当前状态）"""
    cfg = load_mcp_config()
    servers = cfg.setdefault("mcpServers", {})
    if name not in servers:
        return {"error": f"MCP 服务器 '{name}' 不存在"}
    if disabled is None:
        disabled = not bool(servers[name].get("disabled", False))
    servers[name] = {**servers[name], "disabled": bool(disabled)}
    save_mcp_config(cfg)
    await mcp_manager.reload()
    return {
        "success": True,
        "name": name,
        "disabled": bool(disabled),
        "state": "已禁用" if disabled else "已启用",
    }


async def skill_reload_mcp() -> dict:
    """重新连接所有 MCP 服务器（让配置文件改动生效）"""
    return await mcp_manager.reload()


async def skill_disconnect_all_mcp() -> dict:
    """断开所有 MCP 连接（用于排错或临时禁用）"""
    await mcp_manager.shutdown_all()
    return {"success": True, "note": "所有 MCP 服务器已断开。需要时调 reload_mcp 重连。"}


async def skill_test_mcp_server(
    transport: str = "stdio",
    command: str | None = None,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
    url: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> dict:
    """测试一组 MCP 配置能否成功连接 + 列出工具，但不写入配置文件、不影响全局状态。

    用于在 AI 帮用户配置之前先 dry-run 验证。
    """
    test_cfg: dict[str, Any] = {"transport": transport}
    if transport == "stdio":
        if not command:
            return {"error": "stdio 模式必须提供 command"}
        test_cfg["command"] = command
        if args:
            test_cfg["args"] = list(args)
        if env:
            test_cfg["env"] = dict(env)
    else:
        if not url:
            return {"error": f"{transport} 模式必须提供 url"}
        test_cfg["url"] = url
        if headers:
            test_cfg["headers"] = dict(headers)

    conn = MCPConnection("__probe__", test_cfg)
    try:
        ok, msg = await asyncio.wait_for(conn.connect(), timeout=float(timeout))
    except asyncio.TimeoutError:
        await conn.disconnect()
        return {"success": False, "error": f"连接超时（{timeout} 秒）"}
    except Exception as e:
        return {"success": False, "error": f"连接异常：{e}"}

    if not ok:
        await conn.disconnect()
        return {"success": False, "error": msg}

    tools = [
        {"name": t["name"], "description": t.get("description", "")}
        for t in conn.tools
    ]
    await conn.disconnect()
    return {
        "success": True,
        "tool_count": len(tools),
        "tools": tools[:20],
        "truncated": len(tools) > 20,
        "hint": "测试成功，可以放心调 add_mcp_server 正式落库。",
    }


# =============================================================================
# 注册到 skill registry
# =============================================================================

def _register_mcp_skills() -> None:
    registry.register(Skill(
        name="list_mcp_servers",
        description=(
            "列出当前所有 MCP（Model Context Protocol）服务器的配置和连接状态。"
            "返回每个 server 的 transport/disabled/connected/tool_count/last_error。"
            "用户问'我配了哪些 MCP'、'有什么外部工具可用'时调这个。"
        ),
        parameters={"type": "object", "properties": {}},
        handler=skill_list_mcp_servers,
    ))

    registry.register(Skill(
        name="get_mcp_server",
        description="读取某个 MCP 服务器的完整配置（含敏感字段，如 env、headers）",
        parameters={
            "type": "object",
            "properties": {"name": {"type": "string", "description": "服务器名称"}},
            "required": ["name"],
        },
        handler=skill_get_mcp_server,
    ))

    registry.register(Skill(
        name="add_mcp_server",
        description=(
            "为用户添加一个新的 MCP 服务器配置（自动持久化到 mcp_config.json + 自动重连）。"
            "transport 三种：stdio（本地子进程，最常用）/ sse（远程 SSE）/ http（远程 Streamable HTTP）。"
            "stdio 需要 command + args（如 command='npx', args=['-y','@modelcontextprotocol/server-filesystem','D:\\\\Documents']）。"
            "sse/http 需要 url + 可选 headers。env 是子进程环境变量（API Key 等）。"
            "成功后该 server 暴露的工具会立即以 mcp__<name>__<tool> 形式注入到你的 skill registry，可马上调用。"
            "建议在调用前先用 test_mcp_server 验证配置是否能连通。"
        ),
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "服务器名称（唯一标识，不能含空格，建议英文）"},
                "transport": {"type": "string", "enum": ["stdio", "sse", "http"], "default": "stdio"},
                "command": {"type": "string", "description": "stdio 模式必填，启动命令如 npx / node / python"},
                "args": {"type": "array", "items": {"type": "string"}, "description": "stdio 模式命令参数列表"},
                "env": {"type": "object", "description": "stdio 模式子进程环境变量（如 {API_KEY: 'xxx'}）"},
                "cwd": {"type": "string", "description": "stdio 模式工作目录（可选）"},
                "url": {"type": "string", "description": "sse / http 模式服务器 URL"},
                "headers": {"type": "object", "description": "sse / http 模式请求头"},
                "auto_approve": {"type": "array", "items": {"type": "string"}, "description": "白名单工具调用时不要求确认"},
                "disabled": {"type": "boolean", "default": False},
                "overwrite": {"type": "boolean", "default": False, "description": "已存在同名 server 时是否覆盖"},
            },
            "required": ["name"],
        },
        handler=skill_add_mcp_server,
        requires_approval=True,
    ))

    registry.register(Skill(
        name="update_mcp_server",
        description=(
            "局部更新某个 MCP 服务器的字段（只覆盖 updates 里传入的 key），自动持久化 + 自动重连。"
            "可改字段：transport / command / args / env / cwd / url / headers / autoApprove / disabled。"
        ),
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "updates": {"type": "object", "description": "要更新的字段，如 {args: [...], env: {...}}"},
            },
            "required": ["name", "updates"],
        },
        handler=skill_update_mcp_server,
        requires_approval=True,
    ))

    registry.register(Skill(
        name="delete_mcp_server",
        description="删除一个 MCP 服务器配置（不可恢复，会立即断开该 server 的连接和工具）",
        parameters={
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
        handler=skill_delete_mcp_server,
        requires_approval=True,
    ))

    registry.register(Skill(
        name="toggle_mcp_server",
        description="启用 / 禁用某个 MCP 服务器（不传 disabled 则切换当前状态）。禁用后该 server 不再连接，工具也会从 skill registry 移除。",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "disabled": {"type": "boolean", "description": "true=禁用 / false=启用 / 不传=切换"},
            },
            "required": ["name"],
        },
        handler=skill_toggle_mcp_server,
    ))

    registry.register(Skill(
        name="reload_mcp",
        description="按 mcp_config.json 重新连接所有 MCP 服务器（用户手动改了配置文件后让改动生效）",
        parameters={"type": "object", "properties": {}},
        handler=skill_reload_mcp,
    ))

    registry.register(Skill(
        name="disconnect_all_mcp",
        description="断开所有 MCP 服务器连接（排错或临时禁用，需要时再 reload_mcp 重连）",
        parameters={"type": "object", "properties": {}},
        handler=skill_disconnect_all_mcp,
        requires_approval=True,
    ))

    registry.register(Skill(
        name="test_mcp_server",
        description=(
            "测试一组 MCP 配置能否连通（短连接 + 拉 tools 列表，不写入配置、不影响全局）。"
            "推荐在 add_mcp_server 之前调一次以避免配置错误反复重连。"
        ),
        parameters={
            "type": "object",
            "properties": {
                "transport": {"type": "string", "enum": ["stdio", "sse", "http"], "default": "stdio"},
                "command": {"type": "string"},
                "args": {"type": "array", "items": {"type": "string"}},
                "env": {"type": "object"},
                "url": {"type": "string"},
                "headers": {"type": "object"},
                "timeout": {"type": "integer", "default": 30, "description": "连接超时秒数"},
            },
        },
        handler=skill_test_mcp_server,
    ))


_register_mcp_skills()
