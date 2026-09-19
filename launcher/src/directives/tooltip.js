// WebRPA 启动器自定义 Tooltip 指令
// 用法：v-tooltip="'文本'" 或者只写 title 属性也会被自动拦截
// 设计：单例 DOM，鼠标 hover 元素显示，移开消失，无任何浏览器原生 tooltip

let tipEl = null
let showTimer = null

function ensureTipEl() {
  if (tipEl) return tipEl
  tipEl = document.createElement('div')
  tipEl.className = 'webrpa-tooltip'
  tipEl.setAttribute('role', 'tooltip')
  tipEl.style.cssText = [
    'position:fixed',
    'z-index:99999',
    'pointer-events:none',
    'opacity:0',
    'transform:translate(-50%, 4px) scale(0.96)',
    'transition:opacity 140ms ease, transform 180ms cubic-bezier(0.34, 1.56, 0.64, 1)',
    'padding:5px 9px',
    'border-radius:6px',
    'font-size:11px',
    'font-weight:500',
    'line-height:1.4',
    'letter-spacing:0.2px',
    'white-space:nowrap',
    'color:#fff',
    'background:linear-gradient(135deg, #12b7f5 0%, #2086e8 50%, #1a4fc4 100%)',
    'box-shadow:0 4px 14px rgba(18,183,245,0.32),0 8px 24px rgba(26,79,196,0.18),0 1px 0 rgba(255,255,255,0.18) inset',
    'user-select:none',
  ].join(';')

  // 小箭头
  const arrow = document.createElement('div')
  arrow.className = 'webrpa-tooltip-arrow'
  arrow.style.cssText = [
    'position:absolute',
    'left:50%',
    'transform:translateX(-50%)',
    'width:0',
    'height:0',
    'border-left:5px solid transparent',
    'border-right:5px solid transparent',
  ].join(';')
  tipEl.appendChild(arrow)
  tipEl._arrow = arrow

  document.body.appendChild(tipEl)
  return tipEl
}

function show(target, text) {
  const el = ensureTipEl()
  el.firstChild && el.firstChild.nodeType === 3 ? (el.firstChild.nodeValue = text) : null
  // 用 textContent 重置但保留箭头
  el.childNodes.forEach((n) => { if (n.nodeType === 3) n.nodeValue = text })
  if (![...el.childNodes].some((n) => n.nodeType === 3)) {
    el.insertBefore(document.createTextNode(text), el._arrow)
  }

  // 测量目标元素位置
  const rect = target.getBoundingClientRect()
  // 先让浏览器测一次尺寸
  el.style.opacity = '0'
  el.style.left = '-9999px'
  el.style.top = '-9999px'
  // 强制 reflow 拿尺寸
  const tw = el.offsetWidth
  const th = el.offsetHeight

  // 默认在元素上方
  let top = rect.top - th - 8
  let placement = 'top'
  if (top < 4) {
    // 不够空间放上面 → 放下面
    top = rect.bottom + 8
    placement = 'bottom'
  }
  let left = rect.left + rect.width / 2

  // 不超出屏幕
  const minLeft = tw / 2 + 6
  const maxLeft = window.innerWidth - tw / 2 - 6
  left = Math.max(minLeft, Math.min(maxLeft, left))

  el.style.left = left + 'px'
  el.style.top = top + 'px'

  // 箭头
  const arrow = el._arrow
  if (placement === 'top') {
    arrow.style.top = '100%'
    arrow.style.bottom = ''
    arrow.style.borderTop = '5px solid #1a4fc4'
    arrow.style.borderBottom = ''
  } else {
    arrow.style.bottom = '100%'
    arrow.style.top = ''
    arrow.style.borderBottom = '5px solid #12b7f5'
    arrow.style.borderTop = ''
  }

  // 入场
  requestAnimationFrame(() => {
    el.style.opacity = '1'
    el.style.transform = 'translate(-50%, 0) scale(1)'
  })
}

function hide() {
  if (!tipEl) return
  tipEl.style.opacity = '0'
  tipEl.style.transform = 'translate(-50%, 4px) scale(0.96)'
}

function bindEvents(el, getText) {
  const onEnter = () => {
    const text = getText()
    if (!text) return
    if (showTimer) clearTimeout(showTimer)
    showTimer = setTimeout(() => show(el, text), 80)
  }
  const onLeave = () => {
    if (showTimer) { clearTimeout(showTimer); showTimer = null }
    hide()
  }
  el.addEventListener('mouseenter', onEnter)
  el.addEventListener('mouseleave', onLeave)
  el.addEventListener('mousedown', onLeave)
  el._wrTooltipCleanup = () => {
    el.removeEventListener('mouseenter', onEnter)
    el.removeEventListener('mouseleave', onLeave)
    el.removeEventListener('mousedown', onLeave)
  }
}

export const TooltipDirective = {
  mounted(el, binding) {
    // 优先用指令值，否则读取 title 并搬走避免原生 tooltip
    let text = binding.value
    if (!text && el.hasAttribute('title')) {
      text = el.getAttribute('title')
      el.setAttribute('data-tip', text)
      el.removeAttribute('title')
    }
    if (text) bindEvents(el, () => el.getAttribute('data-tip') || binding.value || '')
  },
  updated(el, binding) {
    if (binding.value !== binding.oldValue) {
      el.setAttribute('data-tip', binding.value || '')
    }
  },
  beforeUnmount(el) {
    if (el._wrTooltipCleanup) el._wrTooltipCleanup()
  },
}

// 全局拦截：扫描所有带 title 属性的元素，自动接管
export function installTitleInterceptor(app) {
  // 把已经在 DOM 的 title 全转成自定义
  function processNode(node) {
    if (node.nodeType !== 1) return
    if (node.hasAttribute && node.hasAttribute('title')) {
      const text = node.getAttribute('title')
      if (text) {
        node.setAttribute('data-tip', text)
        node.removeAttribute('title')
        bindEvents(node, () => node.getAttribute('data-tip') || '')
      }
    }
    if (node.children) {
      for (const c of node.children) processNode(c)
    }
  }
  // 初始扫描
  setTimeout(() => processNode(document.body), 0)
  // 监听后续 DOM 变化
  const mo = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.type === 'attributes' && m.attributeName === 'title' && m.target.hasAttribute('title')) {
        processNode(m.target)
      } else if (m.type === 'childList') {
        m.addedNodes.forEach((n) => processNode(n))
      }
    }
  })
  mo.observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ['title'] })
}
