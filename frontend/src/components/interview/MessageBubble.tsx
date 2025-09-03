"use client"

import { cn } from "@/lib/utils"

export interface Message {
  id: string
  type: 'question' | 'answer' | 'processing' | 'evaluation' | 'complete' | 'error'
  content: string
  timestamp: string
  metadata?: {
    type?: string
    focus_area?: string
    difficulty?: string
    question_number?: number
  }
}

interface MessageBubbleProps {
  message: Message
  className?: string
}

export function MessageBubble({ message, className }: MessageBubbleProps) {
  const isUserMessage = message.type === 'answer'
  const isProcessing = message.type === 'processing'
  const isError = message.type === 'error'

  const getBubbleStyles = () => {
    if (isUserMessage) {
      return "bg-blue-100 text-blue-900 ml-auto"
    }
    if (isProcessing) {
      return "bg-orange-50 text-orange-800 border border-orange-200"
    }
    if (isError) {
      return "bg-red-50 text-red-800 border border-red-200"
    }
    return "bg-white text-gray-900 border border-gray-200"
  }

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    } catch {
      return ''
    }
  }

  return (
    <div className={cn("flex", isUserMessage ? "justify-end" : "justify-start", className)}>
      <div className={cn(
        "max-w-3xl rounded-2xl px-6 py-4 shadow-sm",
        getBubbleStyles()
      )}>
        {/* Question metadata */}
        {message.type === 'question' && message.metadata && (
          <div className="flex items-center space-x-2 mb-3 text-sm">
            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
              {message.metadata.type || 'Question'}
            </span>
            {message.metadata.focus_area && (
              <>
                <span className="text-gray-400">•</span>
                <span className="text-gray-600">{message.metadata.focus_area}</span>
              </>
            )}
            {message.metadata.difficulty && (
              <>
                <span className="text-gray-400">•</span>
                <span className="text-gray-500 capitalize">{message.metadata.difficulty}</span>
              </>
            )}
          </div>
        )}
        
        {/* Message content */}
        <div className="whitespace-pre-wrap leading-relaxed">
          {message.content}
        </div>
        
        {/* Processing indicator */}
        {isProcessing && (
          <div className="flex items-center space-x-2 mt-3">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-orange-600"></div>
            <span className="text-sm">AI is analyzing your response...</span>
          </div>
        )}
        
        {/* Timestamp */}
        <div className={cn(
          "text-xs mt-2 opacity-60",
          isUserMessage ? "text-blue-700" : "text-gray-500"
        )}>
          {formatTimestamp(message.timestamp)}
        </div>
      </div>
    </div>
  )
}