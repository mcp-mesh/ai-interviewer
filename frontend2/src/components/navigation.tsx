"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { UserState, User } from "@/lib/types"

interface NavigationProps {
  userState?: UserState
  user?: User | null
  className?: string
  theme?: "dark" | "light"
}

export function Navigation({ userState = "guest", user, className, theme = "dark" }: NavigationProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const isLoggedIn = userState !== "guest" && user

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
    window.location.href = '/'
  }

  // Determine nav styling based on theme and user state
  const getNavStyles = () => {
    if (theme === "light") {
      return "bg-white/95 backdrop-blur-sm border-b border-gray-200 shadow-sm"
    }
    return userState === "guest" 
      ? "bg-transparent backdrop-blur-sm border-b border-white/15" 
      : "bg-background border-b border-border"
  }

  // Helper functions for text colors
  const getLogoTextColor = () => {
    if (theme === "light") return "text-gray-900"
    return userState === "guest" ? "text-white" : "text-foreground"
  }

  const getNavLinkColor = () => {
    if (theme === "light") return "text-gray-600 hover:text-primary-500"
    return userState === "guest" ? "text-white hover:text-primary-100" : "text-text-secondary hover:text-primary-500"
  }

  return (
    <header className={cn(
      "sticky top-0 z-50 w-full transition-all duration-300",
      getNavStyles(),
      className
    )}>
      <div className="container mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 hover:-translate-y-0.5 transition-transform">
            <div className="w-10 h-10 bg-primary-500 rounded-xl flex items-center justify-center shadow-lg">
              <span className="text-white font-bold text-lg">SCI</span>
            </div>
            <span className={cn("text-xl font-bold", getLogoTextColor())}>
              S Corp.
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            {!isLoggedIn ? (
              // Guest Navigation
              <>
                <Link 
                  href="#features" 
                  className={cn(
                    "font-medium transition-colors hover:-translate-y-0.5 transition-transform",
                    getNavLinkColor()
                  )}
                >
                  Features
                </Link>
                <Link 
                  href="#how-it-works"
                  className={cn(
                    "font-medium transition-colors hover:-translate-y-0.5 transition-transform",
                    getNavLinkColor()
                  )}
                >
                  How It Works
                </Link>
                <Link 
                  href="/jobs"
                  className={cn(
                    "font-medium transition-colors hover:-translate-y-0.5 transition-transform",
                    getNavLinkColor()
                  )}
                >
                  Browse Jobs
                </Link>
              </>
            ) : (
              // Logged In Navigation
              <>
                <Link 
                  href="/dashboard" 
                  className="text-text-secondary hover:text-primary-500 font-medium transition-colors"
                >
                  Dashboard
                </Link>
                <Link 
                  href="/jobs"
                  className="text-text-secondary hover:text-primary-500 font-medium transition-colors"
                >
                  Jobs
                </Link>
                <Link 
                  href="/applications"
                  className="text-text-secondary hover:text-primary-500 font-medium transition-colors"
                >
                  Applications
                </Link>
              </>
            )}
          </nav>

          {/* User Actions */}
          <div className="flex items-center gap-4">
            {!isLoggedIn ? (
              // Guest Actions
              <div className="flex items-center gap-3">
                <Link href="/login">
                  <Button 
                    variant={userState === "guest" ? "secondary" : "outline"}
                    size="sm"
                  >
                    Login
                  </Button>
                </Link>
                <Link href="/register">
                  <Button 
                    variant={userState === "guest" ? "glass" : "default"}
                    size="sm"
                  >
                    Get Started
                  </Button>
                </Link>
              </div>
            ) : (
              // Logged In Actions  
              <div className="flex items-center gap-4">
                {/* User Info */}
                <div className="hidden md:flex items-center gap-3">
                  <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center">
                    <span className="text-white font-semibold text-sm">
                      {user?.name?.split(' ').map(n => n[0]).join('') || 'U'}
                    </span>
                  </div>
                  <div className="text-sm">
                    <div className="font-semibold text-foreground">{user?.name}</div>
                    <div className="text-text-muted text-xs">{user?.email}</div>
                  </div>
                </div>

                {/* Action Buttons */}
                <Link href="/applications">
                  <Button variant="outline" size="sm">My Applications</Button>
                </Link>
                
                <Button variant="ghost" size="sm" onClick={handleLogout}>
                  Logout
                </Button>
              </div>
            )}

            {/* Mobile Menu Button */}
            <Button
              variant="ghost"
              size="sm"
              className="md:hidden"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
            >
              <div className="w-5 h-5 flex flex-col justify-center gap-1">
                <div className={cn("w-full h-0.5 bg-current transition-transform", isMenuOpen && "rotate-45 translate-y-1.5")} />
                <div className={cn("w-full h-0.5 bg-current transition-opacity", isMenuOpen && "opacity-0")} />
                <div className={cn("w-full h-0.5 bg-current transition-transform", isMenuOpen && "-rotate-45 -translate-y-1.5")} />
              </div>
            </Button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <Card variant="glass" className="md:hidden mt-2 mb-4">
            <div className="p-4 space-y-4">
              {!isLoggedIn ? (
                <>
                  <Link href="#features" className="block py-2 text-foreground hover:text-primary-500">
                    Features
                  </Link>
                  <Link href="#how-it-works" className="block py-2 text-foreground hover:text-primary-500">
                    How It Works
                  </Link>
                  <Link href="/jobs" className="block py-2 text-foreground hover:text-primary-500">
                    Browse Jobs
                  </Link>
                  <div className="pt-4 border-t border-border space-y-3">
                    <Link href="/login">
                      <Button variant="outline" size="sm" className="w-full">Login</Button>
                    </Link>
                    <Link href="/register">
                      <Button size="sm" className="w-full">Get Started</Button>
                    </Link>
                  </div>
                </>
              ) : (
                <>
                  <div className="flex items-center gap-3 py-2 border-b border-border">
                    <div className="w-10 h-10 bg-primary-500 rounded-full flex items-center justify-center">
                      <span className="text-white font-semibold">
                        {user?.name?.split(' ').map(n => n[0]).join('') || 'U'}
                      </span>
                    </div>
                    <div>
                      <div className="font-semibold text-foreground">{user?.name}</div>
                      <div className="text-text-muted text-sm">{user?.email}</div>
                    </div>
                  </div>
                  <Link href="/dashboard" className="block py-2 text-foreground hover:text-primary-500">
                    Dashboard
                  </Link>
                  <Link href="/jobs" className="block py-2 text-foreground hover:text-primary-500">
                    Jobs
                  </Link>
                  <Link href="/applications" className="block py-2 text-foreground hover:text-primary-500">
                    My Applications
                  </Link>
                  <div className="pt-4 border-t border-border">
                    <Button variant="ghost" size="sm" className="w-full" onClick={handleLogout}>
                      Logout
                    </Button>
                  </div>
                </>
              )}
            </div>
          </Card>
        )}
      </div>
    </header>
  )
}