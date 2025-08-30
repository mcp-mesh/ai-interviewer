"use client"

import { useState } from "react"
import Link from "next/link"
import { InterviewTimer } from "./InterviewTimer"
import { Button } from "@/components/ui/button"
import { UserCircle, LogOut, Shield, ShieldOff } from "lucide-react"
import { User, Job } from "@/lib/types"
import { cn } from "@/lib/utils"

interface InterviewHeaderProps {
  job: Job
  user: User | null
  timeRemaining: number
  questionsAsked?: number
  questionsAnswered?: number
  isResumedSession?: boolean
  isEndingInterview?: boolean
  isSecurityEnabled?: boolean
  onEndInterview?: () => void
  onTimeUpdate?: (timeRemaining: number) => void
  onTimeExpired?: () => void
  className?: string
}

export function InterviewHeader({
  job,
  user,
  timeRemaining,
  questionsAsked = 1,
  questionsAnswered = 0,
  isResumedSession = false,
  isEndingInterview = false,
  isSecurityEnabled = false,
  onEndInterview,
  onTimeUpdate,
  onTimeExpired,
  className
}: InterviewHeaderProps) {
  const [showEndConfirmation, setShowEndConfirmation] = useState(false)

  const handleEndInterview = () => {
    setShowEndConfirmation(true)
  }

  const confirmEndInterview = () => {
    setShowEndConfirmation(false)
    onEndInterview?.()
  }

  const cancelEndInterview = () => {
    setShowEndConfirmation(false)
  }

  const handleLogout = async () => {
    try {
      // Clear local storage
      localStorage.removeItem('user')
      localStorage.removeItem('token')
      
      // Redirect to home
      window.location.href = '/'
    } catch (error) {
      console.error('Logout error:', error)
      window.location.href = '/'
    }
  }

  return (
    <>
      <div className={cn("bg-white border-b border-gray-200 shadow-sm sticky top-0 z-40", className)}>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Left section - Job info */}
            <Link href="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
              <div className="bg-gradient-to-r from-red-600 to-red-700 p-2 rounded-lg">
                <UserCircle className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">
                  Interview: {job.title}
                  {isResumedSession && (
                    <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                      Resumed
                    </span>
                  )}
                </h1>
                <p className="text-sm text-gray-500">
                  Question {questionsAsked} • {questionsAnswered} answered
                </p>
              </div>
            </Link>

            {/* Right section - Timer and controls */}
            <div className="flex items-center space-x-4">
              {/* Timer */}
              <InterviewTimer
                initialTimeRemaining={timeRemaining}
                onTimeUpdate={onTimeUpdate}
                onTimeExpired={onTimeExpired}
              />

              {/* End Interview button */}
              <Button
                onClick={handleEndInterview}
                disabled={isEndingInterview}
                variant="ghost"
                className="text-red-600 hover:text-red-700 hover:bg-red-50 font-medium"
              >
                {isEndingInterview ? 'Ending...' : 'End Interview'}
              </Button>
              
              {/* Logout button */}
              <Button
                onClick={handleLogout}
                variant="ghost" 
                size="sm"
                className="text-gray-600 hover:text-gray-900"
              >
                <LogOut className="h-4 w-4 mr-1" />
                Logout
              </Button>
              
              {/* Security Mode Indicator */}
              <div className={cn(
                "px-2 py-1 rounded text-xs font-medium flex items-center space-x-1",
                isSecurityEnabled 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-orange-100 text-orange-800'
              )}>
                {isSecurityEnabled ? (
                  <>
                    <Shield className="h-3 w-3" />
                    <span>Secure</span>
                  </>
                ) : (
                  <>
                    <ShieldOff className="h-3 w-3" />
                    <span>Dev Mode</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* End Interview Confirmation Modal */}
      {showEndConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 shadow-lg max-w-md w-full">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              End Interview?
            </h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to end the interview? This action cannot be undone and your responses will be submitted for evaluation.
            </p>
            <div className="flex space-x-3 justify-end">
              <Button
                onClick={cancelEndInterview}
                variant="secondary"
              >
                Continue Interview
              </Button>
              <Button
                onClick={confirmEndInterview}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                End Interview
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}