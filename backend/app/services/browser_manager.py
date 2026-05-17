"""全局浏览器管理器 - 通过 browser_engine 在主进程中共享 Playwright context"""
import asyncio
import concurrent.futures
import json
import threading
import sys
from pathlib import Path
from typing import Optional

# 用户数据目录（供外部查询）
USER_DATA_DIR = Path(__file__).parent.parent.parent / "browser_data"
USER_DATA_DIR.mkdir(exist_ok=True)

# picker 脚本（保留，供 browser_engine 或独立进程使用）
_picker_active = False


def get_user_data_dir() -> str:
    return str(USER_DATA_DIR)


# =================== 状态查询 ===================

def is_browser_open() -> bool:
    """检查浏览器引擎是否已启动"""
    try:
        from app.services import browser_engine
        return browser_engine.is_open()
    except Exception:
        return False


def get_browser_proc():
    """兼容旧接口，返回 None（不再使用子进程）"""
    return None


def get_current_browser_config() -> dict:
    try:
        from app.services import browser_engine
        return browser_engine.get_config()
    except Exception:
        return {'type': 'msedge', 'executablePath': '', 'userDataDir': None}


# =================== 启动 / 停止 ===================

def start_browser(
    browser_type: str = 'msedge',
    executable_path: Optional[str] = None,
    user_data_dir: Optional[str] = None,
    fullscreen: bool = False,
    launch_args: Optional[str] = None,
) -> tuple[bool, str]:
    """启动浏览器（在主进程 event loop 中运行）
    
    警告：sync 桥接，不要在 async 上下文中调用，会阻塞事件循环。
    """
    try:
        from app.services import browser_engine
        # 优先取当前已运行的 loop（避免 asyncio.get_event_loop 在 3.12+ 的弃用警告）
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                return False, "没有可用的事件循环"
        future = asyncio.run_coroutine_threadsafe(
            browser_engine.start(
                browser_type=browser_type,
                executable_path=executable_path,
                user_data_dir=user_data_dir,
                fullscreen=fullscreen,
                launch_args=launch_args,
            ),
            loop,
        )
        return future.result(timeout=60)
    except concurrent.futures.TimeoutError:
        return False, "启动浏览器超时（60秒）"
    except Exception as e:
        return False, str(e)


def stop_browser():
    """关闭浏览器
    
    警告：sync 桥接，不要在 async 上下文中调用。
    """
    global _picker_active
    _picker_active = False
    try:
        from app.services import browser_engine
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                return
        future = asyncio.run_coroutine_threadsafe(browser_engine.stop(), loop)
        future.result(timeout=15)
    except concurrent.futures.TimeoutError:
        print("[BrowserManager] stop_browser 超时")
    except Exception as e:
        print(f"[BrowserManager] stop_browser error: {e}")


# =================== 命令 ===================

