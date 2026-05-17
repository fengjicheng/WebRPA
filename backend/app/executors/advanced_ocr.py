"""高级模块执行器 - advanced_ocr"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int, to_float, parse_search_region
import asyncio
import ctypes
import os
import re
import time


def _get_ocr_helpers():
    """延迟导入 OCR 共享单例与结果解析器，避免主程序启动时强依赖 paddleocr"""
    from app.services.paddle_ocr_init import get_ocr_instance, parse_ocr_result
    return get_ocr_instance, parse_ocr_result


@register_executor
class ClickTextExecutor(ModuleExecutor):
    """点击文本模块执行器 - 通过屏幕OCR识别实现鼠标点击指定文本"""

    @property
    def module_type(self) -> str:
        return "click_text"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        target_text = context.resolve_value(config.get('targetText', ''))
        match_mode = config.get('matchMode', 'contains')
        click_button = config.get('clickButton', 'left')
        click_type = config.get('clickType', 'single')
        occurrence = int(config.get('occurrence', 1))
        search_region = config.get('searchRegion', None)
        wait_timeout = int(config.get('waitTimeout', 10))
        result_variable = config.get('resultVariable', '')

        if not target_text:
            return ModuleResult(success=False, error="目标文本不能为空")

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._click_text, target_text, match_mode, click_button,
                click_type, occurrence, search_region, wait_timeout
            )

            if result_variable:
                context.set_variable(result_variable, result)

            if result.get('found'):
                return ModuleResult(
                    success=True,
                    message=f"已点击文本 \"{target_text}\" 位置: ({result['x']}, {result['y']})",
                    data=result
                )
            else:
                return ModuleResult(success=False, error=f"未找到文本: {target_text}")
        except Exception as e:
            return ModuleResult(success=False, error=f"点击文本失败: {str(e)}")

    def _click_text(self, target_text: str, match_mode: str, click_button: str,
                    click_type: str, occurrence: int, search_region: dict,
                    wait_timeout: int) -> dict:
        """执行OCR识别并点击文本"""
        import numpy as np

        try:
            from PIL import ImageGrab
        except ImportError:
            raise ImportError("请安装 Pillow: pip install Pillow")

        try:
            get_ocr_instance, parse_ocr_result = _get_ocr_helpers()
            ocr = get_ocr_instance('ch')
        except ImportError:
            raise ImportError("请安装 paddleocr: pip install paddleocr")

        start_time = time.time()
        loop_count = 0

        while time.time() - start_time < wait_timeout:
            loop_count += 1
            region_x, region_y, region_w, region_h = parse_search_region(search_region)
            if region_w > 0 and region_h > 0:
                screenshot = ImageGrab.grab(bbox=(region_x, region_y, region_x + region_w, region_y + region_h))
                offset_x, offset_y = region_x, region_y
            else:
                screenshot = ImageGrab.grab()
                offset_x, offset_y = 0, 0

            img_array = np.array(screenshot)

            try:
                raw = ocr.predict(img_array)
                items = parse_ocr_result(raw)
            except Exception as e:
                print(f"[点击文本] OCR识别失败: {e}")
                time.sleep(0.3)
                continue

            if not items:
                time.sleep(0.3)
                continue

            matches = []
            for box, recognized_text, confidence in items:
                if not recognized_text or box is None:
                    continue

                is_match = False
                if match_mode == 'exact':
                    is_match = recognized_text == target_text
                elif match_mode == 'contains':
                    is_match = target_text in recognized_text
                elif match_mode == 'regex':
                    try:
                        is_match = bool(re.search(target_text, recognized_text))
                    except Exception:
                        is_match = False

                if is_match:
                    try:
                        x1 = int(min(p[0] for p in box))
                        y1 = int(min(p[1] for p in box))
                        x2 = int(max(p[0] for p in box))
                        y2 = int(max(p[1] for p in box))
                    except Exception:
                        continue

                    center_x = (x1 + x2) // 2 + offset_x
                    center_y = (y1 + y2) // 2 + offset_y
                    matches.append({
                        'text': recognized_text,
                        'x': center_x,
                        'y': center_y,
                        'box': [x1 + offset_x, y1 + offset_y, x2 + offset_x, y2 + offset_y],
                        'confidence': confidence
                    })

            if len(matches) >= occurrence:
                match = matches[occurrence - 1]
                self._perform_click(match['x'], match['y'], click_button, click_type)
                return {
                    'found': True,
                    'text': match['text'],
                    'x': match['x'],
                    'y': match['y'],
                    'box': match['box'],
                    'total_matches': len(matches)
                }

            time.sleep(0.3)

        return {'found': False, 'text': target_text}

    def _perform_click(self, x: int, y: int, button: str, click_type: str):
        """执行鼠标点击"""
        user32 = ctypes.windll.user32

        user32.SetCursorPos(x, y)
        time.sleep(0.05)

        MOUSEEVENTF_LEFTDOWN = 0x0002
        MOUSEEVENTF_LEFTUP = 0x0004
        MOUSEEVENTF_RIGHTDOWN = 0x0008
        MOUSEEVENTF_RIGHTUP = 0x0010
        MOUSEEVENTF_MIDDLEDOWN = 0x0020
        MOUSEEVENTF_MIDDLEUP = 0x0040

        if button == 'left':
            down_event = MOUSEEVENTF_LEFTDOWN
            up_event = MOUSEEVENTF_LEFTUP
        elif button == 'right':
            down_event = MOUSEEVENTF_RIGHTDOWN
            up_event = MOUSEEVENTF_RIGHTUP
        else:
            down_event = MOUSEEVENTF_MIDDLEDOWN
            up_event = MOUSEEVENTF_MIDDLEUP

        clicks = 2 if click_type == 'double' else 1
        for _ in range(clicks):
            user32.mouse_event(down_event, 0, 0, 0, 0)
            time.sleep(0.02)
            user32.mouse_event(up_event, 0, 0, 0, 0)
            if click_type == 'double':
                time.sleep(0.05)


@register_executor
class HoverTextExecutor(ModuleExecutor):
    """鼠标悬停在文本上模块执行器 - 通过屏幕OCR识别实现鼠标悬停在指定文本上"""

    @property
    def module_type(self) -> str:
        return "hover_text"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        target_text = context.resolve_value(config.get('targetText', ''))
        match_mode = config.get('matchMode', 'contains')
        hover_duration = to_int(config.get('hoverDuration', 500), 500, context)
        occurrence = int(config.get('occurrence', 1))
        search_region = config.get('searchRegion', None)
        wait_timeout = int(config.get('waitTimeout', 10))
        result_variable = config.get('resultVariable', '')

        if not target_text:
            return ModuleResult(success=False, error="目标文本不能为空")

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._hover_text, target_text, match_mode, hover_duration,
                occurrence, search_region, wait_timeout
            )

            if result_variable:
                context.set_variable(result_variable, result)

            if result.get('found'):
                return ModuleResult(
                    success=True,
                    message=f"已在文本 \"{target_text}\" 位置 ({result['x']}, {result['y']}) 悬停 {hover_duration}ms",
                    data=result
                )
            else:
                return ModuleResult(success=False, error=f"未找到文本: {target_text}")
        except Exception as e:
            return ModuleResult(success=False, error=f"悬停文本失败: {str(e)}")

    def _hover_text(self, target_text: str, match_mode: str, hover_duration: int,
                    occurrence: int, search_region: dict, wait_timeout: int) -> dict:
        """执行OCR识别并悬停在文本上"""
        import numpy as np

        try:
            from PIL import ImageGrab
        except ImportError:
            raise ImportError("请安装 Pillow: pip install Pillow")

        try:
            get_ocr_instance, parse_ocr_result = _get_ocr_helpers()
            ocr = get_ocr_instance('ch')
        except ImportError:
            raise ImportError("请安装 paddleocr: pip install paddleocr")

        start_time = time.time()
        first_loop = True

        while time.time() - start_time < wait_timeout:
            region_x, region_y, region_w, region_h = parse_search_region(search_region)

            if first_loop:
                print(f"[悬停文本] 解析后区域: x={region_x}, y={region_y}, w={region_w}, h={region_h}")
                first_loop = False

            if region_w > 0 and region_h > 0:
                bbox = (region_x, region_y, region_x + region_w, region_y + region_h)
                screenshot = ImageGrab.grab(bbox=bbox)
                offset_x, offset_y = region_x, region_y
            else:
                screenshot = ImageGrab.grab()
                offset_x, offset_y = 0, 0

            img_array = np.array(screenshot)

            try:
                raw = ocr.predict(img_array)
                items = parse_ocr_result(raw)
            except Exception as e:
                print(f"[悬停文本] OCR识别失败: {e}")
                time.sleep(0.3)
                continue

            if not items:
                time.sleep(0.3)
                continue

            matches = []
            for box, recognized_text, confidence in items:
                if not recognized_text or box is None:
                    continue

                is_match = False
                if match_mode == 'exact':
                    is_match = recognized_text == target_text
                elif match_mode == 'contains':
                    is_match = target_text in recognized_text
                elif match_mode == 'regex':
                    try:
                        is_match = bool(re.search(target_text, recognized_text))
                    except Exception:
                        is_match = False

                if is_match:
                    try:
                        x1 = int(min(p[0] for p in box))
                        y1 = int(min(p[1] for p in box))
                        x2 = int(max(p[0] for p in box))
                        y2 = int(max(p[1] for p in box))
                    except Exception:
                        continue

                    center_x = (x1 + x2) // 2 + offset_x
                    center_y = (y1 + y2) // 2 + offset_y
                    matches.append({
                        'text': recognized_text,
                        'x': center_x,
                        'y': center_y,
                        'box': [x1 + offset_x, y1 + offset_y, x2 + offset_x, y2 + offset_y],
                        'confidence': confidence
                    })

            if len(matches) >= occurrence:
                match = matches[occurrence - 1]

                user32 = ctypes.windll.user32
                user32.SetCursorPos(match['x'], match['y'])
                time.sleep(hover_duration / 1000)

                return {
                    'found': True,
                    'text': match['text'],
                    'x': match['x'],
                    'y': match['y'],
                    'box': match['box'],
                    'total_matches': len(matches)
                }

            time.sleep(0.3)

        return {'found': False, 'text': target_text}
