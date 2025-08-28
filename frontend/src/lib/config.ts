// API Configuration - Real API only
export const API_CONFIG = {
  // Base URL for API calls
  // For client-side requests, use relative URLs to go through nginx proxy
  // For server-side requests, use the container service name
  baseUrl: typeof window !== 'undefined' 
    ? '/api'  // Client-side: use relative URLs through nginx proxy
    : (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://fastapi:8080/api'), // Server-side: direct to backend
} as const