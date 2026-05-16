"""
WebRPA 截图工具 - 完全重写版本
确保 100% 稳定的 Win+Shift+S 截图功能

修复说明：
- 移除杀 explorer.exe 的灾难性行为
- 补全 ctypes 与 SendInput 相关常量
- 添加 _send_key 实现
- 仅清理截图相关进程
"""
import asyncio
import datetime
import uuid
import time as _time
import subprocess
import os
import sys
from pathlib import Path
from PIL import ImageGrab, Image
from typing import Optional, Dict, Any

# Windows 平台才导入 ctypes 用于按键模拟
if sys.platform == 'win32':
    import ctypes
    from ctypes import wintypes
else:
    ctypes = None
    wintypes = None


class ScreenshotToolV2:
    """完全重写的截图工具 - 确保稳定性"""

    # Win32 虚拟键码（仅在 Windows 上使用）
    VK_LWIN = 0x5B
    VK_SHIFT = 0x10
    VK_S = 0x53
    KEYEVENTF_KEYUP = 0x0002

    @staticmethod
    def _kill_screenshot_processes():
        """杀掉残留的截图相关进程（仅截图相关，绝不动 explorer.exe）"""
        # 注意：曾经的版本错误地杀了 explorer.exe，会导致用户桌面/任务栏消失
        for proc in ['ScreenClippingHost.exe', 'SnippingTool.exe']:
            try:
                subprocess.run(
                    ['taskkill', '/F', '/IM', proc],
                    capture_output=True,
                    timeout=2,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                )
            except Exception:
                pass
        _time.sleep(0.3)

    @staticmethod
    def _get_clipboard_image() -> Optional[Image.Image]:
        """从剪贴板获取图片"""
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image) and img.size[0] > 0 and img.size[1] > 0:
                return img
        except Exception as e:
            print(f"[ScreenshotTool] 剪贴板读取异常: {e}")
        return None

    @staticmethod
    def _clear_clipboard():
        """清空剪贴板（仅 Windows）"""
        if ctypes is None:
            return
        try:
            user32 = ctypes.windll.user32
            if user32.OpenClipboard(0):
                try:
                    user32.EmptyClipboard()
                finally:
                    user32.CloseClipboard()
        except Exception:
            pass

    @staticmethod
    def _send_key(vk_code: int, key_up: bool = False):
        """发送一次按键事件（KEYDOWN 或 KEYUP）"""
        if ctypes is None:
            return
        flags = ScreenshotToolV2.KEYEVENTF_KEYUP if key_up else 0
        # 使用 keybd_event（旧 API，足以触发 Win+Shift+S 系统快捷键）
        try:
            ctypes.windll.user32.keybd_event(vk_code, 0, flags, 0)
        except Exception as e:
            print(f"[ScreenshotTool] keybd_event 失败: {e}")

    @staticmethod
    def _trigger_screenshot_ui():
        """触发 Windows 截图 UI（多方案降级）"""

        # 方案1: ms-screenclip:（Win10/11 自带，最稳定）
        try:
            os.startfile('ms-screenclip:')
            print("[ScreenshotTool] 已启动 ms-screenclip:")
            return True
        except Exception as e:
            print(f"[ScreenshotTool] ms-screenclip: 启动失败: {e}")

        # 方案2: SnippingTool.exe /clip
        try:
            snipping = os.path.join(
                os.environ.get('SystemRoot', 'C:\\Windows'),
                'System32', 'SnippingTool.exe'
            )
            if os.path.exists(snipping):
                subprocess.Popen(
                    [snipping, '/clip'],
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print("[ScreenshotTool] 已启动 SnippingTool.exe /clip")
                return True
        except Exception as e:
            print(f"[ScreenshotTool] SnippingTool 失败: {e}")

        # 方案3: 模拟 Win+Shift+S 快捷键
        if ctypes is not None:
            try:
                ScreenshotToolV2._send_key(ScreenshotToolV2.VK_LWIN)
                _time.sleep(0.05)
                ScreenshotToolV2._send_key(ScreenshotToolV2.VK_SHIFT)
                _time.sleep(0.05)
                ScreenshotToolV2._send_key(ScreenshotToolV2.VK_S)
                _time.sleep(0.05)
                ScreenshotToolV2._send_key(ScreenshotToolV2.VK_S, key_up=True)
                _time.sleep(0.05)
                ScreenshotToolV2._send_key(ScreenshotToolV2.VK_SHIFT, key_up=True)
                _time.sleep(0.05)
                ScreenshotToolV2._send_key(ScreenshotToolV2.VK_LWIN, key_up=True)
                print("[ScreenshotTool] 已发送 Win+Shift+S")
                return True
            except Exception as e:
                print(f"[ScreenshotTool] SendKey 失败: {e}")

        return False

    @staticmethod
    def do_screenshot(save_dir: Path) -> Dict[str, Any]:
        """执行截图流程（同步）"""
        save_dir.mkdir(parents=True, exist_ok=True)

        # 第一步：清理环境
        print("[ScreenshotTool] 清理截图进程...")
        ScreenshotToolV2._kill_screenshot_processes()
        ScreenshotToolV2._clear_clipboard()
        _time.sleep(0.5)

        # 第二步：记录初始剪贴板状态
        initial_image = ScreenshotToolV2._get_clipboard_image()
        print(f"[ScreenshotTool] 初始剪贴板: {'有图片' if initial_image else '无图片'}")

        # 第三步：触发截图 UI
        if not ScreenshotToolV2._trigger_screenshot_ui():
            return {'success': False, 'error': '无法启动截图工具'}

        print("[ScreenshotTool] 等待用户截图（最多 90 秒）...")

        # 第四步：监控剪贴板
        start_time = _time.time()
        last_check_time = start_time
        check_count = 0

        while _time.time() - start_time < 90:
            current_time = _time.time()
            elapsed = current_time - start_time

            # 自适应轮询间隔
            if elapsed < 10:
                check_interval = 0.5
            elif elapsed < 30:
                check_interval = 1.0
            else:
                check_interval = 2.0

            if current_time - last_check_time >= check_interval:
                last_check_time = current_time
                check_count += 1

                current_image = ScreenshotToolV2._get_clipboard_image()

                if current_image is not None:
                    if initial_image is None:
                        is_new = True
                    else:
                        is_new = (
                            current_image.size != initial_image.size or
                            current_image.tobytes() != initial_image.tobytes()
                        )

                    if is_new:
                        guid = str(uuid.uuid4())
                        save_path = save_dir / f"{guid}.png"
                        current_image.save(str(save_path), 'PNG')

                        elapsed_time = round(_time.time() - start_time, 1)
                        print(
                            f"[ScreenshotTool] 截图成功！耗时 {elapsed_time}s，"
                            f"检查次数 {check_count}"
                        )

                        # 清空剪贴板
                        ScreenshotToolV2._clear_clipboard()

                        return {
                            'success': True,
                            'path': str(save_path),
                            'width': current_image.width,
                            'height': current_image.height,
                            'elapsed': elapsed_time,
                        }

            _time.sleep(0.1)

        print("[ScreenshotTool] 等待超时（90秒），用户未完成截图")
        return {'success': False, 'error': 'timeout', 'cancelled': True}


async def screenshot_tool_handler(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """异步处理截图请求"""
    try:
        save_to_assets = request_data.get('saveToAssets', True)
        folder = request_data.get('folder', '')

        # 确定保存目录
        if save_to_assets:
            image_assets_dir = Path(__file__).parent.parent.parent / "uploads" / "images"
            save_dir = image_assets_dir / folder if folder else image_assets_dir
        else:
            import tempfile
            save_dir = Path(tempfile.gettempdir())

        print(f"[ScreenshotTool] 保存目录: {save_dir}")

        # 在线程池中执行（避免阻塞事件循环）
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, ScreenshotToolV2.do_screenshot, save_dir)

        if result.get('success'):
            saved_path = Path(result['path'])

            if save_to_assets:
                asset_id = saved_path.stem
                file_name = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                file_size = saved_path.stat().st_size

                # 注册资产
                from app.api.image_assets import image_assets
                asset = {
                    "id": asset_id,
                    "name": f"{asset_id}.png",
                    "originalName": file_name,
                    "size": file_size,
                    "uploadedAt": datetime.datetime.now().isoformat(),
                    "folder": folder or "",
                    "extension": ".png",
                    "path": str(saved_path),
                }
                image_assets[asset_id] = asset
                print(f"[ScreenshotTool] 已注册资产: {asset_id}")

                return {
                    "success": True,
                    "assetId": asset_id,
                    "fileName": file_name,
                    "width": result['width'],
                    "height": result['height'],
                    "elapsed": result['elapsed'],
                }
            else:
                return {
                    "success": True,
                    "path": result['path'],
                    "width": result['width'],
                    "height": result['height'],
                    "elapsed": result['elapsed'],
                }
        else:
            error_msg = result.get('error', '未知错误')
            is_cancelled = result.get('cancelled', False)
            print(f"[ScreenshotTool] 截图失败: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "cancelled": is_cancelled,
            }

    except Exception as e:
        print(f"[ScreenshotTool] 异常: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": f"截图异常: {str(e)}"}
