import { Job, User, Application, Interview } from './types'
import { mockJobs, mockUsers, mockApplications, mockInterviews, mockApiResponse, mockApiError } from './mock-data'
import { API_CONFIG } from './config'
import * as realApi from './api-client'

// Auth API - uses real API or mock based on configuration
export const authApi = API_CONFIG.mode === 'real' ? realApi.authApi : {
  login: async (email: string, password: string): Promise<{ data: { user: User; token: string } | null; error?: string }> => {
    try {
      // Simple mock authentication
      const user = mockUsers.find(u => u.email === email)
      if (user && password === 'password') {
        const response = await mockApiResponse({ 
          user, 
          token: `mock-token-${user.id}` 
        })
        return { data: response.data }
      } else {
        const errorResponse = await mockApiError('Invalid credentials')
        return { data: null, error: errorResponse.error }
      }
    } catch (error) {
      return { data: null, error: 'Login failed' }
    }
  },

  oauthLogin: async (provider: 'google' | 'github'): Promise<{ data: { user: User; token: string } | null; error?: string }> => {
    try {
      // Mock OAuth flow - simulate successful authentication
      const mockOAuthUser: User = {
        id: `oauth-${provider}-${Date.now()}`,
        name: provider === 'google' ? 'John Doe' : 'GitHub User',
        email: provider === 'google' ? 'testuser@gmail.com' : 'testuser@github.com',
        avatar: provider === 'google' 
          ? 'https://lh3.googleusercontent.com/a/default-user' 
          : 'https://github.com/identicons/user.png',
        provider: provider,
        profile: {
          skills: [],
          experience_years: 0,
          location: '',
          resume_url: null
        },
        hasResume: false,
        isResumeAvailable: false,
        availableJobs: 0,
        matchedJobs: 0,
        applications: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }

      // Add to mock users if not exists
      const existingUserIndex = mockUsers.findIndex(u => u.email === mockOAuthUser.email)
      if (existingUserIndex >= 0) {
        mockUsers[existingUserIndex] = mockOAuthUser
      } else {
        mockUsers.push(mockOAuthUser)
      }

      const response = await mockApiResponse({ 
        user: mockOAuthUser, 
        token: `oauth-token-${provider}-${mockOAuthUser.id}` 
      })
      return { data: response.data }
    } catch (error) {
      return { data: null, error: `OAuth login with ${provider} failed` }
    }
  },

  register: async (name: string, email: string, password: string): Promise<{ data: { user: User; token: string } | null; error?: string }> => {
    try {
      // Check if user already exists
      const existingUser = mockUsers.find(u => u.email === email)
      if (existingUser) {
        const errorResponse = await mockApiError('User already exists')
        return { data: null, error: errorResponse.error }
      }

      // Create new user
      const newUser: User = {
        id: `user-${Date.now()}`,
        name,
        email,
        profile: {
          skills: [],
          experience_years: 0,
          location: '',
          resume_url: null
        },
        hasResume: false,
        isResumeAvailable: false,
        availableJobs: 0,
        matchedJobs: 0,
        applications: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }

      mockUsers.push(newUser)
      const response = await mockApiResponse({ 
        user: newUser, 
        token: `mock-token-${newUser.id}` 
      })
      return { data: response.data }
    } catch (error) {
      return { data: null, error: 'Registration failed' }
    }
  }
}

