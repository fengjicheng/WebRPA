"""
AI 助手新增 Skills v2（追加注册到 ai_assistant_skills.registry）

设计理念：让 AI 在搭建工作流前/中/后都更聪明——
  • 搭建前：检查依赖（Excel 资源在不在/全局配置缺什么）
  • 搭建中：自动套用健壮性模板（重试/异常处理）
  • 搭建后：dry-run 模拟（0 秒验证变量流和参数完整性，不真跑外部副作用）
  • 排错时：结构化执行洞察（哪个节点输入输出是什么、为什么失败）
  • 桌面态：让 AI 真看见屏幕、剪贴板、活动窗口
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.services.ai_assistant_skills import registry, Skill, _get_data_folder
from app.services.ai_assistant_module_schemas import get_module_schema


# =============================================================================
# A. dry_run_workflow - 静态模拟执行
# =============================================================================

def _simulate_node_output(mtype: str, cfg: dict) -> dict[str, Any]:
    rv = cfg.get('resultVariable') or cfg.get('variableName')
    out: dict[str, Any] = {}
    if not rv:
        return out
    type_to_fake = {
        'open_page': '<page-handle>',
        'get_text': '<simulated-text>',
        'get_element_text': '<simulated-text>',
        'get_attribute': '<simulated-attr>',
        'get_url': 'https://example.com',
        'get_title': '<simulated-page-title>',
        'input_dialog': '<user-input>',
        'get_clipboard': '<clipboard-text>',
        'api_request': {'status': 200, 'body': '<simulated-api-response>'},
        'json_parse': {'items': []},
        'ai_chat': '<ai-response>',
        'calc_expr': 0,
        'math': 0,
        'string_concat': '<concat-string>',
        'string_replace': '<replaced-string>',
        'regex_extract': [],
        'list_files': [],
        'read_file': '<file-content>',
        'read_excel': [],
        'ocr': '<ocr-text>',
        'screenshot': '<screenshot-path>',
        'current_time': '2024-01-01 00:00:00',
        'random_number': 0,
        'uuid': '00000000-0000-0000-0000-000000000000',
    }
    fake = type_to_fake.get(mtype, f'<{mtype}-output>')
    out[rv] = fake
    return out


def _extract_var_refs(cfg: dict) -> set[str]:
    refs: set[str] = set()
    pattern = re.compile(r'\{\{?([a-zA-Z_][a-zA-Z0-9_]*)(?:\.[a-zA-Z0-9_\[\]]+)?\}?\}')
    for v in cfg.values():
        if isinstance(v, str):
            for m in pattern.findall(v):
                refs.add(m)
        elif isinstance(v, dict):
            refs.update(_extract_var_refs(v))
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    refs.update(_extract_var_refs(item))
                elif isinstance(item, str):
                    for m in pattern.findall(item):
                        refs.add(m)
    return refs


async def skill_dry_run_workflow(
    nodes: list[dict],
    edges: list[dict] | None = None,
    initial_vars: dict[str, Any] | None = None,
    **_: Any,
) -> dict[str, Any]:
    if not isinstance(nodes, list) or not nodes:
        return {'error': 'nodes 为空'}
    edges = edges or []

    by_id = {n['id']: n for n in nodes}
    in_degree = {n['id']: 0 for n in nodes}
    children: dict[str, list[str]] = {n['id']: [] for n in nodes}
    for e in edges:
        s, t = e.get('source'), e.get('target')
        if s in by_id and t in by_id:
            children[s].append(t)
            in_degree[t] = in_degree.get(t, 0) + 1

    queue = [nid for nid, d in in_degree.items() if d == 0]
    visited: list[str] = []
    in_deg = dict(in_degree)
    while queue:
        cur = queue.pop(0)
        visited.append(cur)
        for nxt in children[cur]:
            in_deg[nxt] -= 1
            if in_deg[nxt] == 0:
                queue.append(nxt)

    has_cycle = len(visited) < len(nodes)

    scope: dict[str, Any] = dict(initial_vars or {})
    builtin_vars = {'item', 'index', 'key', 'value', 'ai_response'}

    issues: list[dict[str, Any]] = []
    var_timeline: list[dict[str, Any]] = []
    simulated = 0

    for nid in visited:
        n = by_id[nid]
        mtype = n.get('type') or n.get('data', {}).get('moduleType')
        cfg = {k: v for k, v in (n.get('data') or {}).items() if k not in ('moduleType', 'label', 'name')}

        try:
            schema = get_module_schema(mtype) or {}
        except Exception:
            schema = {}
        required = schema.get('required', []) or []
        for req in required:
            val = cfg.get(req)
            if val is None or val == '' or val == []:
                issues.append({
                    'node_id': nid,
                    'module_type': mtype,
                    'level': 'error',
                    'kind': 'missing_required',
                    'field': req,
                    'message': f'必填字段 `{req}` 未填',
                })

        for ref in _extract_var_refs(cfg):
            if ref in scope or ref in builtin_vars:
                continue
            issues.append({
                'node_id': nid,
                'module_type': mtype,
                'level': 'warning',
                'kind': 'undefined_variable',
                'variable': ref,
                'message': f'引用了未定义的变量 `{ref}`（可能是上游节点尚未产生该变量）',
            })

        produced = _simulate_node_output(mtype, cfg)
        for k, v in produced.items():
            if k in scope:
                issues.append({
                    'node_id': nid,
                    'module_type': mtype,
                    'level': 'warning',
                    'kind': 'variable_overwrite',
                    'variable': k,
                    'message': f'变量 `{k}` 被覆盖（之前已存在）',
                })
            scope[k] = v
            var_timeline.append({
                'node_id': nid,
                'module_type': mtype,
                'produces': k,
            })
        simulated += 1

    if has_cycle:
        issues.append({
            'level': 'error',
            'kind': 'cycle',
            'message': '工作流里存在环（节点互相依赖形成循环），可能导致无限循环',
        })

    return {
        'valid': not any(i.get('level') == 'error' for i in issues),
        'simulated_count': simulated,
        'total_nodes': len(nodes),
        'issues': issues,
        'var_timeline': var_timeline,
        'final_scope_keys': sorted(scope.keys()),
        'tip': 'dry-run 通过不代表真跑也通过（外部 IO 可能失败），但 dry-run 失败一定真跑也会失败',
    }


# =============================================================================
# B. 运行时洞察
# =============================================================================

async def skill_get_execution_summary(workflow_id: str | None = None, **_: Any) -> dict[str, Any]:
    try:
        from app.api.workflows import execution_results
    except Exception as e:
        return {'error': f'无法访问执行结果：{e}'}

    target_id = workflow_id
    if not target_id:
        if not execution_results:
            return {'error': '还没有任何执行记录'}
        target_id = list(execution_results.keys())[-1]

    result = execution_results.get(target_id)
    if not result:
        return {'error': f'找不到 workflow_id={target_id} 的执行记录'}

    if hasattr(result, 'model_dump'):
        result = result.model_dump()
    elif hasattr(result, '__dict__'):
        result = dict(result.__dict__)

    nodes_log = result.get('node_results') or result.get('nodes') or []
    failed = [n for n in nodes_log if (n.get('status') or '').lower() in ('failed', 'error', 'fail')]

    return {
        'workflow_id': target_id,
        'status': result.get('status'),
        'started_at': result.get('started_at') or result.get('start_time'),
        'ended_at': result.get('ended_at') or result.get('end_time'),
        'total_nodes': len(nodes_log),
        'failed_count': len(failed),
        'first_error': (failed[0].get('error') or failed[0].get('message')) if failed else None,
        'first_failed_node': failed[0].get('node_id') if failed else None,
        'node_results': nodes_log,
    }


async def skill_find_failed_nodes_with_reason(workflow_id: str | None = None, **_: Any) -> dict[str, Any]:
    summary = await skill_get_execution_summary(workflow_id=workflow_id)
    if summary.get('error'):
        return summary

    failed: list[dict[str, Any]] = []
    for n in summary.get('node_results', []):
        status = (n.get('status') or '').lower()
        if status not in ('failed', 'error', 'fail'):
            continue
        err = (n.get('error') or n.get('message') or '').strip()
        suggestion = '查看错误详情，可能需要用 client_action(update_node_config) 修复对应字段'
        kind = 'unknown'
        low = err.lower()
        if 'selector' in low or 'no such element' in low or 'element not found' in low:
            kind = 'selector_not_found'
            suggestion = 'selector 选不到元素。先调 probe_page / suggest_selector 拿到真实 selector，再 update_node_config 替换'
        elif 'timeout' in low or '等待超时' in err:
            kind = 'timeout'
            suggestion = '超时。前置加一个 wait_element / wait_page_load，或把 timeout 调大'
        elif 'key' in low and ('not found' in low or 'missing' in low):
            kind = 'missing_key'
            suggestion = '字典/JSON 里某个 key 不存在。检查上一步产出结构（用 dry_run_workflow 看变量时间线）'
        elif '404' in err or 'not found' in low:
            kind = 'url_not_found'
            suggestion = 'URL 404。确认 URL 是否正确，或目标资源是否还在'
        elif '401' in err or '403' in err or 'unauthorized' in low:
            kind = 'auth_failed'
            suggestion = '认证失败。检查全局配置中的 API Key/Token/Cookie'
        elif 'encoding' in low or 'decode' in low:
            kind = 'encoding'
            suggestion = '编码错误。检查文件读写时的 encoding 字段（建议 utf-8）'
        elif 'no such file' in low or 'filenotfound' in low:
            kind = 'file_not_found'
            suggestion = '文件不存在。确认文件路径，或先创建/上传文件'
        failed.append({
            'node_id': n.get('node_id'),
            'module_type': n.get('module_type') or n.get('type'),
            'error': err,
            'kind': kind,
            'suggestion': suggestion,
        })

    return {
        'workflow_id': summary.get('workflow_id'),
        'failed_count': len(failed),
        'failures': failed,
    }


async def skill_get_node_io_snapshot(node_id: str, workflow_id: str | None = None, **_: Any) -> dict[str, Any]:
    summary = await skill_get_execution_summary(workflow_id=workflow_id)
    if summary.get('error'):
        return summary
    for n in summary.get('node_results', []):
        if n.get('node_id') == node_id:
            return {
                'node_id': node_id,
                'module_type': n.get('module_type') or n.get('type'),
                'status': n.get('status'),
                'duration_ms': n.get('duration_ms') or n.get('duration'),
                'input': n.get('input') or n.get('config') or n.get('params'),
                'output': n.get('output') or n.get('result'),
                'error': n.get('error') or n.get('message'),
            }
    return {'error': f'找不到节点 {node_id} 的执行快照（可能这个节点没跑到）'}


# =============================================================================
# E. 搭建前依赖预检
# =============================================================================

async def skill_check_workflow_dependencies(nodes: list[dict], **_: Any) -> dict[str, Any]:
    if not isinstance(nodes, list):
        return {'error': 'nodes 必须是数组'}

    missing: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    needs_ai = False
    needs_email = False
    needs_db = False
    needs_browser = False
    referenced_excels: list[tuple[str, str]] = []
    referenced_images: list[tuple[str, str]] = []
    referenced_custom_modules: list[tuple[str, str]] = []

    for n in nodes:
        mtype = n.get('type') or n.get('data', {}).get('moduleType')
        cfg = n.get('data') or {}
        nid = n.get('id')
        if not mtype:
            continue
        if mtype in ('ai_chat', 'ai_extract', 'ai_classify', 'ai_summarize', 'ai_translate'):
            needs_ai = True
        if mtype in ('send_email', 'read_email', 'delete_email'):
            needs_email = True
        if mtype in ('query_db', 'execute_sql', 'db_insert', 'db_update', 'db_delete'):
            needs_db = True
        if mtype in ('open_page', 'click_element', 'get_text', 'fill_input', 'wait_element', 'screenshot_browser'):
            needs_browser = True
        if mtype in ('read_excel', 'write_excel', 'loop_excel'):
            asset_id = cfg.get('assetId') or cfg.get('asset_id') or cfg.get('excelAssetId')
            if asset_id:
                referenced_excels.append((nid, asset_id))
        if mtype in ('image_match', 'image_click', 'find_image'):
            asset_id = cfg.get('imageAssetId') or cfg.get('templateAssetId')
            if asset_id:
                referenced_images.append((nid, asset_id))
        if mtype and (mtype.startswith('custom_') or mtype.startswith('cm_')):
            referenced_custom_modules.append((nid, mtype))

    try:
        cfg_file = _get_data_folder() / 'global_config.json'
        gconf: dict[str, Any] = {}
        if cfg_file.exists():
            try:
                gconf = json.loads(cfg_file.read_text(encoding='utf-8'))
            except Exception:
                gconf = {}
    except Exception:
        gconf = {}

    if needs_ai:
        ai_cfg = gconf.get('aiChat') or gconf.get('ai') or {}
        if not (ai_cfg.get('apiKey') or ai_cfg.get('api_key')):
            missing.append({
                'kind': 'missing_global_config',
                'section': 'aiChat',
                'field': 'apiKey',
                'message': '工作流用到 AI 节点，但全局配置里没有 AI API Key',
                'fix_hint': '提示用户去全局配置 → AI 对话标签页填 API Key',
            })

    if needs_email:
        email_cfg = gconf.get('email') or gconf.get('smtp') or {}
        if not (email_cfg.get('host') or email_cfg.get('smtpHost')):
            missing.append({
                'kind': 'missing_global_config',
                'section': 'email',
                'field': 'smtpHost',
                'message': '用到邮件节点，但 SMTP 配置缺失',
                'fix_hint': '全局配置 → 邮件标签页填 SMTP 服务器',
            })

    if needs_db:
        db_cfg = gconf.get('database') or {}
        if not db_cfg:
            warnings.append({
                'kind': 'missing_global_config',
                'section': 'database',
                'message': '用到数据库节点，但全局配置里没有数据库连接（也可能在节点里直接配）',
            })

    if referenced_excels:
        try:
            from app.api.data_assets import data_assets
            valid_ids = set(data_assets.keys())
            for nid, aid in referenced_excels:
                if aid not in valid_ids:
                    missing.append({
                        'kind': 'missing_excel_asset',
                        'node_id': nid,
                        'asset_id': aid,
                        'message': f'节点 {nid} 引用了 Excel 资源 {aid}，但该资源不存在',
                        'fix_hint': 'list_data_assets 看现有资源；upload_excel 让用户上传；或修正节点配置',
                    })
        except Exception:
            pass

    if referenced_images:
        try:
            from app.api.image_assets import image_assets
            valid_ids = set(image_assets.keys())
            for nid, aid in referenced_images:
                if aid not in valid_ids:
                    missing.append({
                        'kind': 'missing_image_asset',
                        'node_id': nid,
                        'asset_id': aid,
                        'message': f'节点 {nid} 引用了图像资源 {aid}，但该资源不存在',
                        'fix_hint': 'list_image_assets 看现有；upload_image 让用户上传',
                    })
        except Exception:
            pass

    if referenced_custom_modules:
        try:
            from app.api.custom_modules import custom_modules
            valid_ids = set(custom_modules.keys())
            for nid, mid in referenced_custom_modules:
                if mid not in valid_ids:
                    missing.append({
                        'kind': 'missing_custom_module',
                        'node_id': nid,
                        'module_id': mid,
                        'message': f'节点 {nid} 引用了自定义模块 {mid}，但该模块已被删除',
                        'fix_hint': 'list_custom_modules 看现有；replace_module_type 换成可用的',
                    })
        except Exception:
            pass

    return {
        'ok': not missing,
        'missing_count': len(missing),
        'warning_count': len(warnings),
        'missing': missing,
        'warnings': warnings,
        'tip': 'missing 项是工作流跑不起来的硬障碍，必须先解决；warnings 是建议项',
    }


# =============================================================================
# C. 健壮性自动套用
# =============================================================================

async def skill_suggest_robustness_patches(nodes: list[dict], **_: Any) -> dict[str, Any]:
    if not isinstance(nodes, list):
        return {'error': 'nodes 必须是数组'}

    NETWORK_TYPES = {
        'api_request', 'ai_chat', 'open_page', 'send_email', 'read_email',
        'query_db', 'execute_sql', 'fetch_html', 'download_file', 'upload_file',
    }
    WAIT_TYPES = {
        'wait_element', 'wait_page_load', 'click_element', 'fill_input',
        'get_text', 'find_image', 'image_match', 'phone_image_exists',
    }
    DESTRUCTIVE_TYPES = {
        'send_email', 'execute_sql', 'delete_file', 'delete_folder',
        'db_delete', 'db_update', 'db_insert', 'rename_file',
    }

    patches: list[dict[str, Any]] = []
    for n in nodes:
        mtype = n.get('type') or n.get('data', {}).get('moduleType')
        cfg = n.get('data') or {}
        nid = n.get('id')
        if not mtype or not nid:
            continue

        if mtype in NETWORK_TYPES:
            cur_retry = cfg.get('retryCount') or cfg.get('retry') or 0
            try:
                cur_retry_n = int(cur_retry or 0)
            except Exception:
                cur_retry_n = 0
            if cur_retry_n < 2:
                patches.append({
                    'node_id': nid,
                    'module_type': mtype,
                    'kind': 'add_retry',
                    'patch': {'retryCount': 3, 'retryInterval': 2},
                    'rationale': '网络/外部服务类节点容易抖动，加 3 次重试 + 2s 间隔显著提升成功率',
                    'fix_hint': f'client_action(update_node_config, node_id={nid}, config={{retryCount: 3, retryInterval: 2}})',
                })

        if mtype in WAIT_TYPES:
            cur_timeout = cfg.get('timeout') or cfg.get('waitTimeout') or 0
            try:
                cur_to_n = int(cur_timeout or 0)
            except Exception:
                cur_to_n = 0
            if cur_to_n <= 0:
                default_to = 10 if mtype in ('click_element', 'fill_input', 'get_text') else 30
                patches.append({
                    'node_id': nid,
                    'module_type': mtype,
                    'kind': 'add_timeout',
                    'patch': {'timeout': default_to},
                    'rationale': f'{mtype} 默认无限等。加上 {default_to}s 超时，避免页面挂掉时整个流程卡住',
                    'fix_hint': f'client_action(update_node_config, node_id={nid}, config={{timeout: {default_to}}})',
                })

        if mtype in DESTRUCTIVE_TYPES:
            patches.append({
                'node_id': nid,
                'module_type': mtype,
                'kind': 'wrap_in_try',
                'rationale': '这是不可逆操作，建议在外面包一层 try_catch 节点防止失败连累整个流程',
                'fix_hint': f'在节点 {nid} 前面加 try_catch 节点；catch 分支可加 print_log + send_notification 通知用户',
            })

    return {
        'patch_count': len(patches),
        'patches': patches,
        'tip': '调 bulk_update_nodes 一次性应用所有 add_retry/add_timeout patches；wrap_in_try 需要手动连线',
    }


async def skill_apply_robustness_to_node(
    node_id: str,
    add_retry: bool = True,
    add_timeout: bool = True,
    retry_count: int = 3,
    timeout_seconds: int = 30,
    **_: Any,
) -> dict[str, Any]:
    if not node_id:
        return {'error': 'node_id 必填'}
    patch: dict[str, Any] = {}
    if add_retry:
        patch['retryCount'] = max(1, int(retry_count))
        patch['retryInterval'] = 2
    if add_timeout:
        patch['timeout'] = max(1, int(timeout_seconds))
    return {
        'node_id': node_id,
        'patch': patch,
        'tip': f'用 client_action(update_node_config, node_id={node_id}, config={json.dumps(patch)}) 落实',
    }


# =============================================================================
# F. 全局查找
# =============================================================================

async def skill_find_nodes_referencing(text: str, nodes: list[dict], **_: Any) -> dict[str, Any]:
    if not text:
        return {'error': 'text 必填'}
    text_str = str(text)
    hits: list[dict[str, Any]] = []
    for n in nodes:
        cfg = n.get('data') or {}
        mtype = n.get('type') or cfg.get('moduleType')
        nid = n.get('id')
        for k, v in cfg.items():
            if k in ('moduleType', 'label', 'name'):
                continue
            try:
                sv = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
            except Exception:
                sv = str(v)
            if text_str in sv:
                hits.append({
                    'node_id': nid,
                    'module_type': mtype,
                    'field': k,
                    'value': v,
                })
    return {
        'search_text': text_str,
        'hit_count': len(hits),
        'hits': hits,
        'tip': '对每条 hit 调 update_node_config 改字段；改变量名时用 rename_variable',
    }


# =============================================================================
# D. 桌面/环境感知
# =============================================================================

async def skill_take_screenshot(save_to: str | None = None, **_: Any) -> dict[str, Any]:
    try:
        from PIL import ImageGrab
    except ImportError:
        return {'error': '未安装 Pillow，无法截屏。pip install Pillow'}
    try:
        img = ImageGrab.grab()
        if save_to:
            target = Path(save_to)
        else:
            target = _get_data_folder() / 'ai_screenshots'
            target.mkdir(parents=True, exist_ok=True)
            from datetime import datetime
            target = target / f"shot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(target))
        return {
            'success': True,
            'path': str(target),
            'size': list(img.size),
            'tip': '把这个路径传给 ai_extract / ocr 等节点可以让 AI 看图说话',
        }
    except Exception as e:
        return {'error': f'截屏失败：{e}'}


async def skill_get_clipboard_content(**_: Any) -> dict[str, Any]:
    try:
        import pyperclip  # type: ignore
        text = pyperclip.paste()
        return {'success': True, 'text': text or '', 'length': len(text or '')}
    except ImportError:
        try:
            import win32clipboard  # type: ignore
            win32clipboard.OpenClipboard()
            try:
                text = win32clipboard.GetClipboardData()
            finally:
                win32clipboard.CloseClipboard()
            return {'success': True, 'text': text or '', 'length': len(text or '')}
        except Exception as e:
            return {'error': f'剪贴板读取失败：{e}'}
    except Exception as e:
        return {'error': f'剪贴板读取失败：{e}'}


async def skill_list_open_windows(**_: Any) -> dict[str, Any]:
    try:
        import win32gui  # type: ignore
    except ImportError:
        return {'error': '需要 pywin32：pip install pywin32'}
    windows: list[dict[str, Any]] = []
    fg = None
    try:
        fg = win32gui.GetForegroundWindow()
    except Exception:
        pass

    def _enum(hwnd, _):
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return
            cls = win32gui.GetClassName(hwnd) or ''
            windows.append({
                'hwnd': hwnd,
                'title': title,
                'class': cls,
                'is_foreground': (hwnd == fg),
            })
        except Exception:
            pass

    win32gui.EnumWindows(_enum, None)
    return {'count': len(windows), 'windows': windows}


async def skill_get_active_window_title(**_: Any) -> dict[str, Any]:
    try:
        import win32gui  # type: ignore
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd) if hwnd else ''
        cls = win32gui.GetClassName(hwnd) if hwnd else ''
        return {'hwnd': hwnd, 'title': title, 'class': cls}
    except Exception as e:
        return {'error': f'获取活动窗口失败：{e}'}


# =============================================================================
# 注册所有新 skill
# =============================================================================

def _register_v2() -> None:
    registry.register(Skill(
        name='dry_run_workflow',
        description=(
            '【强烈推荐】静态模拟一遍工作流执行（0 秒，不真跑外部 IO）。'
            '按拓扑顺序遍历节点，每步检查 schema.required 是否齐 + 引用的变量是否在前置 scope 中存在 + 模拟产出新变量供后续节点使用。'
            '返回 issues（潜在问题）+ var_timeline（变量产生时间线）。'
            '搭建完成后必跑——比 run_workflow 真跑快得多，能立刻发现变量名拼错/必填字段漏填/引用了不存在的变量等问题。'
            '用法：dry_run_workflow(nodes=[...], edges=[...])，nodes/edges 来自 client_action(get_workflow_detail)'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'nodes': {'type': 'array', 'items': {'type': 'object'}},
                'edges': {'type': 'array', 'items': {'type': 'object'}},
                'initial_vars': {'type': 'object', 'description': '可选，预设的初始变量'},
            },
            'required': ['nodes'],
        },
        handler=skill_dry_run_workflow,
    ))

    registry.register(Skill(
        name='get_execution_summary',
        description=(
            '获取最近一次（或指定 workflow_id）执行的结构化摘要：状态、起止时间、节点数、失败数、第一个失败节点 + 错误。'
            '比 get_recent_logs 更结构化，AI 一眼能看出哪里挂了。'
        ),
        parameters={
            'type': 'object',
            'properties': {'workflow_id': {'type': 'string', 'description': '可选，不传取最近一次'}},
        },
        handler=skill_get_execution_summary,
    ))

    registry.register(Skill(
        name='find_failed_nodes_with_reason',
        description=(
            '找出最近一次执行中所有失败的节点，并自动归类错误类型（selector_not_found / timeout / auth_failed / file_not_found 等）'
            '+ 给每条失败一个具体的修复建议。比让 AI 自己读日志更直接。'
        ),
        parameters={
            'type': 'object',
            'properties': {'workflow_id': {'type': 'string'}},
        },
        handler=skill_find_failed_nodes_with_reason,
    ))

    registry.register(Skill(
        name='get_node_io_snapshot',
        description=(
            '读取某个节点最近一次执行的输入参数和输出值。让 AI 真正能打开节点的盒子看里面发生了什么。'
            '排错神器：比如 ai_chat 输出不对，先看 input（提示词是什么）和 output（AI 真返回了啥）。'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'node_id': {'type': 'string'},
                'workflow_id': {'type': 'string'},
            },
            'required': ['node_id'],
        },
        handler=skill_get_node_io_snapshot,
    ))

    registry.register(Skill(
        name='check_workflow_dependencies',
        description=(
            '检查工作流的环境依赖是否齐全。'
            '看 AI 节点对应的全局配置是否填了、邮件 SMTP 是否配了、引用的 Excel/图像资源是否存在、自定义模块是否还在。'
            '搭建后必跑——避免搭好一看跑不通才发现 API Key 没配。'
        ),
        parameters={
            'type': 'object',
            'properties': {'nodes': {'type': 'array', 'items': {'type': 'object'}}},
            'required': ['nodes'],
        },
        handler=skill_check_workflow_dependencies,
    ))

    registry.register(Skill(
        name='suggest_robustness_patches',
        description=(
            '扫描画布，给容易失败的节点（网络/等待/不可逆操作）建议加重试/超时/异常处理。'
            '返回 patches 数组，AI 可直接 bulk_update_nodes 应用。'
            '用户要健壮工作流时必跑。'
        ),
        parameters={
            'type': 'object',
            'properties': {'nodes': {'type': 'array', 'items': {'type': 'object'}}},
            'required': ['nodes'],
        },
        handler=skill_suggest_robustness_patches,
    ))

    registry.register(Skill(
        name='apply_robustness_to_node',
        description='给一个节点生成加重试+超时的 patch（AI 拿到后用 client_action update_node_config 应用）',
        parameters={
            'type': 'object',
            'properties': {
                'node_id': {'type': 'string'},
                'add_retry': {'type': 'boolean', 'default': True},
                'add_timeout': {'type': 'boolean', 'default': True},
                'retry_count': {'type': 'integer', 'default': 3},
                'timeout_seconds': {'type': 'integer', 'default': 30},
            },
            'required': ['node_id'],
        },
        handler=skill_apply_robustness_to_node,
    ))

    registry.register(Skill(
        name='find_nodes_referencing',
        description=(
            '在所有节点的 config 字段里搜某段文本（变量名/URL/选择器/文件路径都行），'
            '返回所有用到了该文本的节点 + 哪个字段。'
            '改变量名/URL/选择器时必跑，避免漏改导致前后矛盾。'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'text': {'type': 'string'},
                'nodes': {'type': 'array', 'items': {'type': 'object'}},
            },
            'required': ['text', 'nodes'],
        },
        handler=skill_find_nodes_referencing,
    ))

    registry.register(Skill(
        name='take_screenshot',
        description='截一张当前主屏的截图，保存到本地文件，返回路径。可以再传给 ai_extract/ocr 让 AI 看图',
        parameters={
            'type': 'object',
            'properties': {'save_to': {'type': 'string', 'description': '可选保存路径'}},
        },
        handler=skill_take_screenshot,
    ))

    registry.register(Skill(
        name='get_clipboard_content',
        description='读取系统剪贴板的文本内容',
        parameters={'type': 'object', 'properties': {}},
        handler=skill_get_clipboard_content,
    ))

    registry.register(Skill(
        name='list_open_windows',
        description='列出当前所有可见的桌面窗口（标题/类名/是否前台），用于桌面自动化场景的全局观察',
        parameters={'type': 'object', 'properties': {}},
        handler=skill_list_open_windows,
    ))

    registry.register(Skill(
        name='get_active_window_title',
        description='当前活动（前台）窗口的标题和类名',
        parameters={'type': 'object', 'properties': {}},
        handler=skill_get_active_window_title,
    ))


_register_v2()


# =============================================================================
# 工作流自愈：一次性诊断 + 生成可执行的修复计划（配合知识库中的"自愈循环协议"）
# =============================================================================

async def skill_auto_heal_workflow(workflow_id: str | None = None, **_: Any) -> dict[str, Any]:
    """聚合最近一次执行的失败诊断，并为每个失败节点生成"可直接执行的修复动作清单"。

    返回结构（AI 拿到后按 fix_actions 逐条执行，再重跑）：
    {
      healthy: bool,            # True 表示没有失败，无需修复
      failed_count: int,
      attempts_hint: "最多自动重试 3 轮",
      fixes: [
        { node_id, module_type, error, kind, suggestion,
          required_fields: [...],        # 该模块必填字段（来自 schema）
          fix_actions: [ "具体该做什么" ] }
      ]
    }
    """
    diag = await skill_find_failed_nodes_with_reason(workflow_id=workflow_id)
    if diag.get('error'):
        return diag
    failures = diag.get('failures', []) or []
    if not failures:
        return {
            'healthy': True,
            'failed_count': 0,
            'message': '最近一次执行没有失败节点，无需修复。',
        }

    fixes: list[dict[str, Any]] = []
    for f in failures:
        mtype = f.get('module_type') or ''
        kind = f.get('kind') or 'unknown'
        schema = get_module_schema(mtype) or {}
        required = schema.get('required', []) if isinstance(schema, dict) else []
        actions: list[str] = []
        if kind == 'selector_not_found':
            actions.append("调 probe_page(url=该页面) 或 suggest_selector(target_description=...) 拿到真实 selector")
            actions.append(f"client_action(update_node_config, node_id={f.get('node_id')}, config={{'selector': '<真实selector>'}})")
        elif kind == 'timeout':
            actions.append(f"client_action(update_node_config, node_id={f.get('node_id')}, config={{'timeout': 60}})，或在该节点前插入 wait_element/wait_page_load")
            actions.append(f"或 apply_robustness_to_node(node_id={f.get('node_id')}) 加重试+超时后用 update_node_config 应用")
        elif kind == 'auth_failed':
            actions.append("提醒用户去全局配置补 API Key/Token/Cookie；或检查节点里的密钥字段")
        elif kind == 'file_not_found':
            actions.append("确认文件路径是否正确；必要时先创建/上传文件，再 update_node_config 修正路径字段")
        elif kind == 'url_not_found':
            actions.append("核对 URL 是否正确/资源是否还在；用 fetch_page_html 或 http_get 验证可达性")
        elif kind == 'missing_key':
            actions.append("用 get_node_io_snapshot 看上一步真实产出结构，修正取值路径（如 {data.items} → {data.list}）")
        elif kind == 'encoding':
            actions.append(f"client_action(update_node_config, node_id={f.get('node_id')}, config={{'encoding': 'utf-8'}})")
        else:
            actions.append(f"用 get_node_io_snapshot(node_id={f.get('node_id')}) 看输入输出定位原因，再针对性 update_node_config")
        if required:
            actions.append(f"确认必填字段已填：{', '.join(required)}（可 get_module_schema 看默认值）")
        fixes.append({
            'node_id': f.get('node_id'),
            'module_type': mtype,
            'error': f.get('error'),
            'kind': kind,
            'suggestion': f.get('suggestion'),
            'required_fields': required,
            'fix_actions': actions,
        })

    return {
        'healthy': False,
        'failed_count': len(fixes),
        'attempts_hint': '按 fix_actions 逐条修复后重跑；最多自动重试 3 轮，仍失败再向用户报告。',
        'fixes': fixes,
    }


registry.register(Skill(
    name='auto_heal_workflow',
    description=(
        '【工作流自愈】聚合最近一次运行的失败诊断，为每个失败节点生成"可直接执行的修复动作清单"'
        '（含 selector 重探、超时/重试、必填字段补全、取值路径修正等）。'
        '运行工作流失败后调用本技能拿到修复计划，逐条执行后重跑——这是自愈循环的核心。'
    ),
    parameters={
        'type': 'object',
        'properties': {
            'workflow_id': {'type': 'string', 'description': '可选，默认用最近一次执行'},
        },
    },
    handler=skill_auto_heal_workflow,
))
