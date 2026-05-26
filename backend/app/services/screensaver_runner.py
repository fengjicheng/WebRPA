"""屏保弹幕子进程入口（基于 Win32 API + GDI）

WebRPA 内置的 Python313 是嵌入式精简版，不带 tkinter。
所以这里改用 pywin32 直接画 Win32 全屏窗口，实测可用。

支持的内容类型：
- text       静态文本
- scroll     滚动文本（左/右/上/下，速度可调）
- clock      实时时钟（自定义 strftime）
- date       实时日期
- countdown  倒计时
- bullet     多条弹幕随机轨迹
"""
import argparse
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import win32api
    import win32con
    import win32gui
    import win32ui
except Exception as e:
    print(f"[Screensaver] pywin32 不可用：{e}", file=sys.stderr)
    sys.exit(1)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    return p.parse_args()


def load_config(path: str) -> dict:
    fp = Path(path)
    if not fp.exists():
        return {}
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[Screensaver] 配置解析失败：{e}", file=sys.stderr)
        return {}


def hex_to_rgb(h: str):
    h = (h or "#ffffff").strip()
    if h.startswith("#"):
        h = h[1:]
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return (255, 255, 255)
    try:
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return (255, 255, 255)


def rgb_to_colorref(rgb):
    """Win32 COLORREF: 0x00BBGGRR"""
    r, g, b = rgb
    return r | (g << 8) | (b << 16)


# 退出快捷键 → VK
EXIT_HOTKEY_VK = {
    "Escape": 0x1B,
    "Esc": 0x1B,
    "F12": 0x7B,
    "space": 0x20,
    "Space": 0x20,
}


