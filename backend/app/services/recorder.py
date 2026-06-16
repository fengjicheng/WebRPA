# -*- coding: utf-8 -*-
"""网页智能录制器（Smart Recorder）

在浏览器页面注入监听脚本，捕获点击/输入/选择/勾选/滚动/按键/导航，计算稳定 CSS 选择器，
写入页面 sessionStorage 缓冲区；后端轮询时**排空 context 内所有页面**的缓冲并按时间合并，
因此跨页面跳转、新标签页/弹窗都能持续录制。

为什么用 sessionStorage 而非 expose_binding：
- expose_binding 的函数不保证注入到"当前已加载的文档"，会导致当前页录不到（实测回归）；
- sessionStorage 在当前已加载页面始终可用，最稳。
"""

# 录制注入脚本：监听交互，computeSelector 生成稳定选择器，写入 sessionStorage
# 关键设计：事件监听器**只挂一次**（listenersAttached 守卫，永不重复挂），
# 录制开关由 __webrpaRecorderDisabled 在 pushEvent 内部判断，避免反复注入导致重复事件。
RECORDER_SCRIPT = r"""(function () {
  var KEY = '__webrpa_rec';
  function recording() { return !window.__webrpaRecorderDisabled; }

  function pushEvent(ev) {
    if (!recording()) return;
    try {
      var arr = JSON.parse(sessionStorage.getItem(KEY) || '[]');
      var last = arr.length ? arr[arr.length - 1] : null;
      if (ev.type === 'input' && last && last.type === 'input' && last.selector === ev.selector) {
        arr[arr.length - 1] = ev;
      } else if (ev.type === 'scroll' && last && last.type === 'scroll') {
        last.dy = (last.dy || 0) + (ev.dy || 0); last.y = ev.y; last.ts = ev.ts;
      } else if (ev.type === 'navigate' && last && last.type === 'navigate' && last.url === ev.url) {
        // 跳过重复导航
      } else {
        arr.push(ev);
      }
      sessionStorage.setItem(KEY, JSON.stringify(arr));
    } catch (e) {}
  }

  function isStableClass(c) { return c && c.length < 30 && !/[0-9]{3,}|^[0-9]|--|__[a-z0-9]{4,}/.test(c); }
  function nthOfType(el) {
    var p = el.parentElement; if (!p) return 0;
    var same = Array.prototype.filter.call(p.children, function (c) { return c.tagName === el.tagName; });
    if (same.length <= 1) return 0;
    return same.indexOf(el) + 1;
  }
  function computeSelector(el) {
    if (!el || el.nodeType !== 1) return '';
    if (el.id && /^[A-Za-z][\w-]*$/.test(el.id)) {
      var byId = '#' + el.id;
      try { if (document.querySelectorAll(byId).length === 1) return byId; } catch (e) {}
    }
    var tid = el.getAttribute && (el.getAttribute('data-testid') || el.getAttribute('data-test') || el.getAttribute('data-id'));
    if (tid) { try { if (document.querySelectorAll('[data-testid="' + tid + '"]').length === 1) return '[data-testid="' + tid + '"]'; } catch (e) {} }
    if (el.getAttribute && el.getAttribute('name')) {
      var nm = el.getAttribute('name'); var byName = el.tagName.toLowerCase() + '[name="' + nm + '"]';
      try { if (document.querySelectorAll(byName).length === 1) return byName; } catch (e) {}
    }
    var parts = [], cur = el, depth = 0;
    while (cur && cur.nodeType === 1 && cur !== document.body && cur !== document.documentElement && depth < 6) {
      var tag = cur.tagName.toLowerCase(), seg = tag;
      if (cur.id && /^[A-Za-z][\w-]*$/.test(cur.id)) { parts.unshift('#' + cur.id); break; }
      var cls = (cur.className && typeof cur.className === 'string') ? cur.className.split(/\s+/).filter(isStableClass) : [];
      if (cls.length) seg += '.' + cls.slice(0, 2).join('.');
      else { var n = nthOfType(cur); if (n > 0) seg += ':nth-of-type(' + n + ')'; }
      parts.unshift(seg); cur = cur.parentElement; depth++;
    }
    return parts.join(' > ');
  }

  function ensureBadge() {
    try {
      if (recording()) {
        if (!document.getElementById('__webrpa_rec_badge')) {
          var badge = document.createElement('div');
          badge.id = '__webrpa_rec_badge';
          badge.style.cssText = 'position:fixed;top:10px;right:10px;z-index:2147483647;background:#dc2626;color:#fff;padding:6px 12px;border-radius:999px;font:600 12px sans-serif;box-shadow:0 4px 12px rgba(0,0,0,.3);pointer-events:none;display:flex;align-items:center;gap:6px;';
          badge.innerHTML = '<span style="width:8px;height:8px;border-radius:50%;background:#fff;display:inline-block;animation:wrpaBlink 1s infinite;"></span>WebRPA 录制中';
          var st = document.createElement('style'); st.textContent = '@keyframes wrpaBlink{0%,100%{opacity:1}50%{opacity:.25}}';
          (document.head || document.documentElement).appendChild(st);
          (document.body || document.documentElement).appendChild(badge);
        }
      } else {
        var b = document.getElementById('__webrpa_rec_badge'); if (b) b.remove();
      }
    } catch (e) {}
  }

  // 事件监听器只挂一次（永不重复）
  if (!window.__webrpaRecorderListenersAttached) {
    window.__webrpaRecorderListenersAttached = true;

    document.addEventListener('click', function (e) {
      var el = e.target; if (!el || el.id === '__webrpa_rec_badge') return;
      var tag = (el.tagName || '').toLowerCase();
      if (tag === 'option') return;
      pushEvent({ type: 'click', selector: computeSelector(el), tag: tag,
        text: (el.innerText || el.value || '').trim().slice(0, 60), url: location.href, ts: Date.now() });
    }, true);

    document.addEventListener('change', function (e) {
      var el = e.target; if (!el) return;
      var tag = (el.tagName || '').toLowerCase(), t = (el.type || '').toLowerCase();
      if (tag === 'select') {
        var opt = el.options[el.selectedIndex];
        pushEvent({ type: 'select', selector: computeSelector(el), value: el.value, text: opt ? opt.text : '', url: location.href, ts: Date.now() });
      } else if (tag === 'input' || tag === 'textarea') {
        if (t === 'checkbox' || t === 'radio') pushEvent({ type: 'check', selector: computeSelector(el), value: !!el.checked, url: location.href, ts: Date.now() });
        else pushEvent({ type: 'input', selector: computeSelector(el), value: el.value, url: location.href, ts: Date.now() });
      } else if (el.isContentEditable) {
        pushEvent({ type: 'input', selector: computeSelector(el), value: el.innerText, url: location.href, ts: Date.now() });
      }
    }, true);

    document.addEventListener('input', function (e) {
      var el = e.target; if (!el) return;
      var tag = (el.tagName || '').toLowerCase(), t = (el.type || '').toLowerCase();
      if ((tag === 'input' && t !== 'checkbox' && t !== 'radio') || tag === 'textarea')
        pushEvent({ type: 'input', selector: computeSelector(el), value: el.value, url: location.href, ts: Date.now() });
      else if (el.isContentEditable)
        pushEvent({ type: 'input', selector: computeSelector(el), value: el.innerText, url: location.href, ts: Date.now() });
    }, true);

    document.addEventListener('keydown', function (e) {
      var k = e.key;
      var special = ['Enter','Tab','Escape','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Backspace','Delete','Home','End','PageUp','PageDown'];
      var combo = e.ctrlKey || e.altKey || e.metaKey;
      if (special.indexOf(k) === -1 && !combo) return;
      if (k === 'Control' || k === 'Alt' || k === 'Meta' || k === 'Shift') return;
      var seq = (e.ctrlKey ? 'Control+' : '') + (e.altKey ? 'Alt+' : '') + (e.metaKey ? 'Meta+' : '') + (e.shiftKey && combo ? 'Shift+' : '') + k;
      pushEvent({ type: 'keypress', key: seq, url: location.href, ts: Date.now() });
    }, true);

    var __scrollTimer = null, __lastScrollY = window.scrollY || 0;
    window.addEventListener('scroll', function () {
      if (__scrollTimer) clearTimeout(__scrollTimer);
      __scrollTimer = setTimeout(function () {
        var y = window.scrollY || 0, dy = y - __lastScrollY; __lastScrollY = y;
        if (Math.abs(dy) < 40) return;
        pushEvent({ type: 'scroll', dy: dy, y: y, url: location.href, ts: Date.now() });
      }, 350);
    }, true);
  }

  // 每次脚本执行（页面加载/手动注入）：刷新角标 + 记录一次导航
  ensureBadge();
  pushEvent({ type: 'navigate', url: location.href, ts: Date.now() });
})();"""


