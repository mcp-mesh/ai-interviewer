import { Job, User, Application, Interview } from './types'

// Mock Users
export const mockUsers: User[] = [
  {
    id: 'user-1',
    name: 'John Doe',
    email: 'john@example.com',
    profile: {
      skills: ['JavaScript', 'React', 'Node.js', 'TypeScript'],
      experience_years: 5,
      location: 'San Francisco, CA',
      resume_url: '/resume-john.pdf'
    },
    created_at: '2024-01-15T10:00:00Z'
  },
  {
    id: 'user-2',
    name: 'Sarah Smith',
    email: 'sarah@example.com',
    profile: {
      skills: ['Python', 'Django', 'PostgreSQL', 'AWS'],
      experience_years: 3,
      location: 'New York, NY',
      resume_url: '/resume-sarah.pdf'
    },
    created_at: '2024-02-20T14:30:00Z'
  }
]

// Mock Jobs
export const mockJobs: Job[] = [
  {
    id: 'job-1',
    title: 'Senior Frontend Developer',
    company: 'TechCorp Inc.',
    location: 'San Francisco, CA',
    type: 'full-time',
    salary: '$120,000 - $160,000',
    description: 'We are looking for a Senior Frontend Developer to join our growing team. You will be responsible for building user-facing features using React and TypeScript.',
    requirements: [
      '5+ years of experience with React',
      'Strong TypeScript skills',
      'Experience with modern build tools',
      'Knowledge of testing frameworks'
    ],
    skills: ['React', 'TypeScript', 'JavaScript', 'HTML', 'CSS'],
    remote: true,
    posted_at: '2024-03-01T09:00:00Z',
    match_score: 92
  },
  {
    id: 'job-2',
    title: 'Full Stack Engineer',
    company: 'StartupXYZ',
    location: 'Remote',
    type: 'full-time',
    salary: '$90,000 - $130,000',
    description: 'Join our fast-growing startup as a Full Stack Engineer. Work with modern technologies and help shape our product.',
    requirements: [
      '3+ years full stack development',
      'Experience with Node.js and React',
      'Database design experience',
      'Startup mentality'
    ],
    skills: ['React', 'Node.js', 'PostgreSQL', 'AWS', 'TypeScript'],
    remote: true,
    posted_at: '2024-02-28T16:45:00Z',
    match_score: 88
  },
  {
    id: 'job-3',
    title: 'Backend Developer',
    company: 'Enterprise Solutions',
    location: 'New York, NY',
    type: 'full-time',
    salary: '$100,000 - $140,000',
    description: 'We need a skilled Backend Developer to work on our enterprise-grade applications using Python and Django.',
    requirements: [
      '4+ years Python experience',
      'Django framework expertise',
      'REST API development',
      'Database optimization'
    ],
    skills: ['Python', 'Django', 'PostgreSQL', 'Redis', 'Docker'],
    remote: false,
    posted_at: '2024-02-25T11:20:00Z',
    match_score: 75
  },
  {
    id: 'job-4',
    title: 'DevOps Engineer',
    company: 'CloudTech',
    location: 'Austin, TX',
    type: 'full-time',
    salary: '$110,000 - $150,000',
    description: 'Looking for a DevOps Engineer to manage our cloud infrastructure and CI/CD pipelines.',
    requirements: [
      'AWS/Azure experience',
      'Kubernetes knowledge',
      'CI/CD pipeline experience',
      'Infrastructure as code'
    ],
    skills: ['AWS', 'Kubernetes', 'Docker', 'Terraform', 'Jenkins'],
    remote: true,
    posted_at: '2024-02-20T13:15:00Z',
    match_score: 65
  },
  {
    id: 'job-5',
    title: 'Product Manager',
    company: 'InnovateCorp',
    location: 'Seattle, WA',
    type: 'full-time',
    salary: '$130,000 - $170,000',
    description: 'Lead product strategy and work with cross-functional teams to deliver amazing user experiences.',
    requirements: [
      '5+ years product management',
      'Technical background preferred',
      'Data-driven decision making',
      'Excellent communication skills'
    ],
    skills: ['Product Strategy', 'Data Analysis', 'User Research', 'Agile'],
    remote: true,
    posted_at: '2024-02-15T10:30:00Z',
    match_score: 45
  }
]

// Mock Applications
export const mockApplications: Application[] = [
  {
    id: 'app-1',
    user_id: 'user-1',
    job_id: 'job-1',
    status: 'interview_scheduled',
    applied_at: '2024-03-02T14:00:00Z',
    cover_letter: 'I am excited to apply for the Senior Frontend Developer position...',
    job: mockJobs[0]
  },
  {
    id: 'app-2',
    user_id: 'user-1',
    job_id: 'job-2',
    status: 'pending',
    applied_at: '2024-03-01T16:30:00Z',
    cover_letter: 'As a passionate full stack developer...',
    job: mockJobs[1]
  },
  {
    id: 'app-3',
    user_id: 'user-1',
    job_id: 'job-3',
    status: 'rejected',
    applied_at: '2024-02-28T09:15:00Z',
    cover_letter: 'I would love to join your backend team...',
    job: mockJobs[2]
  }
]

// Mock Interviews
export const mockInterviews: Interview[] = [
  {
    id: 'interview-1',
    application_id: 'app-1',
    status: 'scheduled',
    scheduled_at: '2024-03-10T15:00:00Z',
    questions: [
      {
        id: 'q1',
        question: 'Explain the difference between React hooks and class components.',
        type: 'technical'
      },
      {
        id: 'q2',
        question: 'How would you optimize a React application for performance?',
        type: 'technical'
      },
      {
        id: 'q3',
        question: 'Tell me about a challenging project you worked on.',
        type: 'behavioral'
      }
    ]
  }
]

// Helper functions for mock API responses
export const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

export const mockApiResponse = async <T>(data: T, delayMs: number = 500): Promise<{ data: T; success: boolean }> => {
  await delay(delayMs)
  return { data, success: true }
}

export const mockApiError = async (message: string, delayMs: number = 500): Promise<{ error: string; success: boolean }> => {
  await delay(delayMs)
  return { error: message, success: false }
}