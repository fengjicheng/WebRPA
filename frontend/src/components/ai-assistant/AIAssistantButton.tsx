import { Sparkles } from 'lucide-react'
import { useEffect } from 'react'
import { useAIAssistantStore } from '@/store/aiAssistantStore'

/** 浮动右下角的助手触发按钮 */
export function AIAssistantButton() {
  const isOpen = useAIAssistantStore((s) => s.isPanelOpen)
  const togglePanel = useAIAssistantStore((s) => s.togglePanel)

  // 全局快捷键：Ctrl/Cmd + K 唤起小助手
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().includes('MAC')
      if ((isMac ? e.metaKey : e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        togglePanel()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [togglePanel])

  if (isOpen) return null

  return (
    <button
      onClick={togglePanel}
      title="WebRPA 小助手  (Ctrl+K)"
      className={
        'fixed bottom-5 right-5 z-40 group ' +
        'flex items-center gap-2 h-9 pl-2.5 pr-3 ' +
        'rounded-full border border-[hsl(var(--border))] bg-[hsl(var(--card))] ' +
        'shadow-pop hover:shadow-pop-lg ' +
        'transition-shadow duration-150 ' +
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]'
      }
    >
      <span className="flex items-center justify-center w-6 h-6 rounded-full bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]">
        <Sparkles className="w-3.5 h-3.5" />
      </span>
      <span className="text-[12.5px] font-medium text-[hsl(var(--foreground))]">小助手</span>
      <kbd className="ml-0.5 hidden sm:inline-flex items-center gap-0.5 px-1.5 h-4 rounded border border-[hsl(var(--border))] bg-[hsl(var(--muted))] text-[10px] font-mono text-[hsl(var(--muted-foreground))]">
        Ctrl K
      </kbd>
    </button>
  )
}
