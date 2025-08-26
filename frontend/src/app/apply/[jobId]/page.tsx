"use client"

import { useState, useEffect, useRef } from 'react'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { ToastContainer, useToast } from '@/components/wireframe'
import { User } from '@/lib/types'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { FileText, Bot, CheckCircle2, Eye } from 'lucide-react'

// Application form data types
interface WorkExperience {
  company: string
  jobTitle: string
  startDate: string
  endDate: string
  isCurrent: boolean
  location: string
  responsibilities: string
}

interface Education {
  institution: string
  degree: string
  fieldOfStudy: string
  graduationYear: number
  gpa: string
}

interface ApplicationData {
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
}

const initialFormData: ApplicationData = {
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

const steps = [
  { id: 1, title: 'My Information', key: 'info' },
  { id: 2, title: 'My Experience', key: 'experience' },
  { id: 3, title: 'Application Questions', key: 'questions' },
  { id: 4, title: 'Voluntary Disclosures', key: 'disclosures' },
  { id: 5, title: 'Self Identity', key: 'identity' },
  { id: 6, title: 'Review', key: 'review' }
]

// Mock job data (in real app, this would come from API)
const jobTitles: Record<string, string> = {
  '1': 'Operations Analyst, Institutional Private Client',
  '2': 'Fund Accountant, Investment Fund Services',
  '3': 'Operations Analyst, Separately Managed Accounts',
  '4': 'Operations Analyst, AML',
  '5': 'Senior Software Engineer'
}

interface ApplicationPageProps {
  params: Promise<{
    jobId: string
  }>
}

// Progress Indicator Component
function ProgressIndicator({ currentStep, totalSteps }: { currentStep: number; totalSteps: number }) {
  return (
    <div className="mb-16">
      <div className="flex items-center justify-between mb-8">
        {steps.map((step, index) => {
          const stepNumber = index + 1
          const isCompleted = stepNumber < currentStep
          const isActive = stepNumber === currentStep
          const isLast = index === steps.length - 1
          
          return (
            <div key={step.id} className="flex items-center flex-1">
              <div className="flex flex-col items-center flex-1">
                <div 
                  className={`w-8 h-8 rounded-full flex items-center justify-center mb-2 ${
                    isCompleted 
                      ? 'bg-green-500' 
                      : isActive 
                        ? 'bg-red-500' 
                        : 'bg-gray-300'
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4 text-success-100" />
                  ) : (
                    <div className="w-3 h-3 bg-white rounded-full"></div>
                  )}
                </div>
                <div 
                  className={`text-sm text-center ${
                    isActive ? 'font-semibold text-gray-900' : 'text-gray-600'
                  }`}
                >
                  {step.title}
                </div>
              </div>
              {!isLast && (
                <div 
                  className={`flex-1 h-0.5 mx-4 ${
                    isCompleted ? 'bg-green-500' : 'bg-gray-300'
                  }`}
                />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Step 1: Personal Information
function PersonalInfoStep({ 
  personalData, 
  addressData, 
  onPersonalChange, 
  onAddressChange 
}: { 
  personalData: ApplicationData['personalInfo'], 
  addressData: ApplicationData['addressInfo'],
  onPersonalChange: (data: ApplicationData['personalInfo']) => void,
  onAddressChange: (data: ApplicationData['addressInfo']) => void
}) {
  return (
    <div className="space-y-8">
      {/* Personal Information Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Personal Information</h2>
        
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">First Name *</label>
            <input 
              type="text" 
              value={personalData.firstName}
              onChange={(e) => onPersonalChange({ ...personalData, firstName: e.target.value })}
              className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Last Name *</label>
            <input 
              type="text" 
              value={personalData.lastName}
              onChange={(e) => onPersonalChange({ ...personalData, lastName: e.target.value })}
              className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
            />
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email Address *</label>
            <input 
              type="email" 
              value={personalData.email}
              onChange={(e) => onPersonalChange({ ...personalData, email: e.target.value })}
              className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Phone Number *</label>
            <input 
              type="tel" 
              value={personalData.phone}
              onChange={(e) => onPersonalChange({ ...personalData, phone: e.target.value })}
              className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
            />
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">LinkedIn Profile URL</label>
          <input 
            type="url" 
            value={personalData.linkedIn}
            onChange={(e) => onPersonalChange({ ...personalData, linkedIn: e.target.value })}
            className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
          />
        </div>
      </div>

      {/* Address Information Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Address Information</h2>
        
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Street Address *</label>
          <input 
            type="text" 
            value={addressData.street}
            onChange={(e) => onAddressChange({ ...addressData, street: e.target.value })}
            className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
          />
        </div>
        
        <div className="grid grid-cols-3 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">City *</label>
            <input 
              type="text" 
              value={addressData.city}
              onChange={(e) => onAddressChange({ ...addressData, city: e.target.value })}
              className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">State *</label>
            <select 
              value={addressData.state}
              onChange={(e) => onAddressChange({ ...addressData, state: e.target.value })}
              className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
            >
              <option value="">Select State</option>
              <option value="CA">California</option>
              <option value="NY">New York</option>
              <option value="TX">Texas</option>
              <option value="FL">Florida</option>
              <option value="WA">Washington</option>
              <option value="MA">Massachusetts</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">ZIP Code *</label>
            <input 
              type="text" 
              value={addressData.zipCode}
              onChange={(e) => onAddressChange({ ...addressData, zipCode: e.target.value })}
              className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
            />
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Country *</label>
          <select 
            value={addressData.country}
            onChange={(e) => onAddressChange({ ...addressData, country: e.target.value })}
            className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
          >
            <option value="US">United States</option>
            <option value="CA">Canada</option>
            <option value="UK">United Kingdom</option>
            <option value="AU">Australia</option>
          </select>
        </div>
      </div>
    </div>
  )
}

// Step 2: Experience (matching wireframe)
function ExperienceStep({ data, onChange }: { 
  data: ApplicationData['experience'], 
  onChange: (data: ApplicationData['experience']) => void 
}) {
  const addWorkExperience = () => {
    const newExperience: WorkExperience = {
      company: '',
      jobTitle: '',
      startDate: '',
      endDate: '',
      isCurrent: false,
      location: '',
      responsibilities: ''
    }
    onChange({
      ...data,
      workExperience: [...data.workExperience, newExperience]
    })
  }

  const removeWorkExperience = (index: number) => {
    const updated = data.workExperience.filter((_, i) => i !== index)
    onChange({ ...data, workExperience: updated })
  }

  const updateWorkExperience = (index: number, field: keyof WorkExperience, value: string | boolean) => {
    const updated = data.workExperience.map((exp, i) => 
      i === index ? { ...exp, [field]: value } : exp
    )
    onChange({ ...data, workExperience: updated })
  }

  const addEducation = () => {
    const newEducation: Education = {
      institution: '',
      degree: '',
      fieldOfStudy: '',
      graduationYear: 0,
      gpa: ''
    }
    onChange({
      ...data,
      education: [...data.education, newEducation]
    })
  }

  const removeEducation = (index: number) => {
    const updated = data.education.filter((_, i) => i !== index)
    onChange({ ...data, education: updated })
  }

  const updateEducation = (index: number, field: keyof Education, value: string | boolean) => {
    const updated = data.education.map((edu, i) => 
      i === index ? { ...edu, [field]: value } : edu
    )
    onChange({ ...data, education: updated })
  }

  return (
    <div className="space-y-8">
      {/* Professional Summary Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Professional Summary</h2>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Brief Summary *</label>
          <textarea 
            rows={4}
            value={data.summary}
            onChange={(e) => onChange({ ...data, summary: e.target.value })}
            className="w-full px-3 py-3 border border-gray-300 rounded-md text-base resize-y"
            placeholder="Experienced Full Stack Developer with 8+ years in building scalable web applications..."
          />
        </div>
      </div>

      {/* Skills Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Skills & Technologies</h2>
        
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Technical Skills *</label>
            <textarea 
              rows={3}
              value={data.technicalSkills}
              onChange={(e) => onChange({ ...data, technicalSkills: e.target.value })}
              className="w-full px-3 py-3 border border-gray-300 rounded-md text-base resize-y"
              placeholder="JavaScript, TypeScript, React, Vue.js, Node.js, Python, Django, PostgreSQL, MongoDB, AWS, Docker, Kubernetes, Git, REST APIs, GraphQL"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Soft Skills</label>
            <textarea 
              rows={2}
              value={data.softSkills}
              onChange={(e) => onChange({ ...data, softSkills: e.target.value })}
              className="w-full px-3 py-3 border border-gray-300 rounded-md text-base resize-y"
              placeholder="Leadership, Team Collaboration, Problem Solving, Communication, Agile/Scrum, Project Management"
            />
          </div>
        </div>
      </div>

      {/* Work Experience Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold text-gray-900">Work Experience</h2>
          <button 
            type="button"
            onClick={addWorkExperience}
            className="bg-[#3b82f6] text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-[#2563eb] transition-colors"
          >
            + Add Experience
          </button>
        </div>
        
        {data.workExperience.map((experience, index) => (
          <div key={index} className="border border-gray-200 rounded-lg p-6 mb-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Company Name *</label>
                <input 
                  type="text"
                  value={experience.company}
                  onChange={(e) => updateWorkExperience(index, 'company', e.target.value)}
                  className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
                  placeholder="TechCorp Inc."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Job Title *</label>
                <input 
                  type="text"
                  value={experience.jobTitle}
                  onChange={(e) => updateWorkExperience(index, 'jobTitle', e.target.value)}
                  className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
                  placeholder="Senior Software Engineer"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Start Date *</label>
                <input 
                  type="month"
                  value={experience.startDate}
                  onChange={(e) => updateWorkExperience(index, 'startDate', e.target.value)}
                  className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
                <div className="flex items-center gap-4">
                  <input 
                    type="month"
                    value={experience.endDate}
                    onChange={(e) => updateWorkExperience(index, 'endDate', e.target.value)}
                    disabled={experience.isCurrent}
                    className={`flex-1 px-3 py-3 border border-gray-300 rounded-md text-base ${experience.isCurrent ? 'bg-gray-100' : ''}`}
                  />
                  <label className="flex items-center text-sm text-gray-700">
                    <input 
                      type="checkbox"
                      checked={experience.isCurrent}
                      onChange={(e) => {
                        updateWorkExperience(index, 'isCurrent', e.target.checked)
                        if (e.target.checked) {
                          updateWorkExperience(index, 'endDate', '')
                        }
                      }}
                      className="mr-2"
                    />
                    Current
                  </label>
                </div>
              </div>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
              <input 
                type="text"
                value={experience.location}
                onChange={(e) => updateWorkExperience(index, 'location', e.target.value)}
                className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
                placeholder="San Francisco, CA"
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Key Responsibilities & Achievements *</label>
              <textarea 
                rows={4}
                value={experience.responsibilities}
                onChange={(e) => updateWorkExperience(index, 'responsibilities', e.target.value)}
                className="w-full px-3 py-3 border border-gray-300 rounded-md text-base resize-y"
                placeholder="• Lead development of microservices architecture serving 1M+ daily users&#10;• Mentored 5 junior developers and conducted code reviews&#10;• Improved application performance by 40% through optimization"
              />
            </div>
            
            <button 
              type="button"
              onClick={() => removeWorkExperience(index)}
              className="bg-[#ef4444] text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-[#dc2626] transition-colors"
            >
              Remove
            </button>
          </div>
        ))}
      </div>

      {/* Education Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold text-gray-900">Education</h2>
          <button 
            type="button"
            onClick={addEducation}
            className="bg-[#3b82f6] text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-[#2563eb] transition-colors"
          >
            + Add Education
          </button>
        </div>
        
        {data.education.map((edu, index) => (
          <div key={index} className="border border-gray-200 rounded-lg p-6 mb-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Institution *</label>
                <input 
                  type="text"
                  value={edu.institution}
                  onChange={(e) => updateEducation(index, 'institution', e.target.value)}
                  className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
                  placeholder="Stanford University"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Degree *</label>
                <input 
                  type="text"
                  value={edu.degree}
                  onChange={(e) => updateEducation(index, 'degree', e.target.value)}
                  className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
                  placeholder="Master of Science in Computer Science"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Field of Study</label>
                <input 
                  type="text"
                  value={edu.fieldOfStudy}
                  onChange={(e) => updateEducation(index, 'fieldOfStudy', e.target.value)}
                  className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
                  placeholder="Software Engineering"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Graduation Year *</label>
                <input 
                  type="number"
                  value={edu.graduationYear || ''}
                  onChange={(e) => updateEducation(index, 'graduationYear', e.target.value)}
                  className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
                  placeholder="2018"
                  min="1950"
                  max="2030"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">GPA (Optional)</label>
                <input 
                  type="text"
                  value={edu.gpa}
                  onChange={(e) => updateEducation(index, 'gpa', e.target.value)}
                  className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
                  placeholder="3.8"
                />
              </div>
            </div>
            
            <button 
              type="button"
              onClick={() => removeEducation(index)}
              className="bg-[#ef4444] text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-[#dc2626] transition-colors"
            >
              Remove
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

// Step 3: Application Questions
function ApplicationQuestionsStep({ data, onChange }: { 
  data: ApplicationData['questions'], 
  onChange: (data: ApplicationData['questions']) => void 
}) {
  return (
    <div className="space-y-8">
      {/* Work Authorization Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Work Authorization</h2>
        
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Are you authorized to work in the United States? *
            </label>
            <div className="space-y-2">
              <label className="flex items-center text-sm text-gray-700">
                <input 
                  type="radio" 
                  name="workAuth" 
                  value="yes"
                  checked={data.workAuthorization === 'yes'}
                  onChange={(e) => onChange({ ...data, workAuthorization: e.target.value })}
                  className="mr-2"
                />
                Yes, I am authorized to work in the US
              </label>
              <label className="flex items-center text-sm text-gray-700">
                <input 
                  type="radio" 
                  name="workAuth" 
                  value="no"
                  checked={data.workAuthorization === 'no'}
                  onChange={(e) => onChange({ ...data, workAuthorization: e.target.value })}
                  className="mr-2"
                />
                No, I will need sponsorship
              </label>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Will you now or in the future require sponsorship for employment visa status? *
            </label>
            <select 
              value={data.visaSponsorship}
              onChange={(e) => onChange({ ...data, visaSponsorship: e.target.value })}
              className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
            >
              <option value="">— Make a Selection —</option>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </div>
        </div>
      </div>

      {/* Location & Relocation Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Location & Relocation</h2>
        
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Are you willing to relocate for this position? *
            </label>
            <select 
              value={data.relocate}
              onChange={(e) => onChange({ ...data, relocate: e.target.value })}
              className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
            >
              <option value="">— Make a Selection —</option>
              <option value="yes">Yes</option>
              <option value="no">No</option>
              <option value="maybe">Open to discussion</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Are you open to remote work arrangements? *
            </label>
            <select 
              value={data.remoteWork}
              onChange={(e) => onChange({ ...data, remoteWork: e.target.value })}
              className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
            >
              <option value="">— Make a Selection —</option>
              <option value="fully-remote">Yes, fully remote</option>
              <option value="hybrid">Yes, hybrid (mix of remote and in-office)</option>
              <option value="no">No, prefer in-office only</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              What is your preferred work location? *
            </label>
            <input 
              type="text" 
              value={data.preferredLocation}
              onChange={(e) => onChange({ ...data, preferredLocation: e.target.value })}
              className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
              placeholder="e.g. San Francisco, CA (open to remote)"
            />
          </div>
        </div>
      </div>

      {/* Employment Details Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Employment Details</h2>
        
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              When would you be available to start? *
            </label>
            <select 
              value={data.availability}
              onChange={(e) => onChange({ ...data, availability: e.target.value })}
              className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
            >
              <option value="">— Make a Selection —</option>
              <option value="immediately">Immediately</option>
              <option value="2weeks">2 weeks notice</option>
              <option value="4weeks">4 weeks notice</option>
              <option value="other">Other (please specify)</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Salary Expectations (Annual, USD) *
            </label>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Minimum</label>
                <input 
                  type="number" 
                  value={data.salaryMin}
                  onChange={(e) => onChange({ ...data, salaryMin: e.target.value })}
                  className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
                  placeholder="120000"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Maximum</label>
                <input 
                  type="number" 
                  value={data.salaryMax}
                  onChange={(e) => onChange({ ...data, salaryMax: e.target.value })}
                  className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
                  placeholder="160000"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Step 4: Voluntary Disclosures
function VoluntaryDisclosuresStep({ data, onChange }: { 
  data: ApplicationData['disclosures'], 
  onChange: (data: ApplicationData['disclosures']) => void 
}) {
  return (
    <div className="space-y-8">
      {/* Disclaimer */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
        <div className="flex items-start gap-3">
          <div className="text-yellow-600 text-xl">ℹ️</div>
          <div>
            <h3 className="text-base font-semibold text-yellow-800 mb-2">Voluntary Disclosure</h3>
            <p className="text-yellow-800 text-sm leading-relaxed">
              The information requested below is voluntary and will be kept confidential. It is used for compliance reporting and will not be used in hiring decisions. You may choose to skip any or all of these questions.
            </p>
          </div>
        </div>
      </div>

      {/* Government Employment Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Government Employment</h2>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Are you currently employed by a government or government agency in any capacity? *
          </label>
          <select 
            value={data.governmentEmployment}
            onChange={(e) => onChange({ ...data, governmentEmployment: e.target.value })}
            className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
          >
            <option value="">— Make a Selection —</option>
            <option value="no">No</option>
            <option value="yes">Yes</option>
            <option value="prefer_not_to_say">Prefer not to say</option>
          </select>
        </div>
      </div>

      {/* Non-Compete Agreement Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Non-Compete & Non-Disclosure</h2>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Have you signed a non-compete or non-disclosure agreement which may become an obstacle to your acceptance of employment at S Corp.? *
          </label>
          <select 
            value={data.nonCompete}
            onChange={(e) => onChange({ ...data, nonCompete: e.target.value })}
            className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
          >
            <option value="">— Make a Selection —</option>
            <option value="no">No</option>
            <option value="yes">Yes</option>
            <option value="prefer_not_to_say">Prefer not to say</option>
          </select>
        </div>
      </div>

      {/* Previous Employment Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Previous Employment with S Corp.</h2>
        
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Have you ever worked with S Corp. as a full-time/part-time employee, intern, vendor, agency temporary, or business guest? *
            </label>
            <select 
              value={data.previousEmployment}
              onChange={(e) => onChange({ ...data, previousEmployment: e.target.value })}
              className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
            >
              <option value="">— Make a Selection —</option>
              <option value="no">No</option>
              <option value="yes">Yes</option>
              <option value="prefer_not_to_say">Prefer not to say</option>
            </select>
          </div>
          
          {data.previousEmployment === 'yes' && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Previous Employment Details</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Previous Alias</label>
                  <input 
                    type="text" 
                    value={data.previousAlias}
                    onChange={(e) => onChange({ ...data, previousAlias: e.target.value })}
                    className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
                    placeholder="If different from current name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Personnel Number (PERN)</label>
                  <input 
                    type="text" 
                    value={data.personnelNumber}
                    onChange={(e) => onChange({ ...data, personnelNumber: e.target.value })}
                    className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
                    placeholder="Employee ID if known"
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Step 5: Self Identity
function SelfIdentityStep({ data, onChange }: { 
  data: ApplicationData['identity'], 
  onChange: (data: ApplicationData['identity']) => void 
}) {
  const handleRaceChange = (value: string, checked: boolean) => {
    if (checked) {
      onChange({ ...data, race: [...data.race, value] })
    } else {
      onChange({ ...data, race: data.race.filter(r => r !== value) })
    }
  }

  return (
    <div className="space-y-8">
      {/* Disclaimer */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
        <div className="flex items-start gap-3">
          <div className="text-yellow-600 text-xl">ℹ️</div>
          <div>
            <h3 className="text-base font-semibold text-yellow-800 mb-2">Equal Opportunity Employer</h3>
            <p className="text-yellow-800 text-sm leading-relaxed">
              S Corp. is committed to providing equal employment opportunities. The information requested below is voluntary and will be kept confidential. It will not be used in hiring decisions and is collected for compliance with federal regulations.
            </p>
          </div>
        </div>
      </div>

      {/* Gender Identity Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Gender Identity</h2>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            How do you identify? (Optional)
          </label>
          <select 
            value={data.gender}
            onChange={(e) => onChange({ ...data, gender: e.target.value })}
            className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
          >
            <option value="">— Make a Selection —</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="non-binary">Non-binary</option>
            <option value="other">Other</option>
            <option value="prefer_not_to_say">Prefer not to say</option>
          </select>
        </div>
      </div>

      {/* Race/Ethnicity Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Race/Ethnicity</h2>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Please select the option that best describes your racial/ethnic background (Optional)
          </label>
          <p className="text-xs text-gray-500 mb-4">You may select multiple options if applicable:</p>
          
          <div className="space-y-3">
            {[
              { value: 'hispanic_latino', label: 'Hispanic or Latino' },
              { value: 'white', label: 'White (Not Hispanic or Latino)' },
              { value: 'black', label: 'Black or African American' },
              { value: 'native_american', label: 'American Indian or Alaska Native' },
              { value: 'asian', label: 'Asian' },
              { value: 'pacific_islander', label: 'Native Hawaiian or Other Pacific Islander' },
              { value: 'two_or_more', label: 'Two or More Races' },
              { value: 'prefer_not_to_say', label: 'Prefer not to say' }
            ].map((option) => (
              <label key={option.value} className="flex items-center text-sm text-gray-700">
                <input 
                  type="checkbox" 
                  checked={data.race.includes(option.value)}
                  onChange={(e) => handleRaceChange(option.value, e.target.checked)}
                  className="mr-3"
                />
                {option.label}
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Veteran Status Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Veteran Status</h2>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Are you a protected veteran? (Optional)
          </label>
          <select 
            value={data.veteranStatus}
            onChange={(e) => onChange({ ...data, veteranStatus: e.target.value })}
            className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
          >
            <option value="">— Make a Selection —</option>
            <option value="yes">Yes, I am a protected veteran</option>
            <option value="no">No, I am not a protected veteran</option>
            <option value="prefer_not_to_say">Prefer not to say</option>
          </select>
        </div>
      </div>

      {/* Disability Status Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Disability Status</h2>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Do you have a disability? (Optional)
          </label>
          <select 
            value={data.disability}
            onChange={(e) => onChange({ ...data, disability: e.target.value })}
            className="w-full px-3 py-3 border border-gray-300 rounded-md text-base"
          >
            <option value="">— Make a Selection —</option>
            <option value="yes">Yes, I have a disability</option>
            <option value="no">No, I do not have a disability</option>
            <option value="prefer_not_to_say">Prefer not to say</option>
          </select>
        </div>
      </div>
    </div>
  )
}

// Step 6: Review Step  
function ReviewStep({ data, jobTitle, onSubmit, onBack, isSubmitting }: { 
  data: ApplicationData, 
  jobTitle: string,
  onSubmit: () => void,
  onBack: () => void,
  isSubmitting: boolean
}) {
  const [termsAccepted, setTermsAccepted] = useState(false)
  const [dataConsent, setDataConsent] = useState(true)

  return (
    <div className="space-y-8">
      {/* Review Header */}
      <div className="text-center mb-12">
        <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
          <Eye className="w-8 h-8 text-primary-100" />
        </div>
        <h2 className="text-3xl font-semibold text-gray-900 mb-3">Review Your Application</h2>
        <p className="text-gray-600 max-w-lg mx-auto">
          Please review all the information below before submitting your application. You can edit any section by clicking the "Edit" button.
        </p>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold text-gray-900">Position</h3>
          <button className="bg-gray-200 text-gray-700 px-3 py-1 rounded-lg text-sm font-medium hover:bg-gray-300 transition-colors">
            Edit
          </button>
        </div>
        <p className="text-gray-700 font-medium">{jobTitle}</p>
      </div>
        
      {/* Personal Information */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold text-gray-900">Personal Information</h3>
          <button className="bg-gray-200 text-gray-700 px-3 py-1 rounded-lg text-sm font-medium hover:bg-gray-300 transition-colors">
            Edit
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <span className="text-sm text-gray-600">Name:</span>
            <p className="font-medium text-gray-900">{data.personalInfo.firstName} {data.personalInfo.lastName}</p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Email:</span>
            <p className="font-medium text-gray-900">{data.personalInfo.email}</p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Phone:</span>
            <p className="font-medium text-gray-900">{data.personalInfo.phone}</p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Location:</span>
            <p className="font-medium text-gray-900">{data.addressInfo.city}, {data.addressInfo.state}, {data.addressInfo.country}</p>
          </div>
        </div>
      </div>

      {/* Experience & Skills */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold text-gray-900">Experience & Skills</h3>
          <button className="bg-gray-200 text-gray-700 px-3 py-1 rounded-lg text-sm font-medium hover:bg-gray-300 transition-colors">
            Edit
          </button>
        </div>
        <div className="space-y-4">
          {data.experience.summary && (
            <div>
              <span className="text-sm text-gray-600">Professional Summary:</span>
              <p className="text-gray-900 mt-1">{data.experience.summary}</p>
            </div>
          )}
          {data.experience.workExperience.length > 0 && (
            <div>
              <span className="text-sm text-gray-600">Current Position:</span>
              <p className="font-medium text-gray-900">{data.experience.workExperience[0]?.jobTitle} at {data.experience.workExperience[0]?.company}</p>
            </div>
          )}
          {data.experience.technicalSkills && (
            <div>
              <span className="text-sm text-gray-600">Key Skills:</span>
              <p className="text-gray-900">{data.experience.technicalSkills}</p>
            </div>
          )}
        </div>
      </div>

      {/* Application Preferences */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold text-gray-900">Application Preferences</h3>
          <button className="bg-gray-200 text-gray-700 px-3 py-1 rounded-lg text-sm font-medium hover:bg-gray-300 transition-colors">
            Edit
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <span className="text-sm text-gray-600">Work Authorization:</span>
            <p className="font-medium text-gray-900">{data.questions.workAuthorization || 'Not specified'}</p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Willing to Relocate:</span>
            <p className="font-medium text-gray-900">{data.questions.relocate || 'Not specified'}</p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Remote Work:</span>
            <p className="font-medium text-gray-900">{data.questions.remoteWork || 'Not specified'}</p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Availability:</span>
            <p className="font-medium text-gray-900">{data.questions.availability || 'Not specified'}</p>
          </div>
        </div>
      </div>

      {/* Attached Documents */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h3 className="text-xl font-semibold text-gray-900 mb-6">Attached Documents</h3>
        <div className="flex items-center gap-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <FileText className="w-8 h-8 text-gray-600" />
          <div>
            <p className="font-medium text-gray-900">dhyan_raj_resume.pdf</p>
            <span className="text-sm text-gray-600">Uploaded and analyzed by AI</span>
          </div>
        </div>
      </div>

      {/* Terms & Conditions */}
      <div className="bg-white border border-gray-200 rounded-xl p-8">
        <h3 className="text-xl font-semibold text-gray-900 mb-6">Terms & Conditions</h3>
        
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 mb-6">
          <p className="text-sm text-gray-700 leading-relaxed">
            By submitting this application, you acknowledge that the information provided is accurate and complete to the best of your knowledge. 
            You understand that any false information may result in disqualification from consideration or termination of employment if hired.
          </p>
        </div>
        
        <div className="space-y-4">
          <label className="flex items-start gap-3 cursor-pointer">
            <input 
              type="checkbox"
              checked={termsAccepted}
              onChange={(e) => setTermsAccepted(e.target.checked)}
              className="mt-1"
              required
            />
            <span className="text-sm leading-relaxed text-gray-700">
              I certify that the information I have provided in this application is true, complete, and accurate to the best of my knowledge. I understand that providing false or misleading information may result in rejection of my application or termination if employed.
            </span>
          </label>
          
          <label className="flex items-start gap-3 cursor-pointer">
            <input 
              type="checkbox"
              checked={dataConsent}
              onChange={(e) => setDataConsent(e.target.checked)}
              className="mt-1"
            />
            <span className="text-sm leading-relaxed text-gray-700">
              I consent to S Corp. processing my application data for recruitment purposes and contacting me regarding this position and future opportunities that may be of interest.
            </span>
          </label>
        </div>
      </div>

      {/* Navigation Buttons - consistent with other steps */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200">
        <Button 
          variant="secondary" 
          onClick={onBack}
          className="px-6 py-3 text-base bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 hover:text-gray-900 shadow-sm"
        >
          Back
        </Button>
        
        <Button
          variant="primary"
          onClick={() => termsAccepted && onSubmit()}
          disabled={!termsAccepted || isSubmitting}
          className={`px-6 py-3 text-base ${
            !termsAccepted || isSubmitting ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {isSubmitting ? 'Submitting...' : 'Submit Application'}
        </Button>
      </div>

    </div>
  )
}

export default function ApplicationPage({ params }: ApplicationPageProps) {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState<ApplicationData>(initialFormData)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [resolvedParams, setResolvedParams] = useState<{ jobId: string } | null>(null)
  const hasPreFilledRef = useRef(false)
  const { toasts, showToast, removeToast, clearAllToasts } = useToast()
  
  useEffect(() => {
    params.then(setResolvedParams)
  }, [params])
  
  const jobTitle = resolvedParams ? (jobTitles[resolvedParams.jobId] || 'Unknown Position') : 'Loading...'
  const hasResume = user?.isResumeAvailable || false

  useEffect(() => {
    // Get user from localStorage
    const userData = localStorage.getItem('user')
    if (userData) {
      const parsedUser = JSON.parse(userData)
      setUser(parsedUser)
      
      // AI pre-fill for users with resume (only once)
      if (parsedUser.isResumeAvailable && !hasPreFilledRef.current) {
        hasPreFilledRef.current = true
        setFormData(prev => ({
          ...prev,
          personalInfo: {
            firstName: 'Dhyan',
            lastName: 'Raj', 
            email: 'dhyan.raj@gmail.com',
            phone: '+1 (555) 123-4567',
            linkedIn: 'https://linkedin.com/in/dhyanraj'
          },
          addressInfo: {
            street: '123 Tech Street',
            city: 'San Francisco',
            state: 'CA',
            zipCode: '94102',
            country: 'US'
          },
          experience: {
            summary: 'Experienced Full Stack Developer with 8+ years in building scalable web applications. Proficient in React, Node.js, Python, and cloud technologies. Strong background in agile development and cross-functional collaboration.',
            technicalSkills: 'JavaScript, TypeScript, React, Vue.js, Node.js, Python, Django, PostgreSQL, MongoDB, AWS, Docker, Kubernetes, Git, REST APIs, GraphQL',
            softSkills: 'Leadership, Team Collaboration, Problem Solving, Communication, Agile/Scrum, Project Management',
            workExperience: [
              {
                company: 'TechCorp Inc.',
                jobTitle: 'Senior Software Engineer',
                startDate: '2020-03',
                endDate: '2024-12',
                isCurrent: true,
                location: 'San Francisco, CA',
                responsibilities: '• Lead development of microservices architecture serving 1M+ daily users\n• Mentored 5 junior developers and conducted code reviews\n• Improved application performance by 40% through optimization\n• Implemented CI/CD pipelines reducing deployment time by 60%'
              },
              {
                company: 'StartupXYZ',
                jobTitle: 'Full Stack Developer',
                startDate: '2018-06',
                endDate: '2020-02',
                isCurrent: false,
                location: 'Remote',
                responsibilities: '• Built responsive web applications using React and Node.js\n• Developed RESTful APIs and integrated third-party services\n• Collaborated with design team to implement pixel-perfect UIs\n• Participated in agile development processes and daily standups'
              }
            ],
            education: [
              {
                institution: 'Stanford University',
                degree: 'Master of Science in Computer Science',
                fieldOfStudy: 'Software Engineering',
                graduationYear: 2018,
                gpa: '3.8'
              }
            ]
          }
        }))
        
        // Show pre-fill notification
        setTimeout(() => {
          showToast.success('Information pre-filled from your resume')
        }, 1000)
      }
    } else if (resolvedParams) {
      // Redirect to login if not authenticated
      router.push(`/login?redirect=/apply/${resolvedParams.jobId}`)
    }
  }, [resolvedParams, router])

  const handleNext = async () => {
    if (!resolvedParams) return
    
    // Save current step data with appropriate notification
    const stepMessages = {
      1: 'Saving information...',
      2: 'Saving experience...',
      3: 'Saving responses...',
      4: 'Saving voluntary disclosures...',
      5: 'Saving identity information...'
    }
    
    if (currentStep <= 5) {
      const message = stepMessages[currentStep as keyof typeof stepMessages]
      showToast.info(message)
      
      // Simulate successful API call to save step data
      setTimeout(() => {
        // Mock successful save
        console.log('Saving step data:', {
          stepData: getStepData(currentStep),
          userId: user?.id,
          jobId: resolvedParams.jobId,
          step: currentStep
        })
        
        // Clear the "Saving..." toast before showing success
        clearAllToasts()
        // Show success toast after a brief delay to ensure proper sequencing
        setTimeout(() => {
          showToast.success('Information saved successfully!')
        }, 100)
        
        if (currentStep < steps.length) {
          setCurrentStep(currentStep + 1)
        }
      }, 1000)
    } else if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1)
    }
  }
  
  // Helper function to get current step data
  const getStepData = (step: number) => {
    switch (step) {
      case 1:
        return { personalInfo: formData.personalInfo, addressInfo: formData.addressInfo }
      case 2:
        return { experience: formData.experience }
      case 3:
        return { questions: formData.questions }
      case 4:
        return { disclosures: formData.disclosures }
      case 5:
        return { identity: formData.identity }
      default:
        return {}
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    } else if (resolvedParams) {
      // Go back to job detail
      router.push(`/jobs/${resolvedParams.jobId}`)
    }
  }

  const handleSubmit = async () => {
    if (!resolvedParams) return
    
    setIsSubmitting(true)
    showToast.info('Submitting your application...')
    
    // Simulate successful application submission
    setTimeout(() => {
      // Mock successful submission
      console.log('Submitting complete application:', {
        applicationData: formData,
        userId: user?.id,
        jobId: resolvedParams.jobId
      })
      
      // Clear the "Submitting..." toast before showing success
      clearAllToasts()
      setTimeout(() => {
        showToast.success('Application submitted successfully!')
      }, 100)
      
      setTimeout(() => {
        setIsSubmitting(false)
        
        // Simulate AI evaluation logic - 70% chance of being eligible
        const isEligible = Math.random() > 0.3
        
        // Update user state with new application
        if (user && resolvedParams) {
          const newApplication = {
            jobId: resolvedParams.jobId,
            qualified: isEligible,
            status: isEligible ? 'ELIGIBLE' : undefined, // Set status based on eligibility
            interviewSession: isEligible ? `session-${Date.now()}` : undefined,
            appliedAt: new Date().toISOString()
          }
          
          const updatedUser = {
            ...user,
            applications: [...(user.applications || []), newApplication]
          }
          
          localStorage.setItem('user', JSON.stringify(updatedUser))
        }
        
        // Use the eligibility result for redirect
        const resultType = isEligible ? 'eligible' : 'under-review'
        
        // Redirect to results page with result type
        router.push(`/apply/${resolvedParams.jobId}/result?result=${resultType}`)
      }, 1500)
    }, 2000)
  }

  const isGuest = !user
  const userState = isGuest ? "guest" : (user.isResumeAvailable ? "has-resume" : "no-resume")

  if (!user) {
    return (
      <div className="page-light min-h-screen">
        <Navigation userState="guest" user={null} theme="light" />
        <main className="container max-w-[1400px] mx-auto px-6 pt-20">
          <div className="text-center py-20">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Please Log In</h1>
            <p className="text-gray-600 mb-6">You need to be logged in to apply for this position.</p>
            <Button 
              variant="primary" 
              onClick={() => resolvedParams && router.push(`/login?redirect=/apply/${resolvedParams.jobId}`)}
            >
              Log In to Apply
            </Button>
          </div>
        </main>
      </div>
    )
  }

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <PersonalInfoStep 
            personalData={formData.personalInfo}
            addressData={formData.addressInfo}
            onPersonalChange={(data) => setFormData(prev => ({ ...prev, personalInfo: data }))}
            onAddressChange={(data) => setFormData(prev => ({ ...prev, addressInfo: data }))}
          />
        )
      case 2:
        return (
          <ExperienceStep 
            data={formData.experience} 
            onChange={(data) => setFormData(prev => ({ ...prev, experience: data }))}
          />
        )
      case 3:
        return (
          <ApplicationQuestionsStep 
            data={formData.questions} 
            onChange={(data) => setFormData(prev => ({ ...prev, questions: data }))}
          />
        )
      case 4:
        return (
          <VoluntaryDisclosuresStep 
            data={formData.disclosures} 
            onChange={(data) => setFormData(prev => ({ ...prev, disclosures: data }))}
          />
        )
      case 5:
        return (
          <SelfIdentityStep 
            data={formData.identity} 
            onChange={(data) => setFormData(prev => ({ ...prev, identity: data }))}
          />
        )
      case 6:
        return (
          <ReviewStep 
            data={formData} 
            jobTitle={jobTitle} 
            onSubmit={handleSubmit}
            onBack={handleBack}
            isSubmitting={isSubmitting}
          />
        )
      default:
        return null
    }
  }

  return (
    <div className="page-light min-h-screen">
      <Navigation userState={userState} user={user} theme="light" />
      
      <main className="container max-w-[1200px] mx-auto px-6 pt-20 pb-8">
        {/* Back Link */}
        <div className="mb-8">
          <Link 
            href={resolvedParams ? `/jobs/${resolvedParams.jobId}` : '#'}
            className="text-blue-600 hover:text-blue-700 flex items-center text-base"
          >
            <span className="mr-2">←</span> Back to Job Posting
          </Link>
        </div>

        {/* Job Title */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-gray-900">{jobTitle}</h1>
        </div>

        {/* Progress Indicator */}
        <ProgressIndicator currentStep={currentStep} totalSteps={steps.length} />

        {/* AI Pre-fill Notice */}
        {hasResume && currentStep === 1 && (
          <div className="bg-[#f0f9ff] border border-[#0ea5e9] rounded-xl p-8 mb-12">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">AI-Powered Pre-fill Complete</h2>
                <p className="text-blue-900 text-sm">Information automatically extracted from your uploaded resume</p>
              </div>
            </div>
            <p className="text-blue-900 leading-relaxed">
              We've analyzed your resume and pre-filled most of your information above. Please review and update any details as needed. 
              Your resume has been securely stored and will be included with your application.
            </p>
          </div>
        )}

        {/* Form Content */}
        <div className="max-w-4xl mx-auto">
          {renderCurrentStep()}
          
{/* Navigation Buttons - only show for non-review steps */}
          {currentStep !== steps.length && (
            <div className="flex justify-between items-center mt-12 pt-8 border-t border-gray-200">
              <Button 
                variant="secondary" 
                onClick={handleBack}
                className="px-6 py-3 text-base bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 hover:text-gray-900 shadow-sm"
              >
                Back
              </Button>
              
              <Button 
                variant="primary" 
                onClick={handleNext}
                className="px-6 py-3 text-base"
              >
                Next: {steps[currentStep]?.title || 'Continue'}
              </Button>
            </div>
          )}
        </div>
      </main>
      
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  )
}