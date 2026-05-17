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
        return <AlertTriangle className="w-4 h-4" />
      case 'alert':
        return <Info className="w-4 h-4" />
      case 'success':
        return <CheckCircle2 className="w-4 h-4" />
      default:
        return <HelpCircle className="w-4 h-4" />
    }
  })()

  const iconBg = (() => {
    switch (type) {
      case 'warning':
        return 'bg-[hsl(var(--warning-50))] text-[hsl(var(--warning-500))]'
      case 'success':
        return 'bg-[hsl(var(--success-50))] text-[hsl(var(--success-500))]'
      default:
        return 'bg-[hsl(var(--info-50))] text-[hsl(var(--info-500))]'
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
      className="fixed inset-0 z-[100] bg-black/40 backdrop-blur-[2px] flex items-center justify-center p-4 animate-fade-in"
      onClick={() => {
        if (!isAlertOnly && onCancel) onCancel()
      }}
    >
      <div
        className="bg-[hsl(var(--card))] rounded-[10px] border border-[hsl(var(--border))] shadow-pop-xl w-full max-w-sm overflow-hidden animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5">
          <div className="flex items-start gap-3">
            <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${iconBg}`}>
              {icon}
            </div>
            <div className="flex-1 min-w-0 pt-0.5">
              <h3 className="text-[14px] font-semibold text-[hsl(var(--foreground))] mb-1">
                {titleText}
              </h3>
              <p className="text-[12.5px] leading-relaxed text-[hsl(var(--muted-foreground))] whitespace-pre-wrap">
                {message}
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center justify-end gap-2 px-5 py-3 bg-[hsl(var(--muted))] border-t border-[hsl(var(--border))]">
          {!isAlertOnly && onCancel && (
            <Button variant="outline" size="sm" onClick={onCancel}>
              {cancelText}
            </Button>
          )}
          <Button
            size="sm"
            variant={type === 'warning' ? 'destructive' : 'default'}
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
