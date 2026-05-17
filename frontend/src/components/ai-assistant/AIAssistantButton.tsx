import { Bot } from 'lucide-react'
import { useAIAssistantStore } from '@/store/aiAssistantStore'

/** 浮动右下角的助手触发按钮 */
export function AIAssistantButton() {
  const isOpen = useAIAssistantStore((s) => s.isPanelOpen)
  const togglePanel = useAIAssistantStore((s) => s.togglePanel)

  if (isOpen) return null

  return (
    <button
      onClick={togglePanel}
      title="WebRPA小助手"
      className="fixed bottom-6 right-6 z-40 w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 via-cyan-500 to-teal-500 shadow-2xl hover:scale-110 active:scale-95 transition-transform flex items-center justify-center group"
    >
      <Bot className="w-7 h-7 text-white" />
      <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-emerald-400 ring-2 ring-white animate-pulse" />
      <span className="absolute right-full mr-3 whitespace-nowrap bg-black/80 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
        WebRPA小助手
      </span>
    </button>
  )
}
