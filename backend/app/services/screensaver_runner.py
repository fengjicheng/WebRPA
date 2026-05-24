"""屏保弹幕子进程入口（独立运行）

由 screensaver.py 通过 subprocess.Popen 启动，参数 --config <json路径>。
不依赖 FastAPI / app 包，纯 stdlib + tkinter。
"""
import argparse
import json
import math
import random
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import font as tkfont
except Exception as _e:
    print(f"[Screensaver] tkinter 不可用：{_e}", file=sys.stderr)
    sys.exit(1)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True, help="配置文件路径(JSON)")
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


class Screensaver:
    """tkinter 全屏屏保

    实现策略：
    - 用 toplevel 窗口 + Canvas
    - overrideredirect(True) 去掉标题栏
    - attributes('-topmost', True) 置顶
    - attributes('-fullscreen', True) 全屏
    - attributes('-alpha', a) 整体透明度（Win/macOS 支持）
    - attributes('-transparentcolor', color) Win 单色透明（点击穿透实现关键）
    - 按 Esc 或自定义快捷键退出
    """

    def __init__(self, config: dict):
        self.config = config
        self.root = tk.Tk()
        self.canvas: tk.Canvas | None = None
        self._items: list[int] = []   # 主显示文本的 canvas item id 列表
        self._bullets: list[dict] = []  # bullet 模式的元素状态
        self._tick_after_id: str | None = None
        self._start_time = time.time()

        # 字段读取（带默认值）
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
        self.color: str = c.get("color", "#ffffff")
        self.background: str = c.get("background", "#000000")
        self.background_alpha: float = float(c.get("background_alpha", 1.0) or 1.0)

        self.fullscreen: bool = bool(c.get("fullscreen", True))
        self.scroll_direction: str = c.get("scroll_direction", "left")
        self.scroll_speed: int = int(c.get("scroll_speed", 200) or 200)
        self.scroll_loop: bool = bool(c.get("scroll_loop", True))

        self.click_through: bool = bool(c.get("click_through", False))
        self.show_close_hint: bool = bool(c.get("show_close_hint", True))
        self.exit_hotkey: str = (c.get("exit_hotkey") or "Escape").replace("Esc", "Escape")

        self.outline_color: str = c.get("outline_color", "") or ""
        self.outline_width: int = int(c.get("outline_width", 0) or 0)
        self.rotation: int = int(c.get("rotation", 0) or 0)
        self.vertical_text: bool = bool(c.get("vertical_text", False))

    def setup_window(self):
        root = self.root
        root.title("WebRPA Screensaver")
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        if self.fullscreen:
            try:
                root.attributes("-fullscreen", True)
            except Exception:
                w = root.winfo_screenwidth()
                h = root.winfo_screenheight()
                root.geometry(f"{w}x{h}+0+0")
        try:
            root.overrideredirect(True)
        except Exception:
            pass

        # 整体透明度（仅 Windows / macOS）
        try:
            root.attributes("-alpha", max(0.05, min(1.0, self.background_alpha)))
        except Exception:
            pass

        # 点击穿透：Windows 用 transparentcolor + 把背景设成该颜色
        if self.click_through and sys.platform == "win32":
            try:
                root.attributes("-transparentcolor", self.background)
            except Exception:
                pass

        root.configure(bg=self.background)
        # 隐藏鼠标可选
        # root.config(cursor="none")

        # 退出快捷键
        try:
            root.bind(f"<{self.exit_hotkey}>", lambda e: self.exit())
        except Exception:
            root.bind("<Escape>", lambda e: self.exit())
        # 双击也退出
        root.bind("<Double-Button-1>", lambda e: self.exit())

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        self.canvas = tk.Canvas(
            root, width=sw, height=sh, bg=self.background,
            highlightthickness=0, bd=0,
        )
        self.canvas.pack(fill="both", expand=True)

        if self.show_close_hint:
            hint_font = tkfont.Font(family=self.font_family, size=12)
            self.canvas.create_text(
                sw - 20, sh - 20, anchor="se",
                text=f"按 {self.exit_hotkey if self.exit_hotkey != 'Escape' else 'Esc'} 退出",
                fill=self._dim_color(self.color),
                font=hint_font,
            )

    def _dim_color(self, hex_c: str) -> str:
        r, g, b = hex_to_rgb(hex_c)
        # 低对比度提示文本
        return "#%02x%02x%02x" % (max(0, min(255, r * 6 // 10)), max(0, min(255, g * 6 // 10)), max(0, min(255, b * 6 // 10)))

    def _make_font(self) -> tkfont.Font:
        weight = "bold" if self.font_weight == "bold" else "normal"
        slant = "italic" if self.font_italic else "roman"
        return tkfont.Font(family=self.font_family, size=self.font_size, weight=weight, slant=slant)


    # ===== 不同 content_type 的实现 =====

    def render_static_text(self, text_value: str):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        font = self._make_font()
        cx, cy = sw // 2, sh // 2

        # 描边
        if self.outline_color and self.outline_width > 0:
            for dx in range(-self.outline_width, self.outline_width + 1):
                for dy in range(-self.outline_width, self.outline_width + 1):
                    if dx == 0 and dy == 0:
                        continue
                    self.canvas.create_text(
                        cx + dx, cy + dy, text=text_value, fill=self.outline_color,
                        font=font, anchor="center",
                    )

        # 旋转：tkinter Canvas text 原生不支持 rotate，简单用 90/270 时把文字按字符竖排
        if self.rotation in (90, 270) or self.vertical_text:
            text_value = "\n".join(list(text_value))

        item_id = self.canvas.create_text(
            cx, cy, text=text_value, fill=self.color, font=font, anchor="center",
            justify="center",
        )
        self._items.append(item_id)

    def render_clock(self):
        # 由 tick 函数动态更新
        self.render_static_text(self._format_clock())

    def render_date(self):
        self.render_static_text(self._format_date())

    def render_countdown(self):
        self.render_static_text(self._format_countdown())

    def _format_clock(self) -> str:
        if self.datetime_format:
            try:
                return datetime.now().strftime(self.datetime_format)
            except Exception:
                pass
        return datetime.now().strftime("%H:%M:%S")

    def _format_date(self) -> str:
        if self.datetime_format:
            try:
                return datetime.now().strftime(self.datetime_format)
            except Exception:
                pass
        return datetime.now().strftime("%Y-%m-%d %A")

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

    def render_scroll(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        font = self._make_font()
        text_value = self.text or ""
        if self.vertical_text:
            text_value = "\n".join(list(text_value))
        # 起始位置：根据方向决定
        if self.scroll_direction == "left":
            x, y = sw + 20, sh // 2
            anchor = "w"
        elif self.scroll_direction == "right":
            x, y = -20, sh // 2
            anchor = "e"
        elif self.scroll_direction == "up":
            x, y = sw // 2, sh + 20
            anchor = "n"
        else:  # down
            x, y = sw // 2, -20
            anchor = "s"
        item_id = self.canvas.create_text(
            x, y, text=text_value, fill=self.color, font=font, anchor=anchor,
        )
        self._items.append(item_id)

    def render_bullets(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        # bullets 每条独立轨迹：随机起始 y、随机速度
        for i, b in enumerate(self.bullets):
            text_value = b.get("text", "")
            if not text_value:
                continue
            font_family = b.get("font_family", self.font_family)
            font_size = int(b.get("font_size", self.font_size) or self.font_size)
            color = b.get("color", self.color)
            speed = int(b.get("speed", 200) or 200)
            font_obj = tkfont.Font(family=font_family, size=font_size, weight=("bold" if b.get("bold") else "normal"))
            y = b.get("y") if isinstance(b.get("y"), (int, float)) else random.randint(int(font_size * 1.5), max(int(font_size * 1.5) + 1, sh - int(font_size * 1.5)))
            x = sw + random.randint(0, sw // 2) + i * 40
            item_id = self.canvas.create_text(x, y, text=text_value, fill=color, font=font_obj, anchor="w")
            self._bullets.append({"id": item_id, "speed": speed, "y": y, "text": text_value})

    # ===== 动画循环 =====
    def tick(self):
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            now = time.time()
            dt = 1 / 60  # 目标 60fps

            if self.content_type == "scroll":
                if self._items and self.canvas:
                    delta = self.scroll_speed * dt
                    for iid in self._items:
                        if self.scroll_direction == "left":
                            self.canvas.move(iid, -delta, 0)
                            x1, _, x2, _ = self.canvas.bbox(iid) or (0, 0, 0, 0)
                            if x2 < 0:
                                if self.scroll_loop:
                                    self.canvas.coords(iid, sw + 20, sh // 2)
                                else:
                                    self.exit()
                                    return
                        elif self.scroll_direction == "right":
                            self.canvas.move(iid, delta, 0)
                            x1, _, x2, _ = self.canvas.bbox(iid) or (0, 0, 0, 0)
                            if x1 > sw:
                                if self.scroll_loop:
                                    self.canvas.coords(iid, -20, sh // 2)
                                else:
                                    self.exit(); return
                        elif self.scroll_direction == "up":
                            self.canvas.move(iid, 0, -delta)
                            _, y1, _, y2 = self.canvas.bbox(iid) or (0, 0, 0, 0)
                            if y2 < 0:
                                if self.scroll_loop:
                                    self.canvas.coords(iid, sw // 2, sh + 20)
                                else:
                                    self.exit(); return
                        else:  # down
                            self.canvas.move(iid, 0, delta)
                            _, y1, _, y2 = self.canvas.bbox(iid) or (0, 0, 0, 0)
                            if y1 > sh:
                                if self.scroll_loop:
                                    self.canvas.coords(iid, sw // 2, -20)
                                else:
                                    self.exit(); return

            elif self.content_type == "bullet":
                for b in list(self._bullets):
                    iid = b["id"]
                    if not self.canvas:
                        break
                    self.canvas.move(iid, -b["speed"] * dt, 0)
                    bbox = self.canvas.bbox(iid)
                    if bbox is None:
                        continue
                    x1, _, x2, _ = bbox
                    if x2 < 0:
                        # 重新出现在右侧
                        new_y = random.randint(40, max(41, sh - 40))
                        self.canvas.coords(iid, sw + 50, new_y)

            elif self.content_type in ("clock", "date", "countdown") and self._items and self.canvas:
                if self.content_type == "clock":
                    new_text = self._format_clock()
                elif self.content_type == "date":
                    new_text = self._format_date()
                else:
                    new_text = self._format_countdown()
                # 仅每 100ms 刷一次（内部已是 16ms 帧），降低 GUI 刷新负担
                if int(now * 10) != int(getattr(self, "_last_clock_tick", 0)):
                    self._last_clock_tick = now * 10
                    for iid in self._items:
                        self.canvas.itemconfigure(iid, text=new_text)

            # 16ms 后再调用
            self._tick_after_id = self.root.after(16, self.tick)
        except tk.TclError:
            return  # 窗口已关闭
        except Exception as e:
            print(f"[Screensaver] tick 异常：{e}", file=sys.stderr)
            self._tick_after_id = self.root.after(33, self.tick)

    def run(self):
        self.setup_window()

        # 根据 content_type 渲染初始内容
        ct = self.content_type
        if ct == "text":
            self.render_static_text(self.text or "")
        elif ct == "scroll":
            self.render_scroll()
        elif ct == "clock":
            self.render_clock()
        elif ct == "date":
            self.render_date()
        elif ct == "countdown":
            self.render_countdown()
        elif ct == "bullet":
            self.render_bullets()
        else:
            self.render_static_text(self.text or "WebRPA Screensaver")

        # 启动动画循环
        self.tick()
        self.root.mainloop()

    def exit(self):
        try:
            if self._tick_after_id:
                self.root.after_cancel(self._tick_after_id)
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass


def main():
    args = parse_args()
    config = load_config(args.config)
    saver = Screensaver(config)
    saver.run()


if __name__ == "__main__":
    main()
