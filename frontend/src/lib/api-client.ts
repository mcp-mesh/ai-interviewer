import { Job, User, BackendJob, ApplicationStepData, ApplicationStatus, ApplicationReviewData, FileUploadResponse, FileStatus, JobFilters } from './types'

import { API_CONFIG } from './config'

// Use the centralized API configuration
const API_BASE_URL = API_CONFIG.baseUrl

console.log('API Base URL:', API_BASE_URL)

// Generic API client for making HTTP requests
class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: 'include', // Include cookies for session management
      ...options,
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        const error = new Error(errorData.detail || `HTTP error! status: ${response.status}`)
        ;(error as Error & { status?: number }).status = response.status
        throw error
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error('API request failed:', { url, error })
      throw error
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  async post<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async put<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }

  // For multipart/form-data requests (file uploads)
  async postForm<T>(endpoint: string, formData: FormData): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header for FormData, browser will set it automatically
      headers: {},
    })
  }
}

// Create API client instance
const apiClient = new ApiClient(API_BASE_URL)

// Response interfaces to match backend API structure
interface ApiResponse<T> {
  data: T
  success?: boolean
  total?: number
  page?: number
  limit?: number
}


// Helper function to map backend job format to frontend format
function mapBackendJobToFrontend(backendJob: BackendJob): Job {
  return {
    id: backendJob.id,
    title: backendJob.title,
    company: backendJob.company,
    location: backendJob.location,
    city: backendJob.city,
    state: backendJob.state,
    country: backendJob.country,
    type: backendJob.type,
    category: backendJob.category,
    remote: backendJob.remote,
    description: backendJob.description || '',
    short_description: backendJob.short_description,
    requirements: backendJob.requirements || [],
    benefits: backendJob.benefits || [],
    salaryRange: backendJob.salaryRange,
    matchScore: backendJob.matchScore,
    postedAt: backendJob.postedAt
  } as Job
}


// Jobs API - unified filtering approach
export const jobsApi = {
  // Primary method - always uses search endpoint
  getJobs: async (filters: JobFilters = {}, page = 1, limit = 20): Promise<{ data: Job[]; error?: string }> => {
    try {
      const queryParams = new URLSearchParams()
      
      // New multi-value filters
      if (filters.categories?.length) {
        queryParams.set('category', filters.categories.join(','))
      }
      if (filters.job_types?.length) {
        queryParams.set('job_type', filters.job_types.join(','))
      }
      if (filters.cities?.length) {
        queryParams.set('city', filters.cities.join(','))
      }
      if (filters.states?.length) {
        queryParams.set('state', filters.states.join(','))
      }
      if (filters.countries?.length) {
        queryParams.set('country', filters.countries.join(','))
      }
      
      // Legacy filters for backward compatibility
      if (filters.location) queryParams.set('location', filters.location)
      if (filters.type) queryParams.set('job_type', filters.type)
      if (filters.remote !== undefined) queryParams.set('remote', filters.remote.toString())
      
      queryParams.set('page', page.toString())
      queryParams.set('limit', limit.toString())
      
      const response = await apiClient.get<ApiResponse<BackendJob[]>>(
        `/jobs/search?${queryParams.toString()}`
      )
      
      // Map backend format to frontend format
      const mappedJobs = response.data.map(mapBackendJobToFrontend)
      
      return { data: mappedJobs }
    } catch (error) {
      console.error('Failed to fetch jobs:', error)
      return { data: [], error: 'Failed to fetch jobs' }
    }
  },

  // Legacy method - delegates to getJobs with applied job filtering
  getAll: async (filters?: JobFilters): Promise<{ data: Job[]; error?: string }> => {
    const result = await jobsApi.getJobs(filters || {})
    
    if (result.data && result.data.length > 0) {
      // Filter out jobs user has already applied to (internal filtering)
      try {
        const userData = localStorage.getItem('user')
        if (userData) {
          const user = JSON.parse(userData)
          if (user.applications && user.applications.length > 0) {
            const appliedJobIds = user.applications.map((app: { jobId: string }) => app.jobId)
            result.data = result.data.filter(job => !appliedJobIds.includes(job.id))
          }
        }
        // If no user (guest mode), return all jobs unchanged
      } catch (error) {
        console.error('Error filtering applied jobs:', error)
        // Return unfiltered jobs if filtering fails
      }
    }
    
    return result
  },

  getById: async (id: string): Promise<{ data: Job | null; error?: string }> => {
    try {
      const response = await apiClient.get<ApiResponse<BackendJob>>(`/jobs/${id}`)
      const mappedJob = mapBackendJobToFrontend(response.data)
      return { data: mappedJob }
    } catch (error) {
      console.error('Failed to fetch job:', error)
      return { data: null, error: 'Failed to fetch job' }
    }
  },

  getFeatured: async (): Promise<{ data: Job[]; error?: string }> => {
    try {
      // Use the unified getJobs method and filter featured on frontend
      const result = await jobsApi.getJobs({}, 1, 10)
      if (result.error) return result
      
      const featuredJobs = result.data.filter((job: Job) => (job as BackendJob).is_featured || job.isRecommended).slice(0, 3)
      return { data: featuredJobs }
    } catch (error) {
      console.error('Failed to fetch featured jobs:', error)
      return { data: [], error: 'Failed to fetch featured jobs' }
    }
  },

  getMatched: async (filters?: { location?: string; type?: string; remote?: boolean }): Promise<{ data: Job[]; error?: string }> => {
    try {
      // Use the unified getJobs method 
      const result = await jobsApi.getJobs(filters || {})
      if (result.error) return result
      
      // Filter for jobs with high match scores (when matching algorithm is implemented)
      // For now, return all jobs since matchScore is 0
      let matchedJobs = result.data.filter(job => job.matchScore === undefined || job.matchScore >= 0)
      
      // Filter out jobs user has already applied to (internal filtering)
      try {
        const userData = localStorage.getItem('user')
        if (userData) {
          const user = JSON.parse(userData)
          if (user.applications && user.applications.length > 0) {
            const appliedJobIds = user.applications.map((app: { jobId: string }) => app.jobId)
            matchedJobs = matchedJobs.filter(job => !appliedJobIds.includes(job.id))
          }
        }
        // If no user (guest mode), return all jobs unchanged
      } catch (error) {
        console.error('Error filtering applied jobs from matched jobs:', error)
        // Return unfiltered matched jobs if filtering fails
      }
      
      return { data: matchedJobs }
    } catch (error) {
      console.error('Failed to fetch matched jobs:', error)
      return { data: [], error: 'Failed to fetch matched jobs' }
    }
  },

  getFilters: async (): Promise<{ data: { categories: string[]; job_types: string[]; cities: string[]; states: string[]; countries: string[] } | null; error?: string }> => {
    try {
      const response = await apiClient.get<ApiResponse<{ categories: string[]; job_types: string[]; cities: string[]; states: string[]; countries: string[] }>>('/jobs/filters')
      return { data: response.data }
    } catch (error) {
      console.error('Failed to fetch job filters:', error)
      return { data: null, error: 'Failed to fetch job filters' }
    }
  }
}

