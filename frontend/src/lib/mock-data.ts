import { Job, User, Application, Interview } from './types'

// Mock Users
export const mockUsers: User[] = [
  {
    id: 'user-1',
    name: 'John Doe',
    email: 'john@example.com',
    hasResume: false,
    profile: {
      skills: [],
      experience_years: 0,
      location: '',
      resume_url: null
    },
    availableJobs: 0,
    matchedJobs: 0,
    applications: [],
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z'
  },
  {
    id: 'user-2',
    name: 'Sarah Smith',
    email: 'sarah@example.com',
    hasResume: false,
    profile: {
      skills: [],
      experience_years: 0,
      location: '',
      resume_url: null
    },
    availableJobs: 0,
    matchedJobs: 0,
    applications: [],
    createdAt: '2024-02-20T14:30:00Z',
    updatedAt: '2024-02-20T14:30:00Z'
  }
]

// Mock Jobs (simplified for build)
export const mockJobs: Job[] = [
  {
    id: '1',
    title: 'Senior Software Engineer',
    company: 'S Corp.',
    location: 'San Francisco, CA',
    type: 'Full-time',
    category: 'Engineering',
    description: 'The Software Engineering team at S Corp. is growing rapidly and is seeking new members for our platform development team. The platform team is responsible for building scalable web applications that serve millions of users worldwide. As a Senior Software Engineer, you will be responsible for designing and implementing robust, scalable solutions using modern web technologies.',
    requirements: [
      'BS/MS degree in Computer Science, Engineering, or related field, or equivalent experience',
      '5+ years of professional software development experience', 
      'Strong proficiency in JavaScript, React, and Node.js',
      'Experience with cloud platforms (AWS, GCP, or Azure)',
      'Solid understanding of database design and SQL',
      'Experience with RESTful APIs and microservices architecture',
      'Strong problem-solving skills and attention to detail',
      'Excellent communication skills and ability to work in a collaborative environment'
    ],
    benefits: [
      'Competitive compensation including base salary and equity',
      'Comprehensive healthcare (medical, dental, vision)', 
      '401(k) match and unlimited PTO',
      'Flexible working arrangements',
      'Professional development stipend',
      'Access to cutting-edge technology',
      'Catered meals and gym membership',
      'Collaborative work environment in modern office space'
    ],
    postedAt: '2024-03-01T09:00:00Z',
    salaryRange: {
      min: 150000,
      max: 200000,
      currency: 'USD'
    },
    remote: false,
    matchScore: 95
  },
  {
    id: '2',
    title: 'Full Stack Engineer',
    company: 'StartupXYZ',
    location: 'Remote',
    type: 'Full-time',
    category: 'Engineering',
    description: 'Join our fast-growing startup as a Full Stack Engineer! You will work on building modern web applications from the ground up, contributing to both frontend and backend development. Our team values innovation, collaboration, and rapid iteration as we scale our product to serve thousands of users.',
    requirements: [
      '3+ years of full-stack development experience',
      'Strong proficiency in Node.js and modern JavaScript',
      'Experience with React or Vue.js',
      'Database experience (PostgreSQL, MongoDB)',
      'Understanding of RESTful APIs and GraphQL',
      'Experience with cloud platforms (AWS, GCP)',
      'Familiarity with Docker and containerization',
      'Strong communication and teamwork skills'
    ],
    benefits: [
      'Competitive salary and significant equity package',
      'Health, dental, and vision insurance',
      'Flexible PTO and remote work options',
      '$2000 annual learning and development budget',
      'Latest MacBook Pro and equipment stipend',
      'Stock options with high growth potential',
      'Team retreats and company events',
      'Startup environment with rapid career growth'
    ],
    postedAt: '2024-02-28T10:30:00Z',
    salaryRange: {
      min: 90000,
      max: 130000,
      currency: 'USD'
    },
    remote: true,
    matchScore: 78
  },
  {
    id: '3',
    title: 'Backend Developer',
    company: 'TechStart',
    location: 'Austin, TX',
    type: 'Full-time',
    category: 'Engineering',
    description: 'Backend developer for scalable systems',
    requirements: ['Python experience', 'API development', 'Cloud platforms'],
    postedAt: '2024-02-25T14:00:00Z',
    salaryRange: {
      min: 100000,
      max: 140000,
      currency: 'USD'
    },
    remote: false,
    matchScore: 85
  },
  {
    id: '4',
    title: 'DevOps Engineer',
    company: 'CloudTech',
    location: 'Austin, TX',
    type: 'Full-time',
    category: 'Engineering',
    description: 'Looking for a DevOps Engineer to manage our cloud infrastructure and CI/CD pipelines. You will work with cutting-edge cloud technologies to ensure scalable, reliable, and secure systems that support our growing user base.',
    requirements: [
      '4+ years of DevOps or Site Reliability Engineer experience',
      'Strong experience with AWS/Azure cloud platforms',
      'Proficiency in Kubernetes and container orchestration',
      'Experience with CI/CD pipeline tools (Jenkins, GitLab, GitHub Actions)',
      'Infrastructure as Code experience (Terraform, CloudFormation)',
      'Scripting skills in Python, Bash, or similar',
      'Monitoring and logging tools experience (Prometheus, Grafana, ELK)',
      'Understanding of network security and best practices'
    ],
    benefits: [
      'Competitive salary with performance bonuses',
      'Comprehensive health, dental, and vision coverage',
      'Flexible work arrangements and remote options',
      '$3000 annual professional development budget',
      'Latest cloud certifications paid by company',
      'Equity participation in growing company',
      'Collaborative team environment',
      '25 days PTO plus holidays'
    ],
    salaryRange: {
      min: 110000,
      max: 150000,
      currency: 'USD'
    },
    remote: true,
    postedAt: '2024-02-20T13:15:00Z',
    matchScore: 85
  },
  {
    id: '5',
    title: 'Product Manager',
    company: 'InnovateCorp',
    location: 'Seattle, WA',
    type: 'Full-time',
    category: 'Operations',
    description: 'Lead product strategy and work with cross-functional teams to deliver amazing user experiences. You will drive the product vision, define roadmaps, and collaborate with engineering, design, and marketing teams to bring innovative products to market.',
    requirements: [
      '5+ years of product management experience',
      'Technical background or CS degree preferred',
      'Strong analytical and data-driven decision making skills',
      'Excellent communication and leadership abilities',
      'Experience with Agile/Scrum methodologies',
      'User research and customer interview experience',
      'Familiarity with product analytics tools',
      'Experience managing product roadmaps and priorities'
    ],
    benefits: [
      'Competitive salary plus equity options',
      'Premium healthcare and wellness programs',
      'Unlimited PTO and flexible work schedule',
      '$4000 annual learning and conference budget',
      'Top-tier equipment and home office setup',
      'Stock options with high growth potential',
      'Collaborative and innovative work culture',
      'Career growth and mentorship opportunities'
    ],
    salaryRange: {
      min: 130000,
      max: 170000,
      currency: 'USD'
    },
    remote: true,
    postedAt: '2024-02-15T10:30:00Z',
    matchScore: 75
  }
]

