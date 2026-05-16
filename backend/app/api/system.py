"""系统相关API路由"""
import subprocess
import sys
import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import json

router = APIRouter(prefix="/api/system", tags=["system"])

# 鼠标拾取器进程
mouse_picker_process = None


class OpenUrlRequest(BaseModel):
    url: str


@router.post("/open-url")
async def open_url(request: OpenUrlRequest):
    """使用系统默认浏览器打开URL"""
    import webbrowser
    try:
        webbrowser.open(request.url)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# 文件/文件夹选择器已移至 system_dialog.py，避免路由冲突


@router.get("/mouse-position")
async def get_mouse_position():
    """获取当前鼠标位置"""
    import ctypes
    
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    
    return {
        "success": True,
        "x": pt.x,
        "y": pt.y
    }


# 设置 socketio 实例的引用
_sio = None

def set_napcat_sio(sio):
    """设置 socketio 实例"""
    global _sio
    _sio = sio


class SaveClipboardImageRequest(BaseModel):
    folder: Optional[str] = None
    filename: Optional[str] = None


@router.post("/save-clipboard-image")
async def save_clipboard_image(request: SaveClipboardImageRequest):
    """保存剪贴板图片到图像资源"""
    try:
        from PIL import ImageGrab
        import hashlib
        from datetime import datetime
        import os
        
        # 获取剪贴板图片
        img = ImageGrab.grabclipboard()
        if img is None:
            return {"success": False, "error": "剪贴板中没有图片"}
        
        # 确定保存路径
        base_dir = Path("backend/backend/data/image_assets")
        if request.folder:
            save_dir = base_dir / request.folder
        else:
            save_dir = base_dir
        
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        if request.filename:
            filename = request.filename
            if not filename.endswith('.png'):
                filename += '.png'
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"clipboard_{timestamp}.png"
        
        save_path = save_dir / filename
        
        # 保存图片
        img.save(str(save_path), 'PNG')
        
        # 返回相对路径
        relative_path = str(save_path.relative_to(base_dir))
        
        return {
            "success": True,
            "path": str(save_path),
            "relativePath": relative_path,
            "filename": filename
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}
