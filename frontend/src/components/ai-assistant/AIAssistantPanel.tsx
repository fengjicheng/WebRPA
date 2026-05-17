import { useEffect, useRef, useState } from 'react'
import {
  X,
  Bot,
  Send,
  Loader2,
  Plus,
  Trash2,
  History,
  Settings,
  AlertCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAIAssistantStore, type ChatMessage } from '@/store/aiAssistantStore'
import { useGlobalConfigStore } from '@/store/globalConfigStore'
import { aiAssistantApi } from '@/services/aiAssistantApi'
import {
  bindAssistantSocketEvents,
  buildWorkflowContext,
  executeClientAction,
} from '@/services/aiAssistantSkills'
import { MessageBubble } from './MessageBubble'
import { onAssistantUiEvent } from '@/services/aiAssistantSkills'

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

  // 打开面板时聚焦输入框
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => textareaRef.current?.focus(), 100)
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

  // 绑定 socket 事件（监听后端 tool_call/tool_result 推送）
  useEffect(() => {
    bindAssistantSocketEvents({
      onToolCall: (data) => {
        // 由 chat 接口的同步响应负责写入消息，这里只用于实时反馈（可选）
        console.log('[AI助手] tool_call:', data)
      },
      onToolResult: (data) => {
        console.log('[AI助手] tool_result:', data)
      },
      onAssistantPartial: () => {},
    })
  }, [])

  // 决定使用哪个 LLM 配置：优先 aiAssistant，回退到 ai
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

  async function handleNewSession() {
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

  async function handleSend() {
    const text = input.trim()
    if (!text) return
    if (!configReady) {
      setError('请先在「全局配置 → WebRPA小助手」中填写 API 地址和模型名称')
      return
    }
    setError(null)
    // 立即把用户消息显示出来
    const userMsg: ChatMessage = {
      id: `local-${Date.now()}`,
      role: 'user',
      content: text,
    }
    appendMessage(userMsg)
    setInput('')
    setSending(true)

    try {
      const res = await aiAssistantApi.chat({
        session_id: currentSessionId,
        message: text,
        config: resolvedConfig,
        workflow_context: buildWorkflowContext(),
      })
      if (!res.success || !res.data) {
        setError(res.error || '请求失败')
        return
      }
      const sid = res.data.session_id
      setCurrentSessionId(sid)
      // 重新加载完整消息列表（包含 tool_calls 等中间消息）
      const full = await aiAssistantApi.getSession(sid)
      if (full.success && full.data) {
        setMessages(full.data.messages || [])
      } else {
        appendMessage(res.data.message)
      }

      // 检查最新助手消息中是否含 client_action 工具调用，自动派发到前端执行
      // 后端已经把 client_action 工具的"调用"作为 tool_call 写进消息里
      // 但因为后端 stub 不真实执行，前端这里要找出未执行的 client_action 并执行
      await dispatchClientActions(full.success ? full.data?.messages || [] : [], sid)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setSending(false)
      // 刷新会话列表
      aiAssistantApi.listSessions().then((res) => {
        if (res.success && Array.isArray(res.data)) {
          setSessions(res.data)
        }
      })
    }
  }

  // 派发后端返回的 client_action 工具调用
  async function dispatchClientActions(allMessages: ChatMessage[], _sid: string) {
    if (!allMessages || allMessages.length === 0) return
    // 找最近一条 assistant 消息中尚未本地执行过的 client_action
    const last = [...allMessages].reverse().find((m) => m.role === 'assistant' && m.tool_calls && m.tool_calls.length)
    if (!last || !last.tool_calls) return
    for (const tc of last.tool_calls) {
      if (tc.name !== 'client_action') continue
      const args: any = tc.arguments || {}
      const action = args.action
      const payload = args.payload || {}
      if (!action) continue
      // 标记为本地已执行（避免下一次 send 重复执行）：在 message 内添加扩展字段
      const flagKey = `__client_executed_${tc.id}`
      if ((last as any)[flagKey]) continue
      ;(last as any)[flagKey] = true

      const result = await executeClientAction(action, payload)
      // 把执行结果写入 tool_call 视觉反馈
      const updatedTc = {
        ...tc,
        status: result.success ? ('success' as const) : ('failed' as const),
        result: result,
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

  // 监听跨组件事件示例（让外部知道有人请求打开全局配置）
  // 这里只是消费方示例，实际由 GlobalConfigDialog 监听
  useEffect(() => {
    return onAssistantUiEvent('show_toast', (payload: any) => {
      console.log('[AI助手] Toast：', payload?.message)
    })
  }, [])

  if (!isOpen) return null

  return (
    <div className="fixed top-0 right-0 h-screen w-[420px] z-50 bg-white border-l border-gray-200 shadow-2xl flex flex-col animate-slide-in-right">
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-gradient-to-r from-blue-50 via-cyan-50 to-teal-50">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 via-cyan-500 to-teal-500 flex items-center justify-center">
            <Bot className="w-4.5 h-4.5 text-white" />
          </div>
          <div>
            <div className="text-sm font-semibold text-gray-900">WebRPA小助手</div>
            <div className="text-[11px] text-gray-500">
              {configReady ? `模型：${resolvedConfig.model}` : '需要先配置模型'}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            title="新对话"
            onClick={handleNewSession}
            className="h-8 w-8 text-gray-600 hover:text-gray-900"
          >
            <Plus className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            title="历史对话"
            onClick={() => setShowSessions((v) => !v)}
            className="h-8 w-8 text-gray-600 hover:text-gray-900"
          >
            <History className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            title="关闭"
            onClick={() => setOpen(false)}
            className="h-8 w-8 text-gray-600 hover:text-gray-900"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* 会话列表抽屉 */}
      {showSessions && (
        <div className="border-b bg-gray-50/70 max-h-72 overflow-y-auto">
          {sessions.length === 0 ? (
            <div className="px-4 py-6 text-center text-xs text-gray-500">
              暂无历史对话
            </div>
          ) : (
            sessions.map((s) => (
              <div
                key={s.id}
                onClick={() => handleSelectSession(s.id)}
                className={`group flex items-start gap-2 px-4 py-2.5 cursor-pointer hover:bg-white transition-colors border-b border-gray-100 last:border-b-0 ${
                  s.id === currentSessionId ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {s.title}
                  </div>
                  <div className="text-[11px] text-gray-500 truncate mt-0.5">
                    {s.last_message_preview || `${s.message_count} 条消息`}
                  </div>
                </div>
                <button
                  onClick={(e) => handleDeleteSession(s.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all"
                  title="删除"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))
          )}
        </div>
      )}

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50/30">
        {messages.length === 0 && !isSending && (
          <div className="h-full flex flex-col items-center justify-center text-center px-6 py-8">
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 via-cyan-500 to-teal-500 flex items-center justify-center mb-3">
              <Bot className="w-7 h-7 text-white" />
            </div>
            <div className="text-base font-semibold text-gray-900 mb-1">
              你好，我是 WebRPA 小助手
            </div>
            <div className="text-xs text-gray-500 leading-relaxed max-w-[280px]">
              我了解 WebRPA 的方方面面，能帮你搭建工作流、运行任务、答疑解惑。
              直接告诉我你想做什么吧。
            </div>
            <div className="mt-4 flex flex-wrap gap-1.5 justify-center max-w-[300px]">
              {[
                '帮我新建一个打开网页的工作流',
                'WebRPA 怎么用？',
                '列出所有 AI 类模块',
                '我画布上有哪些节点？',
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="px-2.5 py-1 text-[11px] bg-white border border-gray-200 rounded-full text-gray-700 hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
            {!configReady && (
              <div className="mt-4 flex items-center gap-1.5 text-[11px] text-amber-600">
                <Settings className="w-3 h-3" />
                <span>请先在全局配置中填写小助手的模型信息</span>
              </div>
            )}
          </div>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        {isSending && (
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>小助手思考中…</span>
          </div>
        )}
        {error && (
          <div className="flex items-start gap-2 p-2.5 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
            <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
            <div className="flex-1">{error}</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区 */}
      <div className="border-t bg-white p-3">
        <div className="relative flex items-end gap-2 rounded-xl border border-gray-300 focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100 bg-white p-2 transition-all">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={configReady ? '告诉我你想做什么…（Enter 发送，Shift+Enter 换行）' : '请先配置模型'}
            rows={2}
            disabled={!configReady || isSending}
            className="flex-1 bg-transparent text-sm resize-none outline-none placeholder:text-gray-400 disabled:opacity-60 max-h-32"
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isSending || !configReady}
            size="icon"
            className="h-8 w-8 flex-shrink-0 bg-gradient-to-br from-blue-500 to-cyan-500 hover:opacity-90"
            title="发送"
          >
            {isSending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
        <div className="mt-1.5 flex items-center justify-between text-[10px] text-gray-400">
          <span>{resolvedConfig.enable_tools ? '已启用 Skills 工具调用' : 'Skills 已关闭'}</span>
          <span>WebRPA 小助手 · 由鸣航开发</span>
        </div>
      </div>
    </div>
  )
}
