"use client"

import { useState, useEffect, useRef } from "react"
import { Navigation } from "@/components/navigation"
import { InterviewSidebar } from "./InterviewSidebar"
import { MessageBubble, Message } from "./MessageBubble"
import { AnswerInput } from "./AnswerInput"
import { SecurityMonitor } from "./SecurityMonitor"
import { CheckCircle2 } from "lucide-react"
import { User, Job, UserState } from "@/lib/types"
import { interviewsApi } from "@/lib/api"
import { cn } from "@/lib/utils"

interface InterviewChatProps {
  sessionId?: string // Now optional, will be extracted from API response
  job: Job
  user: User | null
  onComplete?: (reason: 'completed' | 'terminated' | 'time_up') => void
  onError?: (error: string) => void
  className?: string
}

export function InterviewChat({
  sessionId: initialSessionId,
  job,
  user,
  onComplete,
  onError,
  className
}: InterviewChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [isCompleted, setIsCompleted] = useState(false)
  const [isEndingInterview, setIsEndingInterview] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState(300) // Default 5 minutes, will be updated
  const [sessionId, setSessionId] = useState<string | null>(initialSessionId || null)
  const [sessionInfo, setSessionInfo] = useState<{
    questions_asked: number
    questions_answered: number
    time_remaining_seconds: number
  }>({
    questions_asked: 1,
    questions_answered: 0,
    time_remaining_seconds: 300
  })

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const isLoadingRef = useRef<boolean>(false) // Prevent duplicate API calls

  // Security configuration
  const isSecurityEnabled = process.env.NEXT_PUBLIC_SECURITY_ENABLED === 'true'

  // Load interview state on mount
  useEffect(() => {
    loadInterviewState()
  }, [job.id]) // Now depends on job.id instead of sessionId

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadInterviewState = async () => {
    // Prevent duplicate calls
    if (isLoadingRef.current) {
      console.log('Already loading interview state, skipping duplicate call')
      return
    }
    
    isLoadingRef.current = true
    try {
      console.log('Loading interview state for job:', job.id)
      
      // Use new unified API endpoint with jobId parameter
      const { data, error } = await interviewsApi.getCurrentInterviewState(job.id)
      
      if (error) {
        console.error('Failed to load interview state:', error)
        if (error.includes('not found')) {
          onError?.('No interview found for this job. Please start a new interview.')
        } else if (error.includes('expired')) {
          onError?.('Interview session has expired.')
        } else {
          onError?.(error)
        }
        return
      }

      console.log('Interview state loaded:', data)
      
      // Extract session_id from response if not already set
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id)
        console.log('Session ID set from API response:', data.session_id)
      }
      
      // Load conversation history
      const conversationHistory = data.conversation_history || []
      const historyMessages: Message[] = conversationHistory.map((pair: any, index: number) => {
        const messages: Message[] = []
        
        if (pair.question) {
          messages.push({
            id: `question-${index}`,
            type: 'question',
            content: pair.question.text,
            timestamp: pair.question.asked_at || new Date().toISOString(),
            metadata: {
              type: pair.question.type,
              focus_area: pair.question.focus_area,
              difficulty: pair.question.difficulty,
              question_number: pair.question.number
            }
          })
        }
        
        if (pair.response) {
          messages.push({
            id: `answer-${index}`,
            type: 'answer',
            content: pair.response.text,
            timestamp: pair.response.responded_at || new Date().toISOString()
          })
        }
        
        return messages
      }).flat()
      
      // Add current question if not answered yet
      if (data.current_question && data.status === 'active') {
        const currentQuestionMessage: Message = {
          id: `current-question-${Date.now()}`,
          type: 'question',
          content: data.current_question,
          timestamp: new Date().toISOString(),
          metadata: data.question_metadata || {}
        }
        historyMessages.push(currentQuestionMessage)
      }
      
      setMessages(historyMessages)
      
      // Update session info and timing
      setSessionInfo({
        questions_asked: data.session_info?.questions_asked || 1,
        questions_answered: data.session_info?.questions_answered || 0,
        time_remaining_seconds: data.session_info?.time_remaining_seconds || 300
      })
      
      setTimeRemaining(data.session_info?.time_remaining_seconds || 300)
      
      // Check if interview is already completed
      if (data.status !== 'active') {
        setIsCompleted(true)
        if (data.status === 'completed') {
          onComplete?.('completed')
        } else if (data.status === 'terminated') {
          onComplete?.('terminated')
        }
      }
      
    } catch (error) {
      console.error('Error loading interview state:', error)
      onError?.('Failed to load interview state. Please try again.')
    } finally {
      isLoadingRef.current = false
    }
  }

  const submitAnswer = async () => {
    if (!currentAnswer.trim() || isProcessing || isCompleted) return

    const answerToSubmit = currentAnswer
    
    // Add user answer to messages immediately
    const userMessage: Message = {
      id: `answer-${Date.now()}`,
      type: 'answer',
      content: answerToSubmit,
      timestamp: new Date().toISOString()
    }
    
    // Add processing message
    const processingMessage: Message = {
      id: `processing-${Date.now()}`,
      type: 'processing',
      content: 'Analyzing your answer...',
      timestamp: new Date().toISOString()
    }
    
    setMessages(prev => [...prev, userMessage, processingMessage])
    setCurrentAnswer('')
    setIsProcessing(true)

    try {
      // Create abort controller for this request
      const abortController = new AbortController()
      abortControllerRef.current = abortController

      const response = await fetch(`/api/interviews/${sessionId}/answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        credentials: 'include', // Use cookies for auth like other endpoints
        body: JSON.stringify({ answer: answerToSubmit }),
        signal: abortController.signal
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to submit answer')
      }

      // Handle Server-Sent Events
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('Failed to get response stream')
      }

      let buffer = ''
      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        
        // Process complete SSE messages
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const eventData = JSON.parse(line.slice(6))
              
              if (eventData.type === 'processing') {
                // Update processing message
                setMessages(prev => {
                  const withoutProcessing = prev.filter(m => m.type !== 'processing')
                  return [...withoutProcessing, {
                    id: `processing-${Date.now()}`,
                    type: 'processing',
                    content: eventData.message || 'Analyzing your answer...',
                    timestamp: eventData.timestamp || new Date().toISOString()
                  }]
                })
              } else if (eventData.type === 'question') {
                // Remove processing message and add new question
                setMessages(prev => {
                  const withoutProcessing = prev.filter(m => m.type !== 'processing')
                  return [...withoutProcessing, {
                    id: `question-${Date.now()}`,
                    type: 'question',
                    content: eventData.content,
                    timestamp: eventData.timestamp || new Date().toISOString(),
                    metadata: eventData.metadata || {}
                  }]
                })

                // Update session info
                if (eventData.session_info) {
                  setSessionInfo({
                    questions_asked: eventData.session_info.questions_asked || 1,
                    questions_answered: eventData.session_info.questions_answered || 0,
                    time_remaining_seconds: eventData.session_info.time_remaining_seconds || timeRemaining
                  })
                  setTimeRemaining(eventData.session_info.time_remaining_seconds || timeRemaining)
                }
              } else if (eventData.type === 'interview_complete') {
                // Remove processing message and handle completion
                setMessages(prev => prev.filter(m => m.type !== 'processing'))
                setIsCompleted(true)
                
                const completionReason = eventData.completion_reason || eventData.status
                if (completionReason === 'terminated') {
                  onComplete?.('terminated')
                } else {
                  onComplete?.('completed')
                }
              } else if (eventData.type === 'error') {
                // Remove processing message and show error
                setMessages(prev => {
                  const withoutProcessing = prev.filter(m => m.type !== 'processing')
                  return [...withoutProcessing, {
                    id: `error-${Date.now()}`,
                    type: 'error',
                    content: eventData.message || 'An error occurred',
                    timestamp: new Date().toISOString()
                  }]
                })
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e)
            }
          }
        }
      }
    } catch (error: any) {
      console.error('Error submitting answer:', error)
      
      // Remove processing message
      setMessages(prev => prev.filter(m => m.type !== 'processing'))
      
      if (error.name !== 'AbortError') {
        onError?.(error.message || 'Failed to submit answer')
      }
    } finally {
      setIsProcessing(false)
      abortControllerRef.current = null
    }
  }

  const handleEndInterview = async () => {
    if (isEndingInterview) return
    
    setIsEndingInterview(true)
    
    try {
      const { error } = await interviewsApi.endInterview(sessionId, 'user_requested')
      
      if (error) {
        throw new Error(error)
      }

      setIsCompleted(true)
      onComplete?.('completed')
    } catch (error: any) {
      console.error('Error ending interview:', error)
      onError?.(error.message || 'Failed to end interview')
    } finally {
      setIsEndingInterview(false)
    }
  }

  const handleTimeExpired = () => {
    setIsCompleted(true)
    onComplete?.('time_up')
  }

  const handleSecurityViolation = (reason: string, count: number) => {
    console.log(`Security violation ${count}: ${reason}`)
    // Violations are handled by SecurityMonitor component
  }

  const handleSecurityTermination = async (reason: string) => {
    console.log(`Interview terminated due to security violation: ${reason}`)
    setIsEndingInterview(true)
    
    try {
      await interviewsApi.endInterview(sessionId, 'security_violation')
    } catch (error) {
      console.error('Failed to end interview due to security violation:', error)
    }
    
    setIsCompleted(true)
    onComplete?.('terminated')
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  // Determine user state for Navigation component
  const userState: UserState = user?.hasResume ? "has-resume" : user ? "no-resume" : "guest"

  return (
    <div className={cn(
      "min-h-screen bg-gray-50 flex flex-col",
      isSecurityEnabled ? 'select-none' : '',
      className
    )} 
    style={isSecurityEnabled ? {
      userSelect: 'none', 
      WebkitUserSelect: 'none', 
      MozUserSelect: 'none', 
      msUserSelect: 'none'
    } : {}}>
      
      {/* Main Navigation Header */}
      <Navigation
        userState={userState}
        user={user}
        theme="light"
        className="sticky top-0 z-50"
      />

      {/* Main Content Area - Fixed Sidebar + Scrollable Chat */}
      <div className="flex-1 flex">
        
        {/* Left Sidebar - Fixed Position */}
        <div className="w-80 flex-shrink-0 sticky top-16 self-start">
          <InterviewSidebar
            job={job}
            user={user}
            timeRemaining={timeRemaining}
            questionsAsked={sessionInfo.questions_asked}
            questionsAnswered={sessionInfo.questions_answered}
            isEndingInterview={isEndingInterview}
            isSecurityEnabled={isSecurityEnabled}
            onEndInterview={handleEndInterview}
            onTimeUpdate={setTimeRemaining}
            onTimeExpired={handleTimeExpired}
            className="h-[calc(100vh-4rem)] overflow-y-auto"
          />
        </div>

        {/* Main Chat Area - Scrollable */}
        <div className="flex-1 flex flex-col min-h-0">
          
          {/* Messages Area - This will scroll independently */}
          <div className="flex-1 overflow-y-auto bg-white">
            <div className="max-w-4xl mx-auto px-6 py-8">
              <div className="space-y-6">
                {messages.filter(message => {
                  // Filter out empty or invalid messages
                  const isValid = message.content && message.content.trim() !== ''
                  if (!isValid) {
                    console.log('Filtering out invalid message:', message)
                  }
                  return isValid
                }).map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))}

                <div ref={messagesEndRef} />
              </div>
            </div>
          </div>

          {/* Answer Input - Fixed at bottom of chat area */}
          {!isCompleted && (
            <div className="flex-shrink-0 bg-white border-t border-gray-200">
              <AnswerInput
                value={currentAnswer}
                onChange={setCurrentAnswer}
                onSubmit={submitAnswer}
                isProcessing={isProcessing}
                isCompleted={isCompleted}
                isSecurityEnabled={isSecurityEnabled}
                disabled={isEndingInterview}
              />
            </div>
          )}

          {/* Completion State */}
          {isCompleted && (
            <div className="flex-shrink-0 bg-green-50 border-t border-green-200">
              <div className="max-w-4xl mx-auto px-6 py-8 text-center">
                <CheckCircle2 className="h-12 w-12 text-green-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-green-900 mb-2">Interview Completed!</h3>
                <p className="text-green-700 mb-4">Thank you for participating. Your responses have been recorded.</p>
              </div>
            </div>
          )}
          
        </div>
      </div>

      {/* Security Monitor */}
      <SecurityMonitor
        isEnabled={isSecurityEnabled}
        isCompleted={isCompleted}
        isEndingInterview={isEndingInterview}
        onViolation={handleSecurityViolation}
        onTerminate={handleSecurityTermination}
        maxViolations={3}
      />
    </div>
  )
}