_DRAIN_JS = """() => {
  try {
    var arr = JSON.parse(sessionStorage.getItem('__webrpa_rec') || '[]');
    sessionStorage.setItem('__webrpa_rec', '[]');
    return arr;
  } catch (e) { return []; }
}"""


# 模块级状态
_recorder_active = False
_recorder_init_registered = False
_init_context = None


async def _inject_all_pages(ctx):
    """对 context 内所有页面注入录制脚本。脚本内部自带"监听器只挂一次"守卫，
    重复注入安全（仅会刷新角标 + 补一条 navigate），不会产生重复监听。"""
    injected = 0
    for pg in ctx.pages:
        try:
            await pg.evaluate(RECORDER_SCRIPT)
            injected += 1
        except Exception:
            pass
    return injected


async def start_recorder() -> dict:
    """开始录制：注册 init_script（新页面自动注入）+ 立即对现有页面注入，清空各页缓冲。"""
    global _recorder_active, _recorder_init_registered, _init_context
    from app.services import browser_engine

    ctx = browser_engine.get_context()
    if ctx is None:
        return {"success": False, "error": "没有活跃浏览器，请先打开网页"}

    # context 变化（浏览器重启）需要重新注册 init_script
    if _init_context is not ctx:
        _recorder_init_registered = False
        _init_context = ctx

    if not _recorder_init_registered:
        try:
            await ctx.add_init_script(RECORDER_SCRIPT)
            _recorder_init_registered = True
        except Exception as e:
            print(f"[recorder] 注册 init_script 失败：{e}")

    # 解除禁用 + 清空各页缓冲（init_script 只影响新页面，现有页面需直接 evaluate 解除禁用）
    try:
        await ctx.add_init_script("window.__webrpaRecorderDisabled = false;")
    except Exception:
        pass
    for pg in ctx.pages:
        try:
            await pg.evaluate("() => { window.__webrpaRecorderDisabled = false; try { sessionStorage.setItem('__webrpa_rec','[]'); } catch(e){} }")
        except Exception:
            pass

    _recorder_active = True
    injected = await _inject_all_pages(ctx)
    return {"success": True, "data": {"message": f"录制已开始（覆盖 {injected} 个页面）"}}


