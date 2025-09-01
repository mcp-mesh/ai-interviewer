// API Types

export interface UserApplication {
  jobId: string
  qualified: boolean
  status?: 'STARTED' | 'APPLIED' | 'QUALIFIED' | 'INPROGRESS' | 'COMPLETED' | 'INTERVIEW_COMPLETED'
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
  resume_analysis?: {
    professional_summary?: string
    years_experience?: number
    skills?: string[]
    experience?: {
      title: string
      company: string
      duration: string
    }[]
    experience_level?: string
    education_level?: string
    ai_provider?: string
    ai_model?: string
  }
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
  short_description?: string
  requirements: string[]
  benefits?: string[]
  salaryRange?: {
    min: number
    max: number
    currency: string
  }
  interview_duration_minutes?: number
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
  categories?: string[]
  job_types?: string[]
  cities?: string[]
  states?: string[]
  countries?: string[]
  // Legacy filters for backward compatibility
  location?: string
  type?: string
  remote?: boolean
  salaryMin?: number
  salaryMax?: number
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

// User State Types
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

// File API Types
export interface FileUpload {
  file_id: string
  filename: string
  file_path: string
  file_size: number
  content_type: string
  uploaded_at: string
  user_email: string
}

export interface WorkExperienceItem {
  company_name: string
  job_title: string
  start_date?: string
  end_date?: string
  is_current: boolean
  location?: string
  responsibilities: string | string[]
}

export interface EducationItem {
  institution: string
  degree: string
  year?: string
}

export interface ProcessedResumeData {
  skills_extracted: string[]
  experience_years: number
  education: EducationItem[]
  work_experience: WorkExperienceItem[]
  contact_info: { email: string }
  summary?: string
  technical_skills?: string
  soft_skills?: string
  confidence_score: number
}

export interface FileUploadResponse {
  success: boolean
  upload: FileUpload
  processed_data: ProcessedResumeData | null
  profile_updated: boolean
  message: string
}

export interface FileStatus {
  file_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  processed: boolean
}

// Backend API Types (for api-client.ts)
export interface BackendJob {
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
  description?: string
  short_description?: string
  requirements?: string[]
  benefits?: string[]
  salaryRange?: {
    min: number
    max: number
    currency: string
  }
  interview_duration_minutes?: number
  matchScore?: number
  isBookmarked?: boolean
  isRecommended?: boolean
  is_featured?: boolean
  postedAt: string
  expiresAt?: string
}

export interface ApplicationStepData {
  [key: string]: string | number | boolean | string[] | Record<string, unknown>[] | Record<string, unknown> | null | undefined
}

export interface ApplicationStatus {
  applicationId: string
  status: 'draft' | 'submitted' | 'under-review' | 'interview' | 'rejected' | 'accepted'
  currentStep?: number
  totalSteps?: number
  lastUpdated: string
}

export interface ApplicationReviewData {
  applicationId: string
  responses: Record<string, string | string[]>
  personalInfo: {
    firstName: string
    lastName: string
    email: string
    phone: string
    address?: string
  }
  personal_information?: {
    name: string
    email: string
    phone: string
    linkedin: string
    address: string
    location?: {
      city: string
      state: string
      country: string
    }
  }
  position?: {
    job_title: string
  }
  experience_and_skills?: {
    professional_summary?: string
    technical_skills?: string[]
    work_experience?: Record<string, unknown>[]
    education?: Record<string, unknown>[]
    current_position?: {
      job_title: string
      company: string
    }
  }
  questions?: Record<string, string>
  disclosures?: Record<string, string>
  identity?: Record<string, string | string[]>
  application_preferences?: {
    work_authorization?: string
    relocate?: string
    remote_work?: string
    availability?: string
  }
  attached_documents?: {
    resume?: {
      filename?: string
      url?: string
      uploaded_at?: string
      file_size?: number
    }
  }
  coverLetter?: string
  additionalInfo?: Record<string, unknown>
}