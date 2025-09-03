import { CheckCircle2 } from 'lucide-react'
import { Step } from '../types'

interface ProgressIndicatorProps {
  currentStep: number
  totalSteps: number
  steps: Step[]
}

// Progress Indicator Component
export function ProgressIndicator({ currentStep, steps }: ProgressIndicatorProps) {
  return (
    <div className="mb-16">
      <div className="flex items-center justify-between mb-8">
        {steps.map((step, index) => {
          const stepNumber = index + 1
          const isCompleted = stepNumber < currentStep
          const isActive = stepNumber === currentStep
          const isLast = index === steps.length - 1
          
          return (
            <div key={step.id} className="flex items-center flex-1">
              <div className="flex flex-col items-center flex-1">
                <div 
                  className={`w-8 h-8 rounded-full flex items-center justify-center mb-2 ${
                    isCompleted 
                      ? 'bg-green-500' 
                      : isActive 
                        ? 'bg-red-500' 
                        : 'bg-gray-300'
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4 text-success-100" />
                  ) : (
                    <div className="w-3 h-3 bg-white rounded-full"></div>
                  )}
                </div>
                <div 
                  className={`text-sm text-center ${
                    isActive ? 'font-semibold text-gray-900' : 'text-gray-600'
                  }`}
                >
                  {step.title}
                </div>
              </div>
              {!isLast && (
                <div 
                  className={`flex-1 h-0.5 mx-4 ${
                    isCompleted ? 'bg-green-500' : 'bg-gray-300'
                  }`}
                />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}