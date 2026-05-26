import React from 'react'
import { useWorkflowStore } from '@/store/workflowStore'

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: string
}

/**
 * 编辑器级 Error Boundary
 *
 * 目的：避免 react-flow 内部脏节点崩溃导致整个编辑器白屏。
 * 一旦内部组件抛错，显示友好的错误页 + 「清空画布」「刷新页面」恢复按钮。
 *
 * 经历过的事故：旧工作流文件里某个节点没有 position 字段，react-flow 内部
 * getNodePositionWithOrigin 抛 TypeError，整个编辑器白屏，用户什么都做不了。
 */
export class WorkflowErrorBoundary extends React.Component<{ children: React.ReactNode }, State> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: '' }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: '' }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[WorkflowErrorBoundary] 编辑器渲染错误：', error, info)
    this.setState({ errorInfo: info.componentStack || '' })
  }

  handleClearCanvas = () => {
    try {
      useWorkflowStore.getState().clearWorkflow()
    } catch (e) {
      console.error('清空画布失败', e)
    }
    this.setState({ hasError: false, error: null, errorInfo: '' })
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (!this.state.hasError) return this.props.children
    const err = this.state.error
    return (
      <div className="w-full h-full flex items-center justify-center bg-[hsl(var(--background))] p-8">
        <div className="max-w-2xl w-full bg-[hsl(var(--card))] rounded-2xl p-8 border border-[hsl(var(--danger-500)/0.3)] shadow-pop-lg">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-full bg-[hsl(var(--danger-500)/0.12)] flex items-center justify-center shrink-0">
              <svg className="w-6 h-6 text-[hsl(var(--danger-500))]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-bold text-[hsl(var(--foreground))] mb-1">编辑器遇到了一个问题</h2>
              <p className="text-sm text-[hsl(var(--slate-600))] mb-4">
                通常是因为打开的工作流文件含有损坏的节点数据。可以点下方「清空画布」恢复使用，已保存的工作流不会受影响。
              </p>
              {err && (
                <details className="mb-4 text-xs">
                  <summary className="cursor-pointer text-[hsl(var(--slate-700))] hover:text-[hsl(var(--brand-600))]">
                    查看错误详情
                  </summary>
                  <pre className="mt-2 p-3 bg-[hsl(var(--slate-100))] rounded-md overflow-auto max-h-48 text-[hsl(var(--slate-800))]">
                    {err.message}
                    {err.stack ? '\n\n' + err.stack : ''}
                  </pre>
                </details>
              )}
              <div className="flex gap-2">
                <button
                  onClick={this.handleClearCanvas}
                  className="px-4 py-2 rounded-lg bg-[hsl(var(--brand-600))] hover:bg-[hsl(var(--brand-700))] text-white text-sm font-medium transition-colors"
                >
                  清空画布并继续
                </button>
                <button
                  onClick={this.handleReload}
                  className="px-4 py-2 rounded-lg bg-[hsl(var(--slate-100))] hover:bg-[hsl(var(--slate-200))] text-[hsl(var(--slate-800))] text-sm font-medium transition-colors"
                >
                  刷新页面
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }
}
