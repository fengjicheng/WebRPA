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


class ScrcpyManager:
    """Scrcpy 管理器类"""
    
    def __init__(self, scrcpy_path: Optional[str] = None, adb_path: Optional[str] = None):
        """初始化 Scrcpy 管理器
        
        Args:
            scrcpy_path: Scrcpy 可执行文件路径
            adb_path: ADB 可执行文件路径
        """
        if scrcpy_path:
            self.scrcpy_path = scrcpy_path
        else:
            # 使用项目内置的 Scrcpy
            project_root = Path(__file__).parent.parent.parent
            self.scrcpy_path = str(project_root / "scrcpy" / "scrcpy.exe")
        
        if adb_path:
            self.adb_path = adb_path
        else:
            project_root = Path(__file__).parent.parent.parent
            self.adb_path = str(project_root / "scrcpy" / "adb.exe")
        
        if not os.path.exists(self.scrcpy_path):
            raise FileNotFoundError(f"Scrcpy 可执行文件不存在: {self.scrcpy_path}")
        
        self.process: Optional[subprocess.Popen] = None
        self.device_id: Optional[str] = None
        self.recording: bool = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._should_monitor: bool = False
        
        print(f"[ScrcpyManager] 使用 Scrcpy 路径: {self.scrcpy_path}")
        print(f"[ScrcpyManager] 使用 ADB 路径: {self.adb_path}")
    
    def _monitor_process(self, device_id: Optional[str]):
        """监控镜像进程,当进程结束时自动关闭指针位置
        
        Args:
            device_id: 设备 ID
        """
        try:
            while self._should_monitor and self.process:
                # 检查进程是否还在运行
                if self.process.poll() is not None:
                    # 进程已结束
                    print(f"[ScrcpyManager] 检测到镜像窗口已关闭")
                    # 关闭指针位置
                    if device_id:
                        self._disable_pointer_location(device_id)
                    break
                time.sleep(1)
        except Exception as e:
            print(f"[ScrcpyManager] 监控线程异常: {str(e)}")
    
    def _enable_pointer_location(self, device_id: Optional[str] = None) -> bool:
        """开启手机的指针位置显示
        
        Args:
            device_id: 设备 ID
            
        Returns:
            是否成功
        """
        try:
            cmd = [self.adb_path]
            if device_id:
                cmd.extend(['-s', device_id])
            cmd.extend(['shell', 'settings', 'put', 'system', 'pointer_location', '1'])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"[ScrcpyManager] ✅ 已开启指针位置显示")
                return True
            else:
                print(f"[ScrcpyManager] ⚠️ 开启指针位置失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"[ScrcpyManager] ⚠️ 开启指针位置异常: {str(e)}")
            return False
    
    def _disable_pointer_location(self, device_id: Optional[str] = None) -> bool:
        """关闭手机的指针位置显示
        
        Args:
            device_id: 设备 ID
            
        Returns:
            是否成功
        """
        try:
            cmd = [self.adb_path]
            if device_id:
                cmd.extend(['-s', device_id])
            cmd.extend(['shell', 'settings', 'put', 'system', 'pointer_location', '0'])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"[ScrcpyManager] ✅ 已关闭指针位置显示")
                return True
            else:
                print(f"[ScrcpyManager] ⚠️ 关闭指针位置失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"[ScrcpyManager] ⚠️ 关闭指针位置异常: {str(e)}")
            return False
    
    def _bring_window_to_front(self, window_title: str, max_wait_seconds: int = 10) -> bool:
        """强制将窗口置顶到最前面
        
        Args:
            window_title: 窗口标题
            max_wait_seconds: 最大等待时间（秒）
            
        Returns:
            是否成功
        """
        try:
            print(f"[ScrcpyManager] 等待窗口创建: {window_title}")
            
            # 等待窗口创建，最多等待 max_wait_seconds 秒
            hwnd = None
            for i in range(max_wait_seconds * 2):  # 每0.5秒检查一次
                hwnd = win32gui.FindWindow(None, window_title)
                if hwnd:
                    print(f"[ScrcpyManager] ✅ 找到窗口句柄: {hwnd}")
                    break
                time.sleep(0.5)
            
            if not hwnd:
                print(f"[ScrcpyManager] ⚠️ 未找到窗口: {window_title}")
                return False
            
            # 强制将窗口置顶
            # 1. 先恢复窗口（如果是最小化状态）
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # 2. 将窗口设置为前台窗口
            win32gui.SetForegroundWindow(hwnd)
            
            # 3. 将窗口置顶（HWND_TOPMOST）
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
            )
            
            # 4. 再次设置为前台窗口，确保获得焦点
            win32gui.SetForegroundWindow(hwnd)
            
            print(f"[ScrcpyManager] ✅ 窗口已置顶: {window_title}")
            return True
            
        except Exception as e:
            print(f"[ScrcpyManager] ⚠️ 窗口置顶失败: {str(e)}")
            # 置顶失败不影响镜像功能，只是窗口可能不在最前面
            return False
    
    def start_mirror(self, device_id: Optional[str] = None, 
                    max_size: int = 0,
                    bit_rate: str = '8M',
                    max_fps: int = 60,
                    stay_awake: bool = True,
                    turn_screen_off: bool = False,
                    fullscreen: bool = False,
                    always_on_top: bool = True,
                    window_title: str = "手机镜像",
                    no_control: bool = False) -> tuple[bool, str]:
        """启动屏幕镜像
        
        Args:
            device_id: 设备 ID
            max_size: 最大分辨率（0 表示不限制，使用手机原始分辨率）
            bit_rate: 比特率
            max_fps: 最大帧率
            stay_awake: 保持屏幕常亮
            turn_screen_off: 关闭设备屏幕（仅镜像）
            fullscreen: 全屏显示
            always_on_top: 窗口置顶
            window_title: 窗口标题
            no_control: 禁用控制（只读模式）
            
        Returns:
            (成功与否, 错误信息)
        """
        if self.process and self.process.poll() is None:
            return False, "Scrcpy 已在运行中"
        
        # 启动镜像前,先开启指针位置显示
        self._enable_pointer_location(device_id)
        
        # 设置环境变量，确保使用正确的 ADB 和 scrcpy-server
        env = os.environ.copy()
        scrcpy_dir = os.path.dirname(self.scrcpy_path)
        env['ADB'] = self.adb_path
        env['SCRCPY_SERVER_PATH'] = os.path.join(scrcpy_dir, 'scrcpy-server')
        
        # 构建命令
        cmd = [self.scrcpy_path]
        
        if device_id:
            cmd.extend(['-s', device_id])
            self.device_id = device_id
        
        # 只有当 max_size > 0 时才添加 --max-size 参数（0 表示不限制，使用手机原始分辨率）
        if max_size > 0:
            cmd.extend(['--max-size', str(max_size)])
        
        cmd.extend([
            '--video-bit-rate', bit_rate,
            '--max-fps', str(max_fps),
            '--window-title', window_title
        ])
        
        # no_control 和 stay_awake 不能同时使用
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
        
        # no_control 已在上面处理，这里不再重复添加
        
        try:
            print(f"[ScrcpyManager] 启动命令: {' '.join(cmd)}")
            print(f"[ScrcpyManager] 环境变量 ADB: {env.get('ADB')}")
            print(f"[ScrcpyManager] 环境变量 SCRCPY_SERVER_PATH: {env.get('SCRCPY_SERVER_PATH')}")
            
            # 检查 scrcpy-server 文件是否存在
            scrcpy_server_path = env.get('SCRCPY_SERVER_PATH')
            if not os.path.exists(scrcpy_server_path):
                return False, f"❌ Scrcpy server 文件不存在: {scrcpy_server_path}\n💡 请确保 scrcpy-server 文件存在于 backend/scrcpy/ 目录中"
            
            # 不使用 CREATE_NO_WINDOW，让镜像窗口正常显示
            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待一小段时间检查是否启动成功
            time.sleep(2)
            if self.process.poll() is not None:
                # 进程已退出，读取错误信息
                stdout = self.process.stdout.read().decode('utf-8', errors='ignore') if self.process.stdout else ''
                stderr = self.process.stderr.read().decode('utf-8', errors='ignore') if self.process.stderr else ''
                error_msg = f"❌ Scrcpy 启动失败\n"
                if stderr:
                    error_msg += f"错误信息: {stderr}\n"
                if stdout:
                    error_msg += f"输出信息: {stdout}\n"
                error_msg += "\n💡 可能的原因：\n"
                error_msg += "1. 设备未正确连接或授权\n"
                error_msg += "2. scrcpy-server 文件损坏或版本不匹配\n"
                error_msg += "3. 设备 USB 调试权限不足\n"
                error_msg += "4. ADB 服务异常"
                print(f"[ScrcpyManager] {error_msg}")
                return False, error_msg
            
            print(f"[ScrcpyManager] Scrcpy 启动成功，进程ID: {self.process.pid}")
            
            # 等待窗口创建并强制置顶
            self._bring_window_to_front(window_title)
            
            # 启动监控线程,监控镜像进程是否结束
            self._should_monitor = True
            self._monitor_thread = threading.Thread(target=self._monitor_process, args=(device_id,), daemon=True)
            self._monitor_thread.start()
            
            return True, ""
            
        except FileNotFoundError as e:
            error_msg = f"❌ 找不到 Scrcpy 可执行文件: {self.scrcpy_path}\n💡 请确保 scrcpy.exe 存在于 backend/scrcpy/ 目录中"
            print(f"[ScrcpyManager] {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"❌ 启动 Scrcpy 失败: {str(e)}\n💡 请检查 Scrcpy 和 ADB 是否正确安装"
            print(f"[ScrcpyManager] {error_msg}")
            return False, error_msg
    
    def stop_mirror(self) -> tuple[bool, str]:
        """停止屏幕镜像
        
        Returns:
            (成功与否, 错误信息)
        """
        if not self.process:
            return True, ""
        
        # 保存设备ID,用于关闭指针位置
        device_id = self.device_id
        
        try:
            # 停止监控线程
            self._should_monitor = False
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=2)
            
            if self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=5)
            
            self.process = None
            self.device_id = None
            
            # 停止镜像后,关闭指针位置显示
            if device_id:
                self._disable_pointer_location(device_id)
            
            print(f"[ScrcpyManager] Scrcpy 已停止")
            return True, ""
            
        except Exception as e:
            return False, f"停止 Scrcpy 失败: {str(e)}"
    
    def start_recording(self, output_path: str, device_id: Optional[str] = None,
                       max_size: int = 1024,
                       bit_rate: str = '8M',
                       max_fps: int = 60,
                       no_display: bool = False) -> tuple[bool, str]:
        """开始录屏
        
        Args:
            output_path: 输出文件路径
            device_id: 设备 ID
            max_size: 最大分辨率
            bit_rate: 比特率
            max_fps: 最大帧率
            no_display: 不显示窗口（后台录制）
            
        Returns:
            (成功与否, 错误信息)
        """
        if self.recording:
            return False, "已在录屏中"
        
        # 设置环境变量
        env = os.environ.copy()
        scrcpy_dir = os.path.dirname(self.scrcpy_path)
        env['ADB'] = self.adb_path
        env['SCRCPY_SERVER_PATH'] = os.path.join(scrcpy_dir, 'scrcpy-server')
        
        # 构建命令
        cmd = [self.scrcpy_path]
        
        if device_id:
            cmd.extend(['-s', device_id])
        
        cmd.extend([
            '--record', output_path,
            '--max-size', str(max_size),
            '--video-bit-rate', bit_rate,
            '--max-fps', str(max_fps)
        ])
        
        if no_display:
            cmd.append('--no-display')
        
        try:
            print(f"[ScrcpyManager] 开始录屏: {' '.join(cmd)}")
            
            # 检查 scrcpy-server 文件是否存在
            scrcpy_server_path = env.get('SCRCPY_SERVER_PATH')
            if not os.path.exists(scrcpy_server_path):
                return False, f"❌ Scrcpy server 文件不存在: {scrcpy_server_path}"
            
            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待一小段时间检查是否启动成功
            time.sleep(2)
            if self.process.poll() is not None:
                stdout = self.process.stdout.read().decode('utf-8', errors='ignore') if self.process.stdout else ''
                stderr = self.process.stderr.read().decode('utf-8', errors='ignore') if self.process.stderr else ''
                error_msg = f"❌ 录屏启动失败\n"
                if stderr:
                    error_msg += f"错误信息: {stderr}\n"
                if stdout:
                    error_msg += f"输出信息: {stdout}"
                print(f"[ScrcpyManager] {error_msg}")
                return False, error_msg
            
            self.recording = True
            print(f"[ScrcpyManager] 录屏已开始，进程ID: {self.process.pid}")
            return True, ""
            
        except Exception as e:
            error_msg = f"❌ 开始录屏失败: {str(e)}"
            print(f"[ScrcpyManager] {error_msg}")
            return False, error_msg
    
    def stop_recording(self) -> tuple[bool, str]:
        """停止录屏
        
        Returns:
            (成功与否, 错误信息)
        """
        if not self.recording:
            return True, ""
        
        success, error = self.stop_mirror()
        if success:
            self.recording = False
        
        return success, error
    
    def is_running(self) -> bool:
        """检查 Scrcpy 是否正在运行
        
        Returns:
            是否正在运行
        """
        return self.process is not None and self.process.poll() is None
    
    def get_status(self) -> Dict[str, any]:
        """获取 Scrcpy 状态
        
        Returns:
            状态信息
        """
        return {
            'running': self.is_running(),
            'recording': self.recording,
            'device_id': self.device_id
        }


# 全局 Scrcpy 管理器实例
_scrcpy_manager: Optional[ScrcpyManager] = None


def get_scrcpy_manager() -> ScrcpyManager:
    """获取全局 Scrcpy 管理器实例"""
    global _scrcpy_manager
    if _scrcpy_manager is None:
        _scrcpy_manager = ScrcpyManager()
    return _scrcpy_manager
