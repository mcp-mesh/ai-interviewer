"use client"

import { useState, useEffect, Suspense } from 'react'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { Markdown } from '@/components/ui/markdown'
import { Job, User } from '@/lib/types'
import { jobsApi } from '@/lib/api'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { Calendar, MapPin, Clock } from 'lucide-react'
import type { UserApplication } from '@/lib/types'


// Mock similar jobs data
const similarJobs = [
  {
    id: '2',
    title: 'Specialist I, Reconciliation',
    location: 'Oaks, Pennsylvania, United States of America',
    type: 'Full time'
  },
  {
    id: '3', 
    title: 'Operations Analyst, Enhanced Middle Office (Bank Debt)',
    location: 'Oaks, Pennsylvania, United States of America',
    type: 'Full time'
  }
]

const jobSeekersViewed = [
  {
    id: '4',
    title: 'Operations Analyst, Separately Managed Accounts',
    location: 'Oaks, Pennsylvania, United States of America', 
    type: 'Full time'
  },
  {
    id: '5',
    title: 'Operations Analyst, AIFS Investor Services',
    location: 'Oaks, Pennsylvania, United States of America',
    type: 'Full time'  
  },
  {
    id: '6',
    title: 'Operations Analyst, Enhanced Middle Office (Bank Debt)',
    location: 'Oaks, Pennsylvania, United States of America',
    type: 'Full time'
  }
]

function JobDetailContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const jobId = searchParams.get('id')
  const [user, setUser] = useState<User | null>(null)
  const [job, setJob] = useState<Job | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [applying, setApplying] = useState(false)
  
  useEffect(() => {
    // Get user from localStorage
    const userData = localStorage.getItem('user')
    if (userData) {
      const parsedUser = JSON.parse(userData)
      setUser(parsedUser)
    }
  }, [])

  useEffect(() => {
    const loadJobData = async () => {
      if (!jobId) return
      
      setLoading(true)
      setError(null)
      
      try {
        const jobResponse = await jobsApi.getById(jobId)
        if (jobResponse.data) {
          setJob(jobResponse.data)
        } else {
          console.error('Job not found:', jobResponse.error || 'Job not found')
          // setError(jobResponse.error || 'Job not found') // TODO: May need error state management
        }
      } catch (error) {
        console.error('Failed to fetch job details:', error)
        // setError('Failed to load job details') // TODO: May need error state management
      }
      
      setLoading(false)
    }
    
    loadJobData()
  }, [jobId])

  // Calculate user state early for use in all render paths
  const isGuest = !user
  const userState = isGuest ? "guest" : (user.hasResume ? "has-resume" : "no-resume")

  // Loading state
  if (loading) {
    return (
      <div className="page-light min-h-screen">
        <Navigation userState={userState} user={user} theme="light" />
        <main className="container max-w-[1400px] mx-auto px-6 pt-20">
          <div className="text-center py-20">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Loading...</h1>
            <p className="text-gray-600">Loading job details...</p>
          </div>
        </main>
      </div>
    )
  }

  // Error or not found state
  if (error || !job) {
    return (
      <div className="page-light min-h-screen">
        <Navigation userState={userState} user={user} theme="light" />
        <main className="container max-w-[1400px] mx-auto px-6 pt-20">
          <div className="text-center py-20">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Job Not Found</h1>
            <p className="text-gray-600 mb-6">{error || 'The job you&apos;re looking for doesn&apos;t exist or has been removed.'}</p>
            <Link href="/jobs">
              <Button variant="primary">Back to Jobs</Button>
            </Link>
          </div>
        </main>
      </div>
    )
  }

  // Find application for this job
  const currentApplication = user?.applications?.find(app => app.jobId === job?.id)
  const applicationStatus = currentApplication?.status

  // Helper functions for different actions
  const handleStartInterview = () => {
    if (currentApplication) {
      router.push(`/interview/job/prepare/?id=${currentApplication.jobId}`)
    }
  }

  const handleContinueApplication = async () => {
    if (!job?.id) return
    setApplying(true)
    
    try {
      const { applicationsApi } = await import('@/lib/api-client')
      const result = await applicationsApi.startApplication(job.id)
      
      if (result.data) {
        const { applicationId, prefillData, currentStep } = result.data
        localStorage.setItem('currentApplication', JSON.stringify({
          applicationId,
          jobId: job.id,
          currentStep: currentStep || 1,
          prefillData: prefillData || null
        }))
        
        // Refresh user profile to get updated applications list with new STARTED status
        try {
          const { userApi } = await import('@/lib/api')
          const userResult = await userApi.getProfile()
          if (userResult.data) {
            localStorage.setItem('user', JSON.stringify(userResult.data))
            console.log('User profile refreshed after starting application')
          }
        } catch (profileError) {
          console.error('Failed to refresh user profile:', profileError)
          // Don't block the flow if profile refresh fails
        }
        
        router.push(`/apply/job/?id=${job.id}`)
      }
    } catch (error) {
      console.error('Error continuing application:', error)
    } finally {
      setApplying(false)
    }
  }

  const handleContinueInterview = () => {
    if (currentApplication) {
      router.push(`/interview/job/prepare/?id=${currentApplication.jobId}`)
    }
  }

  const handleApplyNow = async () => {
    if (!job?.id || applying) return
    
    if (isGuest) {
      // Show login modal or redirect to login
      router.push(`/login?redirect=/apply/job/?id=${job.id}`)
      return
    }

    // Start the application using our new API with timeout
    setApplying(true)
    try {
      const { applicationsApi } = await import('@/lib/api-client')
      
      // Create a timeout promise
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Application setup timed out')), 15000)
      })
      
      // Race between API call and timeout
      const result = await Promise.race([
        applicationsApi.startApplication(job.id),
        timeoutPromise
      ]) as { data: { applicationId: string; prefillData?: Record<string, unknown>; currentStep?: number } | null; error?: string }
      
      if (result.data) {
        // Success! Redirect to application page with the application_id and prefill data
        const { applicationId, prefillData, currentStep } = result.data
        
        // Store application data for the application page
        localStorage.setItem('currentApplication', JSON.stringify({
          applicationId,
          jobId: job.id,
          currentStep: currentStep || 1,
          prefillData: prefillData || null
        }))
        
        // Refresh user profile to get updated applications list with new STARTED status
        try {
          const { userApi } = await import('@/lib/api')
          const userResult = await userApi.getProfile()
          if (userResult.data) {
            localStorage.setItem('user', JSON.stringify(userResult.data))
            console.log('User profile refreshed after starting application')
          }
        } catch (profileError) {
          console.error('Failed to refresh user profile:', profileError)
          // Don't block the flow if profile refresh fails
        }
        
        console.log('Application started:', { applicationId, currentStep, hasPrefillData: !!prefillData })
        router.push(`/apply/job/?id=${job.id}`)
      } else {
        // Handle API error response
        console.error('Failed to start application:', result.error)
        alert(`Failed to start application: ${result.error || 'Please try again.'}`)
      }
    } catch (error) {
      console.error('Error starting application:', error)
      
      // Handle different error types
      if (error instanceof Error) {
        if (error.message.includes('timed out')) {
          alert('Application setup took longer than expected. Please try again or continue without AI prefill.')
        } else if (error.message.includes('network') || error.message.includes('fetch')) {
          alert('Network error. Please check your connection and try again.')
        } else {
          alert(`Error: ${error.message}`)
        }
      } else {
        alert('An unexpected error occurred. Please try again.')
      }
    } finally {
      setApplying(false)
    }
  }

  const handleBackToSearch = () => {
    if (user?.hasResume) {
      router.push('/jobs/matched')
    } else {
      router.push('/jobs')
    }
  }

  return (
    <div className="page-light min-h-screen">
      <Navigation userState={userState} user={user} theme="light" />
      
      <main className="container max-w-[1400px] mx-auto px-6 pt-20 pb-8">
        {/* Two-column layout */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            {/* Job Header */}
            <div className="mb-8">
              <h1 className="text-4xl font-bold text-red-600 mb-4 leading-tight">
                {job.title}
              </h1>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                <div className="flex flex-wrap items-center gap-6 text-sm text-gray-600">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-4 h-4 text-purple-600" />
                    {job.postedAt ? new Date(job.postedAt).toLocaleDateString('en-US', { 
                      year: 'numeric', 
                      month: 'short', 
                      day: 'numeric' 
                    }) : 'Recently posted'}
                  </span>
                  <span className="flex items-center gap-1">
                    <MapPin className="w-4 h-4 text-primary-600" />
                    {job.location}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4 text-purple-600" />
                    {job.type}
                  </span>
                </div>
                {/* Dynamic button based on application status */}
                {!currentApplication ? (
                  // No application yet - show Apply Now
                  <Button 
                    variant="primary" 
                    size="lg"
                    onClick={handleApplyNow}
                    disabled={loading || applying}
                    className="flex items-center gap-2"
                  >
                    {applying && (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    )}
                    {applying ? 'Starting Application...' : loading ? 'Loading...' : 'Apply Now'}
                  </Button>
                ) : applicationStatus === 'QUALIFIED' ? (
                  // Ready for interview - green button
                  <Button 
                    variant="success" 
                    size="lg"
                    onClick={handleStartInterview}
                    className="flex items-center gap-2"
                  >
                    Start Interview
                  </Button>
                ) : applicationStatus === 'STARTED' ? (
                  // Application in progress
                  <Button 
                    variant="primary" 
                    size="lg"
                    onClick={handleContinueApplication}
                    disabled={applying}
                    className="flex items-center gap-2"
                  >
                    {applying && (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    )}
                    {applying ? 'Continuing...' : 'Continue Application'}
                  </Button>
                ) : applicationStatus === 'INPROGRESS' ? (
                  // Interview in progress
                  <Button 
                    variant="primary" 
                    size="lg"
                    onClick={handleContinueInterview}
                    className="flex items-center gap-2"
                  >
                    Continue Interview
                  </Button>
                ) : applicationStatus === 'APPLIED' ? (
                  // Application submitted - just a label
                  <div className="px-6 py-3 bg-blue-100 text-blue-800 rounded-md text-sm font-medium">
                    Applied
                  </div>
                ) : applicationStatus === 'COMPLETED' ? (
                  // Interview completed - just a label
                  <div className="px-6 py-3 bg-green-100 text-green-800 rounded-md text-sm font-medium">
                    Completed
                  </div>
                ) : (
                  // Fallback - show Apply Now
                  <Button 
                    variant="primary" 
                    size="lg"
                    onClick={handleApplyNow}
                    disabled={loading || applying}
                    className="flex items-center gap-2"
                  >
                    {applying && (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    )}
                    {applying ? 'Starting Application...' : loading ? 'Loading...' : 'Apply Now'}
                  </Button>
                )}
              </div>
            </div>

            {/* Navigation */}
            <div className="flex justify-between items-center mb-8 text-sm text-red-600">
              <button
                onClick={handleBackToSearch}
                className="flex items-center gap-2 hover:text-red-700 transition-colors"
              >
                ← Back to search results
              </button>
              <div className="flex gap-4">
                <button className="hover:text-red-700 transition-colors">
                  ← Previous job
                </button>
                <button className="hover:text-red-700 transition-colors">
                  Next job →
                </button>
              </div>
            </div>

            {/* Job Description */}
            <div className="space-y-6">
              <Markdown content={job.description} />

              {job.requirements && job.requirements.length > 0 && (
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-4">Requirements:</h3>
                  <ul className="list-disc pl-6 space-y-2">
                    {job.requirements.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {job.benefits && job.benefits.length > 0 && (
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-4">Benefits:</h3>
                  <ul className="list-disc pl-6 space-y-2">
                    {job.benefits.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {job.salaryRange && (
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-4">Salary Range:</h3>
                  <p>
                    {job.salaryRange.currency || '$'}{job.salaryRange.min?.toLocaleString()} - {job.salaryRange.currency || '$'}{job.salaryRange.max?.toLocaleString()}
                    {job.salaryRange.currency && job.salaryRange.currency !== '$' ? ` ${job.salaryRange.currency}` : ''}
                  </p>
                </div>
              )}

              <p>
                We are a technology and asset management company delivering on our promise of building brave futures—
                for our clients, our communities, and ourselves. Come build your brave future with us.
              </p>

              <p>We are an Equal Opportunity Employer and welcome applications from all qualified candidates.</p>

              <Button variant="secondary" className="bg-red-600 hover:bg-red-700 text-white flex items-center gap-2">
                <MapPin className="w-4 h-4 text-white" />
                Explore Location
              </Button>
            </div>
          </div>

          {/* Sidebar */}
          <aside className="lg:col-span-1">
            {/* Similar Jobs */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
              <h4 className="font-semibold text-gray-900 mb-4">Similar Jobs</h4>
              <div className="space-y-4">
                {similarJobs.map((similarJob) => (
                  <div key={similarJob.id} className="pb-4 border-b border-gray-200 last:border-b-0 last:pb-0">
                    <Link href={`/jobs/job/?id=${similarJob.id}`}>
                      <h5 className="text-red-600 hover:text-red-700 underline text-sm font-medium mb-2 cursor-pointer">
                        {similarJob.title}
                      </h5>
                    </Link>
                    <div className="text-gray-600 text-xs space-y-1">
                      <div className="flex items-center gap-1">
                        <MapPin className="w-4 h-4 text-primary-600" />
                        {similarJob.location}
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4 text-purple-600" />
                        {similarJob.type}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Job seekers also viewed */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
              <h4 className="font-semibold text-gray-900 mb-4">Job seekers also viewed</h4>
              <div className="space-y-4">
                {jobSeekersViewed.map((viewedJob) => (
                  <div key={viewedJob.id} className="pb-4 border-b border-gray-200 last:border-b-0 last:pb-0">
                    <Link href={`/jobs/job/?id=${viewedJob.id}`}>
                      <h5 className="text-red-600 hover:text-red-700 underline text-sm font-medium mb-2 cursor-pointer">
                        {viewedJob.title}
                      </h5>
                    </Link>
                    <div className="text-gray-600 text-xs space-y-1">
                      <div className="flex items-center gap-1">
                        <MapPin className="w-4 h-4 text-primary-600" />
                        {viewedJob.location}
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4 text-purple-600" />
                        {viewedJob.type}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Share this opportunity */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h4 className="font-semibold text-gray-900">Share this opportunity</h4>
            </div>
          </aside>
        </div>
      </main>
    </div>
  )
}

export default function JobDetailPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg p-6 flex items-center space-x-3">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600" />
          <span className="text-gray-700">Loading job details...</span>
        </div>
      </div>
    }>
      <JobDetailContent />
    </Suspense>
  )
}