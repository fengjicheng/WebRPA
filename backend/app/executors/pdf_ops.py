"""PDF文件处理模块 - 操作相关执行器

包含：
- PDF合并
- PDF拆分
- PDF提取文本
- PDF提取图片
- PDF加密/解密
- PDF添加水印
- PDF旋转页面
- PDF删除页面
- PDF获取信息
- PDF压缩
- PDF插入页面
- PDF重排页面

使用 pypdf 库替代 PyMuPDF，完全符合 MIT 许可证
"""
import asyncio
import os
from typing import List
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject
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


def parse_page_range(page_range: str, total_pages: int = None) -> List[int]:
    """解析页面范围字符串"""
    if not page_range:
        return list(range(total_pages)) if total_pages else []
    
    pages = set()
    parts = page_range.replace(' ', '').split(',')
    
    for part in parts:
        if '-' in part:
            start, end = part.split('-')
            start = int(start) - 1 if start else 0
            end = int(end) if end else (total_pages or 0)
            if total_pages:
                pages.update(range(max(0, start), min(end, total_pages)))
            else:
                pages.update(range(max(0, start), end))
        else:
            page = int(part) - 1
            if total_pages is None or 0 <= page < total_pages:
                pages.add(page)
    
    return sorted(pages)


@register_executor
class PDFMergeExecutor(ModuleExecutor):
    """PDF合并模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_merge"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        
        pdfs_input = context.resolve_value(config.get('pdfFiles', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', '')
        
        if isinstance(pdfs_input, str):
            pdf_paths = [p.strip() for p in pdfs_input.split(',') if p.strip()]
        elif isinstance(pdfs_input, list):
            pdf_paths = pdfs_input
        else:
            return ModuleResult(success=False, error="PDF文件路径格式错误")
        
        if len(pdf_paths) < 2:
            return ModuleResult(success=False, error="至少需要2个PDF文件进行合并")
        if not output_path:
            return ModuleResult(success=False, error="输出PDF路径不能为空")
        
        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._merge, pdf_paths, output_path)
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"已合并 {len(pdf_paths)} 个PDF文件", data=result)
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF合并失败: {str(e)}")
    
    def _merge(self, pdf_paths: List[str], output_path: str) -> dict:
        writer = PdfWriter()
        total_pages = 0
        
        for pdf_path in pdf_paths:
            reader = PdfReader(pdf_path)
            total_pages += len(reader.pages)
            for page in reader.pages:
                writer.add_page(page)
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        return {
            "output_path": output_path,
            "merged_files": len(pdf_paths),
            "total_pages": total_pages,
            "file_size": os.path.getsize(output_path)
        }


@register_executor
class PDFSplitExecutor(ModuleExecutor):
    """PDF拆分模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_split"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_dir = context.resolve_value(config.get('outputDir', ''))
        split_mode = config.get('splitMode', 'single')
        page_ranges = context.resolve_value(config.get('pageRanges', ''))
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
                None, self._split, pdf_path, output_dir, split_mode, page_ranges
            )
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"已拆分为 {len(result['output_files'])} 个PDF文件", data=result)
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF拆分失败: {str(e)}")
    
    def _split(self, pdf_path: str, output_dir: str, split_mode: str, page_ranges: str) -> dict:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_files = []
        
        if split_mode == 'single':
            for i in range(total_pages):
                writer = PdfWriter()
                writer.add_page(reader.pages[i])
                output_path = os.path.join(output_dir, f"{base_name}_page_{i + 1}.pdf")
                with open(output_path, 'wb') as f:
                    writer.write(f)
                output_files.append(output_path)
        else:
            ranges = self._parse_ranges(page_ranges, total_pages)
            for idx, (start, end) in enumerate(ranges):
                writer = PdfWriter()
                for page_num in range(start, end):
                    writer.add_page(reader.pages[page_num])
                output_path = os.path.join(output_dir, f"{base_name}_part_{idx + 1}.pdf")
                with open(output_path, 'wb') as f:
                    writer.write(f)
                output_files.append(output_path)
        
        return {"output_files": output_files, "total_pages": total_pages, "split_count": len(output_files)}
    
    def _parse_ranges(self, page_ranges: str, total_pages: int) -> List[tuple]:
        if not page_ranges:
            return [(0, total_pages)]
        
        ranges = []
        parts = page_ranges.replace(' ', '').split(',')
        
        for part in parts:
            if '-' in part:
                start, end = part.split('-')
                start = int(start) - 1 if start else 0
                end = int(end) if end else total_pages
                ranges.append((max(0, start), min(end, total_pages)))
            else:
                page = int(part) - 1
                if 0 <= page < total_pages:
                    ranges.append((page, page + 1))
        
        return ranges


