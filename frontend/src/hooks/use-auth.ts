import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { userApi } from '@/lib/api'
import { queryKeys } from '@/lib/react-query'
import { User } from '@/lib/types'
import { useRouter } from 'next/navigation'

// Get current user from localStorage (for initial load)
export function useCurrentUser() {
  return useQuery({
    queryKey: queryKeys.auth.user,
    queryFn: async (): Promise<User | null> => {
      // Check localStorage for user data
      if (typeof window !== 'undefined') {
        const userData = localStorage.getItem('user')
        const token = localStorage.getItem('auth_token')
        
        if (userData && token) {
          return JSON.parse(userData)
        }
      }
      return null
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: false, // Don't retry localStorage checks
  })
}

// Login mutation
export function useLogin() {
  return useMutation({
    mutationFn: () => {
      // OAuth login is handled by redirecting to nginx gateway
      console.warn('Direct login not supported - use OAuth')
      return Promise.resolve({ data: null, error: 'Direct login not implemented - use OAuth' })
    },
    onSuccess: () => {
      // OAuth redirect will handle the actual login process
      // This function won't be reached in normal flow
      console.log('Login initiated, redirecting to OAuth...')
    },
    onError: (error) => {
      console.error('Login failed:', error)
    },
  })
}

// OAuth login mutation
export function useOAuthLogin() {
  return useMutation({
    mutationFn: ({ provider }: { 
      provider: 'google' | 'github'
      redirectTo?: string 
    }) => {
      // OAuth is handled by nginx - redirect to the OAuth endpoint
      window.location.href = `/auth/${provider}`
      return Promise.resolve({ data: null }) // Won't actually return since page redirects
    },
    onSuccess: () => {
      // OAuth redirect will handle the actual login process
      // This function won't be reached in normal flow
      console.log('OAuth login initiated, redirecting...')
    },
    onError: (error) => {
      console.error('OAuth login failed:', error)
    },
  })
}

// Register mutation
export function useRegister() {
  return useMutation({
    mutationFn: () => {
      // Registration is handled via OAuth, not direct registration
      return Promise.resolve({ data: null, error: 'Direct registration not implemented - use OAuth' })
    },
    onSuccess: () => {
      // Registration is handled via OAuth, not direct registration
      console.log('Registration initiated, use OAuth instead')
    },
    onError: (error) => {
      console.error('Registration failed:', error)
    },
  })
}

// Logout mutation
export function useLogout() {
  const queryClient = useQueryClient()
  const router = useRouter()
  
  return useMutation({
    mutationFn: async () => {
      // Clear localStorage
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user')
      }
    },
    onSuccess: () => {
      // Clear all cached data
      queryClient.clear()
      
      // Redirect to homepage
      router.push('/')
    },
  })
}

// Update user profile
export function useUpdateProfile() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ profileData }: { 
      profileData: Partial<User['profile']> 
    }) => userApi.updateProfile(profileData),
    onSuccess: (data) => {
      if (data.data) {
        // Update user in cache
        queryClient.setQueryData(queryKeys.auth.user, data.data)
        
        // Update localStorage
        if (typeof window !== 'undefined') {
          localStorage.setItem('user', JSON.stringify(data.data))
        }
        
        // Invalidate related queries
        queryClient.invalidateQueries({ 
          queryKey: queryKeys.auth.user 
        })
      }
    },
    onError: (error) => {
      console.error('Failed to update profile:', error)
    },
  })
}

// Get user profile (useful for detailed profile pages)
export function useUserProfile(userId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.auth.profile(userId),
    queryFn: () => userApi.getProfile(),
    select: (data) => data.data,
    enabled: enabled && !!userId,
    staleTime: 1000 * 60 * 10, // 10 minutes - profile data is relatively stable
  })
}