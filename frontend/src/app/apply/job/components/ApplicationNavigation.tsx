import { Button } from '@/components/ui/button'
import { Step } from '../types'

interface ApplicationNavigationProps {
  currentStep: number
  steps: Step[]
  onNext: () => void
  onBack: () => void
  isProcessingNext: boolean
}

export function ApplicationNavigation({ 
  currentStep, 
  steps, 
  onNext, 
  onBack, 
  isProcessingNext 
}: ApplicationNavigationProps) {
  // Don't show navigation for the review step (it has its own navigation)
  if (currentStep === steps.length) {
    return null
  }

  return (
    <div className="flex justify-between items-center mt-12 pt-8 border-t border-gray-200">
      <Button 
        variant="secondary" 
        onClick={onBack}
        className="px-6 py-3 text-base bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 hover:text-gray-900 shadow-sm"
      >
        Back
      </Button>
      
      <Button 
        variant="primary" 
        onClick={onNext}
        disabled={isProcessingNext}
        className="px-6 py-3 text-base flex items-center gap-2"
      >
        {isProcessingNext && (
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
        )}
        {isProcessingNext 
          ? 'Processing...' 
          : `Next: ${steps[currentStep]?.title || 'Continue'}`
        }
      </Button>
    </div>
  )
}