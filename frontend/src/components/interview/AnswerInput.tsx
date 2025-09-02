"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Mic, MicOff, Send } from "lucide-react"
import { cn } from "@/lib/utils"

interface AnswerInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  isProcessing?: boolean
  isCompleted?: boolean
  placeholder?: string
  disabled?: boolean
  className?: string
  isSecurityEnabled?: boolean
}

export function AnswerInput({
  value,
  onChange,
  onSubmit,
  isProcessing = false,
  isCompleted = false,
  placeholder = "Type your answer here... (Press Enter to submit, Shift+Enter for new line)",
  disabled = false,
  className,
  isSecurityEnabled = false
}: AnswerInputProps) {
  const [isListening, setIsListening] = useState(false)
  const [recognition, setRecognition] = useState<SpeechRecognition | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

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
        
        recognition.onresult = (event: SpeechRecognitionEvent) => {
          let transcript = ''
          for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript
          }
          onChange(transcript)
        }
        
        recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
          console.error('Speech recognition error:', event.error)
          setIsListening(false)
        }
        
        recognition.onend = () => {
          setIsListening(false)
        }
        
        setRecognition(recognition)
      }
    }
  }, [onChange])

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = 'auto'
      
      // Calculate new height based on content
      const newHeight = Math.min(Math.max(textarea.scrollHeight, 60), 200) // Min 60px, Max 200px
      textarea.style.height = `${newHeight}px`
    }
  }, [value])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleSubmit = () => {
    if (!value.trim() || isProcessing || isCompleted || disabled) return
    onSubmit()
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

  const isInputDisabled = isProcessing || isCompleted || disabled

  return (
    <div className={cn("bg-white border-t border-gray-200 shadow-lg", className)}>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-start gap-3 w-full">
          {/* Security Mode Indicator */}
          <div className={`flex-shrink-0 inline-flex items-center px-2 py-1 rounded text-xs font-medium mt-3 ${
            isSecurityEnabled 
              ? 'bg-green-100 text-green-800' 
              : 'bg-yellow-100 text-yellow-800'
          }`}>
            {isSecurityEnabled ? '🔒 Secure' : '🔓 Dev'}
          </div>
          
          <div className="relative flex-1">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyPress={handleKeyPress}
            onCopy={isSecurityEnabled ? (e) => e.preventDefault() : undefined}
            onCut={isSecurityEnabled ? (e) => e.preventDefault() : undefined}
            onPaste={isSecurityEnabled ? (e) => e.preventDefault() : undefined}
            onContextMenu={isSecurityEnabled ? (e) => e.preventDefault() : undefined}
            placeholder={placeholder}
            disabled={isInputDisabled}
            className={cn(
              "w-full pl-4 pr-32 py-3 border border-gray-300 rounded-2xl",
              "focus:ring-2 focus:ring-red-500 focus:border-transparent resize-none",
              "disabled:bg-gray-100 disabled:cursor-not-allowed",
              "text-gray-900 placeholder-gray-500 transition-all duration-200",
              "min-h-[60px] max-h-[200px]",
              isSecurityEnabled ? "select-none" : "select-text"
            )}
            style={{
              userSelect: isSecurityEnabled ? 'none' : 'text',
              WebkitUserSelect: isSecurityEnabled ? 'none' : 'text',
              MozUserSelect: isSecurityEnabled ? 'none' : 'text',
              msUserSelect: isSecurityEnabled ? 'none' : 'text',
              height: '60px' // Initial height
            }}
          />
          
          {/* Voice input button */}
          <Button
            type="button"
            onClick={toggleVoiceInput}
            disabled={isInputDisabled}
            variant="ghost"
            size="sm"
            className={cn(
              "absolute right-16 top-3 h-10 w-10 p-0 rounded-lg transition-colors",
              isListening 
                ? 'bg-red-100 text-red-600 hover:bg-red-200' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
            title={isListening ? 'Stop voice input' : 'Start voice input'}
          >
            {isListening ? (
              <MicOff className="h-5 w-5" />
            ) : (
              <Mic className="h-5 w-5" />
            )}
          </Button>

          {/* Submit button */}
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={isInputDisabled || !value.trim()}
            className={cn(
              "absolute right-3 top-3 h-10 w-10 p-0 rounded-lg",
              "bg-red-600 hover:bg-red-700 text-white",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
            title="Submit answer"
          >
            <Send className="h-4 w-4" />
          </Button>
          </div>
        </div>
        
        {/* Processing indicator */}
        {isProcessing && (
          <div className="mt-3 text-center">
            <div className="inline-flex items-center space-x-2 text-sm text-gray-600">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
              <span>Processing your answer...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}