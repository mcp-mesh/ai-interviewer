"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { ToastContainer, useToast } from '@/components/common'
import Link from 'next/link'
import { Bot } from 'lucide-react'

// Import our extracted components and types
import { ApplicationPageProps, steps } from './types'
import { ProgressIndicator } from './components/ProgressIndicator'
import { ApplicationNavigation } from './components/ApplicationNavigation'

// Import step components
import { PersonalInfoStep } from './components/ApplicationSteps/PersonalInfoStep'
import { ExperienceStep } from './components/ApplicationSteps/ExperienceStep'
import { ApplicationQuestionsStep } from './components/ApplicationSteps/ApplicationQuestionsStep'
import { VoluntaryDisclosuresStep } from './components/ApplicationSteps/VoluntaryDisclosuresStep'
import { SelfIdentityStep } from './components/ApplicationSteps/SelfIdentityStep'
import { ReviewStep } from './components/ApplicationSteps/ReviewStep'

// Import our custom hooks
import { useApplicationData } from './hooks/useApplicationData'
import { useApplicationForm } from './hooks/useApplicationForm'

export default function ApplicationPage({ params }: ApplicationPageProps) {
  const [resolvedParams, setResolvedParams] = useState<{ jobId: string } | null>(null)
  const { toasts, showToast, removeToast } = useToast()
  const router = useRouter()
  
  useEffect(() => {
    params.then(setResolvedParams)
  }, [params])

  // Use our custom hooks for all the complex logic
  const {
    user,
    currentStep,
    setCurrentStep,
    formData,
    setFormData,
    applicationData,
    setApplicationData,
    jobTitle
  } = useApplicationData(resolvedParams)

  const {
    handleNext,
    handleBack,
    handleSubmit,
    isSubmitting,
    isProcessingNext
  } = useApplicationForm({
    resolvedParams,
    applicationData,
    setApplicationData,
    currentStep,
    setCurrentStep,
    formData,
    user
  })

  const isGuest = !user
  const userState = isGuest ? "guest" : (user.hasResume ? "has-resume" : "no-resume")
  const hasResume = user?.hasResume || false

  if (!user) {
    return (
      <div className="page-light min-h-screen">
        <Navigation userState="guest" user={null} theme="light" />
        <main className="container max-w-[1400px] mx-auto px-6 pt-20">
          <div className="text-center py-20">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Please Log In</h1>
            <p className="text-gray-600 mb-6">You need to be logged in to apply for this position.</p>
            <Button 
              variant="primary" 
              onClick={() => resolvedParams && router.push(`/login?redirect=/apply/${resolvedParams.jobId}`)}
            >
              Log In to Apply
            </Button>
          </div>
        </main>
      </div>
    )
  }

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <PersonalInfoStep 
            personalData={formData.personalInfo}
            addressData={formData.addressInfo}
            onPersonalChange={(data) => setFormData(prev => ({ ...prev, personalInfo: data }))}
            onAddressChange={(data) => setFormData(prev => ({ ...prev, addressInfo: data }))}
          />
        )
      case 2:
        return (
          <ExperienceStep 
            data={formData.experience} 
            onChange={(data) => setFormData(prev => ({ ...prev, experience: data }))}
          />
        )
      case 3:
        return (
          <ApplicationQuestionsStep 
            data={formData.questions} 
            onChange={(data) => setFormData(prev => ({ ...prev, questions: data }))}
          />
        )
      case 4:
        return (
          <VoluntaryDisclosuresStep 
            data={formData.disclosures} 
            onChange={(data) => setFormData(prev => ({ ...prev, disclosures: data }))}
          />
        )
      case 5:
        return (
          <SelfIdentityStep 
            data={formData.identity} 
            onChange={(data) => setFormData(prev => ({ ...prev, identity: data }))}
          />
        )
      case 6:
        return (
          <ReviewStep 
            data={formData} 
            jobTitle={jobTitle} 
            onSubmit={handleSubmit}
            onBack={handleBack}
            isSubmitting={isSubmitting}
            applicationId={applicationData?.applicationId}
          />
        )
      default:
        return null
    }
  }

  return (
    <div className="page-light min-h-screen">
      <Navigation userState={userState} user={user} theme="light" />
      
      <main className="container max-w-[1200px] mx-auto px-6 pt-20 pb-8">
        {/* Back Link */}
        <div className="mb-8">
          <Link 
            href={resolvedParams ? `/jobs/job/?id=${resolvedParams.jobId}` : '#'}
            className="text-blue-600 hover:text-blue-700 flex items-center text-base"
          >
            <span className="mr-2">←</span> Back to Job Posting
          </Link>
        </div>

        {/* Job Title */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-gray-900">{jobTitle}</h1>
        </div>

        {/* Progress Indicator */}
        <ProgressIndicator currentStep={currentStep} totalSteps={steps.length} steps={steps} />

        {/* AI Pre-fill Notice */}
        {hasResume && currentStep === 1 && (
          <div className="bg-[#f0f9ff] border border-[#0ea5e9] rounded-xl p-8 mb-12">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">AI-Powered Pre-fill Complete</h2>
                <p className="text-blue-900 text-sm">Information automatically extracted from your uploaded resume</p>
              </div>
            </div>
            <p className="text-blue-900 leading-relaxed">
              We&apos;ve analyzed your resume and pre-filled most of your information above. Please review and update any details as needed. 
              Your resume has been securely stored and will be included with your application.
            </p>
          </div>
        )}

        {/* Form Content */}
        <div className="max-w-4xl mx-auto">
          {renderCurrentStep()}
          
          {/* Navigation Buttons */}
          <ApplicationNavigation 
            currentStep={currentStep}
            steps={steps}
            onNext={handleNext}
            onBack={handleBack}
            isProcessingNext={isProcessingNext}
          />
        </div>
      </main>
      
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  )
}