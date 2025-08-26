// API Types based on wireframe analysis

export interface UserApplication {
  jobId: string
  qualified: boolean
  status?: 'ELIGIBLE' | 'INPROGRESS' | 'COMPLETED'
  interviewSession?: string
  appliedAt: string
  completedAt?: string
}

export interface User {
  id: string
  email: string
  name: string
  hasResume: boolean
  resumeUrl?: string
  avatar?: string
  provider?: 'google' | 'github' | 'email'
  profile?: {
    skills: string[]
    experience_years: number
    location: string
    resume_url: string | null
  }
  isApplicationsAvailable?: boolean
  availableJobs?: number
  matchedJobs?: number
  applications?: UserApplication[]
  createdAt: string
  updatedAt: string
  created_at?: string // For compatibility with mock-data
}

export interface Job {
  id: string
  title: string
  company: string
  location: string
  city?: string
  state?: string
  country?: string
  type: 'Full-time' | 'Part-time' | 'Contract' | 'Internship'
  category: 'Engineering' | 'Operations' | 'Finance' | 'Marketing' | 'Sales' | 'Other'
  remote?: boolean
  description: string
  requirements: string[]
  benefits?: string[]
  salaryRange?: {
    min: number
    max: number
    currency: string
  }
  matchScore?: number
  isBookmarked?: boolean
  isRecommended?: boolean
  postedAt: string
  expiresAt?: string
}

export interface Application {
  id: string
  jobId: string
  userId: string
  status: 'draft' | 'submitted' | 'under-review' | 'interview' | 'rejected' | 'accepted'
  submittedAt?: string
  interviewScheduled?: string
  personalInfo?: {
    firstName: string
    lastName: string
    email: string
    phone: string
    address: string
  }
  experience?: {
    yearsOfExperience: number
    currentRole?: string
    previousRoles?: string[]
  }
  responses?: Record<string, string>
  notes?: string
}

export interface Interview {
  id: string
  applicationId: string
  jobId: string
  userId: string
  type: 'ai' | 'human' | 'technical' | 'behavioral'
  status: 'scheduled' | 'in-progress' | 'completed' | 'cancelled'
  scheduledAt: string
  duration: number // in minutes
  questions?: InterviewQuestion[]
  responses?: InterviewResponse[]
  feedback?: string
  score?: number
}

export interface InterviewQuestion {
  id: string
  question: string
  type: 'technical' | 'behavioral' | 'general'
  expectedAnswer?: string
  difficulty?: 'easy' | 'medium' | 'hard'
}

export interface InterviewResponse {
  questionId: string
  answer: string
  timestamp: string
  score?: number
  feedback?: string
}

export interface JobFilters {
  search?: string
  location?: string
  type?: Job['type'][]
  category?: Job['category'][]
  salaryMin?: number
  salaryMax?: number
  remote?: boolean
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  limit: number
  hasMore: boolean
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

// User State Types (from wireframe analysis)
export type UserState = 
  | 'guest'           // Not logged in
  | 'no-resume'       // Logged in but no resume uploaded
  | 'has-resume'      // Logged in with resume
  | 'interview-ready' // Ready for interviews

export interface UserContext {
  user: User | null
  state: UserState
  isLoading: boolean
}

// Theme types
export type Theme = 'light' | 'dark' | 'system'

// Component Props Types
export interface JobCardProps {
  job: Job
  variant?: 'compact' | 'detailed' | 'featured' | 'dashboard'
  showMatchScore?: boolean
  showBookmark?: boolean
  onApply?: (jobId: string) => void
  onBookmark?: (jobId: string) => void
}

export interface FilterSectionProps {
  title: string
  options: Array<{
    label: string
    value: string
    count: number
  }>
  selectedValues: string[]
  onChange: (values: string[]) => void
  searchable?: boolean
}

export interface UserStatusCardProps {
  state: UserState
  user: User | null
  onUploadResume?: () => void
  onStartInterview?: (roleId: string) => void
}