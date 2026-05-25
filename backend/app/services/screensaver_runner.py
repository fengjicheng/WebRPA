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
        self.datetime_format: str = c.get("datetime_format", "")
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

    # ===== 文本生成 =====

    def _format_clock(self) -> str:
        if self.datetime_format:
            try:
                return self._zh_strftime(self.datetime_format, datetime.now())
            except Exception:
                pass
        return datetime.now().strftime("%H:%M:%S")

    def _format_date(self) -> str:
        if self.datetime_format:
            try:
                return self._zh_strftime(self.datetime_format, datetime.now())
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
        # 双缓冲：在内存 DC 上画，再 BitBlt 到屏幕
        mem_dc = win32gui.CreateCompatibleDC(hdc)
        bmp = win32gui.CreateCompatibleBitmap(hdc, self.sw, self.sh)
        old_bmp = win32gui.SelectObject(mem_dc, bmp)

        try:
            # 填背景
            brush = win32gui.CreateSolidBrush(rgb_to_colorref(self.background))
            win32gui.FillRect(mem_dc, (0, 0, self.sw, self.sh), brush)
            win32gui.DeleteObject(brush)

            # 设置文字颜色（普通文本）
            win32gui.SetTextColor(mem_dc, rgb_to_colorref(self.color))
            win32gui.SetBkMode(mem_dc, win32con.TRANSPARENT)

            ct = self.content_type
            if ct == "bullet":
                self._draw_bullets(mem_dc)
            else:
                text = self._current_text()
                font = self._make_font()
                old_font = win32gui.SelectObject(mem_dc, font)
                self._draw_main_text(mem_dc, text, ct)
                win32gui.SelectObject(mem_dc, old_font)
                win32gui.DeleteObject(font)

            if self.show_close_hint:
                self._draw_close_hint(mem_dc)

            # BitBlt 到屏幕
            win32gui.BitBlt(hdc, 0, 0, self.sw, self.sh, mem_dc, 0, 0, win32con.SRCCOPY)
        finally:
            win32gui.SelectObject(mem_dc, old_bmp)
            win32gui.DeleteObject(bmp)
            win32gui.DeleteDC(mem_dc)

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
            x = int(self._scroll_x)
            y = int(self._scroll_y)
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
            font = self._make_font(size=b.get("size", self.font_size), bold=b.get("bold", False))
            old_font = win32gui.SelectObject(hdc, font)
            old_color = win32gui.SetTextColor(hdc, rgb_to_colorref(b["color"]))
            try:
                win32gui.ExtTextOut(hdc, int(b["x"]), int(b["y"]), 0, None, b["text"])
            except Exception:
                pass
            win32gui.SetTextColor(hdc, old_color)
            win32gui.SelectObject(hdc, old_font)
            win32gui.DeleteObject(font)

    def _draw_close_hint(self, hdc):
        font = self._make_font(size=14, bold=False, italic=False)
        old_font = win32gui.SelectObject(hdc, font)
        # 半暗色提示
        r, g, b = self.color
        dim = (r * 6 // 10, g * 6 // 10, b * 6 // 10)
        old_color = win32gui.SetTextColor(hdc, rgb_to_colorref(dim))
        text = f"按 {self.exit_hotkey} 或双击屏幕退出"
        try:
            sz = win32gui.GetTextExtentPoint32(hdc, text)
            tw, th = sz
        except Exception:
            tw, th = 200, 18
        win32gui.ExtTextOut(hdc, self.sw - tw - 20, self.sh - th - 20, 0, None, text)
        win32gui.SetTextColor(hdc, old_color)
        win32gui.SelectObject(hdc, old_font)
        win32gui.DeleteObject(font)

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
            if self.scroll_direction == "left":
                self._scroll_x -= delta
                if self._scroll_x + self._text_width < 0:
                    if self.scroll_loop:
                        self._scroll_x = float(self.sw + 20)
                    else:
                        self.exit()
                        return
            elif self.scroll_direction == "right":
                self._scroll_x += delta
                if self._scroll_x > self.sw:
                    if self.scroll_loop:
                        self._scroll_x = float(-self._text_width - 20)
                    else:
                        self.exit(); return
            elif self.scroll_direction == "up":
                self._scroll_y -= delta
                if self._scroll_y + self._text_height < 0:
                    if self.scroll_loop:
                        self._scroll_y = float(self.sh + 20)
                    else:
                        self.exit(); return
            else:  # down
                self._scroll_y += delta
                if self._scroll_y > self.sh:
                    if self.scroll_loop:
                        self._scroll_y = float(-self._text_height - 20)
                    else:
                        self.exit(); return
        elif self.content_type == "bullet":
            for b in self._bullet_states:
                b["x"] -= b["speed"] * dt
                if b["x"] + 200 < 0:
                    b["x"] = float(self.sw + random.randint(0, self.sw // 2))
                    b["y"] = float(random.randint(40, max(41, self.sh - 40)))

    def _request_redraw(self):
        if self.hwnd:
            try:
                win32gui.InvalidateRect(self.hwnd, None, False)
            except Exception:
                pass

    def run(self):
        self.create_window()
        last_clock_text = ""
        last_tick = time.time()
        while self.running:
            # 处理一批消息
            try:
                win32gui.PumpWaitingMessages()
            except Exception:
                pass

            now = time.time()
            elapsed = now - last_tick
            if elapsed >= 1 / 60:
                last_tick = now
                self.tick(elapsed)
                # clock/date/countdown 只需 100ms 更新一次
                if self.content_type in ("clock", "date", "countdown"):
                    if self.content_type == "clock":
                        cur = self._format_clock()
                    elif self.content_type == "date":
                        cur = self._format_date()
                    else:
                        cur = self._format_countdown()
                    if cur != last_clock_text:
                        last_clock_text = cur
                        self._request_redraw()
                else:
                    self._request_redraw()

            # 防 CPU 跑满
            time.sleep(0.005)

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