def send_command(action: str, **kwargs) -> dict:
    """发送命令到浏览器引擎（异步转同步）
    
    警告：这个函数是 sync 桥接，会用 future.result(timeout=10) 同步等待。
    在 async 上下文中不要调用本函数（会阻塞事件循环），应直接 await 对应的 async 实现。
    """
    if not is_browser_open():
        return {"success": False, "error": "浏览器未打开"}
    try:
        from app.services import browser_engine
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                return {"success": False, "error": "没有可用的事件循环"}

        async def _run():
            if action == 'navigate':
                return await browser_engine.navigate_to(kwargs.get('url', ''))
            elif action == 'find_page_by_url':
                return await browser_engine.find_page_by_url_async(kwargs.get('url', ''))
            elif action == 'switch_to_page':
                return await browser_engine.switch_to_page_async(kwargs.get('pageIndex', 0))
            elif action == 'start_picker':
                return await _start_picker_engine()
            elif action == 'stop_picker':
                return await _stop_picker_engine()
            elif action == 'get_selected':
                return await _get_picker_result('__elementPickerResult')
            elif action == 'get_similar':
                return await _get_picker_result('__elementPickerSimilar')
            elif action == 'quit':
                await browser_engine.stop()
                return {"success": True}
            else:
                return {"success": False, "error": f"未知命令: {action}"}

        future = asyncio.run_coroutine_threadsafe(_run(), loop)
        return future.result(timeout=10)
    except concurrent.futures.TimeoutError:
        return {"success": False, "error": "浏览器命令超时（10秒）"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# =================== Picker 辅助 ===================

def _load_picker_script() -> str:
    # 直接内嵌完整版 picker 脚本（包含 Ctrl 单选、Alt 相似元素选择）
    return """
(function() {
    if (window.__elementPickerActive) {
        console.log('[ElementPicker] Already active');
        return;
    }
    window.__elementPickerActive = true;
    console.log('[ElementPicker] Initializing v2 (with similar selection)...');

    // 高亮框（鼠标悬停）
    var box = document.createElement('div');
    box.id = '__picker_box';
    box.style.cssText = 'position:fixed;pointer-events:none;border:3px solid #3b82f6;background:rgba(59,130,246,0.18);z-index:2147483647;border-radius:4px;display:none;transition:all 0.05s;';
    document.body.appendChild(box);

    // 相似元素高亮容器
    var similarBoxes = [];
    function clearSimilarBoxes() {
        similarBoxes.forEach(function(b) { try { b.remove(); } catch(e) {} });
        similarBoxes = [];
    }
    function highlightSimilar(elements) {
        clearSimilarBoxes();
        elements.forEach(function(el) {
            try {
                var r = el.getBoundingClientRect();
                var b = document.createElement('div');
                b.className = '__picker_similar_box';
                b.style.cssText = 'position:fixed;pointer-events:none;border:2px solid #f59e0b;background:rgba(245,158,11,0.18);z-index:2147483646;border-radius:3px;';
                b.style.left = r.left + 'px';
                b.style.top = r.top + 'px';
                b.style.width = r.width + 'px';
                b.style.height = r.height + 'px';
                document.body.appendChild(b);
                similarBoxes.push(b);
            } catch(e) {}
        });
    }

    // 提示条
    var tip = document.createElement('div');
    tip.id = '__picker_tip';
    tip.style.cssText = 'position:fixed;top:10px;left:50%;transform:translateX(-50%);background:#1e40af;color:white;padding:10px 20px;border-radius:8px;font-size:14px;z-index:2147483647;font-family:sans-serif;box-shadow:0 4px 12px rgba(0,0,0,0.3);';
    tip.textContent = 'Ctrl+点击选择单个元素 | Alt+点击选择相似元素';
    document.body.appendChild(tip);

    // 工具：判断是否是 picker 自身的 UI 元素
    function isPickerUI(el) {
        if (!el) return true;
        if (el === box || el === tip) return true;
        if (el.id === '__picker_box' || el.id === '__picker_tip') return true;
        if (el.className && typeof el.className === 'string' && el.className.indexOf('__picker_similar_box') !== -1) return true;
        return false;
    }

    // 转义 CSS 类名
    function cssEscape(s) {
        if (!s) return '';
        if (typeof CSS !== 'undefined' && CSS && typeof CSS.escape === 'function') {
            try { return CSS.escape(s); } catch(e) {}
        }
        return String(s).replace(/([!"#$%&'()*+,./:;<=>?@\\[\\\\\\]^`{|}~])/g, '\\\\$1');
    }

    // 生成稳定选择器
    function getSelector(el) {
        if (!el || el === document.body || el === document.documentElement) return 'body';
        if (el.id) {
            try {
                var sel = '#' + cssEscape(el.id);
                if (document.querySelectorAll(sel).length === 1) return sel;
            } catch(e) {}
        }
        if (el.className && typeof el.className === 'string') {
            var classes = el.className.trim().split(/\\s+/).filter(function(c) {
                return c && c.length < 50 && !/^(active|hover|focus|selected|disabled)$/.test(c);
            });
            for (var i = 0; i < classes.length; i++) {
                try {
                    var s = el.tagName.toLowerCase() + '.' + cssEscape(classes[i]);
                    if (document.querySelectorAll(s).length === 1) return s;
                } catch(e) {}
            }
        }
        // 路径
        var path = [];
        var current = el;
        while (current && current !== document.body && path.length < 6) {
            var tag = current.tagName.toLowerCase();
            var parent = current.parentElement;
            if (parent) {
                var siblings = Array.from(parent.children).filter(function(c) {
                    return c.tagName === current.tagName;
                });
                if (siblings.length > 1) {
                    var idx = siblings.indexOf(current) + 1;
                    tag += ':nth-of-type(' + idx + ')';
                }
            }
            path.unshift(tag);
            current = parent;
        }
        return path.join(' > ');
    }

    // 查找相似元素：先尝试同 class，再回退到同父同 tag
    function findSimilar(el) {
        var tag = el.tagName;
        var parent = el.parentElement;
        var bestList = [el];

        // 策略1：document 范围内同 tag + 主要 class
        if (el.className && typeof el.className === 'string') {
            var classes = el.className.trim().split(/\\s+/).filter(function(c) {
                return c && c.length < 50 && !/^(active|hover|focus|selected|disabled)$/.test(c);
            });
            for (var i = 0; i < classes.length; i++) {
                try {
                    var sel = tag.toLowerCase() + '.' + cssEscape(classes[i]);
                    var found = Array.from(document.querySelectorAll(sel));
                    if (found.length > 1 && found.length <= 200) {
                        bestList = found;
                        break;
                    }
                } catch(e) {}
            }
        }
        // 策略2：同父同 tag
        if (bestList.length <= 1 && parent) {
            var sib = Array.from(parent.children).filter(function(c) {
                return c.tagName === tag;
            });
            if (sib.length > 1) bestList = sib;
        }
        return bestList;
    }

    // 生成相似元素的 pattern（含 {index}）
    function buildSimilarPattern(el, list) {
        var tag = el.tagName.toLowerCase();
        // 优先：document 内同 tag+class 完全匹配 list
        if (el.className && typeof el.className === 'string') {
            var classes = el.className.trim().split(/\\s+/).filter(function(c) {
                return c && c.length < 50 && !/^(active|hover|focus|selected|disabled)$/.test(c);
            });
            for (var i = 0; i < classes.length; i++) {
                try {
                    var sel = tag + '.' + cssEscape(classes[i]);
                    var f = Array.from(document.querySelectorAll(sel));
                    if (f.length === list.length) {
                        // 使用 :nth-of-type 不一定准确，使用 nth-match 模拟：用 :nth-child 序号 -> 对单 selector 难表达
                        // 使用 (sel):nth-of-type({index}) 形式 - 对 jQuery/Playwright 都不通用
                        // 改为返回 sel 加上 [data-index='{index}'] 占位 - 不可行
                        // 这里使用 ":nth-match" 不是标准, 还是用父+nth-of-type
                        break;
                    }
                } catch(e) {}
            }
        }
        // 通用：父 + nth-of-type({index})
        var parent = el.parentElement;
        if (parent) {
            var parentSel = getSelector(parent);
            return parentSel + ' > ' + tag + ':nth-of-type({index})';
        }
        return tag + ':nth-of-type({index})';
    }

    // 鼠标移动高亮
    document.addEventListener('mousemove', function(e) {
        var el = document.elementFromPoint(e.clientX, e.clientY);
        if (isPickerUI(el)) return;
        if (!el) return;
        var r = el.getBoundingClientRect();
        box.style.display = 'block';
        box.style.left = r.left + 'px';
        box.style.top = r.top + 'px';
        box.style.width = r.width + 'px';
        box.style.height = r.height + 'px';
    }, true);

    // 点击选择
    document.addEventListener('click', function(e) {
        if (!e.ctrlKey && !e.altKey) return;
        e.preventDefault();
        e.stopPropagation();
        if (e.stopImmediatePropagation) e.stopImmediatePropagation();

        var el = document.elementFromPoint(e.clientX, e.clientY);
        if (!el || isPickerUI(el)) return;

        if (e.altKey) {
            // 相似元素
            var list = findSimilar(el);
            var pattern = buildSimilarPattern(el, list);
            highlightSimilar(list);

            window.__elementPickerSimilar = {
                pattern: pattern,
                count: list.length,
                indices: list.map(function(_, i) { return i + 1; }),
                minIndex: 1,
                maxIndex: list.length,
                selector1: getSelector(list[0]),
                selector2: list.length > 1 ? getSelector(list[1]) : ''
            };
            tip.textContent = '已选择 ' + list.length + ' 个相似元素';
            tip.style.background = '#059669';
            console.log('[ElementPicker] Similar:', pattern, 'count:', list.length);
        } else if (e.ctrlKey) {
            var sel = getSelector(el);
            var rect = el.getBoundingClientRect();
            var attrs = {};
            try {
                Array.from(el.attributes).forEach(function(a) { attrs[a.name] = a.value; });
            } catch(_) {}
            window.__elementPickerResult = {
                selector: sel,
                tagName: el.tagName.toLowerCase(),
                text: ((el.innerText || el.textContent || '') + '').substring(0, 100).trim(),
                attributes: attrs,
                rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
            };
            tip.textContent = '已选择: ' + sel;
            tip.style.background = '#059669';
            console.log('[ElementPicker] Selected:', sel);
        }
    }, true);

    console.log('[ElementPicker] Ready!');
})();
"""


PICKER_SCRIPT = _load_picker_script()


async def _start_picker_engine() -> dict:
    global _picker_active
    from app.services import browser_engine
    pg = browser_engine.get_page()
    if pg is None:
        return {"success": False, "error": "没有活跃页面"}
    try:
        await pg.evaluate(PICKER_SCRIPT)
        _picker_active = True
        return {"success": True, "data": {"message": "选择器已启动"}}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _stop_picker_engine() -> dict:
    global _picker_active
    from app.services import browser_engine
    _picker_active = False
    ctx = browser_engine.get_context()
    if ctx:
        for pg in ctx.pages:
            try:
                await pg.evaluate("""
                    () => {
                        ['__picker_tip','__picker_box'].forEach(id => {
                            var el = document.getElementById(id);
                            if (el) el.remove();
                        });
                        document.querySelectorAll('.__picker_similar_box').forEach(el => el.remove());
                        window.__elementPickerActive = false;
                        window.__elementPickerResult = null;
                        window.__elementPickerSimilar = null;
                    }
                """)
            except Exception:
                pass
    return {"success": True, "data": {"message": "选择器已停止"}}


async def _get_picker_result(key: str) -> dict:
    from app.services import browser_engine
    pg = browser_engine.get_page()
    if pg is None:
        return {"success": True, "data": None}
    try:
        data = await pg.evaluate(f"""
            () => {{
                var r = window.{key};
                window.{key} = null;
                return r;
            }}
        """)
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


# =================== 便捷函数 ===================

def navigate(url: str) -> dict:
    return send_command("navigate", url=url)


def start_picker() -> dict:
    result = send_command("start_picker")
    return result


def stop_picker() -> dict:
    result = send_command("stop_picker")
    return result


def get_selected_element() -> dict:
    return send_command("get_selected")


def get_similar_elements() -> dict:
    return send_command("get_similar")


def is_picker_active() -> bool:
    return _picker_active


def find_page_by_url(url: str) -> dict:
    return send_command("find_page_by_url", url=url)


def switch_to_page(page_index: int) -> dict:
    return send_command("switch_to_page", pageIndex=page_index)


def ensure_browser_open(
    browser_type: str = 'msedge',
    executable_path: Optional[str] = None,
    fullscreen: bool = False,
) -> bool:
    from app.services import browser_engine
    if browser_engine.is_open():
        cfg = browser_engine.get_config()
        if (cfg.get('type') == browser_type and
                cfg.get('executablePath', '') == (executable_path or '') and
                True):
            return True
        # 配置变化，先停止
        stop_browser()
    success, _ = start_browser(browser_type, executable_path, None, fullscreen)
    return success
