"""
WebRPA 独立截图工具
这是一个独立运行的截图程序，不依赖Web前端
使用方法：python screenshot_tool.py [output_path]
"""
import sys
import os
from pathlib import Path

# 添加app目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image, ImageGrab
import argparse
import json


def capture_and_save(output_path: str, return_info: bool = False) -> dict:
    """
    截取全屏并保存
    
    Args:
        output_path: 输出文件路径
        return_info: 是否返回截图信息（用于API调用）
        
    Returns:
        包含截图信息的字典
    """
    try:
        # 截取全屏
        screenshot = ImageGrab.grab()
        
        # 保存截图
        screenshot.save(output_path, "PNG")
        
        result = {
            "success": True,
            "path": output_path,
            "width": screenshot.width,
            "height": screenshot.height,
            "message": f"截图已保存: {output_path}"
        }
        
        if return_info:
            return result
        else:
            print(f"[ScreenshotTool] 截图成功！")
            print(f"[ScreenshotTool] 路径: {output_path}")
            print(f"[ScreenshotTool] 尺寸: {screenshot.width} x {screenshot.height}")
            return result
            
    except Exception as e:
        import traceback
        error_msg = f"截图失败: {str(e)}"
        traceback.print_exc()
        
        return {
            "success": False,
            "error": error_msg
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='WebRPA 独立截图工具')
    parser.add_argument('output', nargs='?', help='输出文件路径（可选）')
    parser.add_argument('--json', action='store_true', help='以JSON格式输出结果')
    parser.add_argument('--temp', action='store_true', help='保存到临时文件')
    
    args = parser.parse_args()
    
    # 确定输出路径
    if args.temp:
        import tempfile
        import uuid
        temp_dir = Path(tempfile.gettempdir())
        output_path = str(temp_dir / f"webrpa_screenshot_{uuid.uuid4()}.png")
    elif args.output:
        output_path = args.output
    else:
        # 默认保存到当前目录
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"screenshot_{timestamp}.png"
    
    # 执行截图
    result = capture_and_save(output_path, return_info=args.json)
    
    # 输出结果
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    
    return 0 if result["success"] else 1


if __name__ == '__main__':
    sys.exit(main())
