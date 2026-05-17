import * as React from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown } from 'lucide-react'

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {}

const SelectNative = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div className="relative">
        <select
          className={cn(
            'flex h-8 w-full appearance-none rounded-[6px] border border-[hsl(var(--slate-200))] bg-[hsl(var(--slate-50))] px-2.5 py-1 pr-8 text-[13px] ' +
              'text-[hsl(var(--foreground))] ' +
              'shadow-[inset_0_1px_2px_rgb(15_23_42_/_0.04)] ' +
              'transition-[border-color,background-color,box-shadow] duration-100 ' +
              'hover:border-[hsl(var(--slate-300))] hover:bg-[hsl(var(--card))] cursor-pointer' +
              'focus-visible:outline-none focus-visible:border-[hsl(var(--brand-500))] focus-visible:bg-[hsl(var(--card))] focus-visible:ring-2 focus-visible:ring-[hsl(var(--brand-500)/0.18)] ' +
              'disabled:cursor-not-allowed disabled:opacity-50',
            className
          )}
          ref={ref}
          {...props}
        >
          {children}
        </select>
        <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[hsl(var(--muted-foreground))] pointer-events-none" />
      </div>
    )
  }
)
SelectNative.displayName = 'SelectNative'

export { SelectNative }
