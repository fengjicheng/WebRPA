"""媒体处理模块 - 基于 yt-dlp 的下载与信息查询执行器集合

模块清单：
- ytdlp_download         : 下载视频（可选清晰度/格式/时间区间）
- ytdlp_download_audio   : 仅下载音频并转码为 mp3/wav/aac/m4a/opus/flac
- ytdlp_get_info         : 拿到视频元信息（标题/时长/作者/封面/描述/上传时间等）
- ytdlp_list_formats     : 列出全部可用清晰度/编码组合
- ytdlp_download_subtitle: 下载字幕（含自动生成的字幕）
- ytdlp_download_playlist: 批量下载播放列表/频道/搜索结果
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import time as time_module
from pathlib import Path
from typing import Optional

from .base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    register_executor,
    get_backend_root,
    get_ffmpeg_path,
)
from .type_utils import to_int


# ---------- 公共工具 ----------

def get_ytdlp_path() -> str:
    """返回 yt-dlp.exe 的绝对路径，找不到则回退到 PATH 中的 yt-dlp"""
    p = get_backend_root() / 'yt-dlp.exe'
    if p.exists():
        return str(p)
    # 兼容部分用户把可执行文件命名为 yt_dlp.exe 的情况
    p2 = get_backend_root() / 'yt_dlp.exe'
    if p2.exists():
        return str(p2)
    return 'yt-dlp'


def _format_size(size: int) -> str:
    if size <= 0:
        return '0 B'
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if size < 1024.0:
            return f'{size:.2f} {unit}'
        size /= 1024.0
    return f'{size:.2f} PB'


def _build_common_args(config: dict, context: ExecutionContext) -> list[str]:
    """构造 yt-dlp 通用参数（cookies、代理、UA、Referer、限速等）"""
    args: list[str] = []

    # 代理
    proxy = context.resolve_value(config.get('proxy', ''))
    if proxy:
        args += ['--proxy', proxy]

    # 不使用系统代理 / 强制不走代理
    if config.get('noProxy'):
        args += ['--proxy', '']

    # User-Agent
    ua = context.resolve_value(config.get('userAgent', ''))
    if ua:
        args += ['--user-agent', ua]

    # Referer
    referer = context.resolve_value(config.get('referer', ''))
    if referer:
        args += ['--referer', referer]

    # 自定义请求头：每行 "Key: Value"
    headers = context.resolve_value(config.get('customHeaders', ''))
    if headers:
        for line in str(headers).replace('|', '\n').split('\n'):
            line = line.strip()
            if line and ':' in line:
                args += ['--add-header', line]

    # cookies 文件
    cookies_file = context.resolve_value(config.get('cookiesFile', ''))
    if cookies_file:
        args += ['--cookies', cookies_file]

    # 从浏览器读 cookies（chrome / edge / firefox / safari ...）
    cookies_browser = context.resolve_value(config.get('cookiesFromBrowser', ''))
    if cookies_browser:
        args += ['--cookies-from-browser', cookies_browser]

    # 限速（如 5M、500K）
    rate_limit = context.resolve_value(config.get('rateLimit', ''))
    if rate_limit:
        args += ['--limit-rate', rate_limit]

    # 重试次数
    retries = to_int(config.get('retries', 5), 5, context)
    args += ['--retries', str(max(0, retries))]

    # 关闭进度条乱码（统一解析），强制 unicode 标准输出
    args += ['--no-color']

    # ffmpeg 路径（合并/转码用）
    ffmpeg = get_ffmpeg_path()
    if ffmpeg and ffmpeg != 'ffmpeg':
        args += ['--ffmpeg-location', ffmpeg]

    return args


def _ensure_dir(path: str) -> str:
    if not path:
        path = os.path.join(os.path.expanduser('~'), 'Downloads')
    os.makedirs(path, exist_ok=True)
    return path


def _strip_ext(filename: str) -> str:
    for ext in ('.mp4', '.mkv', '.webm', '.flv', '.mov', '.m4v', '.avi',
                '.mp3', '.wav', '.m4a', '.aac', '.opus', '.flac', '.ogg'):
        if filename.lower().endswith(ext):
            return filename[: -len(ext)]
    return filename


async def _run_ytdlp(
    args: list[str],
    *,
    timeout: int,
    context: ExecutionContext,
    label: str = '下载',
    capture_json: bool = False,
) -> tuple[bool, str, list[str]]:
    """执行 yt-dlp 子进程并把进度推到前端日志面板。

    返回 (success, last_meaningful_line_or_full_output, all_lines)
    """
    creationflags = 0x08000000 if os.name == 'nt' else 0  # CREATE_NO_WINDOW
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        creationflags=creationflags,
    )

    output_lines: list[str] = []
    last_progress_at = time_module.time()
    last_percent: str = ''
    last_speed: str = ''
    last_eta: str = ''

    progress_re = re.compile(r'\[download\].*?(\d+\.?\d*)%.*?at\s+([\d.]+\s*[KMG]?i?B/s).*?ETA\s+([\d:\-]+)', re.IGNORECASE)
    simple_percent_re = re.compile(r'(\d+\.?\d*)%')
    speed_re = re.compile(r'(\d+\.?\d*\s*[KMG]?i?B/s)', re.IGNORECASE)

    async def reader():
        nonlocal last_progress_at, last_percent, last_speed, last_eta
        while True:
            try:
                line = await asyncio.wait_for(process.stdout.readline(), timeout=5)
            except asyncio.TimeoutError:
                # 心跳：每 5 秒推一次
                now = time_module.time()
                if now - last_progress_at >= 5 and (last_percent or last_speed):
                    parts = [f'{label}中']
                    if last_percent:
                        parts.append(f'进度 {last_percent}%')
                    if last_speed:
                        parts.append(f'速度 {last_speed}')
                    if last_eta:
                        parts.append(f'ETA {last_eta}')
                    await context.send_progress(' | '.join(parts))
                    last_progress_at = now
                continue

            if not line:
                break

            text = line.decode('utf-8', errors='ignore').rstrip('\r\n')
            if not text:
                continue
            output_lines.append(text)

            m = progress_re.search(text)
            if m:
                last_percent = m.group(1)
                last_speed = m.group(2)
                last_eta = m.group(3)
            else:
                pm = simple_percent_re.search(text)
                if pm:
                    last_percent = pm.group(1)
                sm = speed_re.search(text)
                if sm:
                    last_speed = sm.group(1)

            now = time_module.time()
            if now - last_progress_at >= 1.5:
                if last_percent:
                    parts = [f'{label}进度 {last_percent}%']
                    if last_speed:
                        parts.append(f'速度 {last_speed}')
                    if last_eta:
                        parts.append(f'ETA {last_eta}')
                    await context.send_progress(' | '.join(parts))
                    last_progress_at = now
                elif '[Merger]' in text or '[ExtractAudio]' in text or '[VideoConvertor]' in text:
                    await context.send_progress(text)
                    last_progress_at = now

    try:
        await asyncio.wait_for(reader(), timeout=timeout)
        await process.wait()
    except asyncio.TimeoutError:
        try:
            process.kill()
            await process.wait()
        except Exception:
            pass
        return False, f'{label}超时（{timeout} 秒）', output_lines

    return_code = process.returncode
    full_output = '\n'.join(output_lines)
    if return_code != 0:
        # 抽出最后几条有意义的错误
        meaningful = [l for l in output_lines if 'ERROR' in l or 'error' in l.lower() or 'Unable' in l]
        if meaningful:
            return False, '\n'.join(meaningful[-3:]), output_lines
        return False, full_output[-800:] if full_output else '未知错误', output_lines

    if capture_json:
        # 找到第一条像 JSON 的行
        for l in output_lines:
            s = l.strip()
            if s.startswith('{') and s.endswith('}'):
                return True, s, output_lines
        return True, full_output, output_lines

    return True, full_output, output_lines


# ---------- 模块 1：视频下载 ----------

@register_executor
class YtDlpDownloadExecutor(ModuleExecutor):
    """yt-dlp 视频下载

    支持配置：
    - url: 视频链接（支持 YouTube / Bilibili / Twitter / TikTok / Twitch / 微博 / 抖音 等 1000+ 站点）
    - outputPath: 输出目录
    - outputFilename: 文件名模板（默认 %(title)s.%(ext)s）
    - quality: best / worst / 4k / 1080p / 720p / 480p / 360p / audio_only
    - container: mp4 / mkv / webm / 不指定
    - timeRange: 截取时间段（如 *00:01:00-00:02:30，格式 yt-dlp --download-sections）
    - resultVariable: 把输出文件路径写入哪个变量
    - 其它通用项见 _build_common_args
    """

    @property
    def module_type(self) -> str:
        return 'ytdlp_download'

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        url = context.resolve_value(config.get('url', ''))
        if not url:
            return ModuleResult(success=False, error='视频链接不能为空')

        ytdlp = get_ytdlp_path()
        if ytdlp == 'yt-dlp':
            # 用户没把 yt-dlp.exe 放到 backend 也允许走 PATH
            pass
        elif not Path(ytdlp).exists():
            return ModuleResult(success=False, error='yt-dlp.exe 不存在，请放置在 backend 目录下')

        output_path = _ensure_dir(context.resolve_value(config.get('outputPath', '')))
        output_filename = context.resolve_value(config.get('outputFilename', '')) or '%(title)s.%(ext)s'
        # 用户不熟模板时，简单文件名自动补 .%(ext)s
        if '%(' not in output_filename and not output_filename.endswith('%(ext)s'):
            output_filename = _strip_ext(output_filename) + '.%(ext)s'

        quality = (context.resolve_value(config.get('quality', 'best')) or 'best').lower()
        container = (context.resolve_value(config.get('container', '')) or '').lower()

        # 选择 format 表达式
        if quality == 'audio_only':
            format_expr = 'bestaudio/best'
        elif quality in ('best', '', 'auto'):
            format_expr = 'bestvideo+bestaudio/best'
        elif quality == 'worst':
            format_expr = 'worst'
        else:
            # 1080p / 720p / 4k / 2k / 480p ...
            height_map = {
                '4k': 2160, '2160p': 2160,
                '2k': 1440, '1440p': 1440,
                '1080p': 1080, '720p': 720, '480p': 480, '360p': 360, '240p': 240, '144p': 144,
            }
            h = height_map.get(quality)
            if h:
                format_expr = (
                    f'bestvideo[height<={h}]+bestaudio/best[height<={h}]/best'
                )
            else:
                format_expr = quality  # 直接传给 yt-dlp，比如 137+140

        timeout = to_int(config.get('timeout', 1800), 1800, context)
        time_range = context.resolve_value(config.get('timeRange', ''))
        result_variable = config.get('resultVariable', '')
        embed_thumbnail = bool(config.get('embedThumbnail', False))
        write_thumbnail = bool(config.get('writeThumbnail', False))
        embed_chapters = bool(config.get('embedChapters', False))
        write_info_json = bool(config.get('writeInfoJson', False))

        args = [
            ytdlp,
            url,
            '-f', format_expr,
            '-o', os.path.join(output_path, output_filename),
            '--no-playlist',
            '--newline',
            '--print', 'after_move:filepath',
            '--encoding', 'utf-8',
        ]

        if container in ('mp4', 'mkv', 'webm'):
            args += ['--merge-output-format', container]

        if time_range:
            args += ['--download-sections', str(time_range)]

        if embed_thumbnail:
            args += ['--embed-thumbnail']
        if write_thumbnail:
            args += ['--write-thumbnail']
        if embed_chapters:
            args += ['--embed-chapters']
        if write_info_json:
            args += ['--write-info-json']

        args += _build_common_args(config, context)

        await context.send_progress(f'开始下载视频：{url}')

        try:
            success, message, lines = await _run_ytdlp(args, timeout=timeout, context=context, label='下载')
        except Exception as e:
            return ModuleResult(success=False, error=f'调用 yt-dlp 失败：{e}')

        if not success:
            return ModuleResult(success=False, error=message)

        # 找到 yt-dlp --print after_move:filepath 输出的最后一行真实路径
        output_file = ''
        for line in reversed(lines):
            stripped = line.strip()
            if stripped and os.path.exists(stripped):
                output_file = stripped
                break

        if not output_file:
            # 兜底：扫一下输出目录，找最近修改的视频文件
            try:
                candidates = []
                for f in os.listdir(output_path):
                    fp = os.path.join(output_path, f)
                    if os.path.isfile(fp):
                        candidates.append((fp, os.path.getmtime(fp)))
                candidates.sort(key=lambda x: x[1], reverse=True)
                if candidates:
                    output_file = candidates[0][0]
            except Exception:
                pass

        if not output_file or not os.path.exists(output_file):
            return ModuleResult(success=False, error='下载完成但未能定位输出文件')

        size = os.path.getsize(output_file)
        size_str = _format_size(size)

        if result_variable:
            context.set_variable(result_variable, output_file)

        await context.send_progress(f'下载完成：{os.path.basename(output_file)}（{size_str}）', level='success')
        return ModuleResult(
            success=True,
            message=f'视频下载成功：{os.path.basename(output_file)}（{size_str}）',
            data={'output_path': output_file, 'file_size': size},
        )


# ---------- 模块 2：音频下载 ----------

@register_executor
class YtDlpDownloadAudioExecutor(ModuleExecutor):
    """yt-dlp 仅下载音频并转码

    audioFormat: mp3 / wav / m4a / aac / opus / flac / vorbis / best
    audioQuality: 0~10 或 192K / 320K（数字越小质量越高，0 = 最高）
    """

    @property
    def module_type(self) -> str:
        return 'ytdlp_download_audio'

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        url = context.resolve_value(config.get('url', ''))
        if not url:
            return ModuleResult(success=False, error='视频链接不能为空')

        ytdlp = get_ytdlp_path()
        if ytdlp != 'yt-dlp' and not Path(ytdlp).exists():
            return ModuleResult(success=False, error='yt-dlp.exe 不存在，请放置在 backend 目录下')

        output_path = _ensure_dir(context.resolve_value(config.get('outputPath', '')))
        output_filename = context.resolve_value(config.get('outputFilename', '')) or '%(title)s.%(ext)s'
        if '%(' not in output_filename and not output_filename.endswith('%(ext)s'):
            output_filename = _strip_ext(output_filename) + '.%(ext)s'

        audio_format = (context.resolve_value(config.get('audioFormat', 'mp3')) or 'mp3').lower()
        audio_quality = str(context.resolve_value(config.get('audioQuality', '0')) or '0')
        embed_thumbnail = bool(config.get('embedThumbnail', False))
        embed_metadata = bool(config.get('embedMetadata', True))

        timeout = to_int(config.get('timeout', 1800), 1800, context)
        time_range = context.resolve_value(config.get('timeRange', ''))
        result_variable = config.get('resultVariable', '')

        args = [
            ytdlp,
            url,
            '-f', 'bestaudio/best',
            '-x',
            '--audio-format', audio_format,
            '--audio-quality', audio_quality,
            '-o', os.path.join(output_path, output_filename),
            '--no-playlist',
            '--newline',
            '--print', 'after_move:filepath',
            '--encoding', 'utf-8',
        ]
        if embed_thumbnail:
            args += ['--embed-thumbnail']
        if embed_metadata:
            args += ['--embed-metadata']
        if time_range:
            args += ['--download-sections', str(time_range)]

        args += _build_common_args(config, context)

        await context.send_progress(f'开始下载音频（{audio_format}）：{url}')

        try:
            success, message, lines = await _run_ytdlp(args, timeout=timeout, context=context, label='下载音频')
        except Exception as e:
            return ModuleResult(success=False, error=f'调用 yt-dlp 失败：{e}')

        if not success:
            return ModuleResult(success=False, error=message)

        output_file = ''
        for line in reversed(lines):
            stripped = line.strip()
            if stripped and os.path.exists(stripped):
                output_file = stripped
                break
        if not output_file:
            # 兜底：找最近修改的音频文件
            try:
                exts = {'.mp3', '.wav', '.m4a', '.aac', '.opus', '.flac', '.ogg'}
                candidates = []
                for f in os.listdir(output_path):
                    if Path(f).suffix.lower() in exts:
                        fp = os.path.join(output_path, f)
                        candidates.append((fp, os.path.getmtime(fp)))
                candidates.sort(key=lambda x: x[1], reverse=True)
                if candidates:
                    output_file = candidates[0][0]
            except Exception:
                pass

        if not output_file or not os.path.exists(output_file):
            return ModuleResult(success=False, error='下载完成但未能定位输出文件')

        size = os.path.getsize(output_file)
        size_str = _format_size(size)
        if result_variable:
            context.set_variable(result_variable, output_file)

        await context.send_progress(f'音频下载完成：{os.path.basename(output_file)}（{size_str}）', level='success')
        return ModuleResult(
            success=True,
            message=f'音频下载成功：{os.path.basename(output_file)}（{size_str}）',
            data={'output_path': output_file, 'file_size': size},
        )


# ---------- 模块 3：获取视频信息 ----------

@register_executor
class YtDlpGetInfoExecutor(ModuleExecutor):
    """获取视频元信息（不下载视频本体）"""

    @property
    def module_type(self) -> str:
        return 'ytdlp_get_info'

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        url = context.resolve_value(config.get('url', ''))
        if not url:
            return ModuleResult(success=False, error='视频链接不能为空')

        ytdlp = get_ytdlp_path()
        if ytdlp != 'yt-dlp' and not Path(ytdlp).exists():
            return ModuleResult(success=False, error='yt-dlp.exe 不存在，请放置在 backend 目录下')

        timeout = to_int(config.get('timeout', 120), 120, context)
        result_variable = config.get('resultVariable', '')

        args = [
            ytdlp,
            url,
            '-J',  # 输出 JSON
            '--no-playlist',
            '--encoding', 'utf-8',
        ]
        args += _build_common_args(config, context)

        await context.send_progress(f'查询视频信息：{url}')

        try:
            success, output, lines = await _run_ytdlp(
                args, timeout=timeout, context=context, label='查询', capture_json=True,
            )
        except Exception as e:
            return ModuleResult(success=False, error=f'调用 yt-dlp 失败：{e}')

        if not success:
            return ModuleResult(success=False, error=output)

        # 解析 JSON
        info: dict = {}
        try:
            info = json.loads(output)
        except Exception:
            # 找一行最长的 JSON
            for line in lines:
                s = line.strip()
                if s.startswith('{') and s.endswith('}'):
                    try:
                        info = json.loads(s)
                        break
                    except Exception:
                        continue

        if not info:
            return ModuleResult(success=False, error='无法解析 yt-dlp 返回的 JSON')

        simplified = {
            'id': info.get('id'),
            'title': info.get('title'),
            'description': info.get('description'),
            'uploader': info.get('uploader') or info.get('channel'),
            'channel': info.get('channel'),
            'channel_url': info.get('channel_url'),
            'upload_date': info.get('upload_date'),
            'duration': info.get('duration'),
            'duration_string': info.get('duration_string'),
            'view_count': info.get('view_count'),
            'like_count': info.get('like_count'),
            'comment_count': info.get('comment_count'),
            'thumbnail': info.get('thumbnail'),
            'webpage_url': info.get('webpage_url') or url,
            'ext': info.get('ext'),
            'extractor': info.get('extractor'),
            'is_live': info.get('is_live'),
            'tags': info.get('tags'),
            'categories': info.get('categories'),
            'language': info.get('language'),
            'format': info.get('format'),
            'resolution': info.get('resolution'),
            'fps': info.get('fps'),
            'filesize_approx': info.get('filesize_approx'),
        }

        if result_variable:
            context.set_variable(result_variable, simplified)

        await context.send_progress(f'获取信息成功：{simplified.get("title", "?")}', level='success')

        return ModuleResult(
            success=True,
            message=f'获取视频信息：{simplified.get("title", "?")}',
            data=simplified,
        )


# ---------- 模块 4：列出可用格式 ----------

@register_executor
class YtDlpListFormatsExecutor(ModuleExecutor):
    """列出视频所有可用清晰度/编码格式（用于规划下载策略）"""

    @property
    def module_type(self) -> str:
        return 'ytdlp_list_formats'

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        url = context.resolve_value(config.get('url', ''))
        if not url:
            return ModuleResult(success=False, error='视频链接不能为空')

        ytdlp = get_ytdlp_path()
        if ytdlp != 'yt-dlp' and not Path(ytdlp).exists():
            return ModuleResult(success=False, error='yt-dlp.exe 不存在，请放置在 backend 目录下')

        timeout = to_int(config.get('timeout', 120), 120, context)
        result_variable = config.get('resultVariable', '')

        args = [
            ytdlp,
            url,
            '-J',
            '--no-playlist',
            '--encoding', 'utf-8',
        ]
        args += _build_common_args(config, context)

        try:
            success, output, lines = await _run_ytdlp(
                args, timeout=timeout, context=context, label='查询', capture_json=True,
            )
        except Exception as e:
            return ModuleResult(success=False, error=f'调用 yt-dlp 失败：{e}')

        if not success:
            return ModuleResult(success=False, error=output)

        try:
            info = json.loads(output)
        except Exception:
            return ModuleResult(success=False, error='无法解析 JSON')

        formats_raw = info.get('formats') or []
        formats: list[dict] = []
        for f in formats_raw:
            formats.append({
                'format_id': f.get('format_id'),
                'ext': f.get('ext'),
                'resolution': f.get('resolution') or (f'{f.get("width")}x{f.get("height")}' if f.get('width') else None),
                'fps': f.get('fps'),
                'vcodec': f.get('vcodec'),
                'acodec': f.get('acodec'),
                'tbr': f.get('tbr'),
                'filesize': f.get('filesize') or f.get('filesize_approx'),
                'format_note': f.get('format_note'),
            })

        if result_variable:
            context.set_variable(result_variable, formats)

        return ModuleResult(
            success=True,
            message=f'共 {len(formats)} 个可用格式',
            data={'count': len(formats), 'formats': formats},
        )


# ---------- 模块 5：下载字幕 ----------

@register_executor
class YtDlpDownloadSubtitleExecutor(ModuleExecutor):
    """下载字幕

    subtitleLang: zh-Hans,zh-CN,en  逗号分隔；为空时取 all
    autoSubtitle: 是否同时尝试自动生成字幕
    subtitleFormat: srt / vtt / ass / lrc / best
    """

    @property
    def module_type(self) -> str:
        return 'ytdlp_download_subtitle'

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        url = context.resolve_value(config.get('url', ''))
        if not url:
            return ModuleResult(success=False, error='视频链接不能为空')

        ytdlp = get_ytdlp_path()
        if ytdlp != 'yt-dlp' and not Path(ytdlp).exists():
            return ModuleResult(success=False, error='yt-dlp.exe 不存在，请放置在 backend 目录下')

        output_path = _ensure_dir(context.resolve_value(config.get('outputPath', '')))
        output_filename = context.resolve_value(config.get('outputFilename', '')) or '%(title)s.%(ext)s'
        if '%(' not in output_filename:
            output_filename = _strip_ext(output_filename) + '.%(ext)s'

        languages = (context.resolve_value(config.get('subtitleLang', '')) or '').strip()
        if not languages:
            languages = 'all'
        sub_format = (context.resolve_value(config.get('subtitleFormat', 'srt')) or 'srt').lower()
        auto_sub = bool(config.get('autoSubtitle', True))
        timeout = to_int(config.get('timeout', 600), 600, context)
        result_variable = config.get('resultVariable', '')

        args = [
            ytdlp,
            url,
            '--skip-download',
            '--write-subs',
            '--sub-langs', languages,
            '--sub-format', sub_format,
            '-o', os.path.join(output_path, output_filename),
            '--no-playlist',
            '--encoding', 'utf-8',
        ]
        if auto_sub:
            args += ['--write-auto-subs']
        # 强制把 vtt 转成 srt
        if sub_format == 'srt':
            args += ['--convert-subs', 'srt']

        args += _build_common_args(config, context)

        try:
            success, message, lines = await _run_ytdlp(
                args, timeout=timeout, context=context, label='字幕下载',
            )
        except Exception as e:
            return ModuleResult(success=False, error=f'调用 yt-dlp 失败：{e}')

        if not success:
            return ModuleResult(success=False, error=message)

        # 扫一下输出目录，找最新的字幕
        sub_exts = {'.srt', '.vtt', '.ass', '.lrc'}
        downloaded: list[str] = []
        try:
            now = time_module.time()
            for f in os.listdir(output_path):
                fp = os.path.join(output_path, f)
                if Path(f).suffix.lower() in sub_exts and os.path.isfile(fp):
                    if now - os.path.getmtime(fp) <= max(timeout, 600):
                        downloaded.append(fp)
        except Exception:
            pass

        if result_variable:
            context.set_variable(result_variable, downloaded)

        return ModuleResult(
            success=True,
            message=f'字幕下载完成（{len(downloaded)} 个文件）',
            data={'count': len(downloaded), 'files': downloaded},
        )


# ---------- 模块 6：批量下载播放列表 ----------

@register_executor
class YtDlpDownloadPlaylistExecutor(ModuleExecutor):
    """批量下载播放列表 / 频道 / 搜索结果

    支持配置：
    - url: 列表链接
    - playlistItems: 选取条目，例如 1-5,7,9（为空则全下）
    - maxItems: 最多下载多少条
    - quality / container / audioOnly 等同视频下载模块
    """

    @property
    def module_type(self) -> str:
        return 'ytdlp_download_playlist'

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        url = context.resolve_value(config.get('url', ''))
        if not url:
            return ModuleResult(success=False, error='链接不能为空')

        ytdlp = get_ytdlp_path()
        if ytdlp != 'yt-dlp' and not Path(ytdlp).exists():
            return ModuleResult(success=False, error='yt-dlp.exe 不存在，请放置在 backend 目录下')

        output_path = _ensure_dir(context.resolve_value(config.get('outputPath', '')))
        # 播放列表默认按 "%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s" 组织
        output_filename = context.resolve_value(config.get('outputFilename', '')) or \
            '%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s'

        quality = (context.resolve_value(config.get('quality', 'best')) or 'best').lower()
        container = (context.resolve_value(config.get('container', '')) or '').lower()
        audio_only = bool(config.get('audioOnly', False))
        audio_format = (context.resolve_value(config.get('audioFormat', 'mp3')) or 'mp3').lower()

        playlist_items = context.resolve_value(config.get('playlistItems', ''))
        max_items = to_int(config.get('maxItems', 0), 0, context)
        timeout = to_int(config.get('timeout', 7200), 7200, context)
        result_variable = config.get('resultVariable', '')
        skip_existing = bool(config.get('skipExisting', True))

        # 选择 format 表达式
        if audio_only:
            format_expr = 'bestaudio/best'
        elif quality in ('best', '', 'auto'):
            format_expr = 'bestvideo+bestaudio/best'
        elif quality == 'worst':
            format_expr = 'worst'
        else:
            height_map = {
                '4k': 2160, '2160p': 2160, '2k': 1440, '1440p': 1440,
                '1080p': 1080, '720p': 720, '480p': 480, '360p': 360,
            }
            h = height_map.get(quality)
            if h:
                format_expr = f'bestvideo[height<={h}]+bestaudio/best[height<={h}]/best'
            else:
                format_expr = quality

        args = [
            ytdlp,
            url,
            '-f', format_expr,
            '-o', os.path.join(output_path, output_filename),
            '--yes-playlist',
            '--newline',
            '--print', 'after_move:filepath',
            '--encoding', 'utf-8',
            '--ignore-errors',
        ]
        if container in ('mp4', 'mkv', 'webm'):
            args += ['--merge-output-format', container]
        if audio_only:
            args += ['-x', '--audio-format', audio_format, '--audio-quality', '0']
        if playlist_items:
            args += ['--playlist-items', str(playlist_items)]
        if max_items and max_items > 0:
            args += ['--max-downloads', str(max_items)]
        if skip_existing:
            args += ['--no-overwrites']

        args += _build_common_args(config, context)

        await context.send_progress(f'开始批量下载：{url}')

        try:
            success, message, lines = await _run_ytdlp(
                args, timeout=timeout, context=context, label='批量下载',
            )
        except Exception as e:
            return ModuleResult(success=False, error=f'调用 yt-dlp 失败：{e}')

        # 即使 ignore-errors，也认为成功（部分失败也算下完了部分）
        # 只要至少落地了一个文件就 success=True
        downloaded: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped and os.path.exists(stripped) and os.path.isfile(stripped):
                downloaded.append(stripped)

        if not downloaded and not success:
            return ModuleResult(success=False, error=message)

        # 兜底：如果 print after_move 没拿到，扫描 output_path 最新修改的文件
        if not downloaded:
            try:
                cutoff = time_module.time() - max(timeout, 600)
                for root, _, files in os.walk(output_path):
                    for f in files:
                        fp = os.path.join(root, f)
                        if os.path.getmtime(fp) >= cutoff:
                            downloaded.append(fp)
            except Exception:
                pass

        if result_variable:
            context.set_variable(result_variable, downloaded)

        total_size = sum(os.path.getsize(f) for f in downloaded if os.path.exists(f))
        await context.send_progress(
            f'批量下载完成：{len(downloaded)} 个文件，总计 {_format_size(total_size)}',
            level='success',
        )
        return ModuleResult(
            success=True,
            message=f'批量下载完成：共 {len(downloaded)} 个文件',
            data={'count': len(downloaded), 'files': downloaded, 'total_size': total_size},
        )
