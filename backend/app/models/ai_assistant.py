"""WebRPA小助手 - 数据模型"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCallStatus(str, Enum):
    """工具调用状态"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 执行中
    SUCCESS = "success"      # 成功
    FAILED = "failed"        # 失败
    REJECTED = "rejected"    # 用户拒绝


class ToolCall(BaseModel):
    """工具调用记录"""
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    status: ToolCallStatus = ToolCallStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ChatMessage(BaseModel):
    """聊天消息"""
    id: str
    role: MessageRole
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_call_id: Optional[str] = None  # 当 role=tool 时指向源调用
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatSession(BaseModel):
    """会话"""
    id: str
    title: str = "新对话"
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    # 上次会话的简短总结（用作长期记忆的轻量上下文）
    summary: Optional[str] = None


class AssistantConfig(BaseModel):
    """助手配置（前端发来的，每次请求随路携带）"""
    api_url: str = ""
    api_key: str = ""
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 4000
    system_prompt: str = ""           # 用户自定义追加的系统提示词（可空）
    enable_tools: bool = True         # 是否启用工具调用（Skills）
    auto_approve: bool = False        # 是否自动通过工具调用（无需用户确认）


class ChatRequest(BaseModel):
    """对话请求"""
    session_id: Optional[str] = None
    message: str
    config: AssistantConfig
    # 前端可选地附带当前工作流状态作为上下文
    workflow_context: Optional[dict[str, Any]] = None


class ChatResponse(BaseModel):
    """对话响应（非流式）"""
    session_id: str
    message: ChatMessage


class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    title: Optional[str] = None


class SessionListItem(BaseModel):
    """会话列表项"""
    id: str
    title: str
    message_count: int = 0
    updated_at: datetime
    last_message_preview: str = ""


class MemoryEntry(BaseModel):
    """长期记忆条目"""
    id: str
    content: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class ToolApprovalRequest(BaseModel):
    """工具调用审批请求（用户在 supervised 模式下手动批准）"""
    session_id: str
    tool_call_id: str
    approved: bool
    revised_arguments: Optional[dict[str, Any]] = None
