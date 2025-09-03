"use client"

import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Navigation } from "@/components/navigation"
import { InterviewChat } from "@/components/interview/InterviewChat"
import { ToastContainer, useToast, SuspenseWrapper } from "@/components/common"
import { UserState, User, Job } from "@/lib/types"
import { jobsApi } from "@/lib/api"

function ActiveInterviewPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [jobId, setJobId] = useState<string>("")
  // Session ID will be handled by InterviewChat component
  const [job, setJob] = useState<Job | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [userState, setUserState] = useState<UserState>("guest")
  const { toasts, showToast, removeToast } = useToast()

  // Load user data from localStorage
  useEffect(() => {
    const userData = localStorage.getItem('user')
    if (userData) {
      try {
        const parsedUser = JSON.parse(userData)
        setUser(parsedUser)
        setUserState(parsedUser.hasResume ? "has-resume" : "no-resume")
      } catch (error) {
        console.error('Failed to parse user data:', error)
        setUserState("guest")
      }
    } else {
      setUserState("guest")
      router.push('/login')
      return
    }
  }, [router])

  // Session ID is no longer required - InterviewChat will handle it via jobId

  useEffect(() => {
    // Get jobId from query parameters
    const jobIdParam = searchParams.get('jobId') || searchParams.get('id')
    
    if (!jobIdParam) {
      setError('Job ID is required')
      setLoading(false)
      return
    }
    
    setJobId(jobIdParam)
    
    // Fetch job data
    setLoading(true)
    const fetchJob = async () => {
      try {
        const { data: jobData, error: jobError } = await jobsApi.getById(jobIdParam)
        if (jobError) {
          setError(jobError)
        } else {
          setJob(jobData)
        }
      } catch {
        setError('Failed to fetch job information')
      } finally {
        setLoading(false)
      }
    }
    
    fetchJob()
  }, [searchParams])

  const handleInterviewComplete = (reason: 'completed' | 'terminated' | 'time_up') => {
    // Redirect to completion page with reason
    router.push(`/interview/job/complete?jobId=${jobId}&reason=${reason}`)
  }

  const handleInterviewError = (error: string) => {
    showToast.error(error)
    // Optionally redirect back to prepare page after error
    setTimeout(() => {
      router.push(`/interview/job/prepare?jobId=${jobId}`)
    }, 3000)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation userState={userState} user={user} theme="light" />
        <main className="container mx-auto px-6 py-8">
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading interview...</p>
            </div>
          </div>
        </main>
      </div>
    )
  }

  if (error || !job) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation userState={userState} user={user} theme="light" />
        <main className="container mx-auto px-6 py-8">
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <div className="text-red-600 text-6xl mb-4">⚠️</div>
              <h1 className="text-2xl font-bold text-gray-800 mb-2">Interview Session Error</h1>
              <p className="text-gray-600 mb-6">{error || 'Invalid interview session'}</p>
              <button
                onClick={() => router.push(`/interview/job/prepare?jobId=${jobId}`)}
                className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 transition-colors"
              >
                Return to Preparation
              </button>
            </div>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation is hidden during interview for focus */}
      <InterviewChat
        job={job}
        user={user}
        onComplete={handleInterviewComplete}
        onError={handleInterviewError}
      />
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  )
}

export default function ActiveInterviewPage() {
  return (
    <SuspenseWrapper>
      <ActiveInterviewPageContent />
    </SuspenseWrapper>
  )
}