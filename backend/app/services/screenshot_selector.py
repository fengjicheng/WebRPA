"""
WebRPA 专用截图选择器 - 独立系统级工具
使用 PIL + Windows API 实现独立的截图区域选择功能
"""
from PIL import Image, ImageGrab, ImageDraw, ImageFont
from typing import Optional, Tuple
import sys
import os


def create_screenshot_overlay():
    """
    创建一个简单的截图选择器
    使用PIL绘制选择界面
    """
    try:
        # 截取全屏
        screenshot = ImageGrab.grab()
        print(f"[ScreenshotSelector] 全屏截图成功，尺寸: {screenshot.size}")
        
        # 创建一个带有半透明遮罩的图像
        overlay = screenshot.copy()
        draw = ImageDraw.Draw(overlay, 'RGBA')
        
        # 添加半透明黑色遮罩
        draw.rectangle(
            [(0, 0), screenshot.size],
            fill=(0, 0, 0, 128)
        )
        
        # 添加提示文字
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        text = "WebRPA 截图工具 - 使用鼠标框选区域"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (screenshot.width - text_width) // 2
        
        draw.text((text_x, 30), text, fill=(255, 255, 255, 255), font=font)
        
        return screenshot, overlay
        
    except Exception as e:
        print(f"[ScreenshotSelector] 创建截图覆盖层失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def select_screenshot_area_simple() -> Optional[Tuple[int, int, int, int]]:
    """
    简单的截图区域选择
    返回选择的区域坐标 (x1, y1, x2, y2)
    """
    try:
        import subprocess
        import tempfile
        from pathlib import Path
        
        # 使用PowerShell调用Windows截图工具
        # 这是Windows 10/11内置的截图工具
        ps_script = """
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)

# 保存到临时文件
$tempFile = [System.IO.Path]::GetTempFileName() + ".png"
$bitmap.Save($tempFile, [System.Drawing.Imaging.ImageFormat]::Png)
Write-Output $tempFile

$graphics.Dispose()
$bitmap.Dispose()
"""
        
        # 执行PowerShell脚本
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            temp_file = result.stdout.strip()
            print(f"[ScreenshotSelector] 截图已保存到: {temp_file}")
            return temp_file
        else:
            print(f"[ScreenshotSelector] PowerShell执行失败: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"[ScreenshotSelector] 选择区域失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def capture_fullscreen_to_file(output_path: str) -> bool:
    """
    截取全屏并保存到文件
    
    Args:
        output_path: 输出文件路径
        
    Returns:
        是否成功
    """
    try:
        screenshot = ImageGrab.grab()
        screenshot.save(output_path, "PNG")
        print(f"[ScreenshotSelector] 全屏截图已保存: {output_path}")
        return True
    except Exception as e:
        print(f"[ScreenshotSelector] 保存截图失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# 测试代码
if __name__ == '__main__':
    import tempfile
    from pathlib import Path
    
    print("截取全屏...")
    temp_dir = Path(tempfile.gettempdir())
    temp_file = temp_dir / "webrpa_test_screenshot.png"
    
    if capture_fullscreen_to_file(str(temp_file)):
        print(f"截图成功！已保存到: {temp_file}")
    else:
        print("截图失败")


