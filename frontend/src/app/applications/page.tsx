"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { User, UserApplication } from '@/lib/types'
import { jobsApi } from '@/lib/api'
import Link from 'next/link'
import { MapPin, Clock, Calendar, RotateCw, Target, CheckCircle, FileText } from 'lucide-react'

interface ApplicationWithJob extends UserApplication {
  job?: any // Will be populated from API
}

export default function ApplicationsPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [applications, setApplications] = useState<ApplicationWithJob[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      
      // Get user from localStorage
      const userData = localStorage.getItem('user')
      if (userData) {
        const parsedUser = JSON.parse(userData)
        setUser(parsedUser)
        
        // Load job details for each application
        if (parsedUser.applications && parsedUser.applications.length > 0) {
          const applicationsWithJobs = await Promise.all(
            parsedUser.applications.map(async (app: UserApplication) => {
              try {
                const jobResponse = await jobsApi.getById(app.jobId)
                return {
                  ...app,
                  job: jobResponse.data
                }
              } catch (error) {
                console.error(`Failed to fetch job ${app.jobId}:`, error)
                return { ...app, job: null }
              }
            })
          )
          setApplications(applicationsWithJobs)
        }
      } else {
        // Redirect to login if no user found
        router.push('/login?redirect=/applications')
      }
      
      setLoading(false)
    }
    
    loadData()
  }, [router])

  // Group applications by status
  const inProgressApplications = applications.filter(app => app.status === 'INPROGRESS')
  const eligibleApplications = applications.filter(app => app.status === 'ELIGIBLE')
  const completedApplications = applications.filter(app => app.status === 'COMPLETED')
  const appliedApplications = applications.filter(app => !app.status) // undefined status = just applied

  const handleStartInterview = (application: ApplicationWithJob) => {
    // Update status to INPROGRESS and redirect to interview
    if (user) {
      const updatedApplications = user.applications?.map(app => 
        app.jobId === application.jobId 
          ? { ...app, status: 'INPROGRESS' as const }
          : app
      ) || []
      
      const updatedUser = { ...user, applications: updatedApplications }
      localStorage.setItem('user', JSON.stringify(updatedUser))
      
      // Redirect to interview page
      router.push(`/interview/${application.jobId}/prepare`)
    }
  }

  const handleContinueInterview = (application: ApplicationWithJob) => {
    // Redirect to interview page to continue
    router.push(`/interview/${application.jobId}/prepare`)
  }

  const renderJobCard = (application: ApplicationWithJob, actionButton?: React.ReactNode) => {
    if (!application.job) {
      return (
        <Card key={application.jobId} className="mb-4">
          <CardContent className="p-6">
            <p className="text-gray-500">Job details not available</p>
          </CardContent>
        </Card>
      )
    }

    const job = application.job
    return (
      <Card key={application.jobId} className="mb-4 hover:shadow-md transition-shadow border border-gray-200">
        <CardContent className="p-6">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <Link href={`/jobs/${job.id}`}>
                <h3 className="text-lg font-semibold text-red-600 hover:text-red-700 cursor-pointer underline mb-2">
                  {job.title}
                </h3>
              </Link>
              <p className="text-gray-600 mb-2">{job.company}</p>
              <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4 text-primary-600" /> {job.location}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4 text-purple-600" /> {job.type}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-4 h-4 text-purple-600" /> Applied {new Date(application.appliedAt).toLocaleDateString()}
                </span>
              </div>
              <p className="text-gray-700 text-sm line-clamp-2">
                {job.description}
              </p>
            </div>
            <div className="ml-4 flex flex-col items-end gap-2">
              {actionButton}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card>
          <CardContent className="text-center py-8">
            <p className="mb-4">Please log in to view your applications</p>
            <Button onClick={() => router.push('/login')} variant="primary">Go to Login</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="page-light min-h-screen">
        <Navigation userState="has-resume" user={user} theme="light" />
        <main className="container max-w-[900px] mx-auto px-6 pt-20">
          <div className="py-12 text-center">
            <p>Loading your applications...</p>
          </div>
        </main>
      </div>
    )
  }

  if (applications.length === 0) {
    return (
      <div className="page-light min-h-screen">
        <Navigation userState="has-resume" user={user} theme="light" />
        <main className="container max-w-[900px] mx-auto px-6 pt-20">
          <div className="py-12 text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Your Applications</h1>
            <p className="text-gray-600 mb-8">You haven't submitted any applications yet.</p>
            <Button onClick={() => router.push('/jobs')} variant="primary">
              Browse Jobs
            </Button>
          </div>
        </main>
      </div>
    )
  }

  const userState = user?.isResumeAvailable ? "has-resume" : "no-resume"

  return (
    <div className="page-light min-h-screen">
      <Navigation userState={userState} user={user} theme="light" />
      
      <main className="container max-w-[900px] mx-auto px-6 pt-20">
        <div className="py-12">
          {/* Header */}
          <div className="mb-12">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Your Applications
            </h1>
            <p className="text-gray-600">
              Track your job applications and interview progress
            </p>
          </div>

          {/* Section 1: Interviews In Progress */}
          {inProgressApplications.length > 0 && (
            <div className="mb-12">
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
                <RotateCw className="w-5 h-5 text-warning-600" /> Interviews In Progress
              </h2>
              <p className="text-gray-600 mb-6">Continue your interviews that were interrupted</p>
              {inProgressApplications.map(app => 
                renderJobCard(app, 
                  <Button 
                    onClick={() => handleContinueInterview(app)}
                    variant="primary"
                    size="sm"
                  >
                    Continue Interview
                  </Button>
                )
              )}
            </div>
          )}

          {/* Section 2: Ready for Interview */}
          {eligibleApplications.length > 0 && (
            <div className="mb-12">
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
                <Target className="w-5 h-5 text-primary-600" /> Ready for Interview
              </h2>
              <p className="text-gray-600 mb-6">Congratulations! You're eligible to start your interviews</p>
              {eligibleApplications.map(app => 
                renderJobCard(app, 
                  <Button 
                    onClick={() => handleStartInterview(app)}
                    variant="primary"
                    size="sm"
                  >
                    Start Interview
                  </Button>
                )
              )}
            </div>
          )}

          {/* Section 3: Completed Interviews */}
          {completedApplications.length > 0 && (
            <div className="mb-12">
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-success-600" /> Completed Interviews
              </h2>
              <p className="text-gray-600 mb-6">You've completed these interviews</p>
              {completedApplications.map(app => 
                renderJobCard(app, 
                  <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                    Completed
                  </span>
                )
              )}
            </div>
          )}

          {/* Section 4: Applications Submitted */}
          {appliedApplications.length > 0 && (
            <div className="mb-12">
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary-500" /> Applications Submitted
              </h2>
              <p className="text-gray-600 mb-6">Your applications are being reviewed</p>
              {appliedApplications.map(app => 
                renderJobCard(app, 
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                    Applied
                  </span>
                )
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}