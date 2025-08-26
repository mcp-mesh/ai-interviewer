"use client"

import { useState, useEffect, useMemo } from 'react'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { Job, User } from '@/lib/types'
import { jobsApi } from '@/lib/api'
import Link from 'next/link'
import { Search, Target, Calendar, MapPin, Clock } from 'lucide-react'

// Filter categories matching wireframe
const filterCategories = [
  { value: 'Engineering', count: 45 },
  { value: 'Operations', count: 32 },
  { value: 'Finance', count: 18 },
  { value: 'Marketing', count: 12 },
  { value: 'Sales', count: 8 }
]

const filterStates = [
  { value: 'California', count: 28 },
  { value: 'New York', count: 22 },
  { value: 'Texas', count: 15 }
]

const filterCountries = [
  { value: 'United States', count: 115 },
  { value: 'Remote', count: 12 }
]

const filterTypes = [
  { value: 'Full-time', count: 98 },
  { value: 'Contract', count: 15 },
  { value: 'Part-time', count: 8 },
  { value: 'Internship', count: 6 }
]

interface FilterSectionProps {
  title: string
  filterId: string
  options: { value: string; count: number }[]
  selectedValues: string[]
  onChange: (values: string[]) => void
  showSearch?: boolean
}

function FilterSection({ title, filterId, options, selectedValues, onChange, showSearch }: FilterSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  const filteredOptions = showSearch 
    ? options.filter(option => option.value.toLowerCase().includes(searchTerm.toLowerCase()))
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
              <Search className="absolute right-3 top-2.5 w-5 h-5 text-gray-400" />
            </div>
          )}
          
          <div className="space-y-2">
            {filteredOptions.map((option) => (
              <label key={option.value} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedValues.includes(option.value)}
                  onChange={(e) => handleCheckboxChange(option.value, e.target.checked)}
                  className="rounded border-gray-300"
                />
                <span className="text-sm text-gray-700">
                  {option.value} <span className="text-gray-500">({option.count})</span>
                </span>
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function MatchedJobsPage() {
  const [user, setUser] = useState<User | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [allAvailableJobs, setAllAvailableJobs] = useState<Job[]>([])
  const [filteredJobs, setFilteredJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState('relevance')
  const [activeTab, setActiveTab] = useState<'recommended' | 'all'>('recommended')
  
  // Filter states
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [selectedStates, setSelectedStates] = useState<string[]>([])
  const [selectedCountries, setSelectedCountries] = useState<string[]>([])
  const [selectedTypes, setSelectedTypes] = useState<string[]>([])

  // "Recommended" tab shows matched jobs, "All Positions" shows all available jobs
  const recommendedJobs = useMemo(() => jobs, [jobs])
  const allJobs = useMemo(() => allAvailableJobs, [allAvailableJobs])

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      
      // Get user from localStorage
      const userData = localStorage.getItem('user')
      let parsedUser = null
      
      if (userData) {
        parsedUser = JSON.parse(userData)
        setUser(parsedUser)
      }
      
      // Fetch both matched and all available jobs
      try {
        if (parsedUser?.id && parsedUser?.isResumeAvailable) {
          // Get matched jobs for the user
          const matchedJobsResponse = await jobsApi.getMatched(parsedUser.id)
          if (matchedJobsResponse.data) {
            setJobs(matchedJobsResponse.data)
          }
          
          // Get all available jobs for "All Positions" tab
          const allJobsResponse = await jobsApi.getAll()
          if (allJobsResponse.data) {
            setAllAvailableJobs(allJobsResponse.data)
          }
        }
      } catch (error) {
        console.error('Failed to fetch jobs:', error)
      }
      
      setLoading(false)
    }
    
    loadData()
  }, [])

  // Filter jobs based on selected filters, search, and active tab
  useEffect(() => {
    let filtered = activeTab === 'recommended' ? recommendedJobs : allJobs

    // Apply category filter
    if (selectedCategories.length > 0) {
      filtered = filtered.filter(job => selectedCategories.includes(job.category))
    }

    // Apply location filters (simplified)
    if (selectedStates.length > 0) {
      filtered = filtered.filter(job => 
        selectedStates.some(state => job.location.includes(state))
      )
    }

    // Apply type filter
    if (selectedTypes.length > 0) {
      filtered = filtered.filter(job => selectedTypes.includes(job.type))
    }

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(job =>
        job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        job.description.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    setFilteredJobs(filtered)
  }, [recommendedJobs, allJobs, selectedCategories, selectedStates, selectedCountries, selectedTypes, searchTerm, activeTab])

  const userState = user?.isResumeAvailable ? "has-resume" : "no-resume"

  return (
    <div className="page-light min-h-screen">
      <Navigation userState={userState} user={user} theme="light" />
      
      <main className="container max-w-[1400px] mx-auto px-6 pt-20">
        {/* AI Insights Banner for users with resume */}
        <div className="bg-primary-50 border border-primary-200 rounded-xl p-4 mb-8">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <strong className="text-primary-900"><Target className="w-5 h-5 inline mr-2" />AI Recommendations:</strong>
              <span className="text-primary-900 ml-2">
                We found <strong>{jobs.length} position{jobs.length === 1 ? '' : 's'}</strong> that match your profile
              </span>
            </div>
            <Button 
              variant="primary" 
              size="default"
              onClick={() => setActiveTab('recommended')}
            >
              View Matches
            </Button>
          </div>
        </div>

        {/* Results Tabs */}
        <div className="mb-8">
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab('recommended')}
              className={`px-6 py-3 font-semibold border-b-2 transition-colors ${
                activeTab === 'recommended' 
                  ? 'border-blue-600 text-blue-600 bg-blue-50' 
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Recommended for You ({jobs.length})
            </button>
            <button
              onClick={() => setActiveTab('all')}
              className={`px-6 py-3 font-semibold border-b-2 transition-colors ${
                activeTab === 'all' 
                  ? 'border-blue-600 text-blue-600 bg-blue-50' 
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              All Positions ({allAvailableJobs.length})
            </button>
          </div>
        </div>

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
              
              <FilterSection
                title="Category"
                filterId="category"
                options={filterCategories}
                selectedValues={selectedCategories}
                onChange={setSelectedCategories}
                showSearch={true}
              />

              <FilterSection
                title="State"
                filterId="state"
                options={filterStates}
                selectedValues={selectedStates}
                onChange={setSelectedStates}
              />

              <FilterSection
                title="Country"
                filterId="country"
                options={filterCountries}
                selectedValues={selectedCountries}
                onChange={setSelectedCountries}
              />

              <FilterSection
                title="Type"
                filterId="type"
                options={filterTypes}
                selectedValues={selectedTypes}
                onChange={setSelectedTypes}
              />
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
                    <div className="flex items-center gap-6 text-sm text-gray-600 mb-4 flex-wrap">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-4 h-4 text-primary-600" />
                        {job.location}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4 text-purple-600" />
                        {job.type}
                      </span>
                      {job.matchScore && (
                        <span className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold">
                          <Target className="w-4 h-4 inline mr-1" />{job.matchScore}% Match
                        </span>
                      )}
                    </div>
                    <p className="text-gray-700 leading-relaxed">
                      {job.description}
                    </p>
                  </div>
                ))
              ) : (
                // No results
                <div className="bg-white border border-gray-200 rounded-xl p-12 text-center">
                  <Search className="w-16 h-16 mb-4 mx-auto text-gray-400" />
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">No jobs found</h3>
                  <p className="text-gray-600 mb-6">
                    Try adjusting your filters or search criteria
                  </p>
                  <Button
                    variant="primary"
                    onClick={() => {
                      setSelectedCategories([])
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