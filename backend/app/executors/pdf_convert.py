"""PDF文件处理模块 - 转换相关执行器

包含：
- PDF转图片
- 图片转PDF
- PDF转Word (使用pdfplumber提取内容，包括图片和表格)

使用 pypdf + pdfplumber 库，完全符合 MIT 许可证
"""
import asyncio
import os
from typing import List
from pypdf import PdfReader, PdfWriter
from PIL import Image
import io

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor


def ensure_pdf_libs():
    """确保PDF处理库已安装"""
    try:
        import pypdf
        return True
    except ImportError:
        raise ImportError("请安装 pypdf: pip install pypdf")


def parse_page_range(page_range: str, total_pages: int) -> List[int]:
    """解析页面范围字符串"""
    if not page_range:
        return list(range(total_pages))
    
    pages = set()
    parts = page_range.replace(' ', '').split(',')
    
    for part in parts:
        if '-' in part:
            start, end = part.split('-')
            start = int(start) - 1 if start else 0
            end = int(end) if end else total_pages
            pages.update(range(max(0, start), min(end, total_pages)))
        else:
            page = int(part) - 1
            if 0 <= page < total_pages:
                pages.add(page)
    
    return sorted(pages)


@register_executor
class PDFToImagesExecutor(ModuleExecutor):
    """PDF转图片模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_to_images"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_dir = context.resolve_value(config.get('outputDir', ''))
        dpi = int(config.get('dpi', 150))
        image_format = config.get('imageFormat', 'png')
        page_range = context.resolve_value(config.get('pageRange', ''))
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        
        if not output_dir:
            output_dir = os.path.dirname(pdf_path)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._convert, pdf_path, output_dir, dpi, image_format, page_range
            )
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"已将PDF转换为 {len(result['images'])} 张图片", data=result)
        except ImportError as e:
            error_msg = "PDF转图片功能需要安装 pdf2image 库和 poppler 工具\n\n"
            error_msg += "poppler 工具下载：\n"
            error_msg += "访问 https://github.com/oschwartz10612/poppler-windows/releases\n"
            error_msg += "下载最新的 Release-xx.xx.x.zip，解压后将文件夹重命名为 'poppler'\n"
            error_msg += "放置到 backend 目录下即可\n\n"
            error_msg += f"详细错误: {str(e)}"
            return ModuleResult(success=False, error=error_msg)
        except Exception as e:
            error_msg = str(e)
            if "poppler" in error_msg.lower():
                error_msg = "PDF转图片功能需要 poppler 工具\n\n"
                error_msg += "下载地址: https://github.com/oschwartz10612/poppler-windows/releases\n"
                error_msg += "下载最新的 Release-xx.xx.x.zip，解压后将文件夹重命名为 'poppler'\n"
                error_msg += "放置到 backend 目录下即可\n\n"
                error_msg += f"原始错误: {str(e)}"
            return ModuleResult(success=False, error=f"PDF转图片失败: {error_msg}")
    
    def _convert(self, pdf_path: str, output_dir: str, dpi: int, image_format: str, page_range: str) -> dict:
        from pdf2image import convert_from_path
        
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        pages_to_convert = parse_page_range(page_range, total_pages)
        
        # 获取 backend 目录的路径
        backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        poppler_path = os.path.join(backend_root, 'poppler', 'Library', 'bin')
        
        # 如果指定了页面范围，只转换这些页面
        if page_range:
            first_page = min(pages_to_convert) + 1 if pages_to_convert else 1
            last_page = max(pages_to_convert) + 1 if pages_to_convert else total_pages
            
            if os.path.exists(poppler_path):
                images = convert_from_path(pdf_path, dpi=dpi, first_page=first_page, last_page=last_page, poppler_path=poppler_path)
            else:
                images = convert_from_path(pdf_path, dpi=dpi, first_page=first_page, last_page=last_page)
        else:
            if os.path.exists(poppler_path):
                images = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
            else:
                images = convert_from_path(pdf_path, dpi=dpi)
        
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        saved_images = []
        
        for i, img in enumerate(images):
            page_num = pages_to_convert[i] if page_range else i
            output_path = os.path.join(output_dir, f"{base_name}_page_{page_num + 1}.{image_format}")
            img.save(output_path, image_format.upper())
            saved_images.append(output_path)
        
        return {
            "images": saved_images,
            "total_pages": total_pages,
            "converted_pages": len(saved_images),
            "output_dir": output_dir
        }


@register_executor
class ImagesToPDFExecutor(ModuleExecutor):
    """图片转PDF模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "images_to_pdf"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        
        images_input = context.resolve_value(config.get('images', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        page_size = config.get('pageSize', 'A4')
        result_variable = config.get('resultVariable', '')
        
        if isinstance(images_input, str):
            image_paths = [p.strip() for p in images_input.split(',') if p.strip()]
        elif isinstance(images_input, list):
            image_paths = images_input
        else:
            return ModuleResult(success=False, error="图片路径格式错误")
        
        if not image_paths:
            return ModuleResult(success=False, error="图片列表不能为空")
        if not output_path:
            return ModuleResult(success=False, error="输出PDF路径不能为空")
        
        # 检查 output_path 是否是目录，如果是则自动生成文件名
        if os.path.isdir(output_path):
            base_name = os.path.splitext(os.path.basename(image_paths[0]))[0]
            output_path = os.path.join(output_path, f"{base_name}_merged.pdf")
        
        for img_path in image_paths:
            if not os.path.exists(img_path):
                return ModuleResult(success=False, error=f"图片不存在: {img_path}")
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._convert, image_paths, output_path, page_size)
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"已将 {len(image_paths)} 张图片转换为PDF", data=result)
        except Exception as e:
            return ModuleResult(success=False, error=f"图片转PDF失败: {str(e)}")
    
    def _convert(self, image_paths: List[str], output_path: str, page_size: str) -> dict:
        """使用 PIL 将图片转换为 PDF"""
        images = []
        for img_path in image_paths:
            img = Image.open(img_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        if images:
            images[0].save(
                output_path,
                "PDF",
                resolution=100.0,
                save_all=True,
                append_images=images[1:] if len(images) > 1 else []
            )
        
        for img in images:
            img.close()
        
        return {
            "output_path": output_path,
            "page_count": len(image_paths),
            "file_size": os.path.getsize(output_path)
        }


@register_executor
class PDFToWordExecutor(ModuleExecutor):
    """PDF转Word模块执行器
    
    使用 pdf2docx (GPL v3 许可证) 实现高保真的PDF到Word转换
    
    注意：此功能使用 GPL v3 许可证的库，仅供非商业使用
    商业使用需要遵守 GPL v3 许可证或联系原作者获取商业授权
    """

    @property
    def module_type(self) -> str:
        return "pdf_to_word"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_dir = context.resolve_value(config.get('outputDir', ''))
        page_range = context.resolve_value(config.get('pageRange', ''))
        result_variable = config.get('resultVariable', '')

        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")

        if not output_dir:
            output_dir = os.path.dirname(pdf_path)
        os.makedirs(output_dir, exist_ok=True)

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._convert, pdf_path, output_dir, page_range
            )

            if result_variable:
                context.set_variable(result_variable, result)

            return ModuleResult(success=True, message=f"已将PDF转换为Word文档", data=result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return ModuleResult(success=False, error=f"PDF转Word失败: {str(e)}")

    def _convert(self, pdf_path: str, output_dir: str, page_range: str) -> dict:
        """将PDF转换为Word文档 - 使用pdf2docx实现高保真转换"""
        try:
            from pdf2docx import Converter
        except ImportError as e:
            raise ImportError(f"请安装 pdf2docx: pip install pdf2docx - {str(e)}")

        # 生成输出文件名
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.docx")

        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(output_dir, f"{base_name}_{counter}.docx")
            counter += 1

        # 创建转换器
        cv = Converter(pdf_path)
        
        try:
            # 解析页面范围
            if page_range:
                from .pdf_ops import parse_page_range
                from pypdf import PdfReader
                reader = PdfReader(pdf_path)
                total_pages = len(reader.pages)
                pages_to_convert = parse_page_range(page_range, total_pages)
                
                # pdf2docx 使用的页面范围格式是列表
                cv.convert(output_path, pages=pages_to_convert)
                converted_pages = len(pages_to_convert)
            else:
                # 转换所有页面
                cv.convert(output_path)
                from pypdf import PdfReader
                reader = PdfReader(pdf_path)
                total_pages = len(reader.pages)
                converted_pages = total_pages
        finally:
            cv.close()

        return {
            "output_path": output_path,
            "total_pages": total_pages if page_range else converted_pages,
            "converted_pages": converted_pages,
            "file_size": os.path.getsize(output_path)
        }
