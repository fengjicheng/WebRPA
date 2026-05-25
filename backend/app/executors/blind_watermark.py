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


def _import_bwm():
    """延迟导入 blind_watermark，并屏蔽它"first run"打印（每次新进程都会输出一次提示）"""
    from blind_watermark import WaterMark
    try:
        from blind_watermark import bw_notes  # noqa
        bw_notes.close()
    except Exception:
        pass
    return WaterMark


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

        if not out_path:
            return ModuleResult(success=False, error="输出路径不能为空")
        out_fp = _resolve_path(out_path)
        if out_fp is None:
            return ModuleResult(success=False, error="输出路径无效")
        _ensure_parent(out_fp)

        if not isinstance(text, str) or text == "":
            return ModuleResult(success=False, error="水印文本不能为空")

        try:
            WaterMark = _import_bwm()
            bwm = WaterMark(password_wm=password_wm, password_img=password_img)
            bwm.read_img(str(src_fp))
            bwm.read_wm(text, mode='str')
            bwm.embed(str(out_fp))
            wm_bit_len = int(len(bwm.wm_bit))
        except Exception as e:
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
    """盲水印 - 提取文本水印（必须知道嵌入时返回的 wm_bit_len + 两个密码）"""

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
            WaterMark = _import_bwm()
            bwm = WaterMark(password_wm=password_wm, password_img=password_img)
            extracted = bwm.extract(str(src_fp), wm_shape=wm_bit_len, mode='str')
        except Exception as e:
            return ModuleResult(success=False, error=f"提取文本水印失败: {e}")

        if result_var:
            context.set_variable(str(result_var), extracted)

        # 不在 message 中暴露完整文本（避免日志泄露），只显示长度
        return ModuleResult(
            success=True,
            message=f"已提取文本水印，长度 {len(extracted)} 字符",
            data={"text": extracted, "length": len(extracted)},
        )


@register_executor
class BwmEmbedImageExecutor(ModuleExecutor):
    """盲水印 - 嵌入图片水印（水印是一张小图，建议用纯黑白二值图）"""

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

        if not out_path:
            return ModuleResult(success=False, error="输出路径不能为空")
        out_fp = _resolve_path(out_path)
        if out_fp is None:
            return ModuleResult(success=False, error="输出路径无效")
        _ensure_parent(out_fp)

        try:
            WaterMark = _import_bwm()
            bwm = WaterMark(password_wm=password_wm, password_img=password_img)
            bwm.read_img(str(src_fp))
            bwm.read_wm(str(wm_fp))
            bwm.embed(str(out_fp))
            # 提取时需要知道水印图原尺寸（h, w），这里返回它
            shape_arr = bwm.wm_bit  # 1D 比特序列
            # blind_watermark 在 read_wm（图片）时把 wm_bit 拉平了，shape 信息保存在 bwm
            try:
                # 0.4.4: 暴露在 self.wm_bit_shape 不是公共字段，
                # 这里通过 PIL 原图直接获取 h/w
                from PIL import Image as _Img
                with _Img.open(str(wm_fp)) as im:
                    wm_w, wm_h = im.size
            except Exception:
                wm_w, wm_h = 0, 0
            wm_shape = [int(wm_h), int(wm_w)]
            wm_bit_len = int(len(shape_arr))
        except Exception as e:
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
    """盲水印 - 提取图片水印（必须知道嵌入时的水印图尺寸 [h,w]）"""

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

        if not out_path:
            return ModuleResult(success=False, error="提取结果输出路径不能为空")
        out_fp = _resolve_path(out_path)
        if out_fp is None:
            return ModuleResult(success=False, error="输出路径无效")
        _ensure_parent(out_fp)

        try:
            WaterMark = _import_bwm()
            bwm = WaterMark(password_wm=password_wm, password_img=password_img)
            bwm.extract(str(src_fp), wm_shape=(int(wm_h), int(wm_w)), out_wm_name=str(out_fp))
        except Exception as e:
            return ModuleResult(success=False, error=f"提取图片水印失败: {e}")

        if result_var:
            context.set_variable(str(result_var), str(out_fp))

        return ModuleResult(
            success=True,
            message=f"已提取图片水印，输出: {out_fp}",
            data={"output_path": str(out_fp)},
        )
