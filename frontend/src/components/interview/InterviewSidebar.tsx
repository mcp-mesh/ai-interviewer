"use client"

import { Job, User } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { 
  Clock, 
  MessageSquare, 
  CheckCircle2, 
  AlertCircle,
  Building,
  MapPin,
  Calendar,
  Settings,
  HelpCircle
} from "lucide-react"
import { InterviewTimer } from "./InterviewTimer"
import { CameraPreview } from "./CameraPreview"
import { cn } from "@/lib/utils"

interface InterviewSidebarProps {
  job: Job
  user: User | null
  timeRemaining: number
  questionsAsked: number
  questionsAnswered: number
  isEndingInterview: boolean
  isSecurityEnabled: boolean
  onEndInterview: () => void
  onTimeUpdate: (seconds: number) => void
  onTimeExpired: () => void
  className?: string
}

export function InterviewSidebar({
  job,
  user,
  timeRemaining,
  questionsAsked,
  questionsAnswered,
  isEndingInterview,
  isSecurityEnabled,
  onEndInterview,
  onTimeUpdate,
  onTimeExpired,
  className
}: InterviewSidebarProps) {
  
  const progressPercentage = questionsAsked > 0 ? (questionsAnswered / questionsAsked) * 100 : 0
  
  // Calculate time percentage using job's interview duration
  const totalMinutes = job.interview_duration_minutes || 60 // Use job duration or default to 60
  const timePercentage = Math.max(0, (timeRemaining / (totalMinutes * 60)) * 100)
  
  const getTimeStatus = () => {
    const percentage = timePercentage
    if (percentage > 50) return { color: "text-emerald-600", bgColor: "bg-emerald-100", status: "Good" }
    if (percentage > 25) return { color: "text-yellow-600", bgColor: "bg-yellow-100", status: "Moderate" }
    return { color: "text-red-600", bgColor: "bg-red-100", status: "Critical" }
  }
  
  const timeStatus = getTimeStatus()

  return (
    <div className={cn(
      "w-80 bg-white border-r border-gray-200 flex flex-col h-full shadow-sm",
      className
    )}>
      {/* Job Information Header */}
      <div className="p-6 border-b border-gray-100">
        <h1 className="font-bold text-lg text-red-600 leading-tight">
          {job.title}
        </h1>
      </div>

      {/* Interview Timer - Prominent Section */}
      <div className="p-6 border-b border-gray-100">
        {/* Unified Timer and Progress Component */}
        <div className="w-full">
          {/* Timer Display - Full Width */}
          <div className={cn(
            "w-full px-4 py-3 text-center bg-blue-100 transition-all duration-500",
            timePercentage > 50 ? "text-emerald-600" : 
            timePercentage > 25 ? "text-yellow-600" : "text-red-600"
          )}>
            <div className="text-4xl font-mono font-bold">
              <InterviewTimer
                initialTimeRemaining={timeRemaining}
                onTimeUpdate={onTimeUpdate}
                onTimeExpired={onTimeExpired}
                className=""
              />
            </div>
          </div>
          
          {/* Progress Bar - Full Width, No Gap */}
          <div className="w-full bg-gray-200 h-2">
            <div 
              className={cn(
                "h-2 transition-all duration-500",
                timePercentage > 50 ? "bg-emerald-500" : 
                timePercentage > 25 ? "bg-yellow-500" : "bg-red-500"
              )}
              style={{ width: `${Math.max(0, timePercentage)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Progress Section */}
      <div className="p-6 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <MessageSquare className="w-4 h-4" />
          Interview Progress
        </h3>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Questions Asked</span>
            <span className="font-semibold text-gray-900">{questionsAsked}</span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Questions Answered</span>
            <span className="font-semibold text-gray-900">{questionsAnswered}</span>
          </div>
        </div>
      </div>

      {/* Interview Actions */}
      <div className="p-6 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Interview Controls</h3>
        
        <div className="space-y-3">
          <Button
            onClick={onEndInterview}
            disabled={isEndingInterview}
            size="lg"
            className="w-full bg-red-600 hover:bg-red-700 text-white border-red-600 hover:border-red-700 transition-colors duration-200"
          >
            {isEndingInterview ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Ending...
              </>
            ) : (
              <>
                <AlertCircle className="w-4 h-4 mr-2" />
                End Interview
              </>
            )}
          </Button>
          
        </div>
      </div>

      {/* Session Recording */}
      <div className="p-6 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Session Recording</h3>
        <CameraPreview className="w-full h-32" />
      </div>

      {/* Quick Tips - Always Visible */}
      <div className="p-6 bg-blue-50">
        <h4 className="text-sm font-semibold text-blue-800 mb-3">Quick Tips</h4>
        <ul className="text-xs text-blue-700 space-y-2">
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-3 h-3 mt-0.5 text-blue-600" />
            Take your time to think before responding
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-3 h-3 mt-0.5 text-blue-600" />
            Use specific examples from your experience
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-3 h-3 mt-0.5 text-blue-600" />
            Ask for clarification if needed
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-3 h-3 mt-0.5 text-blue-600" />
            Stay focused on the role requirements
          </li>
        </ul>
      </div>

    </div>
  )
}