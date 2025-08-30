"use client"

import { useEffect, useState } from "react"
import { Clock } from "lucide-react"

interface InterviewTimerProps {
  initialTimeRemaining: number // in seconds
  onTimeUpdate?: (timeRemaining: number) => void
  onTimeExpired?: () => void
  className?: string
}

export function InterviewTimer({ 
  initialTimeRemaining, 
  onTimeUpdate, 
  onTimeExpired, 
  className = "" 
}: InterviewTimerProps) {
  const [timeRemaining, setTimeRemaining] = useState(initialTimeRemaining)

  useEffect(() => {
    if (initialTimeRemaining !== timeRemaining) {
      setTimeRemaining(initialTimeRemaining)
    }
  }, [initialTimeRemaining])

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        const newTime = prev - 1
        
        if (newTime <= 0) {
          clearInterval(timer)
          onTimeExpired?.()
          return 0
        }
        
        onTimeUpdate?.(newTime)
        return newTime
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [onTimeUpdate, onTimeExpired])

  const formatTime = (seconds: number) => {
    // Use Date constructor to format time properly
    const date = new Date(seconds * 1000)
    return date.toISOString().substr(11, 8) // HH:MM:SS format
  }

  const getTimerColor = () => {
    if (timeRemaining < 60) {
      return "bg-red-100 text-red-700 border-red-200"
    } else if (timeRemaining < 300) { // Less than 5 minutes
      return "bg-orange-100 text-orange-700 border-orange-200"
    } else {
      return "bg-blue-100 text-blue-700 border-blue-200"
    }
  }

  return (
    <span className={`font-mono font-semibold tabular-nums ${className}`}>
      {formatTime(timeRemaining)}
    </span>
  )
}