// Jobs API - uses real API or mock based on configuration
export const jobsApi = API_CONFIG.mode === 'real' ? realApi.jobsApi : {
  getAll: async (filters?: { location?: string; type?: string; remote?: boolean }): Promise<{ data: Job[]; error?: string }> => {
    try {
      let filteredJobs = [...mockJobs]

      if (filters?.location) {
        filteredJobs = filteredJobs.filter(job => 
          job.location.toLowerCase().includes(filters.location!.toLowerCase())
        )
      }

      if (filters?.type) {
        filteredJobs = filteredJobs.filter(job => job.type === filters.type)
      }

      if (filters?.remote !== undefined) {
        filteredJobs = filteredJobs.filter(job => job.remote === filters.remote)
      }

      const response = await mockApiResponse(filteredJobs)
      return { data: response.data }
    } catch (error) {
      return { data: [], error: 'Failed to fetch jobs' }
    }
  },

  getById: async (id: string): Promise<{ data: Job | null; error?: string }> => {
    try {
      const job = mockJobs.find(j => j.id === id)
      if (job) {
        const response = await mockApiResponse(job)
        return { data: response.data }
      } else {
        return { data: null, error: 'Job not found' }
      }
    } catch (error) {
      return { data: null, error: 'Failed to fetch job' }
    }
  },

  getFeatured: async (): Promise<{ data: Job[]; error?: string }> => {
    try {
      // Return top 3 jobs with highest match scores
      const featured = mockJobs
        .sort((a, b) => (b.matchScore || 0) - (a.matchScore || 0))
        .slice(0, 3)
      
      const response = await mockApiResponse(featured)
      return { data: response.data }
    } catch (error) {
      return { data: [], error: 'Failed to fetch featured jobs' }
    }
  },

  getMatched: async (userId: string, filters?: { location?: string; type?: string; remote?: boolean }): Promise<{ data: Job[]; error?: string }> => {
    try {
      // Always return exactly 2 matched jobs for predictable testing
      // In real API, this would use user profile, skills, experience, etc.
      let matchedJobs = [...mockJobs]
        .slice(0, 2) // Take first 2 jobs as matches
        .map(job => ({
          ...job,
          // Set deterministic high match scores for matched jobs
          matchScore: job.id === '1' ? 95 : 88
        }))

      // Apply filters if provided (after taking the first 2)
      if (filters?.location) {
        matchedJobs = matchedJobs.filter(job => 
          job.location.toLowerCase().includes(filters.location!.toLowerCase())
        )
      }

      if (filters?.type) {
        matchedJobs = matchedJobs.filter(job => job.type === filters.type)
      }

      if (filters?.remote !== undefined) {
        matchedJobs = matchedJobs.filter(job => job.remote === filters.remote)
      }

      const response = await mockApiResponse(matchedJobs)
      return { data: response.data }
    } catch (error) {
      return { data: [], error: 'Failed to fetch matched jobs' }
    }
  }
}

// Applications API - uses real API or mock based on configuration
export const applicationsApi = API_CONFIG.mode === 'real' ? realApi.applicationsApi : {
  create: async (jobId: string, userId: string, coverLetter: string): Promise<{ data: Application | null; error?: string }> => {
    try {
      const job = mockJobs.find(j => j.id === jobId)
      if (!job) {
        return { data: null, error: 'Job not found' }
      }

      const newApplication: Application = {
        id: `app-${Date.now()}`,
        userId: userId,
        jobId: jobId,
        status: 'submitted',
        submittedAt: new Date().toISOString(),
        notes: coverLetter
      }

      mockApplications.push(newApplication)
      const response = await mockApiResponse(newApplication)
      return { data: response.data }
    } catch (error) {
      return { data: null, error: 'Failed to create application' }
    }
  },

  getByUserId: async (userId: string): Promise<{ data: Application[]; error?: string }> => {
    try {
      const userApplications = mockApplications.filter(app => app.userId === userId)
      const response = await mockApiResponse(userApplications)
      return { data: response.data }
    } catch (error) {
      return { data: [], error: 'Failed to fetch applications' }
    }
  },

  updateStatus: async (id: string, status: Application['status']): Promise<{ data: Application | null; error?: string }> => {
    try {
      const appIndex = mockApplications.findIndex(app => app.id === id)
      if (appIndex === -1) {
        return { data: null, error: 'Application not found' }
      }

      mockApplications[appIndex].status = status
      const response = await mockApiResponse(mockApplications[appIndex])
      return { data: response.data }
    } catch (error) {
      return { data: null, error: 'Failed to update application status' }
    }
  }
}

