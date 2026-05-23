import * as React from 'react'
import { cn } from '@/lib/utils'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        ref={ref}
        className={cn(
          // 基础容器
          'flex h-8 w-full rounded-[7px] px-2.5 py-1 text-[13px] ' +
            'border border-[hsl(var(--slate-200))] bg-[hsl(var(--slate-50))] ' +
            'text-[hsl(var(--foreground))] placeholder:text-[hsl(var(--muted-foreground))] ' +
            // 内嵌微阴影 - 提升输入感
            'shadow-[inset_0_1px_2px_rgb(15_23_42_/_0.04)] ' +
            // 过渡
            'transition-[border-color,box-shadow,background-color] duration-150 ease-[cubic-bezier(0.25,1,0.5,1)] ' +
            // 悬浮：浅色升起
            'hover:border-[hsl(var(--slate-300))] hover:bg-[hsl(var(--card))] ' +
            // 聚焦：蓝边 + 蓝光环
            'focus-visible:outline-none focus-visible:border-[hsl(var(--brand-500))] focus-visible:bg-[hsl(var(--card))] focus-visible:ring-2 focus-visible:ring-[hsl(var(--brand-500)/0.18)] ' +
            // 禁用
            'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-[hsl(var(--muted))] ' +
            // 无效
            'aria-[invalid=true]:border-[hsl(var(--danger-500))] aria-[invalid=true]:ring-[hsl(var(--danger-500)/0.18)] ' +
            // 文件
            'file:border-0 file:bg-transparent file:text-[12px] file:font-medium file:text-[hsl(var(--foreground))]',
          className
        )}
        {...props}
      />
    )
  }
)
Input.displayName = 'Input'

export { Input }
