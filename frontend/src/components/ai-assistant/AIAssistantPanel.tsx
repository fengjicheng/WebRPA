import { useEffect, useRef, useState } from 'react'
import {
  X,
  Sparkles,
  Send,
  Square,
  Plus,
  Trash2,
  History,
  Settings,
  AlertCircle,
  Wrench,
  Zap,
  MessageCircleQuestion,
  ListTree,
  Layers,
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
import { PanelResizer } from '@/components/workflow/PanelResizer'
import { useLayoutStore, LAYOUT_LIMITS } from '@/store/layoutStore'

const QUICK_PROMPTS = [
  { text: '帮我新建一个打开网页的工作流', icon: Zap, color: 'icon-chip-success' },
  { text: 'WebRPA 怎么用？', icon: MessageCircleQuestion, color: 'icon-chip-info' },
  { text: '列出所有 AI 类模块', icon: Layers, color: 'icon-chip-violet' },
  { text: '我画布上有哪些节点？', icon: ListTree, color: 'icon-chip-warning' },
]

export function AIAssistantPanel() {
  const isOpen = useAIAssistantStore((s) => s.isPanelOpen)
  const setOpen = useAIAssistantStore((s) => s.setPanelOpen)
  const messages = useAIAssistantStore((s) => s.messages)
  const setMessages = useAIAssistantStore((s) => s.setMessages)
  const appendMessage = useAIAssistantStore((s) => s.appendMessage)
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
  // 用于打断当前任务：保留正在跑的 sessionId 和 AbortController
  const inflightSessionIdRef = useRef<string | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, isSending])

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => textareaRef.current?.focus(), 80)
    }
  }, [isOpen])

  useEffect(() => {
    if (!isOpen) return
    aiAssistantApi.listSessions().then((res) => {
      if (res.success && Array.isArray(res.data)) {
        setSessions(res.data)
      }
    })
  }, [isOpen, setSessions])

  useEffect(() => {
    bindAssistantSocketEvents({
      onToolCall: (data: any) => {
        // 工具开始执行：实时把工具卡片插入到最新的助手消息里
        const tc = data?.tool_call
        if (!tc) return
        const state = useAIAssistantStore.getState()
        const msgs = state.messages
        // 找到最近的、还没有这个 tc 的助手消息，把工具加进去
        for (let i = msgs.length - 1; i >= Math.max(0, msgs.length - 10); i--) {
          const m = msgs[i]
          if (m.role !== 'assistant') continue
          const existing = m.tool_calls || []
          const idx = existing.findIndex((x) => x.id === tc.id)
          if (idx >= 0) {
            existing[idx] = { ...existing[idx], ...tc }
            state.upsertMessage({ ...m, tool_calls: [...existing] })
            return
          }
        }
        // 没有找到对应助手消息，直接造一条临时
        const tempMsg = {
          id: `tmp-${tc.id}`,
          role: 'assistant' as const,
          content: '',
          tool_calls: [tc],
        }
        state.appendMessage(tempMsg)
      },
      onToolResult: (data: any) => {
        const tc = data?.tool_call
        if (!tc) return
        const state = useAIAssistantStore.getState()
        const msgs = state.messages
        for (let i = msgs.length - 1; i >= 0; i--) {
          const m = msgs[i]
          if (m.role !== 'assistant' || !m.tool_calls) continue
          const idx = m.tool_calls.findIndex((x) => x.id === tc.id)
          if (idx >= 0) {
            const newCalls = [...m.tool_calls]
            newCalls[idx] = { ...newCalls[idx], ...tc }
            state.upsertMessage({ ...m, tool_calls: newCalls })
            return
          }
        }
      },
      onAssistantPartial: () => {
        // 中间助手回合（带 tool_calls 但没文本），后端 chat 完成后会用完整列表覆盖
      },
    })
  }, [])

  useEffect(() => {
    return onAssistantUiEvent('show_toast', (payload: any) => {
      console.log('[小助手] toast:', payload?.message)
    })
  }, [])

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

    // 用户在 AI 工作期间发新消息：先打断之前的任务
    if (isSending) {
      await stopCurrent()
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

    const ac = new AbortController()
    abortControllerRef.current = ac

    try {
      const res = await aiAssistantApi.chat({
        session_id: currentSessionId,
        message: messageText,
        config: resolvedConfig,
        workflow_context: buildWorkflowContext(),
      } as any, ac.signal)
      if (!res.success || !res.data) {
        if (ac.signal.aborted) return
        setError(res.error || '请求失败')
        return
      }
      const sid = res.data.session_id
      setCurrentSessionId(sid)
      inflightSessionIdRef.current = sid
      const full = await aiAssistantApi.getSession(sid)
      if (full.success && full.data) {
        setMessages(full.data.messages || [])
      } else {
        appendMessage(res.data.message)
      }
      await dispatchClientActions(full.success ? full.data?.messages || [] : [], sid)
    } catch (e: any) {
      if (ac.signal.aborted || (e && (e.name === 'AbortError' || /aborted/i.test(String(e.message))))) {
        // 用户主动中断，不报错
        return
      }
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setSending(false)
      abortControllerRef.current = null
      inflightSessionIdRef.current = null
      aiAssistantApi.listSessions().then((res) => {
        if (res.success && Array.isArray(res.data)) {
          setSessions(res.data)
        }
      })
    }
  }

  async function stopCurrent() {
    const sid = inflightSessionIdRef.current || currentSessionId
    // 1) 通知后端取消（让正在跑的工具/LLM 调用尽快退出）
    if (sid) {
      try {
        await aiAssistantApi.cancel(sid)
      } catch {}
    }
    // 2) 中断前端的 fetch
    abortControllerRef.current?.abort()
    abortControllerRef.current = null
    // 3) UI 立即恢复成"可输入"状态
    setSending(false)
  }

  async function dispatchClientActions(allMessages: ChatMessage[], _sid: string) {
    if (!allMessages || allMessages.length === 0) return
    // 注意：client_action 工具调用现在由后端 socket 通知前端 **即时执行**（见 aiAssistantSkills.ts
    // 中 ai_assistant:client_action_request 监听），此处不再重复派发，仅处理 build_workflow 自动落地。
    const recent = allMessages.slice(-12)
    for (const msg of recent) {
      if (msg.role !== 'assistant' || !msg.tool_calls || !msg.tool_calls.length) continue
      for (const tc of msg.tool_calls) {
        const flagKey = `__client_executed_${tc.id}`
        if ((msg as any)[flagKey]) continue

        // AI 调用 build_workflow：自动把结果装入画布
        if (tc.name === 'build_workflow' && tc.status === 'success' && tc.result) {
          ;(msg as any)[flagKey] = true
          const built: any = tc.result
          if (Array.isArray(built?.nodes) && Array.isArray(built?.edges)) {
            await executeClientAction('load_workflow_from_data', {
              name: built.name || '小助手生成的工作流',
              nodes: built.nodes,
              edges: built.edges,
            })
            await executeClientAction('fit_view', {})
          }
        }
      }
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      handleSend()
    }
  }

  // 受 layoutStore 控制的宽度（用户可拖拽左边缘）
  const aiAssistantWidth = useLayoutStore((s) => s.aiAssistantWidth)
  const setAiAssistantWidth = useLayoutStore((s) => s.setAiAssistantWidth)
  const [draftWidth, setDraftWidth] = useState<number | null>(null)
  const effectiveWidth = draftWidth ?? aiAssistantWidth

  if (!isOpen) return null

  return (
    <div
      className={
        'fixed top-0 right-0 h-screen z-50 ' +
        'max-w-full responsive-drawer-right ' +
        'bg-[hsl(var(--card))] border-l border-[hsl(var(--border))] shadow-pop-2xl ' +
        'flex flex-col animate-slide-in-right'
      }
      style={{
        width: effectiveWidth,
        transition: draftWidth === null ? 'width 200ms ease-out' : 'none',
      }}
    >
      {/* 左边缘拖拽手柄 */}
      <PanelResizer
        direction="horizontal"
        side="left"
        size={effectiveWidth}
        minSize={LAYOUT_LIMITS.aiAssistant.min}
        maxSize={LAYOUT_LIMITS.aiAssistant.max}
        factor={-1}
        onLive={(w) => setDraftWidth(w)}
        onCommit={(w) => {
          setAiAssistantWidth(w)
          setDraftWidth(null)
        }}
      />
      {/* 顶部装饰条 */}
      <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-[hsl(var(--brand-500))] via-[hsl(var(--brand-400))] to-[hsl(var(--info-500))]" />

      {/* 头部 */}
      <div
        className="flex items-center justify-between px-4 h-14 border-b border-[hsl(var(--border))] flex-shrink-0"
        style={{ background: 'linear-gradient(180deg, hsl(var(--brand-50) / 0.6), hsl(var(--card)))' }}
      >
        <div className="flex items-center gap-2.5 min-w-0">
          {/* 渐变 LOGO 圆环 */}
          <div className="relative flex-shrink-0">
            <div className="w-9 h-9 rounded-[10px] bg-gradient-to-br from-[hsl(var(--brand-500))] to-[hsl(var(--brand-700))] flex items-center justify-center shadow-brand-glow ring-1 ring-[hsl(var(--brand-500)/0.3)]">
              <Sparkles className="w-4 h-4 text-white" strokeWidth={2.4} />
            </div>
            {configReady && (
              <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-[hsl(var(--success-500))] border-2 border-[hsl(var(--card))] shadow-success-glow animate-pulse-ring" />
            )}
          </div>
          <div className="min-w-0">
            <div className="text-[14px] font-bold leading-tight tracking-tight text-gradient">
              WebRPA 小助手
            </div>
            <div className="text-[11px] text-[hsl(var(--muted-foreground))] leading-tight truncate mt-0.5 flex items-center gap-1">
              <span className={`w-1.5 h-1.5 rounded-full ${configReady ? 'bg-[hsl(var(--success-500))]' : 'bg-[hsl(var(--warning-500))]'}`} />
              {configReady ? resolvedConfig.model : '尚未配置模型'}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          <Button variant="ghost" size="icon-sm" title="新对话" onClick={handleNewSession}>
            <Plus className="w-3.5 h-3.5" />
          </Button>
          <Button
            variant={showSessions ? 'tonal' : 'ghost'}
            size="icon-sm"
            title="历史对话"
            onClick={() => setShowSessions((v) => !v)}
          >
            <History className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="icon-sm" title="关闭" onClick={() => setOpen(false)}>
            <X className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>

      {/* 会话列表抽屉 */}
      {showSessions && (
        <div className="border-b border-[hsl(var(--border))] bg-[hsl(var(--slate-50))] max-h-72 overflow-y-auto animate-fade-in-down flex-shrink-0">
          {sessions.length === 0 ? (
            <div className="empty-state py-8">
              <div className="empty-state-icon w-12 h-12 mb-2">
                <History className="w-5 h-5" />
              </div>
              <div className="empty-state-title text-[13px]">暂无历史对话</div>
            </div>
          ) : (
            <div className="py-1.5 space-y-0.5 px-2">
              {sessions.map((s) => (
                <div
                  key={s.id}
                  onClick={() => handleSelectSession(s.id)}
                  className={
                    'group flex items-start gap-2 px-2.5 py-2 cursor-pointer rounded-[8px] transition-all duration-150 ' +
                    (s.id === currentSessionId
                      ? 'bg-[hsl(var(--brand-100))] border border-[hsl(var(--brand-500)/0.3)] shadow-xs'
                      : 'border border-transparent hover:bg-[hsl(var(--card))] hover:border-[hsl(var(--border))] hover:shadow-xs')
                  }
                >
                  <div className="icon-chip icon-chip-brand w-7 h-7 flex-shrink-0">
                    <Sparkles className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-[12.5px] font-medium text-[hsl(var(--slate-800))] truncate">
                      {s.title}
                    </div>
                    <div className="text-[11px] text-[hsl(var(--muted-foreground))] truncate mt-0.5">
                      {s.last_message_preview || `${s.message_count} 条消息`}
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDeleteSession(s.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded-[5px] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--danger-600))] hover:bg-[hsl(var(--danger-50))] transition-all"
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
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && !isSending && (
          <div className="h-full flex flex-col items-center justify-center text-center px-2 animate-fade-in-up">
            <div className="relative mb-4">
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-[hsl(var(--brand-500)/0.4)] to-[hsl(var(--info-500)/0.4)] blur-xl" />
              <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-[hsl(var(--brand-500))] to-[hsl(var(--brand-700))] flex items-center justify-center shadow-brand-glow ring-2 ring-[hsl(var(--brand-500)/0.25)]">
                <Sparkles className="w-7 h-7 text-white" strokeWidth={2.2} />
              </div>
            </div>
            <div className="text-[16px] font-bold text-gradient mb-1.5 tracking-tight">
              你好，我是 WebRPA 小助手
            </div>
            <div className="text-[12.5px] text-[hsl(var(--slate-600))] leading-relaxed max-w-[340px] mb-5">
              我了解 WebRPA 的方方面面，能帮你搭建工作流、运行任务、答疑解惑
            </div>

            <div className="w-full max-w-[360px] space-y-1.5">
              <div className="text-[10px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))] mb-2 flex items-center gap-1.5">
                <Zap className="w-3 h-3" />
                快速开始
              </div>
              {QUICK_PROMPTS.map((q, idx) => {
                const Icon = q.icon
                return (
                  <button
                    key={q.text}
                    onClick={() => handleSend(q.text)}
                    disabled={!configReady || isSending}
                    className="w-full row-card text-left disabled:opacity-50 disabled:cursor-not-allowed text-[12.5px]"
                    style={{ animation: `fadeInUp ${220 + idx * 60}ms cubic-bezier(0.25, 1, 0.5, 1) both` }}
                  >
                    <span className={`icon-chip ${q.color} w-7 h-7`}>
                      <Icon className="w-3.5 h-3.5" />
                    </span>
                    <span className="flex-1 text-[hsl(var(--slate-700))]">{q.text}</span>
                  </button>
                )
              })}
            </div>

            {!configReady && (
              <div className="status-row status-row-warning mt-5 max-w-[340px]">
                <Settings className="w-3.5 h-3.5 shrink-0" />
                <span className="text-[12px]">请先在全局配置中填写小助手的模型</span>
              </div>
            )}
          </div>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        {isSending && (
          <div className="flex items-center gap-2 pl-11">
            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[hsl(var(--brand-500))] animate-pulse" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-[hsl(var(--brand-500))] animate-pulse" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-[hsl(var(--brand-500))] animate-pulse" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-[12px] text-[hsl(var(--muted-foreground))] italic">
              小助手工作中…可在下方再次发送来打断
            </span>
          </div>
        )}
        {error && (
          <div className="status-row status-row-danger animate-fade-in-up">
            <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
            <div className="flex-1 break-words text-[12px]">{error}</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区 */}
      <div className="border-t border-[hsl(var(--border))] p-3 bg-[hsl(var(--slate-50))] flex-shrink-0">
        <div className="relative flex items-end gap-1.5 rounded-[10px] border-[1.5px] border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-xs focus-within:border-[hsl(var(--brand-500))] focus-within:shadow-ring transition-[border-color,box-shadow] duration-150">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={configReady ? (isSending ? '小助手正在工作中…再次发送会先停止它' : '告诉我你想做什么…（Enter 发送，Shift+Enter 换行）') : '请先在全局配置中配置模型'}
            rows={2}
            disabled={!configReady}
            className="flex-1 bg-transparent text-[13px] resize-none outline-none placeholder:text-[hsl(var(--muted-foreground))] disabled:opacity-60 max-h-32 px-3 py-2.5 leading-relaxed"
          />
          <Button
            onClick={() => (isSending ? stopCurrent() : handleSend())}
            disabled={!isSending && (!input.trim() || !configReady)}
            size="icon-sm"
            variant={isSending ? 'destructive' : 'default'}
            className="!h-8 !w-8 flex-shrink-0 m-1"
            title={isSending ? '停止 (再次发送也会自动停止)' : '发送 (Enter)'}
          >
            {isSending ? (
              <Square className="w-3.5 h-3.5 fill-current" />
            ) : (
              <Send className="w-3.5 h-3.5" />
            )}
          </Button>
        </div>
        <div className="mt-2 flex items-center justify-between text-[10.5px] text-[hsl(var(--muted-foreground))] px-1">
          <div className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${resolvedConfig.enable_tools ? 'bg-[hsl(var(--success-500))]' : 'bg-[hsl(var(--slate-400))]'}`} />
            <Wrench className="w-2.5 h-2.5" />
            <span className="font-medium">{resolvedConfig.enable_tools ? 'Skills 已启用' : 'Skills 已关闭'}</span>
          </div>
          <span className="font-mono">WebRPA AI · v2</span>
        </div>
      </div>
    </div>
  )
}