// Applications API - matches our backend endpoints
export const applicationsApi = {
  // Start new application with job ID - returns application_id and step 1 prefill
  startApplication: async (jobId: string): Promise<{ data: { applicationId: string; prefillData?: Record<string, unknown>; currentStep?: number } | null; error?: string }> => {
    try {
      const response = await apiClient.post<{ success: boolean; message: string; data: { application_id: string; prefill_data?: Record<string, unknown>; target_step?: number }; timestamp: string }>(`/applications/new/steps/1`, { job_id: jobId })
      
      // Extract and transform the response to match frontend expectations
      return { 
        data: {
          applicationId: response.data.application_id,
          prefillData: response.data.prefill_data,
          currentStep: response.data.target_step || 1
        }
      }
    } catch (error) {
      console.error('Failed to start application:', error)
      return { data: null, error: 'Failed to start application' }
    }
  },

  // Save current step and get next step prefill
  saveStep: async (applicationId: string, stepNumber: number, stepData: ApplicationStepData): Promise<{ data: { success: boolean; message?: string; data?: Record<string, unknown>; timestamp?: string } | null; error?: string }> => {
    try {
      const response = await apiClient.post<{ success: boolean; message?: string; data?: Record<string, unknown>; timestamp?: string }>(`/applications/${applicationId}/steps/${stepNumber}`, { step_data: stepData })
      return { data: response }
    } catch (error) {
      console.error('Failed to save application step:', error)
      return { data: null, error: 'Failed to save application step' }
    }
  },

  // Get application status
  getStatus: async (applicationId: string): Promise<{ data: ApplicationStatus | null; error?: string }> => {
    try {
      const response = await apiClient.get<ApplicationStatus>(`/applications/${applicationId}/status`)
      return { data: response }
    } catch (error) {
      console.error('Failed to get application status:', error)
      return { data: null, error: 'Failed to get application status' }
    }
  },

  // Get complete review data for Step 6
  getReviewData: async (applicationId: string): Promise<{ data: ApplicationReviewData | null; error?: string }> => {
    try {
      const response = await apiClient.get<ApplicationReviewData>(`/applications/${applicationId}/review`)
      return { data: response }
    } catch (error) {
      console.error('Failed to get application review data:', error)
      return { data: null, error: 'Failed to get application review data' }
    }
  },

}

