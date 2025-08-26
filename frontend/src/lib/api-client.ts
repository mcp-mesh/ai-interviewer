import { Job, User, Application, Interview } from './types'

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
        ;(error as any).status = response.status
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

interface ApiErrorResponse {
  detail: string
  success: false
}

// Helper function to map backend job format to frontend format
function mapBackendJobToFrontend(backendJob: any): Job {
  return {
    id: backendJob.id,
    title: backendJob.title,
    company: backendJob.company,
    location: backendJob.location,
    type: backendJob.type,
    category: backendJob.category,
    remote: backendJob.remote,
    description: backendJob.description || '',
    requirements: backendJob.requirements || [],
    benefits: backendJob.benefits || [],
    salaryRange: backendJob.salaryRange,
    matchScore: backendJob.matchScore,
    postedAt: backendJob.postedAt
  } as Job
}

// Jobs API - matches our backend endpoints
export const jobsApi = {
  getAll: async (filters?: { location?: string; type?: string; remote?: boolean }): Promise<{ data: Job[]; error?: string }> => {
    try {
      const queryParams = new URLSearchParams()
      if (filters?.location) queryParams.append('location', filters.location)
      if (filters?.type) queryParams.append('job_type', filters.type)
      if (filters?.remote !== undefined) queryParams.append('remote', filters.remote.toString())
      
      const endpoint = `/jobs${queryParams.toString() ? '?' + queryParams.toString() : ''}`
      const response = await apiClient.get<ApiResponse<any[]>>(endpoint)
      
      // Map backend format to frontend format
      const mappedJobs = response.data.map(mapBackendJobToFrontend)
      
      return { data: mappedJobs }
    } catch (error) {
      console.error('Failed to fetch jobs:', error)
      return { data: [], error: 'Failed to fetch jobs' }
    }
  },

  getById: async (id: string): Promise<{ data: Job | null; error?: string }> => {
    try {
      const response = await apiClient.get<ApiResponse<any>>(`/jobs/${id}`)
      const mappedJob = mapBackendJobToFrontend(response.data)
      return { data: mappedJob }
    } catch (error) {
      console.error('Failed to fetch job:', error)
      return { data: null, error: 'Failed to fetch job' }
    }
  },

  getFeatured: async (): Promise<{ data: Job[]; error?: string }> => {
    try {
      // For now, get all jobs and filter featured on the frontend
      // Backend could implement a /jobs/featured endpoint later
      const response = await apiClient.get<ApiResponse<any[]>>('/jobs')
      const mappedJobs = response.data.map(mapBackendJobToFrontend)
      const featuredJobs = mappedJobs.filter(job => job.is_featured).slice(0, 3)
      
      return { data: featuredJobs }
    } catch (error) {
      console.error('Failed to fetch featured jobs:', error)
      return { data: [], error: 'Failed to fetch featured jobs' }
    }
  },

  getMatched: async (userId: string, filters?: { location?: string; type?: string; remote?: boolean }): Promise<{ data: Job[]; error?: string }> => {
    try {
      // Backend could implement a /jobs/matched endpoint later
      // For now, get all jobs - they should include matchScore from backend
      const queryParams = new URLSearchParams()
      if (filters?.location) queryParams.append('location', filters.location)
      if (filters?.type) queryParams.append('job_type', filters.type)
      if (filters?.remote !== undefined) queryParams.append('remote', filters.remote.toString())
      
      const endpoint = `/jobs${queryParams.toString() ? '?' + queryParams.toString() : ''}`
      const response = await apiClient.get<ApiResponse<any[]>>(endpoint)
      
      const mappedJobs = response.data.map(mapBackendJobToFrontend)
      // Filter for jobs with high match scores
      const matchedJobs = mappedJobs.filter(job => job.matchScore && job.matchScore > 70)
      
      return { data: matchedJobs }
    } catch (error) {
      console.error('Failed to fetch matched jobs:', error)
      return { data: [], error: 'Failed to fetch matched jobs' }
    }
  }
}

