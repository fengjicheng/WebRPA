"""元素选择器API路由 - 直接使用 browser_engine（主进程异步 Playwright）"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.element_picker.selector import SelectorGenerator

router = APIRouter(prefix="/api/element-picker", tags=["element-picker"])


class StartPickerRequest(BaseModel):
    url: Optional[str] = None
    browserConfig: Optional[dict] = None


@router.post("/start")
async def api_start_picker(request: StartPickerRequest):
    """启动元素选择器 - 使用全局浏览器，支持复用"""
    from app.services import browser_engine
    from app.services.browser_manager import _start_picker_engine

    url = request.url.strip() if request.url else None
    browser_config = request.browserConfig or {}
    browser_type = browser_config.get('type', 'msedge')
    executable_path = browser_config.get('executablePath') or None
    fullscreen = browser_config.get('fullscreen', False)
    launch_args = browser_config.get('launchArgs') or None

    print(f"[ElementPicker] 启动请求，URL: {url or '(使用当前页面)'}, 浏览器: {browser_type}")

    # 确保浏览器已打开
    if not browser_engine.is_open():
        success, error = await browser_engine.start(
            browser_type=browser_type,
            executable_path=executable_path,
            fullscreen=fullscreen,
            launch_args=launch_args,
        )
        if not success:
            raise HTTPException(status_code=500, detail=f"无法启动浏览器: {error}")

    # 如果提供了 URL
    if url:
        ctx = browser_engine.get_context()
        # 查找已打开的匹配页面
        found = False
        if ctx:
            def norm(u):
                u = u.rstrip('/')
                for prefix in ('https://', 'http://'):
                    if u.startswith(prefix):
                        u = u[len(prefix):]
                return u.lower()

            for i, pg in enumerate(ctx.pages):
                try:
                    if norm(pg.url) == norm(url):
                        await pg.bring_to_front()
                        found = True
                        break
                except:
                    continue

        if not found:
            result = await browser_engine.navigate_to(url)
            if not result.get('success'):
                raise HTTPException(status_code=500, detail=f"导航失败: {result.get('error')}")

    # 启动选择器
    result = await _start_picker_engine()
    if result.get('success'):
        return {"message": "元素选择器已启动", "status": "active"}
    raise HTTPException(status_code=500, detail=result.get('error', '启动失败'))


@router.post("/stop")
async def api_stop_picker():
    """停止元素选择器"""
    from app.services.browser_manager import _stop_picker_engine
    await _stop_picker_engine()
    return {"message": "元素选择器已停止", "status": "inactive"}


@router.get("/selected")
async def api_get_selected():
    """获取选中的元素"""
    from app.services import browser_engine
    from app.services.browser_manager import _get_picker_result, is_picker_active
    if not browser_engine.is_open():
        return {"selected": False, "active": False}

    result = await _get_picker_result('__elementPickerResult')
    if result.get('success'):
        data = result.get('data')
        if data:
            best_selector = (SelectorGenerator.generate_selector(data)
                             if hasattr(SelectorGenerator, 'generate_selector')
                             else data.get('selector'))
            return {
                "selected": True,
                "active": True,
                "element": {
                    "selector": best_selector,
                    "originalSelector": data.get('selector'),
                    "tagName": data.get('tagName', ''),
                    "text": data.get('text', ''),
                    "attributes": data.get('attributes', {}),
                    "rect": data.get('rect', {}),
                }
            }
        return {"selected": False, "active": is_picker_active()}
    return {"selected": False, "active": False}


@router.get("/similar")
async def api_get_similar():
    """获取相似元素"""
    from app.services import browser_engine
    from app.services.browser_manager import _get_picker_result, is_picker_active
    if not browser_engine.is_open():
        return {"selected": False, "active": False}

    result = await _get_picker_result('__elementPickerSimilar')
    if result.get('success'):
        data = result.get('data')
        if data:
            return {
                "selected": True,
                "active": True,
                "similar": {
                    "pattern": data.get('pattern', ''),
                    "count": data.get('count', 0),
                    "indices": data.get('indices', []),
                    "minIndex": data.get('minIndex', 1),
                    "maxIndex": data.get('maxIndex', 1),
                    "selector1": data.get('selector1', ''),
                    "selector2": data.get('selector2', ''),
                }
            }
        return {"selected": False, "active": is_picker_active()}
    return {"selected": False, "active": False}


@router.get("/status")
async def api_get_status():
    """获取选择器状态"""
    from app.services.browser_manager import is_picker_active
    if is_picker_active():
        return {"status": "active"}
    return {"status": "inactive"}
