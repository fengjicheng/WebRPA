"""媒体处理工具函数 - FFmpeg相关"""
import asyncio
import os
import subprocess
import re
from typing import Optional, Callable

from .base import get_ffmpeg_path, get_ffprobe_path


# 全局进程管理器 - 跟踪所有运行中的 FFmpeg 进程
class FFmpegProcessManager:
    """FFmpeg 进程管理器，用于跟踪和清理进程"""
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._processes: dict[int, subprocess.Popen] = {}
            cls._instance._process_id = 0
        return cls._instance
    
    async def register(self, process: subprocess.Popen) -> int:
        """注册一个新进程，返回进程ID"""
        async with self._lock:
            self._process_id += 1
            pid = self._process_id
            self._processes[pid] = process
            return pid
    
    async def unregister(self, pid: int):
        """注销进程"""
        async with self._lock:
            if pid in self._processes:
                del self._processes[pid]
    
    async def terminate_all(self):
        """终止所有正在运行的 FFmpeg 进程"""
        async with self._lock:
            for pid, process in list(self._processes.items()):
                try:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            process.kill()
                except Exception as e:
                    print(f"终止 FFmpeg 进程 {pid} 失败: {e}")
            self._processes.clear()
    
    def get_running_count(self) -> int:
        """获取正在运行的进程数量"""
        return sum(1 for p in self._processes.values() if p.poll() is None)


# 全局进程管理器实例
ffmpeg_manager = FFmpegProcessManager()


