import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { User } from '@/lib/types'
import { ApplicationData, steps } from '../types'
import { useToast } from '@/components/common'

interface ApplicationDataState {
  applicationId: string
  currentStep?: number
  prefillData?: Record<string, unknown> | null
}

interface UseApplicationFormProps {
  resolvedParams: { jobId: string } | null
  applicationData: ApplicationDataState | null
  setApplicationData: (data: ApplicationDataState) => void
  currentStep: number
  setCurrentStep: (step: number) => void
  formData: ApplicationData
  user: User | null
}

export function useApplicationForm({
  resolvedParams,
  applicationData,
  setApplicationData,
  currentStep,
  setCurrentStep,
  formData,
  user
}: UseApplicationFormProps) {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isProcessingNext, setIsProcessingNext] = useState(false)
  const { showToast, clearAllToasts } = useToast()

  const handleNext = async () => {
    if (!resolvedParams || !applicationData?.applicationId || isProcessingNext) return
    
    setIsProcessingNext(true) // Set loading state
    
    // Save current step data with appropriate notification
    const stepMessages = {
      1: 'Saving information...',
      2: 'Saving experience...',
      3: 'Saving responses...',
      4: 'Saving voluntary disclosures...',
      5: 'Saving identity information...'
    }
    
    if (currentStep <= 5) {
      const message = stepMessages[currentStep as keyof typeof stepMessages]
      showToast.info(message)
      
      try {
        // Real API call to save step data
        const { applicationsApi } = await import('@/lib/api-client')
        const stepData = getStepData(currentStep)
        
        const result = await applicationsApi.saveStep(
          applicationData.applicationId,
          currentStep,
          stepData
        )
        
        if (result.data) {
          // Clear the "Saving..." toast and show success
          clearAllToasts()
          setTimeout(() => {
            showToast.success('Information saved successfully!')
          }, 100)
          
          // Move to next step
          if (currentStep < steps.length) {
            setCurrentStep(currentStep + 1)
            
            // Update localStorage with new step and capture prefill data from API response
            const updatedAppData = {
              ...applicationData,
              currentStep: currentStep + 1,
              prefillData: result.data.data?.prefill_data ? result.data.data.prefill_data as Record<string, unknown> : null
            }
            localStorage.setItem('currentApplication', JSON.stringify(updatedAppData))
            setApplicationData(updatedAppData)
          }
        } else {
          // Handle API error
          clearAllToasts()
          showToast.error(result.error || 'Failed to save information')
        }
      } catch (error) {
        console.error('Error saving step:', error)
        clearAllToasts()
        showToast.error('An error occurred while saving')
      } finally {
        setIsProcessingNext(false) // Clear loading state for API steps
      }
    } else if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1)
      setIsProcessingNext(false) // Clear loading state for non-API steps
    } else {
      setIsProcessingNext(false) // Clear loading state for edge cases
    }
  }

  // Helper function to get current step data in backend format
  const getStepData = (step: number) => {
    switch (step) {
      case 1:
        return {
          full_name: `${formData.personalInfo.firstName} ${formData.personalInfo.lastName}`.trim(),
          email: formData.personalInfo.email,
          phone: formData.personalInfo.phone,
          address: {
            street: formData.addressInfo.street,
            city: formData.addressInfo.city,
            state: formData.addressInfo.state,
            country: formData.addressInfo.country,
            postal_code: formData.addressInfo.zipCode
          },
          linkedin_url: formData.personalInfo.linkedIn,
          professional_title: formData.personalInfo.firstName ? 'Professional' : '' // Placeholder
        }
      case 2:
        return {
          summary: formData.experience.summary,
          technical_skills: formData.experience.technicalSkills,
          soft_skills: formData.experience.softSkills,
          work_experience: formData.experience.workExperience.map(exp => ({
            job_title: exp.jobTitle,
            company: exp.company,
            location: exp.location,
            start_date: exp.startDate,
            end_date: exp.endDate,
            is_current: exp.isCurrent,
            responsibilities: exp.responsibilities.split('\n').filter(r => r.trim())
          })),
          education: formData.experience.education.map(edu => ({
            degree: edu.degree,
            field: edu.fieldOfStudy,
            school: edu.institution,
            graduation_year: edu.graduationYear.toString(),
            gpa: edu.gpa
          }))
        }
      case 3:
        return {
          work_authorization: formData.questions.workAuthorization,
          visa_sponsorship: formData.questions.visaSponsorship,
          relocate: formData.questions.relocate,
          remote_work: formData.questions.remoteWork,
          preferred_location: formData.questions.preferredLocation,
          availability: formData.questions.availability,
          salary_min: formData.questions.salaryMin,
          salary_max: formData.questions.salaryMax
        }
      case 4:
        return {
          government_employment: formData.disclosures.governmentEmployment,
          non_compete: formData.disclosures.nonCompete,
          previous_employment: formData.disclosures.previousEmployment,
          previous_alias: formData.disclosures.previousAlias,
          personnel_number: formData.disclosures.personnelNumber
        }
      case 5:
        return {
          gender: formData.identity.gender,
          race: formData.identity.race,
          veteran_status: formData.identity.veteranStatus,
          disability: formData.identity.disability
        }
      default:
        return {}
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    } else if (resolvedParams) {
      // Go back to job detail
      router.push(`/jobs/job/?id=${resolvedParams.jobId}`)
    }
  }

  const handleSubmit = async () => {
    if (!resolvedParams || !applicationData?.applicationId) return
    
    setIsSubmitting(true)
    showToast.info('Submitting your application...')
    
    try {
      // Call Step 6 API with submit_application flag
      const { applicationsApi } = await import('@/lib/api-client')
      const result = await applicationsApi.saveStep(
        applicationData.applicationId,
        6,
        { submit_application: true }
      )
      
      if (result.data?.success) {
        // Clear the "Submitting..." toast before showing success
        clearAllToasts()
        setTimeout(() => {
          showToast.success('Application submitted successfully!')
        }, 100)
        
        // Process the submission response data
        const responseData = result.data.data as Record<string, unknown> || {}
        console.log('Step 6 submission response:', result.data)
        
        // Refresh user profile to get updated applications list first
        let updatedUser = user
        if (user) {
          try {
            const { userApi } = await import('@/lib/api')
            const userResult = await userApi.getProfile()
            if (userResult.data) {
              // Update localStorage with fresh user data including applications
              localStorage.setItem('user', JSON.stringify(userResult.data))
              updatedUser = userResult.data
              console.log('User profile refreshed after application submission')
            }
          } catch (profileError) {
            console.error('Failed to refresh user profile:', profileError)
            // Don't block the flow if profile refresh fails
          }
        }
        
        // Determine qualification result using fresh user profile data
        const currentApplication = updatedUser?.applications?.find(app => app.jobId === resolvedParams.jobId)
        const isQualifiedForInterview = currentApplication?.qualified === true && currentApplication?.status === 'QUALIFIED'
        const redirectUrl = responseData.redirect_url as string || 
          `/apply/${resolvedParams.jobId}/result?result=${isQualifiedForInterview ? 'interview' : 'under-review'}`
        
        console.log('Interview qualification result:', { 
          applicationStatus: currentApplication?.status,
          qualified: currentApplication?.qualified,
          isQualifiedForInterview, 
          redirectUrl 
        })
        
        setTimeout(() => {
          setIsSubmitting(false)
          // Use redirect URL based on fresh user profile data
          router.push(redirectUrl)
        }, 1500)
        
      } else {
        throw new Error(result.error || 'Failed to submit application')
      }
      
    } catch (error) {
      console.error('Application submission failed:', error)
      clearAllToasts()
      showToast.error('Failed to submit application. Please try again.')
      setIsSubmitting(false)
    }
  }

  return {
    handleNext,
    handleBack,
    handleSubmit,
    isSubmitting,
    isProcessingNext
  }
}