// Applications API - matches our backend endpoints
export const applicationsApi = {
  create: async (jobId: string, userId: string, coverLetter: string, additionalInfo?: any): Promise<{ data: Application | null; error?: string }> => {
    try {
      const applicationData = {
        job_id: jobId,
        notes: coverLetter,
        cover_letter: coverLetter,
        additional_info: additionalInfo
      }
      
      const response = await apiClient.post<ApiResponse<Application>>('/applications', applicationData)
      return { data: response.data }
    } catch (error) {
      console.error('Failed to create application:', error)
      return { data: null, error: 'Failed to create application' }
    }
  },

  getByUserId: async (userId: string): Promise<{ data: Application[]; error?: string }> => {
    try {
      const response = await apiClient.get<ApiResponse<Application[]>>('/applications')
      return { data: response.data }
    } catch (error) {
      console.error('Failed to fetch applications:', error)
      return { data: [], error: 'Failed to fetch applications' }
    }
  },

  updateStatus: async (id: string, status: Application['status']): Promise<{ data: Application | null; error?: string }> => {
    try {
      const response = await apiClient.put<ApiResponse<Application>>(`/applications/${id}/status`, { status })
      return { data: response.data }
    } catch (error) {
      console.error('Failed to update application status:', error)
      return { data: null, error: 'Failed to update application status' }
    }
  }
}

// User API - matches our backend endpoints
export const userApi = {
  getProfile: async (userId?: string): Promise<{ data: User | null; error?: string }> => {
    try {
      const response = await apiClient.get<ApiResponse<User>>('/users/profile')
      return { data: response.data }
    } catch (error) {
      console.error('Failed to fetch user profile:', error)
      return { data: null, error: 'Failed to fetch user profile' }
    }
  },

  updateProfile: async (userId: string, profileData: Partial<User['profile']>): Promise<{ data: User | null; error?: string }> => {
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
  uploadResume: async (file: File, processWithAi = true): Promise<{ data: any | null; error?: string }> => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('process_with_ai', processWithAi.toString())
      
      const response = await apiClient.postForm<any>('/files/resume', formData)
      return { data: response }
    } catch (error) {
      console.error('Failed to upload resume:', error)
      return { data: null, error: 'Failed to upload resume' }
    }
  },

  getFileStatus: async (fileId: string): Promise<{ data: any | null; error?: string }> => {
    try {
      const response = await apiClient.get<ApiResponse<any>>(`/files/status/${fileId}`)
      return { data: response.data }
    } catch (error) {
      console.error('Failed to get file status:', error)
      return { data: null, error: 'Failed to get file status' }
    }
  }
}

// Auth API - OAuth handled by nginx, session-based auth
export const authApi = {
  login: async (email: string, password: string): Promise<{ data: { user: User; token: string } | null; error?: string }> => {
    // For Phase 2, OAuth is handled by nginx, not direct login
    // This would redirect to OAuth provider or return error
    return { data: null, error: 'Direct login not implemented - use OAuth' }
  },

  oauthLogin: async (provider: 'google' | 'github'): Promise<{ data: { user: User; token: string } | null; error?: string }> => {
    // OAuth is handled by nginx - this would redirect to the OAuth endpoint
    window.location.href = `/auth/${provider}`
    return { data: null } // Won't actually return since page redirects
  },

  register: async (name: string, email: string, password: string): Promise<{ data: { user: User; token: string } | null; error?: string }> => {
    // For Phase 2, registration is handled via OAuth, not direct registration
    return { data: null, error: 'Direct registration not implemented - use OAuth' }
  }
}

// Interviews API - placeholder for future implementation
export const interviewsApi = {
  getByApplicationId: async (applicationId: string): Promise<{ data: Interview | null; error?: string }> => {
    // Placeholder - backend doesn't have interview endpoints yet
    return { data: null, error: 'Interviews API not implemented yet' }
  },

  create: async (applicationId: string, scheduledAt: string): Promise<{ data: Interview | null; error?: string }> => {
    // Placeholder - backend doesn't have interview endpoints yet
    return { data: null, error: 'Interviews API not implemented yet' }
  }
}

export default apiClient