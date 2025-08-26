"use client"

import { useState } from 'react'
import { cn } from '@/lib/utils'

interface OAuthButtonProps {
  provider: 'google' | 'github'
  redirect?: string
  className?: string
}

const GoogleIcon = () => (
  <svg width="18" height="18" viewBox="0 0 18 18">
    <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 0 0 2.38-5.88c0-.57-.05-.66-.15-1.18z"/>
    <path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2.04a4.8 4.8 0 0 1-2.7.75 4.8 4.8 0 0 1-4.52-3.26H1.83v2.07A8 8 0 0 0 8.98 17z"/>
    <path fill="#FBBC05" d="M4.46 10.51a4.8 4.8 0 0 1-.25-1.5c0-.52.09-1.03.25-1.5V5.44H1.83a8 8 0 0 0 0 7.12l2.63-2.05z"/>
    <path fill="#EA4335" d="M8.98 4.24c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 0 0 8.98 1a8 8 0 0 0-7.15 4.44l2.63 2.05A4.8 4.8 0 0 1 8.98 4.24z"/>
  </svg>
)

const GitHubIcon = () => (
  <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
  </svg>
)

export function OAuthButton({ provider, redirect, className }: OAuthButtonProps) {
  const isGoogle = provider === 'google'
  
  // Build the auth URL with redirect parameter, just like old frontend
  const authUrl = `/auth/${provider}${redirect ? `?redirect=${encodeURIComponent(redirect)}` : ''}`

  return (
    <a
      href={authUrl}
      className={cn(
        'flex items-center justify-center gap-3 w-full px-4 py-3.5 rounded-lg font-medium text-sm transition-all duration-200 no-underline',
        isGoogle
          ? 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 hover:border-gray-400'
          : 'bg-gray-900 text-white border border-gray-900 hover:bg-gray-800',
        className
      )}
    >
      {isGoogle ? <GoogleIcon /> : <GitHubIcon />}
      Continue with {provider === 'google' ? 'Google' : 'GitHub'}
    </a>
  )
}