/**
 * 编辑器停靠布局壳
 *
 * 把三个核心面板（modules / config / log）按 layoutStore.panelDocks 的指示
 * 放到 4 个 dock zone（左/右/上/下）之一；中间画布永远在中央。
 *
 * 用 CSS Grid 实现：
 *   .  top  .
 *   left main right
 *   .  bottom .
 *
 * 拖拽时挂载 DockOverlay 让用户选择新的 zone。
 */
import React, { useCallback, useEffect, useRef, useState } from 'react'
import type { PanelId, DockZone } from '@/store/layoutStore'
import { useLayoutStore, LAYOUT_LIMITS } from '@/store/layoutStore'
import { DockOverlay } from './DockOverlay'

interface PanelMap {
  modules: React.ReactNode
  config: React.ReactNode
  log: React.ReactNode
  /** 中央画布 */
  center: React.ReactNode
}

export function EditorDockShell({ panels }: { panels: PanelMap }) {
  const docks = useLayoutStore((s) => s.panelDocks)
  const setPanelDock = useLayoutStore((s) => s.setPanelDock)
  const leftWidth = useLayoutStore((s) => s.leftWidth)
  const rightWidth = useLayoutStore((s) => s.rightWidth)
  const topHeight = useLayoutStore((s) => s.topHeight)
  const bottomHeight = useLayoutStore((s) => s.bottomHeight)

  const containerRef = useRef<HTMLDivElement>(null)
  const [draggingPanel, setDraggingPanel] = useState<PanelId | null>(null)

  // 监听全局事件 webrpa:dock:start，从 DockHandle 触发
  useEffect(() => {
    const onStart = (e: Event) => {
      const detail = (e as CustomEvent).detail as { panelId: PanelId }
      setDraggingPanel(detail.panelId)
    }
    window.addEventListener('webrpa:dock:start', onStart as EventListener)
    return () => window.removeEventListener('webrpa:dock:start', onStart as EventListener)
  }, [])

  const handleDrop = useCallback((zone: DockZone | null) => {
    if (zone && draggingPanel) {
      setPanelDock(draggingPanel, zone)
    }
    setDraggingPanel(null)
  }, [draggingPanel, setPanelDock])

  const handleCancel = useCallback(() => setDraggingPanel(null), [])

  // 哪些 zone 此刻有面板
  const zoneOccupants: Record<DockZone, PanelId | null> = {
    left: null, right: null, top: null, bottom: null,
  }
  ;(Object.keys(docks) as PanelId[]).forEach((p) => {
    zoneOccupants[docks[p]] = p
  })

  // 计算每个 zone 占用的尺寸；空 zone 尺寸为 0（不占空间）
  const colLeft = zoneOccupants.left ? leftWidth : 0
  const colRight = zoneOccupants.right ? rightWidth : 0
  const rowTop = zoneOccupants.top ? topHeight : 0
  const rowBottom = zoneOccupants.bottom ? bottomHeight : 0

  const gridStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: `${colLeft}px minmax(0,1fr) ${colRight}px`,
    gridTemplateRows: `${rowTop}px minmax(0,1fr) ${rowBottom}px`,
    height: '100%',
    width: '100%',
    minHeight: 0,
    minWidth: 0,
  }

  const renderZone = (zone: DockZone, gridArea: string) => {
    const pid = zoneOccupants[zone]
    if (!pid) return null
    return (
      <div style={{ gridArea, minWidth: 0, minHeight: 0, display: 'flex', position: 'relative' }} data-dock-zone={zone}>
        {panels[pid]}
      </div>
    )
  }

  // 把面板放进 grid 对应的位置，center 占中间
  const styleCenter: React.CSSProperties = {
    gridColumnStart: 2,
    gridColumnEnd: 3,
    gridRowStart: 2,
    gridRowEnd: 3,
    minWidth: 0,
    minHeight: 0,
    display: 'flex',
    position: 'relative',
  }
  const zonePos = {
    top: { gridColumn: '1 / 4', gridRow: '1 / 2' } as React.CSSProperties,
    bottom: { gridColumn: '1 / 4', gridRow: '3 / 4' } as React.CSSProperties,
    left: { gridColumn: '1 / 2', gridRow: '2 / 3' } as React.CSSProperties,
    right: { gridColumn: '3 / 4', gridRow: '2 / 3' } as React.CSSProperties,
  }

  void renderZone
  void LAYOUT_LIMITS

  return (
    <div ref={containerRef} className="dock-shell" style={gridStyle}>
      <div style={{ ...zonePos.top, minHeight: 0, display: zoneOccupants.top ? 'flex' : 'none', position: 'relative' }} data-dock-zone="top">
        {zoneOccupants.top && panels[zoneOccupants.top]}
      </div>
      <div style={{ ...zonePos.left, minWidth: 0, display: zoneOccupants.left ? 'flex' : 'none', position: 'relative' }} data-dock-zone="left">
        {zoneOccupants.left && panels[zoneOccupants.left]}
      </div>
      <div style={styleCenter}>{panels.center}</div>
      <div style={{ ...zonePos.right, minWidth: 0, display: zoneOccupants.right ? 'flex' : 'none', position: 'relative' }} data-dock-zone="right">
        {zoneOccupants.right && panels[zoneOccupants.right]}
      </div>
      <div style={{ ...zonePos.bottom, minHeight: 0, display: zoneOccupants.bottom ? 'flex' : 'none', position: 'relative' }} data-dock-zone="bottom">
        {zoneOccupants.bottom && panels[zoneOccupants.bottom]}
      </div>

      <DockOverlay active={!!draggingPanel} containerRef={containerRef} onDrop={handleDrop} onCancel={handleCancel} />
    </div>
  )
}
