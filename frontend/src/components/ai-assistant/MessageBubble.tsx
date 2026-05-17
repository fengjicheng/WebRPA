import {
  Sparkles,
  User,
  Wrench,
  AlertCircle,
  CheckCircle2,
  Loader2,
  ChevronRight,
} from 'lucide-react'
import { useState } from 'react'
import type { ChatMessage, ToolCall } from '@/store/aiAssistantStore'

interface MessageBubbleProps {
  message: ChatMessage
}

function ToolCallCard({ tc }: { tc: ToolCall }) {
  const [expanded, setExpanded] = useState(false)

  const statusClasses = (() => {
    switch (tc.status) {
      case 'success':
        return {
          bar: 'border-l-[hsl(var(--success-500))]',
          icon: 'text-[hsl(var(--success-500))]',
          label: 'badge-success',
          el: <CheckCircle2 className="w-3 h-3" />,
        }
      case 'failed':
        return {
          bar: 'border-l-[hsl(var(--danger-500))]',
          icon: 'text-[hsl(var(--danger-500))]',
          label: 'badge-danger',
          el: <AlertCircle className="w-3 h-3" />,
        }
      case 'running':
        return {
          bar: 'border-l-[hsl(var(--brand-500))]',
          icon: 'text-[hsl(var(--brand-500))]',
          label: 'badge-info',
          el: <Loader2 className="w-3 h-3 animate-spin" />,
        }
      default:
        return {
          bar: 'border-l-[hsl(var(--muted-foreground)/0.4)]',
          icon: 'text-[hsl(var(--muted-foreground))]',
          label: 'badge-default',
          el: <Wrench className="w-3 h-3" />,
        }
    }
  })()

  const hasArgs = tc.arguments && Object.keys(tc.arguments).length > 0
  const hasResult = tc.result !== undefined && tc.status === 'success'

  return (
    <div className={`rounded-[6px] border border-[hsl(var(--border))] bg-[hsl(var(--card))] border-l-2 ${statusClasses.bar} overflow-hidden`}>
      <button
        type="button"
        className="w-full flex items-center gap-2 px-2.5 py-1.5 text-left text-[12px] hover:bg-[hsl(var(--muted))] transition-colors has-hover-only"
        onClick={() => setExpanded((v) => !v)}
      >
        <span className={statusClasses.icon}>{statusClasses.el}</span>
        <code className="font-mono text-[11.5px] text-[hsl(var(--foreground))] truncate flex-1">
          {tc.name}
        </code>
        <span className={`badge ${statusClasses.label}`}>{tc.status}</span>
        <ChevronRight
          className={`w-3 h-3 text-[hsl(var(--muted-foreground))] transition-transform ${expanded ? 'rotate-90' : ''}`}
        />
      </button>
      {expanded && (hasArgs || hasResult || tc.error) && (
        <div className="px-2.5 pb-2 border-t border-[hsl(var(--border))] pt-2 space-y-2">
          {hasArgs && (
            <div>
              <div className="text-[10px] text-[hsl(var(--muted-foreground))] uppercase tracking-wide mb-1">
                参数
              </div>
              <pre className="text-[11px] p-2 rounded bg-[hsl(var(--muted))] border border-[hsl(var(--border))] overflow-x-auto whitespace-pre-wrap break-words">
{JSON.stringify(tc.arguments, null, 2)}
              </pre>
            </div>
          )}
          {hasResult && (
            <div>
              <div className="text-[10px] text-[hsl(var(--muted-foreground))] uppercase tracking-wide mb-1">
                结果
              </div>
              <pre className="text-[11px] p-2 rounded bg-[hsl(var(--muted))] border border-[hsl(var(--border))] overflow-x-auto whitespace-pre-wrap break-words max-h-56">
{typeof tc.result === 'string' ? tc.result : JSON.stringify(tc.result, null, 2)}
              </pre>
            </div>
          )}
          {tc.error && (
            <div className="text-[11px] text-[hsl(var(--danger-500))]">
              {tc.error}
            </div>
          )}
        </div>
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
        className={
          'flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center ' +
          (isUser
            ? 'bg-[hsl(var(--muted))] text-[hsl(var(--foreground))] border border-[hsl(var(--border))]'
            : 'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]')
        }
      >
        {isUser ? <User className="w-3.5 h-3.5" /> : <Sparkles className="w-3.5 h-3.5" />}
      </div>
      <div className={`flex-1 min-w-0 ${isUser ? 'flex justify-end' : ''}`}>
        <div className="inline-block max-w-full space-y-1.5">
          {message.content && (
            <div
              className={
                'inline-block max-w-full rounded-[8px] px-3 py-2 text-[13px] leading-relaxed prose-compact ' +
                (isUser
                  ? 'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]'
                  : 'bg-[hsl(var(--muted))] text-[hsl(var(--foreground))]')
              }
            >
              <div className="whitespace-pre-wrap break-words">{message.content}</div>
            </div>
          )}
          {!isUser && message.tool_calls && message.tool_calls.length > 0 && (
            <div className="space-y-1.5 max-w-[420px]">
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
