"use client"

import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Navigation } from "@/components/navigation"
import { Button } from "@/components/ui/button"
import { CheckCircle2, XCircle, Clock, AlertTriangle } from "lucide-react"
import { UserState, User } from "@/lib/types"
import { SuspenseWrapper } from "@/components/common"

function CompleteInterviewPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [jobId, setJobId] = useState<string>("")
  const [reason, setReason] = useState<string>("completed")
  const [user, setUser] = useState<User | null>(null)
  const [userState, setUserState] = useState<UserState>("guest")

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

  // Get jobId and completion reason from URL params
  useEffect(() => {
    const jobIdParam = searchParams.get('jobId') || searchParams.get('id')
    const completionReason = searchParams.get('reason') || 'completed'
    
    if (jobIdParam) {
      setJobId(jobIdParam)
    }
    setReason(completionReason)
  }, [searchParams])

  const getCompletionDetails = () => {
    switch (reason) {
      case 'completed':
        return {
          icon: <CheckCircle2 className="w-16 h-16 text-green-600" />,
          title: 'Interview Completed Successfully!',
          message: 'Thank you for completing the interview. Your responses have been submitted for review.',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          textColor: 'text-green-900',
          buttonColor: 'bg-green-600 hover:bg-green-700'
        }
      case 'terminated':
        return {
          icon: <XCircle className="w-16 h-16 text-red-600" />,
          title: 'Interview Terminated',
          message: 'Your interview was terminated due to policy violations. Please contact support if you believe this was an error.',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          textColor: 'text-red-900',
          buttonColor: 'bg-red-600 hover:bg-red-700'
        }
      case 'time_up':
        return {
          icon: <Clock className="w-16 h-16 text-orange-600" />,
          title: 'Interview Time Expired',
          message: 'The interview time has elapsed. Your responses up to this point have been submitted for review.',
          bgColor: 'bg-orange-50',
          borderColor: 'border-orange-200',
          textColor: 'text-orange-900',
          buttonColor: 'bg-orange-600 hover:bg-orange-700'
        }
      default:
        return {
          icon: <AlertTriangle className="w-16 h-16 text-gray-600" />,
          title: 'Interview Ended',
          message: 'Your interview has ended. Please check your email for next steps.',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          textColor: 'text-gray-900',
          buttonColor: 'bg-gray-600 hover:bg-gray-700'
        }
    }
  }

  const completionDetails = getCompletionDetails()

  const handleReturnToDashboard = () => {
    router.push('/dashboard')
  }

  const handleViewApplications = () => {
    router.push('/applications')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation userState={userState} user={user} theme="light" />
      
      <main className="container mx-auto px-6 py-8">
        <div className="flex items-center justify-center min-h-[500px]">
          <div className="max-w-2xl w-full">
            <div className={`${completionDetails.bgColor} ${completionDetails.borderColor} border rounded-xl p-8 text-center`}>
              <div className="mb-6">
                {completionDetails.icon}
              </div>
              
              <h1 className={`text-2xl font-bold ${completionDetails.textColor} mb-4`}>
                {completionDetails.title}
              </h1>
              
              <p className={`${completionDetails.textColor} mb-8 text-lg leading-relaxed`}>
                {completionDetails.message}
              </p>
              
              <div className="space-y-4">
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <Button
                    onClick={handleReturnToDashboard}
                    className={`${completionDetails.buttonColor} text-white px-8 py-3`}
                  >
                    Return to Dashboard
                  </Button>
                  
                  <Button
                    onClick={handleViewApplications}
                    variant="secondary"
                    className="px-8 py-3"
                  >
                    View My Applications
                  </Button>
                </div>
              </div>
            </div>
            
            {/* Additional Information */}
            <div className="mt-8 bg-white border border-gray-200 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">What Happens Next?</h3>
              <div className="space-y-3 text-gray-600">
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-red-600 rounded-full mt-2 flex-shrink-0"></div>
                  <p>Your interview responses are being evaluated by our AI system</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-red-600 rounded-full mt-2 flex-shrink-0"></div>
                  <p>You will receive an email notification with your results within 24 hours</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-red-600 rounded-full mt-2 flex-shrink-0"></div>
                  <p>If selected, our team will contact you to schedule the next interview round</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-red-600 rounded-full mt-2 flex-shrink-0"></div>
                  <p>You can track your application status in your dashboard at any time</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default function CompleteInterviewPage() {
  return (
    <SuspenseWrapper>
      <CompleteInterviewPageContent />
    </SuspenseWrapper>
  )
}