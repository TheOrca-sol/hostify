import React, { useState } from 'react'
import { Phone, ChevronDown } from 'lucide-react'

const PhoneInput = ({ value, onChange, placeholder = "Phone number", required = false, className = "" }) => {
  const [selectedCountry, setSelectedCountry] = useState('MA') // Default to Morocco
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)

  // Common countries for the dropdown
  const countries = [
    { code: 'MA', name: 'Morocco', dialCode: '+212', flag: '🇲🇦' },
    { code: 'FR', name: 'France', dialCode: '+33', flag: '🇫🇷' },
    { code: 'ES', name: 'Spain', dialCode: '+34', flag: '🇪🇸' },
    { code: 'US', name: 'United States', dialCode: '+1', flag: '🇺🇸' },
    { code: 'GB', name: 'United Kingdom', dialCode: '+44', flag: '🇬🇧' },
    { code: 'DE', name: 'Germany', dialCode: '+49', flag: '🇩🇪' },
    { code: 'IT', name: 'Italy', dialCode: '+39', flag: '🇮🇹' },
    { code: 'SA', name: 'Saudi Arabia', dialCode: '+966', flag: '🇸🇦' },
    { code: 'AE', name: 'UAE', dialCode: '+971', flag: '🇦🇪' },
    { code: 'EG', name: 'Egypt', dialCode: '+20', flag: '🇪🇬' }
  ]

  const selectedCountryData = countries.find(c => c.code === selectedCountry)

  const handleCountrySelect = (country) => {
    setSelectedCountry(country.code)
    setIsDropdownOpen(false)
    
    // Update the phone number with new country code
    const currentNumber = value || ''
    const numberWithoutCountryCode = currentNumber.replace(/^\+\d+/, '').replace(/^0/, '')
    const newFullNumber = country.dialCode + numberWithoutCountryCode
    
    if (onChange) {
      onChange(newFullNumber)
    }
  }

  const handlePhoneChange = (e) => {
    let input = e.target.value
    
    // Remove any non-digit characters except +
    input = input.replace(/[^\d+]/g, '')
    
    // If user types a number without country code, prepend the selected country code
    if (input && !input.startsWith('+')) {
      if (input.startsWith('0')) {
        // Remove leading 0 for international format
        input = selectedCountryData.dialCode + input.substring(1)
      } else {
        input = selectedCountryData.dialCode + input
      }
    }
    
    if (onChange) {
      onChange(input)
    }
  }

  return (
    <div className={`relative ${className}`}>
      <div className="flex">
        {/* Country Code Dropdown */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center px-3 py-2 border border-r-0 border-gray-300 rounded-l-md bg-gray-50 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <span className="text-lg mr-2">{selectedCountryData?.flag}</span>
            <span className="text-sm text-gray-700">{selectedCountryData?.dialCode}</span>
            <ChevronDown className="h-4 w-4 ml-1 text-gray-500" />
          </button>

          {/* Dropdown */}
          {isDropdownOpen && (
            <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-300 rounded-md shadow-lg z-10 max-h-60 overflow-y-auto">
              {countries.map((country) => (
                <button
                  key={country.code}
                  type="button"
                  onClick={() => handleCountrySelect(country)}
                  className="w-full flex items-center px-3 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none text-left"
                >
                  <span className="text-lg mr-3">{country.flag}</span>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900">{country.name}</div>
                    <div className="text-xs text-gray-500">{country.dialCode}</div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Phone Number Input */}
        <div className="flex-1 relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Phone className="h-4 w-4 text-gray-400" />
          </div>
          <input
            type="tel"
            value={value || ''}
            onChange={handlePhoneChange}
            placeholder={placeholder}
            required={required}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-r-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Click overlay to close dropdown */}
      {isDropdownOpen && (
        <div
          className="fixed inset-0 z-0"
          onClick={() => setIsDropdownOpen(false)}
        />
      )}
    </div>
  )
}

export default PhoneInput 