// User API - matches our backend endpoints
export const userApi = {
  getProfile: async (): Promise<{ data: User | null; error?: string }> => {
    try {
      const response = await apiClient.get<ApiResponse<User>>('/users/profile')
      return { data: response.data }
    } catch (error) {
      console.error('Failed to fetch user profile:', error)
      return { data: null, error: 'Failed to fetch user profile' }
    }
  },

  updateProfile: async (profileData: Partial<User['profile']>): Promise<{ data: User | null; error?: string }> => {
    try {
      const response = await apiClient.put<ApiResponse<User>>('/users/profile', { profile_data: profileData })
      return { data: response.data }
    } catch (error) {
      console.error('Failed to update profile:', error)
      return { data: null, error: 'Failed to update profile' }
    }
  }
}

// File API - for resume uploads
export const fileApi = {
  uploadResume: async (file: File, processWithAi = true): Promise<{ data: FileUploadResponse | null; error?: string }> => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('process_with_ai', processWithAi.toString())
      
      const response = await apiClient.postForm<FileUploadResponse>('/files/resume', formData)
      return { data: response }
    } catch (error) {
      console.error('Failed to upload resume:', error)
      return { data: null, error: 'Failed to upload resume' }
    }
  },

  getFileStatus: async (fileId: string): Promise<{ data: FileStatus | null; error?: string }> => {
    try {
      const response = await apiClient.get<ApiResponse<FileStatus>>(`/files/status/${fileId}`)
      return { data: response.data }
    } catch (error) {
      console.error('Failed to get file status:', error)
      return { data: null, error: 'Failed to get file status' }
    }
  }
}

// Interview API - matches our backend interview endpoints using nginx auth pattern  
export const interviewsApi = {
  // Start new interview
  startInterview: async (jobId: string, applicationId: string): Promise<{ data: any | null; error?: string }> => {
    try {
      const response = await apiClient.post<any>('/interviews/start', {
        job_id: jobId,
        application_id: applicationId
      })
      return { data: response }
    } catch (error: any) {
      console.error('Failed to start interview:', error)
      return { data: null, error: error.message || 'Failed to start interview' }
    }
  },

  // Get current question and session status
  getCurrentQuestion: async (sessionId: string): Promise<{ data: any | null; error?: string }> => {
    try {
      const response = await apiClient.get<any>(`/interviews/${sessionId}/current`)
      return { data: response }
    } catch (error: any) {
      console.error('Failed to get current question:', error)
      return { data: null, error: error.message || 'Failed to get current question' }
    }
  },

  // Submit answer (returns streaming response for SSE)
  submitAnswer: async (sessionId: string, answer: string): Promise<Response> => {
    // For streaming responses, we need to use fetch directly but with cookies
    const response = await fetch(`${API_BASE_URL}/interviews/${sessionId}/answer`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      credentials: 'include', // Use cookies for auth like other endpoints
      body: JSON.stringify({ answer })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to submit answer' }))
      throw new Error(errorData.detail || 'Failed to submit answer')
    }

    return response
  },

  // End interview session
  endInterview: async (sessionId: string, reason: string = 'user_requested'): Promise<{ data: any | null; error?: string }> => {
    try {
      const response = await apiClient.post<any>(`/interviews/${sessionId}/end`, { reason })
      return { data: response }
    } catch (error: any) {
      console.error('Failed to end interview:', error)
      return { data: null, error: error.message || 'Failed to end interview' }
    }
  },

  // Get interview status
  getStatus: async (): Promise<{ data: any | null; error?: string }> => {
    try {
      const response = await apiClient.get<any>('/interviews/status')
      return { data: response }
    } catch (error: any) {
      console.error('Failed to get interview status:', error)
      return { data: null, error: error.message || 'Failed to get interview status' }
    }
  },

  // Finalize interview scoring
  finalizeInterview: async (sessionId: string): Promise<{ data: any | null; error?: string }> => {
    try {
      const response = await apiClient.post<any>(`/interviews/${sessionId}/finalize`, {})
      return { data: response }
    } catch (error: any) {
      console.error('Failed to finalize interview:', error)
      return { data: null, error: error.message || 'Failed to finalize interview' }
    }
  }
}


export default apiClient