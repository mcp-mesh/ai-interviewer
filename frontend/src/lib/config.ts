// Configuration for API mode
export const API_CONFIG = {
  // Set to 'mock' for local development with mock data
  // Set to 'real' for backend integration  
  mode: (process.env.NEXT_PUBLIC_API_MODE || 'real') as 'mock' | 'real',
  
  // Base URL for real API calls
  // For client-side requests, use relative URLs to go through nginx proxy
  // For server-side requests, use the container service name
  baseUrl: typeof window !== 'undefined' 
    ? '/api'  // Client-side: use relative URLs through nginx proxy
    : (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://fastapi:8080/api'), // Server-side: direct to backend
} as const

console.log('API Configuration:', API_CONFIG)