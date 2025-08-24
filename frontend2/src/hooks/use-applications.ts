import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { applicationsApi } from '@/lib/api'
import { queryKeys } from '@/lib/react-query'
import { Application } from '@/lib/types'

// Get applications by user
export function useUserApplications(userId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.applications.byUser(userId),
    queryFn: () => applicationsApi.getByUserId(userId),
    select: (data) => data.data,
    enabled: enabled && !!userId,
    staleTime: 1000 * 60 * 2, // 2 minutes - applications change frequently
  })
}

// Create new application
export function useCreateApplication() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ jobId, userId, coverLetter }: { 
      jobId: string
      userId: string 
      coverLetter: string 
    }) => applicationsApi.create(jobId, userId, coverLetter),
    onSuccess: (data, variables) => {
      // Add the new application to the cache
      queryClient.setQueryData(
        queryKeys.applications.byUser(variables.userId),
        (oldData: Application[] | undefined) => {
          if (oldData && data.data) {
            return [...oldData, data.data]
          }
          return oldData
        }
      )
      
      // Invalidate related queries
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.applications.byUser(variables.userId) 
      })
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.jobs.detail(variables.jobId) 
      })
    },
    onError: (error) => {
      console.error('Failed to create application:', error)
    },
  })
}

// Update application status
export function useUpdateApplicationStatus() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, status }: { 
      id: string
      status: Application['status'] 
    }) => applicationsApi.updateStatus(id, status),
    onMutate: async ({ id, status }) => {
      // Optimistic update - update the UI immediately
      const queryKey = queryKeys.applications.all
      await queryClient.cancelQueries({ queryKey })
      
      const previousData = queryClient.getQueryData(queryKey)
      
      // Update all related queries optimistically
      queryClient.setQueriesData(
        { queryKey: queryKeys.applications.all },
        (oldData: Application[] | undefined) => {
          if (oldData) {
            return oldData.map(app => 
              app.id === id ? { ...app, status } : app
            )
          }
          return oldData
        }
      )
      
      return { previousData }
    },
    onError: (error, variables, context) => {
      // Revert optimistic update on error
      if (context?.previousData) {
        queryClient.setQueryData(queryKeys.applications.all, context.previousData)
      }
      console.error('Failed to update application status:', error)
    },
    onSettled: () => {
      // Refetch to ensure data is consistent
      queryClient.invalidateQueries({ queryKey: queryKeys.applications.all })
    },
  })
}

// Get application statistics
export function useApplicationStats(userId: string, enabled = true) {
  return useQuery({
    queryKey: [...queryKeys.applications.byUser(userId), 'stats'],
    queryFn: async () => {
      const result = await applicationsApi.getByUserId(userId)
      const applications = result.data || []
      
      return {
        total: applications.length,
        pending: applications.filter(app => app.status === 'submitted' || app.status === 'under-review').length,
        interview: applications.filter(app => app.status === 'interview').length,
        accepted: applications.filter(app => app.status === 'accepted').length,
        rejected: applications.filter(app => app.status === 'rejected').length,
      }
    },
    enabled: enabled && !!userId,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}