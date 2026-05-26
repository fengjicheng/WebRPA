"""WebRPA 桌面自动化 - 影刀级增强模块

新增能力（对标影刀 RPA 桌面自动化）：
1. desktop_find_control_smart   智能控件查找(通配符/模糊/多属性组合/评分挑最稳)
2. desktop_extract_table        批量列表/表格抓取(影刀 DataExtraction Wizard 同款)
3. desktop_get_app_state        全应用状态快照(让 AI 一眼看清应用 UI 结构)
4. desktop_query_with_xpath     XPath 风格查询(支持 //Button[@name='登录'])
5. desktop_select_text          双击选中/Ctrl+A 全选并复制文字
6. desktop_get_focused_control  拿到当前焦点控件(动态分析活动元素)
7. desktop_assert_control       断言控件状态(测试场景必备)
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    register_executor,
)
from .type_utils import to_int, to_float


# =====================================================================
# 工具：通配符 / 模糊 匹配
# =====================================================================

def _wildcard_match(pattern: str, text: str, ignore_case: bool = True) -> bool:
    """支持 * ? 的通配符匹配。pattern='*登录*' 匹配 '请登录'"""
    if pattern is None or text is None:
        return False
    if ignore_case:
        pattern = pattern.lower()
        text = text.lower()
    if '*' not in pattern and '?' not in pattern:
        return pattern == text
    # 转换为正则
    regex = re.escape(pattern).replace(r'\*', '.*').replace(r'\?', '.')
    return bool(re.fullmatch(regex, text))


def _fuzzy_score(query: str, text: str) -> float:
    """计算模糊相似度 0~1。用 Jaccard + 包含 + 编辑距离的折中算法"""
    if not query or not text:
        return 0.0
    q = query.lower().strip()
    t = text.lower().strip()
    if q == t:
        return 1.0
    if q in t or t in q:
        return 0.85
    # Jaccard 字符集
    qs = set(q)
    ts = set(t)
    inter = qs & ts
    union = qs | ts
    if not union:
        return 0.0
    jaccard = len(inter) / len(union)
    # 长度相近度
    len_ratio = min(len(q), len(t)) / max(len(q), len(t))
    return jaccard * 0.6 + len_ratio * 0.4


# =====================================================================
# 1. 智能控件查找(通配符 + 模糊 + 多属性 + 评分)
# =====================================================================

@register_executor
class DesktopFindControlSmartExecutor(ModuleExecutor):
    """智能控件查找:支持通配符、模糊匹配、多属性组合,自动选最稳定的匹配项"""

    @property
    def module_type(self) -> str:
        return "desktop_find_control_smart"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        try:
            import uiautomation as auto

            app_variable = config.get("appVariable", "desktop_app")
            window_handle = context.get_variable(app_variable)
            if isinstance(window_handle, dict):
                handle = window_handle.get("handle")
            else:
                handle = window_handle
            if not handle:
                return ModuleResult(success=False, error=f"未找到窗口句柄(变量 {app_variable})")
            window = auto.ControlFromHandle(int(handle))
            if not window or not window.Exists(0, 0):
                return ModuleResult(success=False, error="窗口已关闭")

            # 多个匹配条件(任一满足即可，影刀风格的"灵活定位")
            name_pattern = context.resolve_value(config.get("namePattern", ""))      # 支持 * ?
            class_pattern = context.resolve_value(config.get("classPattern", ""))
            automation_id = context.resolve_value(config.get("automationId", ""))
            control_type = context.resolve_value(config.get("controlType", ""))
            text_contains = context.resolve_value(config.get("textContains", ""))    # name 包含此文字
            fuzzy_match = bool(config.get("fuzzyMatch", False))                       # 是否启用模糊
            fuzzy_threshold = float(config.get("fuzzyThreshold", 0.7))
            search_depth = to_int(config.get("searchDepth", 15), 15, context)
            timeout = to_int(config.get("timeout", 5), 5, context)
            return_all = bool(config.get("returnAll", False))                         # 返回所有匹配项
            save_to_variable = config.get("saveToVariable", "desktop_control")

            start = time.time()
            best_candidates: list[dict] = []

            while time.time() - start < timeout:
                # 收集所有符合条件的候选
                best_candidates.clear()

                def _walk(ctrl, depth):
                    if depth > search_depth:
                        return
                    try:
                        nm = ctrl.Name or ''
                        cn = ctrl.ClassName or ''
                        aid = ctrl.AutomationId or ''
                        ct = ctrl.ControlTypeName or ''

                        # 评分 - 每个匹配条件加分,越多越稳
                        score = 0.0
                        match_reasons: list[str] = []

                        if name_pattern:
                            if _wildcard_match(name_pattern, nm):
                                score += 1.0
                                match_reasons.append(f"name 匹配 {name_pattern}")
                            elif fuzzy_match:
                                fs = _fuzzy_score(name_pattern, nm)
                                if fs >= fuzzy_threshold:
                                    score += fs
                                    match_reasons.append(f"name 模糊匹配 {nm} (相似度 {fs:.2f})")
                                else:
                                    return  # name 必须满足
                            else:
                                return

                        if text_contains and text_contains.lower() not in nm.lower():
                            return
                        if text_contains:
                            score += 0.6
                            match_reasons.append(f"name 包含 {text_contains}")

                        if class_pattern and not _wildcard_match(class_pattern, cn):
                            return
                        if class_pattern:
                            score += 0.4
                            match_reasons.append(f"class 匹配 {class_pattern}")

                        if automation_id and aid != automation_id:
                            return
                        if automation_id:
                            score += 1.5  # automation_id 最稳定,加分高
                            match_reasons.append(f"automation_id 匹配")

                        if control_type and ct != control_type:
                            return
                        if control_type:
                            score += 0.3

                        if score > 0:
                            best_candidates.append({
                                'control': ctrl,
                                'score': score,
                                'name': nm,
                                'class_name': cn,
                                'automation_id': aid,
                                'control_type': ct,
                                'match_reasons': match_reasons,
                                'depth': depth,
                            })

                        # 递归子控件
                        for child in ctrl.GetChildren():
                            _walk(child, depth + 1)
                    except Exception:
                        pass

                _walk(window, 0)
                if best_candidates:
                    break
                await asyncio.sleep(0.3)

            if not best_candidates:
                return ModuleResult(success=False, error=f"在 {timeout} 秒内未找到匹配控件")

            # 按 score 排序,深度越浅越稳定(放第二排序)
            best_candidates.sort(key=lambda c: (-c['score'], c['depth']))

            if return_all:
                items = []
                for c in best_candidates[:50]:
                    rect = c['control'].BoundingRectangle
                    items.append({
                        'name': c['name'],
                        'class_name': c['class_name'],
                        'automation_id': c['automation_id'],
                        'control_type': c['control_type'],
                        'score': round(c['score'], 2),
                        'match_reasons': c['match_reasons'],
                        'rect': {'left': rect.left, 'top': rect.top, 'right': rect.right, 'bottom': rect.bottom},
                        'handle': c['control'].NativeWindowHandle,
                    })
                if save_to_variable:
                    context.set_variable(save_to_variable, items)
                return ModuleResult(success=True, message=f"找到 {len(items)} 个候选控件", data={'controls': items})

            # 只取最稳的
            top = best_candidates[0]
            ctrl = top['control']
            rect = ctrl.BoundingRectangle
            info = {
                'name': top['name'],
                'class_name': top['class_name'],
                'automation_id': top['automation_id'],
                'control_type': top['control_type'],
                'score': round(top['score'], 2),
                'match_reasons': top['match_reasons'],
                'handle': ctrl.NativeWindowHandle,
                'rect': {'left': rect.left, 'top': rect.top, 'right': rect.right, 'bottom': rect.bottom},
            }
            if save_to_variable:
                context.set_variable(save_to_variable, info)
            return ModuleResult(
                success=True,
                message=f"找到控件 {top['name'] or top['control_type']}(评分 {top['score']:.2f},候选 {len(best_candidates)} 个)",
                data=info,
            )
        except ImportError:
            return ModuleResult(success=False, error="缺 uiautomation:pip install uiautomation")
        except Exception as e:
            return ModuleResult(success=False, error=f"智能查找失败:{e}")



# =====================================================================
# 2. 批量列表/表格抓取（影刀 DataExtraction Wizard 同款）
# =====================================================================

@register_executor
class DesktopExtractTableExecutor(ModuleExecutor):
    """从桌面应用的列表/表格控件批量抓取数据(自动遍历所有行/项,提取出结构化数据)"""

    @property
    def module_type(self) -> str:
        return "desktop_extract_table"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        try:
            import uiautomation as auto

            app_variable = config.get("appVariable", "desktop_app")
            window_handle = context.get_variable(app_variable)
            if isinstance(window_handle, dict):
                handle = window_handle.get("handle")
            else:
                handle = window_handle
            if not handle:
                return ModuleResult(success=False, error=f"未找到窗口(变量 {app_variable})")
            window = auto.ControlFromHandle(int(handle))

            # 容器选择 - 列表/树/表格控件
            container_name = context.resolve_value(config.get("containerName", ""))
            container_type = context.resolve_value(config.get("containerType", "List"))  # List/DataGrid/Tree/Table
            include_columns = context.resolve_value(config.get("includeColumns", ""))    # 逗号分隔的列名,空=全部
            limit = to_int(config.get("limit", 1000), 1000, context)
            variable_name = config.get("variableName", "extracted_data")
            scroll_to_load = bool(config.get("scrollToLoad", False))

            # 找容器
            container = None
            type_map = {
                "List": auto.ListControl,
                "DataGrid": auto.DataGridControl,
                "Tree": auto.TreeControl,
                "Table": auto.TableControl,
            }
            search_class = type_map.get(container_type, auto.Control)
            search_params = {"searchDepth": 20}
            if container_name:
                search_params["Name"] = container_name
            try:
                container = search_class(**search_params) if search_class != auto.Control else window.Control(**search_params)
                if not container.Exists(0, 0):
                    container = None
            except Exception:
                container = None

            if not container:
                # 退化:在窗口下找第一个匹配类型的容器
                for child in window.GetChildren():
                    if child.ControlTypeName == container_type:
                        container = child
                        break
                    for sub in child.GetChildren():
                        if sub.ControlTypeName == container_type:
                            container = sub
                            break
                    if container:
                        break

            if not container:
                return ModuleResult(success=False, error=f"未找到 {container_type} 容器")

            # 获取所有行
            items = []
            include_cols = [c.strip() for c in include_columns.split(',') if c.strip()] if include_columns else []

            def _extract_row(row, depth=0):
                """递归提取一行的所有可见单元格文字"""
                row_data = {}
                row_text_parts = []

                def _walk(ctrl, d):
                    if d > 5:
                        return
                    try:
                        nm = ctrl.Name or ''
                        ct = ctrl.ControlTypeName or ''
                        if nm and ct in ('TextControl', 'EditControl', 'DataItemControl', 'ListItemControl', 'HyperlinkControl', 'ButtonControl'):
                            row_text_parts.append(nm)
                            # 试图通过头部 Name 当列名
                            try:
                                # uiautomation 的 GridItem 有 Column 属性
                                col_idx = getattr(ctrl, 'GridItemPattern', lambda: None)()
                                if col_idx:
                                    pass
                            except Exception:
                                pass
                        for child in ctrl.GetChildren():
                            _walk(child, d + 1)
                    except Exception:
                        pass

                _walk(row, 0)
                if row_text_parts:
                    row_data['_raw'] = ' | '.join(row_text_parts)
                    # 尝试按位置分列
                    for i, txt in enumerate(row_text_parts):
                        col_name = include_cols[i] if i < len(include_cols) else f'col_{i+1}'
                        row_data[col_name] = txt
                return row_data

            # 滚动加载（虚拟列表场景）
            if scroll_to_load:
                try:
                    container.WheelDown(times=10)
                    await asyncio.sleep(0.5)
                    container.WheelUp(times=10)
                    await asyncio.sleep(0.3)
                except Exception:
                    pass

            for child in container.GetChildren():
                if len(items) >= limit:
                    break
                ct = child.ControlTypeName
                if ct in ('ListItemControl', 'DataItemControl', 'TreeItemControl', 'TableRowControl', 'CustomControl'):
                    row = _extract_row(child)
                    if row:
                        items.append(row)

            if variable_name:
                context.set_variable(variable_name, items)

            return ModuleResult(
                success=True,
                message=f"批量抓取 {len(items)} 条数据",
                data={'count': len(items), 'rows': items[:10], 'all_in_variable': variable_name},
            )
        except ImportError:
            return ModuleResult(success=False, error="需要 uiautomation")
        except Exception as e:
            return ModuleResult(success=False, error=f"批量抓取失败:{e}")


# =====================================================================
# 3. 应用 UI 状态快照（让 AI 一眼看清结构）
# =====================================================================

@register_executor
class DesktopGetAppStateExecutor(ModuleExecutor):
    """全应用 UI 状态快照:返回当前窗口的控件树结构 + 焦点 + 文本内容,适合 AI 排错或快速感知"""

    @property
    def module_type(self) -> str:
        return "desktop_get_app_state"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        try:
            import uiautomation as auto

            app_variable = config.get("appVariable", "desktop_app")
            window_handle = context.get_variable(app_variable)
            if isinstance(window_handle, dict):
                handle = window_handle.get("handle")
            else:
                handle = window_handle
            if not handle:
                return ModuleResult(success=False, error=f"未找到窗口(变量 {app_variable})")
            window = auto.ControlFromHandle(int(handle))

            max_depth = to_int(config.get("maxDepth", 6), 6, context)
            include_invisible = bool(config.get("includeInvisible", False))
            variable_name = config.get("variableName", "app_state")

            # 拿当前焦点控件
            focused = None
            try:
                focused_ctrl = auto.GetFocusedControl()
                if focused_ctrl:
                    focused = {
                        'name': focused_ctrl.Name or '',
                        'class_name': focused_ctrl.ClassName or '',
                        'control_type': focused_ctrl.ControlTypeName or '',
                        'automation_id': focused_ctrl.AutomationId or '',
                    }
            except Exception:
                pass

            # 控件树
            def _to_dict(ctrl, depth=0):
                if depth > max_depth:
                    return None
                try:
                    rect = ctrl.BoundingRectangle
                    visible = rect.width() > 0 and rect.height() > 0
                    if not include_invisible and not visible:
                        return None
                    node = {
                        'name': ctrl.Name or '',
                        'class_name': ctrl.ClassName or '',
                        'control_type': ctrl.ControlTypeName or '',
                        'automation_id': ctrl.AutomationId or '',
                        'rect': [rect.left, rect.top, rect.right, rect.bottom],
                        'children': [],
                    }
                    # 限制子节点数,避免巨大列表
                    children = ctrl.GetChildren()[:30]
                    for child in children:
                        sub = _to_dict(child, depth + 1)
                        if sub:
                            node['children'].append(sub)
                    return node
                except Exception:
                    return None

            tree = _to_dict(window, 0)

            state = {
                'window_title': window.Name or '',
                'window_class': window.ClassName or '',
                'focused': focused,
                'tree': tree,
                'snapshot_at': datetime.now().isoformat(timespec='seconds'),
            }
            if variable_name:
                context.set_variable(variable_name, state)

            return ModuleResult(
                success=True,
                message=f"已快照应用 UI 状态(树深度 {max_depth})",
                data={'window_title': state['window_title'], 'focused': focused, 'top_level_children': len(tree['children']) if tree else 0},
            )
        except ImportError:
            return ModuleResult(success=False, error="需要 uiautomation")
        except Exception as e:
            return ModuleResult(success=False, error=f"快照失败:{e}")


# =====================================================================
# 4. XPath 风格查询(影刀 selector 表达式同款)
# =====================================================================

_XPATH_RE = re.compile(r'//?(\w+)(?:\[([^\]]+)\])?')


def _parse_xpath_step(step_text: str) -> tuple[str, dict]:
    """解析 //Button[@name='登录'] 这种语法,返回 (control_type, attrs)"""
    m = _XPATH_RE.match(step_text)
    if not m:
        return '', {}
    ct = m.group(1)
    attrs_str = m.group(2) or ''
    attrs = {}
    for kv in re.finditer(r"@(\w+)\s*=\s*['\"]([^'\"]+)['\"]", attrs_str):
        attrs[kv.group(1)] = kv.group(2)
    # 支持 contains(@name, "登录") 形式
    for kv in re.finditer(r'contains\(@(\w+),\s*[\'"]([^\'"]+)[\'"]\)', attrs_str):
        attrs[f'_contains_{kv.group(1)}'] = kv.group(2)
    return ct, attrs


