import * as React from 'react'
import * as TabsPrimitive from '@radix-ui/react-tabs'
import { cn } from '@/lib/utils'

const Tabs = TabsPrimitive.Root

const TabsList = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn(
      'inline-flex h-9 items-center justify-center rounded-[8px] ' +
        'bg-[hsl(var(--slate-100))] p-1 text-[hsl(var(--muted-foreground))] ' +
        'border border-[hsl(var(--slate-200))]',
      className
    )}
    {...props}
  />
))
TabsList.displayName = TabsPrimitive.List.displayName

const TabsTrigger = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      'inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-[6px] px-3 py-1 ' +
        'text-[12px] font-medium border border-transparent ' +
        'transition-[background-color,color,box-shadow,transform] duration-200 ease-[cubic-bezier(0.25,1,0.5,1)] ' +
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))] ' +
        'disabled:pointer-events-none disabled:opacity-50 ' +
        // 激活：品牌蓝填充 + 白字 + 蓝光晕
        'data-[state=active]:!bg-[hsl(var(--brand-600))] data-[state=active]:!text-white ' +
        'data-[state=active]:!border-[hsl(var(--brand-700))] data-[state=active]:shadow-brand-glow data-[state=active]:font-semibold ' +
        // 未激活悬浮
        'data-[state=inactive]:hover:bg-[hsl(var(--card))] data-[state=inactive]:hover:text-[hsl(var(--brand-700))] data-[state=inactive]:hover:shadow-xs',
      className
    )}
    {...props}
  />
))
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName

const TabsContent = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn(
      'mt-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))] ' +
        'data-[state=active]:animate-fade-in-up',
      className
    )}
    {...props}
  />
))
TabsContent.displayName = TabsPrimitive.Content.displayName

export { Tabs, TabsList, TabsTrigger, TabsContent }
