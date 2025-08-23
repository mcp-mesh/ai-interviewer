"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { WireframeButton, ToastContainer, useToast } from '@/components/wireframe'
import { User } from '@/lib/types'

export default function UploadPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [captchaText, setCaptchaText] = useState('7B4K9')
  const [captchaInput, setCaptchaInput] = useState('')
  const [captchaValid, setCaptchaValid] = useState(false)
  const [termsAccepted, setTermsAccepted] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const { toasts, showToast, removeToast } = useToast()

  useEffect(() => {
    // Get user from localStorage
    const userData = localStorage.getItem('user')
    if (userData) {
      setUser(JSON.parse(userData))
    } else {
      // Redirect to login if no user found
      router.push('/login?redirect=/upload')
    }
  }, [router])

  const generateCaptcha = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    let result = ''
    for (let i = 0; i < 5; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return result
  }

  const refreshCaptcha = () => {
    const newCaptcha = generateCaptcha()
    setCaptchaText(newCaptcha)
    setCaptchaInput('')
    setCaptchaValid(false)
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

  const handleCaptchaChange = (value: string) => {
    setCaptchaInput(value.toUpperCase())
    setCaptchaValid(value.toUpperCase() === captchaText)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const isFormValid = selectedFile && captchaValid && termsAccepted

  const handleUpload = async () => {
    if (!isFormValid) return

    setIsUploading(true)
    showToast.info('Uploading resume...')

    // Simulate upload process
    setTimeout(() => {
      // Update user state with resume flag
      if (user) {
        const updatedUser = { ...user, isResumeAvailable: true }
        localStorage.setItem('user', JSON.stringify(updatedUser))
      }

      // Show success and redirect
      showToast.success('Resume uploaded successfully!')
      setTimeout(() => {
        router.push('/dashboard')
      }, 1500)
    }, 2000)
  }

  const getMissingRequirements = () => {
    const missing = []
    if (!selectedFile) missing.push('select a PDF file')
    if (!captchaValid) missing.push('complete the captcha')
    if (!termsAccepted) missing.push('accept terms')
    return missing
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card>
          <CardContent className="text-center py-8">
            <p className="mb-4">Please log in to upload your resume</p>
            <WireframeButton onClick={() => router.push('/login')} variant="primary">Go to Login</WireframeButton>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="page-light min-h-screen">
      <Navigation userState="authenticated" user={user} theme="light" />
      
      <main className="container max-w-[900px] mx-auto px-6 pt-20">
        <div className="py-12">
          {/* Header Section */}
          <div className="text-center mb-12">
            <div className="w-20 h-20 bg-[#3b82f6] rounded-[20px] flex items-center justify-center mx-auto mb-8 text-[2rem] text-white">
              📄
            </div>
            <h1 className="text-[2.5rem] font-bold text-[#1f2937] mb-4">Upload Your Resume</h1>
            <p className="text-[1.125rem] text-[#6b7280] leading-relaxed max-w-[600px] mx-auto">
              Upload your resume for AI-powered analysis and personalized interview questions tailored to your experience.
            </p>
          </div>

          {/* Upload Section */}
          <div 
            className="bg-white border-2 border-dashed border-[#d1d5db] hover:border-[#3b82f6] transition-all duration-300 rounded-2xl p-12 mb-12 text-center"
            style={{
              borderDasharray: '12px 8px',
              borderStyle: 'dashed'
            }}
          >
            <div className="text-[3rem] text-[#9ca3af] mb-6">☁️</div>
            <h3 className="text-[1.5rem] font-semibold text-[#1f2937] mb-4">Upload your resume</h3>
            <p className="text-[#6b7280] mb-8 text-base">Drag and drop your PDF file here, or click to browse</p>
            
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              className="hidden"
              id="resume-upload"
            />
            <WireframeButton 
              onClick={() => document.getElementById('resume-upload')?.click()}
              variant="primary"
              size="md"
            >
              Choose File
            </WireframeButton>
            
            {selectedFile && (
              <div className="mt-4 p-4 bg-[#f0f9ff] border border-[#0ea5e9] rounded-lg">
                <p className="text-[#0c4a6e] font-medium m-0">
                  {selectedFile.name} - {formatFileSize(selectedFile.size)}
                </p>
              </div>
            )}
          </div>

          {/* File Requirements */}
          <div className="bg-white border border-[#e5e7eb] rounded-xl p-8 mb-12">
            <h4 className="text-[1.125rem] font-semibold text-[#1f2937] mb-6">File Requirements:</h4>
            <ul className="list-none p-0 m-0 text-[#4b5563]">
              <li className="flex items-center gap-2 mb-3">
                <span className="text-[#10b981]">✓</span> PDF format only
              </li>
              <li className="flex items-center gap-2 mb-3">
                <span className="text-[#10b981]">✓</span> Maximum file size: 5MB
              </li>
              <li className="flex items-center gap-2 mb-3">
                <span className="text-[#10b981]">✓</span> Text should be selectable (not scanned images)
              </li>
              <li className="flex items-center gap-2">
                <span className="text-[#10b981]">✓</span> Include your work experience, skills, and education
              </li>
            </ul>
          </div>

          {/* Privacy & Security */}
          <div className="bg-[#f0f9ff] border border-[#0ea5e9] rounded-xl p-8 mb-12">
            <h4 className="text-[1.125rem] font-semibold text-[#0c4a6e] mb-4">Privacy & Security</h4>
            <p className="text-[#0c4a6e] leading-relaxed m-0">
              Your resume is processed securely using AI technology and used only to generate personalized interview questions. We do not share your information with third parties.
            </p>
          </div>

          {/* CAPTCHA Section */}
          <div className="bg-white border border-[#e5e7eb] rounded-xl p-8 mb-12">
            <h4 className="text-[1.125rem] font-semibold text-[#1f2937] mb-6">Security Verification</h4>
            
            <div className="border-2 border-[#e5e7eb] rounded-lg p-8 bg-[#f9fafb] text-center">
              <div className="flex items-center justify-center gap-4 mb-4">
                <div className="bg-white border border-[#d1d5db] p-4 rounded font-mono text-[1.5rem] tracking-[0.1em] text-[#1f2937] min-w-[150px]">
                  {captchaText}
                </div>
                <WireframeButton 
                  onClick={refreshCaptcha}
                  variant="secondary"
                  size="sm"
                  className="!p-2 !min-h-[2rem]"
                >
                  🔄
                </WireframeButton>
              </div>
              <div className="mb-2">
                <input
                  type="text"
                  placeholder="Enter the characters above"
                  value={captchaInput}
                  onChange={(e) => handleCaptchaChange(e.target.value)}
                  className="px-3 py-3 border border-[#d1d5db] rounded text-center w-48 text-base"
                />
              </div>
              <div className="text-sm min-h-[20px]">
                {captchaInput.length === captchaText.length && (
                  <span className={captchaValid ? "text-green-600" : "text-red-600"}>
                    {captchaValid ? "✓ Verified" : "✗ Incorrect"}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Legal Agreement */}
          <div className="bg-white border border-[#e5e7eb] rounded-xl p-8 mb-12">
            <h4 className="text-[1.125rem] font-semibold text-[#1f2937] mb-6">Terms and Conditions</h4>
            
            <div className="max-h-48 overflow-y-auto border border-[#e5e7eb] rounded-lg p-6 bg-[#f9fafb] mb-6 text-sm leading-relaxed text-[#4b5563]">
                <h5 className="font-semibold text-[#1f2937] mb-4">S Corp. Resume Processing Agreement</h5>
                
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
                <span className="text-sm leading-relaxed text-[#4b5563]">
                  I have read and agree to the Terms and Conditions above. I consent to the processing of my resume data for AI-powered job matching and interview preparation services.
                </span>
              </label>
          </div>

          {/* Upload Button */}
          <div className="text-center">
            <WireframeButton
              onClick={handleUpload}
              disabled={!isFormValid || isUploading}
              variant="primary"
              size="lg"
              className="px-12 text-[1.125rem]"
            >
              {isUploading ? 'Uploading...' : 'Upload Resume'}
            </WireframeButton>
            <p className="text-[#6b7280] text-sm mt-4">
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