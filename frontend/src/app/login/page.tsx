"use client"

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { OAuthButton } from '@/components/common/OAuthButton'
import { Bot, Target, Mail, BarChart3, Zap } from 'lucide-react'

const benefits = [
  {
    icon: Bot,
    title: 'Instant AI-Based Interviews',
    description: 'Get immediate feedback and practice with our AI interview system before meeting with real recruiters.',
    color: 'bg-brand-blue'
  },
  {
    icon: Target,
    title: 'Smart Profile Matching',
    description: 'Our AI automatically matches your skills and experience to the most relevant job opportunities.',
    color: 'bg-brand-green'
  },
  {
    icon: Mail,
    title: 'Job Alerts & Notifications',
    description: 'Stay updated with personalized notifications when new positions matching your profile are posted.',
    color: 'bg-brand-yellow'
  },
  {
    icon: BarChart3,
    title: 'Application Tracking',
    description: 'Keep track of all your applications, interview schedules, and follow-ups in one centralized dashboard.',
    color: 'bg-brand-purple'
  },
  {
    icon: Zap,
    title: 'AI Resume Optimization',
    description: 'Get AI-powered suggestions to optimize your resume for specific job applications and ATS systems.',
    color: 'bg-red-500'
  }
]

export default function LoginPage() {
  const searchParams = useSearchParams()
  const redirect = searchParams.get('redirect') || '/dashboard'
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // No need to check authentication status - nginx handles this
    // If user reaches this page, they are not authenticated
    setLoading(false)
  }, [redirect])

  // No need for handleOAuthLogin - OAuthButton handles direct links now

  // Show loading while checking authentication
  if (loading) {
    return (
      <div className="page-light min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="page-light min-h-screen">
      {/* Navigation Header */}
      <header className="bg-white/95 backdrop-blur-sm border-b border-gray-200 shadow-sm absolute top-0 left-0 right-0 z-50 transition-all duration-300 py-3">
        <div className="max-w-[1400px] mx-auto px-6 flex justify-between items-center h-16">
          <Link href="/" className="flex items-center gap-3 font-bold text-xl text-gray-900 no-underline transition-all duration-300 hover:-translate-y-px">
            <div className="w-10 h-10 bg-gradient-to-br from-brand-blue to-brand-blue-dark flex items-center justify-center text-white font-bold text-lg shadow-[0_4px_15px_rgba(59,130,246,0.3)]">
              SCI
            </div>
            <span>S Corp.</span>
          </Link>
          
          <div className="flex items-center gap-4">
            <Link href="/" className="text-gray-600 hover:text-primary-500 no-underline px-4 py-2 rounded-lg transition-all duration-200 font-medium">
              Home
            </Link>
            <Link href="/jobs" className="text-gray-600 hover:text-primary-500 no-underline px-4 py-2 rounded-lg transition-all duration-200 font-medium">
              Browse Jobs
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container max-w-[1400px] mx-auto px-6">
        <div className="grid lg:grid-cols-2 gap-16 items-center min-h-screen pt-20">
          
          {/* Left Column - Benefits */}
          <div>
            <div className="max-w-lg">
              <h1 className="text-4xl font-bold text-gray-900 mb-6 leading-tight">
                Join S Corp. Today
              </h1>
              
              <p className="text-lg text-gray-600 mb-8 leading-relaxed">
                Unlock the power of AI-driven career advancement and find your perfect job match with intelligent automation.
              </p>

              <div className="space-y-6">
                {benefits.map((benefit, index) => {
                  const IconComponent = benefit.icon
                  return (
                    <div key={index} className="flex items-start gap-4">
                      <div className={`w-10 h-10 ${benefit.color} rounded-full flex items-center justify-center flex-shrink-0`}>
                        <IconComponent className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900 mb-2">{benefit.title}</h3>
                        <p className="text-gray-600 text-sm leading-relaxed">{benefit.description}</p>
                      </div>
                    </div>
                  )
                })}
              </div>

            </div>
          </div>

          {/* Right Column - Login Form */}
          <div>
            <div className="max-w-md mx-auto">
              <div className="bg-white p-8 rounded-2xl shadow-lg border border-gray-200">
                <div className="text-center mb-8">
                  <h2 className="text-3xl font-bold text-gray-900 mb-2">Register or Login</h2>
                  <p className="text-gray-600 text-sm">Choose your preferred method to get started</p>
                </div>


                <div className="flex flex-col gap-4">
                  <OAuthButton 
                    provider="google" 
                    redirect={redirect}
                  />
                  
                  <OAuthButton 
                    provider="github" 
                    redirect={redirect}
                  />
                </div>

                <div className="mt-8 pt-6 border-t border-gray-200 text-center">
                  <p className="text-gray-600 text-xs leading-relaxed">
                    By continuing, you agree to S Corp.&apos;s{' '}
                    <Link href="#" className="text-brand-blue underline hover:text-brand-blue-dark">
                      Terms of Service
                    </Link>
                    {' '}and{' '}
                    <Link href="#" className="text-brand-blue underline hover:text-brand-blue-dark">
                      Privacy Policy
                    </Link>
                  </p>
                </div>
              </div>

              <div className="text-center mt-6">
                <p className="text-gray-600 text-sm">
                  Just browsing?{' '}
                  <Link href="/jobs" className="text-brand-blue underline hover:text-brand-blue-dark font-medium">
                    Continue without signing up
                  </Link>
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}