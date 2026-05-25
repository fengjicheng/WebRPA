"""盲水印（blind_watermark）模块执行器

集成 https://github.com/guofei9987/blind_watermark
提供 4 个模块：
- bwm_embed_text     嵌入文本水印
- bwm_extract_text   提取文本水印
- bwm_embed_image    嵌入图片水印
- bwm_extract_image  提取图片水印

特性：
- 嵌入后的图像几乎无肉眼差异，但能抵抗常见编辑（缩放/裁剪/截屏/JPEG 重压缩等）
- 双密码：password_img（图像置乱密码）+ password_wm（水印置乱密码）。提取时必须一致
- 文字水印需要把"水印 bit 长度"传给提取端，本模块嵌入时会把它写进结果（resultVariable）

注意：内部用 cv2.imdecode/imencode 替代 cv2.imread/imwrite，
彻底支持 Windows 下含中文/特殊字符的文件路径（OpenCV 自身不支持非 ASCII 路径）。
"""
from __future__ import annotations

from pathlib import Path
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int


def _resolve_path(p: str, must_exist: bool = False) -> Path | None:
    if not p:
        return None
    fp = Path(p).expanduser()
    if must_exist and not fp.exists():
        return None
    return fp


def _ensure_parent(fp: Path) -> None:
    try:
        fp.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def _resolve_output_path(out_path: str, src_fp: Path, default_suffix: str = "_wm") -> Path | None:
    """处理输出路径：支持目录（自动拼文件名）、相对路径、纯文件名"""
    if not out_path:
        return None
    fp = Path(out_path).expanduser()
    # 如果用户给的是已存在的目录，或者结尾是 / \\，自动按 "源文件名_wm.png" 拼
    if (fp.exists() and fp.is_dir()) or out_path.endswith(("/", "\\")):
        return (fp / f"{src_fp.stem}{default_suffix}.png").resolve()
    # 没扩展名 → 默认 .png
    if not fp.suffix:
        return fp.with_suffix(".png").resolve()
    return fp.resolve()


def _imread_unicode(path: str, flags: int = -1):
    """支持中文路径的 imread（用 numpy + cv2.imdecode 实现）"""
    import numpy as np
    import cv2
    try:
        with open(path, "rb") as f:
            data = f.read()
        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, flags)
        return img
    except Exception:
        return None


def _imwrite_unicode(path: str, img, ext: str | None = None) -> bool:
    """支持中文路径的 imwrite（用 cv2.imencode + 二进制写文件）"""
    import cv2
    p = Path(path)
    if ext is None:
        ext = (p.suffix or ".png").lower()
    if not ext.startswith("."):
        ext = "." + ext
    try:
        ok, buf = cv2.imencode(ext, img)
        if not ok:
            return False
        with open(path, "wb") as f:
            f.write(buf.tobytes())
        return True
    except Exception:
        return False


def _import_bwm():
    """延迟导入 blind_watermark，并屏蔽它"first run"打印（每次新进程都会输出一次提示）"""
    from blind_watermark import WaterMark
    try:
        from blind_watermark import bw_notes  # noqa
        bw_notes.close()
    except Exception:
        pass
    return WaterMark


def _bwm_read_img_unicode(bwm, path: str) -> tuple[bool, str]:
    """绕开 cv2.imread 的中文路径限制：自己读字节解码后塞给 bwm"""
    import cv2
    img = _imread_unicode(path, flags=cv2.IMREAD_UNCHANGED)
    if img is None:
        return False, f"无法读取图像（可能格式不支持或路径含特殊字符）：{path}"
    try:
        bwm.read_img(img=img)
        return True, ""
    except Exception as e:
        return False, f"图像读取失败：{e}"


def _bwm_read_wm_image_unicode(bwm, path: str) -> tuple[bool, str, tuple[int, int] | None]:
    """读水印图（绕过 cv2.imread 中文路径限制）。返回 (ok, err, (h, w))"""
    import cv2
    img = _imread_unicode(path, flags=cv2.IMREAD_GRAYSCALE)
    if img is None:
        return False, f"无法读取水印图：{path}", None
    try:
        h, w = int(img.shape[0]), int(img.shape[1])
        # blind_watermark 0.4.4 的 read_wm(mode='bit') 接受 1D bool 数组 → 走完整内部流程
        # （shuffle + bwm_core.read_wm），与 mode='img' 路径完全等价，但跳过 cv2.imread
        wm_bits = (img.flatten() > 128)
        bwm.read_wm(wm_bits, mode='bit')
        return True, "", (h, w)
    except Exception as e:
        return False, f"水印图处理失败：{e}", None


