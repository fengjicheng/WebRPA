"""Scrcpy 管理器 - 管理手机屏幕镜像和录屏"""
import subprocess
import os
import time
import threading
from pathlib import Path
from typing import Optional, Dict
import psutil
import win32gui
import win32con


class ScrcpyInstance:
    """单个 Scrcpy 镜像实例"""
    
    def __init__(self, device_id: str, scrcpy_path: str, adb_path: str):
        """初始化 Scrcpy 实例
        
        Args:
            device_id: 设备 ID
            scrcpy_path: Scrcpy 可执行文件路径
            adb_path: ADB 可执行文件路径
        """
        self.device_id = device_id
        self.scrcpy_path = scrcpy_path
        self.adb_path = adb_path
        self.process: Optional[subprocess.Popen] = None
        self.recording: bool = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._should_monitor: bool = False
        self._pointer_location_enabled: bool = False
    
    def _monitor_process(self):
        """监控镜像进程,当进程结束时自动关闭指针位置"""
        try:
            while self._should_monitor and self.process:
                if self.process.poll() is not None:
                    print(f"[ScrcpyInstance] 设备 {self.device_id} 镜像窗口已关闭")
                    if self._pointer_location_enabled:
                        self._disable_pointer_location()
                        self._pointer_location_enabled = False
                    break
                time.sleep(1)
        except Exception as e:
            print(f"[ScrcpyInstance] 监控线程异常: {str(e)}")
    
    def _enable_pointer_location(self) -> bool:
        """开启手机的指针位置显示"""
        try:
            cmd = [self.adb_path, '-s', self.device_id, 'shell', 'settings', 'put', 'system', 'pointer_location', '1']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"[ScrcpyInstance] ✅ 设备 {self.device_id} 已开启指针位置显示")
                return True
            else:
                print(f"[ScrcpyInstance] ⚠️ 设备 {self.device_id} 开启指针位置失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"[ScrcpyInstance] ⚠️ 设备 {self.device_id} 开启指针位置异常: {str(e)}")
            return False
    
    def _disable_pointer_location(self) -> bool:
        """关闭手机的指针位置显示"""
        try:
            cmd = [self.adb_path, '-s', self.device_id, 'shell', 'settings', 'put', 'system', 'pointer_location', '0']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"[ScrcpyInstance] ✅ 设备 {self.device_id} 已关闭指针位置显示")
                return True
            else:
                print(f"[ScrcpyInstance] ⚠️ 设备 {self.device_id} 关闭指针位置失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"[ScrcpyInstance] ⚠️ 设备 {self.device_id} 关闭指针位置异常: {str(e)}")
            return False
    
    def _bring_window_to_front(self, window_title: str, max_wait_seconds: int = 10) -> bool:
        """强制将窗口置顶到最前面"""
        try:
            print(f"[ScrcpyInstance] 等待窗口创建: {window_title}")
            hwnd = None
            for i in range(max_wait_seconds * 2):
                hwnd = win32gui.FindWindow(None, window_title)
                if hwnd:
                    print(f"[ScrcpyInstance] ✅ 找到窗口句柄: {hwnd}")
                    break
                time.sleep(0.5)
            
            if not hwnd:
                print(f"[ScrcpyInstance] ⚠️ 未找到窗口: {window_title}")
                return False
            
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            win32gui.SetForegroundWindow(hwnd)
            
            print(f"[ScrcpyInstance] ✅ 窗口已置顶: {window_title}")
            return True
        except Exception as e:
            print(f"[ScrcpyInstance] ⚠️ 窗口置顶失败: {str(e)}")
            return False
    
    def start(self, max_size: int = 0, bit_rate: str = '8M', max_fps: int = 60,
             stay_awake: bool = True, turn_screen_off: bool = False, fullscreen: bool = False,
             always_on_top: bool = True, window_title: str = "手机镜像", no_control: bool = False,
             enable_pointer_location: bool = True) -> tuple[bool, str]:
        """启动镜像"""
        print(f"[ScrcpyInstance] start 被调用: device_id={self.device_id}, enable_pointer_location={enable_pointer_location}")
        
        if self.process and self.process.poll() is None:
            return False, f"设备 {self.device_id} 的镜像已在运行中"
        
        if enable_pointer_location:
            print(f"[ScrcpyInstance] 开启指针位置...")
            self._enable_pointer_location()
            self._pointer_location_enabled = True
        else:
            print(f"[ScrcpyInstance] 不开启指针位置")
            self._pointer_location_enabled = False
        
        env = os.environ.copy()
        scrcpy_dir = os.path.dirname(self.scrcpy_path)
        env['ADB'] = self.adb_path
        env['SCRCPY_SERVER_PATH'] = os.path.join(scrcpy_dir, 'scrcpy-server')
        
        cmd = [self.scrcpy_path, '-s', self.device_id]
        
        if max_size > 0:
            cmd.extend(['--max-size', str(max_size)])
        
        cmd.extend([
            '--video-bit-rate', bit_rate,
            '--max-fps', str(max_fps),
            '--window-title', window_title
        ])
        
        if no_control:
            cmd.append('--no-control')
        elif stay_awake:
            cmd.append('--stay-awake')
        
        if turn_screen_off:
            cmd.append('--turn-screen-off')
        if fullscreen:
            cmd.append('--fullscreen')
        if always_on_top:
            cmd.append('--always-on-top')
        
        try:
            print(f"[ScrcpyInstance] 启动设备 {self.device_id} 的镜像: {' '.join(cmd)}")
            
            scrcpy_server_path = env.get('SCRCPY_SERVER_PATH')
            if not os.path.exists(scrcpy_server_path):
                return False, f"❌ Scrcpy server 文件不存在: {scrcpy_server_path}"
            
            self.process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            time.sleep(2)
            if self.process.poll() is not None:
                stdout = self.process.stdout.read().decode('utf-8', errors='ignore') if self.process.stdout else ''
                stderr = self.process.stderr.read().decode('utf-8', errors='ignore') if self.process.stderr else ''
                error_msg = f"❌ 设备 {self.device_id} 镜像启动失败\n"
                if stderr:
                    error_msg += f"错误信息: {stderr}\n"
                if stdout:
                    error_msg += f"输出信息: {stdout}"
                print(f"[ScrcpyInstance] {error_msg}")
                return False, error_msg
            
            print(f"[ScrcpyInstance] 设备 {self.device_id} 镜像启动成功，进程ID: {self.process.pid}")
            self._bring_window_to_front(window_title)
            
            self._should_monitor = True
            self._monitor_thread = threading.Thread(target=self._monitor_process, daemon=True)
            self._monitor_thread.start()
            
            return True, ""
        except Exception as e:
            error_msg = f"❌ 启动设备 {self.device_id} 镜像失败: {str(e)}"
            print(f"[ScrcpyInstance] {error_msg}")
            return False, error_msg
    
    def stop(self) -> tuple[bool, str]:
        """停止镜像"""
        if not self.process:
            return True, ""
        
        pointer_location_enabled = self._pointer_location_enabled
        
        try:
            self._should_monitor = False
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=2)
            
            if self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=5)
            
            self.process = None
            
            if pointer_location_enabled:
                self._disable_pointer_location()
                self._pointer_location_enabled = False
            
            print(f"[ScrcpyInstance] 设备 {self.device_id} 镜像已停止")
            return True, ""
        except Exception as e:
            return False, f"停止设备 {self.device_id} 镜像失败: {str(e)}"
    
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self.process is not None and self.process.poll() is None


