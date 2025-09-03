"use client"

import { useEffect, useRef, useState } from "react"
import { AlertTriangle, X } from "lucide-react"
import { cn } from "@/lib/utils"

interface SecurityMonitorProps {
  isEnabled?: boolean
  isCompleted?: boolean
  isEndingInterview?: boolean
  onViolation?: (reason: string, count: number) => void
  onTerminate?: (reason: string) => void
  maxViolations?: number
}

export function SecurityMonitor({
  isEnabled = false,
  isCompleted = false,
  isEndingInterview = false,
  onViolation,
  onTerminate,
  maxViolations = 3
}: SecurityMonitorProps) {
  const [violations, setViolations] = useState(0)
  const [showWarning, setShowWarning] = useState(false)
  const [warningMessage, setWarningMessage] = useState('')
  const violationsRef = useRef(0)

  // Keep ref in sync with state
  useEffect(() => {
    violationsRef.current = violations
  }, [violations])

  const handleViolation = (reason: string) => {
    // Increment the ref counter first
    violationsRef.current += 1
    const newViolationCount = violationsRef.current
    
    // Update state to trigger re-render
    setViolations(newViolationCount)

    console.log(`🚨 Security violation ${newViolationCount}: ${reason}`)

    // Call violation callback
    onViolation?.(reason, newViolationCount)

    if (newViolationCount >= maxViolations) {
      // Max violations reached - terminate interview
      setWarningMessage(`Interview terminated: ${reason}. You have exceeded the allowed number of violations.`)
      setShowWarning(true)
      
      // Terminate after showing warning
      setTimeout(() => {
        onTerminate?.(reason)
      }, 3000)
    } else {
      // Show warning
      const remainingWarnings = maxViolations - newViolationCount
      setWarningMessage(`Warning ${newViolationCount}/${maxViolations}: ${reason}. ${remainingWarnings} warning(s) remaining before interview termination.`)
      setShowWarning(true)
      
      // Hide warning after 5 seconds
      setTimeout(() => {
        setShowWarning(false)
      }, 5000)
    }
  }

  // Security measures to prevent cheating during interview
  useEffect(() => {
    if (!isEnabled) {
      console.log('🔓 Security features disabled - development mode')
      return
    }

    console.log('🔒 Security features enabled - production mode')

    // Disable right-click context menu
    const handleContextMenu = (e: Event) => {
      e.preventDefault()
      return false
    }

    // Disable copy/paste/cut keyboard shortcuts
    const handleKeyDown = (e: KeyboardEvent) => {
      // Disable Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+A, Ctrl+S, F12, etc.
      if (
        (e.ctrlKey && (e.key === 'c' || e.key === 'v' || e.key === 'x' || e.key === 'a' || e.key === 's')) ||
        (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'C' || e.key === 'J')) ||
        e.key === 'F12' ||
        (e.ctrlKey && e.shiftKey && e.key === 'Delete') ||
        (e.ctrlKey && e.key === 'u')
      ) {
        e.preventDefault()
        return false
      }
    }

    // Disable text selection
    const handleSelectStart = (e: Event) => {
      e.preventDefault()
      return false
    }

    // Disable drag
    const handleDragStart = (e: Event) => {
      e.preventDefault()
      return false
    }

    // Add event listeners
    document.addEventListener('contextmenu', handleContextMenu)
    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('selectstart', handleSelectStart)
    document.addEventListener('dragstart', handleDragStart)

    // Cleanup event listeners on unmount
    return () => {
      document.removeEventListener('contextmenu', handleContextMenu)
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('selectstart', handleSelectStart)
      document.removeEventListener('dragstart', handleDragStart)
    }
  }, [isEnabled])

  // Focus monitoring to detect tab switching or window changes
  useEffect(() => {
    if (!isEnabled) {
      console.log('🔓 Focus monitoring disabled - development mode')
      return
    }

    console.log('🔒 Focus monitoring enabled - production mode')

    const handleVisibilityChange = () => {
      if (document.hidden && !isCompleted && !isEndingInterview) {
        handleViolation('Tab switched or window minimized')
      }
    }

    const handleWindowBlur = () => {
      if (!isCompleted && !isEndingInterview) {
        handleViolation('Window lost focus')
      }
    }

    const handleFocusOut = () => {
      if (!isCompleted && !isEndingInterview) {
        // Add a small delay to avoid false positives from clicking UI elements
        setTimeout(() => {
          if (!document.hasFocus()) {
            handleViolation('Browser lost focus')
          }
        }, 100)
      }
    }

    // Add event listeners
    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('blur', handleWindowBlur)
    window.addEventListener('focusout', handleFocusOut)

    // Cleanup event listeners on unmount
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('blur', handleWindowBlur)
      window.removeEventListener('focusout', handleFocusOut)
    }
  }, [isCompleted, isEndingInterview, isEnabled])

  // Security warning display
  if (!showWarning) return null

  const isTerminating = violations >= maxViolations

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className={cn(
        "max-w-lg w-full rounded-xl p-6 shadow-lg",
        isTerminating 
          ? 'bg-red-50 border-2 border-red-200' 
          : 'bg-orange-50 border-2 border-orange-200'
      )}>
        <div className="flex items-start space-x-3">
          <div className={cn(
            "flex-shrink-0 rounded-full p-2",
            isTerminating ? 'bg-red-100' : 'bg-orange-100'
          )}>
            <AlertTriangle className={cn(
              "h-6 w-6",
              isTerminating ? 'text-red-600' : 'text-orange-600'
            )} />
          </div>
          
          <div className="flex-1">
            <h3 className={cn(
              "text-lg font-semibold mb-2",
              isTerminating ? 'text-red-900' : 'text-orange-900'
            )}>
              {isTerminating ? '🚨 INTERVIEW TERMINATED' : '⚠️ SECURITY VIOLATION WARNING'}
            </h3>
            
            <p className={cn(
              "text-sm mb-4",
              isTerminating ? 'text-red-800' : 'text-orange-800'
            )}>
              {warningMessage}
            </p>
            
            {!isTerminating && (
              <div className={cn(
                "text-xs opacity-75",
                isTerminating ? 'text-red-700' : 'text-orange-700'
              )}>
                Please stay focused on the interview. Switching tabs or windows is not allowed.
              </div>
            )}
          </div>

          {!isTerminating && (
            <button
              onClick={() => setShowWarning(false)}
              className="flex-shrink-0 text-orange-400 hover:text-orange-600 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}