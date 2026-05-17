"""媒体处理模块 - 视频编辑相关"""
import asyncio
import os
import tempfile

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int, to_float
from .media_utils import get_media_duration, run_ffmpeg_with_progress, run_ffmpeg


@register_executor
class TrimVideoExecutor(ModuleExecutor):
    """视频裁剪模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "trim_video"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        start_time = context.resolve_value(config.get('startTime', '00:00:00'))
        end_time = context.resolve_value(config.get('endTime', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', 'trimmed_video')
        
        if not input_path:
            return ModuleResult(success=False, error="输入视频路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入视频不存在: {input_path}")
        
        try:
            if not output_path:
                base, ext = os.path.splitext(input_path)
                output_path = f"{base}_trimmed{ext}"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            args = ['-i', input_path]
            args.extend(['-ss', str(start_time)])
            
            if end_time:
                args.extend(['-to', str(end_time)])
            
            args.extend(['-c', 'copy'])
            args.append(output_path)
            
            await context.send_progress(f"🎬 开始裁剪视频 ({start_time} - {end_time or '结尾'})...")
            
            loop = asyncio.get_running_loop()
            success, message = await loop.run_in_executor(None, lambda: run_ffmpeg(args))
            
            if not success:
                return ModuleResult(success=False, error=f"视频裁剪失败: {message}")
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(success=True, message=f"视频裁剪完成: {output_path}",
                              data={'output_path': output_path})
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="视频裁剪已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"视频裁剪失败: {str(e)}")


@register_executor
class MergeMediaExecutor(ModuleExecutor):
    """媒体合并模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "merge_media"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        merge_type = context.resolve_value(config.get('mergeType', 'video'))
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', 'merged_file')
        
        if not output_path:
            return ModuleResult(success=False, error="输出文件路径不能为空")
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        if merge_type == 'audio_video':
            return await self._merge_audio_video(config, context, output_path, result_variable)
        
        return await self._merge_concat(config, context, output_path, result_variable)
    
    async def _merge_audio_video(self, config: dict, context: ExecutionContext, output_path: str, result_variable: str) -> ModuleResult:
        """音频+视频合并：将音频轨道添加到视频中"""
        video_path = context.resolve_value(config.get('videoPath', ''))
        audio_path = context.resolve_value(config.get('audioPath', ''))
        audio_mode = context.resolve_value(config.get('audioMode', 'replace'))
        audio_volume = to_float(config.get('audioVolume', 1.0), 1.0, context)
        original_volume = to_float(config.get('originalVolume', 1.0), 1.0, context)
        
        if not video_path:
            return ModuleResult(success=False, error="视频文件路径不能为空")
        
        if not audio_path:
            return ModuleResult(success=False, error="音频文件路径不能为空")
        
        if not os.path.exists(video_path):
            return ModuleResult(success=False, error=f"视频文件不存在: {video_path}")
        
        if not os.path.exists(audio_path):
            return ModuleResult(success=False, error=f"音频文件不存在: {audio_path}")
        
        try:
            duration = get_media_duration(video_path)
            
            args = ['-i', video_path, '-i', audio_path]
            
            if audio_mode == 'replace':
                args.extend([
                    '-map', '0:v:0',
                    '-map', '1:a:0',
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-b:a', '192k',
                ])
                if audio_volume != 1.0:
                    args.extend(['-af', f'volume={audio_volume}'])
                args.extend(['-shortest'])
                
            elif audio_mode == 'mix':
                filter_complex = f'[0:a]volume={original_volume}[a0];[1:a]volume={audio_volume}[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2[aout]'
                args.extend([
                    '-filter_complex', filter_complex,
                    '-map', '0:v:0',
                    '-map', '[aout]',
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-b:a', '192k',
                ])
            
            args.append(output_path)
            
            mode_text = "替换音频" if audio_mode == 'replace' else "混合音频"
            if duration:
                await context.send_progress(f"🎬 开始{mode_text}，预计时长 {duration:.0f} 秒...")
            else:
                await context.send_progress(f"🎬 开始{mode_text}...")
            
            success, message = await run_ffmpeg_with_progress(
                args, timeout=7200, total_duration=duration, context=context
            )
            
            if not success:
                return ModuleResult(success=False, error=f"音视频合并失败: {message}")
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(success=True, message=f"音视频合并完成: {output_path}",
                              data={'output_path': output_path, 'mode': audio_mode})
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="音视频合并已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"音视频合并失败: {str(e)}")
    
    async def _merge_concat(self, config: dict, context: ExecutionContext, output_path: str, result_variable: str) -> ModuleResult:
        """普通合并：多个同类型文件拼接"""
        input_files_var = config.get('inputFiles', '')
        
        if not input_files_var:
            return ModuleResult(success=False, error="输入文件列表不能为空")
        
        input_files = context.resolve_value(input_files_var)
        if isinstance(input_files, str):
            input_files = context.variables.get(input_files_var.strip('{}'), [])
        
        if not isinstance(input_files, list) or len(input_files) < 2:
            return ModuleResult(success=False, error="至少需要2个文件进行合并")
        
        for f in input_files:
            if not os.path.exists(f):
                return ModuleResult(success=False, error=f"文件不存在: {f}")
        
        list_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                list_file = f.name
                for file_path in input_files:
                    escaped_path = file_path.replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")
            
            args = ['-f', 'concat', '-safe', '0', '-i', list_file, '-c', 'copy', output_path]
            
            await context.send_progress(f"🎬 开始合并 {len(input_files)} 个媒体文件...")
            
            loop = asyncio.get_running_loop()
            success, message = await loop.run_in_executor(None, lambda: run_ffmpeg(args))
            
            if not success:
                return ModuleResult(success=False, error=f"媒体合并失败: {message}")
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(success=True, message=f"媒体合并完成: {output_path}",
                              data={'output_path': output_path, 'file_count': len(input_files)})
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="媒体合并已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"媒体合并失败: {str(e)}")
        finally:
            if list_file and os.path.exists(list_file):
                try:
                    os.unlink(list_file)
                except Exception:
                    pass


