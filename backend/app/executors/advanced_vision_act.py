# -*- coding: utf-8 -*-
"""视觉驱动操作（Computer-Use / 看屏点选）

让 AI"看"屏幕截图，根据自然语言描述定位目标，直接在该位置执行真实鼠标操作，
不依赖选择器 / 控件树 —— 对 Canvas、游戏、远程桌面、自定义渲染界面尤其有用。

流程：全屏截图 → 视觉大模型返回归一化坐标(0~1000) → 换算成屏幕物理像素 →
SendInput 真实点击 / 移动；也可仅定位把坐标存入变量。
"""
import base64
import json
import re

import httpx

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int

# 复用真实鼠标点击的 SendInput 基础设施
try:
    from .advanced_mouse import (
        _SENDINPUT_AVAILABLE, _set_dpi_aware, _send_mouse_event,
        _BUTTON_EVENTS, _user32,
    )
except Exception:
    _SENDINPUT_AVAILABLE = False
    def _set_dpi_aware():
        return None
    def _send_mouse_event(*_a, **_k):
        return None
    _BUTTON_EVENTS = {}
    _user32 = None


def _normalize_chat_url(api_url: str) -> str:
    url = (api_url or "").strip()
    if not url:
        return url
    if "/chat/completions" in url or "/completions" in url:
        return url
    url = url.rstrip("/")
    if not url.endswith("/v1") and "/v1/" not in url:
        return url + "/v1/chat/completions"
    return url + "/chat/completions"


def _grab_screen_b64():
    """全屏截图，返回 (base64, width, height)。优先 mss，其次 PIL.ImageGrab。"""
    _set_dpi_aware()
    # 优先 mss（更快、支持多屏）
    try:
        import mss
        import mss.tools
        with mss.mss() as sct:
            mon = sct.monitors[1]  # 主显示器
            shot = sct.grab(mon)
            png = mss.tools.to_png(shot.rgb, shot.size)
            return base64.b64encode(png).decode("utf-8"), shot.size[0], shot.size[1]
    except Exception:
        pass
    # 回退 PIL
    try:
        from PIL import ImageGrab
        import io
        img = ImageGrab.grab()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8"), img.width, img.height
    except Exception as e:
        raise RuntimeError(f"屏幕截图失败: {e}")


def _extract_point(text: str):
    """从模型回复里抽取 {found,x,y} （x,y 为 0~1000 归一化）。"""
    if not text:
        return None
    s = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", s)
    if m:
        s = m.group(1).strip()
    data = None
    try:
        data = json.loads(s)
    except Exception:
        i, j = s.find("{"), s.rfind("}")
        if i != -1 and j != -1 and j > i:
            try:
                data = json.loads(s[i:j + 1])
            except Exception:
                data = None
    if isinstance(data, dict):
        return data
    # 兜底：直接找两个数字
    nums = re.findall(r"\d+(?:\.\d+)?", s)
    if len(nums) >= 2:
        return {"found": True, "x": float(nums[0]), "y": float(nums[1])}
    return None


_SYS_PROMPT = (
    "你是一个屏幕视觉定位引擎。用户会给你一张屏幕截图和一个目标描述，"
    "请找到该目标在图中的位置，返回它的中心点坐标。"
    "坐标用 0~1000 的归一化网格表示：左上角 (0,0)，右下角 (1000,1000)。"
    "只输出 JSON：{\"found\": true/false, \"x\": 数字, \"y\": 数字, \"reason\": \"简短说明\"}，"
    "找不到目标时 found 为 false。不要输出任何多余文字、不要用代码块包裹。"
)