class Screensaver:
    """纯 Win32 全屏屏保窗口"""

    def __init__(self, config: dict):
        self.config = config
        self.hwnd = None
        self.running = True
        self._start_time = time.time()

        # 窗口尺寸（全屏）
        self.sw = win32api.GetSystemMetrics(0)  # SM_CXSCREEN
        self.sh = win32api.GetSystemMetrics(1)  # SM_CYSCREEN

        # 字段读取
        c = self.config
        self.content_type: str = c.get("content_type", "scroll")
        self.text: str = c.get("text", "WebRPA")
        # 旧字段兼容（曾经 clock/date 共用 datetime_format）
        self.datetime_format: str = c.get("datetime_format", "")
        # 新字段：clock 和 date 各自独立的格式
        self.clock_format: str = c.get("clock_format", "") or self.datetime_format
        self.date_format: str = c.get("date_format", "") or self.datetime_format
        self.countdown_target: str = c.get("countdown_target", "")
        self.bullets: list[dict] = c.get("bullets", []) or []

        self.font_family: str = c.get("font_family", "Microsoft YaHei")
        self.font_size: int = int(c.get("font_size", 64) or 64)
        self.font_weight: str = c.get("font_weight", "normal")
        self.font_italic: bool = bool(c.get("font_italic", False))
        self.color: tuple = hex_to_rgb(c.get("color", "#ffffff"))
        self.background: tuple = hex_to_rgb(c.get("background", "#000000"))
        self.background_alpha: float = float(c.get("background_alpha", 1.0) or 1.0)
        self.outline_color: str = c.get("outline_color", "") or ""
        self.outline_width: int = int(c.get("outline_width", 0) or 0)

        self.scroll_direction: str = c.get("scroll_direction", "left")
        self.scroll_speed: int = int(c.get("scroll_speed", 200) or 200)
        self.scroll_loop: bool = bool(c.get("scroll_loop", True))

        self.click_through: bool = bool(c.get("click_through", False))
        self.show_close_hint: bool = bool(c.get("show_close_hint", True))
        self.exit_hotkey: str = c.get("exit_hotkey") or "Escape"
        self.exit_vk: int = EXIT_HOTKEY_VK.get(self.exit_hotkey, 0x1B)
        self.vertical_text: bool = bool(c.get("vertical_text", False))
        # 旋转角度（0/90/180/270），仅文字渲染层支持
        self.rotation: int = int(c.get("rotation", 0) or 0) % 360
        # 是否全屏覆盖；为 False 时窗口居中、占屏幕 50%
        self.fullscreen: bool = bool(c.get("fullscreen", True))

        # 滚动状态
        self._scroll_x = 0.0
        self._scroll_y = 0.0
        self._text_width = 0
        self._text_height = 0
        self._inited_pos = False

        # bullet 状态：[{"text", "x", "y", "speed", "color", "size", "bold"}]
        self._bullet_states: list[dict] = []

        # 双击退出检测
        self._last_click_time = 0.0

        # ===== GDI 资源缓存（避免每帧重建，是丝滑的关键）=====
        # 后台 DC、位图、字体、画刷在 create_window 后初始化，整个生命周期复用
        self._mem_dc = None
        self._mem_bmp = None
        self._mem_old_bmp = None
        self._cached_font = None  # 主字体（按 font_size/bold/italic/rotation 缓存）
        self._cached_bg_brush = None  # 背景画刷
        self._cached_close_font = None  # 关闭提示小字体
        self._bullet_font_cache: dict = {}  # (size, bold, italic) -> hfont

        # ===== 滚动条带预渲染缓存（核心丝滑技术）=====
        # 把整段文本预先画到一个比屏幕大很多的"条带位图"上，
        # 每帧只做 1 次 BitBlt(取条带的一段贴屏幕)。
        # 这是 8/16 位时代游戏平滑滚动的经典做法，CPU 几乎不消耗。
        self._strip_dc = None        # 条带的内存 DC
        self._strip_bmp = None       # 条带位图
        self._strip_old_bmp = None
        self._strip_w = 0            # 条带宽度
        self._strip_h = 0            # 条带高度（水平滚动时 = 屏高，垂直滚动时 = 屏宽）
        self._strip_text_w = 0       # 条带中文本本身宽度
        self._strip_text_h = 0       # 文本高度
        self._strip_initialized = False
        self._strip_text_cache = ""  # 上次渲染时的文本，变了要重建

    # ===== 文本生成 =====

    def _format_clock(self) -> str:
        if self.clock_format:
            try:
                return self._zh_strftime(self.clock_format, datetime.now())
            except Exception:
                pass
        return datetime.now().strftime("%H:%M:%S")

    def _format_date(self) -> str:
        if self.date_format:
            try:
                return self._zh_strftime(self.date_format, datetime.now())
            except Exception:
                pass
        return self._zh_strftime("%Y-%m-%d %A", datetime.now())

    @staticmethod
    def _zh_strftime(fmt: str, dt: datetime) -> str:
        """中文版 strftime：把 %A/%a/%B/%b/%p 显式映射成中文，其余交给 datetime.strftime。

        系统 locale 在嵌入式 Python 上不可靠（很多打包环境是英文 locale），所以这里直接做替换。
        """
        zh_weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        zh_weekday_short = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        zh_month = ["一月", "二月", "三月", "四月", "五月", "六月",
                    "七月", "八月", "九月", "十月", "十一月", "十二月"]
        zh_ampm = "上午" if dt.hour < 12 else "下午"

        # 用占位符把要中文化的字段先替换出来，避免和 strftime 冲突
        # 然后再 strftime 余下部分
        marker_a = "\u0001A\u0001"
        marker_a2 = "\u0001a\u0001"
        marker_B = "\u0001B\u0001"
        marker_b = "\u0001b\u0001"
        marker_p = "\u0001p\u0001"

        replaced = (fmt
                    .replace("%A", marker_a)
                    .replace("%a", marker_a2)
                    .replace("%B", marker_B)
                    .replace("%b", marker_b)
                    .replace("%p", marker_p))
        try:
            out = dt.strftime(replaced)
        except Exception:
            out = replaced

        return (out
                .replace(marker_a, zh_weekday[dt.weekday()])
                .replace(marker_a2, zh_weekday_short[dt.weekday()])
                .replace(marker_B, zh_month[dt.month - 1])
                .replace(marker_b, zh_month[dt.month - 1])
                .replace(marker_p, zh_ampm))

    def _format_countdown(self) -> str:
        if not self.countdown_target:
            return "未设置目标时间"
        try:
            target = datetime.fromisoformat(self.countdown_target)
        except Exception:
            return "目标时间格式错误"
        delta = target - datetime.now()
        if delta.total_seconds() <= 0:
            return "时间到！"
        days = delta.days
        h, rem = divmod(delta.seconds, 3600)
        m, s = divmod(rem, 60)
        if days > 0:
            return f"{days} 天 {h:02d}:{m:02d}:{s:02d}"
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _current_text(self) -> str:
        ct = self.content_type
        if ct == "clock":
            return self._format_clock()
        if ct == "date":
            return self._format_date()
        if ct == "countdown":
            return self._format_countdown()
        if ct == "scroll":
            return self.text or ""
        # text / 其他
        return self.text or "WebRPA"


    def _make_font(self, size: int = None, bold: bool = None, italic: bool = None):
        """创建 GDI 字体"""
        lf = win32gui.LOGFONT()
        lf.lfHeight = -(size if size is not None else self.font_size)
        if bold is None:
            bold = self.font_weight == "bold"
        lf.lfWeight = win32con.FW_BOLD if bold else win32con.FW_NORMAL
        lf.lfItalic = 1 if (italic if italic is not None else self.font_italic) else 0
        lf.lfFaceName = self.font_family
        lf.lfCharSet = win32con.DEFAULT_CHARSET
        lf.lfQuality = win32con.CLEARTYPE_QUALITY
        # 字体旋转（GDI 单位是 1/10 度，逆时针为正；UI 上"90°顺时针"对应 lfEscapement = 2700）
        if self.rotation:
            angle_tenths = ((360 - int(self.rotation)) % 360) * 10
            lf.lfEscapement = angle_tenths
            lf.lfOrientation = angle_tenths
        return win32gui.CreateFontIndirect(lf)

    def _init_gdi_resources(self):
        """创建后台 DC/位图/字体/画刷一次，整个屏保生命周期内复用。
        这是滚动文本无卡顿的关键 - 避免每帧 60 次的 GDI 资源创建/销毁。"""
        if self._mem_dc is not None:
            return
        screen_dc = win32gui.GetDC(self.hwnd)
        try:
            self._mem_dc = win32gui.CreateCompatibleDC(screen_dc)
            self._mem_bmp = win32gui.CreateCompatibleBitmap(screen_dc, self.sw, self.sh)
        finally:
            win32gui.ReleaseDC(self.hwnd, screen_dc)
        self._mem_old_bmp = win32gui.SelectObject(self._mem_dc, self._mem_bmp)

        # 后台 DC 默认设置一次
        win32gui.SetBkMode(self._mem_dc, win32con.TRANSPARENT)

        # 主字体
        self._cached_font = self._make_font()
        # 背景画刷
        self._cached_bg_brush = win32gui.CreateSolidBrush(rgb_to_colorref(self.background))
        # 关闭提示字体
        self._cached_close_font = self._make_font(size=14, bold=False, italic=False)

    def _release_gdi_resources(self):
        """退出时释放（一次性）"""
        try:
            if self._mem_dc and self._mem_old_bmp:
                win32gui.SelectObject(self._mem_dc, self._mem_old_bmp)
            if self._mem_bmp:
                win32gui.DeleteObject(self._mem_bmp)
            if self._mem_dc:
                win32gui.DeleteDC(self._mem_dc)
            if self._cached_font:
                win32gui.DeleteObject(self._cached_font)
            if self._cached_bg_brush:
                win32gui.DeleteObject(self._cached_bg_brush)
            if self._cached_close_font:
                win32gui.DeleteObject(self._cached_close_font)
            for f in self._bullet_font_cache.values():
                try:
                    win32gui.DeleteObject(f)
                except Exception:
                    pass
            self._bullet_font_cache.clear()
            # 释放滚动条带
            self._release_strip()
        except Exception:
            pass
        self._mem_dc = None
        self._mem_bmp = None
        self._mem_old_bmp = None
        self._cached_font = None
        self._cached_bg_brush = None
        self._cached_close_font = None

    def _release_strip(self):
        try:
            if self._strip_dc and self._strip_old_bmp:
                win32gui.SelectObject(self._strip_dc, self._strip_old_bmp)
            if self._strip_bmp:
                win32gui.DeleteObject(self._strip_bmp)
            if self._strip_dc:
                win32gui.DeleteDC(self._strip_dc)
        except Exception:
            pass
        self._strip_dc = None
        self._strip_bmp = None
        self._strip_old_bmp = None
        self._strip_initialized = False

    def _build_scroll_strip(self):
        """预渲染滚动条带：把一份完整文本（带描边）画到一个超长位图上，
        水平滚动时条带宽 = 屏幕宽 + 文本宽（前后各留一个屏，循环滚出/滚入）；
        垂直滚动时条带高 = 屏幕高 + 文本高。
        每帧只 BitBlt 一次屏幕区域过去 → 超丝滑。"""
        # 释放旧条带（文本变化时用）
        self._release_strip()

        text = self._current_text() or "WebRPA"
        self._strip_text_cache = text

        # 用一个临时 DC 测算文本尺寸（必须先 SelectObject 字体）
        screen_dc = win32gui.GetDC(self.hwnd)
        try:
            tmp_dc = win32gui.CreateCompatibleDC(screen_dc)
            old_font = win32gui.SelectObject(tmp_dc, self._cached_font)
            try:
                tw, th = win32gui.GetTextExtentPoint32(tmp_dc, text)
            except Exception:
                tw, th = self.font_size * len(text), self.font_size
            win32gui.SelectObject(tmp_dc, old_font)
            win32gui.DeleteDC(tmp_dc)
        finally:
            win32gui.ReleaseDC(self.hwnd, screen_dc)

        self._strip_text_w = tw
        self._strip_text_h = th

        is_horizontal = self.scroll_direction in ("left", "right")
        if is_horizontal:
            # 文本前后各留一个屏宽 → 循环时无缝衔接
            self._strip_w = self.sw + tw + self.sw  # 屏 + 文本 + 屏
            self._strip_h = self.sh
            text_x = self.sw  # 文本起点：第一个屏宽之后
            text_y = (self.sh - th) // 2
        else:
            self._strip_w = self.sw
            self._strip_h = self.sh + th + self.sh
            text_x = (self.sw - tw) // 2
            text_y = self.sh

        # 创建条带 DC + 位图（与屏幕兼容，可走 GPU 加速）
        screen_dc = win32gui.GetDC(self.hwnd)
        try:
            self._strip_dc = win32gui.CreateCompatibleDC(screen_dc)
            self._strip_bmp = win32gui.CreateCompatibleBitmap(screen_dc, self._strip_w, self._strip_h)
        finally:
            win32gui.ReleaseDC(self.hwnd, screen_dc)
        self._strip_old_bmp = win32gui.SelectObject(self._strip_dc, self._strip_bmp)

        # 填背景
        win32gui.FillRect(self._strip_dc, (0, 0, self._strip_w, self._strip_h), self._cached_bg_brush)

        # 绘制文本（带描边）
        win32gui.SetBkMode(self._strip_dc, win32con.TRANSPARENT)
        old_font = win32gui.SelectObject(self._strip_dc, self._cached_font)

        if self.outline_color and self.outline_width > 0:
            try:
                outline_rgb = hex_to_rgb(self.outline_color)
                ow = max(1, min(6, self.outline_width))
                win32gui.SetTextColor(self._strip_dc, rgb_to_colorref(outline_rgb))
                for dx in range(-ow, ow + 1):
                    for dy in range(-ow, ow + 1):
                        if dx == 0 and dy == 0:
                            continue
                        win32gui.ExtTextOut(self._strip_dc, text_x + dx, text_y + dy, 0, None, text)
            except Exception:
                pass

        win32gui.SetTextColor(self._strip_dc, rgb_to_colorref(self.color))
        win32gui.ExtTextOut(self._strip_dc, text_x, text_y, 0, None, text)
        win32gui.SelectObject(self._strip_dc, old_font)

        self._strip_initialized = True
        # 滚动起始位置：文本完整出现在屏幕上还差一个屏宽 / 高
        if self.scroll_direction == "left":
            self._scroll_x = float(self.sw)  # 从第二屏（文本起点）开始往左
        elif self.scroll_direction == "right":
            self._scroll_x = float(-tw)  # 从屏左外开始
        elif self.scroll_direction == "up":
            self._scroll_y = float(self.sh)
        else:  # down
            self._scroll_y = float(-th)
        self._inited_pos = True

    def _get_bullet_font(self, size: int, bold: bool, italic: bool):
        key = (size, bold, italic)
        f = self._bullet_font_cache.get(key)
        if f is None:
            f = self._make_font(size=size, bold=bold, italic=italic)
            self._bullet_font_cache[key] = f
        return f

    # ===== Win32 窗口生命周期 =====

    def create_window(self):
        message_map = {
            win32con.WM_PAINT: self._on_paint_msg,
            win32con.WM_KEYDOWN: self._on_keydown_msg,
            win32con.WM_LBUTTONDBLCLK: self._on_dblclick_msg,
            win32con.WM_DESTROY: self._on_destroy_msg,
            win32con.WM_ERASEBKGND: self._on_erase_msg,
        }

        wc = win32gui.WNDCLASS()
        wc.lpszClassName = "WebRPAScreensaverCls"
        wc.lpfnWndProc = message_map
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.style = 0x0008 | 0x0001 | 0x0002  # CS_DBLCLKS | CS_VREDRAW | CS_HREDRAW
        wc.hbrBackground = win32con.COLOR_WINDOW + 1  # 系统标准
        try:
            self.cls_atom = win32gui.RegisterClass(wc)
        except Exception as e:
            print(f"[Screensaver] RegisterClass: {e}", file=sys.stderr)
            self.cls_atom = "WebRPAScreensaverCls"

        # 整体风格：弹出式无边框 + 置顶层
        ex_style = win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW
        # 整体透明度（底色和文字一起变透明）
        if self.background_alpha < 1.0:
            ex_style |= win32con.WS_EX_LAYERED
        # 点击穿透
        if self.click_through:
            ex_style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT

        # 计算窗口尺寸：fullscreen=True 全屏，否则居中、占屏幕 50%
        if self.fullscreen:
            win_x, win_y, win_w, win_h = 0, 0, self.sw, self.sh
        else:
            win_w = self.sw // 2
            win_h = self.sh // 2
            win_x = (self.sw - win_w) // 2
            win_y = (self.sh - win_h) // 2
        # 用窗口尺寸覆盖 sw/sh，让所有绘制都基于真实窗口尺寸
        self.sw, self.sh = win_w, win_h

        self.hwnd = win32gui.CreateWindowEx(
            ex_style,
            self.cls_atom,
            "WebRPA Screensaver",
            win32con.WS_POPUP | win32con.WS_VISIBLE,
            win_x, win_y, win_w, win_h,
            0, 0, 0, None,
        )

        if (ex_style & win32con.WS_EX_LAYERED) and not self.click_through:
            # 仅整体透明
            alpha = max(13, min(255, int(255 * self.background_alpha)))
            win32gui.SetLayeredWindowAttributes(
                self.hwnd, 0, alpha, win32con.LWA_ALPHA
            )
        elif self.click_through:
            # 点击穿透 + 用 colorkey（背景色透明）
            win32gui.SetLayeredWindowAttributes(
                self.hwnd, rgb_to_colorref(self.background), 0, win32con.LWA_COLORKEY
            )

        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
        win32gui.UpdateWindow(self.hwnd)
        # 强制置顶到最前
        try:
            win32gui.SetForegroundWindow(self.hwnd)
        except Exception:
            pass

    def _on_paint_msg(self, hwnd, msg, wparam, lparam):
        self.on_paint(hwnd)
        return 0

    def _on_keydown_msg(self, hwnd, msg, wparam, lparam):
        if wparam == self.exit_vk:
            self.exit()
        return 0

    def _on_dblclick_msg(self, hwnd, msg, wparam, lparam):
        self.exit()
        return 0

    def _on_destroy_msg(self, hwnd, msg, wparam, lparam):
        win32gui.PostQuitMessage(0)
        self.running = False
        return 0

    def _on_erase_msg(self, hwnd, msg, wparam, lparam):
        # 让 OnPaint 自己处理背景，避免闪烁
        return 1


    # ===== 绘制（双缓冲，无闪烁） =====

    def on_paint(self, hwnd):
        # pywin32 的 BeginPaint 返回 (hdc, PAINTSTRUCT 元组)
        hdc, ps = win32gui.BeginPaint(hwnd)
        try:
            self._draw_to_hdc(hdc)
        except Exception as e:
            print(f"[Screensaver] paint 异常：{e}", file=sys.stderr)
        finally:
            win32gui.EndPaint(hwnd, ps)

    def _draw_to_hdc(self, hdc):
        """绘制一帧到屏幕 DC（双缓冲，复用缓存资源）。
        关键性能点：mem_dc/bitmap/font/brush 都是复用，整帧只做绘制 + BitBlt"""
        # 首次进入或窗口大小变化时初始化资源
        if self._mem_dc is None:
            self._init_gdi_resources()

        mem_dc = self._mem_dc

        # 1. 填背景（用缓存画刷）
        win32gui.FillRect(mem_dc, (0, 0, self.sw, self.sh), self._cached_bg_brush)

        # 2. 设置文字默认色
        win32gui.SetTextColor(mem_dc, rgb_to_colorref(self.color))

        ct = self.content_type
        if ct == "bullet":
            self._draw_bullets(mem_dc)
        else:
            text = self._current_text()
            old_font = win32gui.SelectObject(mem_dc, self._cached_font)
            self._draw_main_text(mem_dc, text, ct)
            win32gui.SelectObject(mem_dc, old_font)

        if self.show_close_hint:
            self._draw_close_hint(mem_dc)

        # 3. 一次 BitBlt 到屏幕（GPU 友好的整帧拷贝）
        win32gui.BitBlt(hdc, 0, 0, self.sw, self.sh, mem_dc, 0, 0, win32con.SRCCOPY)

    def _draw_scroll_strip(self, hdc):
        """超快速滚动路径：直接从预渲染条带 BitBlt 一段到屏幕。
        每帧只 1~2 次 BitBlt，无填背景、无字体绘制、无 mem_dc 中转。
        这是丝滑的核心 - CPU 几乎闲置，全靠 GPU/DMA 拷贝。"""
        if not self._strip_initialized or self._strip_text_cache != self._current_text():
            # 文本变了或首次：重建条带
            self._build_scroll_strip()
        if not self._strip_initialized:
            return  # 创建失败，兜底跳过

        sd = self.scroll_direction
        if sd in ("left", "right"):
            # _scroll_x 是文本块在屏幕坐标系中的 X 位置（屏内可见时 0~sw）
            # 条带中文本起点固定在 strip 的 sw 位置，所以从条带的 (sw - scroll_x) 处开始截取屏宽
            # 但因为 _scroll_x 在 [-text_w, sw] 区间循环，需要处理边界
            sx = int(round(self.sw - self._scroll_x))
            # 处理负值或超出条带宽度
            sx = sx % (self.sw + self._strip_text_w)
            # 屏幕需要 sw 像素宽，从条带 sx 开始
            # 如果末端不够 sw，需要拼接一段从 0 开始
            if sx + self.sw <= self._strip_w:
                win32gui.BitBlt(hdc, 0, 0, self.sw, self.sh, self._strip_dc, sx, 0, win32con.SRCCOPY)
            else:
                # 跨越边界（理论上 strip 宽度已足够，这种情况罕见）
                first = self._strip_w - sx
                win32gui.BitBlt(hdc, 0, 0, first, self.sh, self._strip_dc, sx, 0, win32con.SRCCOPY)
                win32gui.BitBlt(hdc, first, 0, self.sw - first, self.sh, self._strip_dc, 0, 0, win32con.SRCCOPY)
        else:
            # 垂直滚动
            sy = int(round(self.sh - self._scroll_y))
            sy = sy % (self.sh + self._strip_text_h)
            if sy + self.sh <= self._strip_h:
                win32gui.BitBlt(hdc, 0, 0, self.sw, self.sh, self._strip_dc, 0, sy, win32con.SRCCOPY)
            else:
                first = self._strip_h - sy
                win32gui.BitBlt(hdc, 0, 0, self.sw, first, self._strip_dc, 0, sy, win32con.SRCCOPY)
                win32gui.BitBlt(hdc, 0, first, self.sw, self.sh - first, self._strip_dc, 0, 0, win32con.SRCCOPY)

        # 关闭提示叠加（频次低，不影响性能）
        if self.show_close_hint:
            self._draw_close_hint(hdc)

    def _draw_main_text(self, hdc, text: str, ct: str):
        # 竖排：每个字符占一行，逐字符向下绘制
        if self.vertical_text and ct != "scroll":
            self._draw_vertical_text(hdc, text)
            return

        # 测算文本尺寸
        try:
            sz = win32gui.GetTextExtentPoint32(hdc, text)
            tw, th = sz
        except Exception:
            tw, th = self.font_size * len(text), self.font_size
        self._text_width = tw
        self._text_height = th

        if ct == "scroll":
            if not self._inited_pos:
                self._init_scroll_pos()
                self._inited_pos = True
            # 用 round 替代 int 截断 - 消除亚像素抖动造成的"卡顿感"
            x = int(round(self._scroll_x))
            y = int(round(self._scroll_y))
        else:
            # 居中
            x = (self.sw - tw) // 2
            y = (self.sh - th) // 2

        # 描边
        if self.outline_color and self.outline_width > 0:
            try:
                outline_rgb = hex_to_rgb(self.outline_color)
                ow = max(1, min(6, self.outline_width))
                old_color = win32gui.SetTextColor(hdc, rgb_to_colorref(outline_rgb))
                for dx in range(-ow, ow + 1):
                    for dy in range(-ow, ow + 1):
                        if dx == 0 and dy == 0:
                            continue
                        win32gui.ExtTextOut(hdc, x + dx, y + dy, 0, None, text)
                win32gui.SetTextColor(hdc, old_color)
            except Exception:
                pass

        win32gui.ExtTextOut(hdc, x, y, 0, None, text)

    def _draw_vertical_text(self, hdc, text: str):
        """竖排：每行一个字符，整体居中"""
        if not text:
            return
        chars = list(text)
        # 测算单字符高度（用首字符）
        try:
            sample = win32gui.GetTextExtentPoint32(hdc, chars[0])
            ch_w, ch_h = sample
        except Exception:
            ch_w, ch_h = self.font_size, self.font_size
        # 行间距：略微紧凑
        line_h = int(ch_h * 1.05)
        total_h = line_h * len(chars)
        x_center = self.sw // 2
        y_start = (self.sh - total_h) // 2

        ow = 0
        outline_rgb = None
        if self.outline_color and self.outline_width > 0:
            try:
                outline_rgb = hex_to_rgb(self.outline_color)
                ow = max(1, min(6, self.outline_width))
            except Exception:
                ow = 0

        text_color = rgb_to_colorref(self.color)
        for i, ch in enumerate(chars):
            try:
                w, _ = win32gui.GetTextExtentPoint32(hdc, ch)
            except Exception:
                w = ch_w
            x = x_center - w // 2
            y = y_start + i * line_h
            if ow and outline_rgb is not None:
                old_c = win32gui.SetTextColor(hdc, rgb_to_colorref(outline_rgb))
                for dx in range(-ow, ow + 1):
                    for dy in range(-ow, ow + 1):
                        if dx == 0 and dy == 0:
                            continue
                        win32gui.ExtTextOut(hdc, x + dx, y + dy, 0, None, ch)
                win32gui.SetTextColor(hdc, old_c)
            win32gui.SetTextColor(hdc, text_color)
            win32gui.ExtTextOut(hdc, x, y, 0, None, ch)

    def _draw_bullets(self, hdc):
        if not self._bullet_states:
            self._init_bullets()
        for b in self._bullet_states:
            font = self._get_bullet_font(b.get("size", self.font_size), b.get("bold", False), False)
            old_font = win32gui.SelectObject(hdc, font)
            old_color = win32gui.SetTextColor(hdc, rgb_to_colorref(b["color"]))
            try:
                # 用 round 替代 int 截断 - 消除亚像素抖动
                win32gui.ExtTextOut(hdc, int(round(b["x"])), int(round(b["y"])), 0, None, b["text"])
            except Exception:
                pass
            win32gui.SetTextColor(hdc, old_color)
            win32gui.SelectObject(hdc, old_font)

    def _draw_close_hint(self, hdc):
        # 关键：直接绘制路径下 hdc 来自 GetDC(hwnd)，未设过 BkMode；
        # 必须显式设为 TRANSPARENT 否则 ExtTextOut 会用白色填充文字背景
        win32gui.SetBkMode(hdc, win32con.TRANSPARENT)
        old_font = win32gui.SelectObject(hdc, self._cached_close_font)
        # 用纯灰色提示文本（不再混合主文字色，避免在彩色背景上不清晰）
        old_color = win32gui.SetTextColor(hdc, rgb_to_colorref((160, 160, 160)))
        text = f"按 {self.exit_hotkey} 或双击屏幕退出"
        try:
            sz = win32gui.GetTextExtentPoint32(hdc, text)
            tw, th = sz
        except Exception:
            tw, th = 200, 18
        win32gui.ExtTextOut(hdc, self.sw - tw - 20, self.sh - th - 20, 0, None, text)
        win32gui.SetTextColor(hdc, old_color)
        win32gui.SelectObject(hdc, old_font)

    def _init_scroll_pos(self):
        if self.scroll_direction == "left":
            self._scroll_x = float(self.sw + 20)
            self._scroll_y = float((self.sh - self._text_height) // 2)
        elif self.scroll_direction == "right":
            self._scroll_x = float(-self._text_width - 20)
            self._scroll_y = float((self.sh - self._text_height) // 2)
        elif self.scroll_direction == "up":
            self._scroll_x = float((self.sw - self._text_width) // 2)
            self._scroll_y = float(self.sh + 20)
        else:  # down
            self._scroll_x = float((self.sw - self._text_width) // 2)
            self._scroll_y = float(-self._text_height - 20)

    def _init_bullets(self):
        for i, b in enumerate(self.bullets):
            text = b.get("text", "")
            if not text:
                continue
            size = int(b.get("font_size", self.font_size) or self.font_size)
            speed = int(b.get("speed", 200) or 200)
            color = hex_to_rgb(b.get("color", "#ffffff"))
            bold = bool(b.get("bold", False))
            y = random.randint(int(size * 1.5), max(int(size * 1.5) + 1, self.sh - int(size * 1.5)))
            x = self.sw + random.randint(0, self.sw // 2) + i * 40
            self._bullet_states.append({
                "text": text, "x": float(x), "y": float(y),
                "speed": speed, "color": color, "size": size, "bold": bold,
            })


    # ===== 主循环 =====

    def tick(self, dt: float = 1 / 60):
        """每帧更新滚动/弹幕位置；dt 为真实经过秒数（不再硬编码）"""
        if self.content_type == "scroll":
            if not self._inited_pos:
                return  # 等首次绘制后再启动滚动
            delta = self.scroll_speed * dt
            # 条带循环周期 = 屏幕宽 + 文本宽（水平）/ 屏幕高 + 文本高（垂直）
            if self.scroll_direction == "left":
                self._scroll_x -= delta
                period = self.sw + self._strip_text_w
                if self.scroll_loop:
                    if self._scroll_x <= -self._strip_text_w:
                        self._scroll_x += period
                else:
                    if self._scroll_x + self._strip_text_w < 0:
                        self.exit(); return
            elif self.scroll_direction == "right":
                self._scroll_x += delta
                period = self.sw + self._strip_text_w
                if self.scroll_loop:
                    if self._scroll_x >= self.sw:
                        self._scroll_x -= period
                else:
                    if self._scroll_x > self.sw:
                        self.exit(); return
            elif self.scroll_direction == "up":
                self._scroll_y -= delta
                period = self.sh + self._strip_text_h
                if self.scroll_loop:
                    if self._scroll_y <= -self._strip_text_h:
                        self._scroll_y += period
                else:
                    if self._scroll_y + self._strip_text_h < 0:
                        self.exit(); return
            else:  # down
                self._scroll_y += delta
                period = self.sh + self._strip_text_h
                if self.scroll_loop:
                    if self._scroll_y >= self.sh:
                        self._scroll_y -= period
                else:
                    if self._scroll_y > self.sh:
                        self.exit(); return
        elif self.content_type == "bullet":
            for b in self._bullet_states:
                b["x"] -= b["speed"] * dt
                if b["x"] + 200 < 0:
                    b["x"] = float(self.sw + random.randint(0, self.sw // 2))
                    b["y"] = float(random.randint(40, max(41, self.sh - 40)))

    def _request_redraw(self):
        """直接强制立即重绘（不再依赖消息队列里的 WM_PAINT 调度延迟）"""
        if self.hwnd:
            try:
                # RDW_INVALIDATE | RDW_UPDATENOW = 0x0001 | 0x0100
                # 让 Windows 立即派发 WM_PAINT，而不是等下一个消息循环
                win32gui.RedrawWindow(self.hwnd, None, None, 0x0001 | 0x0100)
            except Exception:
                # 兜底
                try:
                    win32gui.InvalidateRect(self.hwnd, None, False)
                except Exception:
                    pass

    def run(self):
        self.create_window()
        # 创建窗口后立即初始化 GDI 资源（一次性）
        self._init_gdi_resources()

        last_clock_text = ""

        # === 极致丝滑配置 ===
        # 1. 提升进程/线程优先级，减少被系统其它进程抢占造成的帧抖动
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            HIGH_PRIORITY_CLASS = 0x80
            kernel32.SetPriorityClass(kernel32.GetCurrentProcess(), HIGH_PRIORITY_CLASS)
            THREAD_PRIORITY_TIME_CRITICAL = 15
            THREAD_PRIORITY_ABOVE_NORMAL = 1
            # 优先尝试 TIME_CRITICAL，失败回退 ABOVE_NORMAL
            try:
                kernel32.SetThreadPriority(kernel32.GetCurrentThread(), THREAD_PRIORITY_TIME_CRITICAL)
            except Exception:
                kernel32.SetThreadPriority(kernel32.GetCurrentThread(), THREAD_PRIORITY_ABOVE_NORMAL)
        except Exception:
            pass

        # 2. 提升 Windows 时钟分辨率到 1ms（默认 ~15ms）让 sleep 更精准
        try:
            import ctypes
            ctypes.windll.winmm.timeBeginPeriod(1)
        except Exception:
            pass

        # 3. 注册为禁止节能/禁止暗管理（避免后台被降频）
        try:
            import ctypes
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            ES_DISPLAY_REQUIRED = 0x00000002
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
        except Exception:
            pass

        # 4. 准备 DwmFlush（与显示器 vsync 严格同步）
        try:
            import ctypes
            dwmapi = ctypes.windll.dwmapi
            dwm_flush = dwmapi.DwmFlush
            dwm_flush.restype = ctypes.c_long
            use_vsync = True
        except Exception:
            dwm_flush = None
            use_vsync = False

        # 探测显示器刷新率
        try:
            screen_dc = win32gui.GetDC(0)
            try:
                hz = win32api.GetDeviceCaps(screen_dc, 116)  # VREFRESH = 116
            finally:
                win32gui.ReleaseDC(0, screen_dc)
            if hz <= 1:
                hz = 60
        except Exception:
            hz = 60
        target_dt = 1.0 / float(hz)

        last_tick = time.perf_counter()
        # clock/date/countdown 这种文本只需 200ms 检查一次是否变化
        slow_check_interval = 0.2
        last_slow_check = 0.0

        ct = self.content_type
        # 滚动/弹幕走"主循环直接绘制"快速路径
        # static / clock / date / countdown 走传统 WM_PAINT 路径（这些场景几乎无重绘需求）
        is_animated = ct in ("scroll", "bullet")

        # === 固定步长累加器（让滚动速度严格按"像素/秒"推进，不被帧抖动影响）===
        # 思路：物理推进步长固定为 target_dt（如 1/60s），主循环把真实经过秒数累加，
        # 然后按固定步长循环 tick 多次。这样一帧卡了 50ms 也不会让滚动一次跳 12 像素，
        # 而是匀速分散到接下来几帧上 → 视觉上完全感知不到。
        physics_dt = target_dt  # 物理步长 = 一个屏幕刷新周期
        accumulator = 0.0
        # 防止系统卡严重时累加器爆炸（例如挂起 30s）
        max_accumulator = 0.25

        try:
            while self.running:
                # 处理消息（不阻塞）
                try:
                    win32gui.PumpWaitingMessages()
                except Exception:
                    pass

                if not self.running:
                    break

                now = time.perf_counter()
                elapsed = now - last_tick
                # 防止 elapsed 过大（休眠唤醒）造成累加器爆炸
                if elapsed > max_accumulator:
                    elapsed = physics_dt
                last_tick = now

                # 累加并按固定步长推进物理状态（速度恒定，不受帧抖影响）
                accumulator += elapsed
                if accumulator > max_accumulator:
                    accumulator = max_accumulator
                # 推进次数有上限，避免下一帧前耗时过长
                steps = 0
                while accumulator >= physics_dt and steps < 6:
                    self.tick(physics_dt)
                    accumulator -= physics_dt
                    steps += 1
                # 不足一步的零头：再以一个完整步长 tick 一次（确保肉眼看不到停滞）
                # 注意这里不能用 accumulator 当 dt（会导致速度抖动），保持物理步长不变

                if is_animated:
                    # 快速路径：主循环直接画，不走 WM_PAINT 消息派发，最少开销
                    try:
                        screen_dc = win32gui.GetDC(self.hwnd)
                        if screen_dc:
                            try:
                                if ct == "scroll":
                                    # 滚动：直接从预渲染条带 BitBlt 一段，1~2 次 GDI 调用
                                    self._draw_scroll_strip(screen_dc)
                                else:
                                    # bullet：双缓冲整屏重绘
                                    self._draw_to_hdc(screen_dc)
                            finally:
                                win32gui.ReleaseDC(self.hwnd, screen_dc)
                    except Exception:
                        # 兜底走 RedrawWindow
                        self._request_redraw()
                else:
                    # clock/date/countdown 文本只在内容变化时才重绘
                    if now - last_slow_check >= slow_check_interval:
                        last_slow_check = now
                        if ct == "clock":
                            cur = self._format_clock()
                        elif ct == "date":
                            cur = self._format_date()
                        elif ct == "countdown":
                            cur = self._format_countdown()
                        else:
                            cur = ""
                        if cur != last_clock_text:
                            last_clock_text = cur
                            self._request_redraw()

                # 等待显示器 vsync 信号，让帧间间隔与屏幕刷新对齐
                if use_vsync and dwm_flush is not None:
                    try:
                        dwm_flush()
                    except Exception:
                        time.sleep(target_dt)
                else:
                    time.sleep(target_dt)
        finally:
            try:
                import ctypes
                ctypes.windll.winmm.timeEndPeriod(1)
            except Exception:
                pass
            try:
                import ctypes
                ES_CONTINUOUS = 0x80000000
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            except Exception:
                pass
            self._release_gdi_resources()

    def exit(self):
        self.running = False
        try:
            if self.hwnd:
                win32gui.DestroyWindow(self.hwnd)
        except Exception:
            pass


def main():
    args = parse_args()
    config = load_config(args.config)
    saver = Screensaver(config)
    try:
        saver.run()
    except KeyboardInterrupt:
        saver.exit()


if __name__ == "__main__":
    main()
