"use client"

import Link from 'next/link'
import { cn } from '@/lib/utils'

interface WireframeNavigationProps {
  className?: string
}

export function WireframeNavigation({ className }: WireframeNavigationProps) {
  return (
    <header className={cn(
      // Base header styles matching wireframe
      'absolute top-0 left-0 right-0 z-50 transition-all duration-300',
      'bg-transparent border-b border-white/15 shadow-[0_2px_8px_rgba(0,0,0,0.1)]',
      'py-3',
      className
    )}>
      <div className="max-w-[1400px] mx-auto px-6 flex justify-between items-center h-16">
        {/* Logo */}
        <Link 
          href="/" 
          className="flex items-center gap-3 font-bold text-xl text-wireframe-white no-underline transition-all duration-300 hover:-translate-y-px"
        >
          <div className="w-10 h-10 bg-gradient-to-br from-wireframe-blue to-wireframe-blue-dark rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-[0_4px_15px_rgba(59,130,246,0.3)]">
            SCI
          </div>
          <span>S Corp.</span>
        </Link>
        
        {/* Navigation Actions */}
        <div className="flex items-center gap-4">
          <nav className="hidden md:flex items-center gap-1">
            <Link 
              href="#features" 
              className="text-wireframe-white no-underline px-4 py-2 rounded-lg transition-all duration-200 font-medium hover:text-wireframe-white hover:bg-white/10"
            >
              Features
            </Link>
            <Link 
              href="#how-it-works"
              className="text-wireframe-white no-underline px-4 py-2 rounded-lg transition-all duration-200 font-medium hover:text-wireframe-white hover:bg-white/10"
            >
              How It Works
            </Link>
            <Link 
              href="/login"
              className="text-wireframe-white no-underline px-4 py-2 rounded-lg transition-all duration-200 font-medium hover:text-wireframe-white hover:bg-white/10"
            >
              Login
            </Link>
          </nav>
        </div>
      </div>
    </header>
  )
}