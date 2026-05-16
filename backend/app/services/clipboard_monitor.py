"""
剪贴板监听服务 - 检测用户截图并通知前端
"""
import asyncio
import threading
import time
from PIL import ImageGrab, Image
from typing import Optional, Callable
import hashlib


class ClipboardMonitorService:
    """监听剪贴板中的图片变化"""
    
    _instance: Optional['ClipboardMonitorService'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_image_hash: Optional[str] = None
        self._on_new_image: Optional[Callable[[Image.Image], None]] = None
        self._check_interval = 0.5  # 每 0.5 秒检查一次
    
    def set_callback(self, callback: Callable[[Image.Image], None]):
        """设置新图片检测到时的回调"""
        self._on_new_image = callback
    
    def start(self):
        """启动剪贴板监听"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print("[ClipboardMonitor] 剪贴板监听已启动")
    
    def stop(self):
        """停止剪贴板监听"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("[ClipboardMonitor] 剪贴板监听已停止")
    
    @staticmethod
    def _get_clipboard_image() -> Optional[Image.Image]:
        """从剪贴板获取图片"""
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image) and img.size[0] > 0 and img.size[1] > 0:
                return img
        except Exception as e:
            print(f"[ClipboardMonitor] 读取剪贴板异常: {e}")
        return None
    
    @staticmethod
    def _image_to_hash(img: Image.Image) -> str:
        """计算图片的哈希值"""
        try:
            return hashlib.md5(img.tobytes()).hexdigest()
        except Exception:
            return ""
    
    def _monitor_loop(self):
        """监听循环"""
        print("[ClipboardMonitor] 监听循环已启动")
        
        while self._running:
            try:
                current_image = self._get_clipboard_image()
                
                if current_image is not None:
                    current_hash = self._image_to_hash(current_image)
                    
                    # 检测到新图片
                    if current_hash and current_hash != self._last_image_hash:
                        print(f"[ClipboardMonitor] 检测到新图片 (哈希: {current_hash[:8]}...)")
                        self._last_image_hash = current_hash
                        
                        # 调用回调
                        if self._on_new_image:
                            try:
                                self._on_new_image(current_image)
                            except Exception as e:
                                print(f"[ClipboardMonitor] 回调异常: {e}")
                
                time.sleep(self._check_interval)
            
            except Exception as e:
                print(f"[ClipboardMonitor] 监听异常: {e}")
                time.sleep(1)
        
        print("[ClipboardMonitor] 监听循环已退出")
