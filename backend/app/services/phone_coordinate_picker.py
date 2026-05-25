"""手机坐标选择器

用 Win32 低级鼠标钩子（WH_MOUSE_LL）拦截 Ctrl+左键 单击，**直接吞掉事件**让 scrcpy 收不到，
手机不会触发点击；普通点击（不按 Ctrl）则透传给系统让 scrcpy 正常工作。
键盘检测继续用 pynput（只读，不需要拦截）。
"""
from typing import Optional, Tuple, Callable
import ctypes
from ctypes import wintypes
import threading
import win32gui
from pynput import keyboard

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


# ===== Windows API 常量与签名 =====
WH_MOUSE_LL = 14
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_QUIT = 0x0012
HC_ACTION = 0


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
    ]


# 钩子过程类型
LowLevelMouseProc = ctypes.WINFUNCTYPE(
    ctypes.c_long,
    ctypes.c_int,            # nCode
    wintypes.WPARAM,         # wParam
    wintypes.LPARAM,         # lParam (指向 MSLLHOOKSTRUCT)
)


# 加载库
_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

_user32.SetWindowsHookExW.restype = wintypes.HHOOK
_user32.SetWindowsHookExW.argtypes = [
    ctypes.c_int, LowLevelMouseProc, wintypes.HINSTANCE, wintypes.DWORD,
]
_user32.CallNextHookEx.restype = ctypes.c_long
_user32.CallNextHookEx.argtypes = [
    wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM,
]
_user32.UnhookWindowsHookEx.restype = wintypes.BOOL
_user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
_user32.GetMessageW.restype = wintypes.BOOL
_user32.GetMessageW.argtypes = [
    ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT,
]
_user32.PostThreadMessageW.restype = wintypes.BOOL
_user32.PostThreadMessageW.argtypes = [
    wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
]
_kernel32.GetCurrentThreadId.restype = wintypes.DWORD


