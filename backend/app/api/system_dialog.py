"""系统对话框相关API - 文件/文件夹选择"""
import subprocess
import sys
import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/system", tags=["system-dialog"])


class OpenUrlRequest(BaseModel):
    url: str


class FolderSelectRequest(BaseModel):
    title: Optional[str] = "选择文件夹"
    initialDir: Optional[str] = None


class FileSelectRequest(BaseModel):
    title: Optional[str] = "选择文件"
    initialDir: Optional[str] = None
    fileTypes: Optional[list[tuple[str, str]]] = None


def select_folder_windows(title: str, initial_dir: str = None) -> str:
    """使用现代 Windows 资源管理器风格的文件夹选择对话框"""
    import tempfile
    import os
    
    logger.info(f"[文件夹选择器] 开始选择文件夹，标题: {title}")
    
    # PowerShell脚本，使用Windows Forms并确保对话框置顶
    ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
$fb = New-Object System.Windows.Forms.FolderBrowserDialog
$fb.Description = "{title}"
$fb.ShowNewFolderButton = $true
{f'$fb.SelectedPath = "{initial_dir}"' if initial_dir else ''}
$fb.RootFolder = [System.Environment+SpecialFolder]::MyComputer

# 创建一个置顶的窗口作为父窗口
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Win32 {{
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
}}
"@

# 创建一个不可见的Form作为父窗口，并设置为TopMost
$form = New-Object System.Windows.Forms.Form
$form.TopMost = $true
$form.ShowInTaskbar = $false
$form.WindowState = [System.Windows.Forms.FormWindowState]::Minimized

$result = $fb.ShowDialog($form)
$form.Dispose()

if ($result -eq [System.Windows.Forms.DialogResult]::OK) {{
    Write-Output $fb.SelectedPath
}}
'''
    
    ps_file = None
    try:
        # 创建临时PowerShell脚本文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8-sig') as f:
            f.write(ps_script)
            ps_file = f.name
        
        logger.info(f"[文件夹选择器] PowerShell脚本已创建: {ps_file}")
        
        # 执行PowerShell脚本（使用-STA参数以支持Windows Forms）
        result = subprocess.run(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-STA", "-NoProfile", "-File", ps_file],
            capture_output=True,
            text=True,
            encoding='utf-8',
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
            timeout=300  # 5分钟超时
        )
        
        logger.info(f"[文件夹选择器] PowerShell执行完成，返回码: {result.returncode}")
        
        if result.stderr:
            logger.warning(f"[文件夹选择器] PowerShell错误输出: {result.stderr}")
        
        selected_path = result.stdout.strip()
        
        if selected_path:
            logger.info(f"[文件夹选择器] 用户选择了文件夹: {selected_path}")
            return selected_path
        else:
            logger.info("[文件夹选择器] 用户取消了选择")
            return ""
            
    except subprocess.TimeoutExpired:
        logger.error("[文件夹选择器] PowerShell执行超时")
        return ""
    except Exception as e:
        logger.error(f"[文件夹选择器] 执行失败: {str(e)}", exc_info=True)
        return ""
    finally:
        # 清理临时文件
        if ps_file and os.path.exists(ps_file):
            try:
                os.unlink(ps_file)
                logger.debug(f"[文件夹选择器] 已删除临时文件: {ps_file}")
            except Exception as e:
                logger.warning(f"[文件夹选择器] 删除临时文件失败: {e}")


def select_file_windows(title: str, initial_dir: str = None, file_filter: str = None) -> str:
    """使用 PowerShell 打开文件选择对话框"""
    import tempfile
    import os
    
    logger.info(f"[文件选择器] 开始选择文件，标题: {title}, 初始目录: {initial_dir}, 过滤器: {file_filter}")
    
    # PowerShell脚本，使用Windows Forms并确保对话框置顶
    ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
$openFileDialog = New-Object System.Windows.Forms.OpenFileDialog
$openFileDialog.Title = "{title}"
{f'$openFileDialog.InitialDirectory = "{initial_dir}"' if initial_dir else ''}
{f'$openFileDialog.Filter = "{file_filter}"' if file_filter else '$openFileDialog.Filter = "所有文件 (*.*)|*.*"'}

# 创建一个置顶的窗口作为父窗口
$form = New-Object System.Windows.Forms.Form
$form.TopMost = $true
$form.ShowInTaskbar = $false
$form.WindowState = [System.Windows.Forms.FormWindowState]::Minimized

$result = $openFileDialog.ShowDialog($form)
$form.Dispose()

if ($result -eq [System.Windows.Forms.DialogResult]::OK) {{
    Write-Output $openFileDialog.FileName
}}
'''
    
    ps_file = None
    try:
        # 创建临时PowerShell脚本文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8-sig') as f:
            f.write(ps_script)
            ps_file = f.name
        
        logger.info(f"[文件选择器] PowerShell脚本已创建: {ps_file}")
        
        # 执行PowerShell脚本（使用-STA参数以支持Windows Forms）
        result = subprocess.run(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-STA", "-NoProfile", "-File", ps_file],
            capture_output=True,
            text=True,
            encoding='utf-8',
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
            timeout=300  # 5分钟超时
        )
        
        logger.info(f"[文件选择器] PowerShell执行完成，返回码: {result.returncode}")
        
        if result.stderr:
            logger.warning(f"[文件选择器] PowerShell错误输出: {result.stderr}")
        
        selected_path = result.stdout.strip()
        
        if selected_path:
            logger.info(f"[文件选择器] 用户选择了文件: {selected_path}")
            return selected_path
        else:
            logger.info("[文件选择器] 用户取消了选择")
            return ""
            
    except subprocess.TimeoutExpired:
        logger.error("[文件选择器] PowerShell执行超时")
        return ""
    except Exception as e:
        logger.error(f"[文件选择器] 执行失败: {str(e)}", exc_info=True)
        return ""
    finally:
        # 清理临时文件
        if ps_file and os.path.exists(ps_file):
            try:
                os.unlink(ps_file)
                logger.debug(f"[文件选择器] 已删除临时文件: {ps_file}")
            except Exception as e:
                logger.warning(f"[文件选择器] 删除临时文件失败: {e}")


