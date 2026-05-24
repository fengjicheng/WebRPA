"""屏保弹幕 API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

from app.services import screensaver as svc


router = APIRouter(prefix="/api/screensaver", tags=["screensaver"])


class StartScreensaverRequest(BaseModel):
    """前端只要把整个 config dict 传过来即可，字段灵活"""
    config: dict[str, Any] = {}


@router.post("/start")
async def api_start(request: StartScreensaverRequest):
    """启动屏保弹幕（独立进程，全屏覆盖整个桌面）"""
    return svc.start(request.config or {})


@router.post("/stop")
async def api_stop():
    """停止屏保弹幕"""
    return svc.stop()


@router.get("/status")
async def api_status():
    """获取屏保弹幕状态"""
    return svc.status()
