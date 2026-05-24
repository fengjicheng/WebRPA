"""WebRPA 元素选择器统一注入脚本（共享给所有 picker 入口）

支持：
- Ctrl+点击：选中单个元素，输出稳定 selector
- Alt+点击两次：第一次记样本 A，第二次拿样本 B，对两者做路径对比，
  把唯一不同那一段替换成 {index} 生成相似选择器；适用于卡片/列表/分类标签等重复结构
- window.__elementPickerDisabled 标志：让外层 stop 后即便脚本被 init_script 重新注入也能立刻退出
- 跨页面：本脚本被 BrowserContext.add_init_script 注册后，
  所有跳转/新开 tab/iframe 主文档都会自动重新注入
"""

PICKER_SCRIPT = r"""(function() {
    if (window.__elementPickerDisabled === true) {
        // 用户已主动停止 picker，即便 init_script 在新页面重新跑也立刻退出
        return;
    }
    if (window.__elementPickerActive) return;
    window.__elementPickerActive = true;

    // ===== UI 元素 =====
    var box = document.createElement('div');
    box.id = '__picker_box';
    box.style.cssText = 'position:fixed;pointer-events:none;border:3px solid #3b82f6;background:rgba(59,130,246,0.18);z-index:2147483647;border-radius:4px;display:none;transition:all 0.05s;';

    var firstBox = document.createElement('div');
    firstBox.id = '__picker_first_box';
    firstBox.style.cssText = 'position:fixed;pointer-events:none;border:3px dashed #f59e0b;background:rgba(245,158,11,0.18);z-index:2147483646;border-radius:4px;display:none;';

    var tip = document.createElement('div');
    tip.id = '__picker_tip';
    tip.style.cssText = 'position:fixed;top:10px;left:50%;transform:translateX(-50%);background:#1e40af;color:white;padding:10px 20px;border-radius:8px;font-size:14px;z-index:2147483647;font-family:sans-serif;box-shadow:0 4px 12px rgba(0,0,0,0.3);';
    tip.textContent = 'Ctrl+点击：选 1 个元素 | Alt+点击两次：分别点击两个相似元素';

    function attachUI() {
        if (!document.body) return;
        if (!box.isConnected) document.body.appendChild(box);
        if (!firstBox.isConnected) document.body.appendChild(firstBox);
        if (!tip.isConnected) document.body.appendChild(tip);
    }
    if (document.body) attachUI();
    else document.addEventListener('DOMContentLoaded', attachUI);

    // 相似元素高亮容器
    var similarBoxes = [];
    function clearSimilar() {
        similarBoxes.forEach(function(b) { try { b.remove(); } catch (e) {} });
        similarBoxes = [];
    }
    function highlightSimilar(elements) {
        clearSimilar();
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
            } catch (e) {}
        });
    }

    function isPickerUI(el) {
        if (!el) return true;
        if (el === box || el === tip || el === firstBox) return true;
        var id = el.id || '';
        if (id === '__picker_box' || id === '__picker_tip' || id === '__picker_first_box') return true;
        if (el.className && typeof el.className === 'string' && el.className.indexOf('__picker_similar_box') !== -1) return true;
        return false;
    }

    function cssEscape(s) {
        if (!s) return '';
        if (typeof CSS !== 'undefined' && CSS && typeof CSS.escape === 'function') {
            try { return CSS.escape(s); } catch (e) {}
        }
        return String(s).replace(/[^a-zA-Z0-9_-]/g, function(c) { return '\\' + c; });
    }
"""

