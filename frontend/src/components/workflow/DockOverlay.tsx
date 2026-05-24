/**
 * 面板停靠覆盖层
 *
 * 用户开始拖动某个面板的 header 时，
 * 这个组件覆盖整个编辑器主区域，渲染 4 个候选吸附区（左/右/上/下）。
 * 鼠标进入哪个区，那个区高亮 + 显示标签；松手时调用 onDrop 通知父组件。
 *
 * 性能：mousemove 不修改任何 React state，只更新 ref + 高亮 div 的 className，
 *      避免拖拽过程中 React 重渲染。
 */
import { useEffect, useRef, useState } from 'react'
import type { DockZone } from '@/store/layoutStore'

interface DockOverlayProps {
  /** 是否正在拖拽中（外部控制） */
  active: boolean
  /** 主内容区域（编辑器中央画布） boundingClientRect 的 ref */
  containerRef: React.RefObject<HTMLElement>
  /** 用户在某个 zone 松开鼠标时回调 */
  onDrop: (zone: DockZone | null) => void
  /** 用户取消拖拽（按 Esc 或松手时未在任何 zone 上） */
  onCancel?: () => void
}

const ZONE_THRESHOLD = 0.32 // 距离边缘 32% 以内算入对应 zone

export function DockOverlay({ active, containerRef, onDrop, onCancel }: DockOverlayProps) {
  const [hovered, setHovered] = useState<DockZone | null>(null)
  const hoveredRef = useRef<DockZone | null>(null)

  useEffect(() => {
    if (!active) {
      setHovered(null)
      hoveredRef.current = null
      return
    }

    function detectZone(clientX: number, clientY: number): DockZone | null {
      const el = containerRef.current
      if (!el) return null
      const r = el.getBoundingClientRect()
      if (clientX < r.left || clientX > r.right || clientY < r.top || clientY > r.bottom) {
        return null
      }
      const fx = (clientX - r.left) / r.width
      const fy = (clientY - r.top) / r.height
      // 取距离最近的边缘
      const dl = fx
      const dr = 1 - fx
      const dt = fy
      const db = 1 - fy
      const minDist = Math.min(dl, dr, dt, db)
      if (minDist > ZONE_THRESHOLD) return null
      if (minDist === dl) return 'left'
      if (minDist === dr) return 'right'
      if (minDist === dt) return 'top'
      return 'bottom'
    }

    function onMove(e: MouseEvent) {
      const z = detectZone(e.clientX, e.clientY)
      if (z !== hoveredRef.current) {
        hoveredRef.current = z
        setHovered(z)
      }
    }
    function onUp(e: MouseEvent) {
      const z = detectZone(e.clientX, e.clientY)
      if (z) onDrop(z)
      else if (onCancel) onCancel()
      else onDrop(null)
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        if (onCancel) onCancel()
        else onDrop(null)
      }
    }

    document.addEventListener('mousemove', onMove, true)
    document.addEventListener('mouseup', onUp, true)
    document.addEventListener('keydown', onKey, true)
    return () => {
      document.removeEventListener('mousemove', onMove, true)
      document.removeEventListener('mouseup', onUp, true)
      document.removeEventListener('keydown', onKey, true)
    }
  }, [active, containerRef, onDrop, onCancel])

  if (!active) return null

  // 4 个 zone 的位置（相对 container），用绝对定位渲染
  const zoneStyle = (zone: DockZone): React.CSSProperties => {
    const base: React.CSSProperties = {
      position: 'absolute',
      pointerEvents: 'none',
      transition: 'background-color 120ms ease-out, border-color 120ms ease-out, box-shadow 120ms ease-out',
      borderRadius: 8,
    }
    const hi = hovered === zone
    const bg = hi ? 'rgba(59,130,246,0.32)' : 'rgba(59,130,246,0.10)'
    const border = hi ? '2px solid rgba(59,130,246,0.95)' : '2px dashed rgba(59,130,246,0.45)'
    const shadow = hi ? '0 0 0 4px rgba(59,130,246,0.18) inset' : 'none'
    const common = { ...base, background: bg, border, boxShadow: shadow }
    if (zone === 'left') return { ...common, left: 8, top: '24%', bottom: '24%', width: '20%' }
    if (zone === 'right') return { ...common, right: 8, top: '24%', bottom: '24%', width: '20%' }
    if (zone === 'top') return { ...common, top: 8, left: '28%', right: '28%', height: '18%' }
    return { ...common, bottom: 8, left: '28%', right: '28%', height: '20%' }
  }

  const labelStyle: React.CSSProperties = {
    position: 'absolute',
    inset: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#1e3a8a',
    fontSize: 13,
    fontWeight: 700,
    letterSpacing: '0.04em',
    textShadow: '0 1px 2px rgba(255,255,255,0.6)',
  }

  // overlay 容器跟随 container 位置（用 fixed 跟随 boundingClientRect）
  const r = containerRef.current?.getBoundingClientRect()
  if (!r) return null

  return (
    <div
      style={{
        position: 'fixed',
        left: r.left,
        top: r.top,
        width: r.width,
        height: r.height,
        zIndex: 9998,
        pointerEvents: 'none',
      }}
    >
      <div style={zoneStyle('left')}>
        <div style={labelStyle}>停靠到 左</div>
      </div>
      <div style={zoneStyle('right')}>
        <div style={labelStyle}>停靠到 右</div>
      </div>
      <div style={zoneStyle('top')}>
        <div style={labelStyle}>停靠到 上</div>
      </div>
      <div style={zoneStyle('bottom')}>
        <div style={labelStyle}>停靠到 下</div>
      </div>
    </div>
  )
}
