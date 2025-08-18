'use client'

import { useState, useEffect, useRef, Suspense } from 'react'
import { 
  ClockIcon,
  UserCircleIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  MicrophoneIcon,
  StopIcon
} from '@heroicons/react/24/outline'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
declare const window: any

interface Message {
  id: string
  type: 'question' | 'answer' | 'processing' | 'evaluation' | 'complete'
  content: string
  timestamp: string
  metadata?: {
    type: string
    focus_area: string
    difficulty: string
    question_number: number
  }
}

function InterviewContent() {
  const router = useRouter()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isResumedSession, setIsResumedSession] = useState(false)
  
  useEffect(() => {
    // Get session ID and resumed flag from URL on client side
    const params = new URLSearchParams(window.location.search)
    setSessionId(params.get('session'))
    setIsResumedSession(params.get('resumed') === 'true')
  }, [])
  
  const [messages, setMessages] = useState<Message[]>([])
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [isCompleted, setIsCompleted] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState(300) // will be updated from session data
  const [sessionInfo, setSessionInfo] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState<string>('')
  const [successMessage, setSuccessMessage] = useState<string>('')
  const [isEndingInterview, setIsEndingInterview] = useState(false)
  const [isListening, setIsListening] = useState(false)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [recognition, setRecognition] = useState<any>(null)
  
  // Focus monitoring for security
  const [focusViolations, setFocusViolations] = useState(0)
  const [showFocusWarning, setShowFocusWarning] = useState(false)
  const [warningMessage, setWarningMessage] = useState('')
  const focusViolationsRef = useRef(0)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const eventSourceRef = useRef<EventSource | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Security configuration - determined at build time
  const isSecurityEnabled = process.env.NEXT_PUBLIC_SECURITY_ENABLED === 'true'

  // Keep ref in sync with state
  useEffect(() => {
    focusViolationsRef.current = focusViolations
  }, [focusViolations])

  useEffect(() => {
    // If no session ID in URL, check if user has an existing active session
    if (!sessionId) {
      checkExistingSession()
      return
    }
    
    // If we have a session ID from URL, load the first question
    console.log('🔍 DEBUG: Session ID from URL, loading first question')
    loadInterviewState()
    
    // Start timer countdown
    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          setIsCompleted(true)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [sessionId, router])

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition()
        
        recognition.continuous = true
        recognition.interimResults = true
        recognition.lang = 'en-US'
        
        recognition.onstart = () => {
          setIsListening(true)
        }
        
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        recognition.onresult = (event: any) => {
          let transcript = ''
          for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript
          }
          setCurrentAnswer(transcript)
        }
        
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        recognition.onerror = (event: any) => {
          console.error('Speech recognition error:', event.error)
          setIsListening(false)
        }
        
        recognition.onend = () => {
          setIsListening(false)
        }
        
        setRecognition(recognition)
      }
    }
  }, [])

  // Security measures to prevent cheating during interview
  useEffect(() => {
    if (!isSecurityEnabled) {
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
  }, [isSecurityEnabled])

  // Focus monitoring to detect tab switching or window changes
  useEffect(() => {
    if (!isSecurityEnabled) {
      console.log('🔓 Focus monitoring disabled - development mode')
      return
    }

    console.log('🔒 Focus monitoring enabled - production mode')

    const handleVisibilityChange = () => {
      if (document.hidden && !isCompleted && !isEndingInterview) {
        handleFocusViolation('Tab switched or window minimized')
      }
    }

    const handleWindowBlur = () => {
      if (!isCompleted && !isEndingInterview) {
        handleFocusViolation('Window lost focus')
      }
    }

    const handleFocusOut = () => {
      if (!isCompleted && !isEndingInterview) {
        // Add a small delay to avoid false positives from clicking UI elements
        setTimeout(() => {
          if (!document.hasFocus()) {
            handleFocusViolation('Browser lost focus')
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
  }, [isCompleted, isEndingInterview, isSecurityEnabled])

  const handleFocusViolation = (reason: string) => {
    // Increment the ref counter first
    focusViolationsRef.current += 1
    const newViolationCount = focusViolationsRef.current
    
    // Update state to trigger re-render
    setFocusViolations(newViolationCount)

    console.log(`🚨 Focus violation ${newViolationCount}: ${reason}`)

    if (newViolationCount >= 3) {
      // Third violation - end interview
      setWarningMessage(`Interview terminated: ${reason}. You have exceeded the allowed number of focus violations.`)
      setShowFocusWarning(true)
      
      // End interview after showing warning
      setTimeout(() => {
        endInterviewDueToViolation()
      }, 3000)
    } else {
      // Show warning
      const remainingWarnings = 3 - newViolationCount
      setWarningMessage(`Warning ${newViolationCount}/3: ${reason}. ${remainingWarnings} warning(s) remaining before interview termination.`)
      setShowFocusWarning(true)
      
      // Hide warning after 5 seconds
      setTimeout(() => {
        setShowFocusWarning(false)
      }, 5000)
    }
  }

  const endInterviewDueToViolation = async () => {
    setIsEndingInterview(true)
    try {
      await fetch('/api/interviews/end', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          reason: 'security_violation',
          violation_type: 'focus_violations',
          violation_count: focusViolationsRef.current
        })
      })
      
      // Redirect to dashboard after brief delay
      setTimeout(() => {
        router.push('/dashboard?message=Interview terminated due to security violations')
      }, 2000)
    } catch (error) {
      console.error('Failed to end interview:', error)
      router.push('/dashboard?message=Interview terminated due to security violations')
    }
  }

  const loadInterviewState = async () => {
    try {
      console.log('🔍 DEBUG: Loading current interview state')
      
      // Get the current question from the session
      const response = await fetch('/api/interviews/current', {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        console.error('🔍 DEBUG: Failed to load interview state:', response.status)
        let errorMessage = ''
        
        if (response.status === 404) {
          errorMessage = 'No active interview session found. Please start a new interview.'
        } else if (response.status === 409) {
          errorMessage = 'Interview already completed for this role. You cannot retake this interview.'
        } else if (response.status === 410) {
          errorMessage = 'Interview session has expired. Please start a new interview.'
        } else {
          const errorData = await response.json().catch(() => ({}))
          errorMessage = errorData.detail || 'Failed to load interview state'
        }
        
        setError(errorMessage)
        setTimeout(() => router.push('/dashboard'), 3000)
        return
      }

      const data = await response.json()
      console.log('🔍 DEBUG: Current interview data:', data)
      
      // Handle resume vs new interview responses
      if (data.resumed) {
        console.log('🔍 DEBUG: Resuming interview with conversation history')
        
        // Load conversation history
        const conversationHistory = data.conversation_history || []
        const historyMessages: Message[] = conversationHistory.map((msg: Record<string, unknown>, index: number) => ({
          id: `history-${index}`,
          type: (msg.type as string) || (msg.role === 'assistant' ? 'question' : 'answer'),
          content: msg.content as string,
          timestamp: (msg.timestamp as string) || new Date().toISOString(),
          metadata: (msg.metadata as Record<string, unknown>) || {}
        }))
        
        // Add current question
        if (data.current_question) {
          const currentQuestionMessage: Message = {
            id: Date.now().toString(),
            type: 'question',
            content: data.current_question,
            timestamp: new Date().toISOString(),
            metadata: data.question_metadata || {}
          }
          historyMessages.push(currentQuestionMessage)
        }
        
        setMessages(historyMessages)
        setError('') // Clear any previous errors
        
        // Show resume message
        if (data.message) {
          setSuccessMessage(data.message) // Use success state to show the resume message
          setTimeout(() => setSuccessMessage(''), 5000) // Clear after 5 seconds
        }
      } else {
        // New interview - just show the current question
        if (data.current_question) {
          const questionMessage: Message = {
            id: Date.now().toString(),
            type: 'question',
            content: data.current_question,
            timestamp: new Date().toISOString(),
            metadata: data.question_metadata || {}
          }
          
          setMessages([questionMessage])
          console.log('🔍 DEBUG: Set initial question message:', questionMessage)
        }
      }
      
      // Use remaining time from server response if available, otherwise use full duration
      const remainingSeconds = data.time_remaining_seconds
      if (remainingSeconds !== undefined) {
        setTimeRemaining(remainingSeconds)
        console.log('🔍 DEBUG: Set timer from remaining time:', remainingSeconds, 'seconds')
      } else {
        // Fallback to full duration for backward compatibility
        const durationInSeconds = (data.duration_minutes || 30) * 60
        setTimeRemaining(durationInSeconds)
        console.log('🔍 DEBUG: Set timer to full duration:', durationInSeconds, 'seconds')
        console.log('🔍 DEBUG: Set timer duration:', data.duration_minutes, 'minutes =', durationInSeconds, 'seconds')
      }
      
      setSessionInfo({
        session_id: data.session_id,
        role_title: data.role_title,
        questions_asked: data.questions_asked,
        total_questions: data.total_questions,
        total_answers: data.total_answers,
        expires_at: data.expires_at,
        started_at: data.started_at,
        duration_minutes: data.duration_minutes
      })
      
      console.log('🔍 DEBUG: Interview state loaded successfully')
    } catch (error) {
      console.error('🔍 DEBUG: Error loading interview state:', error)
      // If there's an error, redirect to dashboard
      router.push('/dashboard')
    }
  }

  const checkExistingSession = async () => {
    try {
      console.log('🔍 DEBUG: Checking for existing active interview session')
      
      const response = await fetch('/api/interviews/status', {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        console.log('🔍 DEBUG: Interview status response:', data)
        
        if (data.has_active_session) {
          // User has an active session, set the session ID and continue
          setSessionId(data.session_id || 'active')
          console.log('🔍 DEBUG: Found existing active session:', data.session_id)
          // Load the current interview state
          loadInterviewState()
          return
        }
      }

      // No active session found, redirect to dashboard
      console.log('🔍 DEBUG: No active session found, redirecting to dashboard')
      router.push('/dashboard')
    } catch (error) {
      console.error('🔍 DEBUG: Error checking existing session:', error)
      router.push('/dashboard')
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Auto-resize textarea like ChatGPT
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = 'auto'
      
      // Calculate new height based on content
      const newHeight = Math.min(Math.max(textarea.scrollHeight, 60), 200) // Min 60px, Max 200px
      textarea.style.height = `${newHeight}px`
    }
  }, [currentAnswer])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const toggleVoiceInput = () => {
    if (!recognition) {
      alert('Speech recognition is not supported in your browser')
      return
    }
    
    if (isListening) {
      recognition.stop()
    } else {
      recognition.start()
    }
  }

  const submitAnswer = async () => {
    if (!currentAnswer.trim() || isProcessing || isCompleted) return

    // Store the answer before clearing it
    const answerToSubmit = currentAnswer

    // Add user answer to messages
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'answer',
      content: answerToSubmit,
      timestamp: new Date().toISOString()
    }
    
    // Add processing message
    const processingMessage: Message = {
      id: 'processing-' + Date.now(),
      type: 'processing',
      content: 'Analyzing your answer...',
      timestamp: new Date().toISOString()
    }
    
    setMessages(prev => [...prev, userMessage, processingMessage])
    setCurrentAnswer('')
    setIsProcessing(true)
    setError('')
    setSuccessMessage('')

    try {
      // Close any existing EventSource
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }

      // Create new EventSource for streaming response
      const response = await fetch('/api/interviews/answer', {
        method: 'POST',
        credentials: 'include', // Use session cookie instead of localStorage token
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify({ answer: answerToSubmit })
      })

      if (!response.ok) {
        const errorData = await response.json()
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
              
              const message: Message = {
                id: Date.now().toString() + Math.random(),
                type: eventData.type,
                content: eventData.content || eventData.message,
                timestamp: eventData.timestamp || new Date().toISOString(),
                metadata: eventData.metadata
              }

              // Replace processing message with new content, or add new message
              if (eventData.type === 'processing') {
                // Replace existing processing message
                setMessages(prev => {
                  const withoutProcessing = prev.filter(m => m.type !== 'processing')
                  return [...withoutProcessing, message]
                })
              } else {
                // Remove processing message and add new message
                setMessages(prev => {
                  const withoutProcessing = prev.filter(m => m.type !== 'processing')
                  return [...withoutProcessing, message]
                })
              }

              // Update session info if provided
              if (eventData.session_info) {
                setSessionInfo(eventData.session_info)
              }

              // Check if interview is complete
              if (eventData.type === 'interview_complete') {
                setIsCompleted(true)
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e)
            }
          }
        }
      }
    } catch (error) {
      console.error('Error submitting answer:', error)
      setError(error instanceof Error ? error.message : 'Failed to submit answer')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submitAnswer()
    }
  }

  const endInterview = async () => {
    if (isEndingInterview) return
    
    try {
      setIsEndingInterview(true)
      const response = await fetch('/api/interviews/end', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        setIsCompleted(true)
        router.push('/dashboard?message=interview_ended')
      } else {
        const errorData = await response.json().catch(() => ({}))
        setError(errorData.detail || 'Failed to end interview')
      }
    } catch (error) {
      console.error('Error ending interview:', error)
      setError('Failed to end interview')
    } finally {
      setIsEndingInterview(false)
    }
  }


  const handleLogout = async () => {
    try {
      await fetch('/logout', {
        method: 'POST',
        credentials: 'include'
      })
    } catch (error) {
      console.error('Logout error:', error)
    }
    window.location.href = '/'
  }


  return (
    <div 
      className={`min-h-screen bg-gray-50 flex flex-col ${isSecurityEnabled ? 'select-none' : ''}`} 
      style={isSecurityEnabled ? {userSelect: 'none', WebkitUserSelect: 'none', MozUserSelect: 'none', msUserSelect: 'none'} : {}}
    >
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link href="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-2 rounded-lg">
                <UserCircleIcon className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">
                  Interview
                  {isResumedSession && (
                    <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                      Resumed
                    </span>
                  )}
                </h1>
                {sessionInfo && (
                  <p className="text-sm text-gray-500">
                    Question {(sessionInfo.total_questions as number) || 1} • {(sessionInfo.total_answers as number) || 0} answered
                  </p>
                )}
              </div>
            </Link>

            <div className="flex items-center space-x-4">
              {/* Timer */}
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-lg ${
                timeRemaining < 60 ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'
              }`}>
                <ClockIcon className="h-4 w-4" />
                <span className="font-semibold">{formatTime(timeRemaining)}</span>
              </div>

              <button
                onClick={() => {
                  if (window.confirm('Are you sure you want to end the interview? This action cannot be undone and your responses will be submitted for evaluation.')) {
                    endInterview()
                  }
                }}
                disabled={isEndingInterview || isCompleted}
                className={`font-medium transition-colors ${
                  isEndingInterview || isCompleted
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-red-600 hover:text-red-900'
                }`}
              >
                {isEndingInterview ? 'Ending...' : 'End Interview'}
              </button>
              
              <button
                onClick={handleLogout}
                className="text-gray-600 hover:text-gray-900 font-medium"
              >
                Logout
              </button>
              
              {/* Security Mode Indicator */}
              <div className={`px-2 py-1 rounded text-xs font-medium ${
                isSecurityEnabled 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {isSecurityEnabled ? '🔒 Secure' : '🔓 Dev'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="space-y-6">
            {messages.filter(message => {
              const isValid = message.type !== 'evaluation' && 
                             message.content && 
                             message.content.trim() !== '';
              if (!isValid) {
                console.log('🔍 DEBUG: Filtering out message:', message);
              }
              return isValid;
            }).map((message) => (
              <div key={message.id} className={`flex ${message.type === 'answer' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-3xl ${
                  message.type === 'answer' 
                    ? 'bg-blue-600 text-white' 
                    : message.type === 'processing'
                    ? 'bg-yellow-50 text-yellow-800 border border-yellow-200'
                    : message.type === 'evaluation'
                    ? 'bg-green-50 text-green-800 border border-green-200'
                    : 'bg-white text-gray-900 border border-gray-200'
                } rounded-2xl px-6 py-4 shadow-sm`}>
                  
                  {message.type === 'question' && message.metadata && (
                    <div className="flex items-center space-x-2 mb-3 text-sm">
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                        {message.metadata.type}
                      </span>
                      <span className="text-gray-500">•</span>
                      <span className="text-gray-600">{message.metadata.focus_area}</span>
                    </div>
                  )}
                  
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  
                  {message.type === 'processing' && (
                    <div className="flex items-center space-x-2 mt-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600"></div>
                      <span className="text-sm">AI is analyzing your response...</span>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {error && (
              <div className="flex justify-center">
                <div className="max-w-md bg-red-50 text-red-800 border border-red-200 rounded-2xl px-6 py-4 shadow-sm flex items-center space-x-2">
                  <ExclamationCircleIcon className="h-5 w-5 text-red-600" />
                  <span>{error}</span>
                </div>
              </div>
            )}

            {successMessage && (
              <div className="flex justify-center">
                <div className="max-w-md bg-blue-50 text-blue-800 border border-blue-200 rounded-2xl px-6 py-4 shadow-sm flex items-center space-x-2">
                  <CheckCircleIcon className="h-5 w-5 text-blue-600" />
                  <span>{successMessage}</span>
                </div>
              </div>
            )}

            {showFocusWarning && (
              <div className="flex justify-center">
                <div className={`max-w-lg ${focusViolations >= 3 ? 'bg-red-50 text-red-800 border-red-200' : 'bg-yellow-50 text-yellow-800 border-yellow-200'} border rounded-2xl px-6 py-4 shadow-sm`}>
                  <div className="flex items-start space-x-2">
                    <ExclamationCircleIcon className={`h-5 w-5 mt-0.5 ${focusViolations >= 3 ? 'text-red-600' : 'text-yellow-600'}`} />
                    <div>
                      <div className="font-semibold text-sm mb-1">
                        {focusViolations >= 3 ? '🚨 INTERVIEW TERMINATED' : '⚠️ FOCUS VIOLATION WARNING'}
                      </div>
                      <div className="text-sm">{warningMessage}</div>
                      {focusViolations < 3 && (
                        <div className="text-xs mt-2 opacity-75">
                          Please stay focused on the interview. Switching tabs or windows is not allowed.
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>

      {/* Answer Input */}
      {!isCompleted && (
        <div className="bg-white border-t border-gray-200 shadow-lg">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="relative w-full">
                <textarea
                  ref={textareaRef}
                  value={currentAnswer}
                  onChange={(e) => setCurrentAnswer(e.target.value)}
                  onKeyPress={handleKeyPress}
                  onCopy={isSecurityEnabled ? (e) => e.preventDefault() : undefined}
                  onCut={isSecurityEnabled ? (e) => e.preventDefault() : undefined}
                  onPaste={isSecurityEnabled ? (e) => e.preventDefault() : undefined}
                  onContextMenu={isSecurityEnabled ? (e) => e.preventDefault() : undefined}
                  placeholder="Type your answer here... (Press Enter to submit, Shift+Enter for new line)"
                  disabled={isProcessing || isCompleted}
                  className="w-full pl-4 pr-12 py-3 border border-gray-300 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none disabled:bg-gray-100 disabled:cursor-not-allowed text-gray-900 placeholder-gray-500 select-text transition-all duration-200 min-h-[60px] max-h-[200px]"
                  style={{
                    userSelect: 'text', 
                    WebkitUserSelect: 'text', 
                    MozUserSelect: 'text', 
                    msUserSelect: 'text',
                    height: '60px' // Initial height
                  }}
                />
                <button
                  onClick={toggleVoiceInput}
                  disabled={isProcessing || isCompleted}
                  className={`absolute right-3 top-3 p-2 rounded-lg transition-colors ${
                    isListening 
                      ? 'bg-red-100 text-red-600 hover:bg-red-200' 
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                  title={isListening ? 'Stop voice input' : 'Start voice input'}
                >
                  {isListening ? (
                    <StopIcon className="h-5 w-5" />
                  ) : (
                    <MicrophoneIcon className="h-5 w-5" />
                  )}
                </button>
            </div>
          </div>
        </div>
      )}

      {/* Completion State */}
      {isCompleted && (
        <div className="bg-green-50 border-t border-green-200">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 text-center">
            <CheckCircleIcon className="h-12 w-12 text-green-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-green-900 mb-2">Interview Completed!</h3>
            <p className="text-green-700 mb-4">Thank you for participating. Your responses have been recorded.</p>
            <button
              onClick={() => router.push('/dashboard')}
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors"
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function InterviewPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>}>
      <InterviewContent />
    </Suspense>
  )
}