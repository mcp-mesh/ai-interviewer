// Application form data types
export interface WorkExperience {
  company: string
  jobTitle: string
  startDate: string
  endDate: string
  isCurrent: boolean
  location: string
  responsibilities: string
}

export interface Education {
  institution: string
  degree: string
  fieldOfStudy: string
  graduationYear: number
  gpa: string
}

export interface ApplicationData {
  personalInfo: {
    firstName: string
    lastName: string
    email: string
    phone: string
    linkedIn: string
  }
  addressInfo: {
    street: string
    city: string
    state: string
    zipCode: string
    country: string
  }
  position?: {
    job_title: string
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
  experience: {
    summary: string
    technicalSkills: string
    softSkills: string
    workExperience: WorkExperience[]
    education: Education[]
  }
  questions: {
    workAuthorization: string
    visaSponsorship: string
    relocate: string
    remoteWork: string
    preferredLocation: string
    availability: string
    salaryMin: string
    salaryMax: string
  }
  disclosures: {
    governmentEmployment: string
    nonCompete: string
    previousEmployment: string
    previousAlias: string
    personnelNumber: string
  }
  identity: {
    gender: string
    race: string[]
    veteranStatus: string
    disability: string
  }
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
}

export interface ApplicationPageProps {
  params: Promise<{
    jobId: string
  }>
}

// Step configuration
export interface Step {
  id: number
  title: string
  key: string
}

export const steps: Step[] = [
  { id: 1, title: 'My Information', key: 'info' },
  { id: 2, title: 'My Experience', key: 'experience' },
  { id: 3, title: 'Application Questions', key: 'questions' },
  { id: 4, title: 'Voluntary Disclosures', key: 'disclosures' },
  { id: 5, title: 'Self Identity', key: 'identity' },
  { id: 6, title: 'Review', key: 'review' }
]

// Initial form data
export const initialFormData: ApplicationData = {
  personalInfo: {
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    linkedIn: ''
  },
  addressInfo: {
    street: '',
    city: '',
    state: '',
    zipCode: '',
    country: 'US'
  },
  experience: {
    summary: '',
    technicalSkills: '',
    softSkills: '',
    workExperience: [],
    education: []
  },
  questions: {
    workAuthorization: '',
    visaSponsorship: '',
    relocate: '',
    remoteWork: '',
    preferredLocation: '',
    availability: '',
    salaryMin: '',
    salaryMax: ''
  },
  disclosures: {
    governmentEmployment: '',
    nonCompete: '',
    previousEmployment: '',
    previousAlias: '',
    personnelNumber: ''
  },
  identity: {
    gender: '',
    race: [],
    veteranStatus: '',
    disability: ''
  }
}