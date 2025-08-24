"use client"

import { useState, useEffect } from 'react'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { Job, User } from '@/lib/types'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

// Mock detailed job data
const jobDetails: Record<string, Omit<Job, 'benefits' | 'requirements'> & { 
  fullDescription: string;
  responsibilities: string[];
  skillTags: string[];
  requirements: string[];
  preferred: string[];
  benefits: string;
  companyInfo: string;
  equalOpportunity: string;
  postedDate: string;
}> = {
  '1': {
    id: '1',
    title: 'Operations Analyst, Institutional Private Client',
    company: 'S Corp.',
    location: 'San Francisco, California, United States of America',
    type: 'Full-time',
    category: 'Operations',
    description: 'The Investment Manager Services Division (IMS) at S Corp. is growing rapidly and is seeking new members on our Institutional Private Client (IPC) team.',
    skillTags: ['Finance', 'Analytics', 'Excel', 'Communication'],
    postedAt: new Date().toISOString(),
    postedDate: 'Jun 27th 2025',
    fullDescription: `The Investment Manager Services Division (IMS) at S Corp. is growing rapidly and is seeking new members on our Institutional Private Client (IPC) team. Our primary goal is to provide exceptional administrative services to our high-net-worth clients and institutional investors. This role involves working closely with portfolio managers and client relationship teams to ensure seamless service delivery.`,
    responsibilities: [
      'You will serve as main daily client contact, cultivating and maintaining close relationships with clients through proactive measures and written/verbal communication.',
      'Process and reconcile client transactions, ensuring accuracy and timeliness.',
      'Coordinate with various departments to resolve client inquiries and issues.',
      'Prepare comprehensive reports and presentations for client meetings.'
    ],
    requirements: [
      'Bachelor\'s degree in Finance, Economics, Business or related field.',
      'Minimum 2-3 years of experience in financial services or client operations.',
      'Strong analytical and problem-solving skills with attention to detail.',
      'Proficiency in Microsoft Excel and financial software systems.',
      'Excellent written and verbal communication skills.',
      'Ability to work in a fast-paced environment while maintaining accuracy.'
    ],
    preferred: [
      'Experience with institutional clients and investment operations.',
      'Knowledge of financial markets and investment products.',
      'Professional certifications such as Series 7 or CFA Level I.'
    ],
    benefits: `Benefits include healthcare (medical, dental, vision, prescription, wellness, EAP, FSA), life and disability insurance (premiums paid for base coverage), 401(k) match, education assistance, commuter benefits, up to 11 paid holidays/year, 21 days PTO/year pro-rated for new hires which increases over time, paid parental leave, back-up childcare arrangements, paid volunteer days, a discounted stock purchase plan, investment options, access to thriving employee networks and more.`,
    companyInfo: `After over 50 years in business, S Corp. remains a leading global provider of investment processing, investment management, and investment operations solutions. Reflecting our experience within financial services and financial technology our offices encompass an open floor plan and numerous art installations designed to encourage innovation and creativity in our workforce. We recognize that our people are our most valuable asset and that a healthy, happy, and motivated workforce is key to our continued growth. At S Corp., we're (literally) invested in your success. We offer our employees paid parental leave, back-up childcare arrangements, paid volunteer days, education assistance and access to thriving employee networks.`,
    equalOpportunity: `S Corp. is an equal opportunity employer and all qualified applicants will receive consideration for employment without regard to race, color, religion, sex, sexual orientation, gender identity, national origin, age, disability status, protected veteran status, or any other characteristic protected by law.`
  },
  '2': {
    id: '2',
    title: 'Fund Accountant, Investment Fund Services',
    company: 'S Corp.',
    location: 'Austin, Texas, United States of America',
    type: 'Full-time',
    category: 'Finance',
    description: 'The Investment Manager Services Division (IMS) at S Corp. is growing rapidly and is seeking new members on our Investment Fund Services accounting team.',
    skillTags: ['Accounting', 'Finance', 'Excel', 'Detail-oriented'],
    postedAt: new Date().toISOString(),
    postedDate: 'Jun 25th 2025',
    fullDescription: `The Investment Manager Services Division (IMS) at S Corp. is growing rapidly and is seeking new members on our Investment Fund Services accounting team. Our primary goal is to provide exceptional accounting and administrative services to investment funds and their managers. This role involves complex fund accounting, financial reporting, and regulatory compliance.`,
    responsibilities: [
      'Prepare accurate and timely financial statements for investment funds.',
      'Calculate and verify net asset values (NAV) on a daily basis.',
      'Maintain detailed records of fund transactions and positions.',
      'Coordinate with auditors and regulators for compliance reporting.',
      'Support month-end and year-end closing processes.'
    ],
    requirements: [
      'Bachelor\'s degree in Accounting, Finance, or related field.',
      'Minimum 1-3 years of experience in fund accounting or public accounting.',
      'Strong understanding of investment vehicles and financial instruments.',
      'Proficiency in accounting software and Microsoft Excel.',
      'Detail-oriented with strong analytical and problem-solving skills.',
      'Knowledge of GAAP and regulatory requirements.'
    ],
    preferred: [
      'CPA certification or progress toward certification.',
      'Experience with hedge funds, private equity, or mutual funds.',
      'Knowledge of fund administration systems and processes.'
    ],
    benefits: `Benefits include healthcare (medical, dental, vision, prescription, wellness, EAP, FSA), life and disability insurance (premiums paid for base coverage), 401(k) match, education assistance, commuter benefits, up to 11 paid holidays/year, 21 days PTO/year pro-rated for new hires which increases over time, paid parental leave, back-up childcare arrangements, paid volunteer days, a discounted stock purchase plan, investment options, access to thriving employee networks and more.`,
    companyInfo: `After over 50 years in business, S Corp. remains a leading global provider of investment processing, investment management, and investment operations solutions. Reflecting our experience within financial services and financial technology our offices encompass an open floor plan and numerous art installations designed to encourage innovation and creativity in our workforce. We recognize that our people are our most valuable asset and that a healthy, happy, and motivated workforce is key to our continued growth. At S Corp., we're (literally) invested in your success. We offer our employees paid parental leave, back-up childcare arrangements, paid volunteer days, education assistance and access to thriving employee networks.`,
    equalOpportunity: `S Corp. is an equal opportunity employer and all qualified applicants will receive consideration for employment without regard to race, color, religion, sex, sexual orientation, gender identity, national origin, age, disability status, protected veteran status, or any other characteristic protected by law.`
  },
  '3': {
    id: '3',
    title: 'Operations Analyst, Separately Managed Accounts',
    company: 'S Corp.',
    location: 'New York, New York, United States of America',
    type: 'Full-time',
    category: 'Operations',
    description: 'The Investment Manager Services Division (IMS) at S Corp. is growing rapidly and is seeking new members on our Separately Managed Accounts team.',
    skillTags: ['Operations', 'Analysis', 'Finance', 'Process Improvement'],
    postedAt: new Date().toISOString(),
    postedDate: 'Jun 20th 2025',
    fullDescription: `The Investment Manager Services Division (IMS) at S Corp. is growing rapidly and is seeking new members on our Separately Managed Accounts team. Our primary goal is to provide exceptional accounting and administrative services to separately managed account programs. This role involves portfolio monitoring, trade processing, and client reporting for institutional separately managed accounts.`,
    responsibilities: [
      'Monitor and reconcile separately managed account portfolios on a daily basis.',
      'Process and validate trades and corporate actions for client accounts.',
      'Prepare comprehensive performance and compliance reports for clients.',
      'Coordinate with investment managers and custodians to resolve discrepancies.',
      'Support new account onboarding and client relationship management.'
    ],
    requirements: [
      'Bachelor\'s degree in Finance, Business, Economics or related field.',
      'Minimum 1-2 years of experience in investment operations or financial services.',
      'Understanding of investment products and portfolio management concepts.',
      'Strong analytical skills with proficiency in Excel and database systems.',
      'Excellent attention to detail and ability to work under tight deadlines.',
      'Strong communication skills for client and vendor interactions.'
    ],
    preferred: [
      'Experience with separately managed accounts or wrap fee programs.',
      'Knowledge of compliance and regulatory requirements for investment advisors.',
      'Familiarity with portfolio management systems and custodial platforms.'
    ],
    benefits: `Benefits include healthcare (medical, dental, vision, prescription, wellness, EAP, FSA), life and disability insurance (premiums paid for base coverage), 401(k) match, education assistance, commuter benefits, up to 11 paid holidays/year, 21 days PTO/year pro-rated for new hires which increases over time, paid parental leave, back-up childcare arrangements, paid volunteer days, a discounted stock purchase plan, investment options, access to thriving employee networks and more.`,
    companyInfo: `After over 50 years in business, S Corp. remains a leading global provider of investment processing, investment management, and investment operations solutions. Reflecting our experience within financial services and financial technology our offices encompass an open floor plan and numerous art installations designed to encourage innovation and creativity in our workforce. We recognize that our people are our most valuable asset and that a healthy, happy, and motivated workforce is key to our continued growth. At S Corp., we're (literally) invested in your success. We offer our employees paid parental leave, back-up childcare arrangements, paid volunteer days, education assistance and access to thriving employee networks.`,
    equalOpportunity: `S Corp. is an equal opportunity employer and all qualified applicants will receive consideration for employment without regard to race, color, religion, sex, sexual orientation, gender identity, national origin, age, disability status, protected veteran status, or any other characteristic protected by law.`
  },
  '4': {
    id: '4',
    title: 'Operations Analyst, AML',
    company: 'S Corp.',
    location: 'Seattle, Washington, United States of America',
    type: 'Full-time',
    category: 'Operations',
    description: 'The Investment Manager Services Division (IMS) at S Corp. is growing rapidly and is seeking new members on our Alternative Investment Funds Investor Services Anti-Money Laundering Team.',
    skillTags: ['AML', 'Compliance', 'Risk Management', 'Investigation'],
    postedAt: new Date().toISOString(),
    postedDate: 'Jun 18th 2025',
    fullDescription: `The Investment Manager Services Division (IMS) at S Corp. is growing rapidly and is seeking new members on our Alternative Investment Funds Investor Services Anti-Money Laundering Team. Our primary goal is to ensure compliance with anti-money laundering regulations and protect our clients and firm from financial crimes. This role involves monitoring transactions, conducting investigations, and maintaining compliance with regulatory requirements.`,
    responsibilities: [
      'Monitor client transactions and identify suspicious activity patterns.',
      'Conduct thorough investigations of potentially suspicious activities.',
      'Prepare detailed Suspicious Activity Reports (SARs) for regulatory filing.',
      'Maintain up-to-date knowledge of AML regulations and industry best practices.',
      'Collaborate with compliance team and external regulators as needed.',
      'Support client onboarding and enhanced due diligence processes.'
    ],
    requirements: [
      'Bachelor\'s degree in Finance, Criminal Justice, Business or related field.',
      'Minimum 2-3 years of experience in AML, compliance, or financial crimes investigation.',
      'Strong understanding of AML regulations including BSA, OFAC, and FinCEN requirements.',
      'Experience with transaction monitoring systems and investigative techniques.',
      'Excellent analytical and critical thinking skills.',
      'Strong written communication skills for report writing and documentation.'
    ],
    preferred: [
      'CAMS (Certified Anti-Money Laundering Specialist) certification.',
      'Experience with alternative investments, hedge funds, or private equity.',
      'Knowledge of international AML regulations and sanctions programs.',
      'Experience with regulatory examinations and audit processes.'
    ],
    benefits: `Benefits include healthcare (medical, dental, vision, prescription, wellness, EAP, FSA), life and disability insurance (premiums paid for base coverage), 401(k) match, education assistance, commuter benefits, up to 11 paid holidays/year, 21 days PTO/year pro-rated for new hires which increases over time, paid parental leave, back-up childcare arrangements, paid volunteer days, a discounted stock purchase plan, investment options, access to thriving employee networks and more.`,
    companyInfo: `After over 50 years in business, S Corp. remains a leading global provider of investment processing, investment management, and investment operations solutions. Reflecting our experience within financial services and financial technology our offices encompass an open floor plan and numerous art installations designed to encourage innovation and creativity in our workforce. We recognize that our people are our most valuable asset and that a healthy, happy, and motivated workforce is key to our continued growth. At S Corp., we're (literally) invested in your success. We offer our employees paid parental leave, back-up childcare arrangements, paid volunteer days, education assistance and access to thriving employee networks.`,
    equalOpportunity: `S Corp. is an equal opportunity employer and all qualified applicants will receive consideration for employment without regard to race, color, religion, sex, sexual orientation, gender identity, national origin, age, disability status, protected veteran status, or any other characteristic protected by law.`
  },
  '5': {
    id: '5',
    title: 'Senior Software Engineer',
    company: 'S Corp.',
    location: 'Boston, Massachusetts, United States of America',
    type: 'Full-time',
    category: 'Engineering',
    description: 'Join our engineering team to build scalable web applications using React, Node.js, and cloud technologies.',
    skillTags: ['React', 'Node.js', 'JavaScript', 'AWS', 'TypeScript'],
    postedAt: new Date().toISOString(),
    postedDate: 'Jun 15th 2025',
    fullDescription: `Join our engineering team to build scalable web applications using React, Node.js, and cloud technologies. We\'re looking for someone with 5+ years of experience in full-stack development and cloud architecture. You\'ll be working on cutting-edge financial technology solutions that serve institutional clients and investment managers globally.`,
    responsibilities: [
      'Design and develop scalable web applications using modern JavaScript frameworks.',
      'Build robust APIs and microservices using Node.js and cloud technologies.',
      'Collaborate with product managers and designers to deliver exceptional user experiences.',
      'Implement automated testing and CI/CD pipelines to ensure code quality.',
      'Mentor junior developers and contribute to technical architecture decisions.',
      'Participate in code reviews and maintain high standards for code quality and security.'
    ],
    requirements: [
      'Bachelor\'s degree in Computer Science, Engineering, or related field.',
      'Minimum 5+ years of experience in full-stack web development.',
      'Expertise in React, TypeScript/JavaScript, Node.js, and modern web technologies.',
      'Experience with cloud platforms (AWS, Azure, or GCP) and containerization.',
      'Strong understanding of software architecture, design patterns, and best practices.',
      'Experience with database technologies (SQL and NoSQL).',
      'Excellent problem-solving skills and attention to detail.'
    ],
    preferred: [
      'Experience in financial services or fintech industry.',
      'Knowledge of microservices architecture and distributed systems.',
      'Experience with DevOps practices and infrastructure as code.',
      'Familiarity with regulatory requirements and security best practices.',
      'Open source contributions and technical leadership experience.'
    ],
    benefits: `Benefits include healthcare (medical, dental, vision, prescription, wellness, EAP, FSA), life and disability insurance (premiums paid for base coverage), 401(k) match, education assistance, commuter benefits, up to 11 paid holidays/year, 21 days PTO/year pro-rated for new hires which increases over time, paid parental leave, back-up childcare arrangements, paid volunteer days, a discounted stock purchase plan, investment options, access to thriving employee networks and more.`,
    companyInfo: `After over 50 years in business, S Corp. remains a leading global provider of investment processing, investment management, and investment operations solutions. Reflecting our experience within financial services and financial technology our offices encompass an open floor plan and numerous art installations designed to encourage innovation and creativity in our workforce. We recognize that our people are our most valuable asset and that a healthy, happy, and motivated workforce is key to our continued growth. At S Corp., we're (literally) invested in your success. We offer our employees paid parental leave, back-up childcare arrangements, paid volunteer days, education assistance and access to thriving employee networks.`,
    equalOpportunity: `S Corp. is an equal opportunity employer and all qualified applicants will receive consideration for employment without regard to race, color, religion, sex, sexual orientation, gender identity, national origin, age, disability status, protected veteran status, or any other characteristic protected by law.`
  }
}

