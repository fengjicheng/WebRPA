import { Button } from './button'
import { AlertTriangle, Info, HelpCircle, CheckCircle2 } from 'lucide-react'

export type ConfirmDialogType = 'confirm' | 'alert' | 'warning' | 'success'

interface ConfirmDialogProps {
  isOpen: boolean
  type?: ConfirmDialogType
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  onConfirm: () => void
  onCancel?: () => void
}

export function ConfirmDialog({
  isOpen,
  type = 'confirm',
  title,
  message,
  confirmText = '确定',
  cancelText = '取消',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!isOpen) return null

  const isAlertOnly = type === 'alert'

  const icon = (() => {
    switch (type) {
      case 'warning':
        return <AlertTriangle className="w-5 h-5" strokeWidth={2.2} />
      case 'alert':
        return <Info className="w-5 h-5" strokeWidth={2.2} />
      case 'success':
        return <CheckCircle2 className="w-5 h-5" strokeWidth={2.2} />
      default:
        return <HelpCircle className="w-5 h-5" strokeWidth={2.2} />
    }
  })()

  // 图标视觉：彩色徽章 + 同色光晕环
  const iconStyle = (() => {
    switch (type) {
      case 'warning':
        return {
          bg: 'bg-[hsl(var(--warning-50))] text-[hsl(var(--warning-600))] border border-[hsl(var(--warning-500)/0.3)]',
          ring: 'ring-[6px] ring-[hsl(var(--warning-500)/0.12)]',
        }
      case 'success':
        return {
          bg: 'bg-[hsl(var(--success-50))] text-[hsl(var(--success-600))] border border-[hsl(var(--success-500)/0.3)]',
          ring: 'ring-[6px] ring-[hsl(var(--success-500)/0.12)]',
        }
      case 'alert':
        return {
          bg: 'bg-[hsl(var(--info-50))] text-[hsl(var(--info-600))] border border-[hsl(var(--info-500)/0.3)]',
          ring: 'ring-[6px] ring-[hsl(var(--info-500)/0.12)]',
        }
      default:
        return {
          bg: 'bg-[hsl(var(--brand-50))] text-[hsl(var(--brand-600))] border border-[hsl(var(--brand-500)/0.3)]',
          ring: 'ring-[6px] ring-[hsl(var(--brand-500)/0.12)]',
        }
    }
  })()

  // 顶部装饰条颜色
  const stripeColor = (() => {
    switch (type) {
      case 'warning': return 'from-[hsl(var(--warning-500))] to-[hsl(var(--warning-400))]'
      case 'success': return 'from-[hsl(var(--success-500))] to-[hsl(var(--success-400))]'
      case 'alert':   return 'from-[hsl(var(--info-500))] to-[hsl(var(--info-400))]'
      default:        return 'from-[hsl(var(--brand-500))] to-[hsl(var(--brand-400))]'
    }
  })()

  const titleText = title ?? {
    warning: '警告',
    alert: '提示',
    success: '成功',
    confirm: '确认',
  }[type]

  return (
    <div
      className="fixed inset-0 z-[100] bg-[hsl(217_45%_15%_/_0.55)] backdrop-blur-[3px] flex items-center justify-center p-4 animate-fade-in"
      onClick={() => {
        if (!isAlertOnly && onCancel) onCancel()
      }}
    >
      <div
        className="relative bg-[hsl(var(--card))] rounded-[14px] border border-[hsl(var(--border))] shadow-pop-2xl w-full max-w-sm overflow-hidden animate-scale-in-bounce"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 顶部彩色装饰条 */}
        <div className={`absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r ${stripeColor}`} />

        <div className="p-5 pt-6">
          <div className="flex items-start gap-3.5">
            <div className={`shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${iconStyle.bg} ${iconStyle.ring}`}>
              {icon}
            </div>
            <div className="flex-1 min-w-0 pt-1">
              <h3 className="text-[15px] font-semibold text-[hsl(var(--slate-900))] mb-1.5 tracking-tight">
                {titleText}
              </h3>
              <p className="text-[13px] leading-relaxed text-[hsl(var(--slate-600))] whitespace-pre-wrap">
                {message}
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 px-5 py-3.5 bg-[hsl(var(--slate-50))] border-t border-[hsl(var(--border))]">
          {!isAlertOnly && onCancel && (
            <Button variant="secondary" size="sm" onClick={onCancel}>
              {cancelText}
            </Button>
          )}
          <Button
            size="sm"
            variant={
              type === 'warning' ? 'destructive'
              : 'success'
            }
            onClick={onConfirm}
          >
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  )
}

// 用于创建全局确认对话框的 hook
import { useState, useCallback } from 'react'

interface UseConfirmOptions {
  type?: ConfirmDialogType
  title?: string
  confirmText?: string
  cancelText?: string
}

export function useConfirm() {
  const [state, setState] = useState<{
    isOpen: boolean
    message: string
    options: UseConfirmOptions
    resolve: ((value: boolean) => void) | null
  }>({
    isOpen: false,
    message: '',
    options: {},
    resolve: null,
  })

  const confirm = useCallback((message: string, options: UseConfirmOptions = {}) => {
    return new Promise<boolean>((resolve) => {
      setState({
        isOpen: true,
        message,
        options,
        resolve,
      })
    })
  }, [])

  const alert = useCallback((message: string, options: Omit<UseConfirmOptions, 'type'> = {}) => {
    return new Promise<boolean>((resolve) => {
      setState({
        isOpen: true,
        message,
        options: { ...options, type: 'alert' },
        resolve,
      })
    })
  }, [])

  const handleConfirm = useCallback(() => {
    state.resolve?.(true)
    setState((prev) => ({ ...prev, isOpen: false, resolve: null }))
  }, [state.resolve])

  const handleCancel = useCallback(() => {
    state.resolve?.(false)
    setState((prev) => ({ ...prev, isOpen: false, resolve: null }))
  }, [state.resolve])

  const ConfirmDialogComponent = () => (
    <ConfirmDialog
      isOpen={state.isOpen}
      type={state.options.type}
      title={state.options.title}
      message={state.message}
      confirmText={state.options.confirmText}
      cancelText={state.options.cancelText}
      onConfirm={handleConfirm}
      onCancel={handleCancel}
    />
  )

  return {
    confirm,
    alert,
    ConfirmDialog: ConfirmDialogComponent,
  }
}