class PhoneCoordinatePicker:
    """坐标选择器：Ctrl+左键 拾取并吞掉事件；普通点击透传到 scrcpy"""

    def __init__(self):
        self.is_active = False
        self.ctrl_pressed = False
        self.scrcpy_hwnd: Optional[int] = None
        self.picked_coordinate: Optional[Tuple[int, int]] = None
        self.callback: Optional[Callable[[int, int], None]] = None
        # 手机分辨率
        self.phone_width: Optional[int] = None
        self.phone_height: Optional[int] = None
        # 钩子相关
        self._hook_thread: Optional[threading.Thread] = None
        self._hook_thread_id: Optional[int] = None
        self._hook_handle = None
        self._hook_proc_ref = None  # 保留 ctypes 回调引用，避免被 GC
        # 键盘 listener（监听 Ctrl）
        self._keyboard_listener: Optional[keyboard.Listener] = None

    # ===== 配置 =====
    def set_phone_resolution(self, width: int, height: int):
        self.phone_width = width
        self.phone_height = height
        print(f"[坐标选择器] 手机分辨率: {width}x{height}")

    def find_scrcpy_window(self) -> Optional[int]:
        """查找 Scrcpy 窗口"""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "手机" in title:
                    windows.append((hwnd, title))
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        return windows[0][0] if windows else None

    # ===== 坐标换算（含 letterbox 处理） =====
    def _client_to_phone(self, client_x: int, client_y: int, client_w: int, client_h: int) -> Optional[Tuple[int, int]]:
        if not (self.phone_width and self.phone_height):
            return None

        window_is_landscape = client_w >= client_h
        phone_is_landscape = self.phone_width >= self.phone_height
        if window_is_landscape != phone_is_landscape:
            phone_w, phone_h = self.phone_height, self.phone_width
        else:
            phone_w, phone_h = self.phone_width, self.phone_height

        phone_aspect = phone_w / phone_h
        client_aspect = client_w / client_h
        if client_aspect > phone_aspect:
            rh = client_h
            rw = int(round(rh * phone_aspect))
            rx = (client_w - rw) // 2
            ry = 0
        else:
            rw = client_w
            rh = int(round(rw / phone_aspect))
            rx = 0
            ry = (client_h - rh) // 2

        inner_x = max(0, min(client_x - rx, rw - 1))
        inner_y = max(0, min(client_y - ry, rh - 1))
        phone_x = int(round(inner_x * phone_w / rw))
        phone_y = int(round(inner_y * phone_h / rh))
        phone_x = max(0, min(phone_x, phone_w - 1))
        phone_y = max(0, min(phone_y, phone_h - 1))
        return (phone_x, phone_y)

    def get_window_coordinate(self, hwnd: Optional[int], screen_x: int, screen_y: int) -> Optional[Tuple[int, int]]:
        """屏幕坐标 → 手机坐标（保留为兼容旧 API）"""
        if not hwnd or not self.phone_width or not self.phone_height:
            return None
        try:
            origin = win32gui.ClientToScreen(hwnd, (0, 0))
            rect = win32gui.GetClientRect(hwnd)
            cw, ch = max(1, rect[2]), max(1, rect[3])
            rx, ry = screen_x - origin[0], screen_y - origin[1]
            if not (0 <= rx < cw and 0 <= ry < ch):
                return None
            return self._client_to_phone(rx, ry, cw, ch)
        except Exception as e:
            print(f"[坐标选择器] get_window_coordinate 错误: {e}")
            return None

    # ===== 鼠标低级钩子 =====
    def _on_mouse_event(self, n_code, w_param, l_param) -> int:
        """低级鼠标钩子回调，运行在钩子线程中"""
        if n_code != HC_ACTION or not self.is_active:
            return _user32.CallNextHookEx(self._hook_handle, n_code, w_param, l_param)

        # 只关注左键按下 + Ctrl 已按下
        if w_param == WM_LBUTTONDOWN and self.ctrl_pressed:
            try:
                ms = ctypes.cast(l_param, ctypes.POINTER(MSLLHOOKSTRUCT))[0]
                screen_x, screen_y = ms.pt.x, ms.pt.y

                if not self.scrcpy_hwnd:
                    self.scrcpy_hwnd = self.find_scrcpy_window()

                if self.scrcpy_hwnd:
                    origin = win32gui.ClientToScreen(self.scrcpy_hwnd, (0, 0))
                    rect = win32gui.GetClientRect(self.scrcpy_hwnd)
                    client_w = max(1, rect[2])
                    client_h = max(1, rect[3])
                    cx = screen_x - origin[0]
                    cy = screen_y - origin[1]
                    if 0 <= cx < client_w and 0 <= cy < client_h:
                        # 在 scrcpy 客户区内：换算坐标 + 吞掉事件
                        phone_xy = self._client_to_phone(cx, cy, client_w, client_h)
                        if phone_xy:
                            self.picked_coordinate = phone_xy
                            print(f"[坐标选择器] ✅ 拾取(已拦截) → 手机({phone_xy[0]}, {phone_xy[1]})")
                            if self.callback:
                                try:
                                    self.callback(*phone_xy)
                                except Exception:
                                    pass
                        # 返回非 0 表示已处理，事件不再向下传递（scrcpy 收不到）
                        return 1
            except Exception as e:
                print(f"[坐标选择器] 钩子回调异常: {e}")
                # 异常时不要吞事件，让 scrcpy 正常处理
                return _user32.CallNextHookEx(self._hook_handle, n_code, w_param, l_param)

        # Ctrl + 左键松开：也吞掉避免 scrcpy 收到孤立的 UP 事件
        if w_param == WM_LBUTTONUP and self.ctrl_pressed:
            return 1

        return _user32.CallNextHookEx(self._hook_handle, n_code, w_param, l_param)

    def _hook_thread_main(self):
        """钩子线程：装钩子 + 跑消息泵 + 卸钩子"""
        self._hook_thread_id = _kernel32.GetCurrentThreadId()
        # 注意：低级钩子的回调必须保持引用，否则会被 GC
        self._hook_proc_ref = LowLevelMouseProc(self._on_mouse_event)
        try:
            self._hook_handle = _user32.SetWindowsHookExW(
                WH_MOUSE_LL,
                self._hook_proc_ref,
                None,  # 全局钩子允许 hMod=NULL（仅在该线程内安装）
                0,
            )
            if not self._hook_handle:
                err = ctypes.get_last_error()
                print(f"[坐标选择器] 安装鼠标钩子失败 err={err}")
                return

            # 消息循环（必须有，否则低级钩子不会被调用）
            msg = wintypes.MSG()
            while True:
                ret = _user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret == 0 or ret == -1:  # WM_QUIT or error
                    break
                _user32.TranslateMessage(ctypes.byref(msg)) if hasattr(_user32, "TranslateMessage") else None
                _user32.DispatchMessageW(ctypes.byref(msg)) if hasattr(_user32, "DispatchMessageW") else None
        finally:
            if self._hook_handle:
                try:
                    _user32.UnhookWindowsHookEx(self._hook_handle)
                except Exception:
                    pass
                self._hook_handle = None
            self._hook_thread_id = None

    # ===== 键盘监听（pynput，只读 Ctrl 状态） =====
    def _on_key_press(self, key):
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
            elif key == keyboard.Key.esc:
                self.stop()
        except Exception:
            pass

    def _on_key_release(self, key):
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = False
        except Exception:
            pass

    # ===== 生命周期 =====
    def start(self, callback: Optional[Callable[[int, int], None]] = None):
        # 即便已激活也清空旧坐标，让下次"开始拾取"是干净状态
        self.picked_coordinate = None
        self.callback = callback
        if self.is_active:
            return

        self.is_active = True
        self.scrcpy_hwnd = self.find_scrcpy_window()

        # 启动鼠标钩子线程
        self._hook_thread = threading.Thread(target=self._hook_thread_main, daemon=True, name="PhoneCoordPicker-Hook")
        self._hook_thread.start()

        # 键盘监听
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._keyboard_listener.start()

        print("[坐标选择器] 已启动（低级鼠标钩子模式：Ctrl+点击 拾取并拦截）")

    def stop(self):
        if not self.is_active:
            return
        self.is_active = False

        # 给钩子线程 PostThreadMessage(WM_QUIT) 让它退出消息泵
        if self._hook_thread_id:
            try:
                _user32.PostThreadMessageW(self._hook_thread_id, WM_QUIT, 0, 0)
            except Exception:
                pass
        if self._hook_thread:
            try:
                self._hook_thread.join(timeout=1.0)
            except Exception:
                pass
            self._hook_thread = None

        if self._keyboard_listener:
            try:
                self._keyboard_listener.stop()
            except Exception:
                pass
            self._keyboard_listener = None

        self.ctrl_pressed = False
        print("[坐标选择器] 已停止")

    def get_picked_coordinate(self) -> Optional[Tuple[int, int]]:
        return self.picked_coordinate


_picker: Optional[PhoneCoordinatePicker] = None


def get_coordinate_picker() -> PhoneCoordinatePicker:
    global _picker
    if _picker is None:
        _picker = PhoneCoordinatePicker()
    return _picker