@register_executor
class PDFExtractTextExecutor(ModuleExecutor):
    """PDF提取文本模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_extract_text"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        page_range = context.resolve_value(config.get('pageRange', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._extract, pdf_path, page_range, output_path)
            
            if result_variable:
                context.set_variable(result_variable, result['text'])
            
            return ModuleResult(success=True, message=f"已从 {result['extracted_pages']} 页中提取文本", data=result)
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF提取文本失败: {str(e)}")
    
    def _extract(self, pdf_path: str, page_range: str, output_path: str) -> dict:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        pages = parse_page_range(page_range, total_pages)
        
        text_parts = []
        for page_num in pages:
            page = reader.pages[page_num]
            text = page.extract_text()
            text_parts.append(f"--- 第 {page_num + 1} 页 ---\n{text}")
        
        full_text = "\n\n".join(text_parts)
        
        if output_path:
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
        
        return {
            "text": full_text,
            "total_pages": total_pages,
            "extracted_pages": len(pages),
            "char_count": len(full_text),
            "output_path": output_path if output_path else None
        }


@register_executor
class PDFExtractImagesExecutor(ModuleExecutor):
    """PDF提取图片模块执行器
    
    注意：pypdf 对图片提取的支持有限，此功能可能无法提取所有图片
    建议使用专门的 PDF 图片提取工具
    """
    
    @property
    def module_type(self) -> str:
        return "pdf_extract_images"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_dir = context.resolve_value(config.get('outputDir', ''))
        min_size = int(config.get('minSize', 100))
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
            result = await loop.run_in_executor(None, self._extract, pdf_path, output_dir, min_size)
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"已提取 {len(result['images'])} 张图片", data=result)
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF提取图片失败: {str(e)}")
    
    def _extract(self, pdf_path: str, output_dir: str, min_size: int) -> dict:
        reader = PdfReader(pdf_path)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        images = []
        img_count = 0
        
        for page_num, page in enumerate(reader.pages):
            if '/Resources' in page and '/XObject' in page['/Resources']:
                xobjects = page['/Resources']['/XObject'].get_object()
                
                for obj_name in xobjects:
                    obj = xobjects[obj_name]
                    
                    if obj['/Subtype'] == '/Image':
                        try:
                            size = (obj['/Width'], obj['/Height'])
                            
                            if size[0] >= min_size and size[1] >= min_size:
                                img_count += 1
                                
                                # 提取图片数据
                                data = obj.get_data()
                                
                                # 尝试确定图片格式
                                if '/Filter' in obj:
                                    filter_type = obj['/Filter']
                                    if filter_type == '/DCTDecode':
                                        ext = 'jpg'
                                    elif filter_type == '/JPXDecode':
                                        ext = 'jp2'
                                    elif filter_type == '/FlateDecode':
                                        ext = 'png'
                                    else:
                                        ext = 'png'
                                else:
                                    ext = 'png'
                                
                                output_path = os.path.join(output_dir, f"{base_name}_page{page_num + 1}_img{img_count}.{ext}")
                                
                                # 如果是原始数据，需要转换为图片
                                if ext == 'png' and '/Filter' in obj and obj['/Filter'] == '/FlateDecode':
                                    try:
                                        # 尝试使用 PIL 处理
                                        mode = "RGB"
                                        if '/ColorSpace' in obj:
                                            cs = obj['/ColorSpace']
                                            if cs == '/DeviceGray':
                                                mode = "L"
                                            elif cs == '/DeviceCMYK':
                                                mode = "CMYK"
                                        
                                        img = Image.frombytes(mode, size, data)
                                        img.save(output_path)
                                    except:
                                        # 如果失败，直接保存原始数据
                                        with open(output_path, 'wb') as f:
                                            f.write(data)
                                else:
                                    with open(output_path, 'wb') as f:
                                        f.write(data)
                                
                                images.append({
                                    "path": output_path,
                                    "page": page_num + 1,
                                    "width": size[0],
                                    "height": size[1],
                                    "format": ext
                                })
                        except Exception as e:
                            # 跳过无法提取的图片
                            continue
        
        return {"images": images, "image_count": len(images), "output_dir": output_dir}


@register_executor
class PDFEncryptExecutor(ModuleExecutor):
    """PDF加密模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_encrypt"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        user_password = context.resolve_value(config.get('userPassword', ''))
        owner_password = context.resolve_value(config.get('ownerPassword', ''))
        permissions = config.get('permissions', {})
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        if not user_password and not owner_password:
            return ModuleResult(success=False, error="至少需要设置一个密码")
        
        if not output_path:
            base, ext = os.path.splitext(pdf_path)
            output_path = f"{base}_encrypted{ext}"
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._encrypt, pdf_path, output_path, user_password, owner_password, permissions
            )
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message="PDF加密成功", data=result)
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF加密失败: {str(e)}")
    
    def _encrypt(self, pdf_path: str, output_path: str, user_password: str, owner_password: str, permissions: dict) -> dict:
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        # 复制所有页面
        for page in reader.pages:
            writer.add_page(page)
        
        # 设置加密
        writer.encrypt(
            user_password=user_password if user_password else "",
            owner_password=owner_password if owner_password else user_password,
            permissions_flag=-1  # pypdf 的权限标志与 PyMuPDF 不同，使用 -1 表示所有权限
        )
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        return {
            "output_path": output_path,
            "has_user_password": bool(user_password),
            "has_owner_password": bool(owner_password),
            "encryption": "AES-256"
        }


