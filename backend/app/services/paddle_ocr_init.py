#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PaddleOCR 模型初始化 - 在后端启动时自动下载模型到项目目录
"""
import os
from pathlib import Path

def init_paddle_ocr_models():
    """初始化 PaddleOCR 模型"""
    try:
        # 设置模型缓存目录到项目内
        project_root = Path(__file__).parent.parent.parent
        models_dir = project_root / "backend" / "models" / "ocr"
        models_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[PaddleOCR] Model cache directory: {models_dir}")
        
        # 导入并初始化 PaddleOCR
        from paddleocr import PaddleOCR
        print("[PaddleOCR] Initializing PaddleOCR...")
        ocr = PaddleOCR(use_angle_cls=True, lang='ch', model_storage_directory=str(models_dir))
        print("[PaddleOCR] PaddleOCR initialized successfully")
        
        return True
    except Exception as e:
        print(f"[PaddleOCR] Warning: Failed to initialize OCR: {e}")
        return False

# 在模块导入时自动初始化
init_paddle_ocr_models()
