import { Job, User, Application, Interview } from './types'
import { mockJobs, mockUsers, mockApplications, mockInterviews, mockApiResponse, mockApiError } from './mock-data'

// Auth API
export const authApi = {
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
        email: provider === 'google' ? 'john.doe@gmail.com' : 'user@github.com',
        profile: {
          skills: ['JavaScript', 'React', 'Node.js', 'TypeScript'],
          experience_years: provider === 'google' ? 5 : 3,
          location: 'San Francisco, CA',
          resume_url: null,
          avatar: provider === 'google' 
            ? 'https://lh3.googleusercontent.com/a/default-user' 
            : 'https://github.com/identicons/user.png',
          provider: provider
        },
        created_at: new Date().toISOString()
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
        created_at: new Date().toISOString()
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

// Jobs API
export const jobsApi = {
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
        .sort((a, b) => (b.match_score || 0) - (a.match_score || 0))
        .slice(0, 3)
      
      const response = await mockApiResponse(featured)
      return { data: response.data }
    } catch (error) {
      return { data: [], error: 'Failed to fetch featured jobs' }
    }
  }
}

// Applications API
export const applicationsApi = {
  create: async (jobId: string, userId: string, coverLetter: string): Promise<{ data: Application | null; error?: string }> => {
    try {
      const job = mockJobs.find(j => j.id === jobId)
      if (!job) {
        return { data: null, error: 'Job not found' }
      }

      const newApplication: Application = {
        id: `app-${Date.now()}`,
        user_id: userId,
        job_id: jobId,
        status: 'pending',
        applied_at: new Date().toISOString(),
        cover_letter: coverLetter,
        job
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
      const userApplications = mockApplications.filter(app => app.user_id === userId)
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

// Interviews API
export const interviewsApi = {
  getByApplicationId: async (applicationId: string): Promise<{ data: Interview | null; error?: string }> => {
    try {
      const interview = mockInterviews.find(i => i.application_id === applicationId)
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
        application_id: applicationId,
        status: 'scheduled',
        scheduled_at: scheduledAt,
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

// User API
export const userApi = {
  updateProfile: async (userId: string, profileData: Partial<User['profile']>): Promise<{ data: User | null; error?: string }> => {
    try {
      const userIndex = mockUsers.findIndex(u => u.id === userId)
      if (userIndex === -1) {
        return { data: null, error: 'User not found' }
      }

      mockUsers[userIndex].profile = {
        ...mockUsers[userIndex].profile,
        ...profileData
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