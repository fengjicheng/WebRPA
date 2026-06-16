# -*- coding: utf-8 -*-
"""桌面智能录制器

用全局键鼠钩子（pynput）记录用户的桌面操作，并尽量用 UIAutomation 识别点击处的控件，
生成语义化步骤，供前端转换为桌面自动化节点（真实鼠标点击 / 键盘输入）。

事件类型：
- click   鼠标点击 {x, y, button, window, control}
- type    键盘文本输入（连续可见字符合并）{text}
- hotkey  组合键/功能键 {keys}
"""
from __future__ import annotations

import threading
import time
from typing import Optional

_lock = threading.Lock()
_events: list[dict] = []
_active = False
_paused = False
_mouse_listener = None
_kbd_listener = None
_type_buffer: list[str] = []
_type_buffer_ts: float = 0.0


def is_active() -> bool:
    return _active


def is_paused() -> bool:
    return _paused


def pause() -> dict:
    global _paused
    with _lock:
        _paused = True
        _flush_type_buffer()
    return {"success": True, "paused": True}


def resume() -> dict:
    global _paused
    with _lock:
        _paused = False
    return {"success": True, "paused": False}


def _flush_type_buffer():
    """把累积的可见字符合并成一个 type 事件"""
    global _type_buffer
    if _type_buffer:
        text = "".join(_type_buffer)
        _type_buffer = []
        if text:
            _events.append({"type": "type", "text": text, "ts": time.time()})


def _describe_control_at(x: int, y: int) -> dict:
    """尽力识别 (x,y) 处的 UIAutomation 控件与所属窗口（失败返回空信息）"""
    info = {"window": "", "control": "", "controlType": "", "automationId": "", "className": ""}
    try:
        import win32gui
        hwnd = win32gui.WindowFromPoint((x, y))
        top = win32gui.GetAncestor(hwnd, 2)  # GA_ROOT
        info["window"] = win32gui.GetWindowText(top) or ""
    except Exception:
        pass
    try:
        import uiautomation as auto
        ctrl = auto.ControlFromPoint(x, y)
        if ctrl:
            info["control"] = (ctrl.Name or "")[:60]
            info["controlType"] = ctrl.ControlTypeName or ""
            try:
                info["automationId"] = ctrl.AutomationId or ""
            except Exception:
                pass
            try:
                info["className"] = ctrl.ClassName or ""
            except Exception:
                pass
    except Exception:
        pass
    return info


def _on_click(x, y, button, pressed):
    if not pressed:
        return
    with _lock:
        if not _active or _paused:
            return
        _flush_type_buffer()
        btn = "left"
        try:
            btn = button.name  # 'left' / 'right' / 'middle'
        except Exception:
            pass
        ctrl = _describe_control_at(int(x), int(y))
        _events.append({
            "type": "click", "x": int(x), "y": int(y), "button": btn,
            "window": ctrl["window"], "control": ctrl["control"],
            "controlType": ctrl["controlType"], "automationId": ctrl.get("automationId", ""),
            "className": ctrl.get("className", ""), "ts": time.time(),
        })


# 功能键名映射（pynput Key -> 友好名）
_SPECIAL_KEYS = {
    'enter': 'Enter', 'tab': 'Tab', 'esc': 'Escape', 'backspace': 'Backspace',
    'space': 'Space', 'delete': 'Delete', 'up': 'Up', 'down': 'Down',
    'left': 'Left', 'right': 'Right', 'home': 'Home', 'end': 'End',
    'page_up': 'PageUp', 'page_down': 'PageDown',
}


def _on_press(key):
    global _type_buffer_ts
    with _lock:
        if not _active or _paused:
            return
        try:
            from pynput import keyboard as _kb
        except Exception:
            return
        # 普通可见字符：累积到输入缓冲
        ch = getattr(key, 'char', None)
        if ch is not None and ch.isprintable() and ch not in ('\x16', '\x03'):
            _type_buffer.append(ch)
            _type_buffer_ts = time.time()
            return
        # 功能键 / 组合键：先冲刷文本缓冲，再记录为 hotkey
        _flush_type_buffer()
        name = None
        try:
            name = key.name  # 特殊键有 .name
        except Exception:
            name = None
        if name == 'space':
            # 空格当作可见输入更自然
            _type_buffer.append(' ')
            _type_buffer_ts = time.time()
            return
        friendly = _SPECIAL_KEYS.get(name or '', None)
        if friendly:
            _events.append({"type": "hotkey", "keys": friendly, "ts": time.time()})


def start_recorder() -> dict:
    """开始桌面录制（启动全局键鼠钩子）"""
    global _active, _mouse_listener, _kbd_listener, _events, _type_buffer, _paused
    with _lock:
        if _active:
            return {"success": True, "message": "已在录制中"}
        try:
            from pynput import mouse as _mouse, keyboard as _kb
        except Exception as e:
            return {"success": False, "error": f"缺少 pynput 库，无法桌面录制: {e}"}
        _events = []
        _type_buffer = []
        _paused = False
        try:
            _mouse_listener = _mouse.Listener(on_click=_on_click)
            _kbd_listener = _kb.Listener(on_press=_on_press)
            _mouse_listener.start()
            _kbd_listener.start()
            _active = True
        except Exception as e:
            return {"success": False, "error": f"启动钩子失败: {e}"}
    return {"success": True, "message": "桌面录制已开始"}


def stop_recorder() -> dict:
    """停止录制并返回全部剩余事件"""
    global _active, _mouse_listener, _kbd_listener
    with _lock:
        _active = False
        _flush_type_buffer()
        for lis in (_mouse_listener, _kbd_listener):
            try:
                if lis:
                    lis.stop()
            except Exception:
                pass
        _mouse_listener = None
        _kbd_listener = None
        remaining = list(_events)
    return {"success": True, "data": remaining}


def drain_events() -> dict:
    """排空并返回已录制事件（轮询用）"""
    global _events
    with _lock:
        # 文本缓冲若停顿超过 1.2s 也先冲刷，避免一直不出现在轮询里
        if _type_buffer and (time.time() - _type_buffer_ts) > 1.2:
            _flush_type_buffer()
        out = list(_events)
        _events = []
    return {"success": True, "data": out}