// Original mock jobs (commented out for build fix)
/* 
export const originalMockJobs: Job[] = [
  {
    id: '1',
    title: 'Senior Frontend Developer',
    company: 'TechCorp Inc.',
    location: 'San Francisco, CA',
    type: 'Full-time',
    category: 'Engineering',
    salaryRange: {
      min: 120000,
      max: 160000,
      currency: 'USD'
    },
    description: 'We are looking for a Senior Frontend Developer to join our growing team. You will be responsible for building user-facing features using React and TypeScript.',
    requirements: [
      '5+ years of experience with React',
      'Strong TypeScript skills',
      'Experience with modern build tools',
      'Knowledge of testing frameworks'
    ],
    postedAt: '2024-03-01T09:00:00Z',
    remote: true,
    matchScore: 92
  },
  {
    id: '2',
    title: 'Full Stack Engineer',
    company: 'StartupXYZ',
    location: 'Remote',
    type: 'Full-time',
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
    id: '3',
    title: 'Backend Developer',
    company: 'Enterprise Solutions',
    location: 'New York, NY',
    type: 'Full-time',
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
    id: '4',
    title: 'DevOps Engineer',
    company: 'CloudTech',
    location: 'Austin, TX',
    type: 'Full-time',
    category: 'Engineering',
    description: 'Looking for a DevOps Engineer to manage our cloud infrastructure and CI/CD pipelines. You will work with cutting-edge cloud technologies to ensure scalable, reliable, and secure systems that support our growing user base.',
    requirements: [
      '4+ years of DevOps or Site Reliability Engineer experience',
      'Strong experience with AWS/Azure cloud platforms',
      'Proficiency in Kubernetes and container orchestration',
      'Experience with CI/CD pipeline tools (Jenkins, GitLab, GitHub Actions)',
      'Infrastructure as Code experience (Terraform, CloudFormation)',
      'Scripting skills in Python, Bash, or similar',
      'Monitoring and logging tools experience (Prometheus, Grafana, ELK)',
      'Understanding of network security and best practices'
    ],
    benefits: [
      'Competitive salary with performance bonuses',
      'Comprehensive health, dental, and vision coverage',
      'Flexible work arrangements and remote options',
      '$3000 annual professional development budget',
      'Latest cloud certifications paid by company',
      'Equity participation in growing company',
      'Collaborative team environment',
      '25 days PTO plus holidays'
    ],
    salaryRange: {
      min: 110000,
      max: 150000,
      currency: 'USD'
    },
    remote: true,
    postedAt: '2024-02-20T13:15:00Z',
    matchScore: 85
  },
  {
    id: '5',
    title: 'Product Manager',
    company: 'InnovateCorp',
    location: 'Seattle, WA',
    type: 'Full-time',
    category: 'Operations',
    description: 'Lead product strategy and work with cross-functional teams to deliver amazing user experiences. You will drive the product vision, define roadmaps, and collaborate with engineering, design, and marketing teams to bring innovative products to market.',
    requirements: [
      '5+ years of product management experience',
      'Technical background or CS degree preferred',
      'Strong analytical and data-driven decision making skills',
      'Excellent communication and leadership abilities',
      'Experience with Agile/Scrum methodologies',
      'User research and customer interview experience',
      'Familiarity with product analytics tools',
      'Experience managing product roadmaps and priorities'
    ],
    benefits: [
      'Competitive salary plus equity options',
      'Premium healthcare and wellness programs',
      'Unlimited PTO and flexible work schedule',
      '$4000 annual learning and conference budget',
      'Top-tier equipment and home office setup',
      'Stock options with high growth potential',
      'Collaborative and innovative work culture',
      'Career growth and mentorship opportunities'
    ],
    salaryRange: {
      min: 130000,
      max: 170000,
      currency: 'USD'
    },
    remote: true,
    postedAt: '2024-02-15T10:30:00Z',
    matchScore: 75
  }
]
*/

