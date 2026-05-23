import * as React from 'react'
import { cn } from '@/lib/utils'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** 是否有悬浮上抬效果 */
  interactive?: boolean
  /** 卡片层级：1 平面、2 浮起、3 强调 */
  elevation?: 1 | 2 | 3
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, interactive, elevation = 1, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-[10px] border border-[hsl(var(--border))] bg-[hsl(var(--card))] text-[hsl(var(--card-foreground))]',
        elevation === 1 && 'shadow-xs',
        elevation === 2 && 'shadow-soft',
        elevation === 3 && 'shadow-pop',
        interactive &&
          'transition-[transform,box-shadow,border-color] duration-200 ease-[cubic-bezier(0.25,1,0.5,1)] ' +
            'hover:-translate-y-[2px] hover:shadow-pop hover:border-[hsl(var(--brand-500)/0.3)] cursor-pointer',
        className
      )}
      {...props}
    />
  )
)
Card.displayName = 'Card'

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex flex-col space-y-1 p-4', className)} {...props} />
  )
)
CardHeader.displayName = 'CardHeader'

const CardTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn('text-[14px] font-semibold leading-none tracking-tight text-[hsl(var(--slate-900))]', className)}
      {...props}
    />
  )
)
CardTitle.displayName = 'CardTitle'

const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-[12px] text-[hsl(var(--muted-foreground))] leading-relaxed', className)}
      {...props}
    />
  )
)
CardDescription.displayName = 'CardDescription'

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('p-4 pt-0', className)} {...props} />
  )
)
CardContent.displayName = 'CardContent'

const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex items-center p-4 pt-0', className)}
      {...props}
    />
  )
)
CardFooter.displayName = 'CardFooter'

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter }
