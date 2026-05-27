"""WebRPA AI 小助手 - MCP（Model Context Protocol）支持

提供：
1. 用户配置的 MCP 服务器持久化（backend/data/mcp_config.json）
2. 多服务器并发连接（stdio / sse / http 三种 transport）
3. 自动发现每个服务器暴露的 tools 并注入到 AI 小助手的 skill registry
4. 工具调用透传：AI 调 mcp__<server>__<tool> 时转发给对应服务器
5. 服务器健康监控、自动重连、出错隔离

设计要点：
- 每个 MCP server 以独立 task 维持长连接（subprocess 或 SSE/HTTP stream）
- 工具注入到 skill registry，命名空间为 mcp__<serverName>__<toolName>
  避免与 WebRPA 内置 skill 冲突
- 配置改动支持热重载：修改后自动重启对应 server
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from contextlib import AsyncExitStack
from datetime import datetime
from pathlib import Path
from typing import Any

from app.services.ai_assistant_skills import Skill, registry


# =============================================================================
# 配置持久化
# =============================================================================

def _config_path() -> Path:
    p = Path(__file__).parent.parent.parent / "data" / "mcp_config.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_mcp_config() -> dict:
    """读取 MCP 配置（标准 mcpServers JSON 格式，与 Claude Desktop / Kiro 兼容）。

    格式示例：
    {
      "mcpServers": {
        "filesystem": {
          "transport": "stdio",
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"],
          "env": {"FOO": "bar"},
          "disabled": false,
          "autoApprove": ["read_file"]
        },
        "weather-api": {
          "transport": "sse",
          "url": "https://example.com/sse",
          "headers": {"Authorization": "Bearer ..."}
        },
        "github": {
          "transport": "http",
          "url": "https://api.github.com/mcp",
          "headers": {}
        }
      }
    }
    """
    p = _config_path()
    if not p.exists():
        return {"mcpServers": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"mcpServers": {}}


def save_mcp_config(config: dict) -> None:
    p = _config_path()
    p.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


# =============================================================================
# 单个 MCP 连接（封装 stdio / sse / http 三种 transport）
# =============================================================================

class MCPConnection:
    """一个 MCP 服务器的长连接封装"""

    def __init__(self, name: str, server_config: dict) -> None:
        self.name = name
        self.config = server_config
        self.session = None  # type: ignore  # mcp.ClientSession
        self._stack: AsyncExitStack | None = None
        self._tools: list[dict] = []  # 缓存的 tool list
        self._task: asyncio.Task | None = None
        self.connected = False
        self.last_error: str | None = None
        self.connected_at: datetime | None = None
        self._lock = asyncio.Lock()

    @property
    def transport(self) -> str:
        # 自动推断 transport：有 command 是 stdio，有 url 看协议
        explicit = (self.config.get("transport") or "").lower()
        if explicit:
            return explicit
        if self.config.get("command"):
            return "stdio"
        url = (self.config.get("url") or "").lower()
        if url.endswith("/sse") or "sse" in url:
            return "sse"
        if url:
            return "http"
        return "stdio"

    @property
    def disabled(self) -> bool:
        return bool(self.config.get("disabled", False))

    @property
    def auto_approve(self) -> set[str]:
        return set(self.config.get("autoApprove") or [])

    async def connect(self) -> tuple[bool, str]:
        """建立连接并初始化 session。返回 (success, msg/err)"""
        async with self._lock:
            if self.connected:
                return True, "already connected"
            if self.disabled:
                return False, "disabled"

            try:
                from mcp import ClientSession
            except ImportError:
                return False, "mcp SDK 未安装"

            self._stack = AsyncExitStack()
            try:
                read, write = await self._open_transport()

                # 某些 transport（如 streamable_http）返回 (read, write, get_session_id)
                # 我们只需 read/write
                session = await self._stack.enter_async_context(
                    ClientSession(read, write)
                )
                await session.initialize()

                # 拉一次 tools 列表
                try:
                    tool_resp = await session.list_tools()
                    self._tools = [
                        {
                            "name": t.name,
                            "description": t.description or "",
                            "inputSchema": t.inputSchema or {"type": "object", "properties": {}},
                        }
                        for t in tool_resp.tools
                    ]
                except Exception as e:
                    self._tools = []
                    print(f"[MCP] {self.name} list_tools 失败: {e}")

                self.session = session
                self.connected = True
                self.connected_at = datetime.now()
                self.last_error = None
                return True, f"已连接，发现 {len(self._tools)} 个工具"
            except Exception as e:
                self.last_error = str(e)
                self.connected = False
                # 关闭 stack
                if self._stack:
                    try:
                        await self._stack.aclose()
                    except Exception:
                        pass
                self._stack = None
                return False, str(e)

    async def _open_transport(self):
        """打开 transport，返回 (read, write) stream"""
        t = self.transport

        if t == "stdio":
            from mcp import StdioServerParameters
            from mcp.client.stdio import stdio_client

            command = self.config.get("command")
            args = self.config.get("args") or []
            env = self.config.get("env") or {}
            cwd = self.config.get("cwd")

            if not command:
                raise ValueError("stdio transport 需要 command")

            # 合并系统 env（不然 npx / node 命令找不到 PATH）
            full_env = {**os.environ, **env}

            params = StdioServerParameters(
                command=command,
                args=list(args),
                env=full_env,
                cwd=cwd,
            )
            read, write = await self._stack.enter_async_context(stdio_client(params))
            return read, write

        if t == "sse":
            from mcp.client.sse import sse_client
            url = self.config.get("url")
            headers = self.config.get("headers") or {}
            if not url:
                raise ValueError("sse transport 需要 url")
            read, write = await self._stack.enter_async_context(
                sse_client(url=url, headers=headers)
            )
            return read, write

        if t in ("http", "streamable_http", "streamable-http"):
            from mcp.client.streamable_http import streamablehttp_client
            url = self.config.get("url")
            headers = self.config.get("headers") or {}
            if not url:
                raise ValueError("http transport 需要 url")
            ctx = await self._stack.enter_async_context(
                streamablehttp_client(url=url, headers=headers)
            )
            # streamablehttp 返回 3-tuple (read, write, get_session_id)
            if isinstance(ctx, tuple) and len(ctx) >= 2:
                return ctx[0], ctx[1]
            raise ValueError("streamable_http 返回值非预期")

        raise ValueError(f"不支持的 transport: {t}")

    async def disconnect(self) -> None:
        async with self._lock:
            self.connected = False
            self.session = None
            if self._stack:
                try:
                    await self._stack.aclose()
                except Exception:
                    pass
                self._stack = None
            self._tools = []

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """调用工具，返回结构化结果"""
        if not self.connected or not self.session:
            return {"error": f"MCP 服务器 '{self.name}' 未连接"}
        try:
            result = await self.session.call_tool(tool_name, arguments=arguments or {})
            # 把 MCP 的 ContentBlock 序列化
            content_text = []
            for c in (result.content or []):
                if hasattr(c, "text"):
                    content_text.append(c.text)
                elif hasattr(c, "data"):
                    content_text.append(f"[binary {len(c.data)} bytes]")
                else:
                    content_text.append(str(c))
            return {
                "is_error": bool(getattr(result, "isError", False)),
                "content": "\n".join(content_text) or "",
                "raw": [str(c) for c in (result.content or [])],
            }
        except Exception as e:
            return {"error": f"call_tool '{tool_name}' 失败: {e}"}

    @property
    def tools(self) -> list[dict]:
        return list(self._tools)


# =============================================================================
# 全局 MCP Manager
# =============================================================================

class MCPManager:
    """所有 MCP 连接的全局管理器"""

    def __init__(self) -> None:
        self.connections: dict[str, MCPConnection] = {}
        self._registered_skill_names: set[str] = set()

    async def reload(self) -> dict:
        """根据 mcp_config.json 重新初始化所有连接

        返回 summary：{connected: [...], failed: [...], disabled: [...]}
        """
        config = load_mcp_config()
        servers = config.get("mcpServers") or {}

        # 1) 先断开所有现有连接 + 反注册 skill
        await self.shutdown_all()

        connected_list = []
        failed_list = []
        disabled_list = []

        # 2) 依次连接（出错的不影响其他）
        # 用 gather 并发
        async def _try_connect(name: str, server_cfg: dict):
            conn = MCPConnection(name, server_cfg)
            self.connections[name] = conn
            if conn.disabled:
                disabled_list.append(name)
                return
            ok, msg = await conn.connect()
            if ok:
                self._inject_skills(conn)
                connected_list.append({
                    "name": name,
                    "tool_count": len(conn.tools),
                    "transport": conn.transport,
                })
            else:
                failed_list.append({"name": name, "error": msg})

        await asyncio.gather(
            *[_try_connect(n, c) for n, c in servers.items()],
            return_exceptions=True,
        )

        return {
            "connected": connected_list,
            "failed": failed_list,
            "disabled": disabled_list,
            "total_servers": len(servers),
        }

    def _inject_skills(self, conn: MCPConnection) -> None:
        """把 MCP 工具注入到 skill registry，命名空间 mcp__<server>__<tool>"""
        for tool in conn.tools:
            tool_name = tool["name"]
            skill_name = f"mcp__{conn.name}__{tool_name}"
            # 避免名字过长导致 LLM 体验差
            if len(skill_name) > 64:
                skill_name = skill_name[:60] + "_etc"

            # 用工厂函数捕获 server name + tool name（避免闭包变量问题）
            def _make_handler(_conn: "MCPConnection", _tool_name: str):
                async def _handler(**kwargs: Any) -> dict:
                    return await _conn.call_tool(_tool_name, kwargs)
                return _handler

            params = tool.get("inputSchema") or {"type": "object", "properties": {}}
            # 兼容 inputSchema 可能不规范的情况
            if not isinstance(params, dict):
                params = {"type": "object", "properties": {}}
            if "type" not in params:
                params["type"] = "object"

            skill = Skill(
                name=skill_name,
                description=f"[MCP·{conn.name}] {tool.get('description') or tool_name}",
                parameters=params,
                handler=_make_handler(conn, tool_name),
                requires_approval=tool_name not in conn.auto_approve,
            )
            registry.register(skill)
            self._registered_skill_names.add(skill_name)

    async def shutdown_all(self) -> None:
        """断开所有连接 + 反注册 skill"""
        # 反注册 skill
        for sn in list(self._registered_skill_names):
            registry._skills.pop(sn, None)
        self._registered_skill_names.clear()

        # 断开连接
        await asyncio.gather(
            *[c.disconnect() for c in self.connections.values()],
            return_exceptions=True,
        )
        self.connections.clear()

    def status(self) -> dict:
        """当前所有 MCP server 的状态"""
        return {
            "servers": [
                {
                    "name": name,
                    "transport": conn.transport,
                    "disabled": conn.disabled,
                    "connected": conn.connected,
                    "tool_count": len(conn.tools),
                    "tools": [
                        {"name": t["name"], "description": t.get("description", "")}
                        for t in conn.tools
                    ],
                    "last_error": conn.last_error,
                    "connected_at": conn.connected_at.isoformat() if conn.connected_at else None,
                    "auto_approve": list(conn.auto_approve),
                }
                for name, conn in self.connections.items()
            ],
            "total_tools_injected": len(self._registered_skill_names),
        }


# 全局单例
mcp_manager = MCPManager()


# =============================================================================
# 启动时自动加载 MCP（从 main.py 调用）
# =============================================================================

async def init_mcp_at_startup() -> dict:
    """后端启动时调用，根据用户配置自动连接所有 MCP server。"""
    try:
        result = await mcp_manager.reload()
        if result["connected"]:
            print(f"[MCP] 已连接 {len(result['connected'])} 个 MCP 服务器，"
                  f"注入 {sum(c['tool_count'] for c in result['connected'])} 个工具")
        if result["failed"]:
            for f in result["failed"]:
                print(f"[MCP] {f['name']} 连接失败: {f['error']}")
        return result
    except Exception as e:
        print(f"[MCP] 初始化异常: {e}")
        return {"error": str(e)}
