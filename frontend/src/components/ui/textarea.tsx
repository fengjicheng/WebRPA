import * as React from 'react'
import { cn } from '@/lib/utils'

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          'flex min-h-[72px] w-full rounded-[6px] border border-[hsl(var(--border))] bg-[hsl(var(--card))] px-2.5 py-2 text-[13px] ' +
            'text-[hsl(var(--foreground))] placeholder:text-[hsl(var(--muted-foreground))] ' +
            'transition-[border-color,box-shadow] duration-100 resize-y ' +
            'focus-visible:outline-none focus-visible:border-[hsl(var(--brand-500))] focus-visible:ring-2 focus-visible:ring-[hsl(var(--brand-500)/0.18)] ' +
            'disabled:cursor-not-allowed disabled:opacity-50',
          className
        )}
        {...props}
      />
    )
  }
)
Textarea.displayName = 'Textarea'

export { Textarea }
