"""格式工厂模块 - 完整的媒体格式转换功能"""
import asyncio
import os
from pathlib import Path
from typing import Optional

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int, to_float, to_bool
from .media_utils import get_media_duration, run_ffmpeg_with_progress, run_ffmpeg


# ==================== 图片格式转换 ====================

@register_executor
class ImageFormatConvertExecutor(ModuleExecutor):
    """图片格式转换执行器 - 支持所有常见图片格式互转"""
    
    @property
    def module_type(self) -> str:
        return "image_format_convert"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        支持的格式: jpg, jpeg, png, bmp, gif, webp, tiff, ico, svg
        """
        input_path = context.resolve_value(config.get('inputPath', ''))
        output_format = context.resolve_value(config.get('outputFormat', 'png')).lower()
        output_path = context.resolve_value(config.get('outputPath', ''))
        quality = to_int(config.get('quality', 95), 95, context)  # 1-100
        resize_width = config.get('resizeWidth', '')
        resize_height = config.get('resizeHeight', '')
        result_variable = config.get('resultVariable', 'converted_image')
        
        if not input_path:
            return ModuleResult(success=False, error="输入图片路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入图片不存在: {input_path}")
        
        # 支持的图片格式
        supported_formats = ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp', 'tiff', 'tif', 'ico']
        if output_format not in supported_formats:
            return ModuleResult(success=False, error=f"不支持的输出格式: {output_format}")
        
        try:
            # 生成输出路径
            if not output_path:
                base_name = os.path.splitext(input_path)[0]
                output_path = f"{base_name}.{output_format}"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            # 构建 FFmpeg 命令
            args = ['-i', input_path]
            
            # 添加缩放参数
            if resize_width or resize_height:
                width = to_int(resize_width, -1, context) if resize_width else -1
                height = to_int(resize_height, -1, context) if resize_height else -1
                args.extend(['-vf', f'scale={width}:{height}'])
            
            # 设置质量参数
            if output_format in ['jpg', 'jpeg']:
                # JPEG 质量: q:v 范围 2-31 (值越小质量越高)
                q_value = int((100 - quality) / 100 * 29 + 2)
                args.extend(['-q:v', str(q_value)])
            elif output_format == 'png':
                # PNG 压缩级别: 0-9
                compression = int((100 - quality) / 10)
                args.extend(['-compression_level', str(compression)])
            elif output_format == 'webp':
                args.extend(['-quality', str(quality)])
            
            args.append(output_path)
            
            await context.send_progress(f"🖼️ 开始转换图片格式: {output_format.upper()}...")
            
            loop = asyncio.get_running_loop()
            success, message = await loop.run_in_executor(None, lambda: run_ffmpeg(args, timeout=300))
            
            if not success:
                return ModuleResult(success=False, error=f"图片格式转换失败: {message}")
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(
                success=True,
                message=f"图片格式转换完成: {output_path}",
                data={'output_path': output_path, 'format': output_format}
            )
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="图片格式转换已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"图片格式转换失败: {str(e)}")


# ==================== 视频格式转换 ====================

@register_executor
class VideoFormatConvertExecutor(ModuleExecutor):
    """视频格式转换执行器 - 支持所有常见视频格式互转"""
    
    @property
    def module_type(self) -> str:
        return "video_format_convert"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        支持的格式: mp4, avi, mkv, mov, wmv, flv, webm, m4v, mpg, mpeg, 3gp, ts
        """
        input_path = context.resolve_value(config.get('inputPath', ''))
        output_format = context.resolve_value(config.get('outputFormat', 'mp4')).lower()
        output_path = context.resolve_value(config.get('outputPath', ''))
        video_codec = context.resolve_value(config.get('videoCodec', 'auto'))
        audio_codec = context.resolve_value(config.get('audioCodec', 'auto'))
        video_bitrate = context.resolve_value(config.get('videoBitrate', ''))
        audio_bitrate = context.resolve_value(config.get('audioBitrate', '128k'))
        fps = config.get('fps', '')
        resolution = context.resolve_value(config.get('resolution', ''))
        result_variable = config.get('resultVariable', 'converted_video')
        
        if not input_path:
            return ModuleResult(success=False, error="输入视频路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入视频不存在: {input_path}")
        
        # 支持的视频格式
        supported_formats = ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v', 'mpg', 'mpeg', '3gp', 'ts', 'ogv']
        if output_format not in supported_formats:
            return ModuleResult(success=False, error=f"不支持的输出格式: {output_format}")
        
        try:
            # 生成输出路径
            if not output_path:
                base_name = os.path.splitext(input_path)[0]
                output_path = f"{base_name}_converted.{output_format}"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            # 获取视频时长
            duration = get_media_duration(input_path)
            
            # 构建 FFmpeg 命令
            args = ['-i', input_path]
            
            # 视频编码器
            if video_codec == 'auto':
                # 根据输出格式自动选择编码器
                codec_map = {
                    'mp4': 'libx264',
                    'webm': 'libvpx-vp9',
                    'mkv': 'libx264',
                    'avi': 'mpeg4',
                    'mov': 'libx264',
                    'flv': 'flv',
                    'wmv': 'wmv2',
                    '3gp': 'h263',
                    'ogv': 'libtheora'
                }
                video_codec = codec_map.get(output_format, 'libx264')
            
            if video_codec != 'copy':
                args.extend(['-c:v', video_codec])
            else:
                args.extend(['-c:v', 'copy'])
            
            # 音频编码器
            if audio_codec == 'auto':
                audio_codec_map = {
                    'mp4': 'aac',
                    'webm': 'libopus',
                    'mkv': 'aac',
                    'avi': 'mp3',
                    'mov': 'aac',
                    'flv': 'aac',
                    'wmv': 'wmav2',
                    'ogv': 'libvorbis'
                }
                audio_codec = audio_codec_map.get(output_format, 'aac')
            
            if audio_codec != 'copy':
                args.extend(['-c:a', audio_codec])
                args.extend(['-b:a', audio_bitrate])
            else:
                args.extend(['-c:a', 'copy'])
            
            # 视频比特率
            if video_bitrate:
                args.extend(['-b:v', video_bitrate])
            
            # 帧率
            if fps:
                fps_value = to_int(fps, 0, context)
                if fps_value > 0:
                    args.extend(['-r', str(fps_value)])
            
            # 分辨率
            if resolution:
                args.extend(['-s', resolution])
            
            args.append(output_path)
            
            if duration:
                await context.send_progress(f"🎬 开始转换视频格式: {output_format.upper()}，预计时长 {duration:.0f} 秒...")
            else:
                await context.send_progress(f"🎬 开始转换视频格式: {output_format.upper()}...")
            
            success, message = await run_ffmpeg_with_progress(
                args,
                timeout=7200,
                total_duration=duration,
                context=context
            )
            
            if not success:
                return ModuleResult(success=False, error=f"视频格式转换失败: {message}")
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(
                success=True,
                message=f"视频格式转换完成: {output_path}",
                data={'output_path': output_path, 'format': output_format}
            )
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="视频格式转换已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"视频格式转换失败: {str(e)}")


