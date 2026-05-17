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
          'flex h-8 w-full rounded-[6px] border border-[hsl(var(--slate-200))] bg-[hsl(var(--slate-50))] px-2.5 py-1 text-[13px] ' +
            'text-[hsl(var(--foreground))] placeholder:text-[hsl(var(--muted-foreground))] ' +
            'shadow-[inset_0_1px_2px_rgb(15_23_42_/_0.04)] ' +
            'transition-[border-color,box-shadow,background-color] duration-100 ' +
            'hover:border-[hsl(var(--slate-300))] hover:bg-[hsl(var(--card))] ' +
            'focus-visible:outline-none focus-visible:border-[hsl(var(--brand-500))] focus-visible:bg-[hsl(var(--card))] focus-visible:ring-2 focus-visible:ring-[hsl(var(--brand-500)/0.18)] ' +
            'disabled:cursor-not-allowed disabled:opacity-50 ' +
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