@register_executor
class AIVisionActExecutor(ModuleExecutor):
    """视觉点选：截屏 + 视觉模型定位 + 真实鼠标操作（或仅定位）"""

    @property
    def module_type(self) -> str:
        return "ai_vision_act"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        api_url = context.resolve_value(config.get("apiUrl", ""))
        api_key = context.resolve_value(config.get("apiKey", ""))
        model = context.resolve_value(config.get("model", ""))
        instruction = context.resolve_value(config.get("instruction", ""))
        action = (context.resolve_value(config.get("action", "click")) or "click").strip()
        button = (context.resolve_value(config.get("button", "left")) or "left").strip()
        var = config.get("variableName", "") or config.get("resultVariable", "")
        max_tokens = to_int(config.get("maxTokens", 300), 300, context)

        if not api_url:
            return ModuleResult(success=False, error="API地址不能为空（需多模态/视觉模型）")
        if not model:
            return ModuleResult(success=False, error="模型名称不能为空")
        if not instruction or not str(instruction).strip():
            return ModuleResult(success=False, error="请填写要操作的目标描述(instruction)")

        # 1) 截屏
        try:
            img_b64, sw, sh = _grab_screen_b64()
        except Exception as e:
            return ModuleResult(success=False, error=str(e))

        # 2) 调用视觉模型
        url = _normalize_chat_url(api_url)
        content = [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
            {"type": "text", "text": f"目标：{instruction}\n请返回该目标中心点的归一化坐标(0~1000)。"},
        ]
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": _SYS_PROMPT},
                {"role": "user", "content": content},
            ],
            "max_tokens": max_tokens,
        }
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, json=body, headers=headers)
            if resp.status_code != 200:
                msg = resp.text
                try:
                    ed = resp.json()
                    if "error" in ed:
                        msg = ed["error"].get("message", msg)
                except Exception:
                    pass
                return ModuleResult(success=False, error=f"视觉API请求失败 ({resp.status_code}): {msg}")
            result = resp.json()
            m = (result.get("choices") or [{}])[0].get("message", {}) or {}
            reply = m.get("content") or m.get("reasoning_content") or ""
        except httpx.TimeoutException:
            return ModuleResult(success=False, error="视觉API请求超时")
        except Exception as e:
            return ModuleResult(success=False, error=f"视觉模型调用失败: {e}")

        # 3) 解析坐标
        pt = _extract_point(reply)
        if not pt or pt.get("found") is False:
            reason = (pt or {}).get("reason") if isinstance(pt, dict) else ""
            if var:
                context.set_variable(var, {"found": False, "x": None, "y": None})
            return ModuleResult(success=False, error=f"未在屏幕上定位到目标：{instruction}。{reason or ''}")

        try:
            nx = float(pt.get("x"))
            ny = float(pt.get("y"))
        except (TypeError, ValueError):
            return ModuleResult(success=False, error=f"视觉模型返回坐标无效：{reply[:120]}")

        # 归一化(0~1000) → 屏幕物理像素
        if nx <= 1.5 and ny <= 1.5:           # 兼容 0~1 归一化
            px, py = int(nx * sw), int(ny * sh)
        elif nx <= 1000 and ny <= 1000 and (nx > sw or ny > sh or max(nx, ny) <= 1000):
            px, py = int(nx / 1000.0 * sw), int(ny / 1000.0 * sh)
        else:                                  # 模型直接给了像素坐标
            px, py = int(nx), int(ny)
        px = max(0, min(px, sw - 1))
        py = max(0, min(py, sh - 1))

        if var:
            context.set_variable(var, {"found": True, "x": px, "y": py})

        # 4) 执行操作
        if action == "locate":
            return ModuleResult(success=True, message=f"已定位「{instruction}」→ ({px}, {py})",
                                data={"x": px, "y": py})

        if not _SENDINPUT_AVAILABLE or _user32 is None:
            return ModuleResult(success=False, error="真实鼠标操作仅支持 Windows 系统")

        try:
            _set_dpi_aware()
            _user32.SetCursorPos(px, py)
            import asyncio
            await asyncio.sleep(0.03)
            if action == "move":
                return ModuleResult(success=True, message=f"已移动到「{instruction}」({px}, {py})",
                                    data={"x": px, "y": py})
            btn = "right" if action == "right" else button
            down_event, up_event = _BUTTON_EVENTS.get(btn, _BUTTON_EVENTS.get("left"))
            clicks = 2 if action == "double" else 1
            for _ in range(clicks):
                _send_mouse_event(down_event)
                await asyncio.sleep(0.05)
                _send_mouse_event(up_event)
                if clicks == 2:
                    await asyncio.sleep(0.1)
            act_text = {"double": "双击", "right": "右键单击"}.get(action, "单击")
            return ModuleResult(success=True, message=f"已在「{instruction}」({px}, {py}) {act_text}",
                                data={"x": px, "y": py})
        except Exception as e:
            return ModuleResult(success=False, error=f"鼠标操作失败: {e}")