# ==================== 音频格式转换 ====================

@register_executor
class AudioFormatConvertExecutor(ModuleExecutor):
    """音频格式转换执行器 - 支持所有常见音频格式互转"""
    
    @property
    def module_type(self) -> str:
        return "audio_format_convert"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        支持的格式: mp3, aac, wav, flac, ogg, m4a, wma, opus, ac3, amr
        """
        input_path = context.resolve_value(config.get('inputPath', ''))
        output_format = context.resolve_value(config.get('outputFormat', 'mp3')).lower()
        output_path = context.resolve_value(config.get('outputPath', ''))
        audio_codec = context.resolve_value(config.get('audioCodec', 'auto'))
        bitrate = context.resolve_value(config.get('bitrate', '192k'))
        sample_rate = config.get('sampleRate', '')
        channels = config.get('channels', '')
        result_variable = config.get('resultVariable', 'converted_audio')
        
        if not input_path:
            return ModuleResult(success=False, error="输入音频路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入音频不存在: {input_path}")
        
        # 支持的音频格式
        supported_formats = ['mp3', 'aac', 'wav', 'flac', 'ogg', 'm4a', 'wma', 'opus', 'ac3', 'amr', 'ape']
        if output_format not in supported_formats:
            return ModuleResult(success=False, error=f"不支持的输出格式: {output_format}")
        
        try:
            # 生成输出路径
            if not output_path:
                base_name = os.path.splitext(input_path)[0]
                output_path = f"{base_name}.{output_format}"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            # 获取音频时长
            duration = get_media_duration(input_path)
            
            # 构建 FFmpeg 命令
            args = ['-i', input_path]
            
            # 音频编码器
            if audio_codec == 'auto':
                codec_map = {
                    'mp3': 'libmp3lame',
                    'aac': 'aac',
                    'wav': 'pcm_s16le',
                    'flac': 'flac',
                    'ogg': 'libvorbis',
                    'm4a': 'aac',
                    'wma': 'wmav2',
                    'opus': 'libopus',
                    'ac3': 'ac3',
                    'amr': 'libopencore_amrnb'
                }
                audio_codec = codec_map.get(output_format, 'aac')
            
            args.extend(['-c:a', audio_codec])
            
            # 比特率 (WAV 和 FLAC 无损格式不需要)
            if output_format not in ['wav', 'flac', 'ape']:
                args.extend(['-b:a', bitrate])
            
            # 采样率
            if sample_rate:
                rate = to_int(sample_rate, 0, context)
                if rate > 0:
                    args.extend(['-ar', str(rate)])
            
            # 声道数
            if channels:
                ch = to_int(channels, 0, context)
                if ch > 0:
                    args.extend(['-ac', str(ch)])
            
            # 移除视频流
            args.extend(['-vn'])
            
            args.append(output_path)
            
            if duration:
                await context.send_progress(f"🎵 开始转换音频格式: {output_format.upper()}，预计时长 {duration:.0f} 秒...")
            else:
                await context.send_progress(f"🎵 开始转换音频格式: {output_format.upper()}...")
            
            success, message = await run_ffmpeg_with_progress(
                args,
                timeout=3600,
                total_duration=duration,
                context=context
            )
            
            if not success:
                return ModuleResult(success=False, error=f"音频格式转换失败: {message}")
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(
                success=True,
                message=f"音频格式转换完成: {output_path}",
                data={'output_path': output_path, 'format': output_format}
            )
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="音频格式转换已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"音频格式转换失败: {str(e)}")


# ==================== 视频转音频 ====================

@register_executor
class VideoToAudioExecutor(ModuleExecutor):
    """视频转音频执行器 - 从视频中提取音频"""
    
    @property
    def module_type(self) -> str:
        return "video_to_audio"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        output_format = context.resolve_value(config.get('outputFormat', 'mp3')).lower()
        output_path = context.resolve_value(config.get('outputPath', ''))
        bitrate = context.resolve_value(config.get('bitrate', '192k'))
        sample_rate = config.get('sampleRate', '')
        result_variable = config.get('resultVariable', 'extracted_audio')
        
        if not input_path:
            return ModuleResult(success=False, error="输入视频路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入视频不存在: {input_path}")
        
        try:
            # 生成输出路径
            if not output_path:
                base_name = os.path.splitext(input_path)[0]
                output_path = f"{base_name}_audio.{output_format}"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            duration = get_media_duration(input_path)
            
            # 构建 FFmpeg 命令
            args = ['-i', input_path]
            args.extend(['-vn'])  # 不要视频
            args.extend(['-b:a', bitrate])
            
            # 采样率
            if sample_rate:
                rate = to_int(sample_rate, 0, context)
                if rate > 0:
                    args.extend(['-ar', str(rate)])
            
            # 根据格式选择编码器
            codec_map = {
                'mp3': 'libmp3lame',
                'aac': 'aac',
                'wav': 'pcm_s16le',
                'flac': 'flac',
                'ogg': 'libvorbis',
                'm4a': 'aac'
            }
            codec = codec_map.get(output_format, 'aac')
            args.extend(['-c:a', codec])
            
            args.append(output_path)
            
            if duration:
                await context.send_progress(f"🎵 开始提取音频，预计时长 {duration:.0f} 秒...")
            else:
                await context.send_progress(f"🎵 开始提取音频...")
            
            success, message = await run_ffmpeg_with_progress(
                args,
                timeout=3600,
                total_duration=duration,
                context=context
            )
            
            if not success:
                return ModuleResult(success=False, error=f"提取音频失败: {message}")
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(
                success=True,
                message=f"音频提取完成: {output_path}",
                data={'output_path': output_path}
            )
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="提取音频已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"提取音频失败: {str(e)}")


# ==================== 视频转GIF ====================

@register_executor
class VideoToGIFExecutor(ModuleExecutor):
    """视频转GIF执行器 - 将视频转换为GIF动图"""
    
    @property
    def module_type(self) -> str:
        return "video_to_gif"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        fps = to_int(config.get('fps', 10), 10, context)
        width = config.get('width', 480)
        start_time = context.resolve_value(config.get('startTime', ''))
        duration = context.resolve_value(config.get('duration', ''))
        result_variable = config.get('resultVariable', 'gif_path')
        
        if not input_path:
            return ModuleResult(success=False, error="输入视频路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入视频不存在: {input_path}")
        
        try:
            # 生成输出路径
            if not output_path:
                base_name = os.path.splitext(input_path)[0]
                output_path = f"{base_name}.gif"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            width_value = to_int(width, 480, context)
            total_duration = get_media_duration(input_path)
            
            # 构建 FFmpeg 命令
            args = ['-i', input_path]
            
            # 时间范围
            if start_time:
                args.extend(['-ss', start_time])
            if duration:
                args.extend(['-t', duration])
            
            # GIF 优化滤镜
            args.extend(['-vf', f'fps={fps},scale={width_value}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse'])
            
            args.append(output_path)
            
            await context.send_progress(f"🎬 开始转换为GIF动图...")
            
            success, message = await run_ffmpeg_with_progress(
                args,
                timeout=1800,
                total_duration=total_duration,
                context=context
            )
            
            if not success:
                return ModuleResult(success=False, error=f"转换GIF失败: {message}")
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(
                success=True,
                message=f"GIF转换完成: {output_path}",
                data={'output_path': output_path}
            )
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="转换GIF已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"转换GIF失败: {str(e)}")


# ==================== 批量格式转换 ====================

@register_executor
class BatchFormatConvertExecutor(ModuleExecutor):
    """批量格式转换执行器 - 批量转换文件夹中的所有媒体文件"""
    
    @property
    def module_type(self) -> str:
        return "batch_format_convert"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_folder = context.resolve_value(config.get('inputFolder', ''))
        output_folder = context.resolve_value(config.get('outputFolder', ''))
        output_format = context.resolve_value(config.get('outputFormat', 'mp4')).lower()
        file_pattern = context.resolve_value(config.get('filePattern', '*.*'))
        recursive = to_bool(config.get('recursive', False), False, context=context)
        result_variable = config.get('resultVariable', 'converted_files')
        
        if not input_folder:
            return ModuleResult(success=False, error="输入文件夹路径不能为空")
        
        if not os.path.exists(input_folder):
            return ModuleResult(success=False, error=f"输入文件夹不存在: {input_folder}")
        
        try:
            # 生成输出文件夹
            if not output_folder:
                output_folder = os.path.join(input_folder, f"converted_{output_format}")
            
            os.makedirs(output_folder, exist_ok=True)
            
            # 查找文件
            from pathlib import Path
            input_path = Path(input_folder)
            
            if recursive:
                files = list(input_path.rglob(file_pattern))
            else:
                files = list(input_path.glob(file_pattern))
            
            if not files:
                return ModuleResult(success=False, error=f"未找到匹配的文件: {file_pattern}")
            
            await context.send_progress(f"📁 找到 {len(files)} 个文件，开始批量转换...")
            
            converted_files = []
            failed_files = []
            
            for i, file_path in enumerate(files, 1):
                if not file_path.is_file():
                    continue
                
                try:
                    # 生成输出路径
                    relative_path = file_path.relative_to(input_path)
                    output_file = Path(output_folder) / relative_path.parent / f"{file_path.stem}.{output_format}"
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    await context.send_progress(f"🎬 [{i}/{len(files)}] 转换: {file_path.name}...")
                    
                    # 构建 FFmpeg 命令
                    args = ['-i', str(file_path)]
                    args.append(str(output_file))
                    
                    duration = get_media_duration(str(file_path))
                    
                    success, message = await run_ffmpeg_with_progress(
                        args,
                        timeout=3600,
                        total_duration=duration,
                        context=context
                    )
                    
                    if success:
                        converted_files.append(str(output_file))
                    else:
                        failed_files.append(str(file_path))
                        
                except Exception as e:
                    failed_files.append(str(file_path))
                    await context.send_progress(f"❌ 转换失败: {file_path.name} - {str(e)}")
            
            if result_variable:
                context.set_variable(result_variable, converted_files)
            
            summary = f"批量转换完成: 成功 {len(converted_files)} 个，失败 {len(failed_files)} 个"
            
            return ModuleResult(
                success=True,
                message=summary,
                data={
                    'converted_files': converted_files,
                    'failed_files': failed_files,
                    'total': len(files),
                    'success_count': len(converted_files),
                    'failed_count': len(failed_files)
                }
            )
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="批量转换已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"批量转换失败: {str(e)}")
