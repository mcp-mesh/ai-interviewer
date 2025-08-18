'use client'

import { useSearchParams, useRouter } from 'next/navigation'
import { useState, useEffect, Suspense } from 'react'
import { 
  ArrowLeftIcon,
  UserIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  ChevronDownIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline'

interface UserProfile {
  email: string
  name: string
  admin: boolean
  blocked?: boolean
  created_at: string
  last_login: string
  provider: string
  notes?: string
}

interface Interview {
  session_id: string
  role_id: string
  role_title: string
  started_at: string
  ended_at?: string
  status: string
  questions_asked: number
  total_score: number
  duration_minutes: number
  completion_reason?: string
}

interface UserInterviewsResponse {
  user: UserProfile
  interviews: Interview[]
}

type SortField = 'started_at' | 'role_title' | 'status' | 'total_score'
type SortOrder = 'asc' | 'desc'

function UserInterviewsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const userEmail = searchParams.get('id')

  const [data, setData] = useState<UserInterviewsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())
  const [sortField, setSortField] = useState<SortField>('started_at')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')

  const loadUserInterviews = async () => {
    if (!userEmail) {
      setError('User email is required')
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError('')
      
      // Get user profile first
      const userResponse = await fetch(`/api/admin/users`, {
        credentials: 'include'
      })
      
      if (!userResponse.ok) {
        throw new Error('Failed to load user data')
      }
      
      const userData = await userResponse.json()
      const user = userData.users?.find((u: UserProfile) => u.email === userEmail)
      
      if (!user) {
        throw new Error('User not found')
      }
      
      // Get user interviews
      const interviewsResponse = await fetch(`/api/admin/users/${encodeURIComponent(userEmail)}/interviews`, {
        credentials: 'include'
      })
      
      if (interviewsResponse.ok) {
        const interviewsData = await interviewsResponse.json()
        setData({
          user,
          interviews: interviewsData.interviews || []
        })
      } else if (interviewsResponse.status === 404) {
        setError('User not found')
      } else {
        throw new Error('Failed to load user interviews')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load user interviews')
      console.error('Load user interviews error:', err)
    } finally {
      setLoading(false)
    }
  }

  const resetUserInterview = async (roleId: string) => {
    if (!userEmail || !confirm('Allow this user to retake the interview for this role?')) {
      return
    }

    try {
      const response = await fetch(`/api/admin/users/${encodeURIComponent(userEmail)}/reset-interview/${roleId}`, {
        method: 'POST',
        credentials: 'include'
      })

      if (response.ok) {
        alert('User can now retake the interview for this role')
        loadUserInterviews() // Reload data
      } else {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to reset interview')
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to reset interview')
      console.error('Reset interview error:', error)
    }
  }

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortOrder('desc')
    }
  }

  const toggleRow = (sessionId: string) => {
    const newExpandedRows = new Set(expandedRows)
    if (expandedRows.has(sessionId)) {
      newExpandedRows.delete(sessionId)
    } else {
      newExpandedRows.add(sessionId)
    }
    setExpandedRows(newExpandedRows)
  }

  useEffect(() => {
    loadUserInterviews()
  }, [userEmail])

  if (!userEmail) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-500" />
          <h1 className="mt-4 text-xl font-semibold text-gray-900">User ID Required</h1>
          <p className="mt-2 text-gray-600">Please provide a valid user ID to view interviews.</p>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading user interviews...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-500" />
          <h1 className="mt-4 text-xl font-semibold text-gray-900">Error</h1>
          <p className="mt-2 text-gray-600">{error}</p>
          <button
            onClick={() => router.push('/admin')}
            className="mt-4 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
          >
            Back to Admin
          </button>
        </div>
      </div>
    )
  }

  if (!data) return null

  const sortedInterviews = [...data.interviews].sort((a, b) => {
    let aValue = a[sortField]
    let bValue = b[sortField]

    if (sortField === 'started_at') {
      aValue = new Date(aValue).getTime()
      bValue = new Date(bValue).getTime()
    }

    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return sortOrder === 'asc' 
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue)
    }

    return sortOrder === 'asc' 
      ? (aValue as number) - (bValue as number)
      : (bValue as number) - (aValue as number)
  })

  const getStatusBadge = (status: string) => {
    const statusClasses = {
      completed: 'bg-green-100 text-green-800',
      active: 'bg-blue-100 text-blue-800',
      expired: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-100 text-gray-800'
    }
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusClasses[status as keyof typeof statusClasses] || 'bg-gray-100 text-gray-800'}`}>
        {status.toUpperCase()}
      </span>
    )
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return null
    return sortOrder === 'asc' ? '↑' : '↓'
  }

  const getUserStatusBadge = () => {
    const badges = []
    
    if (data.user.admin) {
      badges.push(
        <span key="admin" className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
          ADMIN
        </span>
      )
    }
    
    if (data.user.blocked) {
      badges.push(
        <span key="blocked" className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          <XCircleIcon className="h-3 w-3 mr-1" />
          BLOCKED
        </span>
      )
    } else {
      badges.push(
        <span key="active" className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          <CheckCircleIcon className="h-3 w-3 mr-1" />
          ACTIVE
        </span>
      )
    }
    
    badges.push(
      <span key="provider" className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
        {data.user.provider.toUpperCase()}
      </span>
    )
    
    return badges
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/admin')}
                className="flex items-center text-gray-600 hover:text-gray-900"
              >
                <ArrowLeftIcon className="h-5 w-5 mr-2" />
                Back to Admin
              </button>
              <div className="h-6 border-l border-gray-300"></div>
              <div className="flex items-center space-x-3">
                <UserIcon className="h-8 w-8 text-gray-400" />
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">{data.user.name}</h1>
                  <p className="text-sm text-gray-600">{data.user.email}</p>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {getUserStatusBadge()}
            </div>
          </div>
        </div>
      </div>

      {/* User Stats */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ClockIcon className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Interviews</p>
                <p className="text-2xl font-semibold text-gray-900">{data.interviews.length}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CheckCircleIcon className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Completed</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {data.interviews.filter(i => i.status === 'completed').length}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <span className="text-yellow-600 font-semibold text-sm">AVG</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Average Score</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {data.interviews.length > 0 
                    ? Math.round(data.interviews.reduce((sum, i) => sum + i.total_score, 0) / data.interviews.length)
                    : 0}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ClockIcon className="h-8 w-8 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Last Login</p>
                <p className="text-sm font-semibold text-gray-900">
                  {formatDate(data.user.last_login)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Interviews Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Interview History</h2>
          </div>
          
          {data.interviews.length === 0 ? (
            <div className="text-center py-12">
              <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No interviews yet</h3>
              <p className="mt-1 text-sm text-gray-500">This user hasn&apos;t taken any interviews yet.</p>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="w-8 px-6 py-3"></th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('role_title')}
                  >
                    Role {getSortIcon('role_title')}
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('started_at')}
                  >
                    Date {getSortIcon('started_at')}
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('status')}
                  >
                    Status {getSortIcon('status')}
                  </th>
                  <th 
                    className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('total_score')}
                  >
                    Score {getSortIcon('total_score')}
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Questions
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sortedInterviews.map((interview) => (
                  <>
                    <tr key={interview.session_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => toggleRow(interview.session_id)}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          {expandedRows.has(interview.session_id) ? (
                            <ChevronDownIcon className="h-4 w-4" />
                          ) : (
                            <ChevronRightIcon className="h-4 w-4" />
                          )}
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {interview.role_title}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(interview.started_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(interview.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span className="text-lg font-semibold text-gray-900">
                          {interview.total_score}
                        </span>
                        <span className="text-sm text-gray-500">/100</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                        {interview.questions_asked}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                        {interview.duration_minutes} min
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => resetUserInterview(interview.role_id)}
                          className="text-blue-600 hover:text-blue-900 flex items-center space-x-1 ml-auto"
                          title="Allow Retake"
                        >
                          <ArrowPathIcon className="h-4 w-4" />
                          <span>Reset</span>
                        </button>
                      </td>
                    </tr>
                    {expandedRows.has(interview.session_id) && (
                      <tr key={`${interview.session_id}-expanded`}>
                        <td colSpan={8} className="px-6 py-4 bg-gray-50">
                          <div className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                              <div>
                                <h4 className="text-sm font-medium text-gray-900 mb-2">Interview Details</h4>
                                <dl className="space-y-1 text-sm">
                                  <div className="flex justify-between">
                                    <dt className="text-gray-500">Session ID:</dt>
                                    <dd className="text-gray-900 font-mono text-xs">{interview.session_id}</dd>
                                  </div>
                                  <div className="flex justify-between">
                                    <dt className="text-gray-500">Started:</dt>
                                    <dd className="text-gray-900">{formatDate(interview.started_at)}</dd>
                                  </div>
                                  {interview.ended_at && (
                                    <div className="flex justify-between">
                                      <dt className="text-gray-500">Ended:</dt>
                                      <dd className="text-gray-900">{formatDate(interview.ended_at)}</dd>
                                    </div>
                                  )}
                                </dl>
                              </div>
                              <div>
                                <h4 className="text-sm font-medium text-gray-900 mb-2">Performance</h4>
                                <dl className="space-y-1 text-sm">
                                  <div className="flex justify-between">
                                    <dt className="text-gray-500">Total Score:</dt>
                                    <dd className="text-gray-900 font-semibold">{interview.total_score}/100</dd>
                                  </div>
                                  <div className="flex justify-between">
                                    <dt className="text-gray-500">Questions Asked:</dt>
                                    <dd className="text-gray-900">{interview.questions_asked}</dd>
                                  </div>
                                  <div className="flex justify-between">
                                    <dt className="text-gray-500">Duration:</dt>
                                    <dd className="text-gray-900">{interview.duration_minutes} minutes</dd>
                                  </div>
                                </dl>
                              </div>
                              <div>
                                <h4 className="text-sm font-medium text-gray-900 mb-2">Status Info</h4>
                                <dl className="space-y-1 text-sm">
                                  <div className="flex justify-between">
                                    <dt className="text-gray-500">Status:</dt>
                                    <dd>{getStatusBadge(interview.status)}</dd>
                                  </div>
                                  {interview.completion_reason && (
                                    <div className="flex justify-between">
                                      <dt className="text-gray-500">Completion:</dt>
                                      <dd className="text-gray-900 capitalize">{interview.completion_reason}</dd>
                                    </div>
                                  )}
                                </dl>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}

export default function UserInterviewsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      </div>
    }>
      <UserInterviewsContent />
    </Suspense>
  )
}