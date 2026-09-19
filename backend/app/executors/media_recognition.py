"""媒体处理模块 - 识别相关（人脸识别、OCR）"""
import asyncio
import os
import threading
from pathlib import Path

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int, to_float

# 项目内置 easyocr 模型目录
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # WebRPA新版 根目录
_EASYOCR_MODEL_DIR = _PROJECT_ROOT / "models" / "easyocr" / "model"


@register_executor
class FaceRecognitionExecutor(ModuleExecutor):
    """人脸识别模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "face_recognition"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        source_image = context.resolve_value(config.get('sourceImage', ''))
        target_image = context.resolve_value(config.get('targetImage', ''))
        tolerance = to_float(config.get('tolerance', 0.6), 0.6, context)
        result_variable = config.get('resultVariable', 'face_match_result')
        
        if not source_image:
            return ModuleResult(success=False, error="识别图片路径不能为空")
        
        if not target_image:
            return ModuleResult(success=False, error="目标人脸图片路径不能为空")
        
        if not os.path.exists(source_image):
            return ModuleResult(success=False, error=f"识别图片不存在: {source_image}")
        
        if not os.path.exists(target_image):
            return ModuleResult(success=False, error=f"目标人脸图片不存在: {target_image}")
        
        try:
            import face_recognition
            
            loop = asyncio.get_running_loop()

            def do_recognition():
                source_img = face_recognition.load_image_file(source_image)
                target_img = face_recognition.load_image_file(target_image)
                
                source_encodings = face_recognition.face_encodings(source_img)
                target_encodings = face_recognition.face_encodings(target_img)
                
                if len(source_encodings) == 0:
                    return {'matched': False, 'error': '识别图片中未检测到人脸', 'source_faces': 0, 'target_faces': len(target_encodings)}
                
                if len(target_encodings) == 0:
                    return {'matched': False, 'error': '目标图片中未检测到人脸', 'source_faces': len(source_encodings), 'target_faces': 0}
                
                target_encoding = target_encodings[0]
                matches = face_recognition.compare_faces(source_encodings, target_encoding, tolerance=tolerance)
                face_distances = face_recognition.face_distance(source_encodings, target_encoding)
                
                matched = any(matches)
                best_match_index = face_distances.argmin() if len(face_distances) > 0 else -1
                best_distance = float(face_distances[best_match_index]) if best_match_index >= 0 else 1.0
                confidence = round((1 - best_distance) * 100, 2)
                
                return {
                    'matched': matched,
                    'confidence': confidence,
                    'source_faces': len(source_encodings),
                    'target_faces': len(target_encodings),
                    'best_distance': round(best_distance, 4)
                }
            
            result = await loop.run_in_executor(None, do_recognition)
            
            if 'error' in result:
                if result_variable:
                    context.set_variable(result_variable, result)
                return ModuleResult(success=True, message=result['error'], data=result, branch='false')
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            branch = 'true' if result['matched'] else 'false'
            message = f"人脸{'匹配' if result['matched'] else '不匹配'}，置信度: {result['confidence']}%"
            
            return ModuleResult(success=True, message=message, data=result, branch=branch)
        except ImportError:
            return ModuleResult(success=False, error="人脸识别功能初始化失败")
        except Exception as e:
            return ModuleResult(success=False, error=f"人脸识别失败: {str(e)}")


# 全局缓存 easyocr reader，避免每次重新加载模型
_easyocr_reader = None
_easyocr_lock = threading.Lock()
_rapidocr_reader = None
_paddleocr_reader = None


class OCRInitializationError(RuntimeError):
    """所有通用 OCR 引擎均不可用，并保留每个引擎的真实失败原因。"""


def get_easyocr_reader():
    """获取缓存的 easyocr reader，使用项目内置模型目录"""
    global _easyocr_reader
    with _easyocr_lock:
        if _easyocr_reader is None:
            required = (_EASYOCR_MODEL_DIR / "craft_mlt_25k.pth",
                        _EASYOCR_MODEL_DIR / "zh_sim_g2.pth")
            missing = [p.name for p in required if not p.is_file()]
            if missing:
                raise FileNotFoundError(
                    f"EasyOCR 模型不完整（目录 {_EASYOCR_MODEL_DIR}，缺少: {', '.join(missing)}）"
                )
            import easyocr
            model_dir = str(_EASYOCR_MODEL_DIR)
            print(f"[EasyOCR] 使用本地模型目录: {model_dir}")
            _easyocr_reader = easyocr.Reader(
                ['ch_sim', 'en'],
                gpu=False,
                verbose=False,
                model_storage_directory=model_dir,
                download_enabled=False,
            )
    return _easyocr_reader


def _box_sort_key(item):
    box = item[0] if item else None
    try:
        return float(box[0][1]), float(box[0][0])
    except Exception:
        return 0.0, 0.0


def _read_general_ocr(img_array):
    """按 EasyOCR → RapidOCR → PaddleOCR 回退识别，返回 (文本, 引擎名)。

    OCR 功能包允许 PaddleOCR/EasyOCR 二选一；旧实现却硬依赖 EasyOCR，导致只安装
    Paddle 包时直接报“初始化失败”。这里逐引擎尝试，并在全部失败时给出可诊断信息。
    """
    global _rapidocr_reader, _paddleocr_reader
    errors = []

    try:
        reader = get_easyocr_reader()
        rows = reader.readtext(img_array)
        texts = [str(item[1]) for item in sorted(rows or [], key=_box_sort_key) if len(item) > 1]
        return '\n'.join(texts), 'EasyOCR'
    except Exception as e:
        errors.append(f"EasyOCR: {type(e).__name__}: {e}")

    try:
        if _rapidocr_reader is None:
            from rapidocr_onnxruntime import RapidOCR
            _rapidocr_reader = RapidOCR()
        raw = _rapidocr_reader(img_array)
        rows = raw[0] if isinstance(raw, tuple) else raw
        texts = [str(item[1]) for item in sorted(rows or [], key=_box_sort_key) if len(item) > 1]
        return '\n'.join(texts), 'RapidOCR'
    except Exception as e:
        errors.append(f"RapidOCR: {type(e).__name__}: {e}")

    try:
        from app.services.paddle_ocr_init import get_ocr_instance, parse_ocr_result
        if _paddleocr_reader is None:
            _paddleocr_reader = get_ocr_instance('ch')
        if hasattr(_paddleocr_reader, 'predict'):
            raw = _paddleocr_reader.predict(img_array)
        else:
            raw = _paddleocr_reader.ocr(img_array)
        rows = parse_ocr_result(raw)
        texts = [str(item[1]) for item in sorted(rows or [], key=_box_sort_key) if len(item) > 1]
        return '\n'.join(texts), 'PaddleOCR'
    except Exception as e:
        errors.append(f"PaddleOCR: {type(e).__name__}: {e}")

    raise OCRInitializationError("；".join(errors))


@register_executor
class ImageOCRExecutor(ModuleExecutor):
    """图片OCR模块执行器 - 支持图片文件和屏幕区域识别"""
    
    @property
    def module_type(self) -> str:
        return "image_ocr"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ocr_mode = context.resolve_value(config.get('ocrMode', 'file'))
        result_variable = config.get('resultVariable', 'ocr_text')
        ocr_type = context.resolve_value(config.get('ocrType', 'general'))
        
        try:
            loop = asyncio.get_running_loop()
            
            if ocr_mode == 'region':
                return await self._ocr_region(config, context, loop, result_variable, ocr_type)
            else:
                return await self._ocr_file(config, context, loop, result_variable, ocr_type)
                
        except OCRInitializationError as e:
            return ModuleResult(success=False, error=f"OCR识别功能初始化失败：{e}")
        except Exception as e:
            return ModuleResult(success=False, error=f"OCR识别失败: {type(e).__name__}: {e}")
    
    async def _ocr_region(self, config: dict, context: ExecutionContext, loop, result_variable: str, ocr_type: str) -> ModuleResult:
        """区域识别模式 - 截取屏幕指定区域"""
        start_x = context.resolve_value(config.get('startX', ''))
        start_y = context.resolve_value(config.get('startY', ''))
        end_x = context.resolve_value(config.get('endX', ''))
        end_y = context.resolve_value(config.get('endY', ''))
        
        if not all([start_x, start_y, end_x, end_y]):
            return ModuleResult(success=False, error="区域坐标不能为空")
        
        try:
            x1, y1 = int(start_x), int(start_y)
            x2, y2 = int(end_x), int(end_y)
        except ValueError:
            return ModuleResult(success=False, error="坐标必须是数字")
        
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        def capture_and_ocr():
            import ctypes
            from PIL import Image, ImageEnhance
            import io
            import numpy as np
            
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass
            
            img_array = None
            pil_image = None
            try:
                import win32gui
                import win32ui
                import win32con
                
                width = x2 - x1
                height = y2 - y1
                
                hdesktop = win32gui.GetDesktopWindow()
                desktop_dc = win32gui.GetWindowDC(hdesktop)
                img_dc = win32ui.CreateDCFromHandle(desktop_dc)
                mem_dc = img_dc.CreateCompatibleDC()
                
                screenshot = win32ui.CreateBitmap()
                screenshot.CreateCompatibleBitmap(img_dc, width, height)
                mem_dc.SelectObject(screenshot)
                mem_dc.BitBlt((0, 0), (width, height), img_dc, (x1, y1), win32con.SRCCOPY)
                
                bmpinfo = screenshot.GetInfo()
                bmpstr = screenshot.GetBitmapBits(True)
                img_array = np.frombuffer(bmpstr, dtype=np.uint8).reshape(
                    (bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4))
                pil_image = Image.fromarray(img_array[:, :, :3][:, :, ::-1])
                # 转为3通道 numpy 数组（easyocr 需要 RGB）
                img_array = np.array(pil_image)
                
                mem_dc.DeleteDC()
                win32gui.DeleteObject(screenshot.GetHandle())
                win32gui.ReleaseDC(hdesktop, desktop_dc)
                
            except ImportError:
                from PIL import ImageGrab
                pil_image = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                img_array = np.array(pil_image.convert('RGB'))
            
            if ocr_type == 'captcha':
                import ddddocr
                gray_image = pil_image.convert('L')
                enhancer = ImageEnhance.Contrast(gray_image)
                enhanced_image = enhancer.enhance(1.5)
                if enhanced_image.width < 200 or enhanced_image.height < 50:
                    scale = max(200 / enhanced_image.width, 50 / enhanced_image.height, 2)
                    new_size = (int(enhanced_image.width * scale), int(enhanced_image.height * scale))
                    enhanced_image = enhanced_image.resize(new_size, Image.Resampling.LANCZOS)
                
                img_bytes = io.BytesIO()
                enhanced_image.save(img_bytes, format='PNG')
                image_bytes = img_bytes.getvalue()
                
                ocr_engine = ddddocr.DdddOcr()
                result = ocr_engine.classification(image_bytes)
                return result
            else:
                text, _engine = _read_general_ocr(img_array)
                return text
        
        text = await loop.run_in_executor(None, capture_and_ocr)
        
        if result_variable:
            context.set_variable(result_variable, text)
        
        return ModuleResult(
            success=True,
            message=f"区域OCR识别完成: {text[:50]}{'...' if len(text) > 50 else ''}",
            data={'text': text, 'length': len(text), 'region': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}}
        )
    
    async def _ocr_file(self, config: dict, context: ExecutionContext, loop, result_variable: str, ocr_type: str) -> ModuleResult:
        """文件识别模式"""
        image_path = context.resolve_value(config.get('imagePath', ''))
        
        if not image_path:
            return ModuleResult(success=False, error="图片路径不能为空")
        
        if not os.path.exists(image_path):
            return ModuleResult(success=False, error=f"图片不存在: {image_path}")
        
        def do_ocr():
            from PIL import Image, ImageEnhance
            import io
            import numpy as np
            
            with Image.open(image_path) as img:
                pil_image = img.convert('RGB')
                
                if ocr_type == 'captcha':
                    import ddddocr
                    gray_image = pil_image.convert('L')
                    enhancer = ImageEnhance.Contrast(gray_image)
                    enhanced_image = enhancer.enhance(1.5)
                    if enhanced_image.width < 200 or enhanced_image.height < 50:
                        scale = max(200 / enhanced_image.width, 50 / enhanced_image.height, 2)
                        new_size = (int(enhanced_image.width * scale), int(enhanced_image.height * scale))
                        enhanced_image = enhanced_image.resize(new_size, Image.Resampling.LANCZOS)
                    
                    img_bytes = io.BytesIO()
                    enhanced_image.save(img_bytes, format='PNG')
                    image_bytes = img_bytes.getvalue()
                    
                    ocr_engine = ddddocr.DdddOcr()
                    result = ocr_engine.classification(image_bytes)
                    return result
                else:
                    # 修复：将 pil_image 转为 numpy 数组传给 easyocr
                    # 大图自动缩放到最长边 1600px，避免 CPU 推理过慢
                    max_side = max(pil_image.width, pil_image.height)
                    if max_side > 1600:
                        scale = 1600 / max_side
                        new_size = (int(pil_image.width * scale), int(pil_image.height * scale))
                        pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
                    img_array = np.array(pil_image)
                    text, _engine = _read_general_ocr(img_array)
                    return text
        
        text = await loop.run_in_executor(None, do_ocr)
        
        if result_variable:
            context.set_variable(result_variable, text)
        
        return ModuleResult(
            success=True,
            message=f"OCR识别完成: {text[:50]}{'...' if len(text) > 50 else ''}",
            data={'text': text, 'length': len(text)}
        )
