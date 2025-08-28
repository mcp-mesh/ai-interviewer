import React from 'react'
import { UseFormRegisterReturn, FieldError } from 'react-hook-form'
import { cn } from '@/lib/utils'
import { AlertCircle } from 'lucide-react'

// Form Field wrapper component
interface FormFieldProps {
  label?: string
  error?: FieldError | string
  required?: boolean
  children: React.ReactNode
  className?: string
  description?: string
}

export function FormField({ 
  label, 
  error, 
  required, 
  children, 
  className,
  description 
}: FormFieldProps) {
  const errorMessage = typeof error === 'string' ? error : error?.message

  return (
    <div className={cn("space-y-2", className)}>
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      {description && (
        <p className="text-sm text-gray-500 mt-1">{description}</p>
      )}
      {children}
      {errorMessage && (
        <div className="flex items-center gap-1 text-sm text-red-600" role="alert">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  )
}

// Input component
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  registration?: UseFormRegisterReturn
  error?: FieldError | string
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, registration, error, ...props }, ref) => {
    const hasError = !!error

    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm ring-offset-white",
          "file:border-0 file:bg-transparent file:text-sm file:font-medium",
          "placeholder:text-gray-500",
          "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:border-blue-500",
          "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-50",
          hasError && "border-red-300 focus:border-red-500 focus:ring-red-500",
          className
        )}
        ref={ref}
        aria-invalid={hasError}
        {...registration}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

// Textarea component
interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  registration?: UseFormRegisterReturn
  error?: FieldError | string
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, registration, error, ...props }, ref) => {
    const hasError = !!error

    return (
      <textarea
        className={cn(
          "flex min-h-[80px] w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm ring-offset-white",
          "placeholder:text-gray-500",
          "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:border-blue-500",
          "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-50",
          hasError && "border-red-300 focus:border-red-500 focus:ring-red-500",
          "resize-none",
          className
        )}
        ref={ref}
        aria-invalid={hasError}
        {...registration}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

// Select component
interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  registration?: UseFormRegisterReturn
  error?: FieldError | string
  options: { value: string; label: string }[]
  placeholder?: string
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, registration, error, options, placeholder, ...props }, ref) => {
    const hasError = !!error

    return (
      <select
        className={cn(
          "flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm ring-offset-white",
          "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:border-blue-500",
          "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-50",
          hasError && "border-red-300 focus:border-red-500 focus:ring-red-500",
          className
        )}
        ref={ref}
        aria-invalid={hasError}
        {...registration}
        {...props}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    )
  }
)
Select.displayName = "Select"

// Form container component
interface FormContainerProps {
  onSubmit: (e: React.FormEvent) => void
  children: React.ReactNode
  className?: string
}

export function FormContainer({ onSubmit, children, className }: FormContainerProps) {
  return (
    <form 
      onSubmit={onSubmit} 
      className={cn("space-y-6", className)}
      noValidate // We handle validation with Zod
    >
      {children}
    </form>
  )
}

// Form error summary component
interface FormErrorSummaryProps {
  errors: Record<string, FieldError | string>
  title?: string
}

export function FormErrorSummary({ errors, title = "Please correct the following errors:" }: FormErrorSummaryProps) {
  const errorEntries = Object.entries(errors).filter(([, error]) => error)
  
  if (errorEntries.length === 0) return null

  return (
    <div className="rounded-md bg-red-50 border border-red-200 p-4" role="alert">
      <div className="flex items-start gap-2">
        <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
        <div>
          <h3 className="text-sm font-medium text-red-800">{title}</h3>
          <ul className="mt-2 text-sm text-red-700 list-disc list-inside space-y-1">
            {errorEntries.map(([field, error]) => (
              <li key={field}>
                {typeof error === 'string' ? error : error.message}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}