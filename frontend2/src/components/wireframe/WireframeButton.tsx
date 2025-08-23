import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

interface WireframeButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'success'
  size?: 'sm' | 'md' | 'lg'
  children: React.ReactNode
}

export const WireframeButton = forwardRef<HTMLButtonElement, WireframeButtonProps>(
  ({ className, variant = 'primary', size = 'md', children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled}
        className={cn(
          // Base styles - exact from wireframe CSS
          'relative overflow-hidden inline-flex items-center justify-center gap-2',
          'font-semibold border-none cursor-pointer text-decoration-none',
          'transition-all duration-300 ease-in-out',
          
          // Shimmer effect - the flash animation from wireframe
          'before:content-[""] before:absolute before:top-0 before:left-[-100%]',
          'before:w-full before:h-full before:transition-[left] before:duration-500',
          'before:bg-gradient-to-r before:from-transparent before:via-white/20 before:to-transparent',
          'hover:before:left-full',
          
          // Disabled state
          disabled && 'opacity-50 cursor-not-allowed hover:transform-none hover:shadow-none hover:before:left-[-100%]',
          
          // Size variants - using sharper border radius from wireframe
          size === 'sm' && 'px-4 py-2 text-sm min-h-[2.25rem] rounded-md',
          size === 'md' && 'px-6 py-3 text-sm min-h-[2.75rem] rounded-md',
          size === 'lg' && 'px-8 py-4 text-base min-h-[3rem] rounded-md',
          
          // Variant styles - exact from wireframe
          variant === 'primary' && !disabled && [
            'bg-[#3b82f6]', // Flat color instead of gradient
            'text-white shadow-[0_4px_15px_rgba(59,130,246,0.4)]',
            'hover:bg-[#2563eb] hover:-translate-y-0.5'
          ],
          variant === 'secondary' && !disabled && [
            'bg-white/8 border border-white/15',
            'text-white backdrop-blur-xl',
            'hover:bg-white/15 hover:-translate-y-px',
            'hover:shadow-[0_4px_15px_rgba(255,255,255,0.1)]'
          ],
          variant === 'success' && !disabled && [
            'bg-[#10b981]', // Flat color instead of gradient
            'text-white shadow-[0_4px_15px_rgba(16,185,129,0.4)]',
            'hover:bg-[#059669] hover:-translate-y-0.5'
          ],
          
          // Disabled state colors
          disabled && 'bg-[#9ca3af] text-white',
          
          className
        )}
        {...props}
      >
        {children}
      </button>
    )
  }
)

WireframeButton.displayName = 'WireframeButton'