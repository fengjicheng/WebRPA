import {
  Sparkles,
  User,
  Wrench,
  AlertCircle,
  CheckCircle2,
  Loader2,
  ChevronRight,
  ChevronDown,
  Brain,
} from 'lucide-react'
import { useState, useMemo, useEffect, useRef } from 'react'
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

// 工具名 → 中文显示
const TOOL_NAME_LABELS: Record<string, string> = {
  client_action: '操作 WebRPA',
  build_workflow: '设计工作流',
  build_node: '构造节点',
  describe_module: '查询模块用法',
  list_module_categories: '列出模块分类',
  list_modules_in_category: '列出分类下模块',
  search_modules: '搜索模块',
  list_workflows: '列出本地工作流',
  read_workflow: '读取本地工作流',
  save_workflow_file: '保存工作流到本地',
  delete_workflow: '删除工作流',
  list_executors: '列出执行器',
  list_canvas_executors: '列出画布可用执行器',
  list_custom_modules: '列出自定义模块',
  list_scheduled_tasks: '列出计划任务',
  get_recent_logs: '获取近期执行日志',
  get_full_snapshot: '获取项目全量快照',
  list_global_variables: '读取全局变量',
  get_scheduled_task: '查看计划任务',
  get_scheduled_task_logs: '读计划任务日志',
  list_data_assets: '列出 Excel 资源',
  list_image_assets: '列出图像资源',
  get_custom_module: '读取自定义模块',
  search_in_workflows: '全文搜索工作流',
  summarize_workflow: '工作流结构摘要',
  remember: '记住信息',
  recall: '回忆信息',
  forget: '遗忘记忆',
  get_global_config_keys: '查全局配置项',
}

// client_action 的 action 字段中文化
const CLIENT_ACTION_LABELS: Record<string, string> = {
  new_workflow: '新建工作流',
  load_workflow: '打开工作流',
  load_workflow_from_data: '装载工作流到画布',
  save_workflow: '保存工作流',
  run_workflow: '运行工作流（有头）',
  run_workflow_headless: '运行工作流（无头）',
  stop_workflow: '停止运行',
  export_workflow: '导出工作流',
  rename_workflow: '重命名工作流',
  get_workflow_detail: '读取画布详情',
  get_logs: '读取日志',
  get_collected_data: '读取数据表',
  add_nodes: '添加节点',
  delete_node: '删除节点',
  delete_nodes: '批量删除节点',
  update_node_config: '修改节点配置',
  focus_node: '聚焦节点',
  toggle_node_disabled: '启用/禁用节点',
  align_nodes: '对齐节点',
  copy_nodes: '复制节点',
  paste_nodes: '粘贴节点',
  move_node: '移动节点',
  rename_node: '重命名节点',
  find_nodes_by_type: '按类型查找节点',
  connect_nodes: '连接节点',
  disconnect_edge: '删除连线',
  select_all_nodes: '全选节点',
  clear_selection: '取消选中',
  fit_view: '适配画布',
  run_single_node: '运行单节点',
  undo: '撤销',
  redo: '重做',
  add_variable: '新增变量',
  update_variable: '更新变量',
  delete_variable: '删除变量',
  rename_variable: '重命名变量',
  list_variables: '列出变量',
  clear_logs: '清空日志',
  clear_data: '清空数据',
  set_verbose_log: '切换详细日志',
  set_max_log_count: '设置日志条数',
  export_logs: '导出日志',
  download_data: '下载数据',
  upload_excel: '上传 Excel',
  upload_image: '上传图片',
  add_log: '添加日志',
  switch_bottom_panel: '切换底栏',
  open_global_config: '打开全局配置',
  close_global_config: '关闭全局配置',
  open_local_workflow_dialog: '打开本地工作流',
  close_local_workflow_dialog: '关闭本地工作流',
  open_scheduled_tasks: '打开计划任务',
  close_scheduled_tasks: '关闭计划任务',
  open_documentation: '打开文档',
  close_documentation: '关闭文档',
  open_workflow_hub: '打开工作流仓库',
  close_workflow_hub: '关闭工作流仓库',
  open_auto_browser: '打开自动化浏览器',
  close_auto_browser: '关闭自动化浏览器',
  open_phone_mirror: '打开手机投屏',
  close_phone_mirror: '关闭手机投屏',
  open_variable_tracking: '打开变量追踪',
  close_variable_tracking: '关闭变量追踪',
  open_screensaver: '打开屏保弹幕配置',
  close_screensaver: '关闭屏保弹幕配置',
  start_screensaver: '启动屏保弹幕',
  stop_screensaver: '停止屏保弹幕',
  get_screensaver_status: '查询屏保状态',
  open_export_dialog: '打开导出对话框',
  open_module_search: '打开模块搜索框',
  take_screenshot: '触发截图',
  get_global_config: '读取全局配置',
  update_global_config: '更新全局配置',
  show_toast: '显示提示',
}

function getToolLabel(tc: ToolCall): { label: string; sublabel?: string } {
  const base = TOOL_NAME_LABELS[tc.name] || tc.name
  if (tc.name === 'client_action') {
    const action = (tc.arguments as any)?.action
    const actionLabel = action ? (CLIENT_ACTION_LABELS[action] || action) : ''
    return { label: actionLabel || base, sublabel: action }
  }
  if (tc.name === 'describe_module' || tc.name === 'search_modules') {
    const arg = (tc.arguments as any)?.module_type || (tc.arguments as any)?.keyword
    return { label: base, sublabel: arg ? String(arg) : undefined }
  }
  if (tc.name === 'build_workflow') {
    const name = (tc.arguments as any)?.name
    return { label: base, sublabel: name }
  }
  return { label: base }
}

const STATUS_LABELS: Record<string, string> = {
  pending: '待执行',
  running: '执行中',
  success: '已完成',
  failed: '失败',
  rejected: '已拒绝',
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
  const { label, sublabel } = getToolLabel(tc)

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
        <div className="flex-1 min-w-0 flex flex-col">
          <div className="text-[12.5px] text-[hsl(var(--slate-800))] font-medium leading-tight truncate">
            {label}
          </div>
          {sublabel && (
            <code className="font-mono text-[10.5px] text-[hsl(var(--muted-foreground))] truncate leading-tight mt-0.5">
              {sublabel}
            </code>
          )}
        </div>
        <span className={`badge ${styling.status}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${styling.dot}`} />
          {STATUS_LABELS[tc.status] || tc.status}
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

// 思考过程卡片：
//  - 思考中：自动展开 + 内容自动滚到底部
//  - 思考结束（出现 content 或 tool_calls）：自动收起
//  - 用户主动点过 → 完全尊重用户的选择
function ReasoningCard({
  content,
  isThinking,
  durationSec,
}: {
  content: string
  isThinking: boolean
  durationSec?: number
}) {
  // 用户是否手动操作过（true=主动展开，false=主动收起，null=未操作）
  const [userExpanded, setUserExpanded] = useState<boolean | null>(null)
  // 是否曾经检测到思考已结束 - 一旦结束就锁定为 false（避免某些边缘情况下又翻回来）
  const [thinkingFinished, setThinkingFinished] = useState(false)
  const bodyRef = useRef<HTMLDivElement>(null)

  // 思考结束触发 - 一旦从 thinking → not thinking，永久标记为已结束
  useEffect(() => {
    if (!isThinking) {
      setThinkingFinished(true)
    }
  }, [isThinking])

  // 用户没操作过：展开状态 = 思考中（思考时展开，思考完收起）
  // 用户操作过：完全用用户的选择
  const expanded = userExpanded !== null ? userExpanded : (isThinking && !thinkingFinished)

  // 思考过程中内容增长时自动滚到最底部（让用户看到最新思考内容）
  useEffect(() => {
    if (!expanded || !isThinking) return
    const el = bodyRef.current
    if (!el) return
    // 用 rAF 确保 DOM 已经渲染完新内容再滚
    const raf = requestAnimationFrame(() => {
      el.scrollTop = el.scrollHeight
    })
    return () => cancelAnimationFrame(raf)
  }, [content, expanded, isThinking])

  const headerLabel = isThinking
    ? '思考中…'
    : durationSec != null
      ? `已思考 ${durationSec.toFixed(1)} 秒`
      : '已完成思考'

  return (
    <div className="rounded-[12px] border border-[hsl(var(--brand-500)/0.18)] bg-[hsl(var(--brand-50)/0.5)] overflow-hidden">
      <button
        type="button"
        onClick={() => setUserExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 text-[12.5px] font-medium text-[hsl(var(--brand-700))] hover:bg-[hsl(var(--brand-100)/0.5)] transition-colors"
      >
        <Brain className={`w-3.5 h-3.5 ${isThinking ? 'animate-pulse' : ''}`} />
        <span className="flex-1 text-left">{headerLabel}</span>
        {expanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
      </button>
      {expanded && (
        <div
          ref={bodyRef}
          className="px-3 pb-3 pt-1 text-[12.5px] leading-relaxed text-[hsl(var(--slate-600))] whitespace-pre-wrap break-words border-t border-[hsl(var(--brand-500)/0.1)] max-h-[400px] overflow-y-auto"
        >
          {content || '（暂无思考内容）'}
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
          {/* 思考过程（仅 assistant 且模型返回了非空 reasoning_content 时） */}
          {!isUser && message.reasoning_content && message.reasoning_content.trim() && (
            <ReasoningCard
              content={message.reasoning_content}
              isThinking={!message.content && !(message.tool_calls && message.tool_calls.length > 0)}
              durationSec={(message as any).thinking_duration_sec}
            />
          )}
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
