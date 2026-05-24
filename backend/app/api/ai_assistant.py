"""WebRPA小助手 - HTTP API"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.ai_assistant import (
    ChatRequest,
    ChatResponse,
    CreateSessionRequest,
    SessionListItem,
)
from app.services.ai_assistant_service import (
    chat_once,
    create_session,
    delete_session,
    list_sessions,
    load_session,
    save_session,
    cancel_session,
)
from app.services.ai_assistant_skills import registry as skill_registry


router = APIRouter(prefix="/api/ai-assistant", tags=["ai-assistant"])


# Socket.IO 实例（运行时由 main.py 注入）
sio = None


def set_sio(socketio_instance) -> None:
    global sio
    sio = socketio_instance


# ---------- 会话管理 ----------

@router.get("/sessions")
async def api_list_sessions() -> list[SessionListItem]:
    return list_sessions()


@router.post("/sessions")
async def api_create_session(req: CreateSessionRequest):
    session = create_session(req.title)
    return {"session_id": session.id, "title": session.title}


@router.get("/sessions/{session_id}")
async def api_get_session(session_id: str):
    session = load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
    return session


@router.delete("/sessions/{session_id}")
async def api_delete_session(session_id: str):
    ok = delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
    return {"success": True}


class RenameSessionRequest(BaseModel):
    title: str


@router.patch("/sessions/{session_id}/title")
async def api_rename_session(session_id: str, req: RenameSessionRequest):
    session = load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
    session.title = (req.title or "").strip() or session.title
    save_session(session)
    return {"success": True, "title": session.title}


# ---------- 对话 ----------

@router.post("/chat", response_model=ChatResponse)
async def api_chat(req: ChatRequest):
    """一次性对话（非流式）"""
    # 加载或创建会话
    session = None
    if req.session_id:
        session = load_session(req.session_id)
    if session is None:
        session = create_session()

    sid_for_emit = session.id

    async def on_event(event_name: str, payload: dict[str, Any]):
        if sio is None:
            return
        try:
            await sio.emit(f"ai_assistant:{event_name}", {"session_id": sid_for_emit, **payload})
        except Exception as e:
            print(f"[AIAssistant] 推送事件失败 {event_name}: {e}")

    session = await chat_once(
        session=session,
        user_message_text=req.message,
        config=req.config,
        workflow_context=req.workflow_context,
        on_event=on_event,
    )

    # 返回最后一条助手消息
    last_assistant = None
    for m in reversed(session.messages):
        if m.role.value == "assistant" and not m.tool_calls:
            last_assistant = m
            break
    if last_assistant is None:
        # 兜底：返回最后一条
        last_assistant = session.messages[-1] if session.messages else None
    if last_assistant is None:
        raise HTTPException(status_code=500, detail="助手未返回任何消息")

    return ChatResponse(session_id=session.id, message=last_assistant)


@router.post("/sessions/{session_id}/cancel")
async def api_cancel_session(session_id: str):
    """中断当前会话正在跑的对话/工具任务"""
    ok = cancel_session(session_id)
    return {"success": ok, "session_id": session_id}


# ---------- Skills 元数据 ----------

@router.get("/skills")
async def api_list_skills():
    """列出所有可用的 Skills（前端用于渲染调试面板）"""
    return {
        "count": len(skill_registry.names()),
        "skills": [
            {
                "name": s.name,
                "description": s.description,
                "parameters": s.parameters,
                "requires_approval": s.requires_approval,
            }
            for s in skill_registry._skills.values()  # noqa: SLF001
        ],
    }


# ---------- 长期记忆 ----------

@router.get("/memories")
async def api_list_memories():
    from app.services.ai_assistant_skills import _load_memory  # type: ignore
    return {"entries": _load_memory()}


class AddMemoryRequest(BaseModel):
    content: str
    tags: list[str] = []


@router.post("/memories")
async def api_add_memory(req: AddMemoryRequest):
    from app.services.ai_assistant_skills import skill_remember
    return await skill_remember(content=req.content, tags=req.tags)


@router.delete("/memories/{memory_id}")
async def api_delete_memory(memory_id: str):
    from app.services.ai_assistant_skills import skill_forget
    return await skill_forget(memory_id=memory_id)
