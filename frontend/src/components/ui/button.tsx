import * as React from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { buttonHover } from '@/lib/motion'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'
  size?: 'default' | 'sm' | 'lg' | 'icon'
  /** 是否禁用动效（如在高频更新的场景中） */
  noMotion?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', noMotion = false, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50'

    const variants = {
      default: 'bg-blue-600 text-white shadow hover:bg-blue-700 active:bg-blue-800',
      destructive: 'bg-red-600 text-white shadow-sm hover:bg-red-700 active:bg-red-800',
      outline: 'border-2 border-gray-300 bg-white text-gray-700 shadow-sm hover:bg-gray-50 hover:border-gray-400 active:bg-gray-100',
      secondary: 'bg-gray-200 text-gray-900 shadow-sm hover:bg-gray-300 active:bg-gray-400',
      ghost: 'hover:bg-gray-100 hover:text-gray-900 active:bg-gray-200',
      link: 'text-blue-600 underline-offset-4 hover:underline',
    }

    const sizes = {
      default: 'h-9 px-4 py-2',
      sm: 'h-8 rounded-md px-3 text-xs',
      lg: 'h-10 rounded-md px-8',
      icon: 'h-9 w-9',
    }

    const combinedClass = cn(baseStyles, variants[variant], sizes[size], className)

    if (noMotion || props.disabled) {
      return (
        <button
          className={combinedClass}
          ref={ref}
          {...props}
        />
      )
    }

    return (
      <motion.button
        className={combinedClass}
        ref={ref as React.Ref<HTMLButtonElement>}
        whileHover={{ scale: 1.03, y: -1 }}
        whileTap={{ scale: 0.96 }}
        transition={{ type: 'spring', stiffness: 500, damping: 35 }}
        {...(props as React.ButtonHTMLAttributes<HTMLButtonElement>)}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button }
