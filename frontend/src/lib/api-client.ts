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

// Job filter interface
interface JobFilters {
  categories?: string[]
  job_types?: string[]
  cities?: string[]
  states?: string[]
  countries?: string[]
  // Legacy filters for backward compatibility
  location?: string
  type?: string
  remote?: boolean
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
      
      const response = await apiClient.get<ApiResponse<any[]>>(
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

  // Legacy method - delegates to getJobs
  getAll: async (filters?: { location?: string; type?: string; remote?: boolean }): Promise<{ data: Job[]; error?: string }> => {
    return jobsApi.getJobs(filters || {})
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
      // Use the unified getJobs method and filter featured on frontend
      const result = await jobsApi.getJobs({}, 1, 10)
      if (result.error) return result
      
      const featuredJobs = result.data.filter(job => job.is_featured).slice(0, 3)
      return { data: featuredJobs }
    } catch (error) {
      console.error('Failed to fetch featured jobs:', error)
      return { data: [], error: 'Failed to fetch featured jobs' }
    }
  },

  getMatched: async (userId: string, filters?: { location?: string; type?: string; remote?: boolean }): Promise<{ data: Job[]; error?: string }> => {
    try {
      // Use the unified getJobs method 
      const result = await jobsApi.getJobs(filters || {})
      if (result.error) return result
      
      // Filter for jobs with high match scores (when matching algorithm is implemented)
      // For now, return all jobs since matchScore is 0
      const matchedJobs = result.data.filter(job => job.matchScore === undefined || job.matchScore >= 0)
      
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
  startApplication: async (jobId: string): Promise<{ data: any | null; error?: string }> => {
    try {
      const response = await apiClient.post<any>(`/applications/new/steps/1`, { job_id: jobId })
      return { data: response }
    } catch (error) {
      console.error('Failed to start application:', error)
      return { data: null, error: 'Failed to start application' }
    }
  },

  // Save current step and get next step prefill
  saveStep: async (applicationId: string, stepNumber: number, stepData: any): Promise<{ data: any | null; error?: string }> => {
    try {
      const response = await apiClient.post<any>(`/applications/${applicationId}/steps/${stepNumber}`, { step_data: stepData })
      return { data: response }
    } catch (error) {
      console.error('Failed to save application step:', error)
      return { data: null, error: 'Failed to save application step' }
    }
  },

  // Get application status
  getStatus: async (applicationId: string): Promise<{ data: any | null; error?: string }> => {
    try {
      const response = await apiClient.get<any>(`/applications/${applicationId}/status`)
      return { data: response }
    } catch (error) {
      console.error('Failed to get application status:', error)
      return { data: null, error: 'Failed to get application status' }
    }
  },

  // Get complete review data for Step 6
  getReviewData: async (applicationId: string): Promise<{ data: any | null; error?: string }> => {
    try {
      const response = await apiClient.get<any>(`/applications/${applicationId}/review`)
      return { data: response }
    } catch (error) {
      console.error('Failed to get application review data:', error)
      return { data: null, error: 'Failed to get application review data' }
    }
  },

  // Legacy methods for backward compatibility (can be removed later)
  create: async (jobId: string, userId: string, coverLetter: string, additionalInfo?: any): Promise<{ data: Application | null; error?: string }> => {
    console.warn('applicationsApi.create is deprecated, use startApplication instead')
    return { data: null, error: 'Method deprecated' }
  },

  getByUserId: async (userId: string): Promise<{ data: Application[]; error?: string }> => {
    console.warn('applicationsApi.getByUserId is deprecated')
    return { data: [], error: 'Method deprecated' }
  },

  updateStatus: async (id: string, status: Application['status']): Promise<{ data: Application | null; error?: string }> => {
    console.warn('applicationsApi.updateStatus is deprecated')
    return { data: null, error: 'Method deprecated' }
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