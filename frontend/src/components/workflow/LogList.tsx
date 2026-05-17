/**
 * 高性能日志列表 - 用虚拟滚动渲染，无论多少条都能 60fps。
 * 行高固定，估算 22px。删除每行的 framer-motion 包裹（这是大量日志时的卡顿主因）。
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { cn } from '@/lib/utils'
import { useVirtualizer } from '@/hooks/useVirtualizer'
import type { LogEntry, LogLevel } from '@/types'

const ROW_HEIGHT = 22

const levelColors: Record<LogLevel, string> = {
  debug: 'text-gray-500',
  info: 'text-blue-600',
  success: 'text-emerald-600',
  warning: 'text-amber-600',
  error: 'text-red-600',
}

interface LogListProps {
  logs: LogEntry[]
  searchQuery?: string
  onLogClick?: (nodeId?: string) => void
}

function highlightText(text: string, query: string) {
  if (!query) return text
  const idx = text.toLowerCase().indexOf(query.toLowerCase())
  if (idx < 0) return text
  return (
    <>
      {text.slice(0, idx)}
      <mark className="bg-[hsl(48_100%_85%)] text-[hsl(var(--foreground))] rounded px-0.5">
        {text.slice(idx, idx + query.length)}
      </mark>
      {text.slice(idx + query.length)}
    </>
  )
}

export function LogList({ logs, searchQuery, onLogClick }: LogListProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const getScrollElement = useCallback(() => scrollRef.current, [])
  const [autoScroll, setAutoScroll] = useState(true)
  const lastLogCountRef = useRef(logs.length)

  const { virtualItems, totalSize, scrollToBottom } = useVirtualizer({
    count: logs.length,
    getScrollElement,
    estimateSize: ROW_HEIGHT,
    overscan: 10,
  })

  // 用户滚动偏离底部时自动关闭追加滚动；回到底部时恢复
  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    const handler = () => {
      const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 20
      setAutoScroll(nearBottom)
    }
    el.addEventListener('scroll', handler, { passive: true })
    return () => el.removeEventListener('scroll', handler)
  }, [])

  // 新日志到来：如果用户没有手动上滚则跟随
  useEffect(() => {
    if (logs.length !== lastLogCountRef.current) {
      lastLogCountRef.current = logs.length
      if (autoScroll) {
        // 延后到下一帧，等虚拟列表测量完
        requestAnimationFrame(() => scrollToBottom())
      }
    }
  }, [logs.length, autoScroll, scrollToBottom])

  return (
    <div ref={scrollRef} className="flex-1 overflow-auto px-2 py-1">
      <div style={{ height: totalSize, position: 'relative' }}>
        {virtualItems.map((v) => {
          const log = logs[v.index]
          if (!log) return null
          const ts = (() => {
            try {
              return new Date(log.timestamp).toLocaleTimeString()
            } catch {
              return log.timestamp
            }
          })()
          return (
            <div
              key={log.id}
              style={{
                position: 'absolute',
                top: v.start,
                left: 0,
                right: 0,
                height: ROW_HEIGHT,
              }}
              className={cn(
                'text-[12px] font-mono px-3 leading-[22px] truncate rounded',
                log.nodeId
                  ? 'cursor-pointer hover:bg-[hsl(var(--brand-50))]'
                  : 'hover:bg-[hsl(var(--muted))]'
              )}
              onClick={() => onLogClick?.(log.nodeId)}
              title={log.nodeId ? '点击定位到对应模块' : log.message}
            >
              <span className="text-[hsl(var(--muted-foreground))]">[{ts}]</span>{' '}
              <span className={cn(levelColors[log.level], 'font-semibold')}>[{log.level.toUpperCase()}]</span>{' '}
              <span>{highlightText(log.message, searchQuery || '')}</span>
              {log.duration !== undefined && log.duration !== null && (
                <span className="text-[hsl(var(--brand-500))] ml-2">({log.duration.toFixed(2)}ms)</span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
