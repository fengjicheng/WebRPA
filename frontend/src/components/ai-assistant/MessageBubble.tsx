import { Bot, User, Wrench, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'
import type { ChatMessage, ToolCall } from '@/store/aiAssistantStore'

interface MessageBubbleProps {
  message: ChatMessage
}

function ToolCallCard({ tc }: { tc: ToolCall }) {
  const statusColor =
    tc.status === 'success'
      ? 'border-emerald-200 bg-emerald-50'
      : tc.status === 'failed'
      ? 'border-red-200 bg-red-50'
      : tc.status === 'running'
      ? 'border-blue-200 bg-blue-50'
      : 'border-gray-200 bg-gray-50'

  const statusIcon =
    tc.status === 'success' ? (
      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
    ) : tc.status === 'failed' ? (
      <AlertCircle className="w-3.5 h-3.5 text-red-600" />
    ) : tc.status === 'running' ? (
      <Loader2 className="w-3.5 h-3.5 text-blue-600 animate-spin" />
    ) : (
      <Wrench className="w-3.5 h-3.5 text-gray-600" />
    )

  return (
    <div className={`mt-2 rounded-lg border ${statusColor} p-2 text-xs`}>
      <div className="flex items-center gap-1.5 font-medium text-gray-800">
        {statusIcon}
        <span>{tc.name}</span>
        <span className="ml-auto text-[10px] uppercase opacity-60">{tc.status}</span>
      </div>
      {Object.keys(tc.arguments || {}).length > 0 && (
        <details className="mt-1.5 group">
          <summary className="cursor-pointer text-gray-500 hover:text-gray-800 select-none">
            参数
          </summary>
          <pre className="mt-1 p-2 bg-white/60 rounded text-[11px] overflow-x-auto whitespace-pre-wrap break-words">
{JSON.stringify(tc.arguments, null, 2)}
          </pre>
        </details>
      )}
      {tc.result !== undefined && tc.status === 'success' && (
        <details className="mt-1 group">
          <summary className="cursor-pointer text-gray-500 hover:text-gray-800 select-none">
            结果
          </summary>
          <pre className="mt-1 p-2 bg-white/60 rounded text-[11px] overflow-x-auto whitespace-pre-wrap break-words max-h-48">
{typeof tc.result === 'string' ? tc.result : JSON.stringify(tc.result, null, 2)}
          </pre>
        </details>
      )}
      {tc.error && (
        <div className="mt-1 text-red-600 text-[11px]">{tc.error}</div>
      )}
    </div>
  )
}

export function MessageBubble({ message }: MessageBubbleProps) {
  if (message.role === 'tool') {
    // tool 消息不直接展示，由对应 assistant 消息的 tool_calls 卡片显示
    return null
  }

  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-2.5 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-white ${
          isUser
            ? 'bg-gradient-to-br from-violet-500 to-purple-600'
            : 'bg-gradient-to-br from-blue-500 via-cyan-500 to-teal-500'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>
      <div className={`flex-1 min-w-0 ${isUser ? 'flex justify-end' : ''}`}>
        <div
          className={`inline-block max-w-full rounded-2xl px-3.5 py-2 text-sm ${
            isUser
              ? 'bg-blue-500 text-white rounded-tr-md'
              : 'bg-gray-100 text-gray-900 rounded-tl-md'
          }`}
        >
          {message.content && (
            <div className="whitespace-pre-wrap break-words">{message.content}</div>
          )}
          {!isUser && message.tool_calls && message.tool_calls.length > 0 && (
            <div className="mt-1 space-y-1.5">
              {message.tool_calls.map((tc) => (
                <ToolCallCard key={tc.id} tc={tc} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
