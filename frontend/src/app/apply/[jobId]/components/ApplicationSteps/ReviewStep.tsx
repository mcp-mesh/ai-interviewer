import { useState, useEffect } from 'react'
import { FileText, Eye } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ApplicationData } from '../../types'

interface ReviewStepProps {
  data: ApplicationData
  jobTitle: string
  onSubmit: () => void
  onBack: () => void
  isSubmitting: boolean
  applicationId?: string
}

// Step 6: Review Step  
export function ReviewStep({ 
  data, 
  jobTitle, 
  onSubmit, 
  onBack, 
  isSubmitting, 
  applicationId 
}: ReviewStepProps) {
  const [termsAccepted, setTermsAccepted] = useState(false)
  const [dataConsent, setDataConsent] = useState(true)
  const [reviewData, setReviewData] = useState<import('@/lib/types').ApplicationReviewData | null>(null)
  const [isLoadingReview, setIsLoadingReview] = useState(true)

  // Fetch review data from API when component mounts
  useEffect(() => {
    const fetchReviewData = async () => {
      if (!applicationId) {
        setIsLoadingReview(false)
        return
      }

      try {
        const { applicationsApi } = await import('@/lib/api-client')
        const result = await applicationsApi.getReviewData(applicationId)
        
        if (result.data) {
          setReviewData(result.data)
        } else {
          console.error('Failed to fetch review data:', result.error)
        }
      } catch (error) {
        console.error('Error fetching review data:', error)
      } finally {
        setIsLoadingReview(false)
      }
    }

    fetchReviewData()
  }, [applicationId])

  // Show loading state while fetching review data
  if (isLoadingReview) {
    return (
      <div className="space-y-8">
        <div className="text-center mb-12">
          <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
            <Eye className="w-8 h-8 text-primary-100" />
          </div>
          <h2 className="text-3xl font-semibold text-gray-900 mb-3">Review Your Application</h2>
          <p className="text-gray-600 max-w-lg mx-auto">
            Loading your application data...
          </p>
        </div>
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  // Use review data from API if available, otherwise fall back to form data
  const displayData = reviewData || data

  return (
    <div className="space-y-8">
      {/* Review Header */}
      <div className="text-center mb-12">
        <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
          <Eye className="w-8 h-8 text-primary-100" />
        </div>
        <h2 className="text-3xl font-semibold text-gray-900 mb-3">Review Your Application</h2>
        <p className="text-gray-600 max-w-lg mx-auto">
          Please review all the information below before submitting your application. You can edit any section by clicking the &ldquo;Edit&rdquo; button.
        </p>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold text-gray-900">Position</h3>
          <button className="bg-gray-200 text-gray-700 px-3 py-1 rounded-lg text-sm font-medium hover:bg-gray-300 transition-colors">
            Edit
          </button>
        </div>
        <p className="text-gray-700 font-medium">{displayData?.position?.job_title || jobTitle}</p>
      </div>
        
      {/* Personal Information */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold text-gray-900">Personal Information</h3>
          <button className="bg-gray-200 text-gray-700 px-3 py-1 rounded-lg text-sm font-medium hover:bg-gray-300 transition-colors">
            Edit
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <span className="text-sm text-gray-600">Name:</span>
            <p className="font-medium text-gray-900">
              {displayData?.personal_information?.name || 
               `${data.personalInfo.firstName} ${data.personalInfo.lastName}`}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Email:</span>
            <p className="font-medium text-gray-900">
              {displayData?.personal_information?.email || data.personalInfo.email}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Phone:</span>
            <p className="font-medium text-gray-900">
              {displayData?.personal_information?.phone || data.personalInfo.phone}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Location:</span>
            <p className="font-medium text-gray-900">
              {displayData?.personal_information?.location ? 
                `${displayData.personal_information.location.city}, ${displayData.personal_information.location.state}, ${displayData.personal_information.location.country}` :
                `${data.addressInfo.city}, ${data.addressInfo.state}, ${data.addressInfo.country}`
              }
            </p>
          </div>
        </div>
      </div>

      {/* Experience & Skills */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold text-gray-900">Experience & Skills</h3>
          <button className="bg-gray-200 text-gray-700 px-3 py-1 rounded-lg text-sm font-medium hover:bg-gray-300 transition-colors">
            Edit
          </button>
        </div>
        <div className="space-y-4">
          {(displayData?.experience_and_skills?.professional_summary || data.experience.summary) && (
            <div>
              <span className="text-sm text-gray-600">Professional Summary:</span>
              <p className="text-gray-900 mt-1">
                {displayData?.experience_and_skills?.professional_summary || data.experience.summary}
              </p>
            </div>
          )}
          {(displayData?.experience_and_skills?.current_position?.job_title || data.experience.workExperience.length > 0) && (
            <div>
              <span className="text-sm text-gray-600">Current Position:</span>
              <p className="font-medium text-gray-900">
                {displayData?.experience_and_skills?.current_position?.job_title ? 
                  `${displayData.experience_and_skills.current_position.job_title}${displayData.experience_and_skills.current_position.company ? ` at ${displayData.experience_and_skills.current_position.company}` : ''}` :
                  `${data.experience.workExperience[0]?.jobTitle} at ${data.experience.workExperience[0]?.company}`
                }
              </p>
            </div>
          )}
          {(displayData?.experience_and_skills?.technical_skills || data.experience.technicalSkills) && (
            <div>
              <span className="text-sm text-gray-600">Key Skills:</span>
              <p className="text-gray-900">
                {displayData?.experience_and_skills?.technical_skills || data.experience.technicalSkills}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Application Preferences */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold text-gray-900">Application Preferences</h3>
          <button className="bg-gray-200 text-gray-700 px-3 py-1 rounded-lg text-sm font-medium hover:bg-gray-300 transition-colors">
            Edit
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <span className="text-sm text-gray-600">Work Authorization:</span>
            <p className="font-medium text-gray-900">
              {displayData?.application_preferences?.work_authorization || data.questions.workAuthorization || 'Not specified'}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Willing to Relocate:</span>
            <p className="font-medium text-gray-900">
              {displayData?.application_preferences?.relocate || data.questions.relocate || 'Not specified'}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Remote Work:</span>
            <p className="font-medium text-gray-900">
              {displayData?.application_preferences?.remote_work || data.questions.remoteWork || 'Not specified'}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Availability:</span>
            <p className="font-medium text-gray-900">
              {displayData?.application_preferences?.availability || data.questions.availability || 'Not specified'}
            </p>
          </div>
        </div>
      </div>

      {/* Attached Documents */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h3 className="text-xl font-semibold text-gray-900 mb-6">Attached Documents</h3>
        <div className="flex items-center gap-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <FileText className="w-8 h-8 text-gray-600" />
          <div>
            <p className="font-medium text-gray-900">
              {displayData?.attached_documents?.resume?.filename || 'Resume.pdf'}
            </p>
            <span className="text-sm text-gray-600">
              {displayData?.attached_documents?.resume && displayData.attached_documents.resume.uploaded_at && displayData.attached_documents.resume.file_size ? 
                `Uploaded ${new Date(displayData.attached_documents.resume.uploaded_at).toLocaleDateString()} • ${Math.round(displayData.attached_documents.resume.file_size / 1024)} KB • Analyzed by AI` :
                'Uploaded and analyzed by AI'
              }
            </span>
          </div>
        </div>
      </div>

      {/* Terms & Conditions */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h3 className="text-xl font-semibold text-gray-900 mb-6">Terms & Conditions</h3>
        
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 mb-6">
          <p className="text-sm text-gray-700 leading-relaxed">
            By submitting this application, you acknowledge that the information provided is accurate and complete to the best of your knowledge. 
            You understand that any false information may result in disqualification from consideration or termination of employment if hired.
          </p>
        </div>
        
        <div className="space-y-4">
          <label className="flex items-start gap-3 cursor-pointer">
            <input 
              type="checkbox"
              checked={termsAccepted}
              onChange={(e) => setTermsAccepted(e.target.checked)}
              className="mt-1"
              required
            />
            <span className="text-sm leading-relaxed text-gray-700">
              I certify that the information I have provided in this application is true, complete, and accurate to the best of my knowledge. I understand that providing false or misleading information may result in rejection of my application or termination if employed.
            </span>
          </label>
          
          <label className="flex items-start gap-3 cursor-pointer">
            <input 
              type="checkbox"
              checked={dataConsent}
              onChange={(e) => setDataConsent(e.target.checked)}
              className="mt-1"
            />
            <span className="text-sm leading-relaxed text-gray-700">
              I consent to S Corp. processing my application data for recruitment purposes and contacting me regarding this position and future opportunities that may be of interest.
            </span>
          </label>
        </div>
      </div>

      {/* Navigation Buttons - consistent with other steps */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200">
        <Button 
          variant="secondary" 
          onClick={onBack}
          className="px-6 py-3 text-base bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 hover:text-gray-900 shadow-sm"
        >
          Back
        </Button>
        
        <Button
          variant="primary"
          onClick={() => termsAccepted && onSubmit()}
          disabled={!termsAccepted || isSubmitting}
          className={`px-6 py-3 text-base ${
            !termsAccepted || isSubmitting ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {isSubmitting ? 'Submitting...' : 'Submit Application'}
        </Button>
      </div>

    </div>
  )
}