import { ApplicationData } from '../../types'

interface ApplicationQuestionsStepProps {
  data: ApplicationData['questions']
  onChange: (data: ApplicationData['questions']) => void
}

// Step 3: Application Questions
export function ApplicationQuestionsStep({ data, onChange }: ApplicationQuestionsStepProps) {
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