@register_executor
class BwmEmbedTextExecutor(ModuleExecutor):
    """盲水印 - 嵌入文本水印"""

    @property
    def module_type(self) -> str:
        return "bwm_embed_text"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        src_path = context.resolve_value(config.get("imagePath", ""))
        out_path = context.resolve_value(config.get("outputPath", ""))
        text = context.resolve_value(config.get("text", ""))
        password_wm = to_int(config.get("passwordWm", 1), 1, context)
        password_img = to_int(config.get("passwordImg", 1), 1, context)
        result_var = context.resolve_value(config.get("resultVariable", "wm_bit_len"))

        if not src_path:
            return ModuleResult(success=False, error="原图路径不能为空")
        src_fp = _resolve_path(src_path, must_exist=True)
        if not src_fp:
            return ModuleResult(success=False, error=f"原图不存在: {src_path}")

        out_fp = _resolve_output_path(out_path, src_fp)
        if out_fp is None:
            return ModuleResult(success=False, error="输出路径不能为空")
        _ensure_parent(out_fp)

        if not isinstance(text, str) or text == "":
            return ModuleResult(success=False, error="水印文本不能为空")

        try:
            WaterMark = _import_bwm()
            bwm = WaterMark(password_wm=password_wm, password_img=password_img)

            ok, err = _bwm_read_img_unicode(bwm, str(src_fp))
            if not ok:
                return ModuleResult(success=False, error=err)

            bwm.read_wm(text, mode='str')
            wm_bit_len = int(len(bwm.wm_bit))

            # embed 不传 filename，让它返回 ndarray，自己写文件（支持中文路径）
            embed_img = bwm.embed(filename=None)
            if not _imwrite_unicode(str(out_fp), embed_img):
                return ModuleResult(success=False, error=f"写入输出图像失败：{out_fp}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            return ModuleResult(success=False, error=f"嵌入文本水印失败: {e}")

        if result_var:
            context.set_variable(str(result_var), wm_bit_len)

        return ModuleResult(
            success=True,
            message=f"已嵌入文本水印，输出: {out_fp}（wm_bit_len={wm_bit_len}）",
            data={"output_path": str(out_fp), "wm_bit_len": wm_bit_len},
        )


@register_executor
class BwmExtractTextExecutor(ModuleExecutor):
    """盲水印 - 提取文本水印"""

    @property
    def module_type(self) -> str:
        return "bwm_extract_text"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        src_path = context.resolve_value(config.get("imagePath", ""))
        wm_bit_len = to_int(config.get("wmBitLen", 0), 0, context)
        password_wm = to_int(config.get("passwordWm", 1), 1, context)
        password_img = to_int(config.get("passwordImg", 1), 1, context)
        result_var = context.resolve_value(config.get("resultVariable", "extracted_text"))

        if not src_path:
            return ModuleResult(success=False, error="待提取图像路径不能为空")
        src_fp = _resolve_path(src_path, must_exist=True)
        if not src_fp:
            return ModuleResult(success=False, error=f"待提取图像不存在: {src_path}")

        if wm_bit_len <= 0:
            return ModuleResult(success=False, error="wm_bit_len 必须大于 0（来自嵌入时的返回值）")

        try:
            import cv2
            WaterMark = _import_bwm()
            bwm = WaterMark(password_wm=password_wm, password_img=password_img)

            # 自己读图绕开中文路径限制
            embed_img = _imread_unicode(str(src_fp), flags=cv2.IMREAD_COLOR)
            if embed_img is None:
                return ModuleResult(success=False, error=f"无法读取图像：{src_fp}")

            # 调 extract(filename=None, embed_img=embed_img, ...) 让它用我们提供的 ndarray
            extracted = bwm.extract(filename=None, embed_img=embed_img, wm_shape=wm_bit_len, mode='str')
        except Exception as e:
            import traceback
            traceback.print_exc()
            return ModuleResult(success=False, error=f"提取文本水印失败: {e}")

        if result_var:
            context.set_variable(str(result_var), extracted)

        return ModuleResult(
            success=True,
            message=f"已提取文本水印，长度 {len(extracted)} 字符",
            data={"text": extracted, "length": len(extracted)},
        )


@register_executor
class BwmEmbedImageExecutor(ModuleExecutor):
    """盲水印 - 嵌入图片水印"""

    @property
    def module_type(self) -> str:
        return "bwm_embed_image"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        src_path = context.resolve_value(config.get("imagePath", ""))
        wm_path = context.resolve_value(config.get("watermarkPath", ""))
        out_path = context.resolve_value(config.get("outputPath", ""))
        password_wm = to_int(config.get("passwordWm", 1), 1, context)
        password_img = to_int(config.get("passwordImg", 1), 1, context)
        result_var = context.resolve_value(config.get("resultVariable", "wm_image_shape"))

        src_fp = _resolve_path(src_path, must_exist=True)
        if not src_fp:
            return ModuleResult(success=False, error=f"原图不存在: {src_path}")

        wm_fp = _resolve_path(wm_path, must_exist=True)
        if not wm_fp:
            return ModuleResult(success=False, error=f"水印图不存在: {wm_path}")

        out_fp = _resolve_output_path(out_path, src_fp)
        if out_fp is None:
            return ModuleResult(success=False, error="输出路径不能为空")
        _ensure_parent(out_fp)

        try:
            WaterMark = _import_bwm()
            bwm = WaterMark(password_wm=password_wm, password_img=password_img)

            ok, err = _bwm_read_img_unicode(bwm, str(src_fp))
            if not ok:
                return ModuleResult(success=False, error=err)

            ok, err, shape = _bwm_read_wm_image_unicode(bwm, str(wm_fp))
            if not ok or shape is None:
                return ModuleResult(success=False, error=err or "水印图读取失败")
            wm_h, wm_w = shape

            embed_img = bwm.embed(filename=None)
            if not _imwrite_unicode(str(out_fp), embed_img):
                return ModuleResult(success=False, error=f"写入输出图像失败：{out_fp}")

            wm_shape = [int(wm_h), int(wm_w)]
            wm_bit_len = int(len(bwm.wm_bit))
        except Exception as e:
            import traceback
            traceback.print_exc()
            return ModuleResult(success=False, error=f"嵌入图片水印失败: {e}")

        if result_var:
            context.set_variable(str(result_var), wm_shape)

        return ModuleResult(
            success=True,
            message=f"已嵌入图片水印，输出: {out_fp}（水印尺寸 {wm_shape[1]}x{wm_shape[0]}）",
            data={
                "output_path": str(out_fp),
                "wm_shape": wm_shape,
                "wm_bit_len": wm_bit_len,
            },
        )


@register_executor
class BwmExtractImageExecutor(ModuleExecutor):
    """盲水印 - 提取图片水印"""

    @property
    def module_type(self) -> str:
        return "bwm_extract_image"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        src_path = context.resolve_value(config.get("imagePath", ""))
        out_path = context.resolve_value(config.get("outputPath", ""))
        wm_h = to_int(config.get("wmHeight", 0), 0, context)
        wm_w = to_int(config.get("wmWidth", 0), 0, context)
        password_wm = to_int(config.get("passwordWm", 1), 1, context)
        password_img = to_int(config.get("passwordImg", 1), 1, context)
        result_var = context.resolve_value(config.get("resultVariable", "extracted_wm_path"))

        src_fp = _resolve_path(src_path, must_exist=True)
        if not src_fp:
            return ModuleResult(success=False, error=f"待提取图像不存在: {src_path}")

        if wm_h <= 0 or wm_w <= 0:
            return ModuleResult(success=False, error="水印高/宽必须大于 0（来自嵌入时返回的 wm_shape）")

        # 输出是水印图本身，没有源文件参考；不允许传目录但留扩展名兜底
        out_fp = _resolve_output_path(out_path, src_fp, default_suffix="_extracted")
        if out_fp is None:
            return ModuleResult(success=False, error="提取结果输出路径不能为空")
        _ensure_parent(out_fp)

        try:
            import cv2
            WaterMark = _import_bwm()
            bwm = WaterMark(password_wm=password_wm, password_img=password_img)

            embed_img = _imread_unicode(str(src_fp), flags=cv2.IMREAD_COLOR)
            if embed_img is None:
                return ModuleResult(success=False, error=f"无法读取图像：{src_fp}")

            # 用 mode='bit' 拿原始 0/1 序列（避免 mode='img' 内部触发 cv2.imwrite 不支持中文路径）
            wm_bit = bwm.extract(filename=None, embed_img=embed_img, wm_shape=(int(wm_h), int(wm_w)), mode='bit')
            import numpy as np
            wm = np.asarray(wm_bit).reshape(int(wm_h), int(wm_w))
            # 把 0/1 bit 还原成 0/255 灰度
            wm_img = (wm * 255).astype("uint8")
            if not _imwrite_unicode(str(out_fp), wm_img):
                return ModuleResult(success=False, error=f"写入输出图像失败：{out_fp}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            return ModuleResult(success=False, error=f"提取图片水印失败: {e}")

        if result_var:
            context.set_variable(str(result_var), str(out_fp))

        return ModuleResult(
            success=True,
            message=f"已提取图片水印，输出: {out_fp}",
            data={"output_path": str(out_fp)},
        )