PICKER_SCRIPT += r"""
    // ===== 路径采样：把元素到 root 之间的每一层抓取下来，含 tag/id/class/nthChild =====
    function getPath(el) {
        var path = [];
        var current = el;
        while (current && current !== document.body && current !== document.documentElement) {
            var p = current.parentElement;
            var nthChild = p ? Array.prototype.indexOf.call(p.children, current) + 1 : 0;
            var sameTag = p ? Array.prototype.filter.call(p.children, function(c) { return c.tagName === current.tagName; }) : [];
            var nthOfType = sameTag.length > 1 ? sameTag.indexOf(current) + 1 : 0;
            var classes = (current.className && typeof current.className === 'string')
                ? current.className.trim().split(/\s+/).filter(function(c) {
                    return c && c.length < 50 && !/^(active|hover|focus|selected|disabled|on|is-)/i.test(c);
                })
                : [];
            path.unshift({
                tag: current.tagName,
                id: current.id || '',
                classes: classes,
                nthChild: nthChild,
                nthOfType: nthOfType,
                el: current
            });
            current = p;
        }
        return path;
    }

    // 单元素稳定 selector
    function getSelector(el) {
        if (!el || el === document.body || el === document.documentElement) return 'body';
        if (el.id) {
            try {
                var idSel = '#' + cssEscape(el.id);
                if (document.querySelectorAll(idSel).length === 1) return idSel;
            } catch (e) {}
        }
        if (el.className && typeof el.className === 'string') {
            var classes = el.className.trim().split(/\s+/).filter(function(c) {
                return c && c.length < 50 && !/^(active|hover|focus|selected|disabled)$/.test(c);
            });
            for (var i = 0; i < classes.length; i++) {
                try {
                    var sel = el.tagName.toLowerCase() + '.' + cssEscape(classes[i]);
                    if (document.querySelectorAll(sel).length === 1) return sel;
                } catch (e) {}
            }
        }
        var path = getPath(el);
        var parts = [];
        var startIdx = 0;
        for (var k = 0; k < path.length; k++) {
            if (path[k].id) { startIdx = k; break; }
        }
        for (var j = startIdx; j < path.length; j++) {
            var n = path[j];
            if (n.id) parts.push('#' + cssEscape(n.id));
            else if (n.classes.length > 0) parts.push(n.tag.toLowerCase() + '.' + cssEscape(n.classes[0]));
            else if (n.nthOfType > 0) parts.push(n.tag.toLowerCase() + ':nth-of-type(' + n.nthOfType + ')');
            else parts.push(n.tag.toLowerCase());
        }
        return parts.join(' > ');
    }
"""

PICKER_SCRIPT += r"""
    // ===== 两点采样：把 A、B 两个元素的 path 对齐对比 =====
    // 返回 { pattern: 含 {index} 的 selector, elements: 命中元素数组, indices: 每个元素对应的索引值 }
    function findSimilarFromTwo(a, b) {
        if (!a || !b) return null;
        if (a === b) return null;
        if (a.tagName !== b.tagName) return null;

        var pa = getPath(a), pb = getPath(b);
        if (pa.length !== pb.length) return null;

        // 找到唯一不同的层级，要求每层 tag 必须一致
        var diffIdx = -1;
        for (var i = 0; i < pa.length; i++) {
            if (pa[i].tag !== pb[i].tag) return null;
            if (pa[i].nthChild !== pb[i].nthChild) {
                if (diffIdx >= 0) return null;  // 多于一层不同，无法用单 {index} 表达
                diffIdx = i;
            }
        }
        if (diffIdx < 0) return null;

        // 从最近的有 id 的祖先开始，作为绝对锚点
        var startIdx = 0;
        for (var k = 0; k <= diffIdx; k++) {
            if (pa[k].id) { startIdx = k; break; }
        }

        // 构建 selector：固定层用 tag.class 或 tag:nth-child(n)，不同那一层用 {index}
        var parts = [];
        for (var j = startIdx; j < pa.length; j++) {
            var n = pa[j];
            if (n.id) {
                parts.push('#' + cssEscape(n.id));
                continue;
            }
            if (j === diffIdx) {
                // 不同的层：用共有 className 优先；否则 tag:nth-child({index})
                var commonClasses = pa[j].classes.filter(function(c) {
                    return pb[j].classes.indexOf(c) >= 0;
                });
                if (commonClasses.length > 0) {
                    parts.push(n.tag.toLowerCase() + '.' + cssEscape(commonClasses[0]) + ':nth-child({index})');
                } else {
                    parts.push(n.tag.toLowerCase() + ':nth-child({index})');
                }
                continue;
            }
            // 固定层：优先 className（结构更稳），否则 nth-of-type
            if (n.classes.length > 0 && pa[j].classes[0] === pb[j].classes[0]) {
                parts.push(n.tag.toLowerCase() + '.' + cssEscape(n.classes[0]));
            } else if (n.nthOfType > 0) {
                parts.push(n.tag.toLowerCase() + ':nth-of-type(' + n.nthOfType + ')');
            } else {
                parts.push(n.tag.toLowerCase());
            }
        }
        var pattern = parts.join(' > ');

        // 找出所有兄弟元素：在 diffIdx 层的父节点下，所有同 tag 的同辈
        var diffParent = pa[diffIdx].el.parentElement;
        var sameTagSibs = diffParent ? Array.prototype.filter.call(diffParent.children, function(c) {
            return c.tagName === pa[diffIdx].tag;
        }) : [];

        // 对每个 sibling，重建从 diffIdx 之后那段路径，定位到对应叶子
        var elements = [];
        var indices = [];
        for (var s = 0; s < sameTagSibs.length; s++) {
            var sib = sameTagSibs[s];
            var cur = sib;
            var ok = true;
            for (var d = diffIdx + 1; d < pa.length && cur; d++) {
                var info = pa[d];
                var children = Array.prototype.filter.call(cur.children, function(c) { return c.tagName === info.tag; });
                if (children.length === 0) { ok = false; break; }
                // 用 nthOfType 在子节点中定位（A 路径作模板）
                var idx = info.nthOfType > 0 ? Math.min(info.nthOfType, children.length) - 1 : 0;
                cur = children[idx];
            }
            if (ok && cur) {
                elements.push(cur);
                // 真实 nth-child 序号
                var realIdx = Array.prototype.indexOf.call(diffParent.children, sib) + 1;
                indices.push(realIdx);
            }
        }

        if (elements.length < 2) return null;

        return { pattern: pattern, elements: elements, indices: indices };
    }
"""

