import * as React from 'react'
import { cn } from '@/lib/utils'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:
    | 'default'      // 主品牌色（蓝填充，主操作）
    | 'destructive'  // 危险红填充（删除/停止）
    | 'outline'      // 品牌蓝弱底（次级，但带颜色，绝不像纯白）
    | 'secondary'    // 中性灰底（极少使用，仅当容器已有彩色时）
    | 'ghost'        // 弱品牌蓝底，不再透明
    | 'link'         // 文字链接
    | 'subtle'       // 中性灰
    | 'success'      // 成功绿填充（运行/上传/确认）
    | 'warning'      // 警告橙填充
    | 'info'         // 信息青填充
    | 'tonal'        // 品牌色弱调
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
     * - 任何按钮都不许是纯白底，至少要带功能色调
     * - 实心按钮（default/destructive/success/warning/info）：白字 + 阴影 + 功能色，最强调
     * - tonal-*：弱调（彩色 50 + 彩色 700），二级强调
     * - outline：默认就是品牌蓝弱底，绝不像纯白
     * - ghost：弱品牌蓝底，不再透明
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
        'bg-[hsl(var(--brand-50))] text-[hsl(var(--brand-700))] ' +
        'border border-[hsl(var(--brand-500)/0.3)] shadow-xs ' +
        'hover:bg-[hsl(var(--brand-100))] hover:border-[hsl(var(--brand-500)/0.5)] hover:shadow-soft ' +
        'active:bg-[hsl(var(--brand-100))]',
      secondary:
        'bg-[hsl(var(--slate-200))] text-[hsl(var(--slate-700))] border border-[hsl(var(--slate-300))] ' +
        'hover:bg-[hsl(var(--slate-300))] hover:border-[hsl(var(--slate-400))]',
      ghost:
        'bg-[hsl(var(--brand-50)/0.6)] text-[hsl(var(--brand-700))] border border-[hsl(var(--brand-500)/0.2)] ' +
        'hover:bg-[hsl(var(--brand-100))] hover:border-[hsl(var(--brand-500)/0.4)]',
      subtle:
        'bg-[hsl(var(--slate-100))] text-[hsl(var(--muted-foreground))] border border-[hsl(var(--slate-200))] ' +
        'hover:bg-[hsl(var(--slate-200))] hover:text-[hsl(var(--foreground))]',
      link:
        'text-[hsl(var(--primary))] underline-offset-4 hover:underline px-0 h-auto',
      tonal:
        'bg-[hsl(var(--brand-50))] text-[hsl(var(--brand-700))] border border-[hsl(var(--brand-500)/0.3)] ' +
        'hover:bg-[hsl(var(--brand-100))] hover:border-[hsl(var(--brand-500)/0.5)]',
      'tonal-success':
        'bg-[hsl(var(--success-50))] text-[hsl(var(--success-500))] border border-[hsl(var(--success-500)/0.3)] ' +
        'hover:bg-[hsl(138_70%_88%)] hover:border-[hsl(var(--success-500)/0.5)]',
      'tonal-warning':
        'bg-[hsl(var(--warning-50))] text-[hsl(var(--warning-500))] border border-[hsl(var(--warning-500)/0.3)] ' +
        'hover:bg-[hsl(48_94%_88%)] hover:border-[hsl(var(--warning-500)/0.5)]',
      'tonal-danger':
        'bg-[hsl(var(--danger-50))] text-[hsl(var(--danger-500))] border border-[hsl(var(--danger-500)/0.3)] ' +
        'hover:bg-[hsl(0_85%_90%)] hover:border-[hsl(var(--danger-500)/0.5)]',
      'tonal-info':
        'bg-[hsl(var(--info-50))] text-[hsl(var(--info-500))] border border-[hsl(var(--info-500)/0.3)] ' +
        'hover:bg-[hsl(199_90%_88%)] hover:border-[hsl(var(--info-500)/0.5)]',
    }

    const sizes: Record<NonNullable<ButtonProps['size']>, string> = {
      xs: 'h-6 px-2 text-[11px] gap-1',
      sm: 'h-7 px-2.5 text-[12px]',
      default: 'h-8 px-3',
      lg: 'h-10 px-5 text-[14px]',
      icon: 'h-8 w-8 p-0',
    }

    // ghost + icon 组合补强
    const ghostIconBoost =
      variant === 'ghost' && size === 'icon'
        ? 'bg-[hsl(var(--brand-50))] border border-[hsl(var(--brand-500)/0.3)] text-[hsl(var(--brand-700))] hover:bg-[hsl(var(--brand-100))] hover:border-[hsl(var(--brand-500)/0.5)]'
        : ''

    return (
      <button
        ref={ref}
        className={cn(base, variants[variant], sizes[size], ghostIconBoost, className)}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button }
