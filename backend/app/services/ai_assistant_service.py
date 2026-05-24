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

MAX_TOOL_ROUNDS = 8  # 单次用户消息最多轮工具调用（提升以支持复杂任务）

# 上下文压缩阈值：消息总条数超过此值时，自动总结早期消息
CONTEXT_COMPRESSION_THRESHOLD = 50
CONTEXT_KEEP_RECENT = 20  # 压缩时保留最近多少条消息

# 会话级"取消令牌"——用户在 AI 工作期间发新消息时，旧任务会读到这个 token 然后立刻退出
_cancel_tokens: dict[str, asyncio.Event] = {}


def cancel_session(session_id: str) -> bool:
    """中断指定会话当前正在跑的对话/工具任务"""
    ev = _cancel_tokens.get(session_id)
    if ev is None:
        return False
    ev.set()
    return True


def _get_or_create_cancel_token(session_id: str) -> asyncio.Event:
    ev = _cancel_tokens.get(session_id)
    if ev is None or ev.is_set():
        ev = asyncio.Event()
        _cancel_tokens[session_id] = ev
    return ev


def _release_cancel_token(session_id: str) -> None:
    _cancel_tokens.pop(session_id, None)


class _Cancelled(Exception):
    """内部信号：当前会话被取消"""


def _check_cancel(token: asyncio.Event) -> None:
    if token.is_set():
        raise _Cancelled()


async def _maybe_compress_messages(
    session: ChatSession,
    *,
    config: AssistantConfig,
) -> None:
    """会话超长时自动压缩：把早期消息合并成一个 system 摘要消息

    策略：
    - 总消息数超 CONTEXT_COMPRESSION_THRESHOLD
    - 保留最后 CONTEXT_KEEP_RECENT 条消息
    - 把更早的消息（不含 system）调用 LLM 摘要成一段文字，存为伪 system 消息
    - 失败时退化为：拼接前 N 条文本截短作为摘要
    """
    if len(session.messages) <= CONTEXT_COMPRESSION_THRESHOLD:
        return

    keep_count = CONTEXT_KEEP_RECENT
    older_msgs = session.messages[:-keep_count] if keep_count > 0 else session.messages[:]
    recent_msgs = session.messages[-keep_count:] if keep_count > 0 else []

    # 已经压缩过一次的话，会话第一条会是我们注入的 ASSISTANT_SUMMARY；继续往前合并
    summary_text_parts: list[str] = []
    raw_lines: list[str] = []
    for m in older_msgs:
        role = m.role.value if hasattr(m.role, "value") else str(m.role)
        if role == "tool":
            raw_lines.append(f"[工具结果] {(m.content or '')[:240]}")
        elif role == "assistant":
            if m.tool_calls:
                tnames = ", ".join(tc.name for tc in m.tool_calls)
                raw_lines.append(f"[助手调用] {tnames}")
            if m.content:
                raw_lines.append(f"[助手] {m.content[:240]}")
        elif role == "user":
            raw_lines.append(f"[用户] {(m.content or '')[:240]}")
        elif role == "system":
            # 历史 system 摘要直接保留进新摘要里
            summary_text_parts.append(m.content or "")

    # 限制原始日志长度
    raw_text = "\n".join(raw_lines)
    if len(raw_text) > 8000:
        raw_text = raw_text[:4000] + "\n…（中间内容已省略）…\n" + raw_text[-3000:]

    summary_prompt = (
        "下面是一段 WebRPA 小助手与用户之间的较早对话摘录（包含用户提问、助手回答、工具调用与结果）。\n"
        "请用中文产出一份 200~400 字的精炼摘要，提取出：\n"
        "1) 用户的核心目标与重要偏好\n"
        "2) 已经达成的关键事实（搭建过哪些工作流、改过哪些配置等）\n"
        "3) 未完成或被中断的事项\n"
        "4) 对后续对话有用的上下文\n"
        "不要复述工具名，只保留有意义的实质信息。\n\n"
        f"对话内容：\n{raw_text}"
    )

    summary = ""
    try:
        if config.api_url and config.model:
            # 用同一个模型做摘要，但单独请求，控制开销
            data = await _call_llm(
                config=config,
                messages=[
                    {"role": "system", "content": "你是一个善于总结对话上下文的助手。"},
                    {"role": "user", "content": summary_prompt},
                ],
                tools=None,
            )
            summary, _ = _parse_assistant_response(data)
    except Exception as e:
        print(f"[AIAssistant] 自动压缩 LLM 摘要失败：{e}")

    if not summary:
        # 退化方案：直接截短拼接
        summary = "（自动摘要失败，回退原始截断）\n" + raw_text[:1500]

    # 拼装新 history
    parts = []
    parts.extend(summary_text_parts)
    parts.append("【上下文自动摘要】\n" + summary)
    merged_summary = "\n\n".join(p for p in parts if p)

    summary_msg = ChatMessage(
        id=uuid.uuid4().hex[:12],
        role=MessageRole.SYSTEM,
        content=merged_summary,
    )
    session.messages = [summary_msg] + recent_msgs
    print(f"[AIAssistant] 已自动压缩上下文：{len(older_msgs)} 条 → 1 条摘要，保留最近 {len(recent_msgs)} 条")


