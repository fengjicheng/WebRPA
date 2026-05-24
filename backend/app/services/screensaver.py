"""屏保弹幕服务 - Python tkinter 全屏窗口

可在用户电脑屏幕之上覆盖一个全屏弹幕/屏保层，由独立子进程运行（tkinter 必须主线程，避免阻塞 FastAPI）。
支持的内容类型：
- text       静态文本
- scroll     滚动文本（横向 / 纵向 / 双向）
- clock      实时时钟（多种格式）
- date       实时日期
- countdown  倒计时（剩余秒数）
- bullet     弹幕（多条文本随机轨迹滚动）

启动方式：scheduled = subprocess.Popen([python, screensaver.py, '--config', json_path])
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

# 全局子进程句柄（同一时间只允许一个屏保实例）
_proc: Optional[subprocess.Popen] = None
_config_file: Optional[Path] = None


def _python_exe() -> str:
    """返回当前 Python 可执行路径（兼容打包环境）"""
    return sys.executable


def _runner_path() -> Path:
    """子进程运行脚本路径"""
    return Path(__file__).parent / "screensaver_runner.py"


def is_running() -> bool:
    return _proc is not None and _proc.poll() is None


def start(config: dict) -> dict:
    """启动屏保弹幕

    config 关键字段（前端传入）：
    {
        "content_type": "text|scroll|clock|date|countdown|bullet",
        "text": "...",                # text/scroll 用
        "datetime_format": "...",     # clock/date 自定义 strftime（可选）
        "countdown_target": "ISO 时间",# countdown 用
        "bullets": [{...}, ...],      # bullet 多条
        "font_family": "Microsoft YaHei",
        "font_size": 64,
        "font_weight": "normal|bold",
        "font_italic": false,
        "color": "#ffffff",           # 文本颜色
        "background": "#000000",      # 背景色（设置 alpha=0 则透明）
        "background_alpha": 1.0,      # 0~1，透明度（仅 Win）
        "fullscreen": true,
        "screen": 0,                  # 多屏选择
        "scroll_direction": "left|right|up|down",
        "scroll_speed": 200,          # 像素/秒
        "scroll_loop": true,
        "click_through": false,       # 是否让点击穿透到底层
        "show_close_hint": true,      # 是否显示退出快捷键提示
        "exit_hotkey": "Esc",         # 默认 Esc
        "outline_color": "",          # 文字描边颜色（可选）
        "outline_width": 0,           # 描边宽度
        "rotation": 0,                # 旋转角度（仅 text/scroll 支持 0/90/180/270）
        "vertical_text": false,       # 竖排文字
    }
    返回 {"success": True, "message": ...} 或失败信息
    """
    global _proc, _config_file

    if is_running():
        return {"success": False, "error": "屏保已在运行，先停止后再启动"}

    # 把配置写到临时文件传给子进程
    try:
        fd, fp = tempfile.mkstemp(prefix="webrpa_screensaver_", suffix=".json")
        os.close(fd)
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(config or {}, f, ensure_ascii=False)
        _config_file = Path(fp)
    except Exception as e:
        return {"success": False, "error": f"写配置失败：{e}"}

    runner = _runner_path()
    if not runner.exists():
        return {"success": False, "error": f"找不到 runner 脚本：{runner}"}

    try:
        creationflags = 0
        if sys.platform == "win32":
            # 不弹黑色控制台
            creationflags = 0x08000000  # CREATE_NO_WINDOW
        _proc = subprocess.Popen(
            [_python_exe(), str(runner), "--config", str(_config_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            creationflags=creationflags,
        )
        return {"success": True, "message": "屏保已启动", "pid": _proc.pid}
    except Exception as e:
        return {"success": False, "error": f"启动子进程失败：{e}"}


def stop() -> dict:
    global _proc, _config_file
    if not is_running():
        # 即使句柄丢了也清理临时文件
        if _config_file and _config_file.exists():
            try:
                _config_file.unlink()
            except Exception:
                pass
        _config_file = None
        return {"success": True, "message": "屏保未在运行"}
    try:
        assert _proc is not None
        _proc.terminate()
        try:
            _proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _proc.kill()
            _proc.wait(timeout=2)
    except Exception as e:
        return {"success": False, "error": f"停止失败：{e}"}
    finally:
        _proc = None
        if _config_file and _config_file.exists():
            try:
                _config_file.unlink()
            except Exception:
                pass
        _config_file = None
    return {"success": True, "message": "屏保已停止"}


def status() -> dict:
    return {
        "running": is_running(),
        "pid": _proc.pid if is_running() and _proc else None,
    }
