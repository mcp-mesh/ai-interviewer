'use client'

import { useState, useEffect } from 'react'
import { UserCircleIcon, PlayCircleIcon, DocumentCheckIcon, ClockIcon, StarIcon, ChevronRightIcon, ArrowRightIcon, DocumentArrowUpIcon, BriefcaseIcon, CogIcon } from '@heroicons/react/24/outline'
import Link from 'next/link'

interface UserProfile {
  user_id: string
  email: string
  name: string
  admin?: boolean
  resume?: {
    filename: string
    uploaded_at: string
    [key: string]: unknown // Allow additional properties
  }
}

export default function HomePage() {
  const [isLoading, setIsLoading] = useState(false)
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null)
  const [checkingAuth, setCheckingAuth] = useState(true)
  const [renderKey, setRenderKey] = useState(0)

  useEffect(() => {
    checkUserAuthentication()
  }, [])

  useEffect(() => {
    console.log('🔍 DEBUG: UserProfile state changed:', userProfile)
    console.log('🔍 DEBUG: Resume exists in state?', !!userProfile?.resume)
  }, [userProfile])

  const checkUserAuthentication = async () => {
    try {
      // NGINX will handle session validation and pass bearer token to backend
      // We just need to make the request with credentials to send session cookie
      const response = await fetch('/api/user/profile', {
        credentials: 'include', // This sends session cookie to NGINX
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        console.log('🔍 DEBUG: API response received:', data)
        console.log('🔍 DEBUG: Resume data:', data.user?.resume)
        setUserProfile({
          user_id: data.user.user_id,
          email: data.user.email,
          name: data.user.name,
          admin: data.user.admin,
          resume: data.user.resume
        })
        console.log('🔍 DEBUG: UserProfile state set with resume:', data.user?.resume ? 'YES' : 'NO')
        setRenderKey(prev => prev + 1) // Force re-render
      } else {
        // Not authenticated - this is normal for first-time visitors
        console.log('No active session found, status:', response.status)
      }
    } catch (error) {
      console.error('🔍 DEBUG: Error in checkUserAuthentication:', error)
      console.error('🔍 DEBUG: Error details:', error instanceof Error ? error.message : 'Unknown error')
    } finally {
      console.log('🔍 DEBUG: Setting checkingAuth to false')
      setCheckingAuth(false)
    }
  }

  const handleLogout = async () => {
    try {
      // Call logout endpoint to clear server-side session
      await fetch('/logout', {
        method: 'POST',
        credentials: 'include'
      })
    } catch (error) {
      console.error('Logout error:', error)
    }
    
    // Clear user state (no localStorage needed in this architecture)
    setUserProfile(null)
    
    // The logout endpoint will redirect to homepage, but we can also redirect here
    window.location.href = '/'
  }

  const handleGoogleLogin = () => {
    setIsLoading(true)
    // Redirect to NGINX OAuth endpoint
    window.location.href = '/auth/google'
  }

  const handleGithubLogin = () => {
    setIsLoading(true)
    // Redirect to NGINX OAuth endpoint  
    window.location.href = '/auth/github'
  }

  return (
    <div className="min-h-screen relative">
      {/* Full Page Background Image */}
      <div 
        className="fixed inset-0 z-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: 'url(/background.png)' }}
      />
      
      {/* Dark Overlay */}
      <div className="fixed inset-0 z-1 bg-black/50" />
      
      {/* Content Overlay */}
      <div className="relative z-10 min-h-screen">
        {/* Navigation */}
        <nav className="bg-black/20 backdrop-blur-sm border-b border-white/20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <Link href="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
                <div className="bg-blue-600 p-2 rounded-lg">
                  <UserCircleIcon className="h-6 w-6 text-white" />
                </div>
                <h1 className="text-xl font-bold text-white">AI Interviewer</h1>
              </Link>
              <div className="flex items-center space-x-4">
                {userProfile ? (
                  <>
                    <span className="text-white/80 text-sm">Welcome, {userProfile.name.split(' ')[0]}!</span>
                    <Link href="/dashboard" className="text-white hover:text-blue-300 font-medium">
                      Dashboard
                    </Link>
                    {userProfile.admin === true && (
                      <Link 
                        href="/admin"
                        className="text-white hover:text-purple-300 font-medium flex items-center space-x-1"
                      >
                        <CogIcon className="h-4 w-4" />
                        <span>Admin</span>
                      </Link>
                    )}
                    <button 
                      onClick={handleLogout}
                      className="text-white/80 hover:text-white font-medium"
                    >
                      Logout
                    </button>
                  </>
                ) : (
                  <>
                    <button className="text-white/80 hover:text-white font-medium">About</button>
                    <button className="text-white/80 hover:text-white font-medium">Features</button>
                  </>
                )}
              </div>
            </div>
          </div>
        </nav>

        {/* Hero Section */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <div className="flex justify-center mb-8">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-4 rounded-2xl">
                <PlayCircleIcon className="h-12 w-12 text-white" />
              </div>
            </div>
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
              Smart Interviews
            </h1>
            <p className="text-xl text-white/90 max-w-3xl mx-auto mb-12">
              Experience intelligent interviews powered by AI agents. 
              Get personalized questions, real-time analysis, and detailed feedback 
              to showcase your skills effectively.
            </p>

            {/* Action Buttons */}
            {checkingAuth ? (
              <div className="flex justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : userProfile ? (
              <div key={`${userProfile.user_id}-${renderKey}`} className="flex flex-col sm:flex-row gap-4 justify-center items-center max-w-2xl mx-auto">
                {userProfile.resume ? (
                  <>
                    <Link
                      href="/dashboard"
                      className="w-full sm:w-auto bg-blue-600 text-white font-semibold py-3 px-8 rounded-xl hover:bg-blue-700 transition-all duration-200 flex items-center justify-center space-x-3 shadow-sm"
                    >
                      <BriefcaseIcon className="h-5 w-5" />
                      <span>Browse Roles & Start Interview</span>
                    </Link>
                    <Link
                      href="/profile"
                      className="w-full sm:w-auto bg-purple-600 text-white font-semibold py-3 px-8 rounded-xl hover:bg-purple-700 transition-all duration-200 flex items-center justify-center space-x-3 shadow-sm"
                    >
                      <UserCircleIcon className="h-5 w-5" />
                      <span>View Your Profile</span>
                    </Link>
                    <Link
                      href="/upload"
                      className="w-full sm:w-auto bg-gradient-to-r from-teal-600 to-cyan-600 text-white font-semibold py-3 px-8 rounded-xl hover:from-teal-700 hover:to-cyan-700 transition-all duration-200 flex items-center justify-center space-x-3 shadow-sm"
                    >
                      <DocumentArrowUpIcon className="h-5 w-5" />
                      <span>Update Resume</span>
                    </Link>
                  </>
                ) : (
                  <>
                    <Link
                      href="/upload"
                      className="w-full sm:w-auto bg-blue-600 text-white font-semibold py-3 px-8 rounded-xl hover:bg-blue-700 transition-all duration-200 flex items-center justify-center space-x-3 shadow-sm"
                    >
                      <DocumentArrowUpIcon className="h-5 w-5" />
                      <span>Upload Your Resume</span>
                      <ArrowRightIcon className="h-4 w-4" />
                    </Link>
                    <div className="text-center">
                      <p className="text-sm text-gray-500">First, upload your resume to get started</p>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center max-w-lg mx-auto">
                <button
                  onClick={handleGoogleLogin}
                  disabled={isLoading}
                  className="w-full sm:w-auto bg-white border-2 border-gray-200 text-gray-700 font-semibold py-3 px-8 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-all duration-200 flex items-center justify-center space-x-3 shadow-sm"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path fill="#4285f4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34a853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#fbbc05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#ea4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  <span>{isLoading ? 'Connecting...' : 'Continue with Google'}</span>
                </button>

                <button
                  onClick={handleGithubLogin}
                  disabled={isLoading}
                  className="w-full sm:w-auto bg-gray-900 text-white font-semibold py-3 px-8 rounded-xl hover:bg-gray-800 transition-all duration-200 flex items-center justify-center space-x-3 shadow-sm"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                  <span>{isLoading ? 'Connecting...' : 'Continue with GitHub'}</span>
                </button>
              </div>
            )}
          </div>

          {/* Features Grid */}
          <div className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white/10 backdrop-blur-md border border-white/20 p-8 rounded-2xl shadow-2xl hover:bg-white/15 hover:border-white/30 transition-all duration-200">
              <div className="bg-blue-600/80 backdrop-blur-sm w-12 h-12 rounded-xl flex items-center justify-center mb-6">
                <DocumentCheckIcon className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-4">AI-Powered Questions</h3>
              <p className="text-white/80 leading-relaxed">
                Dynamic question generation based on your resume and the role requirements. 
                Each interview is personalized and challenging.
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-md border border-white/20 p-8 rounded-2xl shadow-2xl hover:bg-white/15 hover:border-white/30 transition-all duration-200">
              <div className="bg-indigo-600/80 backdrop-blur-sm w-12 h-12 rounded-xl flex items-center justify-center mb-6">
                <ClockIcon className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-4">Real-time Analysis</h3>
              <p className="text-white/80 leading-relaxed">
                Get instant feedback and follow-up questions based on your responses. 
                The AI adapts to your expertise level.
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-md border border-white/20 p-8 rounded-2xl shadow-2xl hover:bg-white/15 hover:border-white/30 transition-all duration-200">
              <div className="bg-green-600/80 backdrop-blur-sm w-12 h-12 rounded-xl flex items-center justify-center mb-6">
                <StarIcon className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-4">Comprehensive Feedback</h3>
              <p className="text-white/80 leading-relaxed">
                Detailed analysis of your performance with suggestions for improvement 
                and strengths highlighted.
              </p>
            </div>
          </div>

          {/* How it Works */}
          <div className="mt-24">
            <h2 className="text-3xl font-bold text-center text-white mb-16">How it Works</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              {[
                { step: "1", title: "Upload Resume", desc: "Share your resume for personalized questions" },
                { step: "2", title: "Select Role", desc: "Choose the position you're interviewing for" },
                { step: "3", title: "Start Interview", desc: "Engage with AI in an interview" },
                { step: "4", title: "Get Feedback", desc: "Receive detailed analysis and improvement tips" }
              ].map((item, index) => (
                <div key={index} className="text-center relative">
                  <div className="bg-blue-600 text-white w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
                    {item.step}
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                  <p className="text-white/80">{item.desc}</p>
                  {index < 3 && (
                    <ChevronRightIcon className="h-5 w-5 text-white/60 absolute top-6 -right-4 hidden md:block" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="bg-black/20 backdrop-blur-sm border-t border-white/20 mt-24">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div className="text-center text-white/80">
              <p>&copy; 2025 AI Interviewer. Powered by MCP Mesh.</p>
            </div>
          </div>
        </footer>
      </div>
    </div>
  )
}