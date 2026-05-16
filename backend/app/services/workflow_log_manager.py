"""
工作流日志管理器
用于管理工作流执行时的日志，支持写入文件和批量读取
"""
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import threading


class WorkflowLogManager:
    """工作流日志管理器"""
    
    def __init__(self):
        self.log_dir = Path(__file__).parent.parent.parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        self.current_log_file: Optional[Path] = None
        self.is_workflow_running = False
        self.lock = threading.Lock()
        
    def start_workflow_logging(self) -> str:
        """
        开始工作流日志记录
        返回日志文件路径
        """
        with self.lock:
            # 创建新的日志文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_log_file = self.log_dir / f"workflow_{timestamp}.log"
            
            # 清空文件内容（如果存在）
            with open(self.current_log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== 工作流执行日志 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            
            self.is_workflow_running = True
            return str(self.current_log_file)
    
    def write_log(self, message: str):
        """
        写入日志到文件
        """
        if not self.is_workflow_running or not self.current_log_file:
            return
        
        try:
            with open(self.current_log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime("%H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"[WorkflowLogManager] 写入日志失败: {e}")
    
    def stop_workflow_logging(self) -> Optional[str]:
        """
        停止工作流日志记录
        返回日志文件路径
        """
        with self.lock:
            self.is_workflow_running = False
            log_file = self.current_log_file
            self.current_log_file = None
            return str(log_file) if log_file else None
    
    def read_workflow_logs(self, log_file: Optional[str] = None) -> list[str]:
        """
        读取工作流日志
        如果不指定文件，读取当前日志文件
        """
        target_file = Path(log_file) if log_file else self.current_log_file
        
        if not target_file or not target_file.exists():
            return []
        
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return [line.rstrip('\n') for line in lines]
        except Exception as e:
            print(f"[WorkflowLogManager] 读取日志失败: {e}")
            return []
    
    def clear_old_logs(self, keep_days: int = 7):
        """
        清理旧日志文件
        保留最近N天的日志
        """
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=keep_days)
            
            for log_file in self.log_dir.glob("workflow_*.log"):
                if log_file.stat().st_mtime < cutoff_time.timestamp():
                    log_file.unlink()
        except Exception as e:
            print(f"[WorkflowLogManager] 清理旧日志失败: {e}")


# 全局单例
workflow_log_manager = WorkflowLogManager()
