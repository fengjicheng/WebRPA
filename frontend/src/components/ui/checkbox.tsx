import * as React from 'react'
import { cn } from '@/lib/utils'
import { Check } from 'lucide-react'

export interface CheckboxProps {
  id?: string
  checked?: boolean
  onCheckedChange?: (checked: boolean) => void
  disabled?: boolean
  className?: string
}

const Checkbox = React.forwardRef<HTMLButtonElement, CheckboxProps>(
  ({ id, checked = false, onCheckedChange, disabled, className }, ref) => {
    return (
      <button
        type="button"
        role="checkbox"
        aria-checked={checked}
        id={id}
        ref={ref}
        disabled={disabled}
        onClick={() => !disabled && onCheckedChange?.(!checked)}
        className={cn(
          'h-4 w-4 shrink-0 rounded-[3px] border transition-colors duration-100 ' +
            'flex items-center justify-center cursor-pointer ' +
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))] focus-visible:ring-offset-1 focus-visible:ring-offset-[hsl(var(--background))] ' +
            'disabled:cursor-not-allowed disabled:opacity-50',
          checked
            ? 'bg-[hsl(var(--primary))] border-[hsl(var(--primary))]'
            : 'bg-[hsl(var(--card))] border-[hsl(var(--border))] hover:border-[hsl(var(--brand-500)/0.6)]',
          className
        )}
      >
        {checked && <Check className="h-3 w-3 text-white" strokeWidth={3} />}
      </button>
    )
  }
)
Checkbox.displayName = 'Checkbox'

export { Checkbox }
