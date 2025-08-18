'use client'

import { useState, useEffect } from 'react'
import { 
  UserCircleIcon, 
  DocumentArrowUpIcon, 
  PlayIcon, 
  ClockIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowRightIcon,
  ChevronDownIcon,
  CogIcon
} from '@heroicons/react/24/outline'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

interface UserData {
  user_id: string
  email: string
  name: string
  admin?: boolean
  resume?: {
    filename: string
    uploaded_at: string
    structured_analysis?: {
      ai_provider?: string
      ai_model?: string
    }
    analysis_enhanced?: boolean
  }
  current_setup?: {
    status: string
  }
}

interface Role {
  role_id: string
  title: string
  description: string
  short_description?: string
  duration: number
}

export default function Dashboard() {
  const router = useRouter()
  const [userData, setUserData] = useState<UserData | null>(null)
  const [roles, setRoles] = useState<Role[]>([])
  const [selectedRole, setSelectedRole] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [isStartingInterview, setIsStartingInterview] = useState(false)
  const [showRoleDropdown, setShowRoleDropdown] = useState(false)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    // Use session-based authentication instead of localStorage tokens
    fetchUserData()
    fetchRoles()
  }, [])

  const fetchUserData = async () => {
    try {
      const response = await fetch('/api/user/profile', {
        credentials: 'include', // Use session cookies
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
      router.push('/')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchRoles = async () => {
    try {
      const response = await fetch('/api/roles', {
        credentials: 'include', // Use session cookies
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setRoles(data.roles || [])
      }
    } catch (error) {
      console.error('Error fetching roles:', error)
    }
  }

  const handleStartInterview = async () => {
    if (!selectedRole) return
    
    console.log('🔍 DEBUG: Starting interview with role:', selectedRole)
    setIsStartingInterview(true)
    setError('')
    
    try {
      const response = await fetch('/api/interviews/start', {
        method: 'POST',
        credentials: 'include', // Use session cookies
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ role_id: selectedRole })
      })
      
      console.log('🔍 DEBUG: Interview start response status:', response.status)
      
      if (response.status === 409) {
        // Interview already completed for this role
        await response.json().catch(() => ({})) // Consume response body
        setError('You have already completed the interview for this role. You cannot retake this interview.')
        return
      }
      
      if (response.status === 410) {
        // Session expired
        await response.json().catch(() => ({})) // Consume response body
        setError('Your previous interview session has expired. Please try starting a new interview.')
        return
      }
      
      if (response.ok) {
        const data = await response.json()
        console.log('🔍 DEBUG: Interview start response data:', data)
        
        if (data.resumed) {
          // Resuming existing session
          console.log('🔍 DEBUG: Resuming existing interview session')
          router.push(`/interview?session=${data.session_id}&resumed=true`)
        } else {
          // New session
          console.log('🔍 DEBUG: Starting new interview session:', data.session_id)
          router.push(`/interview?session=${data.session_id}`)
        }
      } else {
        const errorData = await response.json().catch(() => ({}))
        console.error('🔍 DEBUG: Interview start error:', errorData)
        setError(errorData.detail || 'Failed to start interview. Please try again.')
      }
    } catch (error) {
      console.error('🔍 DEBUG: Exception starting interview:', error)
      setError('Network error. Please check your connection and try again.')
    } finally {
      setIsStartingInterview(false)
    }
  }

  const handleLogout = async () => {
    try {
      // Call logout endpoint to clear server-side session
      await fetch('/logout', {
        method: 'POST',
        credentials: 'include'
      })
    } catch (error) {
      console.error('Logout error:', error)
    }
    
    // No localStorage to clear in session-based auth
    router.push('/')
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  const hasResume = userData?.resume?.filename
  const canStartInterview = hasResume && selectedRole

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link href="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-2 rounded-lg">
                <UserCircleIcon className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-xl font-bold text-gray-900">AI Interviewer</h1>
            </Link>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center">
                  <span className="text-white font-semibold text-sm">
                    {userData?.name?.charAt(0) || 'U'}
                  </span>
                </div>
                <div className="hidden sm:block">
                  <p className="text-sm font-medium text-gray-900">{userData?.name}</p>
                  <p className="text-xs text-gray-500">{userData?.email}</p>
                </div>
              </div>
              {userData?.admin === true && (
                <Link 
                  href="/admin"
                  className="text-purple-600 hover:text-purple-900 font-medium flex items-center space-x-1"
                >
                  <CogIcon className="h-4 w-4" />
                  <span>Admin</span>
                </Link>
              )}
              <button
                onClick={handleLogout}
                className="text-gray-600 hover:text-gray-900 font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome back, {userData?.name?.split(' ')[0]}!</h1>
          <p className="text-lg text-gray-600">Ready to join our team of exceptional talent? Let&apos;s showcase your skills and find your perfect role.</p>
        </div>

        {/* Setup Steps */}
        <div className="space-y-6">
          {/* Step 1: Resume Upload OR View Profile */}
          {!hasResume ? (
            /* Upload Resume */
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-start space-x-4">
                <div className="w-10 h-10 rounded-full flex items-center justify-center bg-gray-100">
                  <DocumentArrowUpIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Upload Your Resume</h3>
                  <p className="text-gray-600 mb-4">Upload your resume so we can generate personalized interview questions.</p>
                  <Link 
                    href="/upload"
                    className="inline-flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <DocumentArrowUpIcon className="h-4 w-4" />
                    <span>Upload Resume</span>
                  </Link>
                </div>
              </div>
            </div>
          ) : (
            /* View Profile */
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-start space-x-4">
                <div className="w-10 h-10 rounded-full flex items-center justify-center bg-green-100">
                  <CheckCircleIcon className="h-6 w-6 text-green-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">View Your Profile</h3>
                  <p className="text-gray-600 mb-4">
                    Review your structured resume data and upload details that will be used for personalized interviews.
                  </p>
                  
                  <div className="text-sm text-gray-500 mb-4">
                    <p><span className="font-medium">Resume:</span> {userData.resume?.filename}</p>
                    <p><span className="font-medium">Uploaded:</span> {userData.resume?.uploaded_at ? new Date(userData.resume.uploaded_at).toLocaleDateString() : 'Unknown'}</p>
                    {userData.resume?.structured_analysis?.ai_provider && userData.resume?.structured_analysis?.ai_model && (
                      <p><span className="font-medium">Analyzed by:</span> 
                        <span className="text-green-700 font-semibold capitalize"> {userData.resume.structured_analysis.ai_provider}</span>
                        <span className="text-gray-400 ml-1">({userData.resume.structured_analysis.ai_model})</span>
                      </p>
                    )}
                  </div>
                  
                  <Link 
                    href="/profile"
                    className="inline-flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <UserCircleIcon className="h-4 w-4" />
                    <span>View Your Profile</span>
                  </Link>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Select Role */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-start space-x-4">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${selectedRole ? 'bg-green-100' : 'bg-gray-100'}`}>
                {selectedRole ? (
                  <CheckCircleIcon className="h-6 w-6 text-green-600" />
                ) : (
                  <UserCircleIcon className="h-6 w-6 text-gray-400" />
                )}
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Select Interview Role</h3>
                <p className="text-gray-600 mb-4">Choose the position you want to practice interviewing for.</p>
                
                <div className="relative">
                  <button
                    onClick={() => setShowRoleDropdown(!showRoleDropdown)}
                    className="w-full max-w-xl bg-white border border-gray-300 rounded-lg px-4 py-3 text-left flex items-center justify-between hover:border-gray-400 transition-colors"
                  >
                    <div className={selectedRole ? 'text-gray-900' : 'text-gray-500'}>
                      {selectedRole ? (
                        <>
                          <div className="font-medium">{roles.find(r => r.role_id === selectedRole)?.title}</div>
                          <div className="text-xs text-blue-600">{roles.find(r => r.role_id === selectedRole)?.duration} minutes</div>
                        </>
                      ) : (
                        'Select a role...'
                      )}
                    </div>
                    <ChevronDownIcon className="h-5 w-5 text-gray-400" />
                  </button>
                  
                  {showRoleDropdown && (
                    <div className="absolute z-10 mt-1 w-full max-w-xl bg-white border border-gray-300 rounded-lg shadow-lg">
                      {roles.map((role) => (
                        <button
                          key={role.role_id}
                          onClick={() => {
                            console.log('🔍 DEBUG: Role clicked:', role.role_id, role.title)
                            setSelectedRole(role.role_id)
                            setShowRoleDropdown(false)
                            console.log('🔍 DEBUG: Role selection updated')
                          }}
                          className="w-full px-4 py-3 text-left hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg"
                        >
                          <div className="font-medium text-gray-900">{role.title}</div>
                          <div className="text-sm text-gray-500">
                            {role.short_description || role.description}
                          </div>
                          <div className="text-xs text-blue-600 mt-1">{role.duration} minutes</div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Step 3: Start Interview */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-start space-x-4">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${canStartInterview ? 'bg-blue-100' : 'bg-gray-100'}`}>
                <PlayIcon className={`h-6 w-6 ${canStartInterview ? 'text-blue-600' : 'text-gray-400'}`} />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Start Your Interview</h3>
                <p className="text-gray-600 mb-4">
                  Begin your interview with personalized questions based on your resume and role.
                </p>
                
                {!canStartInterview && (
                  <div className="flex items-center space-x-2 text-amber-700 bg-amber-50 p-3 rounded-lg mb-4">
                    <ExclamationTriangleIcon className="h-4 w-4" />
                    <span className="text-sm">Complete the steps above to start your interview</span>
                  </div>
                )}

                {error && (
                  <div className="flex items-center space-x-2 text-red-700 bg-red-50 p-3 rounded-lg mb-4 border border-red-200">
                    <ExclamationTriangleIcon className="h-4 w-4" />
                    <span className="text-sm">{error}</span>
                  </div>
                )}
                
                <button
                  onClick={handleStartInterview}
                  disabled={!canStartInterview || isStartingInterview}
                  className={`inline-flex items-center space-x-2 px-6 py-3 rounded-lg transition-colors ${
                    canStartInterview 
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700' 
                      : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  {isStartingInterview ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Starting Interview...</span>
                    </>
                  ) : (
                    <>
                      <PlayIcon className="h-4 w-4" />
                      <span>Start Interview</span>
                      <ArrowRightIcon className="h-4 w-4" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Interview Info */}
        <div className="mt-12 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Interview Format</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center space-x-3">
              <ClockIcon className="h-6 w-6 text-blue-600" />
              <div>
                <p className="font-medium text-gray-900">{selectedRole ? `${roles.find(r => r.role_id === selectedRole)?.duration || 30} Minutes` : 'Role-Based'}</p>
                <p className="text-sm text-gray-600">Duration varies by role</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <UserCircleIcon className="h-6 w-6 text-indigo-600" />
              <div>
                <p className="font-medium text-gray-900">AI-Powered</p>
                <p className="text-sm text-gray-600">Intelligent questions</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <CheckCircleIcon className="h-6 w-6 text-green-600" />
              <div>
                <p className="font-medium text-gray-900">Real-time Feedback</p>
                <p className="text-sm text-gray-600">Instant analysis</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}