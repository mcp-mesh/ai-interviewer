import React from 'react'
import { cn } from '@/lib/utils'
import { Loader2 } from 'lucide-react'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
  text?: string
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6', 
  lg: 'w-8 h-8'
}

export function LoadingSpinner({ size = 'md', className, text }: LoadingSpinnerProps) {
  return (
    <div className={cn('flex items-center justify-center gap-2', className)} role="status" aria-live="polite">
      <Loader2 className={cn('animate-spin', sizeClasses[size])} aria-hidden="true" />
      {text && (
        <span className="text-sm text-gray-600">{text}</span>
      )}
      <span className="sr-only">Loading...</span>
    </div>
  )
}

export function LoadingPage({ text = "Loading..." }: { text?: string }) {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <LoadingSpinner size="lg" text={text} />
    </div>
  )
}

export function LoadingCard({ text = "Loading..." }: { text?: string }) {
  return (
    <div className="min-h-[200px] flex items-center justify-center p-8">
      <LoadingSpinner size="md" text={text} />
    </div>
  )
}