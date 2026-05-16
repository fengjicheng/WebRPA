"""全局热键服务 - 支持后台快捷键控制工作流运行/停止"""
import asyncio
import threading
from typing import Callable, Optional
import ctypes
from ctypes import wintypes
import sys


# Windows API 常量
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
WM_HOTKEY = 0x0312

# 虚拟键码
VK_F5 = 0x74
VK_F9 = 0x78
VK_F10 = 0x79
VK_F12 = 0x7B


class GlobalHotkeyService:
    """全局热键服务，使用Windows API实现真正的系统级热键"""
    
    _instance: Optional['GlobalHotkeyService'] = None
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
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        
        # 回调函数
        self._on_run_workflow: Optional[Callable[[], None]] = None
        self._on_stop_workflow: Optional[Callable[[], None]] = None
        self._on_macro_start: Optional[Callable[[], None]] = None  # F9 - 开始录制宏
        self._on_macro_stop: Optional[Callable[[], None]] = None   # F10 - 停止录制宏
        self._on_screenshot: Optional[Callable[[], None]] = None   # Ctrl+Shift+F12 - 截图
        
        # 热键ID
        self._hotkey_ids = {
            'run': 1,           # F5
            'stop': 2,          # Shift+F5
            'screenshot': 3,    # Ctrl+Shift+F12
            'macro_start': 4,   # F9
            'macro_stop': 5     # F10
        }
        
        # 是否启用
        self._enabled = True
        
        # Windows API
        self.user32 = ctypes.windll.user32
    
    def set_main_loop(self, loop: asyncio.AbstractEventLoop):
        """设置主事件循环"""
        self._main_loop = loop
    
    def set_callbacks(self, 
                      on_run: Optional[Callable[[], None]] = None,
                      on_stop: Optional[Callable[[], None]] = None,
                      on_macro_start: Optional[Callable[[], None]] = None,
                      on_macro_stop: Optional[Callable[[], None]] = None,
                      on_screenshot: Optional[Callable[[], None]] = None):
        """设置回调函数"""
        self._on_run_workflow = on_run
        self._on_stop_workflow = on_stop
        self._on_macro_start = on_macro_start
        self._on_macro_stop = on_macro_stop
        self._on_screenshot = on_screenshot
    
    def set_enabled(self, enabled: bool):
        """启用/禁用热键"""
        self._enabled = enabled
        print(f"[GlobalHotkey] 热键已{'启用' if enabled else '禁用'}")
    
    def _register_hotkeys(self):
        """注册所有热键"""
        try:
            success_count = 0
            
            # F5 - 运行（使用 MOD_NOREPEAT 标志避免重复触发）
            result = self.user32.RegisterHotKey(None, self._hotkey_ids['run'], 0x4000, VK_F5)  # 0x4000 = MOD_NOREPEAT
            if result:
                print(f"[GlobalHotkey] ✅ F5 热键注册成功")
                success_count += 1
            else:
                error_code = ctypes.get_last_error()
                print(f"[GlobalHotkey] ❌ F5 热键注册失败 (错误码: {error_code})")
            
            # Shift+F5 - 停止
            result = self.user32.RegisterHotKey(None, self._hotkey_ids['stop'], MOD_SHIFT | 0x4000, VK_F5)
            if result:
                print(f"[GlobalHotkey] ✅ Shift+F5 热键注册成功")
                success_count += 1
            else:
                error_code = ctypes.get_last_error()
                print(f"[GlobalHotkey] ❌ Shift+F5 热键注册失败 (错误码: {error_code})")
            
            # Ctrl+Shift+F12 - 截图（已禁用，避免系统崩溃）
            # result = self.user32.RegisterHotKey(None, self._hotkey_ids['screenshot'], 
            #                                  MOD_CONTROL | MOD_SHIFT | 0x4000, VK_F12)
            # if result:
            #     print(f"[GlobalHotkey] ✅ Ctrl+Shift+F12 热键注册成功")
            #     success_count += 1
            # else:
            #     error_code = ctypes.get_last_error()
            #     print(f"[GlobalHotkey] ❌ Ctrl+Shift+F12 热键注册失败 (错误码: {error_code})")
            
            # F9 - 开始录制宏
            result = self.user32.RegisterHotKey(None, self._hotkey_ids['macro_start'], 0x4000, VK_F9)
            if result:
                print(f"[GlobalHotkey] ✅ F9 热键注册成功")
                success_count += 1
            else:
                error_code = ctypes.get_last_error()
                print(f"[GlobalHotkey] ❌ F9 热键注册失败 (错误码: {error_code})")
            
            # F10 - 停止录制宏
            result = self.user32.RegisterHotKey(None, self._hotkey_ids['macro_stop'], 0x4000, VK_F10)
            if result:
                print(f"[GlobalHotkey] ✅ F10 热键注册成功")
                success_count += 1
            else:
                error_code = ctypes.get_last_error()
                print(f"[GlobalHotkey] ❌ F10 热键注册失败 (错误码: {error_code})")
            
            print(f"[GlobalHotkey] 热键注册完成: {success_count}/5 个热键注册成功")
            return success_count > 0
        except Exception as e:
            print(f"[GlobalHotkey] 注册热键失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _unregister_hotkeys(self):
        """注销所有热键"""
        try:
            for hotkey_id in self._hotkey_ids.values():
                self.user32.UnregisterHotKey(None, hotkey_id)
            print("[GlobalHotkey] 热键已注销")
        except Exception as e:
            print(f"[GlobalHotkey] 注销热键失败: {e}")
    
    def _hotkey_loop(self):
        """热键消息循环"""
        print("[GlobalHotkey] 热键消息循环已启动")
        
        # 注册热键
        if not self._register_hotkeys():
            print("[GlobalHotkey] 热键注册失败，消息循环退出")
            return
        
        try:
            msg = wintypes.MSG()
            while self._running:
                # 获取消息
                result = self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                
                if result == 0 or result == -1:
                    break
                
                if msg.message == WM_HOTKEY:
                    hotkey_id = msg.wParam
                    
                    if not self._enabled:
                        continue
                    
                    # 根据热键ID触发相应的回调
                    if hotkey_id == self._hotkey_ids['run']:
                        print("[GlobalHotkey] 检测到运行热键: F5")
                        self._trigger_run()
                    elif hotkey_id == self._hotkey_ids['stop']:
                        print("[GlobalHotkey] 检测到停止热键: Shift+F5")
                        self._trigger_stop()
                    # elif hotkey_id == self._hotkey_ids['screenshot']:  # 已禁用
                        print("[GlobalHotkey] 检测到截图热键: Ctrl+Shift+F12")
                        # self._trigger_screenshot()  # 已禁用
                    elif hotkey_id == self._hotkey_ids['macro_start']:
                        print("[GlobalHotkey] 检测到宏录制开始热键: F9")
                        self._trigger_macro_start()
                    elif hotkey_id == self._hotkey_ids['macro_stop']:
                        print("[GlobalHotkey] 检测到宏录制停止热键: F10")
                        self._trigger_macro_stop()
                
                self.user32.TranslateMessage(ctypes.byref(msg))
                self.user32.DispatchMessageW(ctypes.byref(msg))
        
        except Exception as e:
            print(f"[GlobalHotkey] 热键循环异常: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 注销热键
            self._unregister_hotkeys()
            print("[GlobalHotkey] 热键消息循环已退出")
    
    def _trigger_run(self):
        """触发运行工作流"""
        print(f"[GlobalHotkey] _trigger_run 被调用，回调函数存在: {self._on_run_workflow is not None}, 事件循环存在: {self._main_loop is not None}")
        if self._on_run_workflow and self._main_loop:
            # 在主事件循环中执行回调
            asyncio.run_coroutine_threadsafe(
                self._async_run_callback(),
                self._main_loop
            )
            print("[GlobalHotkey] 运行回调已提交到事件循环")
    
    def _trigger_stop(self):
        """触发停止工作流"""
        print(f"[GlobalHotkey] _trigger_stop 被调用，回调函数存在: {self._on_stop_workflow is not None}, 事件循环存在: {self._main_loop is not None}")
        if self._on_stop_workflow and self._main_loop:
            asyncio.run_coroutine_threadsafe(
                self._async_stop_callback(),
                self._main_loop
            )
            print("[GlobalHotkey] 停止回调已提交到事件循环")
    
    def _trigger_macro_start(self):
        """触发开始录制宏"""
        print(f"[GlobalHotkey] _trigger_macro_start 被调用，回调函数存在: {self._on_macro_start is not None}, 事件循环存在: {self._main_loop is not None}")
        if self._on_macro_start and self._main_loop:
            asyncio.run_coroutine_threadsafe(
                self._async_macro_start_callback(),
                self._main_loop
            )
            print("[GlobalHotkey] 宏录制开始回调已提交到事件循环")
    
    def _trigger_macro_stop(self):
        """触发停止录制宏"""
        print(f"[GlobalHotkey] _trigger_macro_stop 被调用，回调函数存在: {self._on_macro_stop is not None}, 事件循环存在: {self._main_loop is not None}")
        if self._on_macro_stop and self._main_loop:
            asyncio.run_coroutine_threadsafe(
                self._async_macro_stop_callback(),
                self._main_loop
            )
            print("[GlobalHotkey] 宏录制停止回调已提交到事件循环")
    
    def _trigger_screenshot(self):
        """触发截图"""
        print(f"[GlobalHotkey] _trigger_screenshot 被调用，回调函数存在: {self._on_screenshot is not None}, 事件循环存在: {self._main_loop is not None}")
        if self._on_screenshot and self._main_loop:
            asyncio.run_coroutine_threadsafe(
                self._async_screenshot_callback(),
                self._main_loop
            )
            print("[GlobalHotkey] 截图回调已提交到事件循环")
    
    async def _async_run_callback(self):
        """异步执行运行回调"""
        if self._on_run_workflow:
            try:
                result = self._on_run_workflow()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"[GlobalHotkey] 运行回调异常: {e}")
    
    async def _async_stop_callback(self):
        """异步执行停止回调"""
        if self._on_stop_workflow:
            try:
                result = self._on_stop_workflow()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"[GlobalHotkey] 停止回调异常: {e}")
    
    async def _async_macro_start_callback(self):
        """异步执行宏录制开始回调"""
        if self._on_macro_start:
            try:
                result = self._on_macro_start()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"[GlobalHotkey] 宏录制开始回调异常: {e}")
    
    async def _async_macro_stop_callback(self):
        """异步执行宏录制停止回调"""
        if self._on_macro_stop:
            try:
                result = self._on_macro_stop()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"[GlobalHotkey] 宏录制停止回调异常: {e}")
    
    async def _async_screenshot_callback(self):
        """异步执行截图回调"""
        print("[GlobalHotkey] _async_screenshot_callback 开始执行")
        if self._on_screenshot:
            try:
                result = self._on_screenshot()
                if asyncio.iscoroutine(result):
                    await result
                print("[GlobalHotkey] 截图回调执行成功")
            except Exception as e:
                print(f"[GlobalHotkey] 截图回调异常: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("[GlobalHotkey] 截图回调函数不存在")
    
    def start(self):
        """启动热键监听"""
        if self._running:
            return
        
        self._running = True
        
        # 在新线程中运行热键循环
        self._thread = threading.Thread(target=self._hotkey_loop, daemon=True)
        self._thread.start()
        
        print("[GlobalHotkey] 全局热键服务已启动 (F5=运行, Shift+F5=停止, F9=开始录制宏, F10=停止录制宏, Ctrl+Shift+F12=截图)")
    
    def stop(self):
        """停止热键监听"""
        if not self._running:
            return
        
        self._running = False
        
        # 发送退出消息
        try:
            self.user32.PostThreadMessageW(
                self._thread.ident if self._thread else 0,
                0x0012,  # WM_QUIT
                0,
                0
            )
        except:
            pass
        
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        
        print("[GlobalHotkey] 全局热键服务已停止")


# 全局单例
_hotkey_service: Optional[GlobalHotkeyService] = None


def get_hotkey_service() -> GlobalHotkeyService:
    """获取全局热键服务实例"""
    global _hotkey_service
    if _hotkey_service is None:
        _hotkey_service = GlobalHotkeyService()
    return _hotkey_service