class ScrcpyManager:
    """Scrcpy 管理器类 - 支持多设备镜像"""
    
    def __init__(self, scrcpy_path: Optional[str] = None, adb_path: Optional[str] = None):
        """初始化 Scrcpy 管理器"""
        if scrcpy_path:
            self.scrcpy_path = scrcpy_path
        else:
            project_root = Path(__file__).parent.parent.parent
            self.scrcpy_path = str(project_root / "scrcpy" / "scrcpy.exe")
        
        if adb_path:
            self.adb_path = adb_path
        else:
            project_root = Path(__file__).parent.parent.parent
            self.adb_path = str(project_root / "scrcpy" / "adb.exe")
        
        if not os.path.exists(self.scrcpy_path):
            raise FileNotFoundError(f"Scrcpy 可执行文件不存在: {self.scrcpy_path}")
        
        # 存储每个设备的镜像实例
        self.instances: Dict[str, ScrcpyInstance] = {}
        
        # 为了兼容旧代码，保留这些属性
        self.process: Optional[subprocess.Popen] = None
        self.device_id: Optional[str] = None
        self.recording: bool = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._should_monitor: bool = False
        self._pointer_location_enabled: bool = False
        
        print(f"[ScrcpyManager] 使用 Scrcpy 路径: {self.scrcpy_path}")
        print(f"[ScrcpyManager] 使用 ADB 路径: {self.adb_path}")
    
    def _get_or_create_instance(self, device_id: str) -> ScrcpyInstance:
        """获取或创建设备的镜像实例"""
        if device_id not in self.instances:
            self.instances[device_id] = ScrcpyInstance(device_id, self.scrcpy_path, self.adb_path)
        return self.instances[device_id]
    
    def start_mirror(self, device_id: Optional[str] = None, 
                    max_size: int = 0,
                    bit_rate: str = '8M',
                    max_fps: int = 60,
                    stay_awake: bool = True,
                    turn_screen_off: bool = False,
                    fullscreen: bool = False,
                    always_on_top: bool = True,
                    window_title: str = "手机镜像",
                    no_control: bool = False,
                    enable_pointer_location: bool = True) -> tuple[bool, str]:
        """启动屏幕镜像（支持多设备）"""
        if not device_id:
            return False, "必须指定设备ID"
        
        instance = self._get_or_create_instance(device_id)
        success, error = instance.start(
            max_size=max_size,
            bit_rate=bit_rate,
            max_fps=max_fps,
            stay_awake=stay_awake,
            turn_screen_off=turn_screen_off,
            fullscreen=fullscreen,
            always_on_top=always_on_top,
            window_title=window_title,
            no_control=no_control,
            enable_pointer_location=enable_pointer_location
        )
        
        # 为了兼容旧代码，更新这些属性
        if success:
            self.process = instance.process
            self.device_id = device_id
        
        return success, error
    
    def stop_mirror(self, device_id: Optional[str] = None) -> tuple[bool, str]:
        """停止屏幕镜像（支持多设备）"""
        if device_id:
            # 停止指定设备的镜像
            if device_id in self.instances:
                instance = self.instances[device_id]
                success, error = instance.stop()
                if success:
                    del self.instances[device_id]
                    # 如果停止的是当前设备，清空旧属性
                    if self.device_id == device_id:
                        self.process = None
                        self.device_id = None
                return success, error
            return True, ""
        else:
            # 兼容旧代码：停止所有镜像
            errors = []
            for dev_id in list(self.instances.keys()):
                success, error = self.stop_mirror(dev_id)
                if not success:
                    errors.append(f"{dev_id}: {error}")
            
            if errors:
                return False, "; ".join(errors)
            return True, ""
    
    def is_running(self, device_id: Optional[str] = None) -> bool:
        """检查镜像是否正在运行"""
        if device_id:
            if device_id in self.instances:
                return self.instances[device_id].is_running()
            return False
        else:
            # 兼容旧代码：检查是否有任何镜像在运行
            return any(inst.is_running() for inst in self.instances.values())
    
    def get_status(self, device_id: Optional[str] = None) -> Dict[str, any]:
        """获取镜像状态"""
        if device_id:
            if device_id in self.instances:
                instance = self.instances[device_id]
                return {
                    'running': instance.is_running(),
                    'recording': instance.recording,
                    'device_id': device_id
                }
            return {'running': False, 'recording': False, 'device_id': device_id}
        else:
            # 返回所有设备的状态
            return {
                'devices': {
                    dev_id: {
                        'running': inst.is_running(),
                        'recording': inst.recording
                    }
                    for dev_id, inst in self.instances.items()
                },
                # 兼容旧代码
                'running': any(inst.is_running() for inst in self.instances.values()),
                'recording': self.recording,
                'device_id': self.device_id
            }
    
    # 保留旧的方法以兼容现有代码
    def _monitor_process(self, device_id: Optional[str]):
        """兼容旧代码的监控方法"""
        pass
    
    def _enable_pointer_location(self, device_id: Optional[str] = None) -> bool:
        """兼容旧代码"""
        if device_id and device_id in self.instances:
            return self.instances[device_id]._enable_pointer_location()
        return False
    
    def _disable_pointer_location(self, device_id: Optional[str] = None) -> bool:
        """兼容旧代码"""
        if device_id and device_id in self.instances:
            return self.instances[device_id]._disable_pointer_location()
        return False
    
    def _bring_window_to_front(self, window_title: str, max_wait_seconds: int = 10) -> bool:
        """兼容旧代码"""
        return True
    
    def start_recording(self, output_path: str, device_id: Optional[str] = None,
                       max_size: int = 1024,
                       bit_rate: str = '8M',
                       max_fps: int = 60,
                       no_display: bool = False) -> tuple[bool, str]:
        """开始录屏（暂不支持多设备）"""
        return False, "录屏功能暂不支持多设备"
    
    def stop_recording(self) -> tuple[bool, str]:
        """停止录屏"""
        return True, ""


# 全局 Scrcpy 管理器实例
_scrcpy_manager: Optional[ScrcpyManager] = None


def get_scrcpy_manager() -> ScrcpyManager:
    """获取全局 Scrcpy 管理器实例"""
    global _scrcpy_manager
    if _scrcpy_manager is None:
        _scrcpy_manager = ScrcpyManager()
    return _scrcpy_manager
