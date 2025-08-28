"use client"

import { useState, useEffect, useMemo, useCallback } from "react"
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
  currentPage?: "dashboard" | "jobs" | "applications" | "matched" | null
}

export function Navigation({ userState = "guest", user, className, theme = "dark", currentPage }: NavigationProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [jobsCount, setJobsCount] = useState<number>(0)

  // Memoize isLoggedIn to prevent infinite re-renders
  const isLoggedIn = useMemo(() => userState !== "guest" && !!user, [userState, user])

  const handleLogout = () => {
    // Complete cleanup - remove all auth-related data
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
    localStorage.clear() // Clear any other cached data
    
    // Redirect to landing page for clean slate
    window.location.href = '/'
  }

  // Load actual job counts from API
  useEffect(() => {
    const loadJobCounts = async () => {
      if (!isLoggedIn || !user) {
        setJobsCount(0)
        return
      }

      try {
        // Import API client dynamically to avoid circular dependencies
        const { jobsApi } = await import('@/lib/api')
        
        // Get job count based on user's resume status
        if (user.hasResume) {
          const matchedResponse = await jobsApi.getMatched()
          if (matchedResponse.data) {
            setJobsCount(matchedResponse.data.length)
          }
        } else {
          const allJobsResponse = await jobsApi.getAll()
          if (allJobsResponse.data) {
            setJobsCount(allJobsResponse.data.length)
          }
        }
      } catch (error) {
        console.error('Failed to load job counts:', error)
        setJobsCount(0)
      }
    }

    loadJobCounts()
  }, [isLoggedIn, user?.hasResume])

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

  // Helper function to get nav link styling based on selected state
  const getNavLinkClasses = (page: string, isSelected: boolean) => {
    if (isSelected) {
      // Selected page styling - extra bold text, no hover effects
      if (theme === "light") {
        return "font-black text-primary-600 cursor-default transition-colors"
      }
      return userState === "guest" 
        ? "font-black text-white cursor-default transition-colors"
        : "font-black text-primary-500 cursor-default transition-colors"
    } else {
      // Regular link styling - semibold to distinguish from selected
      return `font-semibold transition-colors ${getNavLinkColor()}`
    }
  }

  // Helper to render nav link (either as Link or span based on selection)
  const renderNavLink = (href: string, children: React.ReactNode, page: string) => {
    const isSelected = currentPage === page
    const classes = getNavLinkClasses(page, isSelected)
    
    if (isSelected) {
      return <span className={classes}>{children}</span>
    } else {
      return <Link href={href} className={classes}>{children}</Link>
    }
  }

  // Mobile nav link renderer with block styling
  const renderMobileNavLink = (href: string, children: React.ReactNode, page: string) => {
    const isSelected = currentPage === page
    const baseClasses = "block py-2 transition-colors"
    
    if (isSelected) {
      return (
        <span className={`${baseClasses} text-primary-500 font-black cursor-default`}>
          {children}
        </span>
      )
    } else {
      return (
        <Link href={href} className={`${baseClasses} text-foreground hover:text-primary-500 font-semibold`}>
          {children}
        </Link>
      )
    }
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
                {renderNavLink("/dashboard", "Dashboard", "dashboard")}
                
                {/* Jobs link with badge */}
                <div className="relative pr-6">
                  {renderNavLink(
                    user?.hasResume ? "/jobs/matched" : "/jobs", 
                    "Jobs", 
                    user?.hasResume ? "matched" : "jobs"
                  )}
                  {/* Show badge with dynamic count positioned outside the link */}
                  {jobsCount > 0 && (
                    <span className="absolute -top-1 -right-0 bg-red-500 text-white text-xs rounded-full min-w-[18px] h-[18px] flex items-center justify-center leading-none">
                      {jobsCount}
                    </span>
                  )}
                </div>
                
                {/* Show Applications only when user has applications */}
                {user?.applications && user.applications.length > 0 && (
                  <div className="relative pr-6">
                    {renderNavLink("/applications", "Applications", "applications")}
                    {/* Show badge with application count positioned outside the link */}
                    <span className="absolute -top-1 -right-0 bg-green-500 text-white text-xs rounded-full min-w-[18px] h-[18px] flex items-center justify-center leading-none">
                      {user.applications.length}
                    </span>
                  </div>
                )}
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
                    variant={userState === "guest" ? "glass" : "primary"}
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
                  {renderMobileNavLink("/dashboard", "Dashboard", "dashboard")}
                  
                  <div className="relative pr-6">
                    {renderMobileNavLink(
                      user?.hasResume ? "/jobs/matched" : "/jobs",
                      "Jobs",
                      user?.hasResume ? "matched" : "jobs"
                    )}
                    {/* Show badge with dynamic count positioned outside the link */}
                    {jobsCount > 0 && (
                      <span className="absolute top-2 right-0 bg-red-500 text-white text-xs rounded-full min-w-[18px] h-[18px] flex items-center justify-center leading-none">
                        {jobsCount}
                      </span>
                    )}
                  </div>
                  
                  {/* Show Applications only when user has applications */}
                  {user?.applications && user.applications.length > 0 && (
                    <div className="relative pr-6">
                      {renderMobileNavLink("/applications", "Applications", "applications")}
                      {/* Show badge with application count positioned outside the link */}
                      <span className="absolute top-2 right-0 bg-green-500 text-white text-xs rounded-full min-w-[18px] h-[18px] flex items-center justify-center leading-none">
                        {user.applications.length}
                      </span>
                    </div>
                  )}
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