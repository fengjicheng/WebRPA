"""高级模块执行器 - advanced_macro"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int, to_float, parse_search_region
import asyncio
import ctypes
import json
import os
import re
import struct
import time


@register_executor
class MacroRecorderExecutor(ModuleExecutor):
    """宏录制器模块执行器 - 录制并回放鼠标和键盘操作"""

    @property
    def module_type(self) -> str:
        return "macro_recorder"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import ctypes
        import json

        # 获取配置
        recorded_data = config.get("recordedData", "")  # JSON格式的录制数据
        play_speed = to_float(config.get("playSpeed", 1.0), 1.0, context)  # 播放速度倍率
        repeat_count = to_int(config.get("repeatCount", 1), 1, context)  # 重复次数
        
        # 播放选项
        play_mouse_move = config.get("playMouseMove", True)  # 播放鼠标移动轨迹
        play_mouse_click = config.get("playMouseClick", True)  # 播放鼠标点击
        play_keyboard = config.get("playKeyboard", True)  # 播放键盘操作
        use_relative_position = config.get("useRelativePosition", False)  # 使用相对位置
        
        # 相对位置的基准点（如果启用相对位置）
        base_x = to_int(config.get("baseX", 0), 0, context)
        base_y = to_int(config.get("baseY", 0), 0, context)

        if not recorded_data:
            return ModuleResult(success=False, error="没有录制数据，请先录制操作")

        try:
            # 解析录制数据
            if isinstance(recorded_data, str):
                actions = json.loads(recorded_data)
            else:
                actions = recorded_data
            
            if not actions or not isinstance(actions, list):
                return ModuleResult(success=False, error="录制数据格式无效")

            from ctypes import wintypes
            
            # Windows API
            user32 = ctypes.windll.user32
            
            # 设置进程为 DPI 感知，确保坐标与录制时一致
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
            except Exception:
                try:
                    user32.SetProcessDPIAware()
                except Exception:
                    pass
            
            # SendInput 结构体定义
            INPUT_MOUSE = 0
            INPUT_KEYBOARD = 1
            MOUSEEVENTF_MOVE = 0x0001
            MOUSEEVENTF_LEFTDOWN = 0x0002
            MOUSEEVENTF_LEFTUP = 0x0004
            MOUSEEVENTF_RIGHTDOWN = 0x0008
            MOUSEEVENTF_RIGHTUP = 0x0010
            MOUSEEVENTF_MIDDLEDOWN = 0x0020
            MOUSEEVENTF_MIDDLEUP = 0x0040
            MOUSEEVENTF_WHEEL = 0x0800
            MOUSEEVENTF_VIRTUALDESK = 0x4000
            MOUSEEVENTF_ABSOLUTE = 0x8000
            KEYEVENTF_KEYUP = 0x0002
            KEYEVENTF_UNICODE = 0x0004
            
            class MOUSEINPUT(ctypes.Structure):
                _fields_ = [
                    ("dx", wintypes.LONG),
                    ("dy", wintypes.LONG),
                    ("mouseData", wintypes.DWORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
                ]
            
            class KEYBDINPUT(ctypes.Structure):
                _fields_ = [
                    ("wVk", wintypes.WORD),
                    ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
                ]
            
            class INPUT_UNION(ctypes.Union):
                _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]
            
            class INPUT(ctypes.Structure):
                _fields_ = [
                    ("type", wintypes.DWORD),
                    ("union", INPUT_UNION)
                ]
            
            # 获取虚拟屏幕尺寸（用于坐标转换）
            SM_XVIRTUALSCREEN = 76
            SM_YVIRTUALSCREEN = 77
            SM_CXVIRTUALSCREEN = 78
            SM_CYVIRTUALSCREEN = 79
            
            virtual_left = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
            virtual_top = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
            virtual_width = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
            virtual_height = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
            
            # 安装低级鼠标钩子来清除 LLMHF_INJECTED 标志
            # 这样可以让模拟的鼠标输入看起来像真实的硬件输入
            WH_MOUSE_LL = 14
            LLMHF_INJECTED = 0x00000001
            
            class MSLLHOOKSTRUCT(ctypes.Structure):
                _fields_ = [
                    ("pt", wintypes.POINT),
                    ("mouseData", wintypes.DWORD),
                    ("flags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
                ]
            
            # 钩子回调函数类型
            HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
            
            # 钩子句柄
            mouse_hook = None
            
            # 钩子回调函数 - 清除 LLMHF_INJECTED 标志
            @HOOKPROC
            def mouse_hook_proc(nCode, wParam, lParam):
                if nCode >= 0:
                    # 获取钩子结构体
                    hook_struct = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                    # 清除 LLMHF_INJECTED 标志
                    # 注意：这个修改可能不会传播到其他钩子，但值得一试
                    if hook_struct.flags & LLMHF_INJECTED:
                        hook_struct.flags &= ~LLMHF_INJECTED
                return user32.CallNextHookEx(mouse_hook, nCode, wParam, lParam)
            
            # 安装钩子
            try:
                mouse_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, mouse_hook_proc, None, 0)
            except Exception:
                mouse_hook = None
            
            # mouse_event 常量
            ME_MOVE = 0x0001
            ME_ABSOLUTE = 0x8000
            ME_LEFTDOWN = 0x0002
            ME_LEFTUP = 0x0004
            ME_RIGHTDOWN = 0x0008
            ME_RIGHTUP = 0x0010
            ME_MIDDLEDOWN = 0x0020
            ME_MIDDLEUP = 0x0040
            ME_WHEEL = 0x0800
            
            # 移动鼠标 - 使用 SetCursorPos（直接设置光标位置，更可靠）
            def move_mouse(x, y):
                x = int(x)
                y = int(y)
                # 使用 SetCursorPos 直接设置光标位置
                user32.SetCursorPos(x, y)
            
            # 发送鼠标按键事件 - 先移动到位置再点击
            def send_mouse_button(event_flag, x=None, y=None):
                # 如果提供了坐标，先移动到该位置
                if x is not None and y is not None:
                    user32.SetCursorPos(int(x), int(y))
                
                # 映射 SendInput 标志到 mouse_event 标志
                me_flag = 0
                if event_flag == MOUSEEVENTF_LEFTDOWN:
                    me_flag = ME_LEFTDOWN
                elif event_flag == MOUSEEVENTF_LEFTUP:
                    me_flag = ME_LEFTUP
                elif event_flag == MOUSEEVENTF_RIGHTDOWN:
                    me_flag = ME_RIGHTDOWN
                elif event_flag == MOUSEEVENTF_RIGHTUP:
                    me_flag = ME_RIGHTUP
                elif event_flag == MOUSEEVENTF_MIDDLEDOWN:
                    me_flag = ME_MIDDLEDOWN
                elif event_flag == MOUSEEVENTF_MIDDLEUP:
                    me_flag = ME_MIDDLEUP
                
                # 使用 mouse_event 发送按键事件
                user32.mouse_event(me_flag, 0, 0, 0, 0)
            
            def send_mouse_scroll(delta):
                # 使用 mouse_event 发送滚轮事件
                user32.mouse_event(ME_WHEEL, 0, 0, delta, 0)
            
            def send_key(vk_code, is_up=False):
                inp = INPUT()
                inp.type = INPUT_KEYBOARD
                inp.union.ki.wVk = vk_code
                inp.union.ki.wScan = user32.MapVirtualKeyW(vk_code, 0)
                inp.union.ki.dwFlags = KEYEVENTF_KEYUP if is_up else 0
                inp.union.ki.time = 0
                inp.union.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
                user32.SendInput(1, ctypes.pointer(inp), ctypes.sizeof(INPUT))
            
            def send_unicode_char(char):
                # 按下
                inp_down = INPUT()
                inp_down.type = INPUT_KEYBOARD
                inp_down.union.ki.wVk = 0
                inp_down.union.ki.wScan = ord(char)
                inp_down.union.ki.dwFlags = KEYEVENTF_UNICODE
                inp_down.union.ki.time = 0
                inp_down.union.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
                user32.SendInput(1, ctypes.pointer(inp_down), ctypes.sizeof(INPUT))
                # 释放
                inp_up = INPUT()
                inp_up.type = INPUT_KEYBOARD
                inp_up.union.ki.wVk = 0
                inp_up.union.ki.wScan = ord(char)
                inp_up.union.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
                inp_up.union.ki.time = 0
                inp_up.union.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
                user32.SendInput(1, ctypes.pointer(inp_up), ctypes.sizeof(INPUT))

            # 如果使用相对位置，获取当前鼠标位置作为基准
            if use_relative_position:
                class POINT(ctypes.Structure):
                    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
                pt = POINT()
                user32.GetCursorPos(ctypes.byref(pt))
                # 计算偏移量（当前位置 - 录制时的基准位置）
                offset_x = pt.x - base_x
                offset_y = pt.y - base_y
            else:
                offset_x = 0
                offset_y = 0

            total_actions = len(actions)

            for repeat in range(repeat_count):
                if repeat_count > 1:
                    await context.send_progress(f"🔄 第 {repeat + 1}/{repeat_count} 次播放...")

                last_time = 0
                for i, action in enumerate(actions):
                    action_type = action.get("type")
                    timestamp = action.get("time", 0)
                    
                    # 计算延迟时间（考虑播放速度）
                    if i > 0 and timestamp > last_time:
                        delay = (timestamp - last_time) / 1000 / play_speed
                        # 使用更精确的延迟，最小延迟0.001秒
                        if delay > 0.001:
                            await asyncio.sleep(delay)
                    last_time = timestamp

                    # 执行动作
                    if action_type == "mouse_move" and play_mouse_move:
                        x = action.get("x", 0) + offset_x
                        y = action.get("y", 0) + offset_y
                        try:
                            move_mouse(x, y)
                        except Exception as e:
                            print(f"鼠标移动失败: {e}")
                        # 使用同步延迟，确保事件连续发送
                        import time as time_module
                        time_module.sleep(0.002)  # 2ms 延迟

                    elif action_type == "mouse_click" and play_mouse_click:
                        x = action.get("x", 0) + offset_x
                        y = action.get("y", 0) + offset_y
                        button = action.get("button", "left")
                        pressed = action.get("pressed", True)
                        
                        # 先移动到位置
                        try:
                            move_mouse(x, y)
                        except Exception as e:
                            print(f"鼠标移动失败: {e}")
                        
                        # 短暂延迟，模拟真实操作
                        import time as time_module
                        time_module.sleep(0.01)  # 10ms
                        
                        # 发送按键事件
                        if button == "left":
                            event = MOUSEEVENTF_LEFTDOWN if pressed else MOUSEEVENTF_LEFTUP
                        elif button == "right":
                            event = MOUSEEVENTF_RIGHTDOWN if pressed else MOUSEEVENTF_RIGHTUP
                        elif button == "middle":
                            event = MOUSEEVENTF_MIDDLEDOWN if pressed else MOUSEEVENTF_MIDDLEUP
                        else:
                            continue
                        send_mouse_button(event, x, y)
                        
                        # 点击后短暂延迟
                        time_module.sleep(0.01)  # 10ms

                    elif action_type == "mouse_scroll" and play_mouse_click:
                        delta = action.get("delta", 0)
                        send_mouse_scroll(delta)

                    elif action_type == "key_press" and play_keyboard:
                        key_code = action.get("keyCode", 0)
                        pressed = action.get("pressed", True)
                        if key_code > 0:
                            send_key(key_code, is_up=not pressed)

                    elif action_type == "key_char" and play_keyboard:
                        char = action.get("char", "")
                        if char:
                            send_unicode_char(char)

            # 统计信息
            move_count = sum(1 for a in actions if a.get("type") == "mouse_move")
            click_count = sum(1 for a in actions if a.get("type") == "mouse_click")
            key_count = sum(1 for a in actions if a.get("type") in ("key_press", "key_char"))
            
            message = f"宏播放完成: {total_actions}个动作"
            if repeat_count > 1:
                message += f" × {repeat_count}次"
            details = []
            if move_count > 0 and play_mouse_move:
                details.append(f"移动{move_count}次")
            if click_count > 0 and play_mouse_click:
                details.append(f"点击{click_count}次")
            if key_count > 0 and play_keyboard:
                details.append(f"按键{key_count}次")
            if details:
                message += f" ({', '.join(details)})"

            # 卸载鼠标钩子
            if mouse_hook:
                user32.UnhookWindowsHookEx(mouse_hook)

            return ModuleResult(
                success=True,
                message=message,
                data={
                    "total_actions": total_actions,
                    "repeat_count": repeat_count,
                    "move_count": move_count,
                    "click_count": click_count,
                    "key_count": key_count
                }
            )

        except json.JSONDecodeError:
            # 卸载鼠标钩子
            if 'mouse_hook' in dir() and mouse_hook:
                user32.UnhookWindowsHookEx(mouse_hook)
            return ModuleResult(success=False, error="录制数据JSON格式无效")
        except Exception as e:
            # 卸载鼠标钩子
            if 'mouse_hook' in dir() and mouse_hook:
                user32.UnhookWindowsHookEx(mouse_hook)
            return ModuleResult(success=False, error=f"宏播放失败: {str(e)}")