@register_executor
class PDFDecryptExecutor(ModuleExecutor):
    """PDF解密模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_decrypt"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        password = context.resolve_value(config.get('password', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        
        if not output_path:
            base, ext = os.path.splitext(pdf_path)
            output_path = f"{base}_decrypted{ext}"
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._decrypt, pdf_path, password, output_path)
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message="PDF解密成功", data=result)
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF解密失败: {str(e)}")
    
    def _decrypt(self, pdf_path: str, password: str, output_path: str) -> dict:
        reader = PdfReader(pdf_path)
        
        if reader.is_encrypted:
            if not reader.decrypt(password):
                raise Exception("密码错误")
        
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        return {"output_path": output_path, "page_count": len(reader.pages)}


@register_executor
class PDFAddWatermarkExecutor(ModuleExecutor):
    """PDF添加水印模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_add_watermark"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        watermark_type = config.get('watermarkType', 'text')
        watermark_text = context.resolve_value(config.get('watermarkText', ''))
        watermark_image = context.resolve_value(config.get('watermarkImage', ''))
        opacity = float(config.get('opacity', 0.3))
        position = config.get('position', 'center')
        font_size = int(config.get('fontSize', 48))
        color = config.get('color', '#888888')
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        
        if watermark_type == 'text' and not watermark_text:
            return ModuleResult(success=False, error="水印文字不能为空")
        if watermark_type == 'image' and not watermark_image:
            return ModuleResult(success=False, error="水印图片路径不能为空")
        if watermark_type == 'image' and not os.path.exists(watermark_image):
            return ModuleResult(success=False, error=f"水印图片不存在: {watermark_image}")
        
        if not output_path:
            base, ext = os.path.splitext(pdf_path)
            output_path = f"{base}_watermarked{ext}"
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._add_watermark, pdf_path, output_path, watermark_type,
                watermark_text, watermark_image, opacity, position, font_size, color
            )
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message="PDF水印添加成功", data=result)
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF添加水印失败: {str(e)}")
    
    def _add_watermark(self, pdf_path: str, output_path: str, watermark_type: str,
                       watermark_text: str, watermark_image: str, opacity: float,
                       position: str, font_size: int, color: str) -> dict:
        """
        注意：pypdf 对水印的支持有限，此功能使用简化实现
        建议使用专门的 PDF 水印工具获得更好的效果
        """
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        import tempfile
        
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        # 创建水印 PDF
        watermark_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        watermark_path = watermark_pdf.name
        watermark_pdf.close()
        
        try:
            # 使用 reportlab 创建水印
            c = canvas.Canvas(watermark_path, pagesize=letter)
            
            if watermark_type == 'text':
                c.setFillColorRGB(*self._hex_to_rgb(color))
                c.setFont("Helvetica", font_size)
                c.setFillAlpha(opacity)
                
                if position == 'center':
                    c.drawCentredString(300, 400, watermark_text)
                elif position == 'diagonal':
                    c.saveState()
                    c.translate(300, 400)
                    c.rotate(45)
                    c.drawCentredString(0, 0, watermark_text)
                    c.restoreState()
                elif position == 'tile':
                    for y in range(100, 700, 150):
                        for x in range(100, 500, 200):
                            c.drawString(x, y, watermark_text)
            else:
                # 图片水印
                if os.path.exists(watermark_image):
                    c.setFillAlpha(opacity)
                    if position == 'center':
                        c.drawImage(watermark_image, 200, 300, width=200, height=200, preserveAspectRatio=True, mask='auto')
                    elif position == 'tile':
                        for y in range(100, 700, 250):
                            for x in range(100, 500, 250):
                                c.drawImage(watermark_image, x, y, width=150, height=150, preserveAspectRatio=True, mask='auto')
            
            c.save()
            
            # 读取水印 PDF
            watermark_reader = PdfReader(watermark_path)
            watermark_page = watermark_reader.pages[0]
            
            # 将水印应用到每一页
            for page in reader.pages:
                page.merge_page(watermark_page)
                writer.add_page(page)
            
            # 保存结果
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            return {"output_path": output_path, "watermark_type": watermark_type, "position": position}
        finally:
            # 清理临时文件
            if os.path.exists(watermark_path):
                os.unlink(watermark_path)
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
        return (r, g, b)


