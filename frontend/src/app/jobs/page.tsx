"use client"

import { useState, useEffect } from 'react'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { jobsApi } from '@/lib/api'
import { Job, User } from '@/lib/types'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { MapPin, Clock, Search, Zap } from 'lucide-react'

// Mock job data matching wireframe - commented out as not used
/*
const mockJobs: Job[] = [
  {
    id: '1',
    title: 'Operations Analyst, Institutional Private Client',
    company: 'S Corp.',
    location: 'San Francisco, California, United States of America',
    type: 'Full-time',
    category: 'Operations',
    description: 'The Investment Manager Services Division (IMS) at S Corp. is growing rapidly and is seeking new members on our Institutional Private Client (IPC) team. Our primary goal is to provide exceptional administrative services...',
    requirements: ['Finance', 'Analytics', 'Excel', 'Communication'],
    postedAt: new Date().toISOString()
  },
  {
    id: '2',
    title: 'Fund Accountant, Investment Fund Services',
    company: 'S Corp.',
    location: 'Austin, Texas, United States of America',
    type: 'Full-time',
    category: 'Finance',
    description: 'The Investment Manager Services Division (IMS) at S Corp. is growing rapidly and is seeking new members on our Investment Fund Services accounting team. Our primary goal is to provide exceptional accounting...',
    requirements: ['Accounting', 'Finance', 'Excel', 'Detail-oriented'],
    postedAt: new Date().toISOString()
  },
  {
    id: '3',
    title: 'Operations Analyst, Separately Managed Accounts',
    company: 'S Corp.',
    location: 'New York, New York, United States of America',
    type: 'Full-time',
    category: 'Operations',
    description: 'The Investment Manager Services Division (IMS) at S Corp. is growing rapidly and is seeking new members on our Separately Managed Accounts team. Our primary goal is to provide exceptional accounting and administrative...',
    requirements: ['Operations', 'Analysis', 'Finance', 'Process Improvement'],
    postedAt: new Date().toISOString()
  },
  {
    id: '4',
    title: 'Operations Analyst, AML',
    company: 'S Corp.',
    location: 'Seattle, Washington, United States of America',
    type: 'Full-time',
    category: 'Operations',
    description: 'The Investment Manager Services Division (IMS) at S Corp. is growing rapidly and is seeking new members on our Alternative Investment Funds Investor Services Anti-Money Laundering Team. Our primary goal is...',
    requirements: ['AML', 'Compliance', 'Risk Management', 'Investigation'],
    postedAt: new Date().toISOString()
  },
  {
    id: '5',
    title: 'Senior Software Engineer',
    company: 'S Corp.',
    location: 'Boston, Massachusetts, United States of America',
    type: 'Full-time',
    category: 'Engineering',
    description: 'Join our engineering team to build scalable web applications using React, Node.js, and cloud technologies. We\'re looking for someone with 5+ years of experience in full-stack development and cloud architecture...',
    requirements: ['React', 'Node.js', 'JavaScript', 'AWS', 'TypeScript'],
    postedAt: new Date().toISOString()
  }
]
*/


interface FilterSectionProps {
  title: string
  // filterId: string // TODO: May be needed for future functionality
  options: string[]
  selectedValues: string[]
  onChange: (values: string[]) => void
  showSearch?: boolean
}

