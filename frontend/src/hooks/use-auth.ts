import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { authApi, userApi } from '@/lib/api'
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
  const queryClient = useQueryClient()
  const router = useRouter()
  
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) => 
      authApi.login(email, password),
    onSuccess: (data) => {
      if (data.data) {
        // Store in localStorage
        localStorage.setItem('auth_token', data.data.token)
        localStorage.setItem('user', JSON.stringify(data.data.user))
        
        // Update React Query cache
        queryClient.setQueryData(queryKeys.auth.user, data.data.user)
        
        // Redirect or handle success
        router.push('/dashboard')
      }
    },
    onError: (error) => {
      console.error('Login failed:', error)
    },
  })
}

// OAuth login mutation
export function useOAuthLogin() {
  const queryClient = useQueryClient()
  const router = useRouter()
  
  return useMutation({
    mutationFn: ({ provider, redirectTo }: { 
      provider: 'google' | 'github'
      redirectTo?: string 
    }) => authApi.oauthLogin(provider),
    onSuccess: (data, variables) => {
      if (data.data) {
        // Store in localStorage
        localStorage.setItem('auth_token', data.data.token)
        localStorage.setItem('user', JSON.stringify(data.data.user))
        
        // Update React Query cache
        queryClient.setQueryData(queryKeys.auth.user, data.data.user)
        
        // Redirect
        router.push(variables.redirectTo || '/dashboard')
      }
    },
    onError: (error) => {
      console.error('OAuth login failed:', error)
    },
  })
}

// Register mutation
export function useRegister() {
  const queryClient = useQueryClient()
  const router = useRouter()
  
  return useMutation({
    mutationFn: ({ name, email, password }: { 
      name: string
      email: string 
      password: string 
    }) => authApi.register(name, email, password),
    onSuccess: (data) => {
      if (data.data) {
        // Store in localStorage
        localStorage.setItem('auth_token', data.data.token)
        localStorage.setItem('user', JSON.stringify(data.data.user))
        
        // Update React Query cache
        queryClient.setQueryData(queryKeys.auth.user, data.data.user)
        
        // Redirect to onboarding or dashboard
        router.push('/upload') // Start with resume upload
      }
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
    mutationFn: ({ userId, profileData }: { 
      userId: string
      profileData: Partial<User['profile']> 
    }) => userApi.updateProfile(userId, profileData),
    onSuccess: (data, variables) => {
      if (data.data) {
        // Update user in cache
        queryClient.setQueryData(queryKeys.auth.user, data.data)
        
        // Update localStorage
        if (typeof window !== 'undefined') {
          localStorage.setItem('user', JSON.stringify(data.data))
        }
        
        // Invalidate related queries
        queryClient.invalidateQueries({ 
          queryKey: queryKeys.auth.profile(variables.userId) 
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
    queryFn: () => userApi.getProfile(userId),
    select: (data) => data.data,
    enabled: enabled && !!userId,
    staleTime: 1000 * 60 * 10, // 10 minutes - profile data is relatively stable
  })
}