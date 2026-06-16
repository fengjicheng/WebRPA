# -*- coding: utf-8 -*-
"""pytest 全局配置：确保以 backend 目录为根可 import app.*"""
import os
import sys

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