async def _auto_remember_if_needed(
    user_message: str,
    *,
    config: AssistantConfig,
) -> None:
    """检测用户消息中是否包含明显的偏好/约定，自动写入长期记忆。

    通过简单关键词触发：包含"记住/我习惯/我喜欢/我项目/请记得"等。
    避免把每条普通消息都塞进记忆。
    """
    text = (user_message or "").strip()
    if not text or len(text) < 4:
        return

    triggers = ("记住", "记得", "记一下", "请记住", "我习惯", "我喜欢", "我的项目", "以后都", "之后都", "默认用", "默认使用", "我偏好")
    if not any(t in text for t in triggers):
        return

    try:
        from app.services.ai_assistant_skills import skill_remember
        await skill_remember(content=text[:500], tags=["auto"])
        print(f"[AIAssistant] 自动写入记忆: {text[:50]}…")
    except Exception as e:
        print(f"[AIAssistant] 自动记忆失败：{e}")


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

    # 0. 注册取消令牌（同会话再次调用时旧任务可被取消）
    cancel_token = _get_or_create_cancel_token(session.id)

    # 0b. 自动写入用户偏好（异步，不阻塞主流程）
    try:
        asyncio.create_task(_auto_remember_if_needed(user_message_text, config=config))
    except Exception:
        pass

    # 1. 把用户消息追加进会话
    user_msg = ChatMessage(
        id=uuid.uuid4().hex[:12],
        role=MessageRole.USER,
        content=user_message_text,
    )
    session.messages.append(user_msg)

    # 2. 给会话起标题（首次提问时，自动从问题生成简短标题）
    user_message_count = sum(1 for m in session.messages if m.role == MessageRole.USER)
    if user_message_count == 1 and (session.title in ("", "新对话") or not session.title):
        # 简单清洗：截 26 字符内、剔除换行
        title = user_message_text.strip().split("\n")[0]
        if len(title) > 26:
            title = title[:26] + "…"
        session.title = title or "新对话"

    # 2b. 上下文自动压缩（消息过长时合并早期消息为摘要）
    try:
        await _maybe_compress_messages(session, config=config)
    except Exception as e:
        print(f"[AIAssistant] 自动压缩失败：{e}")

    # 3. 构造系统提示词（每次重新构造，让最新的工作流上下文生效）
    workflow_summary = ""
    if workflow_context:
        try:
            wf_name = workflow_context.get("name") or "未命名工作流"
            nodes = workflow_context.get("nodes") or []
            edges = workflow_context.get("edges") or []
            current_id = (
                workflow_context.get("currentExecutionWorkflowId")
                or workflow_context.get("workflowId")
                or ""
            )
            variables = workflow_context.get("variables") or []

            workflow_summary = (
                f"- 当前画布：{wf_name}（{len(nodes)} 个节点，{len(edges)} 条连线）\n"
                f"- 工作流 ID：{current_id or '（未保存或未运行）'}\n"
            )

            # 节点类型分布
            type_counter: dict[str, int] = {}
            for n in nodes:
                t = n.get("type") or "unknown"
                type_counter[t] = type_counter.get(t, 0) + 1
            if type_counter:
                top_types = sorted(type_counter.items(), key=lambda x: -x[1])[:12]
                workflow_summary += "- 节点类型分布：" + ", ".join(
                    f"{t}×{c}" for t, c in top_types
                ) + "\n"

            # 节点 ID 与 label 映射（让 LLM 能精确引用节点）
            if 0 < len(nodes) <= 50:
                workflow_summary += "- 节点清单（id - type - label）：\n"
                for n in nodes[:50]:
                    nid = n.get("id", "?")
                    nt = n.get("type", "?")
                    label = ""
                    data = n.get("data") or {}
                    if isinstance(data, dict):
                        label = data.get("label") or data.get("customName") or ""
                    workflow_summary += f"  - {nid} - {nt} - {label}\n"

            # 变量
            if variables:
                workflow_summary += f"- 当前变量（{len(variables)} 个）：\n"
                for v in variables[:20]:
                    if isinstance(v, dict):
                        vn = v.get("name", "")
                        vt = v.get("type", "?")
                        workflow_summary += f"  - {vn} ({vt})\n"
        except Exception as e:
            workflow_summary = f"（解析工作流上下文失败：{e}）"

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

    # 4b. 给 system_text 追加可用 client_action 完整列表（让 LLM 不必反复猜测名称）
    if config.enable_tools:
        client_actions_hint = (
            "\n# client_action 速查表（精确名称）\n"
            "工作流：new_workflow / load_workflow / load_workflow_from_data / save_workflow / run_workflow / "
            "run_workflow_headless / stop_workflow / export_workflow / rename_workflow / get_workflow_detail / "
            "get_logs / get_collected_data\n"
            "节点：add_nodes / delete_node / delete_nodes / update_node_config / focus_node / toggle_node_disabled / "
            "align_nodes / copy_nodes / paste_nodes / move_node / rename_node / find_nodes_by_type / "
            "connect_nodes / disconnect_edge / select_all_nodes / clear_selection / fit_view / run_single_node / "
            "undo / redo\n"
            "变量：add_variable / update_variable / delete_variable / rename_variable / list_variables\n"
            "日志/数据：clear_logs / clear_data / set_verbose_log / set_max_log_count / export_logs / download_data / "
            "upload_excel / upload_image / add_log\n"
            "切换/弹窗：switch_bottom_panel(tab=logs|data|variables|assets|images) / "
            "open_global_config / close_global_config / open_local_workflow_dialog / close_local_workflow_dialog / "
            "open_scheduled_tasks / close_scheduled_tasks / open_documentation / close_documentation / "
            "open_workflow_hub / close_workflow_hub / open_auto_browser / close_auto_browser / "
            "open_phone_mirror / close_phone_mirror / open_variable_tracking / close_variable_tracking / "
            "open_export_dialog / open_module_search / take_screenshot\n"
            "全局配置：get_global_config / update_global_config(section=system|ai|aiAssistant|aiScraper|"
            "email|browser|database|qq|feishu|display|workflow, values={...}) / reset_global_config\n"
            "提示：show_toast(message, type)\n"
            "\n# 后端真生效操作（无需前端配合，直接持久化/真触发）\n"
            "计划任务 真生效：create_scheduled_task / update_scheduled_task / delete_scheduled_task / "
            "toggle_scheduled_task / execute_scheduled_task / stop_scheduled_task / clear_scheduled_task_logs / "
            "list_scheduled_tasks / get_scheduled_task / get_scheduled_task_logs\n"
            "自定义模块 真生效：create_custom_module / update_custom_module / delete_custom_module / "
            "list_custom_modules / get_custom_module\n"
            "工作流 真生效：save_local_workflow（持久化文件）/ run_workflow_now（后端立即执行，返回 workflow_id）/ "
            "stop_workflow_now / read_workflow / list_workflows\n"
            "全局变量 真生效：set_global_variable / delete_global_variable / clear_global_variables / "
            "list_global_variables（持久化到 backend/data/global_vars.json）\n"
            "资源 真生效：delete_data_asset / rename_data_asset / delete_image_asset / rename_image_asset\n"
            "系统执行：run_shell_command（PowerShell 等）/ run_python_script（自动用内置 Python313 执行临时脚本后销毁）\n"
            "\n# 真生效 vs 表面功夫：\n"
            "- client_action 大多只影响前端 UI（除变量、资源、运行/导出等是真生效）\n"
            "- 上面「后端真生效」的 skill 直接调用后端服务和 API，会写盘、注册触发器、真启动浏览器等\n"
            "- 用户重启 WebRPA 后，所有「后端真生效」操作的结果仍在\n"
        )
        system_text = system_text + client_actions_hint

    # 5. 多轮工具调用编排
    tools = skill_registry.to_openai_tools() if config.enable_tools else None

    final_assistant_msg: ChatMessage | None = None

    try:
        for round_idx in range(MAX_TOOL_ROUNDS + 1):
            _check_cancel(cancel_token)

            # 拼装发送给 LLM 的 messages
            llm_messages: list[dict[str, Any]] = [{"role": "system", "content": system_text}]
            for m in session.messages:
                llm_messages.append(_convert_message_for_llm(m))

            # LLM 调用与取消监听同时跑
            try:
                llm_task = asyncio.create_task(_call_llm(config=config, messages=llm_messages, tools=tools))
                cancel_wait = asyncio.create_task(cancel_token.wait())
                done, pending = await asyncio.wait(
                    {llm_task, cancel_wait}, return_when=asyncio.FIRST_COMPLETED
                )
                if cancel_wait in done and llm_task not in done:
                    llm_task.cancel()
                    for p in pending:
                        if p is not llm_task:
                            p.cancel()
                    raise _Cancelled()
                # llm 已先完成
                for p in pending:
                    p.cancel()
                raw = llm_task.result()
            except _Cancelled:
                raise
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

                # ===== 并行执行所有工具调用 =====
                async def run_one_tool(tc: ToolCall) -> ToolCall:
                    tc.status = ToolCallStatus.RUNNING
                    tc.started_at = datetime.now()
                    if on_event:
                        try:
                            await _maybe_await(on_event("tool_call", {"tool_call": tc.model_dump(mode="json")}))
                        except Exception:
                            pass
                    try:
                        exec_result = await execute_skill(tc.name, tc.arguments)
                    except Exception as ex:
                        exec_result = {"error": f"工具异常：{ex}"}
                    tc.completed_at = datetime.now()
                    if exec_result.get("success"):
                        tc.status = ToolCallStatus.SUCCESS
                        tc.result = exec_result.get("result")
                    else:
                        tc.status = ToolCallStatus.FAILED
                        tc.error = exec_result.get("error", "未知错误")
                    if on_event:
                        try:
                            await _maybe_await(on_event("tool_result", {"tool_call": tc.model_dump(mode="json")}))
                        except Exception:
                            pass
                    return tc

                tool_tasks = [asyncio.create_task(run_one_tool(tc)) for tc in tool_calls]
                cancel_wait = asyncio.create_task(cancel_token.wait())
                # 等所有工具完成或被取消（不要再 create_task gather，gather 本身就是 awaitable）
                done, pending = await asyncio.wait(
                    set(tool_tasks) | {cancel_wait},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                # 用户取消：把还没跑完的 tool 全部 cancel
                if cancel_wait in done:
                    for t in tool_tasks:
                        if not t.done():
                            t.cancel()
                    raise _Cancelled()
                # 某个 tool 先完成而其他还在跑：继续等剩下的全部完成
                if any(not t.done() for t in tool_tasks):
                    await asyncio.gather(*tool_tasks, return_exceptions=True)
                if not cancel_wait.done():
                    cancel_wait.cancel()

                # 把每条工具的结果消息追加到会话
                for tc in tool_calls:
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

                continue  # 进入下一轮

            # 模型给出最终文本回复
            final_assistant_msg = ChatMessage(
                id=uuid.uuid4().hex[:12],
                role=MessageRole.ASSISTANT,
                content=content,
            )
            session.messages.append(final_assistant_msg)
            break

    except _Cancelled:
        cancel_msg = ChatMessage(
            id=uuid.uuid4().hex[:12],
            role=MessageRole.ASSISTANT,
            content="[已停止] 任务被你打断，未完成的工具调用已取消。",
        )
        session.messages.append(cancel_msg)
        final_assistant_msg = cancel_msg
        if on_event:
            try:
                await _maybe_await(on_event("cancelled", {"reason": "user_cancelled"}))
            except Exception:
                pass
    finally:
        _release_cancel_token(session.id)

    save_session(session)
    return session


async def _maybe_await(value: Any) -> Any:
    """on_event 回调可能是同步函数，统一兼容"""
    if asyncio.iscoroutine(value):
        return await value
    return value
