"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useGoogleReCaptcha } from 'react-google-recaptcha-v3'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { ToastContainer, useToast } from '@/components/common'
import { User } from '@/lib/types'
import { FileText, Upload, CheckCircle, Shield, RefreshCw } from 'lucide-react'

export default function UploadPage() {
  const router = useRouter()
  const { executeRecaptcha } = useGoogleReCaptcha()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [recaptchaToken, setRecaptchaToken] = useState<string | null>(null)
  const [recaptchaLoading, setRecaptchaLoading] = useState(false)
  const [termsAccepted, setTermsAccepted] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const { toasts, showToast, removeToast, clearAllToasts } = useToast()

  useEffect(() => {
    // Get user from localStorage
    const userData = localStorage.getItem('user')
    if (userData) {
      setUser(JSON.parse(userData))
    } else {
      // Redirect to login if no user found
      router.push('/login?redirect=/upload')
    }
    setLoading(false)
  }, [router])

  const executeReCaptcha = async () => {
    if (!executeRecaptcha) {
      showToast.error('reCAPTCHA not available')
      return false
    }

    setRecaptchaLoading(true)
    try {
      const token = await executeRecaptcha('upload_resume')
      setRecaptchaToken(token)
      showToast.success('Security verification completed')
      return true
    } catch (error) {
      showToast.error('Security verification failed')
      console.error('reCAPTCHA error:', error)
      return false
    } finally {
      setRecaptchaLoading(false)
    }
  }

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      if (file.type !== 'application/pdf') {
        showToast.error('Please select a PDF file only.')
        return
      }
      if (file.size > 5 * 1024 * 1024) { // 5MB
        showToast.error('File size must be less than 5MB.')
        return
      }
      setSelectedFile(file)
      showToast.success('File selected successfully!')
    }
  }


  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const isFormValid = selectedFile && recaptchaToken && termsAccepted

  const handleUpload = async () => {
    if (!selectedFile || !termsAccepted) {
      showToast.error('Please complete all required fields')
      return
    }

    // Execute reCAPTCHA if not already done
    if (!recaptchaToken) {
      const success = await executeReCaptcha()
      if (!success) return
    }

    setIsUploading(true)
    showToast.info('Uploading resume...')

    try {
      // Create form data for file upload with reCAPTCHA token
      const formData = new FormData()
      formData.append('file', selectedFile)
      if (recaptchaToken) {
        formData.append('recaptcha_token', recaptchaToken)
      }
      formData.append('process_with_ai', 'true')

      // Make API call to backend
      const response = await fetch('/api/files/resume', {
        method: 'POST',
        body: formData,
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.detail || 'Upload failed')
      }

      if (!result.success) {
        throw new Error(result.error || result.message || 'Upload failed')
      }

      // Fetch updated user profile with resume analysis data
      try {
        const { userApi } = await import('@/lib/api')
        const profileResult = await userApi.getProfile()
        
        if (profileResult.data) {
          // Update user state with fresh profile data including resume analysis
          setUser(profileResult.data)
          localStorage.setItem('user', JSON.stringify(profileResult.data))
        }
      } catch (profileError) {
        console.error('Failed to fetch updated profile:', profileError)
        // Fallback to manual update if profile fetch fails
        if (user) {
          const updatedUser = { 
            ...user, 
            hasResume: true,
            profile: {
              ...user.profile,
              resume_url: result.upload?.file_path || '/uploaded-resume.pdf'
            }
          }
          setUser(updatedUser as User)
          localStorage.setItem('user', JSON.stringify(updatedUser))
        }
      }

      // Clear the "Uploading..." toast before showing success
      clearAllToasts()
      setTimeout(() => {
        showToast.success('Resume uploaded successfully!')
        setTimeout(() => {
          router.push('/dashboard')
        }, 1500)
      }, 100)

    } catch (error) {
      setIsUploading(false)
      clearAllToasts()
      const errorMessage = error instanceof Error ? error.message : 'Upload failed'
      showToast.error(errorMessage)
      console.error('Resume upload failed:', error)
    }
  }

  const getMissingRequirements = () => {
    const missing = []
    if (!selectedFile) missing.push('select a PDF file')
    if (!recaptchaToken) missing.push('complete security verification')
    if (!termsAccepted) missing.push('accept terms')
    return missing
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card>
          <CardContent className="text-center py-8">
            <p className="mb-4">Loading...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card>
          <CardContent className="text-center py-8">
            <p className="mb-4">Please log in to upload your resume</p>
            <Button onClick={() => router.push('/login')} variant="primary">Go to Login</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="page-light min-h-screen">
      <Navigation userState="no-resume" user={user} theme="light" />
      
      <main className="container max-w-[900px] mx-auto px-6 pt-20">
        <div className="py-12">
          {/* Header Section */}
          <div className="text-center mb-12">
            <div className="w-20 h-20 bg-primary-500 rounded-[20px] flex items-center justify-center mx-auto mb-8">
              <FileText className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-[2.5rem] font-bold text-light-text-primary mb-4">Upload Your Resume</h1>
            <p className="text-[1.125rem] text-light-text-secondary leading-relaxed max-w-[600px] mx-auto">
              Upload your resume for AI-powered analysis and personalized interview questions tailored to your experience.
            </p>
          </div>

          {/* Upload Section */}
          <div 
            className="bg-white border-2 border-dashed border-light-border hover:border-primary-500 transition-all duration-300 rounded-2xl p-12 mb-12 text-center"
          >
            <Upload className="w-12 h-12 text-light-text-muted mb-6 mx-auto" />
            <h3 className="text-[1.5rem] font-semibold text-light-text-primary mb-4">Upload your resume</h3>
            <p className="text-light-text-secondary mb-8 text-base">Drag and drop your PDF file here, or click to browse</p>
            
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              className="hidden"
              id="resume-upload"
            />
            <Button 
              onClick={() => document.getElementById('resume-upload')?.click()}
              variant="primary"
              size="default"
            >
              Choose File
            </Button>
            
            {selectedFile && (
              <div className="mt-4 p-4 bg-primary-50 border border-primary-400 rounded-lg">
                <p className="text-primary-900 font-medium m-0">
                  {selectedFile.name} - {formatFileSize(selectedFile.size)}
                </p>
              </div>
            )}
          </div>

          {/* File Requirements */}
          <div className="bg-white border border-light-border rounded-xl p-8 mb-12">
            <h4 className="text-[1.125rem] font-semibold text-light-text-primary mb-6">File Requirements:</h4>
            <ul className="list-none p-0 m-0 text-gray-600">
              <li className="flex items-center gap-2 mb-3">
                <CheckCircle className="w-5 h-5 text-success-500" /> PDF format only
              </li>
              <li className="flex items-center gap-2 mb-3">
                <CheckCircle className="w-5 h-5 text-success-500" /> Maximum file size: 5MB
              </li>
              <li className="flex items-center gap-2 mb-3">
                <CheckCircle className="w-5 h-5 text-success-500" /> Text should be selectable (not scanned images)
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-success-500" /> Include your work experience, skills, and education
              </li>
            </ul>
          </div>

          {/* Privacy & Security */}
          <div className="bg-primary-50 border border-primary-400 rounded-xl p-8 mb-12">
            <h4 className="text-[1.125rem] font-semibold text-primary-900 mb-4">Privacy & Security</h4>
            <p className="text-primary-900 leading-relaxed m-0">
              Your resume is processed securely using AI technology and used only to generate personalized interview questions. We do not share your information with third parties.
            </p>
          </div>

          {/* Security Verification Section */}
          <div className="bg-white border border-light-border rounded-xl p-8 mb-12">
            <h4 className="text-[1.125rem] font-semibold text-light-text-primary mb-6">Security Verification</h4>
            
            <div className="border-2 border-light-border rounded-lg p-8 bg-light-surface text-center">
              <Shield className="w-12 h-12 text-light-text-muted mb-4 mx-auto" />
              <p className="text-light-text-secondary mb-6">
                Click the button below to verify you&apos;re human using Google&apos;s security system.
              </p>
              
              <Button 
                onClick={executeReCaptcha}
                disabled={recaptchaLoading || !!recaptchaToken}
                variant={recaptchaToken ? "outline" : "primary"}
                size="default"
                className="mb-4"
              >
                {recaptchaLoading ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Verifying...
                  </>
                ) : recaptchaToken ? (
                  <>
                    <CheckCircle className="w-4 h-4 mr-2 text-green-600" />
                    Verified
                  </>
                ) : (
                  <>
                    <Shield className="w-4 h-4 mr-2" />
                    Verify Security
                  </>
                )}
              </Button>
              
              {recaptchaToken && (
                <div className="text-sm text-green-600">
                  <CheckCircle className="w-4 h-4 inline mr-1" /> 
                  Security verification completed successfully
                </div>
              )}
            </div>
          </div>

          {/* Legal Agreement */}
          <div className="bg-white border border-light-border rounded-xl p-8 mb-12">
            <h4 className="text-[1.125rem] font-semibold text-light-text-primary mb-6">Terms and Conditions</h4>
            
            <div className="max-h-48 overflow-y-auto border border-light-border rounded-lg p-6 bg-light-surface mb-6 text-sm leading-relaxed text-gray-600">
                <h5 className="font-semibold text-light-text-primary mb-4">S Corp. Resume Processing Agreement</h5>
                
                <p className="mb-4"><strong>1. Data Processing Consent:</strong> By uploading your resume, you explicitly consent to S Corp. processing your personal and professional information contained within your resume for the purposes of job matching, interview preparation, and career services.</p>
                
                <p className="mb-4"><strong>2. AI Analysis:</strong> Your resume will be analyzed using artificial intelligence technology to extract relevant skills, experience, and qualifications. This analysis will be used to provide personalized job recommendations and interview questions.</p>
                
                <p className="mb-4"><strong>3. Data Retention:</strong> Your resume and extracted information will be stored securely for the duration of your active account plus 12 months thereafter, unless you request deletion. You may request deletion of your data at any time by contacting support@aicareers.com.</p>
                
                <p className="mb-4"><strong>4. Data Sharing:</strong> We do not sell or share your personal information with third parties for marketing purposes. Your information may be shared with potential employers only after you explicitly apply for positions and consent to sharing your information with specific companies.</p>
                
                <p className="mb-4"><strong>5. Data Security:</strong> We implement industry-standard security measures to protect your information, including encryption at rest and in transit, secure access controls, and regular security audits.</p>
                
                <p className="mb-4"><strong>6. Accuracy Disclaimer:</strong> While our AI technology is highly accurate, you acknowledge that automated analysis may not capture all nuances of your experience. You are responsible for reviewing and correcting any inaccuracies in your profile.</p>
                
                <p className="mb-4"><strong>7. Right to Withdrawal:</strong> You may withdraw your consent at any time by deleting your account, which will result in the removal of your resume and all associated data from our systems within 30 days.</p>
                
                <p className="mb-4"><strong>8. Updates to Terms:</strong> We may update these terms periodically. Continued use of our service after updates constitutes acceptance of new terms.</p>
                
                <p className="mb-4"><strong>9. Contact Information:</strong> For questions about data processing or to exercise your rights, contact us at privacy@aicareers.com or through our privacy portal.</p>
                
                <p><strong>10. Governing Law:</strong> This agreement is governed by the laws of California and any disputes will be resolved in California courts.</p>
              </div>
              
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={termsAccepted}
                  onChange={(e) => setTermsAccepted(e.target.checked)}
                  className="mt-1"
                />
                <span className="text-sm leading-relaxed text-gray-600">
                  I have read and agree to the Terms and Conditions above. I consent to the processing of my resume data for AI-powered job matching and interview preparation services.
                </span>
              </label>
          </div>

          {/* Upload Button */}
          <div className="text-center">
            <Button
              onClick={handleUpload}
              disabled={!isFormValid || isUploading}
              variant="primary"
              size="lg"
              className="px-12 text-[1.125rem]"
            >
              {isUploading ? 'Uploading...' : 'Upload Resume'}
            </Button>
            <p className="text-light-text-secondary text-sm mt-4">
              {isFormValid 
                ? 'Ready to upload your resume'
                : `Please ${getMissingRequirements().join(', ')} to enable upload`
              }
            </p>
          </div>
        </div>
      </main>
      
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  )
}