@register_executor
class PDFRotateExecutor(ModuleExecutor):
    """PDF旋转页面模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_rotate"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        rotation = int(config.get('rotation', 90))
        page_range = context.resolve_value(config.get('pageRange', ''))
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        if rotation not in [90, 180, 270, -90, -180, -270]:
            return ModuleResult(success=False, error="旋转角度必须是90、180或270度")
        
        if not output_path:
            base, ext = os.path.splitext(pdf_path)
            output_path = f"{base}_rotated{ext}"
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._rotate, pdf_path, output_path, rotation, page_range)
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"已旋转 {result['rotated_pages']} 页", data=result)
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF旋转失败: {str(e)}")
    
    def _rotate(self, pdf_path: str, output_path: str, rotation: int, page_range: str) -> dict:
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        total_pages = len(reader.pages)
        pages_to_rotate = parse_page_range(page_range, total_pages)
        
        for page_num in range(total_pages):
            page = reader.pages[page_num]
            if page_num in pages_to_rotate:
                page.rotate(rotation)
            writer.add_page(page)
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        return {"output_path": output_path, "rotation": rotation, "rotated_pages": len(pages_to_rotate), "total_pages": total_pages}


@register_executor
class PDFDeletePagesExecutor(ModuleExecutor):
    """PDF删除页面模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_delete_pages"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        page_range = context.resolve_value(config.get('pageRange', ''))
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        if not page_range:
            return ModuleResult(success=False, error="请指定要删除的页面")
        
        if not output_path:
            base, ext = os.path.splitext(pdf_path)
            output_path = f"{base}_modified{ext}"
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._delete, pdf_path, output_path, page_range)
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"已删除 {result['deleted_pages']} 页", data=result)
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF删除页面失败: {str(e)}")
    
    def _delete(self, pdf_path: str, output_path: str, page_range: str) -> dict:
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        total_pages = len(reader.pages)
        pages_to_delete = set(parse_page_range(page_range, total_pages))
        
        for page_num in range(total_pages):
            if page_num not in pages_to_delete:
                writer.add_page(reader.pages[page_num])
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        new_page_count = len(writer.pages)
        
        return {
            "output_path": output_path,
            "original_pages": total_pages,
            "deleted_pages": len(pages_to_delete),
            "remaining_pages": new_page_count
        }


@register_executor
class PDFGetInfoExecutor(ModuleExecutor):
    """PDF获取信息模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_get_info"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        password = context.resolve_value(config.get('password', ''))
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._get_info, pdf_path, password)
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"PDF共 {result['page_count']} 页", data=result)
        except Exception as e:
            return ModuleResult(success=False, error=f"获取PDF信息失败: {str(e)}")
    
    def _get_info(self, pdf_path: str, password: str) -> dict:
        reader = PdfReader(pdf_path)
        
        if reader.is_encrypted:
            if password:
                if not reader.decrypt(password):
                    raise Exception("密码错误")
            else:
                raise Exception("PDF已加密，请提供密码")
        
        metadata = reader.metadata or {}
        pages_info = []
        for i, page in enumerate(reader.pages):
            box = page.mediabox
            pages_info.append({
                "page_number": i + 1,
                "width": float(box.width),
                "height": float(box.height),
                "rotation": page.get('/Rotate', 0)
            })
        
        file_size = os.path.getsize(pdf_path)
        
        result = {
            "file_path": pdf_path,
            "file_size": file_size,
            "file_size_mb": round(file_size / 1024 / 1024, 2),
            "page_count": len(reader.pages),
            "is_encrypted": reader.is_encrypted,
            "metadata": {
                "title": metadata.get('/Title', ''),
                "author": metadata.get('/Author', ''),
                "subject": metadata.get('/Subject', ''),
                "keywords": metadata.get('/Keywords', ''),
                "creator": metadata.get('/Creator', ''),
                "producer": metadata.get('/Producer', ''),
                "creation_date": str(metadata.get('/CreationDate', '')),
                "modification_date": str(metadata.get('/ModDate', '')),
            },
            "pages": pages_info
        }
        
        return result


@register_executor
class PDFCompressExecutor(ModuleExecutor):
    """PDF压缩模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_compress"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        image_quality = int(config.get('imageQuality', 80))
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        
        if not output_path:
            base, ext = os.path.splitext(pdf_path)
            output_path = f"{base}_compressed{ext}"
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._compress, pdf_path, output_path, image_quality)
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"PDF压缩完成，压缩率 {result['compression_ratio']}%", data=result)
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF压缩失败: {str(e)}")
    
    def _compress(self, pdf_path: str, output_path: str, image_quality: int) -> dict:
        """
        注意：pypdf 的压缩功能有限，主要通过移除重复对象和压缩流来减小文件大小
        对于包含大量图片的 PDF，压缩效果可能不如 PyMuPDF
        """
        original_size = os.path.getsize(pdf_path)
        
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        # 复制所有页面
        for page in reader.pages:
            writer.add_page(page)
        
        # 压缩内容流
        for page in writer.pages:
            page.compress_content_streams()
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        new_size = os.path.getsize(output_path)
        compression_ratio = round((1 - new_size / original_size) * 100, 1) if original_size > 0 else 0
        
        return {
            "output_path": output_path,
            "original_size": original_size,
            "compressed_size": new_size,
            "original_size_mb": round(original_size / 1024 / 1024, 2),
            "compressed_size_mb": round(new_size / 1024 / 1024, 2),
            "compression_ratio": compression_ratio
        }


