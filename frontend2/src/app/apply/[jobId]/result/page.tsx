"use client"

import { useState, useEffect } from 'react'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { User } from '@/lib/types'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'

// Job titles lookup
const jobTitles: Record<string, string> = {
  '1': 'Operations Analyst, Institutional Private Client',
  '2': 'Fund Accountant, Investment Fund Services', 
  '3': 'Operations Analyst, Separately Managed Accounts',
  '4': 'Operations Analyst, AML',
  '5': 'Senior Software Engineer'
}

interface ApplicationResultProps {
  params: Promise<{
    jobId: string
  }>
}

export default function ApplicationResultPage({ params }: ApplicationResultProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [user, setUser] = useState<User | null>(null)
  const [resolvedParams, setResolvedParams] = useState<{ jobId: string } | null>(null)
  
  useEffect(() => {
    params.then(setResolvedParams)
  }, [params])

  const jobTitle = resolvedParams ? (jobTitles[resolvedParams.jobId] || 'Unknown Position') : 'Loading...'
  const resultType = searchParams.get('result') || 'eligible' // 'eligible' or 'under-review'
  const isEligible = resultType === 'eligible'

  useEffect(() => {
    // Get user from localStorage
    const userData = localStorage.getItem('user')
    if (userData) {
      setUser(JSON.parse(userData))
    } else {
      // Redirect to login if not authenticated
      if (resolvedParams) {
        router.push(`/login?redirect=/apply/${resolvedParams.jobId}/result`)
      }
    }
  }, [resolvedParams, router])

  const handleScheduleForLater = () => {
    // Navigate to dashboard
    router.push('/dashboard')
  }

  const handleStartInterview = () => {
    // Navigate to interview preparation page
    if (resolvedParams) {
      router.push(`/interview/${resolvedParams.jobId}/prepare`)
    }
  }

  const isGuest = !user
  const userState = isGuest ? "guest" : (user?.isResumeAvailable ? "has-resume" : "no-resume")

  if (!user || !resolvedParams) {
    return (
      <div className="page-light min-h-screen">
        <Navigation userState="guest" user={null} theme="light" />
        <main className="container max-w-[1400px] mx-auto px-6 pt-20">
          <div className="text-center py-20">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Loading...</h1>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="page-light min-h-screen">
      <Navigation userState={userState} user={user} theme="light" />
      
      <main className="container max-w-[600px] mx-auto px-6 pt-20 pb-8">
        {isEligible ? (
          // Interview Eligible State
          <div className="text-center">
            {/* Congratulations Header */}
            <div className="mb-8">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-400 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-6 text-3xl relative overflow-hidden shadow-[0_4px_15px_rgba(96,165,250,0.4)] before:content-[''] before:absolute before:top-0 before:left-[-100%] before:w-full before:h-full before:bg-gradient-to-r before:from-transparent before:via-white/20 before:to-transparent before:animate-[shimmer-continuous_2s_ease-in-out_infinite]">
                🎉
              </div>
              <h1 className="text-4xl font-bold text-gray-900 mb-4">
                Congratulations!
              </h1>
              <p className="text-xl text-blue-600 font-semibold mb-8">
                You're invited to participate in our AI-powered interview process
              </p>
            </div>

            {/* Application Summary */}
            <div className="bg-white border border-gray-200 rounded-xl p-8 text-left mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Application Summary</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div>
                  <h3 className="text-sm font-medium text-gray-600 mb-1">Position</h3>
                  <p className="font-semibold text-gray-900">{jobTitle}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-600 mb-1">Location</h3>
                  <p className="font-semibold text-gray-900">San Francisco, CA</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-600 mb-1">Application Date</h3>
                  <p className="font-semibold text-gray-900">Today, {new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-600 mb-1">Status</h3>
                  <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                    Interview Eligible
                  </span>
                </div>
              </div>

              {/* What's Next */}
              <div className="bg-blue-50 rounded-lg p-4 mb-6">
                <h3 className="text-base font-semibold text-blue-800 mb-2">What's Next?</h3>
                <p className="text-blue-800 text-sm">
                  Our AI-powered interview process helps us better understand your capabilities and ensures 
                  a fair, consistent evaluation. The interview is personalized based on your background and the role requirements.
                </p>
              </div>

              {/* Interview Details */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-base font-semibold text-gray-700 mb-3">Interview Details</h3>
                <ul className="space-y-2 text-gray-600 text-sm">
                  <li className="flex items-center">
                    <span className="mr-2">⏱️</span>
                    <strong className="mr-1">Duration:</strong> 20-25 minutes
                  </li>
                  <li className="flex items-center">
                    <span className="mr-2">🤖</span>
                    <strong className="mr-1">Format:</strong> AI-powered conversation
                  </li>
                  <li className="flex items-center">
                    <span className="mr-2">💻</span>
                    <strong className="mr-1">Requirements:</strong> Computer with microphone
                  </li>
                  <li className="flex items-center">
                    <span className="mr-2">🔒</span>
                    <strong className="mr-1">Privacy:</strong> Secure and confidential
                  </li>
                </ul>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
              <Button 
                variant="success" 
                onClick={handleStartInterview}
                className="px-8 py-3 text-base"
              >
                Start Interview Now
              </Button>
              <Button 
                variant="secondary" 
                onClick={handleScheduleForLater}
                className="px-8 py-3 text-base bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
              >
                I need more time
              </Button>
            </div>

            {/* Back Link */}
            <div className="text-center">
              <Link 
                href="/jobs" 
                className="text-gray-600 hover:text-gray-800 text-sm transition-colors"
              >
                ← Back to Browse Positions
              </Link>
            </div>
          </div>
        ) : (
          // Under Review State
          <div className="text-center">
            {/* Thank You Header */}
            <div className="mb-8">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-600 to-blue-800 rounded-full flex items-center justify-center mx-auto mb-6 text-3xl">
                📧
              </div>
              <h1 className="text-4xl font-bold text-gray-900 mb-4">
                Thank You for Your Application
              </h1>
              <p className="text-xl text-gray-600 mb-8">
                We have received your application and will review it carefully
              </p>
            </div>

            {/* Application Summary */}
            <div className="bg-white border border-gray-200 rounded-xl p-8 text-left mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Application Summary</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div>
                  <h3 className="text-sm font-medium text-gray-600 mb-1">Position</h3>
                  <p className="font-semibold text-gray-900">{jobTitle}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-600 mb-1">Location</h3>
                  <p className="font-semibold text-gray-900">San Francisco, CA</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-600 mb-1">Application Date</h3>
                  <p className="font-semibold text-gray-900">Today, {new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-600 mb-1">Status</h3>
                  <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm font-medium">
                    Under Review
                  </span>
                </div>
              </div>

              {/* What's Next */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h3 className="text-base font-semibold text-blue-800 mb-2">What's Next?</h3>
                <p className="text-blue-800 text-sm">
                  Our team will review your application within 5-7 business days. If your background matches 
                  our requirements, we'll contact you with next steps. Thank you for your interest in joining our team!
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
              <Button 
                variant="primary" 
                onClick={() => router.push('/jobs')}
                className="px-8 py-3 text-base"
              >
                View Other Positions
              </Button>
              <Button 
                variant="secondary" 
                onClick={() => router.push('/dashboard')}
                className="px-8 py-3 text-base bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
              >
                View My Applications
              </Button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}