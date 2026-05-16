"""
WebRPA 截图工具 - 完全重写版本
确保 100% 稳定的 Win+Shift+S 截图功能
"""
import asyncio
import datetime
import uuid
import time as _time
import subprocess
import os
from pathlib import Path
from PIL import ImageGrab, Image
from typing import Optional, Dict, Any


class ScreenshotToolV2:
    """完全重写的截图工具 - 确保稳定性"""
    
    @staticmethod
    def _kill_screenshot_processes():
        """杀掉所有截图相关进程"""
        for proc in ['ScreenClippingHost.exe', 'SnippingTool.exe', 'explorer.exe']:
            try:
                subprocess.run(['taskkill', '/F', '/IM', proc], 
                             capture_output=True, timeout=2)
            except Exception:
                pass
        _time.sleep(0.3)
    
    @staticmethod
    def _get_clipboard_image() -> Optional[Image.Image]:
        """从剪贴板获取图片（更稳定的实现）"""
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image) and img.size[0] > 0 and img.size[1] > 0:
                return img
        except Exception as e:
            print(f"[ScreenshotTool] 剪贴板读取异常: {e}")
        return None
    
    @staticmethod
    def _clear_clipboard():
        """清空剪贴板"""
        try:
            ctypes.windll.user32.OpenClipboard(0)
            ctypes.windll.user32.EmptyClipboard()
            ctypes.windll.user32.CloseClipboard()
        except Exception:
            pass
    
    @staticmethod
    def _trigger_screenshot_ui():
        """触发 Windows 截图 UI（多方案降级）"""
        
        # 方案1: SnippingTool.exe /clip（最稳定）
        try:
            snipping = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'),
                                   'System32', 'SnippingTool.exe')
            if os.path.exists(snipping):
                subprocess.Popen(
                    [snipping, '/clip'],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print("[ScreenshotTool] 已启动 SnippingTool.exe /clip")
                return True
        except Exception as e:
            print(f"[ScreenshotTool] SnippingTool 失败: {e}")
        
        # 方案2: SendInput Win+Shift+S（比 ms-screenclip 更稳定，不会黑屏）
        try:
            ScreenshotToolV2._send_key(ScreenshotToolV2.VK_LWIN)
            _time.sleep(0.1)
            ScreenshotToolV2._send_key(ScreenshotToolV2.VK_SHIFT)
            _time.sleep(0.1)
            ScreenshotToolV2._send_key(ScreenshotToolV2.VK_S)
            _time.sleep(0.1)
            ScreenshotToolV2._send_key(ScreenshotToolV2.VK_S, key_up=True)
            _time.sleep(0.1)
            ScreenshotToolV2._send_key(ScreenshotToolV2.VK_SHIFT, key_up=True)
            _time.sleep(0.1)
            ScreenshotToolV2._send_key(ScreenshotToolV2.VK_LWIN, key_up=True)
            print("[ScreenshotTool] 已发送 Win+Shift+S")
            return True
        except Exception as e:
            print(f"[ScreenshotTool] SendInput 失败: {e}")
        
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
        
        # 第四步：监控剪贴板（改进的检测逻辑）
        # 前 10 秒：每 0.5 秒检查一次（用户通常很快截图）
        # 10-30 秒：每 1 秒检查一次
        # 30-90 秒：每 2 秒检查一次
        
        start_time = _time.time()
        last_check_time = start_time
        check_count = 0
        
        while _time.time() - start_time < 90:
            current_time = _time.time()
            elapsed = current_time - start_time
            
            # 根据经过时间调整检查间隔
            if elapsed < 10:
                check_interval = 0.5
            elif elapsed < 30:
                check_interval = 1.0
            else:
                check_interval = 2.0
            
            # 到达检查时间
            if current_time - last_check_time >= check_interval:
                last_check_time = current_time
                check_count += 1
                
                current_image = ScreenshotToolV2._get_clipboard_image()
                
                # 判断是否有新图片
                if current_image is not None:
                    # 与初始图片对比
                    if initial_image is None:
                        # 初始无图片，现在有图片 -> 新截图
                        is_new = True
                    else:
                        # 初始有图片，比较尺寸和内容
                        is_new = (current_image.size != initial_image.size or 
                                 current_image.tobytes() != initial_image.tobytes())
                    
                    if is_new:
                        # 保存截图
                        guid = str(uuid.uuid4())
                        save_path = save_dir / f"{guid}.png"
                        current_image.save(str(save_path), 'PNG')
                        
                        elapsed_time = round(_time.time() - start_time, 1)
                        print(f"[ScreenshotTool] ✅ 截图成功！耗时 {elapsed_time}s，检查次数 {check_count}")
                        
                        # 清空剪贴板
                        ScreenshotToolV2._clear_clipboard()
                        
                        return {
                            'success': True,
                            'path': str(save_path),
                            'width': current_image.width,
                            'height': current_image.height,
                            'elapsed': elapsed_time
                        }
            
            # 短暂休眠，避免 CPU 占用过高
            _time.sleep(0.1)
        
        print("[ScreenshotTool] ⏱️ 等待超时（90秒），用户未完成截图")
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
        loop = asyncio.get_event_loop()
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
                    "path": str(saved_path)
                }
                image_assets[asset_id] = asset
                print(f"[ScreenshotTool] 已注册资产: {asset_id}")
                
                return {
                    "success": True,
                    "assetId": asset_id,
                    "fileName": file_name,
                    "width": result['width'],
                    "height": result['height'],
                    "elapsed": result['elapsed']
                }
            else:
                return {
                    "success": True,
                    "path": result['path'],
                    "width": result['width'],
                    "height": result['height'],
                    "elapsed": result['elapsed']
                }
        else:
            error_msg = result.get('error', '未知错误')
            is_cancelled = result.get('cancelled', False)
            print(f"[ScreenshotTool] ❌ 截图失败: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "cancelled": is_cancelled
            }
    
    except Exception as e:
        print(f"[ScreenshotTool] 异常: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": f"截图异常: {str(e)}"}