@register_executor
class RotateVideoExecutor(ModuleExecutor):
    """视频旋转/翻转模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "rotate_video"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        rotate_type = context.resolve_value(config.get('rotateType', 'rotate_90'))
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', 'rotated_video')
        
        if not input_path:
            return ModuleResult(success=False, error="输入视频路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入视频不存在: {input_path}")
        
        try:
            if not output_path:
                base, ext = os.path.splitext(input_path)
                output_path = f"{base}_rotated{ext}"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            duration = get_media_duration(input_path)
            
            args = ['-i', input_path]
            
            if rotate_type == 'rotate_90':
                args.extend(['-vf', 'transpose=1'])
            elif rotate_type == 'rotate_180':
                args.extend(['-vf', 'transpose=1,transpose=1'])
            elif rotate_type == 'rotate_270':
                args.extend(['-vf', 'transpose=2'])
            elif rotate_type == 'flip_h':
                args.extend(['-vf', 'hflip'])
            elif rotate_type == 'flip_v':
                args.extend(['-vf', 'vflip'])
            else:
                return ModuleResult(success=False, error=f"不支持的旋转类型: {rotate_type}")
            
            args.extend(['-c:a', 'copy'])
            args.append(output_path)
            
            if duration:
                await context.send_progress(f"🎬 开始旋转视频，预计时长 {duration:.0f} 秒...")
            else:
                await context.send_progress(f"🎬 开始旋转视频...")
            
            success, message = await run_ffmpeg_with_progress(
                args, timeout=3600, total_duration=duration, context=context
            )
            
            if not success:
                return ModuleResult(success=False, error=f"视频旋转失败: {message}")
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(success=True, message=f"视频旋转完成: {output_path}",
                              data={'output_path': output_path})
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="视频旋转已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"视频旋转失败: {str(e)}")


@register_executor
class VideoSpeedExecutor(ModuleExecutor):
    """视频倍速播放模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "video_speed"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        speed = to_float(config.get('speed', 1.0), 1.0, context)
        adjust_audio = config.get('adjustAudio', True)
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', 'speed_video')
        
        if not input_path:
            return ModuleResult(success=False, error="输入视频路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入视频不存在: {input_path}")
        
        if speed <= 0 or speed > 100:
            return ModuleResult(success=False, error="倍速必须在 0-100 之间")
        
        try:
            if not output_path:
                base, ext = os.path.splitext(input_path)
                output_path = f"{base}_speed{speed}x{ext}"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            duration = get_media_duration(input_path)
            
            args = ['-i', input_path]
            video_filter = f"setpts={1/speed}*PTS"
            
            if adjust_audio:
                audio_filter = ""
                temp_speed = speed
                
                while temp_speed > 2.0:
                    audio_filter += "atempo=2.0,"
                    temp_speed /= 2.0
                while temp_speed < 0.5:
                    audio_filter += "atempo=0.5,"
                    temp_speed /= 0.5
                audio_filter += f"atempo={temp_speed}"
                
                args.extend(['-filter_complex', f"[0:v]{video_filter}[v];[0:a]{audio_filter}[a]"])
                args.extend(['-map', '[v]', '-map', '[a]'])
            else:
                args.extend(['-vf', video_filter])
                args.extend(['-c:a', 'copy'])
            
            args.append(output_path)
            
            if duration:
                new_duration = duration / speed
                await context.send_progress(f"🎬 开始调整视频速度（{speed}x），预计时长 {new_duration:.0f} 秒...")
            else:
                await context.send_progress(f"🎬 开始调整视频速度（{speed}x）...")
            
            success, message = await run_ffmpeg_with_progress(
                args, timeout=7200, total_duration=duration, context=context
            )
            
            if not success:
                return ModuleResult(success=False, error=f"视频倍速处理失败: {message}")
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(success=True, message=f"视频倍速处理完成（{speed}x）: {output_path}",
                              data={'output_path': output_path, 'speed': speed})
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="视频倍速处理已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"视频倍速处理失败: {str(e)}")


