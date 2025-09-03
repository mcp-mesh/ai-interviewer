import { ApplicationData, WorkExperience, Education } from '../../types'

interface ExperienceStepProps {
  data: ApplicationData['experience']
  onChange: (data: ApplicationData['experience']) => void
}

// Step 2: Experience
export function ExperienceStep({ data, onChange }: ExperienceStepProps) {
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