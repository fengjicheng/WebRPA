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
async def api_start_picker(request: StartPickerRequest | None = None):
    """启动元素选择器 - 使用全局浏览器，支持复用"""
    from app.services import browser_engine
    from app.services.browser_manager import _start_picker_engine

    if request is None:
        request = StartPickerRequest()
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
                except Exception:
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


class TestSelectorRequest(BaseModel):
    selector: str
    hints: Optional[dict] = None
    highlight: bool = True


# 在页面上高亮一组矩形框（2.5 秒后自动消失），用于"测试定位"可视化反馈
_OVERLAY_JS = """
(boxes) => {
  try {
    const id = '__webrpa_selector_test_overlay__';
    document.getElementById(id)?.remove();
    const layer = document.createElement('div');
    layer.id = id;
    layer.style.cssText = 'position:fixed;left:0;top:0;width:0;height:0;z-index:2147483647;pointer-events:none;';
    boxes.forEach((b, i) => {
      const d = document.createElement('div');
      d.style.cssText = 'position:fixed;border:2px solid #ef4444;background:rgba(239,68,68,0.15);box-shadow:0 0 0 1px rgba(255,255,255,0.6);pointer-events:none;border-radius:2px;transition:opacity .3s;';
      d.style.left = b.x + 'px';
      d.style.top = b.y + 'px';
      d.style.width = b.width + 'px';
      d.style.height = b.height + 'px';
      if (i === 0) {
        const tag = document.createElement('div');
        tag.textContent = '匹配 ' + boxes.length + ' 个';
        tag.style.cssText = 'position:absolute;left:0;top:-20px;background:#ef4444;color:#fff;font:12px sans-serif;padding:1px 6px;border-radius:3px;white-space:nowrap;';
        d.appendChild(tag);
      }
      layer.appendChild(d);
    });
    document.documentElement.appendChild(layer);
    setTimeout(() => { layer.style.transition='opacity .4s'; layer.style.opacity='0'; setTimeout(()=>layer.remove(), 400); }, 2500);
  } catch (e) {}
}
"""


@router.post("/test-selector")
async def api_test_selector(req: TestSelectorRequest):
    """在当前浏览器页面上测试选择器是否命中元素，并高亮匹配项。

    - 先测主选择器；命中失败时若提供 hints，则尝试自愈候选选择器。
    - 返回命中数量、命中所用选择器、首个元素信息，并在页面上高亮匹配框。
    """
    from app.services import browser_engine

    if not browser_engine.is_open():
        return {"success": False, "error": "浏览器未打开，请先启动浏览器或元素拾取后再测试"}
    page = browser_engine.get_page()
    if page is None:
        return {"success": False, "error": "没有可用的页面"}

    selector = (req.selector or "").strip()
    if not selector:
        return {"success": False, "error": "选择器为空"}

    candidates = [selector]
    if req.hints:
        try:
            from app.executors.base import build_fallback_selectors
            for c in build_fallback_selectors(req.hints):
                if c not in candidates:
                    candidates.append(c)
        except Exception:
            pass

    tried = []
    for cand in candidates:
        try:
            loc = page.locator(cand)
            count = await loc.count()
        except Exception as e:
            tried.append({"selector": cand, "error": str(e)[:160]})
            continue
        tried.append({"selector": cand, "count": count})
        if count > 0:
            # 收集首个元素信息
            element = {}
            try:
                first = loc.first
                tag = await first.evaluate("e => e.tagName ? e.tagName.toLowerCase() : ''")
                try:
                    text = (await first.inner_text(timeout=1500)) or ""
                except Exception:
                    text = ""
                element = {"tag": tag, "text": text.strip()[:120]}
            except Exception:
                pass
            # 高亮
            if req.highlight:
                try:
                    boxes = []
                    for i in range(min(count, 30)):
                        try:
                            b = await loc.nth(i).bounding_box()
                            if b:
                                boxes.append(b)
                        except Exception:
                            pass
                    if boxes:
                        await page.evaluate(_OVERLAY_JS, boxes)
                except Exception:
                    pass
            return {
                "success": True,
                "matched": True,
                "count": count,
                "matchedSelector": cand,
                "isPrimary": cand == selector,
                "element": element,
                "tried": tried,
            }

    return {"success": True, "matched": False, "count": 0, "tried": tried}
