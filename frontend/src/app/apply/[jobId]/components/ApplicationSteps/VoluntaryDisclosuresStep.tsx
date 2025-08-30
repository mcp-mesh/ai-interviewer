import { ApplicationData } from '../../types'

interface VoluntaryDisclosuresStepProps {
  data: ApplicationData['disclosures']
  onChange: (data: ApplicationData['disclosures']) => void
}

// Step 4: Voluntary Disclosures
export function VoluntaryDisclosuresStep({ data, onChange }: VoluntaryDisclosuresStepProps) {
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