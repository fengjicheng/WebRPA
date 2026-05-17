import * as React from 'react'
import { cn } from '@/lib/utils'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:
    | 'default'      // 主品牌色（蓝，主操作）
    | 'destructive'  // 危险红（删除/停止）
    | 'outline'      // 描边
    | 'secondary'    // 次级
    | 'ghost'        // 透明
    | 'link'         // 文字链接
    | 'subtle'       // 弱调
    | 'success'      // 成功绿（运行/启动/创建）
    | 'warning'      // 警告橙（待确认）
    | 'info'         // 信息青（下载/查看）
  size?: 'default' | 'sm' | 'lg' | 'icon' | 'xs'
  /** 兼容旧调用：禁用动效（新版本无装饰性动效，此参数仅作兼容占位） */
  noMotion?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', noMotion: _noMotion, ...props }, ref) => {
    const base =
      'inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-[6px] text-[13px] font-medium ' +
      'transition-[background-color,border-color,color,box-shadow] duration-100 ' +
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))] focus-visible:ring-offset-1 focus-visible:ring-offset-[hsl(var(--background))] ' +
      'disabled:pointer-events-none disabled:opacity-50 select-none'

    const variants: Record<NonNullable<ButtonProps['variant']>, string> = {
      default:
        'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] hover:bg-[hsl(var(--brand-700))] active:bg-[hsl(var(--brand-700))]',
      destructive:
        'bg-[hsl(var(--destructive))] text-[hsl(var(--destructive-foreground))] hover:opacity-90 active:opacity-95',
      outline:
        'border border-[hsl(var(--border))] bg-[hsl(var(--card))] text-[hsl(var(--foreground))] hover:bg-[hsl(var(--muted))]',
      secondary:
        'bg-[hsl(var(--secondary))] text-[hsl(var(--secondary-foreground))] hover:bg-[hsl(var(--muted))]',
      ghost:
        'text-[hsl(var(--foreground))] hover:bg-[hsl(var(--muted))]',
      subtle:
        'bg-[hsl(var(--muted))] text-[hsl(var(--foreground))] hover:bg-[hsl(var(--accent))]',
      link:
        'text-[hsl(var(--primary))] underline-offset-4 hover:underline px-0 h-auto',
      success:
        'bg-[hsl(var(--success-500))] text-white hover:brightness-110 active:brightness-95 shadow-sm',
      warning:
        'bg-[hsl(var(--warning-500))] text-white hover:brightness-110 active:brightness-95 shadow-sm',
      info:
        'bg-[hsl(var(--info-500))] text-white hover:brightness-110 active:brightness-95 shadow-sm',
    }

    const sizes: Record<NonNullable<ButtonProps['size']>, string> = {
      xs: 'h-6 px-2 text-[11px] gap-1',
      sm: 'h-7 px-2.5 text-[12px]',
      default: 'h-8 px-3',
      lg: 'h-10 px-5 text-[14px]',
      icon: 'h-8 w-8 p-0',
    }

    return (
      <button
        ref={ref}
        className={cn(base, variants[variant], sizes[size], className)}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button }
