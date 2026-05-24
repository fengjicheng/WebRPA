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

