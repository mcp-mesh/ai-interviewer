"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { WireframeButton } from '@/components/wireframe'
import { JobCard } from '@/components/job-card'
import { jobsApi } from '@/lib/api'
import { Job, User } from '@/lib/types'
import Link from 'next/link'

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [featuredJobs, setFeaturedJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Get user from localStorage (in a real app, use proper auth context)
    const userData = localStorage.getItem('user')
    if (userData) {
      const parsedUser = JSON.parse(userData)
      setUser(parsedUser)
      
      // Fetch dashboard data
      fetchDashboardData()
    } else {
      // Redirect to login if no user found
      window.location.href = '/login?redirect=/dashboard'
    }
  }, [])

  // Show different dashboard based on user state
  const hasResume = user?.isResumeAvailable || false
  const hasApplications = user?.isApplicationsAvailable || false

  // Mock top matches for dashboard
  const topMatches: Job[] = [
    {
      id: '1',
      title: 'Senior Software Engineer',
      company: 'TechCorp',
      location: 'San Francisco, CA',
      type: 'Full-time',
      category: 'Engineering',
      description: 'Perfect match for your React and Node.js expertise. Join our team building scalable web applications.',
      requirements: ['React', 'Node.js', 'TypeScript', 'AWS'],
      matchScore: 95,
      salaryRange: { min: 140, max: 180, currency: 'USD' },
      postedAt: new Date().toISOString()
    },
    {
      id: '2', 
      title: 'Lead Frontend Developer',
      company: 'RemoteFirst Inc',
      location: 'Remote',
      type: 'Full-time',
      category: 'Engineering',
      description: 'Remote-first role focusing on React architecture and team leadership.',
      requirements: ['React', 'JavaScript', 'CSS', 'Leadership'],
      matchScore: 92,
      salaryRange: { min: 130, max: 170, currency: 'USD' },
      postedAt: new Date().toISOString()
    },
    {
      id: '3',
      title: 'Full Stack Engineer', 
      company: 'StartupCo',
      location: 'Palo Alto, CA',
      type: 'Full-time',
      category: 'Engineering',
      description: 'Startup environment with modern tech stack and significant growth opportunity.',
      requirements: ['React', 'Node.js', 'MongoDB', 'Docker'],
      matchScore: 90,
      salaryRange: { min: 125, max: 165, currency: 'USD' },
      postedAt: new Date().toISOString()
    }
  ]

  const fetchDashboardData = async () => {
    setLoading(true)
    
    try {
      const jobsResponse = await jobsApi.getFeatured()
      if (jobsResponse.data) {
        setFeaturedJobs(jobsResponse.data.slice(0, 3))
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    }
    
    setLoading(false)
  }

  const handleUploadResume = () => {
    router.push('/upload')
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card>
          <CardContent className="text-center py-8">
            <p className="mb-4">Please log in to view your dashboard</p>
            <WireframeButton onClick={() => router.push('/login')} variant="primary">Go to Login</WireframeButton>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Show resume upload dashboard if no resume
  if (!hasResume) {
    return (
      <div className="page-light min-h-screen">
        <Navigation userState="authenticated" user={user} theme="light" />
        
        <main className="container max-w-[900px] mx-auto px-6 pt-20">
          <div className="py-12">
            {/* Welcome Section */}
            <div className="mb-12">
              <h1 className="text-2xl font-bold text-[#1f2937] mb-2">
                Welcome to S Corp., {user?.name?.split(' ')[0]}! 👋
              </h1>
              <p className="text-[#6b7280] text-lg">
                Let's get you set up to find your perfect job match
              </p>
            </div>

            {/* Upload Resume CTA - Main Focus */}
            <div className="bg-blue-50 border border-blue-200 rounded-2xl p-12 mb-12 text-center">
              <div className="max-w-2xl mx-auto">
                <div className="text-5xl mb-4">📄</div>
                <h2 className="text-3xl font-bold mb-4">
                  Upload Your Resume to Unlock AI-Powered Matching
                </h2>
                <p className="text-lg mb-8 leading-relaxed text-gray-600">
                  Get personalized job recommendations, instant match scores, and AI-powered application assistance by uploading your resume.
                </p>
                <WireframeButton 
                  onClick={handleUploadResume}
                  variant="primary"
                  size="lg"
                  className="px-8 py-3 text-base"
                >
                  Upload Resume Now
                </WireframeButton>
              </div>
            </div>

            {/* Benefits Grid */}
            <div className="mb-12">
              <h3 className="text-2xl font-semibold text-gray-900 mb-8 text-center">
                What happens after you upload your resume?
              </h3>
              
              <div className="grid md:grid-cols-3 gap-8">
                <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6 text-2xl">🎯</div>
                  <h4 className="text-xl font-semibold text-gray-900 mb-4">Smart Job Matching</h4>
                  <p className="text-gray-600 leading-relaxed">Our AI analyzes your skills and experience to find the most relevant job opportunities with match scores.</p>
                </div>

                <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6 text-2xl">⚡</div>
                  <h4 className="text-xl font-semibold text-gray-900 mb-4">Auto-Fill Applications</h4>
                  <p className="text-gray-600 leading-relaxed">Save time with AI-powered application forms that automatically fill in your information from your resume.</p>
                </div>

                <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
                  <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-6 text-2xl">🤖</div>
                  <h4 className="text-xl font-semibold text-gray-900 mb-4">AI-Powered Interviews</h4>
                  <p className="text-gray-600 leading-relaxed">Experience streamlined interviews with our AI interviewer that provides instant feedback and faster hiring decisions.</p>
                </div>
              </div>
            </div>

            {/* Current Status Card */}
            <div className="bg-white border border-gray-200 rounded-xl p-8 mb-12">
              <h3 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
                📊 Your Profile Status
              </h3>
              
              <div className="grid md:grid-cols-3 gap-8">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-700 font-medium">Profile Completion</span>
                    <span className="text-gray-500 text-sm">25%</span>
                  </div>
                  <div className="bg-gray-200 rounded-lg h-2 overflow-hidden">
                    <div className="bg-blue-500 h-full w-1/4 rounded-lg"></div>
                  </div>
                  <p className="text-gray-500 text-sm mt-2">Upload your resume to boost your profile to 85%</p>
                </div>
                
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-700 font-medium">Job Matches Found</span>
                    <span className="text-yellow-500 font-semibold">0</span>
                  </div>
                  <p className="text-gray-500 text-sm">Complete your profile to see personalized matches</p>
                </div>
                
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-700 font-medium">Applications Submitted</span>
                    <span className="text-gray-500 font-semibold">0</span>
                  </div>
                  <p className="text-gray-500 text-sm">Start applying once you upload your resume</p>
                </div>
              </div>
            </div>

            {/* Next Steps */}
            <div className="bg-white border border-gray-200 rounded-xl p-8 mb-12">
              <h3 className="text-xl font-semibold text-gray-900 mb-6">
                Recommended Next Steps
              </h3>
              
              <div className="space-y-4">
                <div className="flex items-center gap-4 p-4 bg-yellow-50 rounded-lg">
                  <div className="w-8 h-8 bg-yellow-500 text-white rounded-full flex items-center justify-center font-semibold text-sm">1</div>
                  <div>
                    <h4 className="font-semibold text-yellow-800 mb-1">Upload Your Resume</h4>
                    <p className="text-yellow-700 text-sm">This unlocks personalized job matching and AI features</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
                  <div className="w-8 h-8 bg-gray-400 text-white rounded-full flex items-center justify-center font-semibold text-sm">2</div>
                  <div>
                    <h4 className="font-semibold text-gray-600 mb-1">Browse Matched Positions</h4>
                    <p className="text-gray-500 text-sm">See jobs ranked by AI compatibility scores</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
                  <div className="w-8 h-8 bg-gray-400 text-white rounded-full flex items-center justify-center font-semibold text-sm">3</div>
                  <div>
                    <h4 className="font-semibold text-gray-600 mb-1">Apply with AI Assistance</h4>
                    <p className="text-gray-500 text-sm">Use auto-fill and get AI interview preparation</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    )
  }

  // Show "has resume" dashboard
  return (
    <div className="page-light min-h-screen">
      <Navigation userState="authenticated" user={user} theme="light" />
      
      <main className="container max-w-[900px] mx-auto px-6 pt-20">
        <div className="py-12">
          {/* Welcome Section */}
          <div className="mb-12">
            <h1 className="text-2xl font-bold text-[#1f2937] mb-2">
              Welcome back, {user?.name?.split(' ')[0]}! 👋
            </h1>
            <p className="text-[#6b7280] text-lg">
              Your profile is ready - let's find your perfect match
            </p>
          </div>

          {/* Profile Summary Card */}
          <div className="bg-white border border-[#e5e7eb] rounded-xl p-8 mb-12">
            <div className="flex justify-between items-start mb-8">
              <h3 className="text-[1.5rem] font-semibold text-[#1f2937] flex items-center gap-2">
                📄 Your Profile Summary
              </h3>
              <WireframeButton 
                onClick={handleUploadResume}
                variant="secondary"
                size="sm"
                className="text-sm"
              >
                Update Resume
              </WireframeButton>
            </div>
            
            <div className="grid md:grid-cols-4 gap-8">
              <div>
                <h4 className="font-semibold text-[#1f2937] mb-2">Experience Level</h4>
                <p className="text-[#6b7280] text-sm">Senior (5+ years)</p>
              </div>
              
              <div>
                <h4 className="font-semibold text-[#1f2937] mb-2">Primary Skills</h4>
                <div className="flex flex-wrap gap-2 mt-2">
                  <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">JavaScript</span>
                  <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">React</span>
                  <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">Node.js</span>
                  <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">AWS</span>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold text-[#1f2937] mb-2">Preferred Location</h4>
                <p className="text-[#6b7280] text-sm">San Francisco, CA (Remote OK)</p>
              </div>
              
              <div>
                <h4 className="font-semibold text-[#1f2937] mb-2">Salary Range</h4>
                <p className="text-[#6b7280] text-sm">$120k - $180k</p>
              </div>
            </div>
          </div>

          {/* Current Status Card */}
          <div className="bg-white border border-[#e5e7eb] rounded-xl p-8 mb-12">
            <h3 className="text-[1.25rem] font-semibold text-[#1f2937] mb-6 flex items-center gap-2">
              📊 Your Profile Status
            </h3>
            
            <div className="grid md:grid-cols-3 gap-8">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-[#374151] font-medium">Profile Completion</span>
                  <span className="text-[#10b981] text-sm font-semibold">85%</span>
                </div>
                <div className="bg-[#f3f4f6] rounded-lg h-2 overflow-hidden">
                  <div className="bg-[#10b981] h-full w-[85%] rounded-lg"></div>
                </div>
                <p className="text-[#6b7280] text-sm mt-2">Great! Your profile is nearly complete</p>
              </div>
              
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-[#374151] font-medium">Job Matches Found</span>
                  <span className="text-[#3b82f6] font-semibold text-xl">24</span>
                </div>
                <p className="text-[#6b7280] text-sm">Including 8 positions with 90%+ match scores</p>
              </div>
              
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-[#374151] font-medium">Applications Submitted</span>
                  <span className="text-[#f59e0b] font-semibold">0</span>
                </div>
                <p className="text-[#6b7280] text-sm">Ready to start applying to your matches</p>
              </div>
            </div>
          </div>

          {/* AI Matches Section */}
          <div className="bg-blue-50 border border-blue-200 rounded-2xl p-10 mb-12 text-center">
            <div className="max-w-2xl mx-auto">
              <div className="text-5xl mb-4">🎯</div>
              <h2 className="text-3xl font-bold mb-4">
                We Found 24 Perfect Matches for You!
              </h2>
              <p className="text-lg mb-8 leading-relaxed text-[#374151]">
                Based on your resume, our AI has identified positions that match your skills, experience, and preferences.
              </p>
              <WireframeButton 
                onClick={() => router.push('/jobs')}
                variant="primary"
                size="lg"
                className="px-8 py-3 text-base"
              >
                Browse Your Matches
              </WireframeButton>
            </div>
          </div>

          {/* Top Matches Preview */}
          <div className="bg-white border border-[#e5e7eb] rounded-xl p-8 mb-12">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-[1.25rem] font-semibold text-[#1f2937]">Your Top Matches</h3>
              <Link href="/jobs" className="text-[#3b82f6] hover:text-blue-700 font-medium text-sm">
                View All 24 →
              </Link>
            </div>
            
            <div className="space-y-4">
              {topMatches.map((job) => (
                <JobCard 
                  key={job.id}
                  job={job}
                  variant="dashboard"
                  showMatchScore={true}
                />
              ))}
            </div>
          </div>

          {/* Next Steps */}
          <div className="bg-white border border-[#e5e7eb] rounded-xl p-8">
            <h3 className="text-[1.25rem] font-semibold text-[#1f2937] mb-6">
              Recommended Next Steps
            </h3>
            
            <div className="space-y-4">
              <div className="flex items-center gap-4 p-4 bg-yellow-50 rounded-lg">
                <div className="w-8 h-8 bg-[#f59e0b] text-white rounded-full flex items-center justify-center font-semibold text-sm">1</div>
                <div>
                  <h4 className="font-semibold text-[#92400e] mb-1">Review Your Top Matches</h4>
                  <p className="text-[#78350f] text-sm">24 positions are waiting for you with high match scores</p>
                </div>
              </div>
              
              <div className="flex items-center gap-4 p-4 bg-[#f3f4f6] rounded-lg">
                <div className="w-8 h-8 bg-[#9ca3af] text-white rounded-full flex items-center justify-center font-semibold text-sm">2</div>
                <div>
                  <h4 className="font-semibold text-[#4b5563] mb-1">Apply to Your Favorites</h4>
                  <p className="text-[#6b7280] text-sm">Use AI-powered application assistance for faster submissions</p>
                </div>
              </div>
              
              <div className="flex items-center gap-4 p-4 bg-[#f3f4f6] rounded-lg">
                <div className="w-8 h-8 bg-[#9ca3af] text-white rounded-full flex items-center justify-center font-semibold text-sm">3</div>
                <div>
                  <h4 className="font-semibold text-[#4b5563] mb-1">Schedule AI Interviews</h4>
                  <p className="text-[#6b7280] text-sm">Get instant feedback and move forward faster</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}