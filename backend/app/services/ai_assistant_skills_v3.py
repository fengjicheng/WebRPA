"""
AI 助手 Skills v3 - 对标 Hermes Agent 的能力

借鉴 Hermes Agent 的 5 支柱架构（Nous Research）：
  1. Memory (user.md + memory.md)        ← 用户画像 + 项目环境
  2. Skills (markdown + YAML front-matter) ← AI 自创建技能
  3. Soul (soul.md)                        ← 教训/人格 - 不再犯第二次
  4. Crons                                  ← 定时 + 一次性延时
  5. Self-Improving Loop                   ← 用得越久越懂用户

具体新增能力：
  A. 系统控制：屏幕亮度 / 系统音量 / 启动程序 / 关闭程序 / 锁屏 / 关机
  B. 一次性延时：30 秒后做某事
  C. 自学习：把成功的工具组合保存为新 skill
  D. 教训记忆：犯过的错记录 + 下次自动 recall 避免重犯
  E. 用户画像：偏好/风格/常用 API 在多会话间累积
"""
from __future__ import annotations

import json
import os
import sys
import asyncio
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.services.ai_assistant_skills import (
    registry,
    Skill,
    _get_data_folder,
    execute_skill,
)


# =============================================================================
# 公共：数据目录
# =============================================================================

def _ai_data_dir() -> Path:
    folder = _get_data_folder() / 'ai_assistant'
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _learned_skills_dir() -> Path:
    folder = _ai_data_dir() / 'learned_skills'
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _lessons_file() -> Path:
    return _ai_data_dir() / 'lessons.json'


def _user_profile_file() -> Path:
    return _ai_data_dir() / 'user_profile.json'


def _soul_file() -> Path:
    return _ai_data_dir() / 'soul.md'


def _memory_md_file() -> Path:
    return _ai_data_dir() / 'memory.md'


def _user_md_file() -> Path:
    return _ai_data_dir() / 'user.md'


def _read_json(p: Path, default: Any) -> Any:
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return default


def _write_json(p: Path, data: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding='utf-8')


# =============================================================================
# A. 系统控制 - 屏幕亮度 / 音量 / 启动程序 / 关闭程序 / 锁屏 / 关机
# =============================================================================

async def skill_set_screen_brightness(percent: int, **_: Any) -> dict[str, Any]:
    """通过 PowerShell WMI 调整笔记本屏幕亮度（仅笔记本支持，台式机外接显示器无效）"""
    try:
        p = max(0, min(100, int(percent)))
    except Exception:
        return {'error': 'percent 必须是 0-100 的整数'}
    try:
        ps = (
            f'(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)'
            f'.WmiSetBrightness(1, {p})'
        )
        proc = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps],
            capture_output=True, text=True, timeout=10,
        )
        if proc.returncode != 0:
            return {'error': f'PowerShell 失败：{proc.stderr.strip() or proc.stdout.strip()}'}
        return {'success': True, 'brightness': p, 'message': f'已设置屏幕亮度为 {p}%'}
    except subprocess.TimeoutExpired:
        return {'error': '设置亮度超时'}
    except Exception as e:
        return {'error': f'设置亮度失败：{e}'}


async def skill_get_screen_brightness(**_: Any) -> dict[str, Any]:
    """读取当前屏幕亮度（仅笔记本）"""
    try:
        ps = '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness'
        proc = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps],
            capture_output=True, text=True, timeout=10,
        )
        out = (proc.stdout or '').strip()
        if proc.returncode != 0 or not out:
            return {'error': f'读取失败（可能是台式机不支持）：{proc.stderr.strip()}'}
        try:
            val = int(out.splitlines()[0])
        except Exception:
            return {'error': f'解析失败：{out}'}
        return {'brightness': val}
    except Exception as e:
        return {'error': f'读取亮度失败：{e}'}


async def skill_set_system_volume(percent: int, **_: Any) -> dict[str, Any]:
    """设置系统音量（0-100），优先用 pycaw，没有就降级到 nircmd"""
    try:
        p = max(0, min(100, int(percent)))
    except Exception:
        return {'error': 'percent 必须是 0-100 的整数'}
    # 1) 尝试 pycaw（精确）
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # type: ignore
        from comtypes import CLSCTX_ALL  # type: ignore
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        volume.SetMasterVolumeLevelScalar(p / 100.0, None)
        return {'success': True, 'volume': p, 'message': f'已设置系统音量为 {p}%（pycaw）'}
    except ImportError:
        pass
    except Exception:
        pass
    # 2) 降级：模拟按键（粗略，每次 2%）
    try:
        # 用 PowerShell 调 WScript.Shell 发送音量键
        ps_mute_check = "[Audio]::Volume" if False else ""
        # 简化做法：把目标 percent 转成"先静音再用 VolumeUp 键加上去"
        # 但这太粗糙。退而求其次：返回错误
        return {'error': '未安装 pycaw（推荐：pip install pycaw comtypes）'}
    except Exception as e:
        return {'error': f'设置音量失败：{e}'}


