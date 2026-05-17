"""手机视觉识别模块执行器 - 图像识别和OCR文本识别"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .phone_utils import ensure_phone_connected
from ..services.adb_manager import get_adb_manager
from .type_utils import to_int, to_float
from pathlib import Path
import asyncio
import tempfile
import time
import os


@register_executor
class PhoneClickImageExecutor(ModuleExecutor):
    """手机点击图像 - 在手机屏幕上识别图像并点击"""
    
    @property
    def module_type(self) -> str:
        return "phone_click_image"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        image_path = context.resolve_value(config.get('imagePath', ''))
        confidence = to_float(config.get('confidence', 0.8), 0.8, context)
        click_position = context.resolve_value(config.get('clickPosition', 'center'))
        click_type = context.resolve_value(config.get('clickType', 'click'))  # click 或 long_press
        wait_timeout = to_int(config.get('waitTimeout', 10), 10, context)
        
        if not image_path:
            return ModuleResult(success=False, error="图像路径不能为空")
        
        if not Path(image_path).exists():
            return ModuleResult(success=False, error=f"图像文件不存在: {image_path}")
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context, config)
        if not success:
            return ModuleResult(success=False, error=error)
        
        try:
            import cv2
            import numpy as np
        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装 opencv-python: pip install opencv-python"
            )
        
        try:
            adb = get_adb_manager()
            
            # 读取模板图像
            template = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if template is None:
                return ModuleResult(success=False, error="无法读取图像文件，请检查图像格式")
            
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            h, w = template_gray.shape
            
            context.log(f"📐 模板图像尺寸: {w}x{h}")
            
            start_time = time.time()
            found = False
            click_x, click_y = 0, 0
            best_confidence = 0
            check_count = 0
            
            # 创建临时目录保存截图
            with tempfile.TemporaryDirectory() as temp_dir:
                screenshot_path = os.path.join(temp_dir, 'phone_screenshot.png')
                
                while time.time() - start_time < wait_timeout:
                    check_count += 1
                    
                    # 截取手机屏幕
                    success, error = adb.screenshot(screenshot_path, device_id)
                    if not success:
                        return ModuleResult(success=False, error=f"截取手机屏幕失败: {error}")
                    
                    # 读取截图
                    screen = cv2.imread(screenshot_path)
                    if screen is None:
                        await asyncio.sleep(0.3)
                        continue
                    
                    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
                    screen_h, screen_w = screen_gray.shape
                    
                    # 第一次循环时输出屏幕尺寸
                    if check_count == 1:
                        context.log(f"📱 手机屏幕截图尺寸: {screen_w}x{screen_h}")
                    
                    # 检查模板是否大于屏幕
                    if w > screen_w or h > screen_h:
                        return ModuleResult(
                            success=False,
                            error=f"❌ 模板图像 ({w}x{h}) 大于手机屏幕 ({screen_w}x{screen_h})，请截取更小的区域作为模板"
                        )
                    
                    # 模板匹配
                    result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    # 更新并输出当前最高匹配度
                    if max_val > best_confidence:
                        best_confidence = max_val
                        context.log(f"🔍 第{check_count}次检测 - 当前最高匹配度: {best_confidence:.2%} (阈值: {confidence:.2%})")
                    
                    if max_val >= confidence:
                        # 找到匹配
                        img_left = max_loc[0]
                        img_top = max_loc[1]
                        img_right = img_left + w
                        img_bottom = img_top + h
                        
                        # 根据点击位置计算坐标
                        click_x, click_y = self._calculate_click_position(
                            click_position, img_left, img_top, img_right, img_bottom, w, h
                        )
                        
                        best_confidence = max_val
                        found = True
                        context.log(f"✅ 找到匹配！位置: ({img_left}, {img_top}), 匹配度: {best_confidence:.2%}")
                        break
                    
                    await asyncio.sleep(0.3)
            
            if not found:
                return ModuleResult(
                    success=False,
                    error=f"❌ 在 {wait_timeout} 秒内未找到匹配的图像（最高匹配度: {best_confidence:.2%}，共检测{check_count}次）\n💡 建议：\n1. 降低置信度阈值（当前{confidence:.2%}）\n2. 确保模板图像是从相同分辨率的手机截取的\n3. 截取更小、更独特的区域作为模板"
                )
            
            # 执行点击
            if click_type == 'long_press':
                success, error = adb.long_press(click_x, click_y, 1000, device_id)
                action_name = "长按"
            else:
                success, error = adb.tap(click_x, click_y, device_id)
                action_name = "点击"
            
            if not success:
                return ModuleResult(success=False, error=error)
            
            position_name = self._get_position_name(click_position)
            return ModuleResult(
                success=True,
                message=f"✅ 已在图像{position_name} ({click_x}, {click_y}) {action_name}，匹配度: {best_confidence:.2%}",
                data={"x": click_x, "y": click_y, "confidence": best_confidence}
            )
            
        except Exception as e:
            return ModuleResult(success=False, error=f"点击图像失败: {str(e)}")
    
    def _calculate_click_position(self, position: str, left: int, top: int, right: int, bottom: int, w: int, h: int) -> tuple:
        """根据点击位置计算实际坐标"""
        import random
        
        if position == "center":
            return (left + w // 2, top + h // 2)
        elif position == "top-left":
            return (left + 5, top + 5)
        elif position == "top-right":
            return (right - 5, top + 5)
        elif position == "bottom-left":
            return (left + 5, bottom - 5)
        elif position == "bottom-right":
            return (right - 5, bottom - 5)
        elif position == "top":
            return (left + w // 2, top + 5)
        elif position == "bottom":
            return (left + w // 2, bottom - 5)
        elif position == "left":
            return (left + 5, top + h // 2)
        elif position == "right":
            return (right - 5, top + h // 2)
        elif position == "random":
            margin = 5
            rand_x = random.randint(left + margin, right - margin)
            rand_y = random.randint(top + margin, bottom - margin)
            return (rand_x, rand_y)
        else:
            return (left + w // 2, top + h // 2)
    
    def _get_position_name(self, position: str) -> str:
        """获取位置的中文名称"""
        names = {
            "center": "中心",
            "top-left": "左上角",
            "top-right": "右上角",
            "bottom-left": "左下角",
            "bottom-right": "右下角",
            "top": "顶部",
            "bottom": "底部",
            "left": "左侧",
            "right": "右侧",
            "random": "随机位置"
        }
        return names.get(position, "中心")


@register_executor
class PhoneClickTextExecutor(ModuleExecutor):
    """手机点击文本 - 在手机屏幕上OCR识别文本并点击"""
    
    @property
    def module_type(self) -> str:
        return "phone_click_text"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        target_text = context.resolve_value(config.get('targetText', ''))
        match_mode = config.get('matchMode', 'contains')  # exact, contains, regex
        click_type = context.resolve_value(config.get('clickType', 'click'))  # click 或 long_press
        occurrence = to_int(config.get('occurrence', 1), 1, context)
        wait_timeout = to_int(config.get('waitTimeout', 10), 10, context)
        
        if not target_text:
            return ModuleResult(success=False, error="目标文本不能为空")
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context, config)
        if not success:
            return ModuleResult(success=False, error=error)
        
        try:
            import numpy as np
            from PIL import Image
        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装 Pillow: pip install Pillow"
            )
        
        # 使用 RapidOCR - 速度快，支持中文
        try:
            from rapidocr_onnxruntime import RapidOCR
            ocr = RapidOCR()
        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装 rapidocr-onnxruntime: pip install rapidocr-onnxruntime"
            )
        
        try:
            import re
            adb = get_adb_manager()
            
            start_time = time.time()
            found = False
            click_x, click_y = 0, 0
            matched_text = ""
            
            # 创建临时目录保存截图
            with tempfile.TemporaryDirectory() as temp_dir:
                screenshot_path = os.path.join(temp_dir, 'phone_screenshot.png')
                
                while time.time() - start_time < wait_timeout:
                    # 截取手机屏幕
                    success, error = adb.screenshot(screenshot_path, device_id)
                    if not success:
                        return ModuleResult(success=False, error=f"截取手机屏幕失败: {error}")
                    
                    # 读取截图
                    img = Image.open(screenshot_path)
                    img_array = np.array(img)
                    
                    # OCR识别
                    try:
                        result, _ = ocr(img_array)
                    except Exception as e:
                        context.log(f"OCR识别失败: {e}")
                        await asyncio.sleep(0.3)
                        continue
                    
                    if not result:
                        await asyncio.sleep(0.3)
                        continue
                    
                    # 查找匹配的文本
                    matches = []
                    for item in result:
                        # item 格式: [box, text, confidence]
                        # box 格式: [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                        box, recognized_text, confidence = item
                        
                        if not recognized_text:
                            continue
                        
                        # 匹配检查
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
                            x1 = int(min(p[0] for p in box))
                            y1 = int(min(p[1] for p in box))
                            x2 = int(max(p[0] for p in box))
                            y2 = int(max(p[1] for p in box))
                            
                            center_x = (x1 + x2) // 2
                            center_y = (y1 + y2) // 2
                            matches.append({
                                'text': recognized_text,
                                'x': center_x,
                                'y': center_y,
                                'confidence': confidence
                            })
                    
                    # 检查是否找到足够的匹配
                    if len(matches) >= occurrence:
                        match = matches[occurrence - 1]
                        click_x = match['x']
                        click_y = match['y']
                        matched_text = match['text']
                        found = True
                        break
                    
                    await asyncio.sleep(0.3)
            
            if not found:
                return ModuleResult(
                    success=False,
                    error=f"在 {wait_timeout} 秒内未找到匹配的文本: {target_text}"
                )
            
            # 执行点击
            if click_type == 'long_press':
                success, error = adb.long_press(click_x, click_y, 1000, device_id)
                action_name = "长按"
            else:
                success, error = adb.tap(click_x, click_y, device_id)
                action_name = "点击"
            
            if not success:
                return ModuleResult(success=False, error=error)
            
            return ModuleResult(
                success=True,
                message=f"已{action_name}文本 \"{matched_text}\" 位置: ({click_x}, {click_y})",
                data={"x": click_x, "y": click_y, "text": matched_text}
            )
            
        except Exception as e:
            return ModuleResult(success=False, error=f"点击文本失败: {str(e)}")




@register_executor
class PhoneWaitImageExecutor(ModuleExecutor):
    """手机等待图像 - 等待图像出现在手机屏幕上"""
    
    @property
    def module_type(self) -> str:
        return "phone_wait_image"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        image_path = context.resolve_value(config.get('imagePath', ''))
        confidence = to_float(config.get('confidence', 0.8), 0.8, context)
        wait_timeout = to_int(config.get('waitTimeout', 30), 30, context)
        check_interval = to_float(config.get('checkInterval', 0.5), 0.5, context)
        result_variable = config.get('resultVariable', '')
        
        if not image_path:
            return ModuleResult(success=False, error="图像路径不能为空")
        
        if not Path(image_path).exists():
            return ModuleResult(success=False, error=f"图像文件不存在: {image_path}")
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context, config)
        if not success:
            return ModuleResult(success=False, error=error)
        
        try:
            import cv2
            import numpy as np
        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装 opencv-python: pip install opencv-python"
            )
        
        try:
            adb = get_adb_manager()
            
            # 读取模板图像
            template = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if template is None:
                return ModuleResult(success=False, error="无法读取图像文件，请检查图像格式")
            
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            h, w = template_gray.shape
            
            context.log(f"📐 模板图像尺寸: {w}x{h}")
            
            start_time = time.time()
            found = False
            match_x, match_y = 0, 0
            best_confidence = 0
            check_count = 0
            
            # 创建临时目录保存截图
            with tempfile.TemporaryDirectory() as temp_dir:
                screenshot_path = os.path.join(temp_dir, 'phone_screenshot.png')
                
                while time.time() - start_time < wait_timeout:
                    check_count += 1
                    
                    # 截取手机屏幕
                    success, error = adb.screenshot(screenshot_path, device_id)
                    if not success:
                        return ModuleResult(success=False, error=f"截取手机屏幕失败: {error}")
                    
                    # 读取截图
                    screen = cv2.imread(screenshot_path)
                    if screen is None:
                        await asyncio.sleep(check_interval)
                        continue
                    
                    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
                    screen_h, screen_w = screen_gray.shape
                    
                    # 第一次循环时输出屏幕尺寸
                    if check_count == 1:
                        context.log(f"📱 手机屏幕截图尺寸: {screen_w}x{screen_h}")
                    
                    # 检查模板是否大于屏幕
                    if w > screen_w or h > screen_h:
                        return ModuleResult(
                            success=False,
                            error=f"❌ 模板图像 ({w}x{h}) 大于手机屏幕 ({screen_w}x{screen_h})，请截取更小的区域作为模板"
                        )
                    
                    # 模板匹配
                    result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    # 更新最高匹配度
                    if max_val > best_confidence:
                        best_confidence = max_val
                        context.log(f"🔍 第{check_count}次检测 - 当前最高匹配度: {best_confidence:.2%} (阈值: {confidence:.2%})")
                    
                    if max_val >= confidence:
                        # 找到匹配
                        match_x = max_loc[0] + w // 2
                        match_y = max_loc[1] + h // 2
                        best_confidence = max_val
                        found = True
                        context.log(f"✅ 找到匹配！位置: ({match_x}, {match_y}), 匹配度: {best_confidence:.2%}")
                        break
                    
                    await asyncio.sleep(check_interval)
            
            if not found:
                return ModuleResult(
                    success=False,
                    error=f"❌ 在 {wait_timeout} 秒内未找到匹配的图像（最高匹配度: {best_confidence:.2%}，共检测{check_count}次）\n💡 建议：\n1. 降低置信度阈值（当前{confidence:.2%}）\n2. 确保模板图像是从相同分辨率的手机截取的\n3. 截取更小、更独特的区域作为模板"
                )
            
            elapsed_time = time.time() - start_time
            result_data = {
                "x": match_x,
                "y": match_y,
                "confidence": best_confidence,
                "elapsed_time": round(elapsed_time, 2)
            }
            
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"✅ 图像已出现在 ({match_x}, {match_y})，匹配度: {best_confidence:.2%}，耗时: {elapsed_time:.2f}秒",
                data=result_data
            )
            
        except Exception as e:
            return ModuleResult(success=False, error=f"等待图像失败: {str(e)}")



@register_executor
class PhoneImageExistsExecutor(ModuleExecutor):
    """手机图像存在判断 - 判断图像是否存在于手机屏幕上,类似条件判断模块"""
    
    @property
    def module_type(self) -> str:
        return "phone_image_exists"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        image_path = context.resolve_value(config.get('imagePath', ''))
        confidence = to_float(config.get('confidence', 0.8), 0.8, context)
        wait_timeout = to_int(config.get('waitTimeout', 5), 5, context)
        
        if not image_path:
            return ModuleResult(success=False, error="图像路径不能为空")
        
        if not Path(image_path).exists():
            return ModuleResult(success=False, error=f"图像文件不存在: {image_path}")
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context, config)
        if not success:
            return ModuleResult(success=False, error=error)
        
        try:
            import cv2
            import numpy as np
        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装 opencv-python: pip install opencv-python"
            )
        
        try:
            adb = get_adb_manager()
            
            # 读取模板图像
            template = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if template is None:
                return ModuleResult(success=False, error="无法读取图像文件，请检查图像格式")
            
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            h, w = template_gray.shape
            
            context.log(f"📐 模板图像尺寸: {w}x{h}")
            
            start_time = time.time()
            found = False
            match_x, match_y = 0, 0
            best_confidence = 0
            check_count = 0
            
            # 创建临时目录保存截图
            with tempfile.TemporaryDirectory() as temp_dir:
                screenshot_path = os.path.join(temp_dir, 'phone_screenshot.png')
                
                while time.time() - start_time < wait_timeout:
                    check_count += 1
                    
                    # 截取手机屏幕
                    success, error = adb.screenshot(screenshot_path, device_id)
                    if not success:
                        return ModuleResult(success=False, error=f"截取手机屏幕失败: {error}")
                    
                    # 读取截图
                    screen = cv2.imread(screenshot_path)
                    if screen is None:
                        await asyncio.sleep(0.3)
                        continue
                    
                    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
                    screen_h, screen_w = screen_gray.shape
                    
                    # 第一次循环时输出屏幕尺寸
                    if check_count == 1:
                        context.log(f"📱 手机屏幕截图尺寸: {screen_w}x{screen_h}")
                    
                    # 检查模板是否大于屏幕
                    if w > screen_w or h > screen_h:
                        return ModuleResult(
                            success=False,
                            error=f"❌ 模板图像 ({w}x{h}) 大于手机屏幕 ({screen_w}x{screen_h})，请截取更小的区域作为模板"
                        )
                    
                    # 模板匹配
                    result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    # 更新最高匹配度
                    if max_val > best_confidence:
                        best_confidence = max_val
                        context.log(f"🔍 第{check_count}次检测 - 当前最高匹配度: {best_confidence:.2%} (阈值: {confidence:.2%})")
                    
                    if max_val >= confidence:
                        # 找到匹配
                        match_x = max_loc[0] + w // 2
                        match_y = max_loc[1] + h // 2
                        found = True
                        context.log(f"✅ 找到匹配！位置: ({match_x}, {match_y}), 匹配度: {best_confidence:.2%}")
                        break
                    
                    await asyncio.sleep(0.3)
            
            # 根据是否找到图像返回不同的分支
            branch = 'true' if found else 'false'
            
            if found:
                message = f"图像存在，位置: ({match_x}, {match_y})，匹配度: {best_confidence:.2%}"
                data = {"exists": True, "x": match_x, "y": match_y, "confidence": best_confidence}
            else:
                message = f"图像不存在（最高匹配度: {best_confidence:.2%}，共检测{check_count}次）"
                data = {"exists": False, "confidence": best_confidence, "check_count": check_count}
            
            return ModuleResult(
                success=True,
                message=message,
                branch=branch,
                data=data
            )
            
        except Exception as e:
            return ModuleResult(success=False, error=f"图像存在判断失败: {str(e)}")
