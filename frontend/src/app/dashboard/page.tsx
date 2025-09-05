"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { jobsApi } from '@/lib/api'
import { User } from '@/lib/types'
import { FileText, Target, Zap, Bot, BarChart3, User as UserIcon } from 'lucide-react'

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  // const [featuredJobs, setFeaturedJobs] = useState<Job[]>([])

  useEffect(() => {
    // Get user data from API using session-based authentication
    const fetchUserData = async () => {
      try {
        const { userApi } = await import('@/lib/api')
        const result = await userApi.getProfile()
        
        if (result.data) {
          setUser(result.data)
          // Store real user data in localStorage for other pages to access
          localStorage.setItem('user', JSON.stringify(result.data))
          // Fetch dashboard data after getting user
          fetchDashboardData()
          setLoading(false)
        } else {
          // No user data found, redirect to login
          window.location.href = '/login?redirect=/dashboard'
        }
      } catch (error) {
        console.error('Failed to fetch user data:', error)
        // API call failed (likely not authenticated), redirect to login
        window.location.href = '/login?redirect=/dashboard'
      }
    }

    fetchUserData()
  }, [])

  // Show different dashboard based on user state
  const hasResume = user?.hasResume || false
  // const hasApplications = user?.isApplicationsAvailable || false

  // Dynamic profile status calculations
  const getProfileCompletion = () => {
    if (!user) return { percentage: 0, text: 'Please log in' }
    
    if (user.applications && user.applications.length > 0) {
      return { 
        percentage: 100, 
        text: 'Profile complete - actively applying!',
        color: 'text-green-600'
      }
    } else if (user.hasResume) {
      return { 
        percentage: 60, 
        text: 'Great! Start applying to boost to 100%',
        color: 'text-blue-600'
      }
    } else {
      return { 
        percentage: 25, 
        text: 'Upload your resume to boost your profile to 60%',
        color: 'text-gray-500'
      }
    }
  }

  const getJobMatchesCount = () => {
    if (!user) return 0
    // If user has resume, show matched jobs count, otherwise show available jobs
    if (user.hasResume) {
      return user.matchedJobs || 0
    } else {
      return user.availableJobs || 0
    }
  }

  const getApplicationsCount = () => {
    if (!user) return 0
    return user.applications ? user.applications.length : 0
  }

  const profileStatus = getProfileCompletion()
  const jobMatchesCount = getJobMatchesCount()
  const applicationsCount = getApplicationsCount()


  const fetchDashboardData = async () => {
    // setLoading(true) // TODO: May be needed for future functionality
    
    try {
      const jobsResponse = await jobsApi.getFeatured()
      if (jobsResponse.data) {
        // setFeaturedJobs(jobsResponse.data.slice(0, 3)) // TODO: May be needed for future functionality
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    }
    
    // setLoading(false) // TODO: May be needed for future functionality
  }

  const handleUploadResume = () => {
    router.push('/upload')
  }

  if (loading) {
    return (
      <div className="page-light min-h-screen">
        <Navigation userState="guest" user={null} theme="light" />
        <main className="container max-w-[900px] mx-auto px-6 pt-20">
          <div className="py-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading your dashboard...</p>
          </div>
        </main>
      </div>
    )
  }

  // Show resume upload dashboard if no resume
  if (!hasResume) {
    return (
      <div className="page-light min-h-screen">
        <Navigation userState="has-resume" user={user} theme="light" currentPage="dashboard" />
        
        <main className="container max-w-[900px] mx-auto px-6 pt-20">
          <div className="py-12">
            {/* Welcome Section */}
            <div className="mb-12">
              <h1 className="text-2xl font-bold text-[#1f2937] mb-2">
                Welcome to S Corp., {user?.name?.split(' ')[0]}!
              </h1>
              <p className="text-[#6b7280] text-lg">
                Let&apos;s get you set up to find your perfect job match
              </p>
            </div>

            {/* Upload Resume CTA - Main Focus */}
            <div className="bg-blue-50 border border-blue-200 rounded-2xl p-12 mb-12 text-center">
              <div className="max-w-2xl mx-auto">
                <FileText className="w-16 h-16 mb-4 mx-auto text-primary-500" />
                <h2 className="text-3xl font-bold mb-4">
                  Upload Your Resume to Unlock AI-Powered Matching
                </h2>
                <p className="text-lg mb-8 leading-relaxed text-gray-600">
                  Get personalized job recommendations, instant match scores, and AI-powered application assistance by uploading your resume.
                </p>
                <Button 
                  onClick={handleUploadResume}
                  variant="primary"
                  size="lg"
                  className="px-8 py-3 text-base"
                >
                  Upload Resume Now
                </Button>
              </div>
            </div>

            {/* Benefits Grid */}
            <div className="mb-12">
              <h3 className="text-2xl font-semibold text-gray-900 mb-8 text-center">
                What happens after you upload your resume?
              </h3>
              
              <div className="grid md:grid-cols-3 gap-8">
                <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Target className="w-8 h-8 text-blue-600" />
                  </div>
                  <h4 className="text-xl font-semibold text-gray-900 mb-4">Smart Job Matching</h4>
                  <p className="text-gray-600 leading-relaxed">Our AI analyzes your skills and experience to find the most relevant job opportunities with match scores.</p>
                </div>

                <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Zap className="w-8 h-8 text-green-600" />
                  </div>
                  <h4 className="text-xl font-semibold text-gray-900 mb-4">Auto-Fill Applications</h4>
                  <p className="text-gray-600 leading-relaxed">Save time with AI-powered application forms that automatically fill in your information from your resume.</p>
                </div>

                <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
                  <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Bot className="w-8 h-8 text-yellow-600" />
                  </div>
                  <h4 className="text-xl font-semibold text-gray-900 mb-4">AI-Powered Interviews</h4>
                  <p className="text-gray-600 leading-relaxed">Experience streamlined interviews with our AI interviewer that provides instant feedback and faster hiring decisions.</p>
                </div>
              </div>
            </div>

            {/* Current Status Card */}
            <div className="bg-white border border-gray-200 rounded-xl p-8 mb-12">
              <h3 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-success-600" /> Your Profile Status
              </h3>
              
              <div className="grid md:grid-cols-3 gap-8">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-700 font-medium">Profile Completion</span>
                    <span className={`text-sm font-semibold ${profileStatus.color}`}>{profileStatus.percentage}%</span>
                  </div>
                  <div className="bg-gray-200 rounded-lg h-2 overflow-hidden">
                    <div className="bg-blue-500 h-full rounded-lg" style={{width: `${profileStatus.percentage}%`}}></div>
                  </div>
                  <p className="text-gray-500 text-sm mt-2">{profileStatus.text}</p>
                </div>
                
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-700 font-medium">Job Matches Found</span>
                    <span className={`font-semibold ${jobMatchesCount > 0 ? 'text-blue-600' : 'text-yellow-500'}`}>{jobMatchesCount}</span>
                  </div>
                  <p className="text-gray-500 text-sm">
                    {jobMatchesCount > 0 ? `Including ${user?.matchedJobs || 0} high-match positions` : 'Complete your profile to see personalized matches'}
                  </p>
                </div>
                
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-700 font-medium">Applications Submitted</span>
                    <span className={`font-semibold ${applicationsCount > 0 ? 'text-green-600' : 'text-gray-500'}`}>{applicationsCount}</span>
                  </div>
                  <p className="text-gray-500 text-sm">
                    {applicationsCount > 0 ? 'Great progress on your applications!' : 'Start applying once you upload your resume'}
                  </p>
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
      <Navigation userState="has-resume" user={user} theme="light" currentPage="dashboard" />
      
      <main className="container max-w-[900px] mx-auto px-6 pt-20">
        <div className="py-12">
          {/* Welcome Section */}
          <div className="mb-12">
            <h1 className="text-2xl font-bold text-[#1f2937] mb-2">
              Welcome back, {user?.name?.split(' ')[0]}!
            </h1>
            <p className="text-[#6b7280] text-lg">
              Your profile is ready - let&apos;s find your perfect match
            </p>
          </div>

          {/* Conditional Content Based on Resume Status */}
          {!hasResume ? (
            <>
              {/* Upload Resume CTA - Main Focus */}
              <div className="bg-blue-50 border border-blue-200 rounded-2xl p-12 mb-12 text-center">
                <div className="max-w-2xl mx-auto">
                  <FileText className="w-16 h-16 mb-4 mx-auto text-primary-500" />
                  <h2 className="text-3xl font-bold mb-4">
                    Upload Your Resume to Unlock AI-Powered Matching
                  </h2>
                  <p className="text-lg mb-8 leading-relaxed text-gray-600">
                    Get personalized job recommendations, instant match scores, and AI-powered application assistance by uploading your resume.
                  </p>
                  <Button 
                    onClick={handleUploadResume}
                    variant="primary"
                    size="lg"
                    className="px-8 py-3 text-base"
                  >
                    Upload Resume Now
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <>
              {/* AI Resume Analysis Card */}
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-8 mb-12">
                <div className="flex justify-between items-start mb-6">
                  <h3 className="text-[1.5rem] font-semibold text-[#1f2937] flex items-center gap-2">
                    <Bot className="w-6 h-6 text-blue-600" /> AI Profile Analysis
                  </h3>
                  <Button 
                    onClick={handleUploadResume}
                    variant="gray"
                    size="sm"
                    className="text-sm"
                  >
                    Update Resume
                  </Button>
                </div>
                
                {/* Professional Summary */}
                <div className="mb-8">
                  <p className="text-[#374151] leading-relaxed text-base">
                    {user?.resume_analysis?.professional_summary || "Professional summary will appear here after AI analysis."}
                  </p>
                </div>
                
                {/* Key Stats */}
                <div className="grid md:grid-cols-3 gap-6 mb-6">
                  <div className="bg-white rounded-lg p-4 border border-blue-100">
                    <div className="flex items-center gap-2 mb-2">
                      <Target className="w-5 h-5 text-green-600" />
                      <span className="font-semibold text-[#1f2937]">Experience</span>
                    </div>
                    <p className="text-2xl font-bold text-green-600">{user?.resume_analysis?.years_experience || 0}</p>
                    <p className="text-sm text-gray-600">Years</p>
                  </div>
                  
                  <div className="bg-white rounded-lg p-4 border border-blue-100">
                    <div className="flex items-center gap-2 mb-2">
                      <UserIcon className="w-5 h-5 text-purple-600" />
                      <span className="font-semibold text-[#1f2937]">Level</span>
                    </div>
                    <p className="text-xl font-bold text-purple-600 capitalize">{user?.resume_analysis?.experience_level || "Not specified"}</p>
                    <p className="text-sm text-gray-600">Career Level</p>
                  </div>
                  
                  <div className="bg-white rounded-lg p-4 border border-blue-100">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="w-5 h-5 text-indigo-600" />
                      <span className="font-semibold text-[#1f2937]">Education</span>
                    </div>
                    <p className="text-lg font-bold text-indigo-600">{user?.resume_analysis?.education_level || "Not specified"}</p>
                    <p className="text-sm text-gray-600">Highest Level</p>
                  </div>
                </div>
                
                {/* AI Analysis Info */}
                <div className="bg-white/80 rounded-lg p-4 border border-blue-100">
                  <p className="text-sm text-[#6b7280] mb-3">
                    {user?.detailedAnalysisCompleted 
                      ? "🤖 Your resume was automatically analyzed by AI to extract this structured information."
                      : "🤖 Your resume will be analyzed by AI to extract structured information."}
                  </p>
                  <div className="flex items-center gap-6 text-xs text-[#6b7280]">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span>Provider: <span className="font-semibold capitalize">{user?.resume_analysis?.ai_provider || "Unknown"}</span></span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
                      <span>Model: <span className="font-semibold">{user?.resume_analysis?.ai_model || "Unknown"}</span></span>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Current Status Card */}
          <div className="bg-white border border-[#e5e7eb] rounded-xl p-8 mb-12">
            <h3 className="text-[1.25rem] font-semibold text-[#1f2937] mb-6 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-success-600" /> Your Profile Status
            </h3>
            
            <div className="grid md:grid-cols-3 gap-8">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-[#374151] font-medium">Profile Completion</span>
                  <span className={`text-sm font-semibold ${profileStatus.color}`}>{profileStatus.percentage}%</span>
                </div>
                <div className="bg-[#f3f4f6] rounded-lg h-2 overflow-hidden">
                  <div className="bg-[#10b981] h-full rounded-lg" style={{width: `${profileStatus.percentage}%`}}></div>
                </div>
                <p className="text-[#6b7280] text-sm mt-2">{profileStatus.text}</p>
              </div>
              
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-[#374151] font-medium">Job Matches Found</span>
                  <span className={`font-semibold text-xl ${jobMatchesCount > 0 ? 'text-[#3b82f6]' : 'text-[#f59e0b]'}`}>{jobMatchesCount}</span>
                </div>
                <p className="text-[#6b7280] text-sm">
                  {user?.matchedJobs && user.matchedJobs > 0 
                    ? `Including ${user.matchedJobs} positions with high match scores` 
                    : jobMatchesCount > 0 
                      ? `${jobMatchesCount} positions available for you`
                      : 'No matches found - update your profile'
                  }
                </p>
              </div>
              
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-[#374151] font-medium">Applications Submitted</span>
                  <span className={`font-semibold ${applicationsCount > 0 ? 'text-[#10b981]' : 'text-[#f59e0b]'}`}>{applicationsCount}</span>
                </div>
                <p className="text-[#6b7280] text-sm">
                  {applicationsCount > 0 
                    ? `You&apos;ve submitted ${applicationsCount} ${applicationsCount === 1 ? 'application' : 'applications'} - great job!`
                    : 'Ready to start applying to your matches'
                  }
                </p>
              </div>
            </div>
          </div>

          {/* AI Matches Section - Only show if resume is available */}
          {user?.hasResume && (
            <div className="bg-blue-50 border border-blue-200 rounded-2xl p-10 mb-12 text-center">
              <div className="max-w-2xl mx-auto">
                <Target className="w-16 h-16 mb-4 mx-auto text-blue-500" />
                {user.matchedJobs && user.matchedJobs > 0 ? (
                  // Show matched jobs count if matches found
                  <>
                    <h2 className="text-3xl font-bold mb-4">
                      We Found {user.matchedJobs} Perfect Match{user.matchedJobs === 1 ? '' : 'es'} for You!
                    </h2>
                    <p className="text-lg mb-8 leading-relaxed text-[#374151]">
                      Based on your resume, our AI has identified {user.matchedJobs} high-match positions out of {user.availableJobs || 'many'} total opportunities.
                    </p>
                    <Button 
                      onClick={() => router.push('/jobs/matched')}
                      variant="primary"
                      size="lg"
                      className="px-8 py-3 text-base"
                    >
                      Browse Your Matches
                    </Button>
                  </>
                ) : (
                  // Show browse all jobs if no matches found
                  <>
                    <h2 className="text-3xl font-bold mb-4">
                      Ready to Find Your Perfect Job?
                    </h2>
                    <p className="text-lg mb-8 leading-relaxed text-[#374151]">
                      Your resume has been processed! Browse all available positions to find opportunities that match your skills and experience.
                    </p>
                    <Button 
                      onClick={() => router.push('/jobs')}
                      variant="primary"
                      size="lg"
                      className="px-8 py-3 text-base"
                    >
                      Browse All Jobs
                    </Button>
                  </>
                )}
              </div>
            </div>
          )}


        </div>
      </main>
    </div>
  )
}