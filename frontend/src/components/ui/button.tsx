import * as React from 'react'
import { cn } from '@/lib/utils'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:
    | 'default'      // 主品牌色（蓝填充，主操作）
    | 'destructive'  // 危险红填充（删除/停止）
    | 'outline'      // 浅灰底+边框（最常用次级，明显"是按钮"）
    | 'secondary'    // 中灰填充（次级）
    | 'ghost'        // 透明，仅 hover 出底（图标按钮、菜单项用）
    | 'link'         // 文字链接
    | 'subtle'       // 极弱调，多用于内联
    | 'success'      // 成功绿填充（运行/上传/确认）
    | 'warning'      // 警告橙填充
    | 'info'         // 信息青填充
    | 'tonal'        // 品牌色弱调（蓝底白字的轻量版）
    | 'tonal-success'  // 绿弱调
    | 'tonal-warning'  // 橙弱调
    | 'tonal-danger'   // 红弱调
    | 'tonal-info'     // 青弱调
  size?: 'default' | 'sm' | 'lg' | 'icon' | 'xs'
  /** 兼容旧调用：禁用动效（新版本无装饰性动效，此参数仅作兼容占位） */
  noMotion?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', noMotion: _noMotion, ...props }, ref) => {
    const base =
      'inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-[6px] text-[13px] font-medium ' +
      'transition-[background-color,border-color,color,box-shadow,transform] duration-100 ' +
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))] focus-visible:ring-offset-1 focus-visible:ring-offset-[hsl(var(--background))] ' +
      'disabled:pointer-events-none disabled:opacity-50 select-none ' +
      'active:translate-y-px'

    /**
     * 设计原则：
     * - 实心按钮（default/destructive/success/warning/info）：白字 + 阴影 + 品牌色，最强调
     * - tonal-*：弱调（彩色 50 + 彩色 700），二级强调
     * - outline：浅灰底（slate-50）+ 1px 边框 + 极弱阴影，明显"是按钮"，覆盖大多数中性次级动作
     * - secondary：中灰填充，弱调容器
     * - ghost：透明，仅 icon 按钮使用，hover 浮起
     */
    const variants: Record<NonNullable<ButtonProps['variant']>, string> = {
      default:
        'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] shadow-soft ' +
        'hover:bg-[hsl(var(--brand-700))] hover:shadow-pop active:bg-[hsl(var(--brand-700))]',
      destructive:
        'bg-[hsl(var(--destructive))] text-[hsl(var(--destructive-foreground))] shadow-soft ' +
        'hover:brightness-110 hover:shadow-pop active:brightness-95',
      success:
        'bg-[hsl(var(--success-500))] text-white shadow-soft ' +
        'hover:brightness-110 hover:shadow-pop active:brightness-95',
      warning:
        'bg-[hsl(var(--warning-500))] text-white shadow-soft ' +
        'hover:brightness-110 hover:shadow-pop active:brightness-95',
      info:
        'bg-[hsl(var(--info-500))] text-white shadow-soft ' +
        'hover:brightness-110 hover:shadow-pop active:brightness-95',
      outline:
        'bg-[hsl(var(--slate-50))] text-[hsl(var(--foreground))] ' +
        'border border-[hsl(var(--slate-200))] shadow-xs ' +
        'hover:bg-[hsl(var(--card))] hover:border-[hsl(var(--slate-300))] hover:shadow-soft ' +
        'active:bg-[hsl(var(--slate-100))]',
      secondary:
        'bg-[hsl(var(--slate-100))] text-[hsl(var(--foreground))] border border-[hsl(var(--slate-200))] ' +
        'hover:bg-[hsl(var(--slate-200))] hover:border-[hsl(var(--slate-300))]',
      ghost:
        'text-[hsl(var(--foreground))] hover:bg-[hsl(var(--muted))]',
      subtle:
        'bg-transparent text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))]',
      link:
        'text-[hsl(var(--primary))] underline-offset-4 hover:underline px-0 h-auto',
      tonal:
        'bg-[hsl(var(--brand-50))] text-[hsl(var(--brand-700))] border border-[hsl(var(--brand-500)/0.22)] ' +
        'hover:bg-[hsl(var(--brand-100))] hover:border-[hsl(var(--brand-500)/0.4)]',
      'tonal-success':
        'bg-[hsl(var(--success-50))] text-[hsl(var(--success-500))] border border-[hsl(var(--success-500)/0.22)] ' +
        'hover:bg-[hsl(138_70%_92%)] hover:border-[hsl(var(--success-500)/0.4)]',
      'tonal-warning':
        'bg-[hsl(var(--warning-50))] text-[hsl(var(--warning-500))] border border-[hsl(var(--warning-500)/0.22)] ' +
        'hover:bg-[hsl(48_94%_92%)] hover:border-[hsl(var(--warning-500)/0.4)]',
      'tonal-danger':
        'bg-[hsl(var(--danger-50))] text-[hsl(var(--danger-500))] border border-[hsl(var(--danger-500)/0.22)] ' +
        'hover:bg-[hsl(0_85%_94%)] hover:border-[hsl(var(--danger-500)/0.4)]',
      'tonal-info':
        'bg-[hsl(var(--info-50))] text-[hsl(var(--info-500))] border border-[hsl(var(--info-500)/0.22)] ' +
        'hover:bg-[hsl(199_90%_92%)] hover:border-[hsl(var(--info-500)/0.4)]',
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
