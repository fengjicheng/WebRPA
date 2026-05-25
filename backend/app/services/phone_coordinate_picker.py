"""手机坐标选择器 - 最终方案：正确的坐标转换"""
from typing import Optional, Tuple, Callable
import win32gui
import ctypes
from pynput import mouse, keyboard

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


class PhoneCoordinatePicker:
    """坐标选择器 - 正确处理坐标转换"""
    
    def __init__(self):
        self.is_active = False
        self.ctrl_pressed = False
        self.scrcpy_hwnd: Optional[int] = None
        self.picked_coordinate: Optional[Tuple[int, int]] = None
        self.mouse_listener: Optional[mouse.Listener] = None
        self.keyboard_listener: Optional[keyboard.Listener] = None
        self.callback: Optional[Callable[[int, int], None]] = None
        # 手机分辨率
        self.phone_width: Optional[int] = None
        self.phone_height: Optional[int] = None
        
    def set_phone_resolution(self, width: int, height: int):
        """设置手机分辨率"""
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
    
    def on_click(self, x: int, y: int, button, pressed: bool):
        """鼠标点击 → 转换为手机坐标

        正确处理：
        1. DPI 缩放：win32gui.ClientToScreen / GetClientRect 在 PerMonitorV2 DPI 下返回的就是物理像素，
           而 pynput 给的鼠标坐标也是物理像素，所以两者对齐
        2. **黑边/letterbox**：scrcpy 会保持手机宽高比，在 client area 居中渲染，多余空间是黑边。
           必须先求出"手机画面真实矩形"再做映射，否则点黑边或边缘会偏几十像素
        3. 旋转：手机横竖屏切换时窗口会重布局，按 client area 当前宽高比与手机分辨率对比来判断
        """
        if not self.is_active or button != mouse.Button.left or not pressed or not self.ctrl_pressed:
            return

        if not self.scrcpy_hwnd:
            self.scrcpy_hwnd = self.find_scrcpy_window()

        if not (self.scrcpy_hwnd and self.phone_width and self.phone_height):
            return

        try:
            # 客户区位置 + 尺寸
            origin = win32gui.ClientToScreen(self.scrcpy_hwnd, (0, 0))
            client_rect = win32gui.GetClientRect(self.scrcpy_hwnd)
            client_w = max(1, client_rect[2])
            client_h = max(1, client_rect[3])

            relative_x = x - origin[0]
            relative_y = y - origin[1]
            if not (0 <= relative_x < client_w and 0 <= relative_y < client_h):
                return  # 点在窗口外

            # 决定实际的手机分辨率方向（横/竖屏）：以窗口方向为准
            window_is_landscape = client_w >= client_h
            phone_is_landscape = self.phone_width >= self.phone_height
            if window_is_landscape != phone_is_landscape:
                phone_w = self.phone_height
                phone_h = self.phone_width
            else:
                phone_w = self.phone_width
                phone_h = self.phone_height

            # 关键：scrcpy 在 client area 内保持手机宽高比居中渲染（letterbox/pillarbox）
            # 计算手机画面的真实渲染矩形 (rx, ry, rw, rh)
            phone_aspect = phone_w / phone_h
            client_aspect = client_w / client_h
            if client_aspect > phone_aspect:
                # 客户区比手机更宽 → 上下贴边、两侧黑边
                rh = client_h
                rw = int(round(rh * phone_aspect))
                rx = (client_w - rw) // 2
                ry = 0
            else:
                # 客户区比手机更窄 → 左右贴边、上下黑边
                rw = client_w
                rh = int(round(rw / phone_aspect))
                rx = 0
                ry = (client_h - rh) // 2

            # 点击位置相对于"手机画面真实矩形"
            inner_x = relative_x - rx
            inner_y = relative_y - ry
            if not (0 <= inner_x < rw and 0 <= inner_y < rh):
                # 点在黑边上，按用户习惯就近 clamp 到边缘（不要拒绝）
                inner_x = max(0, min(inner_x, rw - 1))
                inner_y = max(0, min(inner_y, rh - 1))

            # 按比例映射到手机坐标
            phone_x = int(round(inner_x * phone_w / rw))
            phone_y = int(round(inner_y * phone_h / rh))
            phone_x = max(0, min(phone_x, phone_w - 1))
            phone_y = max(0, min(phone_y, phone_h - 1))

            print(f"[坐标选择器] ✅ client=({client_w}x{client_h}) inner=({rw}x{rh}@{rx},{ry}) → 手机({phone_x}, {phone_y})")
            self.picked_coordinate = (phone_x, phone_y)
            if self.callback:
                self.callback(phone_x, phone_y)
        except Exception as e:
            print(f"[坐标选择器] 错误: {e}")
            import traceback
            traceback.print_exc()
    
    def on_key_press(self, key):
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
            elif key == keyboard.Key.esc:
                self.stop()
        except Exception:
            pass
    
    def on_key_release(self, key):
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = False
        except Exception:
            pass
    
    def start(self, callback: Optional[Callable[[int, int], None]] = None):
        if self.is_active:
            return
        
        self.is_active = True
        self.picked_coordinate = None
        self.callback = callback
        self.scrcpy_hwnd = self.find_scrcpy_window()
        
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.mouse_listener.start()
        
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.keyboard_listener.start()
        
        print("[坐标选择器] 已启动")
    
    def stop(self):
        if not self.is_active:
            return
        
        self.is_active = False
        
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        print("[坐标选择器] 已停止")
    
    def get_picked_coordinate(self) -> Optional[Tuple[int, int]]:
        return self.picked_coordinate

    def get_window_coordinate(self, hwnd: Optional[int], screen_x: int, screen_y: int) -> Optional[Tuple[int, int]]:
        """屏幕坐标 → 手机坐标（含 letterbox 处理，与 on_click 逻辑一致）"""
        if not hwnd or not self.phone_width or not self.phone_height:
            return None
        try:
            origin = win32gui.ClientToScreen(hwnd, (0, 0))
            client_rect = win32gui.GetClientRect(hwnd)
            client_w = max(1, client_rect[2])
            client_h = max(1, client_rect[3])

            relative_x = screen_x - origin[0]
            relative_y = screen_y - origin[1]
            if not (0 <= relative_x < client_w and 0 <= relative_y < client_h):
                return None

            window_is_landscape = client_w >= client_h
            phone_is_landscape = self.phone_width >= self.phone_height
            if window_is_landscape != phone_is_landscape:
                phone_w = self.phone_height
                phone_h = self.phone_width
            else:
                phone_w = self.phone_width
                phone_h = self.phone_height

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

            inner_x = max(0, min(relative_x - rx, rw - 1))
            inner_y = max(0, min(relative_y - ry, rh - 1))
            phone_x = int(round(inner_x * phone_w / rw))
            phone_y = int(round(inner_y * phone_h / rh))
            phone_x = max(0, min(phone_x, phone_w - 1))
            phone_y = max(0, min(phone_y, phone_h - 1))
            return (phone_x, phone_y)
        except Exception as e:
            print(f"[坐标选择器] get_window_coordinate 错误: {e}")
            return None


_picker: Optional[PhoneCoordinatePicker] = None

def get_coordinate_picker() -> PhoneCoordinatePicker:
    global _picker
    if _picker is None:
        _picker = PhoneCoordinatePicker()
    return _picker
