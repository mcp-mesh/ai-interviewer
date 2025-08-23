"use client"

import { useEffect, useState } from 'react'
import { cn } from '@/lib/utils'

export type ToastType = 'info' | 'success' | 'warning' | 'error'

interface Toast {
  id: string
  message: string
  type: ToastType
}

interface ToastProps {
  toast: Toast
  onRemove: (id: string) => void
}

function ToastItem({ toast, onRemove }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onRemove(toast.id)
    }, 3000)

    return () => clearTimeout(timer)
  }, [toast.id, onRemove])

  const getToastStyles = (type: ToastType) => {
    switch (type) {
      case 'success':
        return {
          background: '#f0fdf4',
          color: '#166534',
          borderColor: '#bbf7d0'
        }
      case 'warning':
        return {
          background: '#fffbeb',
          color: '#92400e',
          borderColor: '#fcd34d'
        }
      case 'error':
        return {
          background: '#fef2f2',
          color: '#991b1b',
          borderColor: '#fca5a5'
        }
      default: // info
        return {
          background: '#eff6ff',
          color: '#1e40af',
          borderColor: '#93c5fd'
        }
    }
  }

  const styles = getToastStyles(toast.type)

  return (
    <div
      className={cn(
        "alert relative overflow-hidden rounded-2xl p-6 border backdrop-blur-sm",
        "animate-in slide-in-from-right-full duration-300"
      )}
      style={{
        position: 'fixed',
        top: '2rem',
        right: '2rem',
        zIndex: 1000,
        minWidth: '300px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        ...styles
      }}
    >
      {/* Shimmer effect */}
      <div
        className="absolute top-0 left-0 right-0 h-px"
        style={{
          background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent)'
        }}
      />
      
      <div className="flex items-center justify-between">
        <span className="font-medium">{toast.message}</span>
        <button
          onClick={() => onRemove(toast.id)}
          className="ml-4 opacity-70 hover:opacity-100 transition-opacity"
          style={{ color: styles.color }}
        >
          ✕
        </button>
      </div>
    </div>
  )
}

interface ToastContainerProps {
  toasts: Toast[]
  onRemove: (id: string) => void
}

export function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  return (
    <div className="fixed top-0 right-0 z-[1000] pointer-events-none">
      {toasts.map((toast, index) => (
        <div
          key={toast.id}
          className="pointer-events-auto"
          style={{
            marginTop: `${index * 5}rem`
          }}
        >
          <ToastItem toast={toast} onRemove={onRemove} />
        </div>
      ))}
    </div>
  )
}

// Toast hook for managing toasts
export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = (message: string, type: ToastType = 'info') => {
    const id = Math.random().toString(36).substr(2, 9)
    setToasts(prev => [...prev, { id, message, type }])
  }

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id))
  }

  const showToast = {
    info: (message: string) => addToast(message, 'info'),
    success: (message: string) => addToast(message, 'success'),
    warning: (message: string) => addToast(message, 'warning'),
    error: (message: string) => addToast(message, 'error')
  }

  return {
    toasts,
    showToast,
    removeToast
  }
}