// Interviews API - uses real API or mock based on configuration
export const interviewsApi = API_CONFIG.mode === 'real' ? realApi.interviewsApi : {
  getByApplicationId: async (applicationId: string): Promise<{ data: Interview | null; error?: string }> => {
    try {
      const interview = mockInterviews.find(i => i.applicationId === applicationId)
      if (interview) {
        const response = await mockApiResponse(interview)
        return { data: response.data }
      } else {
        return { data: null, error: 'Interview not found' }
      }
    } catch (error) {
      return { data: null, error: 'Failed to fetch interview' }
    }
  },

  create: async (applicationId: string, scheduledAt: string): Promise<{ data: Interview | null; error?: string }> => {
    try {
      const newInterview: Interview = {
        id: `interview-${Date.now()}`,
        applicationId: applicationId,
        jobId: 'mock-job-id', // This should come from the application
        userId: 'mock-user-id', // This should come from the application
        type: 'ai',
        status: 'scheduled',
        scheduledAt: scheduledAt,
        duration: 60,
        questions: [
          {
            id: 'q1',
            question: 'Tell me about yourself and your experience.',
            type: 'behavioral'
          },
          {
            id: 'q2',
            question: 'What interests you about this position?',
            type: 'behavioral'
          }
        ]
      }

      mockInterviews.push(newInterview)
      const response = await mockApiResponse(newInterview)
      return { data: response.data }
    } catch (error) {
      return { data: null, error: 'Failed to create interview' }
    }
  }
}

// File API - uses real API (no mock equivalent)
export const fileApi = API_CONFIG.mode === 'real' ? realApi.fileApi : {
  uploadResume: async (file: File, processWithAi = true): Promise<{ data: any | null; error?: string }> => {
    // Mock file upload - simulate successful upload
    return {
      data: {
        success: true,
        upload: {
          file_id: `file-mock-${Date.now()}`,
          filename: file.name,
          file_path: `/uploads/mock-${file.name}`,
          file_size: file.size,
          content_type: file.type,
          uploaded_at: new Date().toISOString(),
          user_email: 'mock@example.com'
        },
        processed_data: processWithAi ? {
          skills_extracted: ['JavaScript', 'React', 'Node.js'],
          experience_years: 3,
          education: [],
          work_experience: [],
          contact_info: { email: 'mock@example.com' },
          summary: 'Mock resume processing result',
          confidence_score: 0.85
        } : null,
        profile_updated: processWithAi,
        message: 'Mock resume uploaded successfully'
      }
    }
  },

  getFileStatus: async (fileId: string): Promise<{ data: any | null; error?: string }> => {
    return {
      data: {
        file_id: fileId,
        status: 'completed',
        processed: true
      }
    }
  }
}

// User API - uses real API or mock based on configuration
export const userApi = API_CONFIG.mode === 'real' ? realApi.userApi : {
  updateProfile: async (userId: string, profileData: Partial<User['profile']>): Promise<{ data: User | null; error?: string }> => {
    try {
      const userIndex = mockUsers.findIndex(u => u.id === userId)
      if (userIndex === -1) {
        return { data: null, error: 'User not found' }
      }

      if (mockUsers[userIndex].profile) {
        mockUsers[userIndex].profile = {
          ...mockUsers[userIndex].profile!,
          ...profileData
        }
      } else {
        mockUsers[userIndex].profile = {
          skills: profileData?.skills || [],
          experience_years: profileData?.experience_years || 0,
          location: profileData?.location || '',
          resume_url: profileData?.resume_url || null
        }
      }

      const response = await mockApiResponse(mockUsers[userIndex])
      return { data: response.data }
    } catch (error) {
      return { data: null, error: 'Failed to update profile' }
    }
  },

  getProfile: async (userId: string): Promise<{ data: User | null; error?: string }> => {
    try {
      const user = mockUsers.find(u => u.id === userId)
      if (user) {
        const response = await mockApiResponse(user)
        return { data: response.data }
      } else {
        return { data: null, error: 'User not found' }
      }
    } catch (error) {
      return { data: null, error: 'Failed to fetch user profile' }
    }
  }
}