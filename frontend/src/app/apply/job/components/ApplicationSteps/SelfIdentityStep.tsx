import { ApplicationData } from '../../types'

interface SelfIdentityStepProps {
  data: ApplicationData['identity']
  onChange: (data: ApplicationData['identity']) => void
}

// Step 5: Self Identity
export function SelfIdentityStep({ data, onChange }: SelfIdentityStepProps) {
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