PICKER_SCRIPT += r"""
    // ===== 鼠标事件 =====
    var firstSample = null;
    var firstSampleTime = 0;

    function setFirstSampleBox(el) {
        if (!el) {
            firstBox.style.display = 'none';
            return;
        }
        var r = el.getBoundingClientRect();
        firstBox.style.left = r.left + 'px';
        firstBox.style.top = r.top + 'px';
        firstBox.style.width = r.width + 'px';
        firstBox.style.height = r.height + 'px';
        firstBox.style.display = 'block';
    }

    document.addEventListener('mousemove', function(e) {
        if (window.__elementPickerDisabled === true) return;
        var el = document.elementFromPoint(e.clientX, e.clientY);
        if (!el || isPickerUI(el)) return;
        var r = el.getBoundingClientRect();
        box.style.display = 'block';
        box.style.left = r.left + 'px';
        box.style.top = r.top + 'px';
        box.style.width = r.width + 'px';
        box.style.height = r.height + 'px';
        if (e.altKey) {
            box.style.borderColor = '#f59e0b';
            box.style.background = 'rgba(245,158,11,0.18)';
        } else {
            box.style.borderColor = '#3b82f6';
            box.style.background = 'rgba(59,130,246,0.18)';
        }
    }, true);

    document.addEventListener('click', function(e) {
        if (window.__elementPickerDisabled === true) return;
        if (!e.ctrlKey && !e.altKey) return;
        e.preventDefault();
        e.stopPropagation();
        if (e.stopImmediatePropagation) e.stopImmediatePropagation();

        var el = document.elementFromPoint(e.clientX, e.clientY);
        if (!el || isPickerUI(el)) return;

        if (e.altKey) {
            var now = Date.now();
            // 30 秒后样本 A 自动失效
            if (firstSample && (now - firstSampleTime) > 30000) {
                firstSample = null;
            }

            if (!firstSample || firstSample === el) {
                firstSample = el;
                firstSampleTime = now;
                setFirstSampleBox(el);
                tip.textContent = '已记录第 1 个样本，请 Alt+点击第 2 个相似元素（30 秒内）';
                tip.style.background = '#d97706';
                return;
            }

            // 第 2 次：进行两点采样推断
            var sampleA = firstSample;
            var sampleB = el;
            firstSample = null;
            setFirstSampleBox(null);

            var result = findSimilarFromTwo(sampleA, sampleB);
            if (!result || result.elements.length < 2) {
                tip.textContent = '无法识别相似模式，两个元素结构不一致或层级不同';
                tip.style.background = '#dc2626';
                clearSimilar();
                return;
            }

            highlightSimilar(result.elements);
            window.__elementPickerSimilar = {
                pattern: result.pattern,
                count: result.elements.length,
                indices: result.indices,
                minIndex: result.indices.length > 0 ? Math.min.apply(null, result.indices) : 1,
                maxIndex: result.indices.length > 0 ? Math.max.apply(null, result.indices) : result.elements.length,
                selector1: getSelector(sampleA),
                selector2: getSelector(sampleB)
            };
            tip.textContent = '已识别 ' + result.elements.length + ' 个相似元素：' + result.pattern.slice(0, 60);
            tip.style.background = '#059669';
        } else if (e.ctrlKey) {
            var sel = getSelector(el);
            var rect = el.getBoundingClientRect();
            var attrs = {};
            try {
                Array.prototype.forEach.call(el.attributes, function(a) { attrs[a.name] = a.value; });
            } catch (_) {}
            window.__elementPickerResult = {
                selector: sel,
                tagName: el.tagName.toLowerCase(),
                text: ((el.innerText || el.textContent || '') + '').substring(0, 100).trim(),
                attributes: attrs,
                rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
            };
            tip.textContent = '已选择: ' + sel.slice(0, 80);
            tip.style.background = '#059669';
        }
    }, true);
})();
"""
