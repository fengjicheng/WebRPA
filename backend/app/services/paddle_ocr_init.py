#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PaddleOCR 模型初始化与单例管理

集中管理 PaddleOCR 实例，避免重复初始化导致的「PDX has already been initialized」错误，
并解决 PaddlePaddle 3.3.1 onednn 后端 PIR 属性转换不兼容问题（必须禁用 mkldnn）。
"""
import os
import threading
from pathlib import Path

# 关键环境变量：必须在 import paddle 之前设置
# PaddlePaddle 3.3.1 的 onednn 后端在某些算子上有 PIR 属性转换 bug，会导致推理崩溃
os.environ.setdefault('FLAGS_use_mkldnn', '0')
os.environ.setdefault('FLAGS_enable_pir_in_executor', '0')

_paddle_initialized = False
_ocr_instance = None
_ocr_instance_ch_only = None
_lock = threading.Lock()


def _get_models_dir() -> Path:
    """返回项目本地模型缓存目录

    paddle_ocr_init.py 位于 backend/app/services/
    parent.parent.parent 已经是 backend，无需再拼接一次 "backend"
    """
    backend_root = Path(__file__).parent.parent.parent
    models_dir = backend_root / "models" / "ocr"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def init_paddle_ocr_models():
    """启动时预热 PaddleOCR（幂等，只会执行一次）。

    PaddleOCR 是可选依赖，初始化失败不影响主程序运行——
    只有当用户使用「点击文本」「悬停文本」等 OCR 模块时才会真正需要它。
    """
    global _paddle_initialized
    with _lock:
        if _paddle_initialized:
            return True

        try:
            models_dir = _get_models_dir()
            from paddleocr import PaddleOCR
            # 提前实例化以触发模型下载，但不缓存为共享实例（避免线程问题）
            _ = PaddleOCR(
                use_textline_orientation=True,
                lang='ch',
                enable_mkldnn=False,
            )
            print(f"[PaddleOCR] 初始化成功，模型目录: {models_dir}")
            _paddle_initialized = True
            return True
        except ImportError:
            _paddle_initialized = True
            return False
        except Exception as e:
            msg = str(e)
            if 'langchain.docstore' in msg or 'paddle' in msg.lower():
                print(f"[PaddleOCR] OCR 功能不可用（依赖问题），相关模块运行时会提示")
            else:
                print(f"[PaddleOCR] 初始化失败: {msg[:200]}")
            _paddle_initialized = True
            return False


def get_ocr_instance(lang: str = 'ch'):
    """获取共享的 PaddleOCR 实例。

    为不同 lang 维护独立单例。中文识别模型 'ch' 默认包含英文识别能力。
    """
    global _ocr_instance, _ocr_instance_ch_only
    with _lock:
        if lang == 'ch':
            if _ocr_instance is None:
                from paddleocr import PaddleOCR
                _ocr_instance = PaddleOCR(
                    use_textline_orientation=True,
                    lang='ch',
                    enable_mkldnn=False,
                )
            return _ocr_instance
        else:
            # 其他语种暂不缓存（用户场景多以中英文为主）
            from paddleocr import PaddleOCR
            return PaddleOCR(
                use_textline_orientation=True,
                lang=lang,
                enable_mkldnn=False,
            )


def parse_ocr_result(raw_result):
    """统一解析 PaddleOCR predict 的返回结果。

    新版 PaddleOCR (>= 3.0) 返回:
        [{'rec_texts': [...], 'rec_scores': [...], 'rec_polys': [...], 'rec_boxes': [...]}]
    旧版返回:
        [[(box, (text, conf)), ...]]

    返回统一格式: [(box, text, confidence), ...]
        box 是 [[x1,y1], [x2,y1], [x2,y2], [x1,y2]] 形式的多边形
    """
    items = []
    if not raw_result:
        return items

    first = raw_result[0] if isinstance(raw_result, list) else raw_result

    # 新版字典格式
    if isinstance(first, dict):
        texts = first.get('rec_texts') or []
        scores = first.get('rec_scores') or []
        polys = first.get('rec_polys') or first.get('dt_polys') or []
        for i, t in enumerate(texts):
            box = polys[i] if i < len(polys) else None
            score = scores[i] if i < len(scores) else 0.0
            try:
                # 转 numpy 数组为列表
                if box is not None and hasattr(box, 'tolist'):
                    box = box.tolist()
            except Exception:
                pass
            items.append((box, t, float(score) if score is not None else 0.0))
        return items

    # 旧版嵌套元组格式
    try:
        for entry in (first if isinstance(first, list) else raw_result):
            if not entry:
                continue
            if len(entry) == 2:
                box, text_conf = entry
                if isinstance(text_conf, (list, tuple)) and len(text_conf) >= 2:
                    text, conf = text_conf[0], text_conf[1]
                else:
                    text, conf = str(text_conf), 0.0
            elif len(entry) >= 3:
                box, text, conf = entry[0], entry[1], entry[2]
            else:
                continue
            items.append((box, text, float(conf) if conf is not None else 0.0))
    except Exception:
        pass
    return items
