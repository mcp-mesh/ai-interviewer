import { ApplicationData } from '../../types'

interface PersonalInfoStepProps {
  personalData: ApplicationData['personalInfo']
  addressData: ApplicationData['addressInfo']
  onPersonalChange: (data: ApplicationData['personalInfo']) => void
  onAddressChange: (data: ApplicationData['addressInfo']) => void
}

// Step 1: Personal Information
export function PersonalInfoStep({ 
  personalData, 
  addressData, 
  onPersonalChange, 
  onAddressChange 
}: PersonalInfoStepProps) {
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