import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobsApi } from '@/lib/api'
import { queryKeys } from '@/lib/react-query'
import { Job, JobFilters } from '@/lib/types'

// Get all jobs with optional filters
export function useJobs(filters?: JobFilters, enabled = true) {
  return useQuery({
    queryKey: queryKeys.jobs.list(filters),
    queryFn: () => jobsApi.getAll(filters),
    select: (data) => data.data, // Extract the data from the API response
    staleTime: 1000 * 60 * 5, // 5 minutes - job listings don't change frequently
    enabled: Boolean(enabled),
  })
}

// Get single job by ID
export function useJob(id: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.jobs.detail(id),
    queryFn: () => jobsApi.getById(id),
    select: (data) => data.data,
    enabled: enabled && !!id, // Don't fetch if no ID provided
    staleTime: 1000 * 60 * 10, // 10 minutes - individual job details are more stable
  })
}

// Get featured jobs
export function useFeaturedJobs() {
  return useQuery({
    queryKey: queryKeys.jobs.featured,
    queryFn: () => jobsApi.getFeatured(),
    select: (data) => data.data,
    staleTime: 1000 * 60 * 15, // 15 minutes - featured jobs change less frequently
  })
}

// Get matched jobs for a user (if we implement this API endpoint)
export function useMatchedJobs(userId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.jobs.matched(userId),
    queryFn: () => jobsApi.getAll({ /* we could add a matched filter */ }),
    select: (data) => data.data?.filter((job: Job) => job.matchScore && job.matchScore > 70), // Mock filtering
    enabled: enabled && !!userId,
    staleTime: 1000 * 60 * 10, // 10 minutes
  })
}

// Mutation for bookmarking jobs (if we implement this)
export function useBookmarkJob() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async () => {
      // This would be a real API call
      // For now, we'll just simulate success
      return { success: true }
    },
    onSuccess: () => {
      // Invalidate job queries to refetch updated bookmark status
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs.all })
    },
  })
}

// Prefetch job details (useful for hover states, etc.)
export function usePrefetchJob() {
  const queryClient = useQueryClient()
  
  return (id: string) => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.jobs.detail(id),
      queryFn: () => jobsApi.getById(id),
      staleTime: 1000 * 60 * 10, // 10 minutes
    })
  }
}