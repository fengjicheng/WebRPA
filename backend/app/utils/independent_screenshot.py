"""
独立截图工具
使用 Windows API 模拟 Win+Shift+S 触发系统截图栏
纯粹依赖剪贴板变化检测截图完成，最多等待60秒
"""
import ctypes
import ctypes.wintypes
import time
import uuid
import sys
import os
from pathlib import Path
from PIL import ImageGrab, Image
import json


# Windows 虚拟键码
VK_LWIN   = 0x5B
VK_SHIFT  = 0x10
VK_S      = 0x53
KEYEVENTF_KEYUP = 0x0002

# INPUT 结构体
INPUT_KEYBOARD = 1

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ('wVk',         ctypes.wintypes.WORD),
        ('wScan',       ctypes.wintypes.WORD),
        ('dwFlags',     ctypes.wintypes.DWORD),
        ('time',        ctypes.wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong)),
    ]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ('ki', KEYBDINPUT),
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.wintypes.DWORD),
        ('_input', _INPUT_UNION),
    ]


def _send_key(vk: int, key_up: bool = False):
    """发送单个按键事件"""
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp._input.ki.wVk = vk
    inp._input.ki.wScan = 0
    inp._input.ki.dwFlags = KEYEVENTF_KEYUP if key_up else 0
    inp._input.ki.time = 0
    inp._input.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def send_win_shift_s():
    """
    通过 Windows SendInput API 模拟 Win+Shift+S
    触发 Windows 截图栏（所有 Windows 10/11 均支持）
    """
    try:
        # 按下 Win
        _send_key(VK_LWIN)
        time.sleep(0.05)
        # 按下 Shift
        _send_key(VK_SHIFT)
        time.sleep(0.05)
        # 按下 S
        _send_key(VK_S)
        time.sleep(0.05)
        # 松开 S
        _send_key(VK_S, key_up=True)
        time.sleep(0.05)
        # 松开 Shift
        _send_key(VK_SHIFT, key_up=True)
        time.sleep(0.05)
        # 松开 Win
        _send_key(VK_LWIN, key_up=True)
        print("[DEBUG] Win+Shift+S 已发送", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[DEBUG] SendInput 失败: {e}", file=sys.stderr)
        return False


def get_clipboard_image():
    """安全地获取剪贴板图片，返回 Image 或 None"""
    try:
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            return img
    except Exception:
        pass
    return None


def images_equal(img1, img2):
    """比较两张图片是否相同"""
    if img1 is None and img2 is None:
        return True
    if img1 is None or img2 is None:
        return False
    if img1.size != img2.size:
        return False
    return img1.tobytes() == img2.tobytes()


def take_independent_screenshot(save_dir: str) -> dict:
    """
    触发 Windows 截图栏并监控剪贴板变化
    - 使用 Windows SendInput API 发送 Win+Shift+S（系统级，不依赖焦点）
    - 纯粹依赖剪贴板变化检测截图完成
    - 最多等待 60 秒，超时才判定取消
    """
    try:
        save_dir_path = Path(save_dir)
        save_dir_path.mkdir(parents=True, exist_ok=True)

        # 记录初始剪贴板状态
        initial_image = get_clipboard_image()
        print(f"[DEBUG] 初始剪贴板图片: {'有图片' if initial_image else '无图片'}", file=sys.stderr)

        # 发送 Win+Shift+S
        if not send_win_shift_s():
            return {'success': False, 'error': 'Failed to send Win+Shift+S'}

        print("[DEBUG] 已触发截图栏，等待用户截图...", file=sys.stderr)

        # 每 0.3 秒检查一次剪贴板，最多等待 60 秒
        max_wait_seconds = 60
        check_interval = 0.3
        max_checks = int(max_wait_seconds / check_interval)

        for i in range(max_checks):
            time.sleep(check_interval)

            current_image = get_clipboard_image()

            if current_image is not None and not images_equal(current_image, initial_image):
                guid = str(uuid.uuid4())
                save_path = save_dir_path / f"{guid}.png"
                current_image.save(str(save_path), 'PNG')
                elapsed = round((i + 1) * check_interval, 1)
                print(f"[DEBUG] 截图成功，耗时 {elapsed} 秒，保存至: {save_path}", file=sys.stderr)
                return {
                    'success': True,
                    'path': str(save_path),
                    'width': current_image.width,
                    'height': current_image.height,
                    'message': 'Screenshot saved successfully'
                }

        # 60 秒超时，用户取消
        print("[DEBUG] 等待超时（60秒），用户未完成截图", file=sys.stderr)
        return {
            'success': False,
            'error': 'timeout',
            'cancelled': True
        }

    except Exception as e:
        print(f"[DEBUG] 异常: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'success': False, 'error': 'No save directory specified'}))
        sys.exit(1)

    save_dir = sys.argv[1]
    result = take_independent_screenshot(save_dir)
    print(json.dumps(result))
    sys.exit(0 if result.get('success') else 1)
