import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "relative overflow-hidden inline-flex items-center justify-center gap-2 whitespace-nowrap font-semibold ring-offset-background transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 cursor-pointer before:content-[''] before:absolute before:top-0 before:left-[-100%] before:w-full before:h-full before:transition-[left] before:duration-500 before:bg-gradient-to-r before:from-transparent before:via-white/20 before:to-transparent hover:before:left-full",
  {
    variants: {
      variant: {
        primary: "bg-[#3b82f6] text-white shadow-[0_4px_15px_rgba(59,130,246,0.4)] hover:bg-[#2563eb] hover:-translate-y-0.5 disabled:bg-[#9ca3af]",
        secondary: "bg-white/8 border border-white/15 text-white backdrop-blur-xl hover:bg-white/15 hover:-translate-y-px hover:shadow-[0_4px_15px_rgba(255,255,255,0.1)] disabled:bg-[#9ca3af]",
        success: "bg-[#10b981] text-white shadow-[0_4px_15px_rgba(16,185,129,0.4)] hover:bg-[#059669] hover:-translate-y-0.5 disabled:bg-[#9ca3af]",
        outline: "border border-primary-500 text-primary-500 hover:bg-primary-500 hover:text-white",
        ghost: "hover:bg-surface hover:text-foreground",
        link: "text-primary-500 underline-offset-4 hover:underline",
        glass: "bg-white/10 backdrop-blur-lg border border-white/20 text-white hover:bg-white/20",
        gray: "bg-gray-100 border border-gray-300 text-gray-800 hover:bg-gray-200 hover:-translate-y-0.5 shadow-sm disabled:bg-gray-50"
      },
      size: {
        sm: "px-4 py-2 text-sm min-h-[2.25rem] rounded-md",
        default: "px-6 py-3 text-sm min-h-[2.75rem] rounded-md",
        lg: "px-8 py-4 text-base min-h-[3rem] rounded-md",
        xl: "px-10 py-5 text-lg min-h-[3.5rem] rounded-lg",
        icon: "h-10 w-10 rounded-md",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean
  'aria-label'?: string
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, children, disabled, 'aria-label': ariaLabel, ...props }, ref) => {
    const isDisabled = disabled || loading
    
    return (
      <button
        className={cn(
          buttonVariants({ variant, size }),
          isDisabled && "hover:transform-none hover:shadow-none hover:before:left-[-100%]",
          className
        )}
        ref={ref}
        disabled={isDisabled}
        aria-label={ariaLabel}
        aria-disabled={isDisabled}
        {...props}
      >
        {loading && (
          <div 
            className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" 
            aria-hidden="true"
          />
        )}
        {children}
      </button>
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }