# -*- coding: utf-8 -*-
"""本地测试运行器（内置 Python 环境用）

内置 Python 装了 langsmith，其 pytest 插件会在自动加载时报错。
本脚本禁用插件自动加载、并显式加载 pytest-asyncio，保证本地一键跑通：

    ..\\Python313\\python.exe run_tests.py
"""
import os
import sys
import subprocess

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

here = os.path.dirname(os.path.abspath(__file__))
cmd = [
    sys.executable, "-m", "pytest",
    "-p", "pytest_asyncio.plugin",
    "tests",
    *sys.argv[1:],
]
raise SystemExit(subprocess.call(cmd, cwd=here))