async def skill_get_system_volume(**_: Any) -> dict[str, Any]:
    """读取系统音量（0-100）"""
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # type: ignore
        from comtypes import CLSCTX_ALL  # type: ignore
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        scalar = volume.GetMasterVolumeLevelScalar()
        muted = bool(volume.GetMute())
        return {'volume': int(round(scalar * 100)), 'muted': muted}
    except ImportError:
        return {'error': '未安装 pycaw'}
    except Exception as e:
        return {'error': f'读取音量失败：{e}'}


async def skill_set_volume_mute(muted: bool = True, **_: Any) -> dict[str, Any]:
    """系统静音 / 取消静音"""
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # type: ignore
        from comtypes import CLSCTX_ALL  # type: ignore
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        volume.SetMute(1 if muted else 0, None)
        return {'success': True, 'muted': bool(muted)}
    except Exception as e:
        return {'error': f'静音失败：{e}'}


async def skill_launch_application(
    name_or_path: str,
    args: list[str] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """启动应用程序。可以传：
    - 完整路径：D:\\xxx\\xxx.exe
    - 应用名（Windows）：QQ / WeChat / chrome / notepad / cmd
    - 系统命令：cmd / explorer / mspaint / calc / control
    自动按以下顺序尝试：
      1) 直接 Popen 路径
      2) Win+R 协议（start xxx）
      3) 在常见安装目录里搜
    """
    if not name_or_path or not name_or_path.strip():
        return {'error': '应用名不能为空'}
    name = name_or_path.strip()
    args = args or []

    # 1) 如果是绝对路径，直接 Popen
    if os.path.isabs(name) and os.path.exists(name):
        try:
            subprocess.Popen([name, *args], shell=False)
            return {'success': True, 'launched': name, 'mode': 'absolute_path'}
        except Exception as e:
            return {'error': f'启动失败（绝对路径）：{e}'}

    # 2) start 命令（让 Windows 自己在 PATH / App Paths / 注册表里找）
    try:
        cmd = ['cmd', '/c', 'start', '', name, *args]
        subprocess.Popen(cmd, shell=False)
        # start 命令异步，我们没法立刻知道有没有跑起来，给一点容错
        await asyncio.sleep(0.4)
        return {'success': True, 'launched': name, 'mode': 'shell_start'}
    except Exception:
        pass

    # 3) 常见安装目录搜
    common_dirs = [
        r'C:\Program Files',
        r'C:\Program Files (x86)',
        os.path.expandvars(r'%LOCALAPPDATA%'),
        os.path.expandvars(r'%APPDATA%'),
    ]
    name_lower = name.lower()
    candidates: list[str] = []
    for root in common_dirs:
        if not os.path.isdir(root):
            continue
        try:
            for dirpath, _dirs, files in os.walk(root):
                for f in files:
                    fl = f.lower()
                    if fl.endswith('.exe') and name_lower in fl:
                        candidates.append(os.path.join(dirpath, f))
                        if len(candidates) >= 5:
                            break
                if len(candidates) >= 5:
                    break
            if len(candidates) >= 5:
                break
        except Exception:
            continue
    if candidates:
        target = candidates[0]
        try:
            subprocess.Popen([target, *args], shell=False)
            return {
                'success': True,
                'launched': target,
                'mode': 'searched',
                'other_candidates': candidates[1:],
            }
        except Exception as e:
            return {'error': f'启动失败（搜索路径）：{e}', 'candidates': candidates}

    return {'error': f'找不到 {name}。可以传完整路径，或检查是否已安装'}


async def skill_close_application(name: str, force: bool = False, **_: Any) -> dict[str, Any]:
    """通过进程名关闭应用"""
    if not name or not name.strip():
        return {'error': '进程名不能为空'}
    pname = name.strip()
    if not pname.lower().endswith('.exe'):
        pname = f'{pname}.exe'
    try:
        flag = '/F' if force else ''
        cmd = ['taskkill', '/IM', pname]
        if force:
            cmd.append('/F')
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            return {'success': True, 'killed': pname, 'output': proc.stdout.strip()}
        return {
            'error': f'关闭失败：{proc.stderr.strip() or proc.stdout.strip()}',
            'returncode': proc.returncode,
        }
    except Exception as e:
        return {'error': f'关闭失败：{e}'}


async def skill_lock_screen(**_: Any) -> dict[str, Any]:
    """锁屏（Win+L 等效）"""
    try:
        subprocess.Popen(['rundll32.exe', 'user32.dll,LockWorkStation'], shell=False)
        return {'success': True, 'message': '已发起锁屏'}
    except Exception as e:
        return {'error': f'锁屏失败：{e}'}


async def skill_shutdown_computer(
    seconds: int = 60,
    cancel: bool = False,
    restart: bool = False,
    **_: Any,
) -> dict[str, Any]:
    """关机 / 重启 / 取消（默认 60s 倒计时给用户反悔机会）"""
    try:
        if cancel:
            proc = subprocess.run(['shutdown', '/a'], capture_output=True, text=True, timeout=5)
            return {'success': proc.returncode == 0, 'message': '已取消关机/重启'}
        flag = '/r' if restart else '/s'
        secs = max(0, int(seconds))
        proc = subprocess.run(
            ['shutdown', flag, '/t', str(secs), '/d', 'p:0:0'],
            capture_output=True, text=True, timeout=5,
        )
        if proc.returncode != 0:
            return {'error': f'失败：{proc.stderr.strip() or proc.stdout.strip()}'}
        action = '重启' if restart else '关机'
        return {
            'success': True,
            'message': f'已发起 {secs}s 后{action}（用 cancel=True 撤销）',
        }
    except Exception as e:
        return {'error': f'shutdown 失败：{e}'}


async def skill_open_url(url: str, **_: Any) -> dict[str, Any]:
    """用默认浏览器打开 URL"""
    if not url:
        return {'error': 'url 必填'}
    try:
        os.startfile(url)
        return {'success': True, 'opened': url}
    except Exception as e:
        # 退到 start 命令
        try:
            subprocess.Popen(['cmd', '/c', 'start', '', url], shell=False)
            return {'success': True, 'opened': url, 'mode': 'shell_start'}
        except Exception as e2:
            return {'error': f'打开 URL 失败：{e}; {e2}'}


async def skill_send_notification(
    title: str,
    message: str,
    duration: int = 5,
    **_: Any,
) -> dict[str, Any]:
    """系统右下角通知（Windows Toast）"""
    try:
        from win10toast import ToastNotifier  # type: ignore
        ToastNotifier().show_toast(
            title or 'WebRPA',
            message or '',
            duration=max(1, int(duration)),
            threaded=True,
        )
        return {'success': True, 'notified': True}
    except ImportError:
        # PowerShell BurntToast 兜底太重；用 msg 命令
        try:
            subprocess.Popen([
                'msg', '*', '/time:5',
                f'{title}: {message}',
            ], shell=False)
            return {'success': True, 'notified': True, 'mode': 'msg'}
        except Exception as e:
            return {'error': f'通知失败：{e}'}
    except Exception as e:
        return {'error': f'通知失败：{e}'}


# =============================================================================
# B. 一次性延时执行 - "30 秒后把屏幕亮度调到 100%"
# =============================================================================

# 后台任务表 - 用 asyncio Task，可通过 token 取消
_pending_tasks: dict[str, asyncio.Task] = {}


async def skill_schedule_one_shot(
    delay_seconds: int,
    skill_name: str,
    skill_args: dict[str, Any] | None = None,
    note: str = '',
    **_: Any,
) -> dict[str, Any]:
    """N 秒后执行某个 skill 一次。
    
    例如：30 秒后把屏幕亮度调到 100% →
      schedule_one_shot(delay_seconds=30, skill_name='set_screen_brightness', skill_args={'percent': 100})
    
    返回 token，可用 cancel_one_shot 取消。
    """
    if not skill_name:
        return {'error': 'skill_name 必填'}
    try:
        delay = max(0, int(delay_seconds))
    except Exception:
        return {'error': 'delay_seconds 必须是整数'}

    skill_args = skill_args or {}
    token = uuid.uuid4().hex[:10]

    async def _runner():
        try:
            await asyncio.sleep(delay)
            await execute_skill(skill_name, skill_args)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f'[AIAssistant][one_shot] {token} 执行失败：{e}')
        finally:
            _pending_tasks.pop(token, None)

    task = asyncio.create_task(_runner())
    _pending_tasks[token] = task
    return {
        'success': True,
        'token': token,
        'fires_at': (datetime.now().timestamp() + delay),
        'message': f'已安排 {delay}s 后执行 {skill_name}（note={note}）',
        'tip': '用 cancel_one_shot(token=...) 取消',
    }


