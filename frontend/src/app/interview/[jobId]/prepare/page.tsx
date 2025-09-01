"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Navigation } from "@/components/navigation"
import { Button } from "@/components/ui/button"
import { Markdown } from "@/components/ui/markdown"
import { ToastContainer, useToast } from "@/components/common"
import { AlertTriangle, Calendar, Clock, Ban, Scale, Wrench, Lightbulb, CheckCircle2, Settings } from "lucide-react"
import { UserState, User, Job } from "@/lib/types"
import { jobsApi, interviewsApi } from "@/lib/api"
import { useRouter } from 'next/navigation'

interface PreparePageProps {
  params: Promise<{ jobId: string }>
}

export default function InterviewPreparePage({ params }: PreparePageProps) {
  const router = useRouter()
  const [jobId, setJobId] = useState<string>("")
  const [job, setJob] = useState<Job | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [userState, setUserState] = useState<UserState>("guest")
  const [isStartingInterview, setIsStartingInterview] = useState(false)
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
    }
  }, [])

  useEffect(() => {
    const resolveParams = async () => {
      const resolvedParams = await params
      setJobId(resolvedParams.jobId)
      
      // Fetch job data
      setLoading(true)
      try {
        const { data: jobData, error: jobError } = await jobsApi.getById(resolvedParams.jobId)
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
    resolveParams()
  }, [params])

  const handleStartInterview = async () => {
    if (isStartingInterview) return
    
    // Check if user is logged in (authentication is handled by nginx, but we still validate user data)
    if (!user) {
      showToast.error('Please log in to start the interview')
      router.push('/login')
      return
    }

    // Check if user has a resume
    if (!user.hasResume) {
      showToast.error('Please upload your resume before starting the interview')
      router.push('/upload')
      return
    }

    // Find user's application for this job
    const application = user.applications?.find(app => app.jobId === jobId)
    
    if (!application) {
      showToast.error('Application not found for this job. Please apply first.')
      router.push(`/jobs/${jobId}`)
      return
    }

    // Check if application is qualified for interview
    if (!application.qualified) {
      showToast.error('Your application is not qualified for an interview yet.')
      router.push('/applications')
      return
    }

    setIsStartingInterview(true)
    showToast.info('Starting your interview...')

    // With the new unified API, we don't need to start interview separately
    // Just redirect to active page and let it handle the interview state
    try {
      showToast.success('Loading your interview...')
      router.push(`/interview/${jobId}/active`)
    } catch (error: any) {
      console.error('Failed to navigate to interview:', error)
      showToast.error('Failed to start interview. Please try again.')
    } finally {
      setIsStartingInterview(false)
    }
  }

  const handleGoBack = () => {
    window.location.href = '/dashboard'
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation userState={userState} user={user} theme="light" />
        <main className="container mx-auto px-6 py-8">
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading interview preparation...</p>
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
              <div className="text-red-600 text-6xl mb-4">
                <AlertTriangle className="w-16 h-16 mx-auto text-error-500" />
              </div>
              <h1 className="text-2xl font-bold text-gray-800 mb-2">Job Not Found</h1>
              <p className="text-gray-600 mb-6">{error || 'The requested job could not be found.'}</p>
              <Button onClick={handleGoBack} variant="primary">Return to Dashboard</Button>
            </div>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation userState={userState} user={user} theme="light" />
      
      <main className="container mx-auto px-6 py-8">
        {/* Two-column layout */}
        <div className="flex gap-8">
          {/* Main Content */}
          <div className="flex-1">
            {/* Job Header */}
            <div className="mb-8">
              <h1 className="text-red-600 text-4xl font-bold mb-4 leading-tight">{job.title}</h1>
              <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-6 text-gray-500 text-sm">
                  <div className="flex items-center gap-1">
                    <Calendar className="w-4 h-4 text-purple-600" />
                    Interview Duration: {job.interview_duration_minutes || 60} minutes
                  </div>
                </div>
                <div className="flex gap-4">
                  <Button 
                    variant="secondary" 
                    size="default" 
                    onClick={handleGoBack}
                    className="px-6 py-3 bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                  >
                    I Need More Time
                  </Button>
                  <Button 
                    variant="primary" 
                    size="default" 
                    onClick={handleStartInterview}
                    disabled={isStartingInterview}
                    className="px-6 py-3"
                  >
                    {isStartingInterview ? 'Starting...' : "I'm Ready - Start Interview"}
                  </Button>
                </div>
              </div>
            </div>

            {/* Navigation */}
            <div className="flex justify-between items-center mb-8 text-red-600 text-sm">
              <Link href="/dashboard" className="text-red-600 no-underline flex items-center gap-2 hover:text-red-700">
                ← Back to Dashboard
              </Link>
            </div>

            {/* Interview Rules Section */}
            <div className="bg-red-50 border border-red-200 rounded-xl p-8 mb-12">
              <h2 className="text-xl font-semibold text-red-600 mb-6 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-error-600" />
                Interview Guidelines & Rules
              </h2>
              
              <div className="space-y-6">
                <div>
                  <h4 className="font-semibold text-red-800 mb-3 flex items-center gap-1">
                    <Ban className="w-4 h-4 text-error-600" />
                    Prohibited Activities
                  </h4>
                  <ul className="list-none pl-4 text-red-900">
                    <li className="mb-2 flex items-start gap-2">
                      <span className="text-red-600 font-bold">•</span>
                      <span><strong>Copy & Paste:</strong> Copying and pasting text is disabled during the interview</span>
                    </li>
                    <li className="mb-2 flex items-start gap-2">
                      <span className="text-red-600 font-bold">•</span>
                      <span><strong>Tab Switching:</strong> Switching to other browser tabs or applications is not allowed</span>
                    </li>
                    <li className="mb-2 flex items-start gap-2">
                      <span className="text-red-600 font-bold">•</span>
                      <span><strong>JavaScript Modification:</strong> Attempting to modify browser developer tools or JavaScript is prohibited</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-red-600 font-bold">•</span>
                      <span><strong>External Assistance:</strong> Using external resources, tools, or getting help from others during the interview</span>
                    </li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-red-800 mb-3 flex items-center gap-1">
                    <Scale className="w-4 h-4 text-warning-600" />
                    Violation Policy
                  </h4>
                  <p className="text-red-900 mb-4">Our AI monitoring system will detect violations and respond as follows:</p>
                  <ul className="list-none pl-4 text-red-900">
                    <li className="mb-2 flex items-start gap-2">
                      <span className="text-amber-500 font-bold">1st & 2nd Violation:</span>
                      <span>You will receive a warning and the interview will continue</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-red-600 font-bold">3rd Violation:</span>
                      <span>The interview will be automatically terminated and marked as incomplete</span>
                    </li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-red-800 mb-3 flex items-center gap-1">
                    <Clock className="w-4 h-4 text-purple-600" />
                    Time Management
                  </h4>
                  <ul className="list-none pl-4 text-red-900">
                    <li className="mb-2 flex items-start gap-2">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span><strong>Duration:</strong> This interview is scheduled for {job.interview_duration_minutes || 60} minutes</span>
                    </li>
                    <li className="mb-2 flex items-start gap-2">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span><strong>Auto-End:</strong> The interview will automatically end when time expires</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span><strong>Manual Exit:</strong> You can end the interview early at any time using the &ldquo;End Interview&rdquo; button</span>
                    </li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-red-800 mb-3 flex items-center gap-1">
                    <Wrench className="w-4 h-4 text-primary-500" />
                    Technical Issues & Recovery
                  </h4>
                  <ul className="list-none pl-4 text-red-900">
                    <li className="mb-2 flex items-start gap-2">
                      <span className="text-blue-500 font-bold">•</span>
                      <span><strong>Reconnection Window:</strong> If technical issues occur, you can reconnect and resume your interview as long as the total scheduled time hasn&apos;t elapsed</span>
                    </li>
                    <li className="mb-2 flex items-start gap-2">
                      <span className="text-blue-500 font-bold">•</span>
                      <span><strong>Example:</strong> If your interview starts at 2:00 PM for 30 minutes, you can reconnect until 2:30 PM, even if you were disconnected</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-500 font-bold">•</span>
                      <span><strong>Progress Saved:</strong> Your answers and progress will be automatically saved and restored upon reconnection</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Role Description */}
            <div className="bg-white border border-gray-200 rounded-xl p-8">
              
              <Markdown 
                content={`${job.description}

## Requirements
${job.requirements.map(req => `- ${req}`).join('\n')}
${job.benefits && job.benefits.length > 0 ? `\n## Benefits and Perks\n${job.benefits.map(benefit => `- ${benefit}`).join('\n')}` : ''}
${job.salaryRange ? `\n## Compensation\n$${job.salaryRange.min.toLocaleString()} - $${job.salaryRange.max.toLocaleString()} ${job.salaryRange.currency} annually` : ''}`}
                className="text-gray-600"
              />
            </div>
          </div>

          {/* Sidebar */}
          <aside className="w-80 space-y-8">

            {/* Preparation Tips */}
            <div className="border border-gray-200 rounded-lg p-6">
              <h4 className="font-semibold mb-4 text-gray-800 flex items-center gap-1">
                <Lightbulb className="w-4 h-4 text-warning-500" />
                Preparation Tips
              </h4>
              <ul className="list-none p-0 text-sm text-gray-600">
                <li className="mb-3 flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-success-600" />
                  <span>Ensure stable internet connection</span>
                </li>
                <li className="mb-3 flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-success-600" />
                  <span>Use a quiet environment</span>
                </li>
                <li className="mb-3 flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-success-600" />
                  <span>Close unnecessary applications</span>
                </li>
                <li className="mb-3 flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-success-600" />
                  <span>Have your resume nearby for reference</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-success-600" />
                  <span>Test your microphone and camera</span>
                </li>
              </ul>
            </div>

            {/* Technical Requirements */}
            <div className="border border-gray-200 rounded-lg p-6">
              <h4 className="font-semibold mb-4 text-gray-800 flex items-center gap-1">
                <Settings className="w-4 h-4 text-primary-500" />
                Technical Requirements
              </h4>
              <ul className="list-none p-0 text-sm text-gray-600">
                <li className="mb-3 flex items-start gap-2">
                  <span className="text-blue-500">•</span>
                  <span>Chrome, Firefox, Safari, or Edge browser</span>
                </li>
                <li className="mb-3 flex items-start gap-2">
                  <span className="text-blue-500">•</span>
                  <span>Microphone access for voice responses</span>
                </li>
                <li className="mb-3 flex items-start gap-2">
                  <span className="text-blue-500">•</span>
                  <span>Camera access for verification</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-500">•</span>
                  <span>Minimum 5 Mbps internet speed</span>
                </li>
              </ul>
            </div>
          </aside>
        </div>
      </main>
      
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  )
}