/**
 * Progress 组件 - 进度条
 * 视觉：浅灰底 + 品牌蓝填充 + 流光高亮
 */

interface ProgressProps {
  value?: number
  className?: string
  /** 进度条颜色变体 */
  variant?: 'default' | 'success' | 'warning' | 'danger'
  /** 不确定进度（流动动画） */
  indeterminate?: boolean
}

export function Progress({
  value = 0,
  className = '',
  variant = 'default',
  indeterminate,
}: ProgressProps) {
  const colorMap = {
    default: 'from-[hsl(var(--brand-500))] to-[hsl(var(--brand-600))]',
    success: 'from-[hsl(var(--success-500))] to-[hsl(var(--success-600))]',
    warning: 'from-[hsl(var(--warning-500))] to-[hsl(var(--warning-600))]',
    danger:  'from-[hsl(var(--danger-500))]  to-[hsl(var(--danger-600))]',
  }

  if (indeterminate) {
    return (
      <div
        className={`relative h-1.5 w-full overflow-hidden rounded-full bg-[hsl(var(--slate-100))] ${className}`}
      >
        <div
          className={`absolute inset-y-0 w-[30%] rounded-full bg-gradient-to-r ${colorMap[variant]}`}
          style={{ animation: 'progressIndeterminate 1.4s cubic-bezier(0.4, 0, 0.2, 1) infinite' }}
        />
      </div>
    )
  }

  const safeValue = Math.min(100, Math.max(0, value))

  return (
    <div
      className={`relative h-1.5 w-full overflow-hidden rounded-full bg-[hsl(var(--slate-100))] ${className}`}
    >
      <div
        className={`relative h-full bg-gradient-to-r ${colorMap[variant]} rounded-full transition-[width] duration-300 ease-[cubic-bezier(0.25,1,0.5,1)]`}
        style={{ width: `${safeValue}%` }}
      >
        {/* 高光扫过 */}
        <div
          className="absolute inset-0 opacity-50 rounded-full"
          style={{
            background:
              'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.4) 50%, transparent 100%)',
            animation: 'shimmer 2.2s linear infinite',
            backgroundSize: '200% 100%',
          }}
        />
      </div>
    </div>
  )
}