async def _drain_all(ctx) -> list:
    """排空 context 内所有页面的 sessionStorage 缓冲，按时间排序合并。"""
    merged = []
    for pg in ctx.pages:
        try:
            arr = await pg.evaluate(_DRAIN_JS)
            if arr:
                merged.extend(arr)
        except Exception:
            pass
    merged.sort(key=lambda e: e.get("ts", 0) if isinstance(e, dict) else 0)
    return merged


async def stop_recorder() -> dict:
    """停止录制：禁用监听、移除角标，返回剩余事件。"""
    global _recorder_active
    from app.services import browser_engine

    ctx = browser_engine.get_context()
    remaining = []
    if ctx is not None:
        remaining = await _drain_all(ctx)
        for pg in ctx.pages:
            try:
                await pg.evaluate("""() => {
                    window.__webrpaRecorderActive = false;
                    window.__webrpaRecorderDisabled = true;
                    var b = document.getElementById('__webrpa_rec_badge');
                    if (b) b.remove();
                }""")
            except Exception:
                pass
        try:
            await ctx.add_init_script("window.__webrpaRecorderDisabled = true;")
        except Exception:
            pass

    _recorder_active = False
    return {"success": True, "data": {"events": remaining}}


async def drain_recorder_events() -> dict:
    """排空所有页面录制缓冲（实时轮询调用）。
    新页面/新标签页由 add_init_script 自动注入，无需在此重复注入（避免重复 navigate 事件）。"""
    from app.services import browser_engine

    ctx = browser_engine.get_context()
    if ctx is None:
        return {"success": True, "data": []}
    if not _recorder_active:
        return {"success": True, "data": []}
    data = await _drain_all(ctx)
    return {"success": True, "data": data}


def is_recorder_active() -> bool:
    return _recorder_active
