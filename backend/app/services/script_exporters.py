# -*- coding: utf-8 -*-
"""多目标脚本导出器：Selenium(Python) 与 Playwright(JavaScript/Node)

在原有 Playwright Python 导出之外，再提供两种目标，方便不同技术栈团队接手脚本：
- selenium  ->  独立的 Selenium + Python 脚本
- playwright-js -> 独立的 Playwright + Node.js(JavaScript) 脚本

覆盖范围：网页打开/点击/输入/悬停/下拉/勾选/键盘、等待、滚动、截图、获取元素、
导航（刷新/前进/后退/关闭）、流程控制（条件/循环/遍历/跳出/继续）、变量与日志。
对于这两个目标暂不支持的高级模块（系统操作、Excel、AI、手机等），会生成清晰的
注释占位并附上原配置，提示请在 WebRPA 内运行或手动实现，绝不静默丢弃。
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, List, Dict


class _BaseScriptExporter:
    """共享的工作流遍历 / 拓扑 / 分支收集逻辑（语言无关）"""

    brace = False  # True 表示用花括号块（JS），False 表示用缩进块（Python）

    def __init__(self):
        self.lines: List[str] = []
        self.indent = 0
        self.node_map: Dict[str, dict] = {}
        self.edge_map: Dict[str, Dict[str, list]] = {}
        self.all_edges: list = []
        self.var_names: List[str] = []

    # ---------- 输出原语 ----------
    def add(self, code: str = ""):
        self.lines.append(("    " * self.indent) + code if code else "")

    def comment(self, text: str):
        prefix = "// " if self.brace else "# "
        for ln in str(text).split("\n"):
            self.add(f"{prefix}{ln}")

    def open_block(self, header: str):
        self.add(header)
        self.indent += 1

    def close_block(self):
        self.indent = max(0, self.indent - 1)
        if self.brace:
            self.add("}")

    # ---------- 主入口 ----------
    def export(self, workflow_data: dict) -> str:
        self.lines = []
        self.indent = 0
        name = workflow_data.get("name", "未命名工作流")
        nodes = workflow_data.get("nodes", []) or []
        edges = workflow_data.get("edges", []) or []
        variables = workflow_data.get("variables", []) or []

        self.node_map = {n["id"]: n for n in nodes if isinstance(n, dict) and "id" in n}
        self.all_edges = edges
        self.edge_map = {}
        for edge in edges:
            s = edge.get("source")
            h = edge.get("sourceHandle", "default") or "default"
            t = edge.get("target")
            if s is None or t is None:
                continue
            self.edge_map.setdefault(s, {}).setdefault(h, []).append(t)

        order = self._build_execution_order(nodes, edges)

        for ln in self.header_lines(name):
            self.add(ln)
        self.begin_main()
        self.var_names = [v.get("name") for v in variables if isinstance(v, dict) and v.get("name")]
        for ln in self.var_init_lines(variables):
            self.add(ln)
        self.add("")

        processed: set = set()
        for nid in order:
            node = self.node_map.get(nid)
            if node and nid not in processed:
                self._gen_node(node, processed)

        self.end_main()
        for ln in self.footer_lines():
            self.add(ln)
        return "\n".join(self.lines)

    # ---------- 拓扑与分支（移植自 Playwright 导出器，语言无关） ----------
    def _build_execution_order(self, nodes: list, edges: list) -> list:
        ids = [n["id"] for n in nodes if isinstance(n, dict) and "id" in n]
        adj = {i: [] for i in ids}
        indeg = {i: 0 for i in ids}
        for e in edges:
            s, t = e.get("source"), e.get("target")
            if s in adj and t in indeg:
                adj[s].append(t)
                indeg[t] += 1
        queue = [i for i in ids if indeg[i] == 0]
        result = []
        while queue:
            cur = queue.pop(0)
            result.append(cur)
            for nx in adj[cur]:
                indeg[nx] -= 1
                if indeg[nx] == 0:
                    queue.append(nx)
        # 兜底：把未排进去的（成环）补上
        for i in ids:
            if i not in result:
                result.append(i)
        return result

    def _topological_sort_nodes(self, node_ids: set) -> list:
        node_ids = set(node_ids)
        adj = {i: [] for i in node_ids}
        indeg = {i: 0 for i in node_ids}
        for e in self.all_edges:
            s, t = e.get("source"), e.get("target")
            if s in node_ids and t in node_ids:
                adj[s].append(t)
                indeg[t] += 1
        queue = [i for i in node_ids if indeg[i] == 0]
        result = []
        while queue:
            cur = queue.pop(0)
            result.append(cur)
            for nx in adj[cur]:
                indeg[nx] -= 1
                if indeg[nx] == 0:
                    queue.append(nx)
        for i in node_ids:
            if i not in result:
                result.append(i)
        return result

    def _collect_branch_nodes(self, start_nodes: list, exclude_starts: list) -> set:
        """从分支起点出发收集该分支可达的全部节点（不跨入另一分支起点）"""
        exclude = set(exclude_starts or [])
        collected: set = set()
        stack = list(start_nodes or [])
        while stack:
            nid = stack.pop()
            if nid in collected or nid in exclude:
                continue
            collected.add(nid)
            for h, targets in self.edge_map.get(nid, {}).items():
                for t in targets:
                    if t not in collected and t not in exclude:
                        stack.append(t)
        return collected

    def _collect_loop_body_nodes(self, start_nodes: list, done_nodes: list) -> set:
        done = set(done_nodes or [])
        collected: set = set()
        stack = list(start_nodes or [])
        while stack:
            nid = stack.pop()
            if nid in collected or nid in done:
                continue
            collected.add(nid)
            for h, targets in self.edge_map.get(nid, {}).items():
                if h in ("done", "loop-done"):
                    continue
                for t in targets:
                    if t not in collected and t not in done:
                        stack.append(t)
        return collected

    # ---------- 节点分派 ----------
    def _gen_node(self, node: dict, processed: set):
        nid = node["id"]
        if nid in processed:
            return
        processed.add(nid)
        ntype = node.get("type", "")
        data = node.get("data", {}) or {}
        mtype = data.get("moduleType", ntype)
        label = data.get("label", mtype)

        if ntype == "groupNode":
            self.comment(f"分组: {label}")
            return

        self.add("")
        self.comment(f"节点: {label}")

        if mtype == "condition":
            self._gen_condition(data, nid, processed)
            return
        if mtype in ("loop", "foreach"):
            self._gen_loop(data, nid, processed, is_foreach=(mtype == "foreach"))
            return

        method = getattr(self, f"m_{mtype}", None)
        if method:
            try:
                for ln in (method(data) or []):
                    self.add(ln)
            except Exception as e:
                self.comment(f"[导出告警] 模块 {mtype} 生成失败: {e}")
        else:
            self._unsupported(mtype, data)

    def _unsupported(self, mtype: str, data: dict):
        self.comment(f"[WebRPA] 模块「{mtype}」在此目标暂不支持自动导出，请在 WebRPA 中运行或手动实现。原配置：")
        try:
            for k in [k for k in data.keys() if k not in ("label", "moduleType")][:10]:
                v = str(data.get(k))
                if len(v) > 80:
                    v = v[:80] + "..."
                self.comment(f"  {k} = {v}")
        except Exception:
            pass

    # ---------- 子类需实现 ----------
    def header_lines(self, name: str) -> List[str]:
        raise NotImplementedError

    def begin_main(self):
        raise NotImplementedError

    def end_main(self):
        raise NotImplementedError

    def footer_lines(self) -> List[str]:
        raise NotImplementedError

    def var_init_lines(self, variables: list) -> List[str]:
        raise NotImplementedError

    def _gen_condition(self, data, nid, processed):
        raise NotImplementedError

    def _gen_loop(self, data, nid, processed, is_foreach=False):
        raise NotImplementedError


_VAR_REF = re.compile(r'\$?\{\{([a-zA-Z_\u4e00-\u9fa5][\w\u4e00-\u9fa5]*)\}\}')


class SeleniumExporter(_BaseScriptExporter):
    """导出为 Selenium + Python 脚本"""

    brace = False

    def resolve(self, value: Any) -> str:
        """把含 {var}/${var} 的值翻译为 Python 表达式（f-string）。"""
        if value is None:
            return '""'
        if isinstance(value, bool):
            return "True" if value else "False"
        if isinstance(value, (int, float)):
            return str(value)
        if not isinstance(value, str):
            return json.dumps(value, ensure_ascii=False)
        # 先转义所有花括号，再把变量引用占位还原为 f-string 表达式
        escaped = value.replace("{", "{{").replace("}", "}}")
        escaped = _VAR_REF.sub(lambda m: f"{{variables.get('{m.group(1)}', '')}}", escaped)
        # 兼容单层 ${var} / {var}
        escaped = re.sub(r'\$?\{\{([a-zA-Z_\u4e00-\u9fa5][\w\u4e00-\u9fa5]*)\}\}',
                         lambda m: f"{{variables.get('{m.group(1)}', '')}}", escaped)
        escaped = escaped.replace("\\", "\\\\").replace('"', '\\"')
        return f'f"{escaped}"'

    def header_lines(self, name: str) -> List[str]:
        return [
            '"""',
            f'Selenium 自动化脚本 - {name}',
            f'由 WebRPA 自动生成于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            '',
            '使用方法:',
            '1. 安装依赖: pip install selenium',
            '2. 安装与浏览器匹配的 WebDriver（Selenium 4 已内置 Selenium Manager，通常无需手动安装）',
            '3. 运行脚本: python this_script.py',
            '"""',
            'import time',
            'from selenium import webdriver',
            'from selenium.webdriver.common.by import By',
            'from selenium.webdriver.common.keys import Keys',
            'from selenium.webdriver.common.action_chains import ActionChains',
            'from selenium.webdriver.support.ui import WebDriverWait, Select',
            'from selenium.webdriver.support import expected_conditions as EC',
            '',
            'variables = {}',
            'driver = webdriver.Chrome()',
            'driver.maximize_window()',
            '',
            'def _by(selector):',
            '    s = (selector or "").strip()',
            '    if s.startswith("xpath="):',
            '        return (By.XPATH, s[6:])',
            '    if s.startswith("css="):',
            '        return (By.CSS_SELECTOR, s[4:])',
            '    if s.startswith("/") or s.startswith("(") or s.startswith("./"):',
            '        return (By.XPATH, s)',
            '    return (By.CSS_SELECTOR, s)',
            '',
            'def find(selector, timeout=30):',
            '    by, val = _by(selector)',
            '    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, val)))',
            '',
            'def find_all(selector):',
            '    by, val = _by(selector)',
            '    return driver.find_elements(by, val)',
            '',
        ]

    def begin_main(self):
        self.add("def run_workflow():")
        self.indent += 1

    def end_main(self):
        self.indent -= 1

    def footer_lines(self) -> List[str]:
        return [
            '',
            'if __name__ == "__main__":',
            '    try:',
            '        run_workflow()',
            '    finally:',
            '        try:',
            '            driver.quit()',
            '        except Exception:',
            '            pass',
        ]

    def var_init_lines(self, variables: list) -> List[str]:
        lines = []
        for v in variables:
            if not isinstance(v, dict) or not v.get("name"):
                continue
            name = v["name"]
            val = v.get("value", v.get("defaultValue", ""))
            lines.append(f'variables["{name}"] = {json.dumps(val, ensure_ascii=False)}')
        return lines

    # ---------- 动作生成 ----------
    def m_open_page(self, data):
        return [f'driver.get({self.resolve(data.get("url", ""))})']

    def m_click_element(self, data):
        sel = self.resolve(data.get("selector", ""))
        ctype = data.get("clickType", "single")
        if ctype == "double":
            return [f'_el = find({sel})', 'ActionChains(driver).double_click(_el).perform()']
        if ctype == "right":
            return [f'_el = find({sel})', 'ActionChains(driver).context_click(_el).perform()']
        return [f'find({sel}).click()']

    def m_hover_element(self, data):
        sel = self.resolve(data.get("selector", ""))
        return [f'ActionChains(driver).move_to_element(find({sel})).perform()']

    def m_input_text(self, data):
        sel = self.resolve(data.get("selector", ""))
        text = self.resolve(data.get("text", ""))
        lines = [f'_el = find({sel})']
        if data.get("clearBefore", True):
            lines.append('_el.clear()')
        lines.append(f'_el.send_keys(str({text}))')
        return lines

    def m_get_element_info(self, data):
        sel = self.resolve(data.get("selector", ""))
        attr = data.get("attribute", "text")
        var = data.get("variableName", "result")
        multiple = data.get("multiple", False)
        if multiple:
            if attr == "text":
                return [f'variables["{var}"] = [e.text for e in find_all({sel})]']
            return [f'variables["{var}"] = [e.get_attribute("{attr}") for e in find_all({sel})]']
        if attr == "text":
            return [f'variables["{var}"] = find({sel}).text']
        return [f'variables["{var}"] = find({sel}).get_attribute("{attr}")']

    def m_wait(self, data):
        dur = data.get("duration", 1000)
        try:
            secs = float(dur) / 1000
        except Exception:
            secs = 1
        return [f'time.sleep({secs})']

    def m_wait_element(self, data):
        sel = self.resolve(data.get("selector", ""))
        timeout = int(data.get("timeout", 30000)) // 1000 or 30
        return [f'find({sel}, timeout={timeout})']

    def m_close_page(self, data):
        return ['driver.close()']

    def m_refresh_page(self, data):
        return ['driver.refresh()']

    def m_go_back(self, data):
        return ['driver.back()']

    def m_go_forward(self, data):
        return ['driver.forward()']

    def m_screenshot(self, data):
        path = self.resolve(data.get("savePath", "screenshot.png"))
        lines = [f'driver.save_screenshot({path})']
        var = data.get("variableName")
        if var:
            lines.append(f'variables["{var}"] = {path}')
        return lines

    def m_scroll_page(self, data):
        direction = data.get("direction", "down")
        dist = data.get("distance", 500)
        if direction == "up":
            return [f'driver.execute_script("window.scrollBy(0, -{dist})")']
        if direction == "top":
            return ['driver.execute_script("window.scrollTo(0, 0)")']
        if direction == "bottom":
            return ['driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")']
        return [f'driver.execute_script("window.scrollBy(0, {dist})")']

    def m_select_dropdown(self, data):
        sel = self.resolve(data.get("selector", ""))
        mode = data.get("selectBy", "text")
        value = self.resolve(data.get("value", ""))
        if mode == "value":
            return [f'Select(find({sel})).select_by_value(str({value}))']
        if mode == "index":
            return [f'Select(find({sel})).select_by_index(int({value}))']
        return [f'Select(find({sel})).select_by_visible_text(str({value}))']

    def m_set_checkbox(self, data):
        sel = self.resolve(data.get("selector", ""))
        checked = bool(data.get("checked", True))
        return [f'_el = find({sel})', f'if _el.is_selected() != {checked}:', '    _el.click()']

    def m_keyboard_action(self, data):
        keys = self.resolve(data.get("keySequence", data.get("keys", "")))
        return [f'ActionChains(driver).send_keys(str({keys})).perform()']

    def m_set_variable(self, data):
        name = data.get("variableName", "")
        if not name:
            return []
        return [f'variables["{name}"] = {self.resolve(data.get("value", ""))}']

    def m_print_log(self, data):
        msg = self.resolve(data.get("logMessage", data.get("message", "")))
        level = data.get("level", "INFO")
        return [f'print("[{level}] " + str({msg}))']

    def m_break_loop(self, data):
        return ["break"]

    def m_continue_loop(self, data):
        return ["continue"]

    # ---------- 流程控制 ----------
    def _build_condition_expr(self, data) -> str:
        left = data.get("leftValue", data.get("value1", data.get("variable")))
        op = data.get("operator", data.get("compareOperator"))
        right = data.get("rightValue", data.get("value2", data.get("compareValue")))
        if left is not None and op:
            l = self.resolve(left)
            r = self.resolve(right if right is not None else "")
            mapping = {
                "==": f"str({l}) == str({r})", "equals": f"str({l}) == str({r})",
                "!=": f"str({l}) != str({r})", "not_equals": f"str({l}) != str({r})",
                ">": f"float({l}) > float({r})", "<": f"float({l}) < float({r})",
                ">=": f"float({l}) >= float({r})", "<=": f"float({l}) <= float({r})",
                "contains": f"str({r}) in str({l})", "not_contains": f"str({r}) not in str({l})",
                "empty": f"not str({l})", "not_empty": f"bool(str({l}))",
            }
            return mapping.get(op, f"str({l}) == str({r})")
        raw = data.get("condition", data.get("expression", "True"))
        return self.resolve(raw) if isinstance(raw, str) and ("{" in raw) else (str(raw) or "True")

    def _emit_branch(self, targets, exclude, processed):
        nodes = self._collect_branch_nodes(targets, exclude)
        for tid in self._topological_sort_nodes(nodes):
            if tid in self.node_map and tid not in processed:
                self._gen_node(self.node_map[tid], processed)
        for nid in nodes:
            processed.add(nid)

    def _gen_condition(self, data, nid, processed):
        expr = self._build_condition_expr(data)
        em = self.edge_map.get(nid, {})
        true_t = em.get("true", []) or em.get("condition-true", [])
        false_t = em.get("false", []) or em.get("condition-false", [])
        self.open_block(f"if {expr}:")
        if true_t:
            self._emit_branch(true_t, false_t, processed)
        else:
            self.add("pass")
        self.close_block()
        if false_t:
            self.open_block("else:")
            self._emit_branch(false_t, true_t, processed)
            self.close_block()

    def _gen_loop(self, data, nid, processed, is_foreach=False):
        em = self.edge_map.get(nid, {})
        body_t = em.get("loop", []) or em.get("loop-body", []) or em.get("body", []) or em.get("default", [])
        done_t = em.get("done", []) or em.get("loop-done", [])
        if is_foreach:
            lst = data.get("listVariable", data.get("sourceVariable", ""))
            item = data.get("itemVariable", "item")
            self.open_block(f'for _item in variables.get("{lst}", []):')
            self.add(f'variables["{item}"] = _item')
        else:
            ltype = data.get("loopType", data.get("loopMode", "count"))
            if ltype == "while":
                cond = self._build_condition_expr(data)
                self.open_block(f"while {cond}:")
            else:
                count = data.get("count", data.get("loopCount", 1))
                idx = data.get("indexVariable", "index")
                self.open_block(f'for _i in range(int({self.resolve(count)})):')
                self.add(f'variables["{idx}"] = _i')
        if body_t:
            body_nodes = self._collect_loop_body_nodes(body_t, done_t)
            for tid in self._topological_sort_nodes(body_nodes):
                if tid in self.node_map and tid not in processed:
                    self._gen_node(self.node_map[tid], processed)
            for n in body_nodes:
                processed.add(n)
        else:
            self.add("pass")
        self.close_block()
        for tid in done_t:
            if tid in self.node_map and tid not in processed:
                self._gen_node(self.node_map[tid], processed)


