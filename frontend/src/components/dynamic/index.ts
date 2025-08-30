// Dynamic imports for code splitting  
import dynamic from 'next/dynamic'
import React from 'react'

// Lazy load heavy components
export const DynamicJobCard = dynamic(
  () => import('@/components/job-card').then(mod => ({ default: mod.JobCard })),
  {
    loading: () => React.createElement('div', { className: 'animate-pulse bg-gray-200 h-32 rounded-lg' }),
    ssr: false // Disable SSR for client-side components
  }
)

export const DynamicNavigation = dynamic(
  () => import('@/components/navigation').then(mod => ({ default: mod.Navigation })),
  {
    loading: () => React.createElement('div', { className: 'h-16 bg-gray-200 animate-pulse' }),
    ssr: true // Keep SSR for navigation
  }
)

// Lazy load form components for better performance
export const DynamicApplicationForm = dynamic(
  () => import('@/app/apply/[jobId]/page'),
  {
    loading: () => React.createElement('div', { className: 'animate-pulse bg-gray-200 h-64 rounded-lg' }),
    ssr: false
  }
)

// Common UI components
export const DynamicCard = dynamic(
  () => import('@/components/common').then(mod => ({ default: mod.Card })),
  {
    loading: () => React.createElement('div', { className: 'bg-gray-200 border rounded-xl p-6 animate-pulse' }),
    ssr: false
  }
)