function FilterSection({ title, /* filterId, */ options, selectedValues, onChange, showSearch }: FilterSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  const filteredOptions = showSearch 
    ? options.filter(option => option.toLowerCase().includes(searchTerm.toLowerCase()))
    : options

  const toggleExpanded = () => setIsExpanded(!isExpanded)

  const handleCheckboxChange = (value: string, checked: boolean) => {
    if (checked) {
      onChange([...selectedValues, value])
    } else {
      onChange(selectedValues.filter(v => v !== value))
    }
  }

  return (
    <div className="border-b border-gray-200 pb-4 mb-4">
      <div 
        className="flex justify-between items-center cursor-pointer py-2"
        onClick={toggleExpanded}
      >
        <h5 className="font-semibold text-gray-900">{title}</h5>
        <div className="text-gray-500 font-bold text-lg">
          {isExpanded ? '−' : '+'}
        </div>
      </div>
      
      {isExpanded && (
        <div className="mt-3 space-y-3">
          {showSearch && (
            <div className="relative">
              <input
                type="text"
                placeholder={`Search in ${title}`}
                className="w-full px-3 py-2 pr-8 border border-gray-300 rounded text-sm"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              <Search className="absolute right-3 top-2.5 w-4 h-4 text-gray-400" />
            </div>
          )}
          
          <div className="space-y-2">
            {filteredOptions.map((option) => (
              <label key={option} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedValues.includes(option)}
                  onChange={(e) => handleCheckboxChange(option, e.target.checked)}
                  className="rounded border-gray-300"
                />
                <span className="text-sm text-gray-700">
                  {option}
                </span>
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function JobsPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  // const [jobs, setJobs] = useState<Job[]>([]) // TODO: May be needed for future functionality
  const [filteredJobs, setFilteredJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState('relevance')
  
  // Filter states
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [selectedCities, setSelectedCities] = useState<string[]>([])
  const [selectedStates, setSelectedStates] = useState<string[]>([])
  const [selectedCountries, setSelectedCountries] = useState<string[]>([])
  const [selectedTypes, setSelectedTypes] = useState<string[]>([])
  
  // Filter options from API
  const [filterOptions, setFilterOptions] = useState<{
    categories: string[]
    job_types: string[]
    cities: string[]
    states: string[]
    countries: string[]
  } | null>(null)

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      
      // Get user from localStorage
      const userData = localStorage.getItem('user')
      if (userData) {
        const parsedUser = JSON.parse(userData)
        setUser(parsedUser)
        
        // Redirect users with resume to matched jobs page
        if (parsedUser.hasResume) {
          router.push('/jobs/matched')
          return
        }
      }
      
      // Fetch jobs and filters from API
      try {
        const [jobsResponse, filtersResponse] = await Promise.all([
          jobsApi.getAll(), // Use filtered method that excludes applied jobs
          jobsApi.getFilters()
        ])
        
        if (jobsResponse.data) {
          // setJobs(jobsResponse.data) // TODO: May be needed for future functionality
        }
        
        if (filtersResponse.data) {
          setFilterOptions(filtersResponse.data)
        }
      } catch (error) {
        console.error('Failed to fetch data:', error)
      }
      
      setLoading(false)
    }
    
    loadData()
  }, [router])

  // Refetch jobs when filters change - now using API filtering
  useEffect(() => {
    const fetchFilteredJobs = async () => {
      if (!filterOptions) return // Wait for filter options to load
      
      const filters = {
        categories: selectedCategories.length > 0 ? selectedCategories : undefined,
        job_types: selectedTypes.length > 0 ? selectedTypes : undefined,
        cities: selectedCities.length > 0 ? selectedCities : undefined,
        states: selectedStates.length > 0 ? selectedStates : undefined,
        countries: selectedCountries.length > 0 ? selectedCountries : undefined
      }
      
      try {
        const jobsResponse = await jobsApi.getAll(filters)
        if (jobsResponse.data) {
          let filtered = jobsResponse.data
          
          // Apply search filter (done on frontend for now)
          if (searchTerm) {
            filtered = filtered.filter(job =>
              job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
              job.description.toLowerCase().includes(searchTerm.toLowerCase())
            )
          }
          
          setFilteredJobs(filtered)
        }
      } catch (error) {
        console.error('Failed to fetch filtered jobs:', error)
      }
    }

    fetchFilteredJobs()
  }, [selectedCategories, selectedCities, selectedStates, selectedCountries, selectedTypes, searchTerm, filterOptions])

  const isGuest = !user
  const userState = isGuest ? "guest" : (user.hasResume ? "has-resume" : "no-resume")

  return (
    <div className="page-light min-h-screen">
      <Navigation userState={userState} user={user} theme="light" currentPage="jobs" />
      
      <main className="container max-w-[1400px] mx-auto px-6 pt-20">
        {/* Login Banner for Guest Users */}
        {isGuest && (
          <div className="bg-primary-50 border border-primary-200 rounded-xl p-4 mb-8">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <strong className="text-primary-900 flex items-center gap-1">
                  <Zap className="h-4 w-4 text-warning-500" />
                  Get AI-Powered Matching:
                </strong>
                <span className="text-primary-900 ml-2">
                  Login to see personalized job recommendations and apply with one click
                </span>
              </div>
              <Link href="/login?redirect=/jobs">
                <Button variant="primary" size="default">
                  Login to Get Matched
                </Button>
              </Link>
            </div>
          </div>
        )}

        {/* Upload Resume Banner for Logged In Users Without Resume */}
        {!isGuest && user && !user.hasResume && (
          <div className="bg-primary-50 border border-primary-200 rounded-xl p-4 mb-8">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <strong className="text-primary-900 flex items-center gap-1"><Zap className="w-4 h-4" /> Get AI-Powered Matching:</strong>
                <span className="text-primary-900 ml-2">
                  Upload your resume to see personalized job recommendations
                </span>
              </div>
              <Link href="/upload">
                <Button variant="primary" size="default">
                  Upload Resume
                </Button>
              </Link>
            </div>
          </div>
        )}

        {/* Two-column layout */}
        <div className="grid lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <aside className="lg:col-span-1">
            {/* Values Card */}
            <div className="bg-primary-50 border border-primary-200 rounded-t-xl p-6 mb-0">
              <h3 className="text-lg font-semibold text-primary-900 mb-3">Our AI Values</h3>
              <p className="text-primary-900 text-sm leading-relaxed mb-4">
                Innovation. Excellence. Collaboration. Transparency. Growth. Fun. These are our six core values and define who we are.
              </p>
              <a href="#" className="text-primary-900 hover:text-primary-800 text-sm font-medium underline">
                Learn more.
              </a>
            </div>

            {/* Refine Search */}
            <div className="bg-white border border-gray-200 rounded-b-xl border-t-0 p-4">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">Refine your search</h4>
              
              {filterOptions && (
                <>
                  <FilterSection
                    title="Category"
                    // filterId="category" // TODO: May be needed for future functionality
                    options={filterOptions.categories}
                    selectedValues={selectedCategories}
                    onChange={setSelectedCategories}
                    showSearch={true}
                  />

                  <FilterSection
                    title="City"
                    // filterId="city" // TODO: May be needed for future functionality
                    options={filterOptions.cities}
                    selectedValues={selectedCities}
                    onChange={setSelectedCities}
                    showSearch={true}
                  />

                  <FilterSection
                    title="State"
                    // filterId="state" // TODO: May be needed for future functionality
                    options={filterOptions.states}
                    selectedValues={selectedStates}
                    onChange={setSelectedStates}
                  />

                  <FilterSection
                    title="Country"
                    // filterId="country" // TODO: May be needed for future functionality
                    options={filterOptions.countries}
                    selectedValues={selectedCountries}
                    onChange={setSelectedCountries}
                  />

                  <FilterSection
                    title="Type"
                    // filterId="type" // TODO: May be needed for future functionality
                    options={filterOptions.job_types}
                    selectedValues={selectedTypes}
                    onChange={setSelectedTypes}
                  />
                </>
              )}
            </div>
          </aside>

          {/* Main Content Area */}
          <div className="lg:col-span-3">
            {/* Content Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Search from below list"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 placeholder:text-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span className="font-medium">
                  {loading ? 'Loading...' : `${filteredJobs.length} Jobs`}
                </span>
                <span>|</span>
                <span>Sort by</span>
                <select
                  className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                >
                  <option value="relevance">Most relevant</option>
                  <option value="date">Newest First</option>
                  <option value="title">Job Title</option>
                </select>
              </div>
            </div>

            {/* Job Listings */}
            <div className="space-y-6">
              {loading ? (
                // Loading state
                Array.from({ length: 5 }, (_, i) => (
                  <div key={i} className="bg-white border border-gray-200 rounded-xl p-6 animate-pulse">
                    <div className="h-6 bg-gray-200 rounded mb-3"></div>
                    <div className="h-4 bg-gray-200 rounded mb-2 w-2/3"></div>
                    <div className="h-16 bg-gray-200 rounded"></div>
                  </div>
                ))
              ) : filteredJobs.length > 0 ? (
                filteredJobs.map((job) => (
                  <div key={job.id} className="bg-white border border-gray-200 rounded-xl p-6">
                    <Link href={`/jobs/${job.id}`}>
                      <h3 className="text-lg font-semibold text-red-600 hover:text-red-700 cursor-pointer underline mb-3">
                        {job.title}
                      </h3>
                    </Link>
                    <div className="flex items-center gap-6 text-sm text-gray-600 mb-4">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-4 h-4" /> {job.location}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" /> {job.type}
                      </span>
                    </div>
                    <p className="text-gray-700 leading-relaxed">
                      {job.description}
                    </p>
                  </div>
                ))
              ) : (
                // No results
                <div className="bg-white border border-gray-200 rounded-xl p-12 text-center">
                  <div className="text-5xl mb-4"><Search className="w-12 h-12 mx-auto text-gray-400" /></div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">No jobs found</h3>
                  <p className="text-gray-600 mb-6">
                    Try adjusting your filters or search criteria
                  </p>
                  <Button
                    variant="primary"
                    onClick={() => {
                      setSelectedCategories([])
                      setSelectedCities([])
                      setSelectedStates([])
                      setSelectedCountries([])
                      setSelectedTypes([])
                      setSearchTerm('')
                    }}
                  >
                    Clear All Filters
                  </Button>
                </div>
              )}
            </div>

            {/* Load More */}
            {filteredJobs.length > 0 && (
              <div className="text-center mt-12">
                <Button variant="secondary" onClick={() => {/* Load more */}}>
                  Load More Positions
                </Button>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}