@register_executor
class ExtractFrameExecutor(ModuleExecutor):
    """视频截取帧模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "extract_frame"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        timestamp = context.resolve_value(config.get('timestamp', '00:00:01'))
        output_path = context.resolve_value(config.get('outputPath', ''))
        image_format = context.resolve_value(config.get('imageFormat', 'jpg'))
        result_variable = config.get('resultVariable', 'frame_image')
        
        if not input_path:
            return ModuleResult(success=False, error="输入视频路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入视频不存在: {input_path}")
        
        try:
            if not output_path:
                base_name = os.path.splitext(input_path)[0]
                output_path = f"{base_name}_frame.{image_format}"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            args = ['-ss', str(timestamp), '-i', input_path, '-vframes', '1', '-q:v', '2', output_path]
            
            await context.send_progress(f"🎬 开始提取视频帧（{timestamp}）...")
            
            loop = asyncio.get_running_loop()
            success, message = await loop.run_in_executor(None, lambda: run_ffmpeg(args, timeout=60))
            
            if not success:
                return ModuleResult(success=False, error=f"提取视频帧失败: {message}")
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(success=True, message=f"视频帧提取完成: {output_path}",
                              data={'output_path': output_path, 'timestamp': timestamp})
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="提取视频帧已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"提取视频帧失败: {str(e)}")


@register_executor
class AddSubtitleExecutor(ModuleExecutor):
    """视频添加字幕模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "add_subtitle"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        subtitle_file = context.resolve_value(config.get('subtitleFile', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', 'subtitled_video')
        
        if not input_path:
            return ModuleResult(success=False, error="输入视频路径不能为空")
        
        if not subtitle_file:
            return ModuleResult(success=False, error="字幕文件路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入视频不存在: {input_path}")
        
        if not os.path.exists(subtitle_file):
            return ModuleResult(success=False, error=f"字幕文件不存在: {subtitle_file}")
        
        try:
            if not output_path:
                base, ext = os.path.splitext(input_path)
                output_path = f"{base}_subtitled{ext}"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            duration = get_media_duration(input_path)
            
            escaped_subtitle = subtitle_file.replace('\\', '/').replace(':', '\\:')
            args = ['-i', input_path, '-vf', f"subtitles='{escaped_subtitle}'", '-c:a', 'copy', output_path]
            
            if duration:
                await context.send_progress(f"🎬 开始添加字幕，预计时长 {duration:.0f} 秒...")
            else:
                await context.send_progress(f"🎬 开始添加字幕...")
            
            success, message = await run_ffmpeg_with_progress(
                args, timeout=7200, total_duration=duration, context=context
            )
            
            if not success:
                return ModuleResult(success=False, error=f"添加字幕失败: {message}")
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(success=True, message=f"字幕添加完成: {output_path}",
                              data={'output_path': output_path})
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="添加字幕已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"添加字幕失败: {str(e)}")


@register_executor
class ResizeVideoExecutor(ModuleExecutor):
    """视频分辨率调整模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "resize_video"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        width = to_int(config.get('width', 0), 0, context)
        height = to_int(config.get('height', 0), 0, context)
        keep_aspect = config.get('keepAspect', True)
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', 'resized_video')
        
        if not input_path:
            return ModuleResult(success=False, error="输入视频路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入视频不存在: {input_path}")
        
        if width <= 0 and height <= 0:
            return ModuleResult(success=False, error="宽度和高度至少需要指定一个")
        
        try:
            if not output_path:
                base, ext = os.path.splitext(input_path)
                output_path = f"{base}_resized{ext}"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            duration = get_media_duration(input_path)
            
            args = ['-i', input_path]
            
            if keep_aspect:
                if width > 0 and height > 0:
                    scale_filter = f"scale='min({width},iw)':'min({height},ih)':force_original_aspect_ratio=decrease"
                elif width > 0:
                    scale_filter = f"scale={width}:-1"
                else:
                    scale_filter = f"scale=-1:{height}"
            else:
                w = width if width > 0 else 'iw'
                h = height if height > 0 else 'ih'
                scale_filter = f"scale={w}:{h}"
            
            args.extend(['-vf', scale_filter])
            args.extend(['-c:a', 'copy'])
            args.append(output_path)
            
            if duration:
                await context.send_progress(f"🎬 开始调整分辨率，预计时长 {duration:.0f} 秒...")
            else:
                await context.send_progress(f"🎬 开始调整分辨率...")
            
            success, message = await run_ffmpeg_with_progress(
                args, timeout=7200, total_duration=duration, context=context
            )
            
            if not success:
                return ModuleResult(success=False, error=f"分辨率调整失败: {message}")
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(success=True, message=f"分辨率调整完成: {output_path}",
                              data={'output_path': output_path, 'width': width, 'height': height})
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="分辨率调整已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"分辨率调整失败: {str(e)}")
