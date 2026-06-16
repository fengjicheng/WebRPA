# -*- coding: utf-8 -*-
"""网页智能录制器 API"""
from fastapi import APIRouter

from app.services import recorder as rec
from app.services import browser_engine

router = APIRouter(prefix="/api/recorder", tags=["recorder"])


@router.post("/start")
async def api_start_recorder():
    """开始录制（需先打开浏览器）"""
    if not browser_engine.is_open():
        return {"success": False, "error": "浏览器未打开，请先打开网页或自动化浏览器"}
    return await rec.start_recorder()


@router.post("/stop")
async def api_stop_recorder():
    """停止录制并返回剩余事件"""
    return await rec.stop_recorder()


@router.get("/events")
async def api_drain_events():
    """轮询排空已录制事件"""
    if not browser_engine.is_open():
        return {"success": True, "data": []}
    return await rec.drain_recorder_events()


@router.get("/status")
async def api_recorder_status():
    return {"active": rec.is_recorder_active(), "browserOpen": browser_engine.is_open()}
