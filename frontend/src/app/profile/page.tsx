'use client'

import { useState, useEffect } from 'react'
import { 
  UserCircleIcon, 
  DocumentTextIcon,
  CalendarIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowLeftIcon,
  BriefcaseIcon,
  AcademicCapIcon,
  SparklesIcon
} from '@heroicons/react/24/outline'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

interface StructuredAnalysis {
  professional_summary: string
  technical_skills: string[]
  years_experience: number
  education_level: string
  key_achievements: string[]
  work_experience: Array<{
    title: string
    company: string
    duration: string
    key_responsibilities: string[]
  }>
  document_quality: string
  ai_provider?: string
  ai_model?: string
}

interface ResumeData {
  filename: string
  uploaded_at: string
  file_size: number
  extracted_text: string
  structured_analysis?: StructuredAnalysis
  analysis_enhanced: boolean
  text_stats: {
    char_count: number
    word_count: number
    line_count: number
    pages_processed: number
    total_pages: number
  }
  page_count: number
  sections: {
    [key: string]: string
  }
  summary: string
  minio_path: string
}

interface UserData {
  user_id: string
  email: string
  name: string
  admin?: boolean
  resume?: ResumeData
}

export default function ProfilePage() {
  const router = useRouter()
  const [userData, setUserData] = useState<UserData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    fetchUserData()
  }, [])

  const fetchUserData = async () => {
    try {
      const response = await fetch('/api/user/profile', {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setUserData(data.user)
      } else {
        throw new Error('Failed to fetch user data')
      }
    } catch (error) {
      console.error('Error fetching user data:', error)
      setError('Failed to load profile data')
      router.push('/dashboard')
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  if (error || !userData?.resume) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-600 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Profile Not Available</h2>
          <p className="text-gray-600 mb-4">{error || 'No resume data found'}</p>
          <Link 
            href="/dashboard"
            className="inline-flex items-center space-x-2 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
          >
            <ArrowLeftIcon className="h-4 w-4" />
            <span>Back to Dashboard</span>
          </Link>
        </div>
      </div>
    )
  }

  const { resume } = userData
  const { structured_analysis } = resume

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link href="/dashboard" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
              <ArrowLeftIcon className="h-5 w-5 text-gray-600" />
              <div className="bg-gradient-to-r from-purple-600 to-indigo-600 p-2 rounded-lg">
                <UserCircleIcon className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-xl font-bold text-gray-900">Your Profile</h1>
            </Link>
            
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-full flex items-center justify-center">
                <span className="text-white font-semibold text-sm">
                  {userData.name?.charAt(0) || 'U'}
                </span>
              </div>
              <div className="hidden sm:block">
                <p className="text-sm font-medium text-gray-900">{userData.name}</p>
                <p className="text-xs text-gray-500">{userData.email}</p>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Profile Overview</h1>
          <p className="text-lg text-gray-600">Your structured resume data used for AI-powered interviews</p>
        </div>

        {/* Structured Data */}
        {structured_analysis && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
              <SparklesIcon className="h-6 w-6 text-purple-600" />
              <span>AI Analyzed Profile</span>
            </h2>

            {/* AI Analysis Info */}
            {structured_analysis.ai_provider && structured_analysis.ai_model && (
              <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-2xl border border-purple-200 p-6">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-xl flex items-center justify-center">
                    <SparklesIcon className="h-6 w-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">AI-Powered Analysis</h3>
                    <p className="text-gray-700 mb-3">
                      Your resume was analyzed using advanced AI technology to extract structured information and insights.
                    </p>
                    <div className="flex items-center space-x-6 text-sm">
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                        <span className="text-gray-600">Provider:</span>
                        <span className="font-semibold text-purple-700 capitalize">{structured_analysis.ai_provider}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-indigo-600 rounded-full"></div>
                        <span className="text-gray-600">Model:</span>
                        <span className="font-semibold text-indigo-700">{structured_analysis.ai_model}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Professional Summary */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-start space-x-4">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <UserCircleIcon className="h-5 w-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Professional Summary</h3>
                  <p className="text-gray-700 leading-relaxed">{structured_analysis.professional_summary}</p>
                </div>
              </div>
            </div>

            {/* Key Information */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center space-x-3 mb-3">
                  <CalendarIcon className="h-5 w-5 text-green-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Experience</h3>
                </div>
                <p className="text-3xl font-bold text-green-600">{structured_analysis.years_experience}</p>
                <p className="text-sm text-gray-600">Years of experience</p>
              </div>

              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center space-x-3 mb-3">
                  <AcademicCapIcon className="h-5 w-5 text-purple-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Education</h3>
                </div>
                <p className="text-xl font-bold text-purple-600">{structured_analysis.education_level}</p>
                <p className="text-sm text-gray-600">Highest level</p>
              </div>

              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center space-x-3 mb-3">
                  <CheckCircleIcon className="h-5 w-5 text-indigo-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Quality</h3>
                </div>
                <p className="text-xl font-bold text-indigo-600 capitalize">{structured_analysis.document_quality}</p>
                <p className="text-sm text-gray-600">Resume rating</p>
              </div>
            </div>

            {/* Technical Skills */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
                <div className="w-5 h-5 bg-blue-100 rounded flex items-center justify-center">
                  <span className="text-xs text-blue-600">⚡</span>
                </div>
                <span>Technical Skills</span>
              </h3>
              <div className="flex flex-wrap gap-2">
                {structured_analysis.technical_skills.map((skill, index) => (
                  <span 
                    key={index} 
                    className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-medium border border-blue-200"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            {/* Work Experience */}
            {structured_analysis.work_experience && structured_analysis.work_experience.length > 0 && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
                  <BriefcaseIcon className="h-5 w-5 text-gray-600" />
                  <span>Work Experience</span>
                </h3>
                <div className="space-y-4">
                  {structured_analysis.work_experience.map((job, index) => (
                    <div key={index} className="border-l-4 border-blue-200 pl-4">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h4 className="font-semibold text-gray-900">{job.title}</h4>
                          <p className="text-blue-600 font-medium">{job.company}</p>
                        </div>
                        <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">{job.duration}</span>
                      </div>
                      {job.key_responsibilities && job.key_responsibilities.length > 0 && (
                        <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                          {job.key_responsibilities.map((responsibility, idx) => (
                            <li key={idx}>{responsibility}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Key Achievements */}
            {structured_analysis.key_achievements && structured_analysis.key_achievements.length > 0 && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
                  <div className="w-5 h-5 bg-yellow-100 rounded flex items-center justify-center">
                    <span className="text-xs text-yellow-600">🏆</span>
                  </div>
                  <span>Key Achievements</span>
                </h3>
                <ul className="space-y-2">
                  {structured_analysis.key_achievements.map((achievement, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{achievement}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Update Resume Button */}
        <div className="mt-8 text-center">
          <Link 
            href="/upload"
            className="inline-flex items-center space-x-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            <DocumentTextIcon className="h-5 w-5" />
            <span>Update Resume</span>
          </Link>
        </div>

        {/* Resume File Info */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 mb-6 mt-12">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
              <DocumentTextIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Resume Details</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-gray-500 mb-1">Filename</p>
                  <p className="font-medium text-gray-900">{resume.filename}</p>
                </div>
                <div>
                  <p className="text-gray-500 mb-1">Upload Date</p>
                  <p className="font-medium text-gray-900">
                    {new Date(resume.uploaded_at).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 mb-1">File Size</p>
                  <p className="font-medium text-gray-900">{(resume.file_size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Analysis Status */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center space-x-4">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${resume.analysis_enhanced ? 'bg-green-100' : 'bg-amber-100'}`}>
              {resume.analysis_enhanced ? (
                <CheckCircleIcon className="h-6 w-6 text-green-600" />
              ) : (
                <ExclamationTriangleIcon className="h-6 w-6 text-amber-600" />
              )}
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {resume.analysis_enhanced ? 'AI Analysis Complete' : 'AI Analysis Incomplete'}
              </h3>
              <p className="text-sm text-gray-600">
                {resume.analysis_enhanced ? 
                  'Your resume has been processed and structured by AI for personalized interviews' :
                  'AI analysis is not available for this resume'
                }
              </p>
            </div>
          </div>
        </div>

        {/* Document Stats */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Document Statistics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-2xl font-bold text-blue-600">{resume.text_stats?.total_pages || resume.page_count || 0}</p>
              <p className="text-sm text-gray-600">Pages</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-2xl font-bold text-green-600">{resume.text_stats?.word_count?.toLocaleString() || 0}</p>
              <p className="text-sm text-gray-600">Words</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-2xl font-bold text-purple-600">{resume.text_stats?.char_count?.toLocaleString() || 0}</p>
              <p className="text-sm text-gray-600">Characters</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              {structured_analysis?.ai_provider && structured_analysis?.ai_model ? (
                <>
                  <p className="text-lg font-bold text-indigo-600 capitalize">{structured_analysis.ai_provider}</p>
                  <p className="text-xs text-gray-500 mb-1">{structured_analysis.ai_model}</p>
                  <p className="text-sm text-gray-600">AI Analysis</p>
                </>
              ) : (
                <>
                  <p className="text-2xl font-bold text-indigo-600">{resume.analysis_enhanced ? 'Enhanced' : 'Basic'}</p>
                  <p className="text-sm text-gray-600">Analysis</p>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}