@router.post("/open-url")
async def open_url(request: OpenUrlRequest):
    """使用系统默认浏览器打开URL"""
    import webbrowser
    try:
        webbrowser.open(request.url)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/select-folder")
async def select_folder(request: FolderSelectRequest):
    """打开文件夹选择对话框"""
    try:
        logger.info(f"[API] 收到文件夹选择请求: {request}")
        
        folder_path = select_folder_windows(
            title=request.title or "选择文件夹",
            initial_dir=request.initialDir
        )
        
        if folder_path:
            logger.info(f"[API] 文件夹选择成功: {folder_path}")
            return {"success": True, "path": folder_path}
        else:
            logger.info("[API] 用户取消了文件夹选择")
            return {"success": False, "path": None, "message": "用户取消选择"}
    except Exception as e:
        logger.error(f"[API] 文件夹选择失败: {str(e)}", exc_info=True)
        return {"success": False, "path": None, "error": str(e)}


@router.post("/select-file")
async def select_file(request: FileSelectRequest):
    """打开文件选择对话框"""
    try:
        logger.info(f"[API] 收到文件选择请求: {request}")
        
        file_filter = None
        if request.fileTypes:
            filter_parts = []
            for desc, pattern in request.fileTypes:
                filter_parts.append(f"{desc}|{pattern}")
            file_filter = "|".join(filter_parts)
        
        file_path = select_file_windows(
            title=request.title or "选择文件",
            initial_dir=request.initialDir,
            file_filter=file_filter
        )
        
        if file_path:
            logger.info(f"[API] 文件选择成功: {file_path}")
            return {"success": True, "path": file_path}
        else:
            logger.info("[API] 用户取消了文件选择")
            return {"success": False, "path": None, "message": "用户取消选择"}
    except Exception as e:
        logger.error(f"[API] 文件选择失败: {str(e)}", exc_info=True)
        return {"success": False, "path": None, "error": str(e)}
