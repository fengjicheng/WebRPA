# -*- coding: utf-8 -*-
"""留存清理 API：查看/修改录像与采集数据的自动清理策略，并支持手动清理。"""
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.services import retention_manager

router = APIRouter(prefix="/api/retention", tags=["retention"])


class RetentionConfig(BaseModel):
    enabled: Optional[bool] = None
    recordings_max_days: Optional[int] = None
    recordings_max_total_mb: Optional[int] = None
    data_max_days: Optional[int] = None
    data_max_total_mb: Optional[int] = None
    cleanup_interval_hours: Optional[int] = None


@router.get("/config")
async def get_config():
    return {"success": True, "config": retention_manager.load_config(), "usage": retention_manager.get_usage()}


@router.post("/config")
async def set_config(req: RetentionConfig):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    conf = retention_manager.save_config(updates)
    return {"success": True, "config": conf}


@router.post("/cleanup")
async def run_cleanup_now():
    """立即手动清理一次（忽略开关）。"""
    return retention_manager.run_cleanup(force=True)


@router.get("/usage")
async def get_usage():
    return {"success": True, "usage": retention_manager.get_usage()}
