'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Plus, Trash2, Eye, EyeOff, Save, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { Markdown } from '@/components/ui/markdown'
import { User } from '@/lib/types'

interface JobFormData {
  // Basic Information
  title: string
  company: string
  category: string
  job_type: string
  status: string
  interview_duration_minutes: number
  
  // Location
  city: string
  state: string
  country: string
  remote: boolean
  
  // Content
  description: string
  
  // Compensation
  salary_min: number | null
  salary_max: number | null
  salary_currency: string
  
  // Dynamic Arrays
  requirements: string[]
  benefits: string[]
}

export default function CreateJobPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [activeDescriptionTab, setActiveDescriptionTab] = useState<'write' | 'preview'>('write')
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  
  const [formData, setFormData] = useState<JobFormData>({
    title: '',
    company: '',
    category: '',
    job_type: 'Full-time',
    status: 'open',
    interview_duration_minutes: 45,
    city: '',
    state: '',
    country: '',
    remote: false,
    description: '',
    salary_min: null,
    salary_max: null,
    salary_currency: 'USD',
    requirements: [''],
    benefits: ['']
  })

  useEffect(() => {
    loadCurrentUser()
  }, [])

  const loadCurrentUser = async () => {
    try {
      const { userApi } = await import('@/lib/api')
      const result = await userApi.getProfile()
      
      if (result.data) {
        setCurrentUser(result.data)
        localStorage.setItem('user', JSON.stringify(result.data))
      } else {
        window.location.href = '/login?redirect=/admin/jobs/create'
      }
    } catch (error) {
      console.error('Failed to load current user:', error)
      window.location.href = '/login?redirect=/admin/jobs/create'
    }
  }

  const handleInputChange = (field: keyof JobFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleArrayChange = (field: 'requirements' | 'benefits', index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].map((item, i) => i === index ? value : item)
    }))
  }

  const addArrayItem = (field: 'requirements' | 'benefits') => {
    setFormData(prev => ({
      ...prev,
      [field]: [...prev[field], '']
    }))
  }

  const removeArrayItem = (field: 'requirements' | 'benefits', index: number) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index)
    }))
  }

  const handleSubmit = async () => {
    try {
      setLoading(true)
      setError('')

      // Filter out empty requirements and benefits
      const cleanedData = {
        ...formData,
        requirements: formData.requirements.filter(req => req.trim() !== ''),
        benefits: formData.benefits.filter(benefit => benefit.trim() !== '')
      }

      const response = await fetch('/api/admin/jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(cleanedData)
      })

      if (response.ok) {
        router.push('/admin')
      } else {
        const errorData = await response.json()
        setError(errorData.message || 'Failed to create job')
      }
    } catch (error) {
      console.error('Create job error:', error)
      setError('Failed to create job')
    } finally {
      setLoading(false)
    }
  }

  const jobCategories = [
    'Engineering',
    'Finance', 
    'Operations',
    'Sales',
    'Marketing',
    'Product',
    'Design',
    'Other'
  ]

  const jobTypes = [
    'Full-time',
    'Part-time', 
    'Contract',
    'Internship',
    'Freelance'
  ]

  const currencies = [
    'USD', 'EUR', 'GBP', 'CAD', 'AUD', 'INR'
  ]

  return (
    <div className="page-light min-h-screen">
      <Navigation 
        userState="has-resume" 
        user={currentUser} 
        theme="light"
        currentPage="admin"
      />
      
      <main className="container max-w-[1400px] mx-auto px-6 pt-20">
        <div className="py-12">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <Link href="/admin">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="w-4 h-4" />
                </Button>
              </Link>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Create Job</h1>
                <p className="text-gray-600">Add a new job posting</p>
              </div>
            </div>
            
            <div>
              <Button
                onClick={handleSubmit}
                disabled={loading || !formData.title.trim()}
                className="flex items-center gap-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                Create Job
              </Button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 shadow-sm">
              <span className="text-red-700">{error}</span>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setError('')}
                className="ml-auto text-red-500 hover:bg-red-100"
              >
                ×
              </Button>
            </div>
          )}

          {/* Form Section */}
          <div className="space-y-8">
              {/* Basic Information */}
              <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Job Title *
                    </label>
                    <input
                      type="text"
                      value={formData.title}
                      onChange={(e) => handleInputChange('title', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="e.g., Senior Software Engineer"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Company
                    </label>
                    <input
                      type="text"
                      value={formData.company}
                      onChange={(e) => handleInputChange('company', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="e.g., Acme Corp"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Category
                      </label>
                      <select
                        value={formData.category}
                        onChange={(e) => handleInputChange('category', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">Select category</option>
                        {jobCategories.map(category => (
                          <option key={category} value={category}>{category}</option>
                        ))}
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Job Type
                      </label>
                      <select
                        value={formData.job_type}
                        onChange={(e) => handleInputChange('job_type', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        {jobTypes.map(type => (
                          <option key={type} value={type}>{type}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Status
                      </label>
                      <select
                        value={formData.status}
                        onChange={(e) => handleInputChange('status', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="open">Open</option>
                        <option value="closed">Closed</option>
                        <option value="on_hold">On Hold</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Interview Duration (minutes)
                      </label>
                      <input
                        type="number"
                        value={formData.interview_duration_minutes}
                        onChange={(e) => handleInputChange('interview_duration_minutes', parseInt(e.target.value) || 45)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        min="15"
                        max="180"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Location */}
              <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Location</h2>
                <div className="space-y-4">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="remote"
                      checked={formData.remote}
                      onChange={(e) => handleInputChange('remote', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <label htmlFor="remote" className="ml-2 text-sm font-medium text-gray-700">
                      Remote position
                    </label>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        City
                      </label>
                      <input
                        type="text"
                        value={formData.city}
                        onChange={(e) => handleInputChange('city', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="e.g., San Francisco"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        State/Province
                      </label>
                      <input
                        type="text"
                        value={formData.state}
                        onChange={(e) => handleInputChange('state', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="e.g., California"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Country
                      </label>
                      <input
                        type="text"
                        value={formData.country}
                        onChange={(e) => handleInputChange('country', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="e.g., United States of America"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Compensation */}
              <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Compensation</h2>
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Minimum Salary
                      </label>
                      <input
                        type="number"
                        value={formData.salary_min || ''}
                        onChange={(e) => handleInputChange('salary_min', e.target.value ? parseInt(e.target.value) : null)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="e.g., 80000"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Maximum Salary
                      </label>
                      <input
                        type="number"
                        value={formData.salary_max || ''}
                        onChange={(e) => handleInputChange('salary_max', e.target.value ? parseInt(e.target.value) : null)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="e.g., 120000"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Currency
                      </label>
                      <select
                        value={formData.salary_currency}
                        onChange={(e) => handleInputChange('salary_currency', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        {currencies.map(currency => (
                          <option key={currency} value={currency}>{currency}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              </div>

              {/* Job Description */}
              <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Job Description</h2>
                
                {/* Tab Navigation */}
                <div className="flex border-b border-gray-200 mb-4">
                  <button
                    onClick={() => setActiveDescriptionTab('write')}
                    className={`flex items-center gap-2 px-4 py-2 font-medium border-b-2 transition-colors ${
                      activeDescriptionTab === 'write'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Write
                  </button>
                  <button
                    onClick={() => setActiveDescriptionTab('preview')}
                    className={`flex items-center gap-2 px-4 py-2 font-medium border-b-2 transition-colors ${
                      activeDescriptionTab === 'preview'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    <Eye className="w-4 h-4" />
                    Preview
                  </button>
                </div>
                
                {/* Tab Content */}
                {activeDescriptionTab === 'write' ? (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description (Markdown supported)
                    </label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => handleInputChange('description', e.target.value)}
                      rows={12}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                      placeholder="## About the Role

This is a great opportunity to join our team...

### Responsibilities
- Write clean, maintainable code
- Collaborate with team members
- Participate in code reviews

### Requirements
- 3+ years experience with React
- Strong JavaScript/TypeScript skills
- Experience with modern web technologies"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Supports Markdown formatting. Switch to Preview tab to see how it will look.
                    </p>
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Preview
                    </label>
                    <div className="border border-gray-300 rounded-lg p-4 bg-gray-50 min-h-[288px] max-h-[400px] overflow-y-auto">
                      {formData.description ? (
                        <Markdown content={formData.description} />
                      ) : (
                        <p className="text-gray-400 text-sm italic">No description entered yet. Switch to Write tab to add content.</p>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Requirements */}
              <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">Requirements</h2>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => addArrayItem('requirements')}
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="space-y-3">
                  {formData.requirements.map((req, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="text"
                        value={req}
                        onChange={(e) => handleArrayChange('requirements', index, e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="e.g., Bachelor's degree in Computer Science"
                      />
                      {formData.requirements.length > 1 && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => removeArrayItem('requirements', index)}
                          className="text-red-600 hover:bg-red-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Benefits */}
              <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">Benefits</h2>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => addArrayItem('benefits')}
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="space-y-3">
                  {formData.benefits.map((benefit, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="text"
                        value={benefit}
                        onChange={(e) => handleArrayChange('benefits', index, e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="e.g., Health insurance coverage"
                      />
                      {formData.benefits.length > 1 && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => removeArrayItem('benefits', index)}
                          className="text-red-600 hover:bg-red-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
        </div>
      </main>
    </div>
  )
}