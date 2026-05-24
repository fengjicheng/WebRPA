/**
 * 面板 header 上的"拖拽抓手"
 *
 * 用法：放在每个面板的标题栏开头，按住即开始拖拽。
 * 拖拽过程通过全局事件 'webrpa:dock:start' / 'webrpa:dock:end' 让上层 EditorShell 显示 DockOverlay。
 */
import { useCallback } from 'react'
import { GripVertical } from 'lucide-react'
import type { PanelId } from '@/store/layoutStore'

interface DockHandleProps {
  panelId: PanelId
  title?: string
}

export function DockHandle({ panelId, title }: DockHandleProps) {
  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    // 抛全局事件，让 EditorShell 接管 overlay 显示与 mouseup 收尾
    window.dispatchEvent(new CustomEvent('webrpa:dock:start', { detail: { panelId } }))
    document.body.style.cursor = 'grabbing'
    document.body.style.userSelect = 'none'

    const onUp = () => {
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      // 不在这里 dispatch end - DockOverlay 监听 mouseup 后会回调 EditorShell 处理
      document.removeEventListener('mouseup', onUp, true)
    }
    document.addEventListener('mouseup', onUp, true)
  }, [panelId])

  return (
    <button
      type="button"
      onMouseDown={onMouseDown}
      title={title || '拖动以更换面板停靠位置'}
      className="dock-handle inline-flex items-center justify-center w-5 h-5 rounded text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--brand-600))] hover:bg-[hsl(var(--brand-50))] cursor-grab active:cursor-grabbing transition-colors"
    >
      <GripVertical className="w-3.5 h-3.5" strokeWidth={2.2} />
    </button>
  )
}