_JS_VAR_REF = re.compile(r'\$?\{\{?([a-zA-Z_\u4e00-\u9fa5][\w\u4e00-\u9fa5]*)\}?\}')


class PlaywrightJSExporter(_BaseScriptExporter):
    """导出为 Playwright + Node.js(JavaScript) 脚本"""

    brace = True

    def resolve(self, value: Any) -> str:
        """把含 {var}/${var} 的值翻译为 JS 表达式（模板字符串）。"""
        if value is None:
            return '""'
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if not isinstance(value, str):
            return "JSON.parse(" + json.dumps(json.dumps(value, ensure_ascii=False)) + ")"
        # 1) 变量引用替换为哨兵
        def _sentinel(m):
            return f"\x00{m.group(1)}\x00"
        tmp = _JS_VAR_REF.sub(_sentinel, value)
        # 2) 为模板字符串转义
        tmp = tmp.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        # 3) 还原哨兵为模板表达式
        tmp = re.sub(r"\x00([a-zA-Z_\u4e00-\u9fa5][\w\u4e00-\u9fa5]*)\x00",
                     lambda m: '${variables[' + json.dumps(m.group(1)) + '] ?? ""}', tmp)
        return f"`{tmp}`"

    def header_lines(self, name: str) -> List[str]:
        return [
            "/**",
            f" * Playwright(JavaScript) 自动化脚本 - {name}",
            f" * 由 WebRPA 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            " *",
            " * 使用方法:",
            " * 1. 安装依赖: npm i playwright",
            " * 2. 安装浏览器: npx playwright install chromium",
            " * 3. 运行脚本: node this_script.js",
            " */",
            "const { chromium } = require('playwright');",
            "let variables = {};",
            "",
        ]

    def begin_main(self):
        self.add("(async () => {")
        self.indent += 1
        self.add("const browser = await chromium.launch({ headless: false });")
        self.add("const context = await browser.newContext();")
        self.add("const page = await context.newPage();")
        self.add("try {")
        self.indent += 1

    def end_main(self):
        self.indent -= 1
        self.add("} finally {")
        self.indent += 1
        self.add("await browser.close();")
        self.indent -= 1
        self.add("}")
        self.indent -= 1
        self.add("})();")

    def footer_lines(self) -> List[str]:
        return []

    def var_init_lines(self, variables: list) -> List[str]:
        lines = []
        for v in variables:
            if not isinstance(v, dict) or not v.get("name"):
                continue
            val = v.get("value", v.get("defaultValue", ""))
            lines.append(f'variables[{json.dumps(v["name"])}] = {json.dumps(val, ensure_ascii=False)};')
        return lines

    # ---------- 动作 ----------
    def m_open_page(self, data):
        wait = data.get("waitUntil", "load")
        return [f'await page.goto({self.resolve(data.get("url", ""))}, {{ waitUntil: "{wait}" }});']

    def m_click_element(self, data):
        sel = self.resolve(data.get("selector", ""))
        ctype = data.get("clickType", "single")
        if ctype == "double":
            return [f'await page.dblclick({sel});']
        if ctype == "right":
            return [f'await page.click({sel}, {{ button: "right" }});']
        return [f'await page.click({sel});']

    def m_hover_element(self, data):
        return [f'await page.hover({self.resolve(data.get("selector", ""))});']

    def m_input_text(self, data):
        sel = self.resolve(data.get("selector", ""))
        text = self.resolve(data.get("text", ""))
        return [f'await page.fill({sel}, String({text}));']

    def m_get_element_info(self, data):
        sel = self.resolve(data.get("selector", ""))
        attr = data.get("attribute", "text")
        var = json.dumps(data.get("variableName", "result"))
        multiple = data.get("multiple", False)
        if multiple:
            if attr == "text":
                return [f'variables[{var}] = await page.$$eval({sel}, els => els.map(e => e.textContent));']
            return [f'variables[{var}] = await page.$$eval({sel}, (els, a) => els.map(e => e.getAttribute(a)), "{attr}");']
        if attr == "text":
            return [f'variables[{var}] = await page.textContent({sel});']
        return [f'variables[{var}] = await page.getAttribute({sel}, "{attr}");']

    def m_wait(self, data):
        try:
            ms = int(float(data.get("duration", 1000)))
        except Exception:
            ms = 1000
        return [f'await page.waitForTimeout({ms});']

    def m_wait_element(self, data):
        sel = self.resolve(data.get("selector", ""))
        timeout = int(data.get("timeout", 30000))
        state = data.get("state", "visible")
        return [f'await page.waitForSelector({sel}, {{ state: "{state}", timeout: {timeout} }});']

    def m_close_page(self, data):
        return ['await page.close();']

    def m_refresh_page(self, data):
        return ['await page.reload();']

    def m_go_back(self, data):
        return ['await page.goBack();']

    def m_go_forward(self, data):
        return ['await page.goForward();']

    def m_screenshot(self, data):
        path = self.resolve(data.get("savePath", "screenshot.png"))
        full = "true" if data.get("fullPage", False) else "false"
        lines = [f'await page.screenshot({{ path: {path}, fullPage: {full} }});']
        var = data.get("variableName")
        if var:
            lines.append(f'variables[{json.dumps(var)}] = {path};')
        return lines

    def m_scroll_page(self, data):
        direction = data.get("direction", "down")
        dist = int(data.get("distance", 500))
        if direction == "up":
            return [f'await page.evaluate((d) => window.scrollBy(0, -d), {dist});']
        if direction == "top":
            return ['await page.evaluate(() => window.scrollTo(0, 0));']
        if direction == "bottom":
            return ['await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));']
        return [f'await page.evaluate((d) => window.scrollBy(0, d), {dist});']

    def m_select_dropdown(self, data):
        sel = self.resolve(data.get("selector", ""))
        mode = data.get("selectBy", "text")
        value = self.resolve(data.get("value", ""))
        if mode == "value":
            return [f'await page.selectOption({sel}, {{ value: String({value}) }});']
        if mode == "index":
            return [f'await page.selectOption({sel}, {{ index: Number({value}) }});']
        return [f'await page.selectOption({sel}, {{ label: String({value}) }});']

    def m_set_checkbox(self, data):
        sel = self.resolve(data.get("selector", ""))
        checked = "true" if data.get("checked", True) else "false"
        return [f'await page.setChecked({sel}, {checked});']

    def m_keyboard_action(self, data):
        keys = self.resolve(data.get("keySequence", data.get("keys", "")))
        return [f'await page.keyboard.press(String({keys}));']

    def m_set_variable(self, data):
        name = data.get("variableName", "")
        if not name:
            return []
        return [f'variables[{json.dumps(name)}] = {self.resolve(data.get("value", ""))};']

    def m_print_log(self, data):
        msg = self.resolve(data.get("logMessage", data.get("message", "")))
        level = data.get("level", "INFO")
        return [f'console.log("[{level}] " + String({msg}));']

    def m_break_loop(self, data):
        return ["break;"]

    def m_continue_loop(self, data):
        return ["continue;"]

    # ---------- 流程控制 ----------
    def _build_condition_expr(self, data) -> str:
        left = data.get("leftValue", data.get("value1", data.get("variable")))
        op = data.get("operator", data.get("compareOperator"))
        right = data.get("rightValue", data.get("value2", data.get("compareValue")))
        if left is not None and op:
            l = self.resolve(left)
            r = self.resolve(right if right is not None else "")
            mapping = {
                "==": f"String({l}) === String({r})", "equals": f"String({l}) === String({r})",
                "!=": f"String({l}) !== String({r})", "not_equals": f"String({l}) !== String({r})",
                ">": f"Number({l}) > Number({r})", "<": f"Number({l}) < Number({r})",
                ">=": f"Number({l}) >= Number({r})", "<=": f"Number({l}) <= Number({r})",
                "contains": f"String({l}).includes(String({r}))",
                "not_contains": f"!String({l}).includes(String({r}))",
                "empty": f"!String({l})", "not_empty": f"!!String({l})",
            }
            return mapping.get(op, f"String({l}) === String({r})")
        raw = data.get("condition", data.get("expression", "true"))
        if isinstance(raw, str) and "{" in raw:
            return self.resolve(raw)
        return str(raw) if raw not in (None, "") else "true"

    def _emit_branch(self, targets, exclude, processed):
        nodes = self._collect_branch_nodes(targets, exclude)
        for tid in self._topological_sort_nodes(nodes):
            if tid in self.node_map and tid not in processed:
                self._gen_node(self.node_map[tid], processed)
        for nid in nodes:
            processed.add(nid)

    def _gen_condition(self, data, nid, processed):
        expr = self._build_condition_expr(data)
        em = self.edge_map.get(nid, {})
        true_t = em.get("true", []) or em.get("condition-true", [])
        false_t = em.get("false", []) or em.get("condition-false", [])
        self.open_block(f"if ({expr}) {{")
        if true_t:
            self._emit_branch(true_t, false_t, processed)
        self.close_block()
        if false_t:
            self.open_block("else {")
            self._emit_branch(false_t, true_t, processed)
            self.close_block()

    def _gen_loop(self, data, nid, processed, is_foreach=False):
        em = self.edge_map.get(nid, {})
        body_t = em.get("loop", []) or em.get("loop-body", []) or em.get("body", []) or em.get("default", [])
        done_t = em.get("done", []) or em.get("loop-done", [])
        if is_foreach:
            lst = json.dumps(data.get("listVariable", data.get("sourceVariable", "")))
            item = json.dumps(data.get("itemVariable", "item"))
            self.open_block(f"for (const _item of (variables[{lst}] || [])) {{")
            self.add(f"variables[{item}] = _item;")
        else:
            ltype = data.get("loopType", data.get("loopMode", "count"))
            if ltype == "while":
                cond = self._build_condition_expr(data)
                self.open_block(f"while ({cond}) {{")
            else:
                count = self.resolve(data.get("count", data.get("loopCount", 1)))
                idx = json.dumps(data.get("indexVariable", "index"))
                self.open_block(f"for (let _i = 0; _i < Number({count}); _i++) {{")
                self.add(f"variables[{idx}] = _i;")
        if body_t:
            body_nodes = self._collect_loop_body_nodes(body_t, done_t)
            for tid in self._topological_sort_nodes(body_nodes):
                if tid in self.node_map and tid not in processed:
                    self._gen_node(self.node_map[tid], processed)
            for n in body_nodes:
                processed.add(n)
        self.close_block()
        for tid in done_t:
            if tid in self.node_map and tid not in processed:
                self._gen_node(self.node_map[tid], processed)


def export_workflow_to_script(workflow_data: dict, target: str = "selenium") -> str:
    """统一导出入口。target: 'selenium' | 'playwright-js'"""
    if target in ("playwright-js", "playwright_js", "js", "javascript", "node"):
        return PlaywrightJSExporter().export(workflow_data)
    return SeleniumExporter().export(workflow_data)