async def skill_cancel_one_shot(token: str, **_: Any) -> dict[str, Any]:
    """取消一个延时任务"""
    if not token:
        return {'error': 'token 必填'}
    task = _pending_tasks.pop(token, None)
    if not task:
        return {'error': f'找不到 token={token}（可能已经执行完或已取消）'}
    if not task.done():
        task.cancel()
    return {'success': True, 'cancelled': token}


async def skill_list_pending_tasks(**_: Any) -> dict[str, Any]:
    """列出所有待执行的延时任务"""
    items = []
    for token, t in list(_pending_tasks.items()):
        items.append({
            'token': token,
            'done': t.done(),
            'cancelled': t.cancelled() if t.done() else False,
        })
    return {'count': len(items), 'tasks': items}


# =============================================================================
# C. 自学习 - AI 自己创建可重用 Skill（学到了不再重新摸索）
# =============================================================================

async def skill_save_learned_skill(
    name: str,
    description: str,
    when_to_use: str,
    steps: list[dict],
    tags: list[str] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """把 AI 在对话中摸索出的"工具组合"保存成新 Skill（学到了不再重新摸索）。
    
    steps 数组，每个元素：
      {
        "tool": "build_workflow" 或者 "client_action" 等,
        "args": {...},
        "purpose": "这一步在干什么的中文说明"
      }
    
    保存为 markdown 文件（仿 Hermes Agent 的 skill 格式：YAML front-matter + 正文）
    存到 backend/data/ai_assistant/learned_skills/<name>.md
    
    后续会话可调 list_learned_skills + run_learned_skill 复用。
    """
    if not name or not name.strip():
        return {'error': 'name 必填'}
    name_safe = ''.join(c for c in name.strip() if c.isalnum() or c in '_-')
    if not name_safe:
        return {'error': 'name 只能包含字母、数字、下划线、横线'}
    if not isinstance(steps, list) or not steps:
        return {'error': 'steps 不能为空'}

    target = _learned_skills_dir() / f'{name_safe}.md'

    # YAML front-matter（Hermes 风格）
    front_matter = {
        'name': name_safe,
        'description': description or '',
        'when_to_use': when_to_use or '',
        'tags': tags or [],
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'usage_count': 0,
        'success_count': 0,
        'last_used': None,
        'steps_count': len(steps),
    }

    # markdown 正文
    parts = [
        '---',
        json.dumps(front_matter, ensure_ascii=False, indent=2),
        '---',
        '',
        f'# {name_safe}',
        '',
        f'**用途**：{description}',
        '',
        f'**何时使用**：{when_to_use}',
        '',
        '## 执行步骤',
        '',
    ]
    for i, s in enumerate(steps, 1):
        tool = s.get('tool', '')
        args = s.get('args', {}) or {}
        purpose = s.get('purpose', '')
        parts.extend([
            f'### Step {i}: {purpose or tool}',
            '',
            '```json',
            json.dumps({'tool': tool, 'args': args}, ensure_ascii=False, indent=2),
            '```',
            '',
        ])
    parts.append('')

    target.write_text('\n'.join(parts), encoding='utf-8')

    return {
        'success': True,
        'name': name_safe,
        'path': str(target),
        'message': f'Skill「{name_safe}」已保存（{len(steps)} 步）',
    }


def _parse_learned_skill(p: Path) -> dict[str, Any]:
    """读 markdown skill 文件 → 拆 front-matter + 步骤"""
    text = p.read_text(encoding='utf-8')
    front: dict[str, Any] = {}
    body = text
    if text.startswith('---'):
        try:
            end = text.find('---', 3)
            if end > 0:
                front = json.loads(text[3:end].strip())
                body = text[end + 3:]
        except Exception:
            front = {}
    # 抓 ```json 代码块作为 steps
    steps: list[dict] = []
    in_block = False
    block_lines: list[str] = []
    for line in body.splitlines():
        if line.strip().startswith('```json'):
            in_block = True
            block_lines = []
            continue
        if in_block and line.strip().startswith('```'):
            in_block = False
            try:
                steps.append(json.loads('\n'.join(block_lines)))
            except Exception:
                pass
            continue
        if in_block:
            block_lines.append(line)
    front['_path'] = str(p)
    front['_steps'] = steps
    return front


async def skill_list_learned_skills(query: str = '', **_: Any) -> dict[str, Any]:
    """列出所有 AI 学过的 Skill。可按 query（描述/标签/名字）过滤"""
    folder = _learned_skills_dir()
    items: list[dict[str, Any]] = []
    q = (query or '').lower().strip()
    for f in sorted(folder.glob('*.md')):
        try:
            data = _parse_learned_skill(f)
        except Exception:
            continue
        # 不返回 steps（太长）
        steps_count = len(data.get('_steps', []))
        info = {k: v for k, v in data.items() if k != '_steps'}
        info['steps_count'] = steps_count
        if not q:
            items.append(info)
        else:
            haystack = json.dumps(info, ensure_ascii=False).lower()
            if q in haystack:
                items.append(info)
    return {'count': len(items), 'skills': items}


async def skill_get_learned_skill(name: str, **_: Any) -> dict[str, Any]:
    """读取一个 Skill 完整内容（包含 steps）"""
    if not name:
        return {'error': 'name 必填'}
    p = _learned_skills_dir() / f'{name}.md'
    if not p.exists():
        return {'error': f'Skill {name} 不存在'}
    try:
        data = _parse_learned_skill(p)
        return data
    except Exception as e:
        return {'error': f'读取失败：{e}'}


async def skill_run_learned_skill(
    name: str,
    overrides: dict[str, dict[str, Any]] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """按顺序执行一个学过的 Skill 的所有步骤。
    
    overrides: 可选，按 step_index 覆盖参数。例如 {0: {url: '...'}} 把第 1 步的 url 换掉。
    """
    if not name:
        return {'error': 'name 必填'}
    p = _learned_skills_dir() / f'{name}.md'
    if not p.exists():
        return {'error': f'Skill {name} 不存在'}
    try:
        data = _parse_learned_skill(p)
        steps = data.get('_steps', []) or []
        front = {k: v for k, v in data.items() if not k.startswith('_')}
    except Exception as e:
        return {'error': f'解析失败：{e}'}

    overrides = overrides or {}
    results: list[dict[str, Any]] = []
    failed_at = None
    success = True
    for i, s in enumerate(steps):
        tool = s.get('tool')
        args = dict(s.get('args') or {})
        if str(i) in overrides:
            args.update(overrides[str(i)])
        elif i in overrides:
            args.update(overrides[i])
        try:
            r = await execute_skill(tool, args)
        except Exception as e:
            r = {'error': f'execute_skill 异常：{e}'}
        results.append({'step': i, 'tool': tool, 'result': r})
        if isinstance(r, dict) and r.get('error'):
            success = False
            failed_at = i
            break

    # 更新使用统计
    try:
        front['usage_count'] = int(front.get('usage_count', 0)) + 1
        if success:
            front['success_count'] = int(front.get('success_count', 0)) + 1
        front['last_used'] = datetime.now().isoformat(timespec='seconds')
        # 重新写入文件
        body_text = p.read_text(encoding='utf-8')
        if body_text.startswith('---'):
            end = body_text.find('---', 3)
            if end > 0:
                new_text = (
                    '---\n'
                    + json.dumps(front, ensure_ascii=False, indent=2)
                    + '\n---'
                    + body_text[end + 3:]
                )
                p.write_text(new_text, encoding='utf-8')
    except Exception:
        pass

    return {
        'success': success,
        'name': name,
        'executed_steps': len(results),
        'total_steps': len(steps),
        'failed_at_step': failed_at,
        'results': results,
    }


async def skill_delete_learned_skill(name: str, **_: Any) -> dict[str, Any]:
    """删除一个学过的 Skill"""
    if not name:
        return {'error': 'name 必填'}
    p = _learned_skills_dir() / f'{name}.md'
    if not p.exists():
        return {'error': f'Skill {name} 不存在'}
    p.unlink()
    return {'success': True, 'deleted': name}


# =============================================================================
# D. 教训 (Lessons) - 犯过的错记下来，下次自动 recall 不再重犯
# 对应 Hermes Agent 的 "Soul" 概念
# =============================================================================

async def skill_record_lesson(
    mistake: str,
    correct_approach: str,
    context: str = '',
    tags: list[str] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """记录一条"教训"——某次犯了什么错，正确做法是什么。
    
    AI 在每次新对话开始时会自动 recall_lessons 把所有教训加载到系统提示词，
    避免再次犯同样的错。
    """
    if not mistake or not correct_approach:
        return {'error': 'mistake 和 correct_approach 都必填'}
    items = _read_json(_lessons_file(), [])
    if not isinstance(items, list):
        items = []
    entry = {
        'id': uuid.uuid4().hex[:10],
        'mistake': mistake.strip(),
        'correct_approach': correct_approach.strip(),
        'context': context.strip() if context else '',
        'tags': tags or [],
        'recorded_at': datetime.now().isoformat(timespec='seconds'),
        'recall_count': 0,
    }
    items.append(entry)
    if len(items) > 200:
        items = items[-200:]
    _write_json(_lessons_file(), items)
    return {'success': True, 'lesson_id': entry['id'], 'total_lessons': len(items)}


async def skill_recall_lessons(query: str = '', limit: int = 20, **_: Any) -> dict[str, Any]:
    """查询教训库"""
    items = _read_json(_lessons_file(), [])
    if not isinstance(items, list):
        return {'lessons': [], 'count': 0}
    q = (query or '').lower().strip()
    if q:
        items = [
            i for i in items
            if q in (i.get('mistake', '') + i.get('correct_approach', '') + i.get('context', '')).lower()
            or q in ' '.join(i.get('tags', [])).lower()
        ]
    items = items[-limit:]
    return {'count': len(items), 'lessons': items}


async def skill_forget_lesson(lesson_id: str, **_: Any) -> dict[str, Any]:
    """删除一条教训"""
    items = _read_json(_lessons_file(), [])
    if not isinstance(items, list):
        return {'error': '教训库为空'}
    new_items = [i for i in items if i.get('id') != lesson_id]
    if len(new_items) == len(items):
        return {'error': f'找不到 lesson_id={lesson_id}'}
    _write_json(_lessons_file(), new_items)
    return {'success': True, 'remaining': len(new_items)}


# =============================================================================
# E. 用户画像 (User Profile) - 用得越久越懂用户
# 对应 Hermes Agent 的 user.md
# =============================================================================

async def skill_update_user_profile(
    field: str,
    value: Any,
    **_: Any,
) -> dict[str, Any]:
    """更新用户画像中的某个字段。常见字段：
    - name: 用户名/称呼
    - role: 用户角色（开发者 / 设计师 / 学生 等）
    - preferred_language: 偏好的语言（默认中文）
    - communication_style: 沟通风格（简洁 / 详细 / 严肃 等）
    - common_tasks: 常做的任务类型 [list]
    - never_do: 用户明确不希望 AI 做的事 [list]
    - api_keys_named: 用户提到过的 API Key 别名（不存值，只存名字）[list]
    - timezone: 时区
    - working_hours: 工作时间段
    - tools_in_use: 常用工具/库 [list]
    """
    if not field:
        return {'error': 'field 必填'}
    profile = _read_json(_user_profile_file(), {})
    if not isinstance(profile, dict):
        profile = {}
    # 数组类字段：append 而不是覆盖
    array_fields = {'common_tasks', 'never_do', 'api_keys_named', 'tools_in_use'}
    if field in array_fields:
        existing = profile.get(field, []) or []
        if not isinstance(existing, list):
            existing = []
        if isinstance(value, list):
            for v in value:
                if v not in existing:
                    existing.append(v)
        else:
            if value not in existing:
                existing.append(value)
        profile[field] = existing
    else:
        profile[field] = value
    profile['_updated_at'] = datetime.now().isoformat(timespec='seconds')
    _write_json(_user_profile_file(), profile)
    return {'success': True, 'field': field, 'profile_keys': list(profile.keys())}


async def skill_get_user_profile(**_: Any) -> dict[str, Any]:
    """读取完整用户画像"""
    return _read_json(_user_profile_file(), {})


async def skill_clear_user_profile(**_: Any) -> dict[str, Any]:
    """清空用户画像（敏感信息清理用）"""
    p = _user_profile_file()
    if p.exists():
        p.unlink()
    return {'success': True, 'cleared': True}


# =============================================================================
# F. 教训自动 recall - 给系统提示词补充材料
# =============================================================================

def get_lessons_summary_for_prompt(limit: int = 30) -> str:
    """加载所有教训为系统提示词补充段（在每次对话开始时由 service 自动调用）"""
    items = _read_json(_lessons_file(), [])
    if not isinstance(items, list) or not items:
        return ''
    items = items[-limit:]
    lines = ['# 历史教训（这些错误绝对不能再犯）', '']
    for it in items:
        mistake = it.get('mistake', '')
        correct = it.get('correct_approach', '')
        ctx = it.get('context', '')
        if mistake and correct:
            lines.append(f"- 不要：{mistake}")
            lines.append(f"  正确：{correct}")
            if ctx:
                lines.append(f"  场景：{ctx}")
            lines.append('')
    return '\n'.join(lines)


def get_user_profile_summary_for_prompt() -> str:
    """加载用户画像为系统提示词补充段"""
    profile = _read_json(_user_profile_file(), {})
    if not isinstance(profile, dict) or not profile:
        return ''
    # 过滤内部字段
    visible = {k: v for k, v in profile.items() if not k.startswith('_')}
    if not visible:
        return ''
    lines = ['# 用户画像（你已经认识这位用户）', '']
    for k, v in visible.items():
        if isinstance(v, list):
            if v:
                lines.append(f'- **{k}**：{", ".join(str(x) for x in v)}')
        else:
            lines.append(f'- **{k}**：{v}')
    lines.append('')
    return '\n'.join(lines)


def get_learned_skills_summary_for_prompt(limit: int = 20) -> str:
    """加载所有学过 skill 的概要（让 AI 知道有哪些 skill 可调用）"""
    folder = _learned_skills_dir()
    if not folder.exists():
        return ''
    items: list[dict] = []
    for f in sorted(folder.glob('*.md')):
        try:
            data = _parse_learned_skill(f)
            items.append({
                'name': data.get('name'),
                'description': data.get('description'),
                'when_to_use': data.get('when_to_use'),
                'usage_count': data.get('usage_count', 0),
            })
        except Exception:
            continue
    if not items:
        return ''
    items.sort(key=lambda x: -int(x.get('usage_count', 0) or 0))
    items = items[:limit]
    lines = ['# 已学习的 Skills（你之前自己创建过的可重用流程）', '']
    for it in items:
        lines.append(f"- **{it['name']}**：{it.get('description', '')}")
        if it.get('when_to_use'):
            lines.append(f"  - 何时用：{it['when_to_use']}")
        lines.append(f"  - 调用方式：run_learned_skill(name='{it['name']}')")
    lines.append('')
    return '\n'.join(lines)


# =============================================================================
# 注册所有新 skill
# =============================================================================

def _register_v3() -> None:
    # A. 系统控制
    registry.register(Skill(
        name='set_screen_brightness',
        description='设置笔记本屏幕亮度（0-100，台式机不支持）。例如：percent=80',
        parameters={
            'type': 'object',
            'properties': {'percent': {'type': 'integer', 'minimum': 0, 'maximum': 100}},
            'required': ['percent'],
        },
        handler=skill_set_screen_brightness,
    ))
    registry.register(Skill(
        name='get_screen_brightness',
        description='读取当前屏幕亮度（0-100）',
        parameters={'type': 'object', 'properties': {}},
        handler=skill_get_screen_brightness,
    ))
    registry.register(Skill(
        name='set_system_volume',
        description='设置系统音量（0-100）。需要 pycaw（pip install pycaw comtypes）',
        parameters={
            'type': 'object',
            'properties': {'percent': {'type': 'integer', 'minimum': 0, 'maximum': 100}},
            'required': ['percent'],
        },
        handler=skill_set_system_volume,
    ))
    registry.register(Skill(
        name='get_system_volume',
        description='读取系统音量（0-100）和静音状态',
        parameters={'type': 'object', 'properties': {}},
        handler=skill_get_system_volume,
    ))
    registry.register(Skill(
        name='set_volume_mute',
        description='系统静音/取消静音',
        parameters={
            'type': 'object',
            'properties': {'muted': {'type': 'boolean', 'default': True}},
        },
        handler=skill_set_volume_mute,
    ))
    registry.register(Skill(
        name='launch_application',
        description=(
            '启动一个应用（QQ / WeChat / chrome / notepad / cmd / explorer 等）。'
            '可以传应用名（系统会找）或绝对路径。例如启动 QQ：launch_application(name_or_path="QQ")'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'name_or_path': {'type': 'string'},
                'args': {'type': 'array', 'items': {'type': 'string'}},
            },
            'required': ['name_or_path'],
        },
        handler=skill_launch_application,
    ))
    registry.register(Skill(
        name='close_application',
        description='通过进程名关闭应用（force=True 会强制结束未保存数据）',
        parameters={
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'description': '进程名，例如 QQ.exe / chrome.exe'},
                'force': {'type': 'boolean', 'default': False},
            },
            'required': ['name'],
        },
        handler=skill_close_application,
    ))
    registry.register(Skill(
        name='lock_screen',
        description='锁屏（Win+L 等效）',
        parameters={'type': 'object', 'properties': {}},
        handler=skill_lock_screen,
    ))
    registry.register(Skill(
        name='shutdown_computer',
        description=(
            '关机/重启/取消。默认 60 秒倒计时给用户反悔机会。'
            '高危操作！必须先和用户确认。'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'seconds': {'type': 'integer', 'default': 60},
                'cancel': {'type': 'boolean', 'default': False},
                'restart': {'type': 'boolean', 'default': False},
            },
        },
        handler=skill_shutdown_computer,
        requires_approval=True,
    ))
    registry.register(Skill(
        name='open_url',
        description='用默认浏览器打开 URL',
        parameters={
            'type': 'object',
            'properties': {'url': {'type': 'string'}},
            'required': ['url'],
        },
        handler=skill_open_url,
    ))
    registry.register(Skill(
        name='send_notification',
        description='系统右下角弹出 Toast 通知（需要 win10toast 或退到 msg 命令）',
        parameters={
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'message': {'type': 'string'},
                'duration': {'type': 'integer', 'default': 5},
            },
            'required': ['title', 'message'],
        },
        handler=skill_send_notification,
    ))

    # B. 一次性延时
    registry.register(Skill(
        name='schedule_one_shot',
        description=(
            'N 秒后执行某个 skill 一次（一次性延时任务，不是周期性）。'
            '示例：30 秒后把屏幕亮度调到 100% → '
            'schedule_one_shot(delay_seconds=30, skill_name="set_screen_brightness", skill_args={"percent": 100})。'
            '返回 token，可用 cancel_one_shot 取消。'
            '【真正周期性的定时任务请用 create_scheduled_task】'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'delay_seconds': {'type': 'integer'},
                'skill_name': {'type': 'string'},
                'skill_args': {'type': 'object'},
                'note': {'type': 'string'},
            },
            'required': ['delay_seconds', 'skill_name'],
        },
        handler=skill_schedule_one_shot,
    ))
    registry.register(Skill(
        name='cancel_one_shot',
        description='取消一个待执行的延时任务',
        parameters={
            'type': 'object',
            'properties': {'token': {'type': 'string'}},
            'required': ['token'],
        },
        handler=skill_cancel_one_shot,
    ))
    registry.register(Skill(
        name='list_pending_tasks',
        description='列出所有待执行的延时任务',
        parameters={'type': 'object', 'properties': {}},
        handler=skill_list_pending_tasks,
    ))

    # C. 自学习
    registry.register(Skill(
        name='save_learned_skill',
        description=(
            '把 AI 在对话中摸索出的"工具组合"保存为新 Skill（学到了不再重新摸索）。'
            '当 AI 完成一个有价值的复杂流程后，主动建议用户「我把这个流程记下来吧，以后一句话就能复用」，'
            '用户同意后调这个工具。Skill 会以 markdown + YAML 格式保存到 backend/data/ai_assistant/learned_skills/。'
            '**这就是 Hermes Agent 同款的自创建 skill 能力**。'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'description': '英文小写下划线，例如 daily_news_collect'},
                'description': {'type': 'string'},
                'when_to_use': {'type': 'string', 'description': '什么场景下应该用这个 skill'},
                'steps': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'tool': {'type': 'string'},
                            'args': {'type': 'object'},
                            'purpose': {'type': 'string'},
                        },
                    },
                },
                'tags': {'type': 'array', 'items': {'type': 'string'}},
            },
            'required': ['name', 'description', 'when_to_use', 'steps'],
        },
        handler=skill_save_learned_skill,
    ))
    registry.register(Skill(
        name='list_learned_skills',
        description='列出所有 AI 学过的 Skill（按使用次数排序，最常用的在前）',
        parameters={
            'type': 'object',
            'properties': {'query': {'type': 'string'}},
        },
        handler=skill_list_learned_skills,
    ))
    registry.register(Skill(
        name='get_learned_skill',
        description='读取一个 Skill 的完整内容（包含全部 steps）',
        parameters={
            'type': 'object',
            'properties': {'name': {'type': 'string'}},
            'required': ['name'],
        },
        handler=skill_get_learned_skill,
    ))
    registry.register(Skill(
        name='run_learned_skill',
        description=(
            '按顺序执行一个学过的 Skill 的所有步骤。'
            'overrides 可选，按 step_index 覆盖参数。例如 {"0": {"url": "..."}}。'
            '调用后会自动更新使用统计。'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'overrides': {'type': 'object'},
            },
            'required': ['name'],
        },
        handler=skill_run_learned_skill,
    ))
    registry.register(Skill(
        name='delete_learned_skill',
        description='删除一个学过的 Skill',
        parameters={
            'type': 'object',
            'properties': {'name': {'type': 'string'}},
            'required': ['name'],
        },
        handler=skill_delete_learned_skill,
        requires_approval=True,
    ))

    # D. 教训
    registry.register(Skill(
        name='record_lesson',
        description=(
            '记录一条「教训」——某次犯了什么错，正确做法是什么。'
            'AI 应该在以下时机主动记录教训：'
            '① 用户纠正了你的某个做法 ② 工具调用失败但事后找到了正确方法 ③ 用户说「以后不要这样做」。'
            '每次新对话开始时这些教训会自动加载到系统提示词，避免重犯。'
            '**这就是 Hermes Agent 同款的"不再犯第二次错误"机制**。'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'mistake': {'type': 'string', 'description': '错误的做法'},
                'correct_approach': {'type': 'string', 'description': '正确做法'},
                'context': {'type': 'string', 'description': '场景描述（什么情况下容易犯）'},
                'tags': {'type': 'array', 'items': {'type': 'string'}},
            },
            'required': ['mistake', 'correct_approach'],
        },
        handler=skill_record_lesson,
    ))
    registry.register(Skill(
        name='recall_lessons',
        description='查询教训库（query 可空，返回最近的若干条）',
        parameters={
            'type': 'object',
            'properties': {
                'query': {'type': 'string'},
                'limit': {'type': 'integer', 'default': 20},
            },
        },
        handler=skill_recall_lessons,
    ))
    registry.register(Skill(
        name='forget_lesson',
        description='删除一条教训',
        parameters={
            'type': 'object',
            'properties': {'lesson_id': {'type': 'string'}},
            'required': ['lesson_id'],
        },
        handler=skill_forget_lesson,
    ))

    # E. 用户画像
    registry.register(Skill(
        name='update_user_profile',
        description=(
            '更新用户画像中的某个字段（用得越久越懂用户）。'
            '常见字段：name / role / preferred_language / communication_style / common_tasks / '
            'never_do / api_keys_named / timezone / working_hours / tools_in_use。'
            'AI 应在用户透露相关信息时主动调用——例如用户说"我是 Java 开发者"就 update(field="role", value="Java 开发者")。'
            '【绝对不要把 API Key 的真实值写进画像，只能写别名】。'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'field': {'type': 'string'},
                'value': {},
            },
            'required': ['field', 'value'],
        },
        handler=skill_update_user_profile,
    ))
    registry.register(Skill(
        name='get_user_profile',
        description='读取完整用户画像',
        parameters={'type': 'object', 'properties': {}},
        handler=skill_get_user_profile,
    ))
    registry.register(Skill(
        name='clear_user_profile',
        description='清空用户画像（敏感信息清理用）',
        parameters={'type': 'object', 'properties': {}},
        handler=skill_clear_user_profile,
        requires_approval=True,
    ))


_register_v3()