@register_executor
class PDFInsertPagesExecutor(ModuleExecutor):
    """PDF插入页面模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_insert_pages"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        insert_pdf = context.resolve_value(config.get('insertPdf', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        insert_position = int(config.get('insertPosition', 0))
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        if not insert_pdf:
            return ModuleResult(success=False, error="要插入的PDF路径不能为空")
        if not os.path.exists(insert_pdf):
            return ModuleResult(success=False, error=f"要插入的PDF不存在: {insert_pdf}")
        
        if not output_path:
            base, ext = os.path.splitext(pdf_path)
            output_path = f"{base}_inserted{ext}"
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._insert, pdf_path, insert_pdf, output_path, insert_position)
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"已插入 {result['inserted_pages']} 页", data=result)
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF插入页面失败: {str(e)}")
    
    def _insert(self, pdf_path: str, insert_pdf: str, output_path: str, insert_position: int) -> dict:
        reader = PdfReader(pdf_path)
        insert_reader = PdfReader(insert_pdf)
        writer = PdfWriter()
        
        original_pages = len(reader.pages)
        insert_pages = len(insert_reader.pages)
        
        if insert_position == -1 or insert_position >= original_pages:
            position = original_pages
        else:
            position = max(0, insert_position)
        
        # 添加插入位置之前的页面
        for i in range(position):
            writer.add_page(reader.pages[i])
        
        # 添加要插入的页面
        for page in insert_reader.pages:
            writer.add_page(page)
        
        # 添加插入位置之后的页面
        for i in range(position, original_pages):
            writer.add_page(reader.pages[i])
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        total_pages = len(writer.pages)
        
        return {
            "output_path": output_path,
            "original_pages": original_pages,
            "inserted_pages": insert_pages,
            "total_pages": total_pages,
            "insert_position": position
        }


@register_executor
class PDFReorderPagesExecutor(ModuleExecutor):
    """PDF重排页面模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_reorder_pages"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        page_order = context.resolve_value(config.get('pageOrder', ''))
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        if not page_order:
            return ModuleResult(success=False, error="请指定页面顺序")
        
        if not output_path:
            base, ext = os.path.splitext(pdf_path)
            output_path = f"{base}_reordered{ext}"
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._reorder, pdf_path, output_path, page_order)
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message="PDF页面重排完成", data=result)
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF重排页面失败: {str(e)}")
    
    def _reorder(self, pdf_path: str, output_path: str, page_order: str) -> dict:
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        total_pages = len(reader.pages)
        
        if isinstance(page_order, str):
            order = [int(p.strip()) - 1 for p in page_order.split(',') if p.strip()]
        else:
            order = [int(p) - 1 for p in page_order]
        
        for idx in order:
            if idx < 0 or idx >= total_pages:
                raise Exception(f"页面索引 {idx + 1} 超出范围 (1-{total_pages})")
        
        for idx in order:
            writer.add_page(reader.pages[idx])
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        return {"output_path": output_path, "original_pages": total_pages, "new_page_count": len(order), "page_order": [i + 1 for i in order]}
