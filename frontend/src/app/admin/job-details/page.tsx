'use client'

import { useSearchParams, useRouter } from 'next/navigation'
import { useState, useEffect, Suspense } from 'react'
import Link from 'next/link'
import ReactMarkdown from 'react-markdown'
import { 
  ArrowLeft,
  User as UserIcon,
  Star,
  BarChart3,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  ArrowUp,
  ArrowDown,
  GraduationCap,
  Lightbulb,
  MessageSquare,
  Briefcase,
  AlertTriangle
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface JobData {
  job_id: string
  title: string
  description: string
  status: string
  created_at: string
  created_by: string
  updated_at?: string
  updated_by?: string
}

interface InterviewData {
  session_id: string
  candidate_name: string
  candidate_email: string
  interview_date: string
  overall_score: number
  technical_knowledge: number
  problem_solving: number
  communication: number
  experience_relevance: number
  hire_recommendation: string
  feedback: string
  completion_reason: string
  ended_at: string
  duration: number
}

interface JobStatistics {
  total_interviews: number
  average_score: number
  strong_yes_count: number
  yes_count: number
  hire_rate: number
}

interface JobDetailsResponse {
  job: JobData
  interviews: InterviewData[]
  statistics: JobStatistics
}

interface InterviewDetailsResponse {
  session_id: string
  candidate: {
    name: string
    email: string
    resume_info: Record<string, unknown>
  }
  interview: {
    started_at: string
    ended_at: string
    duration: number
    status: string
    completion_reason: string
  }
  job_info: {
    description: string
    requirements: string
  }
  conversation: Array<{
    type: string
    content: string
    timestamp: string
  }>
  evaluation: {
    overall_score: number
    technical_knowledge: number
    problem_solving: number
    communication: number
    experience_relevance: number
    hire_recommendation: string
    feedback: string
    evaluation_timestamp: string
  }
}

type SortField = 'candidate_name' | 'interview_date' | 'overall_score' | 'technical_knowledge' | 'problem_solving' | 'communication' | 'experience_relevance' | 'hire_recommendation'
type SortOrder = 'asc' | 'desc'

function JobDetailsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const jobId = searchParams.get('id')

  const [data, setData] = useState<JobDetailsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())
  const [sortField, setSortField] = useState<SortField>('interview_date')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')
  const [interviewDetails, setInterviewDetails] = useState<InterviewDetailsResponse | null>(null)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(false)

  useEffect(() => {
    if (jobId) {
      loadJobDetails()
    } else {
      setError('No job ID provided')
      setLoading(false)
    }
  }, [jobId])

  const loadJobDetails = async () => {
    if (!jobId) return

    try {
      setLoading(true)
      setError('')
      
      const response = await fetch(`/api/admin/jobs/${jobId}`, {
        credentials: 'include'
      })
      
      if (response.ok) {
        const jobData = await response.json()
        setData(jobData)
      } else if (response.status === 404) {
        setError('Job not found')
      } else {
        throw new Error('Failed to load job details')
      }
    } catch (err) {
      setError('Failed to load job details')
      console.error('Load job details error:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadInterviewDetails = async (sessionId: string) => {
    try {
      setLoadingDetails(true)
      const response = await fetch(`/api/interviews/${sessionId}/details`, {
        credentials: 'include'
      })
      
      if (response.ok) {
        const details = await response.json()
        setInterviewDetails(details)
      } else {
        throw new Error('Failed to load interview details')
      }
    } catch (err) {
      console.error('Load interview details error:', err)
    } finally {
      setLoadingDetails(false)
    }
  }

  const toggleRow = async (sessionId: string) => {
    const newExpandedRows = new Set(expandedRows)
    
    if (expandedRows.has(sessionId)) {
      newExpandedRows.delete(sessionId)
      setExpandedRows(newExpandedRows)
    } else {
      newExpandedRows.add(sessionId)
      setExpandedRows(newExpandedRows)
      await loadInterviewDetails(sessionId)
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

  const sortedInterviews = data?.interviews.slice().sort((a, b) => {
    let aValue: string | number = a[sortField]
    let bValue: string | number = b[sortField]
    
    if (sortField === 'interview_date') {
      aValue = new Date(aValue).getTime()
      bValue = new Date(bValue).getTime()
    }
    
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      aValue = aValue.toLowerCase()
      bValue = bValue.toLowerCase()
    }
    
    if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1
    if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1
    return 0
  }) || []

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return null
    return sortOrder === 'asc' ? 
      <ArrowUp className="w-4 h-4 ml-1 inline" /> : 
      <ArrowDown className="w-4 h-4 ml-1 inline" />
  }

  const getStatusBadge = (status: string) => {
    const statusClasses = {
      open: 'bg-green-100 text-green-800',
      closed: 'bg-red-100 text-red-800',
      on_hold: 'bg-yellow-100 text-yellow-800'
    }
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusClasses[status as keyof typeof statusClasses] || 'bg-gray-100 text-gray-800'}`}>
        {status.replace('_', ' ').toUpperCase()}
      </span>
    )
  }

  const getHireRecommendationBadge = (recommendation: string) => {
    const classes = {
      strong_yes: 'bg-green-100 text-green-800',
      yes: 'bg-blue-100 text-blue-800',
      maybe: 'bg-yellow-100 text-yellow-800',
      no: 'bg-red-100 text-red-800',
      strong_no: 'bg-red-100 text-red-800'
    }
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${classes[recommendation as keyof typeof classes] || 'bg-gray-100 text-gray-800'}`}>
        {recommendation.replace('_', ' ').toUpperCase()}
      </span>
    )
  }

  const getScoreColor = (score: number, max: number = 100) => {
    const percentage = (score / max) * 100
    if (percentage >= 80) return 'text-green-600'
    if (percentage >= 60) return 'text-yellow-600'
    return 'text-red-600'
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

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500" />
            <span className="text-gray-700">Loading job details...</span>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="bg-white border border-gray-200 rounded-xl p-6 text-center shadow-sm">
          <AlertTriangle className="mx-auto h-12 w-12 text-red-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Job</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={() => router.push('/admin')}>
            Back to Admin
          </Button>
        </div>
      </div>
    )
  }

  if (!data) {
    return null
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <Link 
                href="/admin"
                className="text-gray-600 hover:text-gray-900 flex items-center space-x-2"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>Back to Admin</span>
              </Link>
              <div className="h-4 w-px bg-gray-300" />
              <h1 className="text-xl font-bold text-gray-900">Job Details</h1>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Job Header */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6 shadow-sm hover:shadow-lg transition-all duration-200">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">{data.job.title}</h2>
              
              {/* Job Description with Collapse/Expand */}
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-3">
                  <h3 className="text-lg font-semibold text-gray-900">Job Description</h3>
                  <button
                    onClick={() => setIsDescriptionExpanded(!isDescriptionExpanded)}
                    className="flex items-center gap-1 px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors duration-200"
                  >
                    {isDescriptionExpanded ? (
                      <>
                        <ChevronUp className="w-4 h-4" />
                        Hide Details
                      </>
                    ) : (
                      <>
                        <ChevronDown className="w-4 h-4" />
                        Show Details
                      </>
                    )}
                  </button>
                </div>
                
                {isDescriptionExpanded && (
                  <div className="text-gray-600 text-base prose prose-base max-w-none">
                    <ReactMarkdown
                      components={{
                        h3: ({children}) => <h3 className="text-lg font-semibold text-gray-900 mt-4 mb-2">{children}</h3>,
                        h4: ({children}) => <h4 className="text-base font-medium text-gray-800 mt-3 mb-2">{children}</h4>,
                        ul: ({children}) => <ul className="list-disc list-inside space-y-1 mt-2 mb-3">{children}</ul>,
                        ol: ({children}) => <ol className="list-decimal list-inside space-y-1 mt-2 mb-3">{children}</ol>,
                        li: ({children}) => <li className="text-gray-600">{children}</li>,
                        strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
                        p: ({children}) => <p className="mb-3 text-gray-600 leading-relaxed">{children}</p>,
                        em: ({children}) => <em className="italic text-gray-700">{children}</em>
                      }}
                    >
                      {data.job.description}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
              <div className="flex items-center space-x-4">
                {getStatusBadge(data.job.status)}
                <span className="text-sm text-gray-500">
                  Created by {data.job.created_by} on {formatDate(data.job.created_at)}
                </span>
              </div>
            </div>
          </div>

          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center">
                <UserIcon className="h-8 w-8 text-blue-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-blue-900">Total Interviews</p>
                  <p className="text-2xl font-bold text-blue-600">{data.statistics.total_interviews}</p>
                </div>
              </div>
            </div>

            <div className="bg-yellow-50 rounded-lg p-4">
              <div className="flex items-center">
                <BarChart3 className="h-8 w-8 text-yellow-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-yellow-900">Average Score</p>
                  <p className="text-2xl font-bold text-yellow-600">{data.statistics.average_score}/100</p>
                </div>
              </div>
            </div>

            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center">
                <CheckCircle className="h-8 w-8 text-green-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-green-900">Hire Rate</p>
                  <p className="text-2xl font-bold text-green-600">{data.statistics.hire_rate}%</p>
                </div>
              </div>
            </div>

            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center">
                <Star className="h-8 w-8 text-purple-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-purple-900">Strong Hires</p>
                  <p className="text-2xl font-bold text-purple-600">{data.statistics.strong_yes_count + data.statistics.yes_count}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Interviews Table */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-lg transition-all duration-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Interview History</h3>
            <p className="text-sm text-gray-600 mt-1">Click on any row to view detailed feedback and conversation</p>
          </div>

          {sortedInterviews.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('candidate_name')}
                    >
                      Candidate {getSortIcon('candidate_name')}
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('interview_date')}
                    >
                      Interview Date {getSortIcon('interview_date')}
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('overall_score')}
                    >
                      Overall Score {getSortIcon('overall_score')}
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('technical_knowledge')}
                    >
                      Tech Knowledge {getSortIcon('technical_knowledge')}
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('problem_solving')}
                    >
                      Problem Solving {getSortIcon('problem_solving')}
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('communication')}
                    >
                      Communication {getSortIcon('communication')}
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('experience_relevance')}
                    >
                      Experience {getSortIcon('experience_relevance')}
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('hire_recommendation')}
                    >
                      Recommendation {getSortIcon('hire_recommendation')}
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {sortedInterviews.map((interview) => (
                    <>
                      <tr 
                        key={interview.session_id}
                        className="hover:bg-gray-50 cursor-pointer"
                        onClick={() => toggleRow(interview.session_id)}
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            {expandedRows.has(interview.session_id) ? 
                              <ChevronUp className="w-4 h-4 text-gray-400 mr-2" /> :
                              <ChevronDown className="w-4 h-4 text-gray-400 mr-2" />
                            }
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {interview.candidate_name}
                              </div>
                              <div className="text-sm text-gray-500">
                                {interview.candidate_email}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(interview.interview_date)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`text-sm font-bold ${getScoreColor(interview.overall_score)}`}>
                            {interview.overall_score}/100
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`text-sm ${getScoreColor(interview.technical_knowledge, 25)}`}>
                            {interview.technical_knowledge}/25
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`text-sm ${getScoreColor(interview.problem_solving, 25)}`}>
                            {interview.problem_solving}/25
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`text-sm ${getScoreColor(interview.communication, 25)}`}>
                            {interview.communication}/25
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`text-sm ${getScoreColor(interview.experience_relevance, 25)}`}>
                            {interview.experience_relevance}/25
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getHireRecommendationBadge(interview.hire_recommendation)}
                        </td>
                      </tr>

                      {/* Expanded Row Details */}
                      {expandedRows.has(interview.session_id) && (
                        <tr>
                          <td colSpan={8} className="px-6 py-4 bg-gray-50">
                            {loadingDetails ? (
                              <div className="flex items-center justify-center py-4">
                                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500" />
                                <span className="text-gray-600 ml-3">Loading interview details...</span>
                              </div>
                            ) : interviewDetails && interviewDetails.session_id === interview.session_id ? (
                              <div className="space-y-6">
                                {/* Detailed Scores */}
                                <div>
                                  <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                                    <BarChart3 className="w-4 h-4 mr-2" />
                                    Detailed Evaluation
                                  </h4>
                                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div className="flex items-center space-x-2">
                                      <GraduationCap className="w-5 h-5 text-blue-600" />
                                      <div>
                                        <p className="text-xs text-gray-500">Technical Knowledge</p>
                                        <p className="text-sm font-semibold text-gray-900">
                                          {interviewDetails.evaluation.technical_knowledge}/25
                                        </p>
                                      </div>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                      <Lightbulb className="w-5 h-5 text-yellow-600" />
                                      <div>
                                        <p className="text-xs text-gray-500">Problem Solving</p>
                                        <p className="text-sm font-semibold text-gray-900">
                                          {interviewDetails.evaluation.problem_solving}/25
                                        </p>
                                      </div>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                      <MessageSquare className="w-5 h-5 text-green-600" />
                                      <div>
                                        <p className="text-xs text-gray-500">Communication</p>
                                        <p className="text-sm font-semibold text-gray-900">
                                          {interviewDetails.evaluation.communication}/25
                                        </p>
                                      </div>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                      <Briefcase className="w-5 h-5 text-purple-600" />
                                      <div>
                                        <p className="text-xs text-gray-500">Experience</p>
                                        <p className="text-sm font-semibold text-gray-900">
                                          {interviewDetails.evaluation.experience_relevance}/25
                                        </p>
                                      </div>
                                    </div>
                                  </div>
                                </div>

                                {/* Feedback */}
                                <div>
                                  <h4 className="text-sm font-semibold text-gray-900 mb-2">Detailed Feedback</h4>
                                  <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
                                    <div className="text-sm text-gray-700 prose prose-sm max-w-none">
                                      <ReactMarkdown
                                        components={{
                                          h3: ({children}) => <h3 className="text-base font-semibold text-gray-900 mt-4 mb-2">{children}</h3>,
                                          h4: ({children}) => <h4 className="text-sm font-medium text-gray-800 mt-3 mb-1">{children}</h4>,
                                          ul: ({children}) => <ul className="list-disc list-inside space-y-1 mt-2">{children}</ul>,
                                          li: ({children}) => <li className="text-gray-700">{children}</li>,
                                          strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
                                          p: ({children}) => <p className="mb-2 text-gray-700">{children}</p>
                                        }}
                                      >
                                        {interviewDetails.evaluation.feedback}
                                      </ReactMarkdown>
                                    </div>
                                  </div>
                                </div>

                                {/* Interview Metadata */}
                                <div>
                                  <h4 className="text-sm font-semibold text-gray-900 mb-2">Interview Details</h4>
                                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                    <div>
                                      <p className="text-xs text-gray-500">Started</p>
                                      <p className="text-gray-900">{formatDate(interviewDetails.interview.started_at)}</p>
                                    </div>
                                    <div>
                                      <p className="text-xs text-gray-500">Duration</p>
                                      <p className="text-gray-900">{Math.round(interviewDetails.interview.duration / 60)} minutes</p>
                                    </div>
                                    <div>
                                      <p className="text-xs text-gray-500">Completion</p>
                                      <p className="text-gray-900">{interviewDetails.interview.completion_reason}</p>
                                    </div>
                                    <div>
                                      <p className="text-xs text-gray-500">Questions</p>
                                      <p className="text-gray-900">{interviewDetails.conversation.filter(c => c.type === 'question').length}</p>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            ) : null}
                          </td>
                        </tr>
                      )}
                    </>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12">
              <UserIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No interviews yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                No candidates have interviewed for this job yet.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function JobDetailsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500" />
            <span className="text-gray-700">Loading job details...</span>
          </div>
        </div>
      </div>
    }>
      <JobDetailsContent />
    </Suspense>
  )
}