// Mock similar jobs data
const similarJobs = [
  {
    id: '2',
    title: 'Specialist I, Reconciliation',
    location: 'Oaks, Pennsylvania, United States of America',
    type: 'Full time'
  },
  {
    id: '3', 
    title: 'Operations Analyst, Enhanced Middle Office (Bank Debt)',
    location: 'Oaks, Pennsylvania, United States of America',
    type: 'Full time'
  }
]

const jobSeekersViewed = [
  {
    id: '4',
    title: 'Operations Analyst, Separately Managed Accounts',
    location: 'Oaks, Pennsylvania, United States of America', 
    type: 'Full time'
  },
  {
    id: '5',
    title: 'Operations Analyst, AIFS Investor Services',
    location: 'Oaks, Pennsylvania, United States of America',
    type: 'Full time'  
  },
  {
    id: '6',
    title: 'Operations Analyst, Enhanced Middle Office (Bank Debt)',
    location: 'Oaks, Pennsylvania, United States of America',
    type: 'Full time'
  }
]

interface JobDetailProps {
  params: Promise<{
    id: string
  }>
}

export default function JobDetailPage({ params }: JobDetailProps) {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(false)
  const [resolvedParams, setResolvedParams] = useState<{ id: string } | null>(null)
  
  useEffect(() => {
    params.then(setResolvedParams)
  }, [params])
  
  const job = resolvedParams ? jobDetails[resolvedParams.id] : null
  
  useEffect(() => {
    // Get user from localStorage
    const userData = localStorage.getItem('user')
    if (userData) {
      const parsedUser = JSON.parse(userData)
      setUser(parsedUser)
    }
  }, [])

  if (!resolvedParams || !job) {
    return (
      <div className="page-light min-h-screen">
        <Navigation userState="guest" user={null} theme="light" />
        <main className="container max-w-[1400px] mx-auto px-6 pt-20">
          <div className="text-center py-20">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Job Not Found</h1>
            <p className="text-gray-600 mb-6">The job you're looking for doesn't exist or has been removed.</p>
            <Link href="/jobs">
              <Button variant="primary">Back to Jobs</Button>
            </Link>
          </div>
        </main>
      </div>
    )
  }

  const isGuest = !user
  const userState = isGuest ? "guest" : (user.isResumeAvailable ? "has-resume" : "no-resume")

  const handleApplyNow = () => {
    if (!resolvedParams) return
    
    if (isGuest) {
      // Show login modal or redirect to login
      router.push(`/login?redirect=/apply/${resolvedParams.id}`)
    } else {
      // Redirect to application page
      router.push(`/apply/${resolvedParams.id}`)
    }
  }

  const handleBackToSearch = () => {
    if (user?.isResumeAvailable) {
      router.push('/jobs/matched')
    } else {
      router.push('/jobs')
    }
  }

  return (
    <div className="page-light min-h-screen">
      <Navigation userState={userState} user={user} theme="light" />
      
      <main className="container max-w-[1400px] mx-auto px-6 pt-20 pb-8">
        {/* Two-column layout */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            {/* Job Header */}
            <div className="mb-8">
              <h1 className="text-4xl font-bold text-red-600 mb-4 leading-tight">
                {job.title}
              </h1>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                <div className="flex flex-wrap items-center gap-6 text-sm text-gray-600">
                  <span className="flex items-center gap-1">
                    📅 {job.postedDate}
                  </span>
                  <span className="flex items-center gap-1">
                    📍 {job.location}
                  </span>
                  <span className="flex items-center gap-1">
                    🕐 {job.type}
                  </span>
                </div>
                <Button 
                  variant="primary" 
                  size="lg"
                  onClick={handleApplyNow}
                  disabled={loading}
                >
                  {loading ? 'Loading...' : 'Apply Now'}
                </Button>
              </div>
            </div>

            {/* Navigation */}
            <div className="flex justify-between items-center mb-8 text-sm text-red-600">
              <button
                onClick={handleBackToSearch}
                className="flex items-center gap-2 hover:text-red-700 transition-colors"
              >
                ← Back to search results
              </button>
              <div className="flex gap-4">
                <button className="hover:text-red-700 transition-colors">
                  ← Previous job
                </button>
                <button className="hover:text-red-700 transition-colors">
                  Next job →
                </button>
              </div>
            </div>

            {/* Job Description */}
            <div className="text-gray-700 leading-relaxed space-y-6">
              <p>{job.fullDescription}</p>

              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">What you will do:</h3>
                <ul className="list-disc pl-6 space-y-2">
                  {job.responsibilities.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </div>

              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">What we need from you:</h3>
                <ul className="list-disc pl-6 space-y-2">
                  {job.requirements.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </div>

              {job.preferred.length > 0 && (
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-4">What we would like from you:</h3>
                  <ul className="list-disc pl-6 space-y-2">
                    {job.preferred.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              <p>{job.benefits}</p>

              <p>
                We are a technology and asset management company delivering on our promise of building brave futures (SM)—
                for our clients, our communities, and ourselves. Come build your brave future at S Corp..
              </p>

              <p>S Corp. is an Equal Opportunity Employer and so much more...</p>

              <p>{job.companyInfo}</p>

              <p>{job.equalOpportunity}</p>

              <Button variant="secondary" className="bg-red-600 hover:bg-red-700 text-white">
                📍 Explore Location
              </Button>
            </div>
          </div>

          {/* Sidebar */}
          <aside className="lg:col-span-1">
            {/* Similar Jobs */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
              <h4 className="font-semibold text-gray-900 mb-4">Similar Jobs</h4>
              <div className="space-y-4">
                {similarJobs.map((similarJob) => (
                  <div key={similarJob.id} className="pb-4 border-b border-gray-200 last:border-b-0 last:pb-0">
                    <Link href={`/jobs/${similarJob.id}`}>
                      <h5 className="text-red-600 hover:text-red-700 underline text-sm font-medium mb-2 cursor-pointer">
                        {similarJob.title}
                      </h5>
                    </Link>
                    <div className="text-gray-600 text-xs space-y-1">
                      <div className="flex items-center gap-1">
                        📍 {similarJob.location}
                      </div>
                      <div className="flex items-center gap-1">
                        🕐 {similarJob.type}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Job seekers also viewed */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
              <h4 className="font-semibold text-gray-900 mb-4">Job seekers also viewed</h4>
              <div className="space-y-4">
                {jobSeekersViewed.map((viewedJob) => (
                  <div key={viewedJob.id} className="pb-4 border-b border-gray-200 last:border-b-0 last:pb-0">
                    <Link href={`/jobs/${viewedJob.id}`}>
                      <h5 className="text-red-600 hover:text-red-700 underline text-sm font-medium mb-2 cursor-pointer">
                        {viewedJob.title}
                      </h5>
                    </Link>
                    <div className="text-gray-600 text-xs space-y-1">
                      <div className="flex items-center gap-1">
                        📍 {viewedJob.location}
                      </div>
                      <div className="flex items-center gap-1">
                        🕐 {viewedJob.type}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Share this opportunity */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h4 className="font-semibold text-gray-900">Share this opportunity</h4>
            </div>
          </aside>
        </div>
      </main>
    </div>
  )
}