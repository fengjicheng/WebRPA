"""WebRPA小助手 - 主服务层

负责：
- 与 LLM 通信（OpenAI 兼容协议，含 tools / function calling）
- 会话持久化（JSON 文件）
- 编排多轮工具调用
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Optional

import httpx

from app.models.ai_assistant import (
    AssistantConfig,
    ChatMessage,
    ChatSession,
    MessageRole,
    SessionListItem,
    ToolCall,
    ToolCallStatus,
)
from app.services.ai_assistant_knowledge import build_system_prompt
from app.services.ai_assistant_skills import execute_skill, registry as skill_registry


# ---------- 持久化 ----------

def _get_sessions_dir() -> Path:
    folder = Path("backend/data/ai_assistant/sessions")
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _session_path(session_id: str) -> Path:
    # 基础校验，防路径穿越
    if not session_id or "/" in session_id or "\\" in session_id or ".." in session_id:
        raise ValueError(f"非法 session_id: {session_id}")
    return _get_sessions_dir() / f"{session_id}.json"


def load_session(session_id: str) -> ChatSession | None:
    fp = _session_path(session_id)
    if not fp.exists():
        return None
    try:
        return ChatSession(**json.loads(fp.read_text(encoding="utf-8")))
    except Exception as e:
        print(f"[AIAssistant] 加载会话失败 {session_id}: {e}")
        return None


def save_session(session: ChatSession) -> None:
    fp = _session_path(session.id)
    session.updated_at = datetime.now()
    fp.write_text(
        json.dumps(session.model_dump(), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def list_sessions() -> list[SessionListItem]:
    items: list[SessionListItem] = []
    for fp in _get_sessions_dir().glob("*.json"):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            messages = data.get("messages", [])
            last_text = ""
            if messages:
                # 找最后一条非空文本
                for m in reversed(messages):
                    content = m.get("content", "")
                    if content:
                        last_text = content[:80]
                        break
            items.append(SessionListItem(
                id=data.get("id"),
                title=data.get("title", "新对话"),
                message_count=len(messages),
                updated_at=data.get("updated_at") or data.get("created_at"),
                last_message_preview=last_text,
            ))
        except Exception:
            pass
    items.sort(key=lambda x: x.updated_at, reverse=True)
    return items


def create_session(title: str | None = None) -> ChatSession:
    session = ChatSession(
        id=uuid.uuid4().hex[:12],
        title=title or "新对话",
    )
    save_session(session)
    return session


def delete_session(session_id: str) -> bool:
    fp = _session_path(session_id)
    if not fp.exists():
        return False
    try:
        fp.unlink()
        return True
    except Exception:
        return False


# ---------- LLM 调用 ----------

class LLMError(Exception):
    pass


def _normalize_api_url(api_url: str) -> str:
    """把可能不带 chat/completions 的 base URL 补全"""
    url = (api_url or "").strip()
    if not url:
        raise LLMError("API 地址不能为空")
    # 用户给的是 https://api.openai.com/v1 这种基础地址时，自动补
    if not url.endswith("/chat/completions"):
        if url.endswith("/v1") or url.endswith("/v1/"):
            url = url.rstrip("/") + "/chat/completions"
        elif url.endswith("/api/paas/v4") or url.endswith("/api/paas/v4/"):
            url = url.rstrip("/") + "/chat/completions"
    return url


def _convert_message_for_llm(msg: ChatMessage) -> dict[str, Any]:
    """把内部 ChatMessage 转换为 OpenAI 协议格式"""
    base: dict[str, Any] = {"role": msg.role.value if isinstance(msg.role, MessageRole) else str(msg.role)}

    if msg.role == MessageRole.TOOL:
        base["tool_call_id"] = msg.tool_call_id or ""
        base["content"] = msg.content or ""
        return base

    if msg.role == MessageRole.ASSISTANT and msg.tool_calls:
        base["content"] = msg.content or None
        base["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                },
            }
            for tc in msg.tool_calls
        ]
        return base

    base["content"] = msg.content or ""
    return base


async def _call_llm(
    *,
    config: AssistantConfig,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """调用 LLM 接口（OpenAI 兼容协议）"""
    if not config.model:
        raise LLMError("模型名称不能为空")

    url = _normalize_api_url(config.api_url)
    body: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "stream": False,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    async with httpx.AsyncClient(timeout=180) as client:
        try:
            resp = await client.post(url, json=body, headers=headers)
        except httpx.TimeoutException:
            raise LLMError("LLM 请求超时（超过 180 秒）")
        except httpx.ConnectError as e:
            raise LLMError(f"无法连接到 LLM 服务: {e}")
        except Exception as e:
            raise LLMError(f"LLM 请求异常: {e}")

    if resp.status_code != 200:
        # 解析错误信息
        try:
            err = resp.json()
            msg = err.get("error", {}).get("message") if isinstance(err.get("error"), dict) else None
            msg = msg or err.get("message") or resp.text
        except Exception:
            msg = resp.text
        raise LLMError(f"LLM 返回 {resp.status_code}: {msg}")

    try:
        return resp.json()
    except Exception as e:
        raise LLMError(f"无法解析 LLM 响应: {e}")


def _parse_assistant_response(data: dict[str, Any]) -> tuple[str, list[ToolCall]]:
    """从 LLM 响应中抽出文本与工具调用"""
    if "choices" not in data or not data["choices"]:
        return "", []
    choice = data["choices"][0]
    msg = choice.get("message", {})
    content = msg.get("content") or ""
    raw_tool_calls = msg.get("tool_calls") or []
    tool_calls: list[ToolCall] = []
    for tc in raw_tool_calls:
        fn = tc.get("function", {})
        args_str = fn.get("arguments") or "{}"
        try:
            args = json.loads(args_str) if isinstance(args_str, str) else args_str
        except json.JSONDecodeError:
            args = {"_raw_arguments": args_str}
        tool_calls.append(ToolCall(
            id=tc.get("id") or uuid.uuid4().hex[:12],
            name=fn.get("name", ""),
            arguments=args,
        ))
    return content, tool_calls


# ---------- 主对话循环 ----------

MAX_TOOL_ROUNDS = 5  # 单次用户消息最多轮工具调用


async def chat_once(
    *,
    session: ChatSession,
    user_message_text: str,
    config: AssistantConfig,
    workflow_context: dict[str, Any] | None = None,
    on_event: Optional[callable] = None,
) -> ChatSession:
    """处理一次用户消息（含多轮工具调用）。

    on_event(event_name, payload)：可选的回调，用于 Socket.IO 推送中间事件
        - "tool_call": 模型决定调用某个工具
        - "tool_result": 工具执行结果
        - "assistant_partial": 中间助手回合
    """

    # 1. 把用户消息追加进会话
    user_msg = ChatMessage(
        id=uuid.uuid4().hex[:12],
        role=MessageRole.USER,
        content=user_message_text,
    )
    session.messages.append(user_msg)

    # 2. 给会话起标题（首次提问时）
    if session.title == "新对话" and len([m for m in session.messages if m.role == MessageRole.USER]) == 1:
        session.title = user_message_text.strip()[:30] or "新对话"

    # 3. 构造系统提示词（每次重新构造，让最新的工作流上下文生效）
    workflow_summary = ""
    if workflow_context:
        try:
            wf_name = workflow_context.get("name") or "未命名工作流"
            node_count = len(workflow_context.get("nodes") or [])
            edge_count = len(workflow_context.get("edges") or [])
            current_id = workflow_context.get("currentExecutionWorkflowId") or workflow_context.get("workflowId") or ""
            workflow_summary = (
                f"- 当前画布：{wf_name}（{node_count} 个节点，{edge_count} 条连线）\n"
                f"- 工作流 ID：{current_id or '（未运行）'}\n"
            )
            # 节点类型摘要（让 AI 知道画布上有哪些模块）
            type_counter: dict[str, int] = {}
            for n in (workflow_context.get("nodes") or []):
                t = n.get("type") or "unknown"
                type_counter[t] = type_counter.get(t, 0) + 1
            if type_counter:
                workflow_summary += "- 节点类型分布：" + ", ".join(
                    f"{t}×{c}" for t, c in sorted(type_counter.items(), key=lambda x: -x[1])[:10]
                )
        except Exception:
            pass

    # 4. 加载长期记忆摘要
    memory_summary = ""
    try:
        from app.services.ai_assistant_skills import _load_memory  # type: ignore
        items = _load_memory()
        if items:
            recent = items[-5:]
            memory_summary = "\n".join(f"- {i.get('content', '')}" for i in recent)
    except Exception:
        pass

    system_text = build_system_prompt(
        user_extra_prompt=config.system_prompt,
        enable_tools=config.enable_tools,
        workflow_summary=workflow_summary,
        memory_summary=memory_summary,
    )

    # 5. 多轮工具调用编排
    tools = skill_registry.to_openai_tools() if config.enable_tools else None

    final_assistant_msg: ChatMessage | None = None

    for round_idx in range(MAX_TOOL_ROUNDS + 1):
        # 拼装发送给 LLM 的 messages
        llm_messages: list[dict[str, Any]] = [{"role": "system", "content": system_text}]
        # 把会话里所有非系统消息按顺序加进去
        for m in session.messages:
            llm_messages.append(_convert_message_for_llm(m))

        try:
            raw = await _call_llm(config=config, messages=llm_messages, tools=tools)
        except LLMError as e:
            err_msg = ChatMessage(
                id=uuid.uuid4().hex[:12],
                role=MessageRole.ASSISTANT,
                content=f"[LLM 调用失败] {e}",
            )
            session.messages.append(err_msg)
            final_assistant_msg = err_msg
            break

        content, tool_calls = _parse_assistant_response(raw)

        # 如果模型给出了工具调用
        if tool_calls and config.enable_tools and round_idx < MAX_TOOL_ROUNDS:
            assistant_msg = ChatMessage(
                id=uuid.uuid4().hex[:12],
                role=MessageRole.ASSISTANT,
                content=content,
                tool_calls=tool_calls,
            )
            session.messages.append(assistant_msg)

            if on_event:
                try:
                    await _maybe_await(on_event("assistant_partial", {
                        "message": assistant_msg.model_dump(mode="json"),
                    }))
                except Exception:
                    pass

            # 执行每个工具调用
            for tc in tool_calls:
                tc.status = ToolCallStatus.RUNNING
                tc.started_at = datetime.now()
                if on_event:
                    try:
                        await _maybe_await(on_event("tool_call", {"tool_call": tc.model_dump(mode="json")}))
                    except Exception:
                        pass
                exec_result = await execute_skill(tc.name, tc.arguments)
                tc.completed_at = datetime.now()
                if exec_result.get("success"):
                    tc.status = ToolCallStatus.SUCCESS
                    tc.result = exec_result.get("result")
                else:
                    tc.status = ToolCallStatus.FAILED
                    tc.error = exec_result.get("error", "未知错误")

                # 把工具结果作为 tool 角色消息加入
                tool_msg = ChatMessage(
                    id=uuid.uuid4().hex[:12],
                    role=MessageRole.TOOL,
                    content=json.dumps(
                        tc.result if tc.status == ToolCallStatus.SUCCESS else {"error": tc.error},
                        ensure_ascii=False,
                        default=str,
                    ),
                    tool_call_id=tc.id,
                )
                session.messages.append(tool_msg)

                if on_event:
                    try:
                        await _maybe_await(on_event("tool_result", {"tool_call": tc.model_dump(mode="json")}))
                    except Exception:
                        pass

            # 进入下一轮，让模型基于工具结果继续输出
            continue

        # 模型给出最终文本回复
        final_assistant_msg = ChatMessage(
            id=uuid.uuid4().hex[:12],
            role=MessageRole.ASSISTANT,
            content=content,
        )
        session.messages.append(final_assistant_msg)
        break

    save_session(session)
    return session


async def _maybe_await(value: Any) -> Any:
    """on_event 回调可能是同步函数，统一兼容"""
    if asyncio.iscoroutine(value):
        return await value
    return value