// Mock Applications (simplified for build)
export const mockApplications: Application[] = [
  {
    id: 'app-1',
    userId: 'user-1',
    jobId: '1',
    status: 'submitted',
    submittedAt: '2024-03-02T14:00:00Z',
    notes: 'I am excited to apply for the Senior Frontend Developer position...'
  },
  {
    id: 'app-2',
    userId: 'user-1',
    jobId: '2',
    status: 'under-review',
    submittedAt: '2024-03-01T10:30:00Z',
    notes: 'Looking forward to contributing to your startup...'
  }
]

// Original mock applications (commented out for build fix)
/*
export const originalMockApplications: Application[] = [
  {
    id: 'app-1',
    user_id: 'user-1',
    job_id: '1',
    status: 'interview_scheduled',
    applied_at: '2024-03-02T14:00:00Z',
    cover_letter: 'I am excited to apply for the Senior Frontend Developer position...',
    job: mockJobs[0]
  },
  {
    id: 'app-2',
    user_id: 'user-1',
    job_id: '2',
    status: 'pending',
    applied_at: '2024-03-01T16:30:00Z',
    cover_letter: 'As a passionate full stack developer...',
    job: mockJobs[1]
  },
  {
    id: 'app-3',
    user_id: 'user-1',
    job_id: '3',
    status: 'rejected',
    applied_at: '2024-02-28T09:15:00Z',
    cover_letter: 'I would love to join your backend team...',
    job: mockJobs[2]
  }
]
*/

// Mock Interviews (simplified for build)
export const mockInterviews: Interview[] = [
  {
    id: 'interview-1',
    applicationId: 'app-1',
    jobId: '1',
    userId: 'user-1',
    type: 'ai',
    status: 'scheduled',
    scheduledAt: '2024-03-05T15:00:00Z',
    duration: 60,
    questions: [
      {
        id: 'q1',
        question: 'Tell me about yourself and your experience.',
        type: 'behavioral'
      }
    ]
  }
]

// Original mock interviews (commented out for build fix)
/*
export const originalMockInterviews: Interview[] = [
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
*/

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