import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { User } from '@/lib/types'
import { ApplicationData, initialFormData } from '../types'
import { convertDateFormat } from '../utils'

interface ApplicationDataState {
  applicationId: string
  currentStep?: number
  prefillData?: Record<string, unknown> | null
}

export function useApplicationData(resolvedParams: { jobId: string } | null) {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState<ApplicationData>(initialFormData)
  const [applicationData, setApplicationData] = useState<ApplicationDataState | null>(null)
  const [jobTitle, setJobTitle] = useState<string>('Loading...')
  const lastPrefillDataRef = useRef<Record<string, unknown> | null>(null)

  // Load application data and job info
  useEffect(() => {
    const loadApplicationAndJobData = async () => {
      if (!resolvedParams?.jobId) return

      // Get current application data from localStorage (set by Apply Now button)
      const currentAppData = localStorage.getItem('currentApplication')
      if (currentAppData) {
        const appData = JSON.parse(currentAppData)
        setApplicationData(appData)
        setCurrentStep(appData.currentStep || 1)
      }

      // Fetch job data to get real job title
      try {
        const { jobsApi } = await import('@/lib/api')
        const jobResult = await jobsApi.getById(resolvedParams.jobId)
        if (jobResult.data) {
          setJobTitle(jobResult.data.title)
        }
      } catch (error) {
        console.error('Failed to load job data:', error)
      }
    }

    loadApplicationAndJobData()
  }, [resolvedParams])

  // Initialize user and prefill data on mount - data should be ready from job detail page
  useEffect(() => {
    // Get user from localStorage
    const userData = localStorage.getItem('user')
    if (userData) {
      const parsedUser = JSON.parse(userData)
      setUser(parsedUser)
      
      // Prefill form if we have data and user has resume
      // Only prefill if we have new prefill data that we haven't processed yet
      if (parsedUser.hasResume && applicationData?.prefillData && 
          applicationData.prefillData !== lastPrefillDataRef.current) {
        lastPrefillDataRef.current = applicationData.prefillData
        const prefill = applicationData.prefillData as Record<string, unknown> || {}
        
        console.log('Prefilling form data:', prefill) // Debug log
        
        // Parse full name
        const nameParts = (prefill.full_name as string)?.split(' ') || ['', '']
        const firstName = nameParts[0] || ''
        const lastName = nameParts.slice(1).join(' ') || ''
        
        setFormData(prev => ({
          ...prev,
          personalInfo: {
            firstName,
            lastName,
            email: (prefill.email as string) || parsedUser.email || '',
            phone: (prefill.phone as string) || '',
            linkedIn: (prefill.linkedin_url as string) || ''
          },
          addressInfo: {
            street: ((prefill.address as Record<string, unknown>)?.street as string) || '',
            city: ((prefill.address as Record<string, unknown>)?.city as string) || '',
            state: ((prefill.address as Record<string, unknown>)?.state as string) || '',
            zipCode: ((prefill.address as Record<string, unknown>)?.postal_code as string) || '',
            country: ((prefill.address as Record<string, unknown>)?.country as string) || 'US'
          },
          experience: {
            summary: (prefill.summary as string) || '',
            technicalSkills: (prefill.technical_skills as string) || '',
            softSkills: (prefill.soft_skills as string) || '',
            workExperience: ((prefill.work_experience as Record<string, unknown>[]) || []).map((exp: Record<string, unknown>) => ({
              company: (exp.company_name as string) || '',
              jobTitle: (exp.job_title as string) || '',
              startDate: exp.start_date ? convertDateFormat(exp.start_date as string) : '',
              endDate: exp.is_current ? '' : (exp.end_date ? convertDateFormat(exp.end_date as string) : ''),
              isCurrent: (exp.is_current as boolean) || false,
              location: (exp.location as string) || '',
              responsibilities: Array.isArray(exp.responsibilities) ? (exp.responsibilities as string[]).join('\n• ') : ((exp.responsibilities as string) || '')
            })),
            education: ((prefill.education as Record<string, unknown>[]) || []).map((edu: Record<string, unknown>) => ({
              institution: (edu.institution as string) || '',
              degree: (edu.degree as string) || '',
              fieldOfStudy: (edu.field_of_study as string) || '',
              graduationYear: (edu.graduation_year && !isNaN(parseInt(edu.graduation_year as string, 10))) 
                ? parseInt(edu.graduation_year as string, 10) 
                : 0,
              gpa: (edu.gpa as string) || ''
            }))
          }
        }))
      }
    } else if (resolvedParams) {
      // Redirect to login if not authenticated
      router.push(`/login?redirect=/apply/job/?id=${resolvedParams.jobId}`)
    }
    setLoading(false)
  }, [resolvedParams, router, applicationData])

  return {
    user,
    loading,
    currentStep,
    setCurrentStep,
    formData,
    setFormData,
    applicationData,
    setApplicationData,
    jobTitle
  }
}