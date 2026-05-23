import {
  Sparkles,
  User,
  Wrench,
  AlertCircle,
  CheckCircle2,
  Loader2,
  ChevronRight,
} from 'lucide-react'
import { useState, useMemo } from 'react'
import { marked } from 'marked'
import type { ChatMessage, ToolCall } from '@/store/aiAssistantStore'

// marked 配置 - 启用 GFM (GitHub 风格 Markdown：表格/任务列表/删除线/换行)
marked.setOptions({
  gfm: true,
  breaks: true,
})

interface MessageBubbleProps {
  message: ChatMessage
}

// 把 marked 输出的 HTML 包成可交互的 React 内容
function MarkdownContent({ content }: { content: string }) {
  const html = useMemo(() => {
    try {
      return marked.parse(content) as string
    } catch {
      return content.replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
      }[c] || c))
    }
  }, [content])

  return (
    <div className="ai-md">
      <div
        className="ai-md-body"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </div>
  )
}

function ToolCallCard({ tc }: { tc: ToolCall }) {
  const [expanded, setExpanded] = useState(false)

  const styling = (() => {
    switch (tc.status) {
      case 'success':
        return {
          border: 'border-l-[3px] border-l-[hsl(var(--success-500))]',
          chip: 'icon-chip icon-chip-success',
          status: 'badge-success',
          el: <CheckCircle2 className="w-3.5 h-3.5" />,
          dot: 'bg-[hsl(var(--success-500))]',
        }
      case 'failed':
        return {
          border: 'border-l-[3px] border-l-[hsl(var(--danger-500))]',
          chip: 'icon-chip icon-chip-danger',
          status: 'badge-danger',
          el: <AlertCircle className="w-3.5 h-3.5" />,
          dot: 'bg-[hsl(var(--danger-500))]',
        }
      case 'running':
        return {
          border: 'border-l-[3px] border-l-[hsl(var(--brand-500))]',
          chip: 'icon-chip icon-chip-brand',
          status: 'badge-brand',
          el: <Loader2 className="w-3.5 h-3.5 animate-spin" />,
          dot: 'bg-[hsl(var(--brand-500))] animate-pulse',
        }
      default:
        return {
          border: 'border-l-[3px] border-l-[hsl(var(--slate-300))]',
          chip: 'icon-chip icon-chip-slate',
          status: 'badge-default',
          el: <Wrench className="w-3.5 h-3.5" />,
          dot: 'bg-[hsl(var(--slate-400))]',
        }
    }
  })()

  const hasArgs = tc.arguments && Object.keys(tc.arguments).length > 0
  const hasResult = tc.result !== undefined && tc.status === 'success'

  return (
    <div
      className={`rounded-[10px] border border-[hsl(var(--border))] bg-[hsl(var(--card))] ${styling.border} overflow-hidden shadow-xs transition-shadow hover:shadow-soft`}
    >
      <button
        type="button"
        className="w-full flex items-center gap-2 px-2.5 py-2 text-left hover:bg-[hsl(var(--brand-50)/0.4)] transition-colors duration-150"
        onClick={() => setExpanded((v) => !v)}
      >
        <span className={styling.chip}>{styling.el}</span>
        <code className="font-mono text-[12px] text-[hsl(var(--slate-800))] truncate flex-1 font-medium">
          {tc.name}
        </code>
        <span className={`badge ${styling.status}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${styling.dot}`} />
          {tc.status}
        </span>
        <ChevronRight
          className={`w-3.5 h-3.5 text-[hsl(var(--muted-foreground))] transition-transform duration-200 ${
            expanded ? 'rotate-90' : ''
          }`}
        />
      </button>
      {expanded && (hasArgs || hasResult || tc.error) && (
        <div className="px-2.5 pb-2.5 border-t border-[hsl(var(--border))] pt-2.5 space-y-2 animate-fade-in-up bg-[hsl(var(--slate-50)/0.5)]">
          {hasArgs && (
            <div>
              <div className="text-[10px] text-[hsl(var(--muted-foreground))] uppercase tracking-wider font-semibold mb-1.5">
                参数
              </div>
              <pre className="text-[11px] p-2.5 rounded-[6px] bg-[hsl(var(--slate-900))] text-[hsl(var(--slate-100))] overflow-x-auto whitespace-pre-wrap break-words shadow-soft">
{JSON.stringify(tc.arguments, null, 2)}
              </pre>
            </div>
          )}
          {hasResult && (
            <div>
              <div className="text-[10px] text-[hsl(var(--muted-foreground))] uppercase tracking-wider font-semibold mb-1.5">
                结果
              </div>
              <pre className="text-[11px] p-2.5 rounded-[6px] bg-[hsl(var(--slate-900))] text-[hsl(var(--slate-100))] overflow-x-auto whitespace-pre-wrap break-words max-h-56 shadow-soft">
{typeof tc.result === 'string' ? tc.result : JSON.stringify(tc.result, null, 2)}
              </pre>
            </div>
          )}
          {tc.error && (
            <div className="status-row status-row-danger text-[12px]">
              <AlertCircle className="w-3.5 h-3.5 shrink-0" />
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
    return null
  }

  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''} animate-fade-in-up`}>
      {/* 头像 */}
      <div
        className={
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-soft ' +
          (isUser
            ? 'bg-gradient-to-br from-[hsl(var(--slate-100))] to-[hsl(var(--slate-200))] text-[hsl(var(--slate-700))] border border-[hsl(var(--slate-300))]'
            : 'bg-gradient-to-br from-[hsl(var(--brand-500))] to-[hsl(var(--brand-700))] text-white shadow-brand-glow')
        }
      >
        {isUser ? <User className="w-4 h-4" /> : <Sparkles className="w-4 h-4" strokeWidth={2.4} />}
      </div>

      <div className={`flex-1 min-w-0 ${isUser ? 'flex justify-end' : ''}`}>
        <div className={`inline-block ${isUser ? 'max-w-[85%]' : 'max-w-full w-full'} space-y-2`}>
          {message.content && (
            <div
              className={
                isUser
                  ? 'inline-block max-w-full px-3.5 py-2.5 text-[13px] leading-relaxed bg-gradient-to-br from-[hsl(var(--brand-500))] to-[hsl(var(--brand-600))] text-white rounded-[14px] rounded-tr-[4px] shadow-brand-glow whitespace-pre-wrap break-words'
                  : 'block max-w-full px-4 py-3 text-[13.5px] bg-[hsl(var(--card))] text-[hsl(var(--slate-800))] rounded-[14px] rounded-tl-[4px] border border-[hsl(var(--border))] shadow-soft'
              }
            >
              {isUser ? (
                <div>{message.content}</div>
              ) : (
                <MarkdownContent content={message.content} />
              )}
            </div>
          )}
          {!isUser && message.tool_calls && message.tool_calls.length > 0 && (
            <div className="space-y-1.5 max-w-[440px]">
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