@register_executor
class DesktopQueryWithXpathExecutor(ModuleExecutor):
    """用 XPath 风格表达式查找控件:支持 //Button[@name='登录'] / //*[contains(@name,'确定')]"""

    @property
    def module_type(self) -> str:
        return "desktop_query_with_xpath"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        try:
            import uiautomation as auto

            app_variable = config.get("appVariable", "desktop_app")
            window_handle = context.get_variable(app_variable)
            if isinstance(window_handle, dict):
                handle = window_handle.get("handle")
            else:
                handle = window_handle
            if not handle:
                return ModuleResult(success=False, error=f"未找到窗口(变量 {app_variable})")
            window = auto.ControlFromHandle(int(handle))

            xpath = context.resolve_value(config.get("xpath", ""))
            if not xpath:
                return ModuleResult(success=False, error="xpath 不能为空")
            timeout = to_int(config.get("timeout", 5), 5, context)
            save_to_variable = config.get("saveToVariable", "desktop_control")

            # 简单解析:逐段处理 //Button[...]/Edit[...]
            steps = []
            for m in _XPATH_RE.finditer(xpath):
                ct, attrs = _parse_xpath_step(m.group(0))
                steps.append((ct, attrs))
            if not steps:
                return ModuleResult(success=False, error=f"无法解析 xpath: {xpath}")

            type_map = {
                'Button': auto.ButtonControl, 'Edit': auto.EditControl, 'Text': auto.TextControl,
                'ComboBox': auto.ComboBoxControl, 'List': auto.ListControl,
                'ListItem': auto.ListItemControl, 'CheckBox': auto.CheckBoxControl,
                'RadioButton': auto.RadioButtonControl, 'Tree': auto.TreeControl,
                'TreeItem': auto.TreeItemControl, 'Tab': auto.TabControl, 'TabItem': auto.TabItemControl,
                'Menu': auto.MenuControl, 'MenuItem': auto.MenuItemControl, 'Image': auto.ImageControl,
                'Pane': auto.PaneControl, 'Window': auto.WindowControl, 'Group': auto.GroupControl,
                'Custom': auto.CustomControl,
            }

            start = time.time()
            current = window
            while time.time() - start < timeout:
                ok = True
                cur = window
                for ct, attrs in steps:
                    klass = type_map.get(ct, auto.Control) if ct != '*' else auto.Control
                    params = {'searchDepth': 15}
                    for k, v in attrs.items():
                        if k == 'name' or k == 'Name':
                            params['Name'] = v
                        elif k == 'classname' or k == 'class' or k == 'ClassName':
                            params['ClassName'] = v
                        elif k == 'automationid' or k == 'AutomationId':
                            params['AutomationId'] = v
                    # contains 语义:不能用 uiautomation 直接传,得遍历
                    contains_filters = {k.replace('_contains_', ''): v for k, v in attrs.items() if k.startswith('_contains_')}
                    try:
                        if contains_filters:
                            # 遍历找包含子串的
                            found = None
                            def _walk(ctrl, d=0):
                                nonlocal found
                                if found or d > 15:
                                    return
                                try:
                                    if ct != '*' and ctrl.ControlTypeName != ct:
                                        for child in ctrl.GetChildren():
                                            _walk(child, d + 1)
                                            if found:
                                                return
                                        return
                                    nm = ctrl.Name or ''
                                    cn = ctrl.ClassName or ''
                                    aid = ctrl.AutomationId or ''
                                    match = True
                                    for k, v in contains_filters.items():
                                        check_v = nm if k.lower() == 'name' else (cn if k.lower() == 'classname' else aid)
                                        if v not in check_v:
                                            match = False
                                            break
                                    if match:
                                        found = ctrl
                                        return
                                    for child in ctrl.GetChildren():
                                        _walk(child, d + 1)
                                        if found:
                                            return
                                except Exception:
                                    pass
                            _walk(cur, 0)
                            if found:
                                cur = found
                            else:
                                ok = False
                                break
                        else:
                            target = cur.Control(**params) if klass == auto.Control else klass(**params)
                            if target.Exists(0, 0):
                                cur = target
                            else:
                                ok = False
                                break
                    except Exception:
                        ok = False
                        break
                if ok:
                    current = cur
                    rect = current.BoundingRectangle
                    info = {
                        'name': current.Name or '',
                        'class_name': current.ClassName or '',
                        'automation_id': current.AutomationId or '',
                        'control_type': current.ControlTypeName or '',
                        'handle': current.NativeWindowHandle,
                        'rect': {'left': rect.left, 'top': rect.top, 'right': rect.right, 'bottom': rect.bottom},
                    }
                    if save_to_variable:
                        context.set_variable(save_to_variable, info)
                    return ModuleResult(success=True, message=f"已找到 xpath 匹配: {xpath}", data=info)
                await asyncio.sleep(0.3)

            return ModuleResult(success=False, error=f"在 {timeout} 秒内未匹配 xpath: {xpath}")
        except ImportError:
            return ModuleResult(success=False, error="需要 uiautomation")
        except Exception as e:
            return ModuleResult(success=False, error=f"XPath 查询失败:{e}")



