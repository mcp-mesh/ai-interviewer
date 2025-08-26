import { QueryClient } from '@tanstack/react-query'
import { JobFilters } from './types'

interface ErrorWithStatus {
  status: number
}

function isErrorWithStatus(error: unknown): error is ErrorWithStatus {
  return error !== null && typeof error === 'object' && 'status' in error
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Stale time - how long data is considered fresh
      staleTime: 1000 * 60 * 5, // 5 minutes
      // Cache time - how long data stays in cache after becoming unused
      gcTime: 1000 * 60 * 30, // 30 minutes (previously cacheTime)
      // Retry failed requests
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors (client errors)
        if (isErrorWithStatus(error)) {
          const status = error.status
          if (status >= 400 && status < 500) return false
        }
        // Retry up to 3 times for other errors
        return failureCount < 3
      },
      // Refetch on window focus for important data
      refetchOnWindowFocus: true,
      // Don't refetch on reconnect by default
      refetchOnReconnect: false,
    },
    mutations: {
      // Retry mutations once on failure
      retry: 1,
    },
  },
})

// Query keys factory for consistency
export const queryKeys = {
  // Auth
  auth: {
    user: ['auth', 'user'] as const,
    profile: (userId: string) => ['auth', 'profile', userId] as const,
  },
  // Jobs
  jobs: {
    all: ['jobs'] as const,
    list: (filters?: JobFilters) => ['jobs', 'list', filters] as const,
    detail: (id: string) => ['jobs', 'detail', id] as const,
    featured: ['jobs', 'featured'] as const,
    matched: (userId: string) => ['jobs', 'matched', userId] as const,
  },
  // Applications
  applications: {
    all: ['applications'] as const,
    byUser: (userId: string) => ['applications', 'user', userId] as const,
    detail: (id: string) => ['applications', 'detail', id] as const,
  },
  // Interviews
  interviews: {
    all: ['interviews'] as const,
    byApplication: (appId: string) => ['interviews', 'application', appId] as const,
    detail: (id: string) => ['interviews', 'detail', id] as const,
  },
} as const