def get_media_duration(input_path: str) -> Optional[float]:
    """获取媒体文件时长（秒）"""
    ffprobe = get_ffprobe_path()
    print(f"[DEBUG] 获取媒体时长: {input_path}")
    try:
        result = subprocess.run(
            [ffprobe, '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', input_path],
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        if result.returncode == 0 and result.stdout.strip():
            duration = float(result.stdout.strip())
            print(f"[DEBUG] 媒体时长: {duration} 秒")
            return duration
        else:
            print(f"[DEBUG] 获取时长失败: returncode={result.returncode}, stderr={result.stderr}")
    except Exception as e:
        print(f"[DEBUG] 获取时长异常: {e}")
    return None


async def run_ffmpeg_with_progress(
    args: list, 
    timeout: int = 600,
    on_progress: Optional[Callable[[float, str], None]] = None,
    total_duration: Optional[float] = None,
    context: Optional['ExecutionContext'] = None
) -> tuple[bool, str]:
    """
    运行 ffmpeg 命令，支持进度回调
    
    Args:
        args: ffmpeg 参数列表
        timeout: 超时时间（秒）
        on_progress: 进度回调函数 (progress_percent, status_message) - 同步回调
        total_duration: 总时长（秒），用于计算进度
        context: 执行上下文，用于发送进度日志到前端
    
    Returns:
        (success, message)
    """
    import time as time_module
    
    ffmpeg = get_ffmpeg_path()
    print(f"[DEBUG] FFmpeg 路径: {ffmpeg}")
    print(f"[DEBUG] FFmpeg 参数: {args}")
    
    cmd = [ffmpeg, '-y'] + args
    print(f"[DEBUG] 完整命令: {' '.join(cmd)}")
    
    process = None
    pid = None
    stderr_output = []
    last_progress_msg = ['']
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        print(f"[DEBUG] FFmpeg 进程已启动, PID: {process.pid}")
        pid = await ffmpeg_manager.register(process)
        
        loop = asyncio.get_running_loop()
        start_time = time_module.time()
        progress_data = {'percent': 0, 'msg': '', 'updated': False}
        
        def read_stderr():
            """读取 stderr 输出"""
            last_update_time = -10
            buffer = ""
            line_count = 0
            
            try:
                while True:
                    char = process.stderr.read(1)
                    if not char:
                        break
                    
                    char_str = char.decode('utf-8', errors='ignore')
                    
                    if char_str == '\r' or char_str == '\n':
                        line_str = buffer.strip()
                        buffer = ""
                        
                        if not line_str:
                            continue
                        
                        line_count += 1
                        stderr_output.append(line_str)
                        
                        if line_count <= 5 or line_count % 50 == 0:
                            print(f"[DEBUG] FFmpeg 输出 #{line_count}: {line_str[:100]}")
                        
                        size_match = re.search(r'size=\s*(\d+)kB', line_str)
                        time_match = re.search(r'time=(\d+):(\d+):(\d+\.?\d*)', line_str)
                        speed_match = re.search(r'speed=\s*([\d.]+)x', line_str)
                        bitrate_match = re.search(r'bitrate=\s*([\d.]+)kbits/s', line_str)
                        
                        if time_match:
                            hours = int(time_match.group(1))
                            minutes = int(time_match.group(2))
                            seconds = float(time_match.group(3))
                            current_time = hours * 3600 + minutes * 60 + seconds
                            
                            if total_duration and total_duration > 0:
                                progress = min(99.9, (current_time / total_duration) * 100)
                                elapsed = time_module.time() - start_time
                                
                                if elapsed - last_update_time >= 3:
                                    last_update_time = elapsed
                                    if progress > 0:
                                        eta = (elapsed / progress) * (100 - progress)
                                        msg = f"处理中 {progress:.1f}%，预计剩余 {eta:.0f}秒"
                                    else:
                                        msg = "处理中..."
                                    
                                    progress_data['percent'] = progress
                                    progress_data['msg'] = msg
                                    progress_data['updated'] = True
                                    last_progress_msg[0] = msg
                                    print(f"[DEBUG] FFmpeg 进度: {msg}")
                                    
                                    if on_progress:
                                        on_progress(progress, msg)
                            else:
                                elapsed = time_module.time() - start_time
                                if elapsed - last_update_time >= 3:
                                    last_update_time = elapsed
                                    time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                                    msg_parts = [f"已处理 {time_str}"]
                                    
                                    if size_match:
                                        size_kb = int(size_match.group(1))
                                        if size_kb < 1024:
                                            msg_parts.append(f"大小 {size_kb}KB")
                                        else:
                                            msg_parts.append(f"大小 {size_kb/1024:.1f}MB")
                                    
                                    if speed_match:
                                        speed = float(speed_match.group(1))
                                        msg_parts.append(f"速度 {speed:.1f}x")
                                    
                                    if bitrate_match:
                                        bitrate = float(bitrate_match.group(1))
                                        if bitrate < 1024:
                                            msg_parts.append(f"码率 {bitrate:.0f}kbps")
                                        else:
                                            msg_parts.append(f"码率 {bitrate/1024:.1f}Mbps")
                                    
                                    msg = "，".join(msg_parts)
                                    progress_data['msg'] = msg
                                    progress_data['updated'] = True
                                    last_progress_msg[0] = msg
                                    print(f"[DEBUG] FFmpeg 进度: {msg}")
                                    
                                    if on_progress:
                                        on_progress(0, msg)
                        
                        if 'error' in line_str.lower() or 'invalid' in line_str.lower():
                            print(f"[DEBUG] FFmpeg 可能的错误: {line_str}")
                    else:
                        buffer += char_str
                
                print(f"[DEBUG] FFmpeg stderr 读取完成，共 {line_count} 行")
                        
            except Exception as e:
                print(f"[DEBUG] 读取 stderr 异常: {e}")
                import traceback
                traceback.print_exc()
            
            return process.wait()
        
        async def send_progress_periodically():
            """定期发送进度更新到前端"""
            last_sent = ''
            check_count = 0
            try:
                while True:
                    await asyncio.sleep(2)
                    check_count += 1
                    current_msg = last_progress_msg[0]
                    
                    if check_count <= 3 or check_count % 5 == 0:
                        print(f"[DEBUG] 进度检查 #{check_count}: msg='{current_msg}', last_sent='{last_sent}'")
                    
                    if current_msg and current_msg != last_sent:
                        last_sent = current_msg
                        print(f"[DEBUG] 准备发送进度到前端: {current_msg}")
                        if context:
                            try:
                                await context.send_progress(f"🎬 {current_msg}")
                                print(f"[DEBUG] 进度已发送到前端")
                            except Exception as e:
                                print(f"[DEBUG] 发送进度失败: {e}")
            except asyncio.CancelledError:
                print(f"[DEBUG] 进度发送任务已取消，共检查 {check_count} 次")
                raise
        
        progress_task = asyncio.create_task(send_progress_periodically())
        
        try:
            return_code = await asyncio.wait_for(
                loop.run_in_executor(None, read_stderr),
                timeout=timeout
            )
            print(f"[DEBUG] FFmpeg 返回码: {return_code}")
        except asyncio.TimeoutError:
            print(f"[DEBUG] FFmpeg 执行超时")
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except Exception:
                    process.kill()
            return False, "FFmpeg 执行超时"
        except asyncio.CancelledError:
            print(f"[DEBUG] FFmpeg 任务被取消")
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except Exception:
                    process.kill()
            raise
        finally:
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass
        
        if return_code == 0:
            print(f"[DEBUG] FFmpeg 执行成功")
            return True, ""
        else:
            error_msg = '\n'.join(stderr_output[-20:])
            print(f"[DEBUG] FFmpeg 执行失败: {error_msg}")
            return False, error_msg
            
    except asyncio.CancelledError:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except Exception:
                process.kill()
        raise
    except Exception as e:
        print(f"[DEBUG] FFmpeg 异常: {e}")
        import traceback
        traceback.print_exc()
        if process and process.poll() is None:
            process.terminate()
        return False, str(e)
    finally:
        if pid is not None:
            await ffmpeg_manager.unregister(pid)


def run_ffmpeg(args: list, timeout: int = 600) -> tuple[bool, str]:
    """运行ffmpeg命令（同步版本，用于简单操作）"""
    ffmpeg = get_ffmpeg_path()
    cmd = [ffmpeg, '-y'] + args
    
    print(f"[DEBUG] 同步 FFmpeg 命令: {' '.join(cmd)}")
    
    process = None
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        stdout, stderr = process.communicate(timeout=timeout)
        
        if process.returncode == 0:
            print(f"[DEBUG] 同步 FFmpeg 执行成功")
            return True, stdout.decode('utf-8', errors='ignore')
        else:
            error_msg = stderr.decode('utf-8', errors='ignore')
            print(f"[DEBUG] 同步 FFmpeg 执行失败: {error_msg[-500:]}")
            return False, error_msg
    except subprocess.TimeoutExpired:
        if process:
            process.terminate()
            try:
                process.wait(timeout=2)
            except Exception:
                process.kill()
        return False, "FFmpeg执行超时"
    except Exception as e:
        print(f"[DEBUG] 同步 FFmpeg 异常: {e}")
        if process and process.poll() is None:
            process.terminate()
        return False, str(e)