# =====================================================================
# 5. 双击/全选并复制文字
# =====================================================================

@register_executor
class DesktopSelectTextExecutor(ModuleExecutor):
    """从控件中选中并提取文字(双击/Ctrl+A 全选/拖选范围)"""

    @property
    def module_type(self) -> str:
        return "desktop_select_text"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        try:
            import uiautomation as auto
            import pyautogui
            import pyperclip

            control_variable = config.get("controlVariable", "desktop_control")
            ctrl_info = context.get_variable(control_variable)
            if not ctrl_info:
                return ModuleResult(success=False, error=f"未找到控件(变量 {control_variable})")
            handle = ctrl_info.get('handle') if isinstance(ctrl_info, dict) else ctrl_info
            ctrl = auto.ControlFromHandle(int(handle)) if handle else None
            if not ctrl or not ctrl.Exists(0, 0):
                return ModuleResult(success=False, error="控件不存在")

            select_mode = config.get("selectMode", "all")  # all/double_click/range
            variable_name = config.get("variableName", "selected_text")

            ctrl.SetFocus()
            await asyncio.sleep(0.15)

            if select_mode == 'double_click':
                ctrl.DoubleClick()
            elif select_mode == 'all':
                pyautogui.hotkey('ctrl', 'a')
            else:
                ctrl.Click()

            await asyncio.sleep(0.1)
            pyautogui.hotkey('ctrl', 'c')
            await asyncio.sleep(0.2)
            text = pyperclip.paste() or ''
            if variable_name:
                context.set_variable(variable_name, text)
            return ModuleResult(
                success=True,
                message=f"已提取文字 ({len(text)} 字符)",
                data={'text': text[:200], 'length': len(text)},
            )
        except ImportError as e:
            return ModuleResult(success=False, error=f"缺依赖:{e}")
        except Exception as e:
            return ModuleResult(success=False, error=f"提取文字失败:{e}")


