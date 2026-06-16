# -*- coding: utf-8 -*-
"""访问鉴权管理 API（仅本机可查看/修改 Token）"""
from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services import security_manager as sec

router = APIRouter(prefix="/api/security", tags=["security"])


def _client_is_local(request: Request) -> bool:
    host = request.client.host if request.client else None
    return sec.is_loopback(host)


class ToggleRequest(BaseModel):
    enabled: bool


@router.get("/status")
async def status(request: Request):
    """鉴权状态：是否启用、当前来源是否本机。Token 仅本机可见。"""
    local = _client_is_local(request)
    return {
        "enabled": sec.is_enabled(),
        "isLocal": local,
        "token": sec.get_token() if local else None,
    }


@router.post("/toggle")
async def toggle(req: ToggleRequest, request: Request):
    """开关鉴权（仅本机可操作）"""
    if not _client_is_local(request):
        return {"success": False, "error": "仅本机可修改鉴权设置"}
    return {"success": True, **sec.set_enabled(req.enabled)}


@router.post("/regenerate")
async def regenerate(request: Request):
    """重置 Token（仅本机可操作）"""
    if not _client_is_local(request):
        return {"success": False, "error": "仅本机可重置 Token"}
    return {"success": True, "token": sec.regenerate_token()}
