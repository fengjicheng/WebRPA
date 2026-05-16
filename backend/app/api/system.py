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


# 注：/open-url 已移至 system_dialog.py，避免路由冲突
# 注：/mouse-position 已移至 system_mouse.py，避免路由冲突


class ScreenshotToolRequest(BaseModel):
    """截图工具请求"""
    saveToAssets: bool = True
    folder: Optional[str] = None


@router.post("/screenshot-tool")
async def screenshot_tool(request: ScreenshotToolRequest):
    """启动系统截图工具（Win+Shift+S），等待用户截图后保存"""
    try:
        from app.services.screenshot_tool_v2 import screenshot_tool_handler
        result = await screenshot_tool_handler(request.model_dump())
        return result
    except Exception as e:
        return {"success": False, "error": f"截图工具启动失败: {e}"}


@router.post("/screenshot")
async def screenshot_screen():
    """直接对当前屏幕进行截图（不需要用户交互）"""
    import tempfile
    import os
    from datetime import datetime
    try:
        from PIL import ImageGrab
    except ImportError:
        return {"success": False, "error": "缺少 Pillow 依赖（pip install Pillow）"}
    
    try:
        # 截取整个屏幕
        loop = asyncio.get_running_loop()
        img = await loop.run_in_executor(None, ImageGrab.grab)
        if img is None:
            return {"success": False, "error": "截屏失败，未获取到图像"}
        
        # 保存到 image_assets
        image_assets_dir = Path(__file__).parent.parent.parent / "uploads" / "images"
        image_assets_dir.mkdir(parents=True, exist_ok=True)
        
        import uuid
        asset_id = str(uuid.uuid4())
        save_path = image_assets_dir / f"{asset_id}.png"
        await loop.run_in_executor(None, lambda: img.save(str(save_path), 'PNG'))
        
        file_name = f"screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        file_size = save_path.stat().st_size
        
        # 注册资产
        from app.api.image_assets import image_assets
        image_assets[asset_id] = {
            "id": asset_id,
            "name": f"{asset_id}.png",
            "originalName": file_name,
            "size": file_size,
            "uploadedAt": datetime.now().isoformat(),
            "folder": "",
            "extension": ".png",
            "path": str(save_path),
        }
        
        return {
            "success": True,
            "assetId": asset_id,
            "fileName": file_name,
            "width": img.width,
            "height": img.height,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": f"截屏失败: {e}"}


# 设置 socketio 实例的引用（保留旧名以兼容历史导入）
_sio = None


def set_napcat_sio(sio):
    """[已废弃] 旧的 sio 注入入口，保留兼容性。
    
    实际的 napcat 事件由 system_napcat.py 中的 set_napcat_sio 接管。
    """
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
