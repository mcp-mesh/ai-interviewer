import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  shimmer?: boolean
  iconColor?: 'blue' | 'green' | 'purple'
  children: React.ReactNode
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          // Base card styles
          'relative overflow-hidden rounded-3xl transition-all duration-300',
          'bg-white/5 backdrop-blur-[20px] border border-white/10',
          'shadow-card',
          
          // Top shimmer line
          'before:content-[""] before:absolute before:top-0 before:left-0 before:right-0 before:h-px',
          'before:bg-gradient-to-r before:from-transparent before:via-white/30 before:to-transparent',
          
          // Hover effects
          'hover:-translate-y-1 hover:shadow-card-hover hover:border-white/20',
          
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

Card.displayName = 'Card'

interface CardIconProps extends React.HTMLAttributes<HTMLDivElement> {
  color?: 'blue' | 'green' | 'purple'
  shimmer?: boolean
  children: React.ReactNode
}

export const CardIcon = forwardRef<HTMLDivElement, CardIconProps>(
  ({ className, color = 'blue', shimmer = true, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          // Base icon styles
          'relative w-14 h-14 rounded-2xl flex items-center justify-center',
          'mb-6 text-2xl overflow-hidden',
          
          // Shimmer animation
          shimmer && [
            'before:content-[""] before:absolute before:top-[-50%] before:left-[-50%]',
            'before:w-[200%] before:h-[200%] before:animate-shimmer',
            'before:bg-gradient-to-br before:from-transparent before:via-white/10 before:to-transparent',
            'before:rotate-45'
          ],
          
          // Color variants
          color === 'blue' && [
            'bg-gradient-to-br from-brand-blue/20 to-brand-blue-dark/30',
            'text-blue-400 border border-brand-blue/30'
          ],
          color === 'green' && [
            'bg-gradient-to-br from-brand-green/20 to-brand-green-dark/30', 
            'text-green-400 border border-brand-green/30'
          ],
          color === 'purple' && [
            'bg-gradient-to-br from-brand-purple/20 to-brand-purple-dark/30',
            'text-purple-400 border border-brand-purple/30'
          ],
          
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

CardIcon.displayName = 'CardIcon'

export const CardBody = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('p-6 pt-4 pb-8', className)}
        {...props}
      >
        {children}
      </div>
    )
  }
)

CardBody.displayName = 'CardBody'