# =====================================================================
# 6. 拿当前焦点控件
# =====================================================================

@register_executor
class DesktopGetFocusedControlExecutor(ModuleExecutor):
    """返回当前键盘焦点所在的控件信息(动态分析活动元素)"""

    @property
    def module_type(self) -> str:
        return "desktop_get_focused_control"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        try:
            import uiautomation as auto
            save_to_variable = config.get("saveToVariable", "focused_control")
            ctrl = auto.GetFocusedControl()
            if not ctrl:
                return ModuleResult(success=False, error="当前没有焦点控件")
            rect = ctrl.BoundingRectangle
            info = {
                'name': ctrl.Name or '',
                'class_name': ctrl.ClassName or '',
                'automation_id': ctrl.AutomationId or '',
                'control_type': ctrl.ControlTypeName or '',
                'handle': ctrl.NativeWindowHandle,
                'rect': {'left': rect.left, 'top': rect.top, 'right': rect.right, 'bottom': rect.bottom},
            }
            if save_to_variable:
                context.set_variable(save_to_variable, info)
            return ModuleResult(success=True, message=f"焦点控件: {info['name'] or info['control_type']}", data=info)
        except Exception as e:
            return ModuleResult(success=False, error=f"获取焦点失败:{e}")


# =====================================================================
# 7. 断言控件状态(测试场景)
# =====================================================================

