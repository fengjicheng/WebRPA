import { useEffect, useRef, useState } from 'react'
import {
  X,
  Sparkles,
  Send,
  Loader2,
  Plus,
  Trash2,
  History,
  Settings,
  AlertCircle,
  Wrench,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAIAssistantStore, type ChatMessage } from '@/store/aiAssistantStore'
import { useGlobalConfigStore } from '@/store/globalConfigStore'
import { aiAssistantApi } from '@/services/aiAssistantApi'
import {
  bindAssistantSocketEvents,
  buildWorkflowContext,
  executeClientAction,
  onAssistantUiEvent,
} from '@/services/aiAssistantSkills'
import { MessageBubble } from './MessageBubble'

const QUICK_PROMPTS = [
  '帮我新建一个打开网页的工作流',
  'WebRPA 怎么用？',
  '列出所有 AI 类模块',
  '我画布上有哪些节点？',
]

export function AIAssistantPanel() {
  const isOpen = useAIAssistantStore((s) => s.isPanelOpen)
  const setOpen = useAIAssistantStore((s) => s.setPanelOpen)
  const messages = useAIAssistantStore((s) => s.messages)
  const setMessages = useAIAssistantStore((s) => s.setMessages)
  const appendMessage = useAIAssistantStore((s) => s.appendMessage)
  const upsertMessage = useAIAssistantStore((s) => s.upsertMessage)
  const isSending = useAIAssistantStore((s) => s.isSending)
  const setSending = useAIAssistantStore((s) => s.setSending)
  const currentSessionId = useAIAssistantStore((s) => s.currentSessionId)
  const setCurrentSessionId = useAIAssistantStore((s) => s.setCurrentSessionId)
  const sessions = useAIAssistantStore((s) => s.sessions)
  const setSessions = useAIAssistantStore((s) => s.setSessions)

  const aiAssistantConfig = useGlobalConfigStore((s) => s.config.aiAssistant)
  const aiFallbackConfig = useGlobalConfigStore((s) => s.config.ai)

  const [input, setInput] = useState('')
  const [showSessions, setShowSessions] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, isSending])

  // 打开时聚焦
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => textareaRef.current?.focus(), 80)
    }
  }, [isOpen])

  // 加载会话列表
  useEffect(() => {
    if (!isOpen) return
    aiAssistantApi.listSessions().then((res) => {
      if (res.success && Array.isArray(res.data)) {
        setSessions(res.data)
      }
    })
  }, [isOpen, setSessions])

  // 绑定 socket 事件
  useEffect(() => {
    bindAssistantSocketEvents({
      onToolCall: () => {},
      onToolResult: () => {},
      onAssistantPartial: () => {},
    })
  }, [])

  // 监听跨组件事件示例
  useEffect(() => {
    return onAssistantUiEvent('show_toast', (payload: any) => {
      // 这里可以接入应用的 toast 系统；暂时打 console
      console.log('[小助手] toast:', payload?.message)
    })
  }, [])

  // 配置回退：aiAssistant -> ai
  const resolvedConfig = (() => {
    const a = aiAssistantConfig
    const b = aiFallbackConfig
    return {
      api_url: a?.apiUrl || b?.apiUrl || '',
      api_key: a?.apiKey || b?.apiKey || '',
      model: a?.model || b?.model || '',
      temperature: a?.temperature ?? 0.7,
      max_tokens: a?.maxTokens ?? 4000,
      system_prompt: a?.systemPrompt || '',
      enable_tools: a?.enableTools ?? true,
      auto_approve: a?.autoApprove ?? false,
    }
  })()

  const configReady = !!(resolvedConfig.api_url && resolvedConfig.model)

  function handleNewSession() {
    setMessages([])
    setCurrentSessionId(null)
    setError(null)
    setInput('')
    textareaRef.current?.focus()
  }

  async function handleSelectSession(id: string) {
    setShowSessions(false)
    setError(null)
    const res = await aiAssistantApi.getSession(id)
    if (res.success && res.data) {
      setCurrentSessionId(res.data.id)
      setMessages(res.data.messages || [])
    } else {
      setError(res.error || '加载会话失败')
    }
  }

  async function handleDeleteSession(id: string, e: React.MouseEvent) {
    e.stopPropagation()
    const res = await aiAssistantApi.deleteSession(id)
    if (res.success) {
      setSessions(sessions.filter((s) => s.id !== id))
      if (id === currentSessionId) {
        handleNewSession()
      }
    }
  }

  async function handleSend(text?: string) {
    const messageText = (text ?? input).trim()
    if (!messageText) return
    if (!configReady) {
      setError('请先在「全局配置 → 小助手」中填写 API 地址和模型')
      return
    }
    setError(null)
    const userMsg: ChatMessage = {
      id: `local-${Date.now()}`,
      role: 'user',
      content: messageText,
    }
    appendMessage(userMsg)
    setInput('')
    setSending(true)

    try {
      const res = await aiAssistantApi.chat({
        session_id: currentSessionId,
        message: messageText,
        config: resolvedConfig,
        workflow_context: buildWorkflowContext(),
      })
      if (!res.success || !res.data) {
        setError(res.error || '请求失败')
        return
      }
      const sid = res.data.session_id
      setCurrentSessionId(sid)
      const full = await aiAssistantApi.getSession(sid)
      if (full.success && full.data) {
        setMessages(full.data.messages || [])
      } else {
        appendMessage(res.data.message)
      }
      await dispatchClientActions(full.success ? full.data?.messages || [] : [], sid)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setSending(false)
      aiAssistantApi.listSessions().then((res) => {
        if (res.success && Array.isArray(res.data)) {
          setSessions(res.data)
        }
      })
    }
  }

  // 执行后端返回的 client_action
  async function dispatchClientActions(allMessages: ChatMessage[], _sid: string) {
    if (!allMessages || allMessages.length === 0) return
    const last = [...allMessages].reverse().find((m) => m.role === 'assistant' && m.tool_calls && m.tool_calls.length)
    if (!last || !last.tool_calls) return
    for (const tc of last.tool_calls) {
      if (tc.name !== 'client_action') continue
      const args: any = tc.arguments || {}
      const action = args.action
      const payload = args.payload || {}
      if (!action) continue
      const flagKey = `__client_executed_${tc.id}`
      if ((last as any)[flagKey]) continue
      ;(last as any)[flagKey] = true

      const result = await executeClientAction(action, payload)
      const updatedTc = {
        ...tc,
        status: result.success ? ('success' as const) : ('failed' as const),
        result,
      }
      const newMsg = {
        ...last,
        tool_calls: last.tool_calls.map((x) => (x.id === tc.id ? updatedTc : x)),
      }
      upsertMessage(newMsg)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!isOpen) return null

  return (
    <div
      className={
        'fixed top-0 right-0 h-screen z-50 ' +
        'w-[420px] max-w-full responsive-drawer-right ' +
        'bg-[hsl(var(--card))] border-l border-[hsl(var(--border))] shadow-pop-xl ' +
        'flex flex-col animate-slide-in-right'
      }
    >
      {/* 头部 */}
      <div className="flex items-center justify-between px-3.5 h-12 border-b border-[hsl(var(--border))]">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-7 h-7 rounded-full bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <div className="min-w-0">
            <div className="text-[13px] font-semibold leading-tight truncate">WebRPA 小助手</div>
            <div className="text-[11px] text-[hsl(var(--muted-foreground))] leading-tight truncate">
              {configReady ? `${resolvedConfig.model}` : '尚未配置模型'}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-0.5 flex-shrink-0">
          <Button
            variant="ghost"
            size="icon"
            title="新对话"
            onClick={handleNewSession}
            className="h-7 w-7"
          >
            <Plus className="w-3.5 h-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            title="历史对话"
            onClick={() => setShowSessions((v) => !v)}
            className={`h-7 w-7 ${showSessions ? 'bg-[hsl(var(--muted))]' : ''}`}
          >
            <History className="w-3.5 h-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            title="关闭"
            onClick={() => setOpen(false)}
            className="h-7 w-7"
          >
            <X className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>

      {/* 会话列表抽屉 */}
      {showSessions && (
        <div className="border-b border-[hsl(var(--border))] bg-[hsl(var(--muted))/0.4] max-h-72 overflow-y-auto">
          {sessions.length === 0 ? (
            <div className="px-4 py-6 text-center text-[12px] text-[hsl(var(--muted-foreground))]">
              暂无历史对话
            </div>
          ) : (
            <div className="py-1">
              {sessions.map((s) => (
                <div
                  key={s.id}
                  onClick={() => handleSelectSession(s.id)}
                  className={
                    'group flex items-start gap-2 px-3 py-2 cursor-pointer transition-colors ' +
                    (s.id === currentSessionId
                      ? 'bg-[hsl(var(--brand-50))]'
                      : 'hover:bg-[hsl(var(--muted))]')
                  }
                >
                  <div className="flex-1 min-w-0">
                    <div className="text-[12.5px] font-medium text-[hsl(var(--foreground))] truncate">
                      {s.title}
                    </div>
                    <div className="text-[11px] text-[hsl(var(--muted-foreground))] truncate mt-0.5">
                      {s.last_message_preview || `${s.message_count} 条消息`}
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDeleteSession(s.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--danger-500))] hover:bg-[hsl(var(--card))] transition-all"
                    title="删除"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 消息区 */}
      <div className="flex-1 overflow-y-auto px-3.5 py-3 space-y-3">
        {messages.length === 0 && !isSending && (
          <div className="h-full flex flex-col items-center justify-center text-center px-4">
            <div className="w-11 h-11 rounded-full bg-[hsl(var(--brand-50))] text-[hsl(var(--primary))] flex items-center justify-center mb-3">
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="text-[14px] font-semibold text-[hsl(var(--foreground))] mb-1">
              你好，我是 WebRPA 小助手
            </div>
            <div className="text-[12px] text-[hsl(var(--muted-foreground))] leading-relaxed max-w-[320px]">
              我了解 WebRPA 的方方面面，能帮你搭建工作流、运行任务、答疑解惑。
            </div>
            <div className="mt-4 flex flex-wrap gap-1.5 justify-center max-w-[340px]">
              {QUICK_PROMPTS.map((q) => (
                <button
                  key={q}
                  onClick={() => handleSend(q)}
                  disabled={!configReady || isSending}
                  className="px-2.5 h-6 text-[11px] rounded-full border border-[hsl(var(--border))] bg-[hsl(var(--card))] text-[hsl(var(--foreground))] hover:bg-[hsl(var(--muted))] hover:border-[hsl(var(--brand-500)/0.5)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {q}
                </button>
              ))}
            </div>
            {!configReady && (
              <div className="mt-4 flex items-center gap-1.5 text-[11px] text-[hsl(var(--warning-500))]">
                <Settings className="w-3 h-3" />
                <span>请先在全局配置中填写小助手的模型</span>
              </div>
            )}
          </div>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        {isSending && (
          <div className="flex items-center gap-1.5 text-[11.5px] text-[hsl(var(--muted-foreground))] pl-9">
            <Loader2 className="w-3 h-3 animate-spin" />
            <span>小助手思考中</span>
          </div>
        )}
        {error && (
          <div className="flex items-start gap-1.5 p-2.5 rounded border border-[hsl(var(--danger-500)/0.25)] bg-[hsl(var(--danger-50))] text-[12px] text-[hsl(var(--danger-500))]">
            <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
            <div className="flex-1 break-words">{error}</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区 */}
      <div className="border-t border-[hsl(var(--border))] p-2.5">
        <div className="relative flex items-end gap-1.5 rounded-[8px] border border-[hsl(var(--border))] bg-[hsl(var(--card))] focus-within:border-[hsl(var(--brand-500))] focus-within:shadow-[0_0_0_3px_hsl(var(--brand-500)/0.15)] transition-[border-color,box-shadow]">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={configReady ? '告诉我你想做什么…（Enter 发送，Shift+Enter 换行）' : '请先在全局配置中配置模型'}
            rows={2}
            disabled={!configReady || isSending}
            className="flex-1 bg-transparent text-[13px] resize-none outline-none placeholder:text-[hsl(var(--muted-foreground))] disabled:opacity-60 max-h-32 px-2.5 py-2"
          />
          <Button
            onClick={() => handleSend()}
            disabled={!input.trim() || isSending || !configReady}
            size="icon"
            className="h-7 w-7 flex-shrink-0 m-1"
            title="发送 (Enter)"
          >
            {isSending ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Send className="w-3.5 h-3.5" />
            )}
          </Button>
        </div>
        <div className="mt-1.5 flex items-center justify-between text-[10.5px] text-[hsl(var(--muted-foreground))]">
          <div className="flex items-center gap-1">
            <Wrench className="w-2.5 h-2.5" />
            <span>{resolvedConfig.enable_tools ? 'Skills 已启用' : 'Skills 已关闭'}</span>
          </div>
          <span>WebRPA 小助手 · 鸣航</span>
        </div>
      </div>
    </div>
  )
}
