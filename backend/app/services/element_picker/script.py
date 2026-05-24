"""元素选择器注入脚本"""

PICKER_SCRIPT = """(function() {
    // 防止重复注入
    if (window.__elementPickerActive) {
        console.log('[ElementPicker] Already active');
        return;
    }
    window.__elementPickerActive = true;
    console.log('[ElementPicker] Initializing...');
    
    // 创建高亮框
    var box = document.createElement('div');
    box.id = '__element_picker_box';
    box.style.cssText = 'position:fixed;pointer-events:none;border:3px solid #3b82f6;background:rgba(59,130,246,0.2);z-index:2147483647;border-radius:4px;display:none;transition:all 0.1s;';
    document.body.appendChild(box);
    
    // 创建提示条
    var tip = document.createElement('div');
    tip.id = '__element_picker_tip';
    tip.style.cssText = 'position:fixed;top:10px;left:50%;transform:translateX(-50%);background:#1e40af;color:white;padding:10px 20px;border-radius:8px;font-size:14px;z-index:2147483647;font-family:sans-serif;box-shadow:0 4px 12px rgba(0,0,0,0.3);';
    tip.textContent = 'Ctrl+点击：选 1 个元素 | Alt+点击两次：第 1 次定样本，第 2 次推断相似元素';
    document.body.appendChild(tip);
    
    console.log('[ElementPicker] UI created');
    
    // 生成选择器
    function getSelector(el) {
        if (!el || el === document.body || el === document.documentElement) {
            return 'body';
        }
        
        // 优先使用 id
        if (el.id) {
            return '#' + el.id;
        }
        
        // 使用 class
        if (el.className && typeof el.className === 'string') {
            var classes = el.className.trim().split(/\\s+/);
            for (var i = 0; i < classes.length; i++) {
                if (classes[i] && classes[i].length < 50) {
                    var sel = el.tagName.toLowerCase() + '.' + classes[i];
                    try {
                        if (document.querySelectorAll(sel).length === 1) {
                            return sel;
                        }
                    } catch(e) {}
                }
            }
        }

        // 使用路径
        var path = [];
        var current = el;
        while (current && current !== document.body && path.length < 5) {
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
    
    // 查找相似元素（多策略：先按 className 匹配，再按 tag + 父级结构，最后按 tag 同辈）
    function findSimilar(el) {
        if (!el || el === document.documentElement || el === document.body) return [el];

        var tag = el.tagName;
        var classList = (el.className && typeof el.className === 'string')
            ? el.className.trim().split(/\s+/).filter(function(c) { return c && !/^(active|hover|selected|focus|current)/i.test(c); })
            : [];

        // 策略 1：相同主要 className 的全局元素（最准确）
        if (classList.length > 0) {
            for (var i = 0; i < classList.length; i++) {
                var cls = classList[i];
                if (cls.length < 2) continue;
                try {
                    var nodes = document.querySelectorAll(tag.toLowerCase() + '.' + CSS.escape(cls));
                    if (nodes.length >= 2 && nodes.length <= 200) {
                        return Array.from(nodes);
                    }
                } catch (err) {}
            }
        }

        // 策略 2：父元素下相同 tag（原始逻辑）
        var parent = el.parentElement;
        if (parent) {
            var siblings = Array.from(parent.children).filter(function(c) {
                return c.tagName === tag;
            });
            if (siblings.length >= 2 && siblings.length <= 200) {
                return siblings;
            }
        }

        // 策略 3：祖父元素下，同 tag + 类似嵌套深度（处理 <div><a/></div><div><a/></div>）
        var grand = parent && parent.parentElement;
        if (grand) {
            var pTag = parent.tagName;
            var cousinParents = Array.from(grand.children).filter(function(c) {
                return c.tagName === pTag;
            });
            var cousins = [];
            for (var k = 0; k < cousinParents.length; k++) {
                var matched = cousinParents[k].querySelector(tag.toLowerCase());
                if (matched) cousins.push(matched);
            }
            if (cousins.length >= 2 && cousins.length <= 200) {
                return cousins;
            }
        }

        // 策略 4：相同 role 属性
        if (el.getAttribute('role')) {
            try {
                var byRole = document.querySelectorAll(tag.toLowerCase() + '[role="' + el.getAttribute('role') + '"]');
                if (byRole.length >= 2 && byRole.length <= 200) {
                    return Array.from(byRole);
                }
            } catch (err) {}
        }

        return [el];
    }

    // ===== 两点采样：根据 A、B 两个样本元素推断"重复模式" =====

    // 取祖先链（含自身），从 root 到自身排序
    function getAncestors(el) {
        var arr = [];
        var c = el;
        while (c && c !== document.body && c !== document.documentElement) {
            arr.unshift(c);
            c = c.parentElement;
        }
        return arr;
    }

    // 找两元素的最低公共祖先
    function lowestCommonAncestor(a, b) {
        var pa = new Set();
        var c = a;
        while (c) { pa.add(c); c = c.parentElement; }
        c = b;
        while (c) {
            if (pa.has(c)) return c;
            c = c.parentElement;
        }
        return document.body;
    }

    // 给定两个元素，提取它们共有的 class（用于全局匹配 selector）
    function commonClasses(a, b) {
        function listOf(el) {
            return (el.className && typeof el.className === 'string')
                ? el.className.trim().split(/\s+/).filter(function(c) {
                    return c && !/^(active|hover|selected|focus|current|on|is-)/i.test(c) && c.length > 1;
                })
                : [];
        }
        var la = listOf(a), lb = new Set(listOf(b));
        return la.filter(function(c) { return lb.has(c); });
    }

    // 从两个样本元素推断完整的相似元素集合
    function findSimilarFromTwo(a, b) {
        if (!a || !b) return null;
        if (a === b) return [a];
        if (a.tagName !== b.tagName) return null;

        var tag = a.tagName.toLowerCase();

        // 策略 A：两元素共有的 className → 全局匹配
        var common = commonClasses(a, b);
        for (var i = 0; i < common.length; i++) {
            var cls = common[i];
            try {
                var nodes = document.querySelectorAll(tag + '.' + CSS.escape(cls));
                if (nodes.length >= 2 && nodes.length <= 500
                    && Array.prototype.indexOf.call(nodes, a) >= 0
                    && Array.prototype.indexOf.call(nodes, b) >= 0) {
                    return { items: Array.from(nodes), pattern: tag + '.' + CSS.escape(cls), strategy: 'common-class' };
                }
            } catch (err) {}
        }

        // 策略 B：找 LCA，把 a、b 投影到 LCA 直接子节点的层（卡片型重复结构）
        var lca = lowestCommonAncestor(a, b);
        if (lca && lca !== document.body) {
            var aChain = getAncestors(a), bChain = getAncestors(b);
            var aIdx = aChain.indexOf(lca), bIdx = bChain.indexOf(lca);
            // a/b 在 LCA 之下的"第一个分叉子节点"
            var aProj = aChain[aIdx + 1], bProj = bChain[bIdx + 1];
            if (aProj && bProj && aProj !== bProj && aProj.tagName === bProj.tagName) {
                // 收集 LCA 下所有同 tag 的兄弟，从中挑出与 aProj 类结构相似的
                var siblings = Array.from(lca.children).filter(function(c) {
                    return c.tagName === aProj.tagName;
                });
                if (siblings.length >= 2 && siblings.length <= 500
                    && siblings.indexOf(aProj) >= 0 && siblings.indexOf(bProj) >= 0) {
                    // 共有 className 进一步精确化
                    var projCommon = commonClasses(aProj, bProj);
                    if (projCommon.length > 0) {
                        for (var j = 0; j < projCommon.length; j++) {
                            var pc = projCommon[j];
                            var matched = siblings.filter(function(s) {
                                return s.classList && s.classList.contains(pc);
                            });
                            if (matched.length >= 2 && matched.indexOf(aProj) >= 0 && matched.indexOf(bProj) >= 0) {
                                // 现在 matched 是父级容器层的列表，需要把 a、b 在容器内的相对路径还原
                                var mapped = mapItemsByRelativePath(matched, aProj, a, bProj, b);
                                if (mapped) return { items: mapped, pattern: 'lca-relative', strategy: 'lca-class' };
                                return { items: matched, pattern: 'lca-tag', strategy: 'lca-class-only' };
                            }
                        }
                    }
                    var mapped2 = mapItemsByRelativePath(siblings, aProj, a, bProj, b);
                    if (mapped2) return { items: mapped2, pattern: 'lca-relative', strategy: 'lca-tag' };
                    return { items: siblings, pattern: 'lca-tag', strategy: 'lca-tag-only' };
                }
            }
        }

        return null;
    }

    // 给定 LCA 下的容器列表（containers），以及两组样本 (containerA→leafA, containerB→leafB)，
    // 推断"从容器到 leaf 的相对路径"，再批量映射到所有 container 上得到完整 leaf 列表
    function mapItemsByRelativePath(containers, contA, leafA, contB, leafB) {
        function relPath(cont, leaf) {
            var path = [];
            var c = leaf;
            while (c && c !== cont) {
                var p = c.parentElement;
                if (!p) return null;
                var sameTag = Array.prototype.filter.call(p.children, function(s) { return s.tagName === c.tagName; });
                var idx = sameTag.indexOf(c);
                path.unshift({ tag: c.tagName, idx: idx, total: sameTag.length });
                c = p;
            }
            return path;
        }
        var pa = relPath(contA, leafA), pb = relPath(contB, leafB);
        if (!pa || !pb || pa.length !== pb.length) return null;
        // 路径必须 tag 完全一致（每层），idx 可不同（兼容多个相同结构卡片中"子项位置"略有差异）
        for (var i = 0; i < pa.length; i++) {
            if (pa[i].tag !== pb[i].tag) return null;
        }
        // 用第一组路径作为模板批量取
        var results = [];
        for (var k = 0; k < containers.length; k++) {
            var cur = containers[k];
            var ok = true;
            for (var d = 0; d < pa.length && cur; d++) {
                var sameTag = Array.prototype.filter.call(cur.children, function(s) { return s.tagName === pa[d].tag; });
                if (sameTag.length === 0) { ok = false; break; }
                // 优先用 a 路径的 idx；越界则用最后一个
                var idx = Math.min(pa[d].idx, sameTag.length - 1);
                cur = sameTag[idx];
            }
            if (ok && cur) results.push(cur);
        }
        if (results.length >= 2) return results;
        return null;
    }

    // 给定一组相似元素，生成最佳 CSS selector 模式
    function buildSimilarSelector(el, similar, sampleB) {
        if (similar.length <= 1) return getSelector(el);

        var classList = (el.className && typeof el.className === 'string')
            ? el.className.trim().split(/\s+/).filter(function(c) { return c && !/^(active|hover|selected|focus|current)/i.test(c); })
            : [];

        // 优先用 className（短而精）
        // 如果传入了第二个样本，优先用 A、B 共有 className
        if (sampleB) {
            var common = commonClasses(el, sampleB);
            for (var c = 0; c < common.length; c++) {
                try {
                    var sel0 = el.tagName.toLowerCase() + '.' + CSS.escape(common[c]);
                    var hits0 = document.querySelectorAll(sel0);
                    if (hits0.length === similar.length) {
                        return sel0;
                    }
                } catch (err) {}
            }
        }
        for (var i = 0; i < classList.length; i++) {
            var cls = classList[i];
            if (cls.length < 2) continue;
            try {
                var sel = el.tagName.toLowerCase() + '.' + CSS.escape(cls);
                var hits = document.querySelectorAll(sel);
                if (hits.length === similar.length) {
                    // 用 :nth-of-type 兼容，大多数 RPA 引擎更熟
                    return sel;
                }
            } catch (err) {}
        }

        // 退而求其次：parent + nth-of-type
        var parent = el.parentElement;
        if (parent) {
            var parentSel = getSelector(parent);
            var tag = el.tagName.toLowerCase();
            return parentSel + ' > ' + tag + ':nth-of-type({index})';
        }
        return getSelector(el);
    }
    
    // 鼠标移动高亮
    document.addEventListener('mousemove', function(e) {
        var el = document.elementFromPoint(e.clientX, e.clientY);
        if (!el || el === tip || el === box || el.id === '__element_picker_tip' || el.id === '__element_picker_box') {
            return;
        }
        var rect = el.getBoundingClientRect();
        box.style.left = rect.left + 'px';
        box.style.top = rect.top + 'px';
        box.style.width = rect.width + 'px';
        box.style.height = rect.height + 'px';
        box.style.display = 'block';
    }, true);
    
    // 点击选择
    document.addEventListener('click', function(e) {
        // 只响应 Ctrl 或 Alt 点击
        if (!e.ctrlKey && !e.altKey) {
            return;
        }
        
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        
        var el = document.elementFromPoint(e.clientX, e.clientY);
        if (!el || el === tip || el === box) {
            return;
        }
        
        console.log('[ElementPicker] Click detected, ctrl:', e.ctrlKey, 'alt:', e.altKey);
        
        if (e.altKey) {
            // Alt+点击：两次采样选择相似元素
            // 第一次 Alt+点击 → 暂存样本 A，提示用户再点第二个
            // 第二次 Alt+点击 → 用 A、B 推断完整重复模式（最准）
            // 若用户长时间未点第二个或主动按 Esc，退化为单点猜测
            var now = Date.now();
            var stash = window.__elementPickerSampleA;
            // 30 秒后自动失效
            if (stash && (now - stash.time) > 30000) stash = null;

            if (!stash || stash.el === el) {
                // 第一次：先存样本 A，并给元素加个虚框提示用户
                window.__elementPickerSampleA = { el: el, time: now };
                tip.textContent = '已选第 1 个样本，请 Alt+点击第 2 个相似元素（30 秒内）';
                tip.style.background = '#0ea5e9';
                box.style.borderColor = '#f59e0b';
                box.style.background = 'rgba(245,158,11,0.25)';
                console.log('[ElementPicker] Sample A locked:', el);
            } else {
                // 第二次：根据 A、B 推断
                var sampleA = stash.el;
                window.__elementPickerSampleA = null;
                box.style.borderColor = '#3b82f6';
                box.style.background = 'rgba(59,130,246,0.2)';

                var inferred = findSimilarFromTwo(sampleA, el);
                var similar, selector;
                if (inferred && inferred.items.length >= 2) {
                    similar = inferred.items;
                    selector = buildSimilarSelector(sampleA, similar, el);
                    console.log('[ElementPicker] Two-sample inference:', inferred.strategy, 'count:', similar.length);
                } else {
                    // 推断失败 → 退化为单点猜
                    similar = findSimilar(el);
                    selector = buildSimilarSelector(el, similar);
                    console.log('[ElementPicker] Two-sample failed, fallback to single:', similar.length);
                }

                window.__elementPickerSimilar = {
                    pattern: selector,
                    count: similar.length,
                    indices: similar.map(function(s, i) { return i + 1; }),
                    minIndex: 1,
                    maxIndex: similar.length
                };

                tip.textContent = '已识别 ' + similar.length + ' 个相似元素';
                tip.style.background = '#059669';
            }
        } else if (e.ctrlKey) {
            // Ctrl+点击：选择单个元素
            var selector = getSelector(el);
            var rect = el.getBoundingClientRect();
            
            window.__elementPickerResult = {
                selector: selector,
                tagName: el.tagName.toLowerCase(),
                text: (el.textContent || '').substring(0, 100).trim(),
                attributes: { id: el.id || '', className: el.className || '' },
                rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
            };
            
            tip.textContent = '已选择: ' + selector;
            tip.style.background = '#059669';
            console.log('[ElementPicker] Element selected:', selector);
        }
    }, true);
    
    console.log('[ElementPicker] Ready!');
})();"""
