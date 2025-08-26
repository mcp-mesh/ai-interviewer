import { z } from 'zod'

// Common validation patterns
export const emailSchema = z
  .string()
  .min(1, 'Email is required')
  .email('Please enter a valid email address')

export const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, 'Password must contain at least one uppercase letter, one lowercase letter, and one number')

export const nameSchema = z
  .string()
  .min(2, 'Name must be at least 2 characters')
  .max(100, 'Name cannot exceed 100 characters')
  .regex(/^[a-zA-Z\s'-]+$/, 'Name can only contain letters, spaces, hyphens, and apostrophes')

export const phoneSchema = z
  .string()
  .regex(/^[\+]?[1-9][\d]{0,15}$/, 'Please enter a valid phone number')
  .optional()

// Auth schemas
export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'Password is required'),
})

export const registerSchema = z.object({
  name: nameSchema,
  email: emailSchema,
  password: passwordSchema,
  confirmPassword: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
})

// Profile schemas
export const profileUpdateSchema = z.object({
  name: nameSchema.optional(),
  email: emailSchema.optional(),
  location: z.string().max(200, 'Location cannot exceed 200 characters').optional(),
  bio: z.string().max(500, 'Bio cannot exceed 500 characters').optional(),
  skills: z.array(z.string().max(50, 'Skill name cannot exceed 50 characters')).optional(),
  experienceYears: z.number().int().min(0).max(50).optional(),
})

// Application schemas
export const applicationSchema = z.object({
  jobId: z.string().min(1, 'Job ID is required'),
  personalInfo: z.object({
    firstName: nameSchema,
    lastName: nameSchema,
    email: emailSchema,
    phone: phoneSchema,
    address: z.string().min(10, 'Please enter a complete address').max(300, 'Address cannot exceed 300 characters'),
  }),
  experience: z.object({
    yearsOfExperience: z.number().int().min(0, 'Experience cannot be negative').max(50, 'Experience cannot exceed 50 years'),
    currentRole: z.string().max(100, 'Current role cannot exceed 100 characters').optional(),
    previousRoles: z.array(z.string().max(100, 'Role description cannot exceed 100 characters')).optional(),
  }),
  coverLetter: z.string()
    .min(50, 'Cover letter must be at least 50 characters')
    .max(2000, 'Cover letter cannot exceed 2000 characters'),
  responses: z.record(z.string(), z.string()).optional(), // Dynamic form responses
})

// Resume upload schema
export const resumeUploadSchema = z.object({
  file: z.instanceof(File, { message: 'Please select a file' })
    .refine((file) => file.size <= 5 * 1024 * 1024, 'File size must be less than 5MB')
    .refine((file) => {
      const allowedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
      ]
      return allowedTypes.includes(file.type)
    }, 'File must be PDF, Word document, or plain text'),
  captcha: z.string().min(1, 'Please enter the captcha'),
})

// Contact/Support schemas
export const contactSchema = z.object({
  name: nameSchema,
  email: emailSchema,
  subject: z.string().min(5, 'Subject must be at least 5 characters').max(200, 'Subject cannot exceed 200 characters'),
  message: z.string().min(20, 'Message must be at least 20 characters').max(1000, 'Message cannot exceed 1000 characters'),
  category: z.enum(['general', 'technical', 'billing', 'feedback'], {
    message: 'Please select a category'
  }).optional(),
})

// Interview schemas
export const interviewResponseSchema = z.object({
  questionId: z.string().min(1, 'Question ID is required'),
  answer: z.string().min(10, 'Answer must be at least 10 characters').max(2000, 'Answer cannot exceed 2000 characters'),
  timeSpent: z.number().int().min(1, 'Time spent must be at least 1 second').optional(),
})

// Search/Filter schemas
export const jobSearchSchema = z.object({
  query: z.string().max(200, 'Search query cannot exceed 200 characters').optional(),
  location: z.string().max(100, 'Location cannot exceed 100 characters').optional(),
  category: z.string().max(50, 'Category cannot exceed 50 characters').optional(),
  type: z.enum(['Full-time', 'Part-time', 'Contract', 'Internship']).optional(),
  remote: z.boolean().optional(),
  salaryMin: z.number().int().min(0).optional(),
  salaryMax: z.number().int().min(0).optional(),
}).refine((data) => {
  if (data.salaryMin && data.salaryMax) {
    return data.salaryMin <= data.salaryMax
  }
  return true
}, {
  message: 'Minimum salary cannot be greater than maximum salary',
  path: ['salaryMax'],
})

// Settings schemas
export const notificationSettingsSchema = z.object({
  emailNotifications: z.boolean(),
  jobAlerts: z.boolean(),
  interviewReminders: z.boolean(),
  applicationUpdates: z.boolean(),
  marketingEmails: z.boolean(),
})

export const privacySettingsSchema = z.object({
  profileVisibility: z.enum(['public', 'private', 'contacts-only']),
  showEmail: z.boolean(),
  showPhone: z.boolean(),
  allowMessagesFromRecruiters: z.boolean(),
})

// Type exports for easy use in components
export type LoginFormData = z.infer<typeof loginSchema>
export type RegisterFormData = z.infer<typeof registerSchema>
export type ProfileUpdateData = z.infer<typeof profileUpdateSchema>
export type ApplicationFormData = z.infer<typeof applicationSchema>
export type ResumeUploadData = z.infer<typeof resumeUploadSchema>
export type ContactFormData = z.infer<typeof contactSchema>
export type InterviewResponseData = z.infer<typeof interviewResponseSchema>
export type JobSearchData = z.infer<typeof jobSearchSchema>
export type NotificationSettingsData = z.infer<typeof notificationSettingsSchema>
export type PrivacySettingsData = z.infer<typeof privacySettingsSchema>