@register_executor
class DesktopAssertControlExecutor(ModuleExecutor):
    """断言桌面控件的状态(存在/可见/启用/选中/包含文字),不满足则失败,适合测试场景"""

    @property
    def module_type(self) -> str:
        return "desktop_assert_control"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        try:
            import uiautomation as auto

            control_variable = config.get("controlVariable", "desktop_control")
            ctrl_info = context.get_variable(control_variable)
            if not ctrl_info:
                return ModuleResult(success=False, error=f"未找到控件(变量 {control_variable})")
            handle = ctrl_info.get('handle') if isinstance(ctrl_info, dict) else ctrl_info
            ctrl = auto.ControlFromHandle(int(handle)) if handle else None
            if not ctrl:
                return ModuleResult(success=False, error="控件已不存在")

            assertion = config.get("assertion", "exists")  # exists/visible/enabled/selected/text_contains/value_equals
            expected = context.resolve_value(config.get("expected", ""))

            ok = False
            actual = ''
            if assertion == 'exists':
                ok = ctrl.Exists(0, 0)
            elif assertion == 'visible':
                rect = ctrl.BoundingRectangle
                ok = rect.width() > 0 and rect.height() > 0
                actual = f"{rect.width()}x{rect.height()}"
            elif assertion == 'enabled':
                ok = bool(ctrl.IsEnabled)
                actual = str(ctrl.IsEnabled)
            elif assertion == 'selected':
                try:
                    sp = ctrl.GetSelectionItemPattern()
                    ok = bool(sp.IsSelected) if sp else False
                except Exception:
                    ok = False
            elif assertion == 'text_contains':
                actual = ctrl.Name or ''
                ok = expected in actual
            elif assertion == 'value_equals':
                try:
                    vp = ctrl.GetValuePattern()
                    actual = vp.Value if vp else ''
                except Exception:
                    actual = ''
                ok = actual == expected
            else:
                return ModuleResult(success=False, error=f"未知断言: {assertion}")

            if ok:
                return ModuleResult(success=True, message=f"断言通过: {assertion}", data={'actual': actual})
            else:
                return ModuleResult(success=False, error=f"断言失败: {assertion} (期望 {expected!r}, 实际 {actual!r})")
        except Exception as e:
            return ModuleResult(success=False, error=f"断言执行异常:{e}")


