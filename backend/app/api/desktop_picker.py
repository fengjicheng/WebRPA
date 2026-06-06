"""
桌面元素选择器API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio

router = APIRouter(prefix="/api/desktop-picker", tags=["desktop-picker"])

# 导入元素选择器服务
from app.services.desktop_element_picker import get_desktop_element_picker

# 存储捕获的元素信息
_captured_element: Optional[Dict[str, Any]] = None
_capture_event = asyncio.Event()
# 保存主事件循环引用，供子线程回调使用
_main_loop: Optional[asyncio.AbstractEventLoop] = None


class ElementPickerResponse(BaseModel):
    """元素选择器响应"""
    success: bool
    message: str
    element: Optional[Dict[str, Any]] = None


@router.get("/windows")
async def list_open_windows():
    """枚举当前所有可见的顶层窗口（供配置面板可视化选择窗口标题）"""
    try:
        import win32gui  # type: ignore

        windows: list[Dict[str, Any]] = []

        def _enum(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return
            title = win32gui.GetWindowText(hwnd)
            if not title or not title.strip():
                return
            try:
                cls = win32gui.GetClassName(hwnd)
            except Exception:
                cls = ""
            # 过滤掉一些系统/无意义窗口
            if cls in ("Progman", "WorkerW", "Shell_TrayWnd", "Button"):
                return
            windows.append({"hwnd": hwnd, "title": title.strip(), "class": cls})

        win32gui.EnumWindows(_enum, None)

        # 去重（同标题保留一个）并按标题排序
        seen = set()
        uniq = []
        for w in windows:
            if w["title"] in seen:
                continue
            seen.add(w["title"])
            uniq.append(w)
        uniq.sort(key=lambda x: x["title"].lower())

        return {"success": True, "windows": uniq}
    except ImportError:
        return {"success": False, "error": "需要安装 pywin32", "windows": []}
    except Exception as e:
        return {"success": False, "error": str(e), "windows": []}


@router.post("/start")
async def start_element_picker():
    """启动桌面元素选择器"""
    try:
        global _captured_element, _capture_event, _main_loop
        _captured_element = None
        _capture_event.clear()
        # 在 async 路由中可安全获取当前 running loop
        try:
            _main_loop = asyncio.get_running_loop()
        except RuntimeError:
            _main_loop = None
        
        picker = get_desktop_element_picker()
        
        # 定义回调函数（在子线程中调用）
        def on_element_captured(element_info: Dict[str, Any]):
            global _captured_element
            _captured_element = element_info
            # 通过保存的主循环引用安全唤醒等待者
            if _main_loop is not None:
                try:
                    _main_loop.call_soon_threadsafe(_capture_event.set)
                except Exception as e:
                    print(f"[desktop_picker] 唤醒事件失败: {e}")
        
        picker.start_picking(on_element_captured)
        
        return {
            "success": True,
            "message": "元素选择器已启动，请将鼠标移动到目标元素上，按Ctrl+点击捕获"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动元素选择器失败: {str(e)}")


@router.post("/stop")
async def stop_element_picker():
    """停止桌面元素选择器"""
    try:
        picker = get_desktop_element_picker()
        picker.stop_picking()
        
        return {
            "success": True,
            "message": "元素选择器已停止"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止元素选择器失败: {str(e)}")


@router.get("/captured")
async def get_captured_element():
    """获取捕获的元素信息（轮询接口）"""
    global _captured_element
    
    if _captured_element:
        element = _captured_element
        _captured_element = None  # 清空
        
        # 构建简洁的控件路径
        control_path = ""
        if element.get('selectors'):
            # 优先使用automation_id
            for selector in element['selectors']:
                if selector['type'] == 'automation_id':
                    control_path = f"automation_id:{selector['value']}"
                    break
            
            # 其次使用name_and_type
            if not control_path:
                for selector in element['selectors']:
                    if selector['type'] == 'name_and_type':
                        control_path = f"name:{selector['name']}"
                        break
            
            # 最后使用class_name
            if not control_path:
                for selector in element['selectors']:
                    if selector['type'] == 'class_name':
                        control_path = f"class_name:{selector['class_name']}"
                        break
        
        return ElementPickerResponse(
            success=True,
            message="已获取捕获的元素",
            element={
                "control_type": element.get('control_type', ''),
                "name": element.get('name', ''),
                "automation_id": element.get('automation_id', ''),
                "class_name": element.get('class_name', ''),
                "control_path": control_path,
                "properties": {
                    "is_visible": element.get('is_visible', False),
                    "is_enabled": element.get('is_enabled', False),
                    "rectangle": element.get('rectangle', {}),
                    "selectors": element.get('selectors', [])
                }
            }
        )
    
    return ElementPickerResponse(
        success=False,
        message="暂无捕获的元素"
    )


@router.get("/wait-capture")
async def wait_for_capture(timeout: int = 60):
    """等待元素捕获（长轮询接口）"""
    global _captured_element, _capture_event
    
    try:
        # 等待捕获事件，最多等待timeout秒
        await asyncio.wait_for(_capture_event.wait(), timeout=timeout)
        
        if _captured_element:
            element = _captured_element
            _captured_element = None
            _capture_event.clear()
            
            return ElementPickerResponse(
                success=True,
                message="已捕获元素",
                element=element
            )
        
        return ElementPickerResponse(
            success=False,
            message="未捕获到元素"
        )
        
    except asyncio.TimeoutError:
        return ElementPickerResponse(
            success=False,
            message="等待超时"
        )
