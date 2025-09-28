import React, { useState } from 'react'
import { api } from '../services/api'

export default function PropertyForm({ onPropertyAdded, onCancel }) {
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    ical_url: '',
    sync_frequency: 3,
    auto_verification: true,
    auto_contract: true,
    auto_messaging: true,
    // New fields
    wifi_name: '',
    wifi_password: '',
    check_in_time: '15:00',
    check_out_time: '11:00',
    latitude: '',
    longitude: '',
    property_type: 'apartment',
    access_instructions: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [urlTestResult, setUrlTestResult] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (!formData.name.trim()) {
        throw new Error('Property name is required')
      }

      // If we have a URL but haven't tested it, test it first
      if (formData.ical_url && !urlTestResult?.success) {
        const testResult = await testIcalUrl()
        if (!testResult.success) {
          throw new Error('Please fix the iCal URL issues before continuing')
        }
      }

      const result = await api.createProperty(formData)
      if (result.success) {
        // If property was created with a calendar URL, trigger initial sync
        if (formData.ical_url) {
          await api.syncPropertyCalendar(result.property.id)
        }
        onPropertyAdded(result.property)
      } else {
        throw new Error(result.error || 'Failed to create property')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setFormData({
      ...formData,
      [e.target.name]: value
    })
    // Reset URL test result when URL changes
    if (e.target.name === 'ical_url') {
      setUrlTestResult(null)
    }
  }

  const testIcalUrl = async () => {
    if (!formData.ical_url) {
      setUrlTestResult({ success: false, error: 'Please enter an iCal URL' })
      return
    }
    
    try {
      setLoading(true)
      const result = await api.testIcalUrl(formData.ical_url)
      setUrlTestResult(result)
      if (!result.success) {
        throw new Error(result.error || 'Invalid iCal URL')
      }
      return result
    } catch (err) {
      setUrlTestResult({ success: false, error: err.message })
      throw err
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
      <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Add New Property</h3>
          <p className="mt-1 text-sm text-gray-600">
            Add a property to start managing reservations and guest verification.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
              {error}
            </div>
          )}

          {/* Property Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700">
              Property Name *
            </label>
            <input
              type="text"
              id="name"
              name="name"
              required
              value={formData.name}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g., Ocean View Apartment"
            />
          </div>

          {/* Address */}
          <div>
            <label htmlFor="address" className="block text-sm font-medium text-gray-700">
              Address
            </label>
            <input
              type="text"
              id="address"
              name="address"
              value={formData.address}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Property address"
            />
          </div>

          {/* iCal URL */}
          <div>
            <label htmlFor="ical_url" className="block text-sm font-medium text-gray-700">
              Calendar iCal URL
            </label>
            <div className="mt-1 flex rounded-md shadow-sm">
              <input
                type="url"
                id="ical_url"
                name="ical_url"
                value={formData.ical_url}
                onChange={handleChange}
                className={`flex-1 min-w-0 block w-full px-3 py-2 border rounded-l-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                  urlTestResult?.success ? 'border-green-300' : 
                  urlTestResult?.error ? 'border-red-300' : 
                  'border-gray-300'
                }`}
                placeholder="https://airbnb.com/calendar/ical/..."
              />
              <button
                type="button"
                onClick={testIcalUrl}
                disabled={!formData.ical_url || loading}
                className={`inline-flex items-center px-3 py-2 border border-l-0 rounded-r-md text-sm ${
                  urlTestResult?.success ? 'bg-green-50 text-green-700 border-green-300 hover:bg-green-100' :
                  urlTestResult?.error ? 'bg-red-50 text-red-700 border-red-300 hover:bg-red-100' :
                  'bg-gray-50 text-gray-500 border-gray-300 hover:bg-gray-100'
                } focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {loading ? 'Testing...' : 'Test URL'}
              </button>
            </div>
            {urlTestResult && (
              <p className={`mt-1 text-sm ${urlTestResult.success ? 'text-green-600' : 'text-red-600'}`}>
                {urlTestResult.success ? '✓ Valid iCal URL' : urlTestResult.error}
              </p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Get this from Airbnb, Booking.com, or your calendar platform
            </p>
          </div>

          {/* Sync Frequency */}
          <div>
            <label htmlFor="sync_frequency" className="block text-sm font-medium text-gray-700">
              Sync Frequency (hours)
            </label>
            <select
              id="sync_frequency"
              name="sync_frequency"
              value={formData.sync_frequency}
              onChange={handleChange}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
            >
              <option value="1">Every hour</option>
              <option value="3">Every 3 hours</option>
              <option value="6">Every 6 hours</option>
              <option value="12">Every 12 hours</option>
              <option value="24">Once a day</option>
            </select>
          </div>

          {/* Property Type and Times */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="property_type" className="block text-sm font-medium text-gray-700">
                Property Type
              </label>
              <select
                id="property_type"
                name="property_type"
                value={formData.property_type}
                onChange={handleChange}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
              >
                <option value="apartment">Apartment</option>
                <option value="house">House</option>
                <option value="villa">Villa</option>
                <option value="studio">Studio</option>
                <option value="condo">Condo</option>
                <option value="room">Room</option>
              </select>
            </div>
            <div></div>
          </div>

          {/* Check-in/Check-out Times */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="check_in_time" className="block text-sm font-medium text-gray-700">
                Default Check-in Time
              </label>
              <input
                type="time"
                id="check_in_time"
                name="check_in_time"
                value={formData.check_in_time}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label htmlFor="check_out_time" className="block text-sm font-medium text-gray-700">
                Default Check-out Time
              </label>
              <input
                type="time"
                id="check_out_time"
                name="check_out_time"
                value={formData.check_out_time}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* WiFi Information */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="wifi_name" className="block text-sm font-medium text-gray-700">
                WiFi Name (SSID)
              </label>
              <input
                type="text"
                id="wifi_name"
                name="wifi_name"
                value={formData.wifi_name}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="WiFi network name"
              />
            </div>
            <div>
              <label htmlFor="wifi_password" className="block text-sm font-medium text-gray-700">
                WiFi Password
              </label>
              <input
                type="text"
                id="wifi_password"
                name="wifi_password"
                value={formData.wifi_password}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="WiFi password"
              />
            </div>
          </div>

          {/* Location Coordinates */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="latitude" className="block text-sm font-medium text-gray-700">
                Latitude (Optional)
              </label>
              <input
                type="number"
                step="any"
                id="latitude"
                name="latitude"
                value={formData.latitude}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., 36.8485"
              />
            </div>
            <div>
              <label htmlFor="longitude" className="block text-sm font-medium text-gray-700">
                Longitude (Optional)
              </label>
              <input
                type="number"
                step="any"
                id="longitude"
                name="longitude"
                value={formData.longitude}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., 10.1658"
              />
            </div>
          </div>

          {/* Access Instructions */}
          <div>
            <label htmlFor="access_instructions" className="block text-sm font-medium text-gray-700">
              Access Instructions (Optional)
            </label>
            <textarea
              id="access_instructions"
              name="access_instructions"
              rows={3}
              value={formData.access_instructions}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Door codes, key location, special instructions for guests..."
            />
          </div>

          {/* Auto Features */}
          <div className="space-y-3">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="auto_verification"
                name="auto_verification"
                checked={formData.auto_verification}
                onChange={handleChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="auto_verification" className="ml-2 block text-sm text-gray-700">
                Auto-send verification links to guests
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="auto_contract"
                name="auto_contract"
                checked={formData.auto_contract}
                onChange={handleChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="auto_contract" className="ml-2 block text-sm text-gray-700">
                Auto-generate contracts for verified guests
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="auto_messaging"
                name="auto_messaging"
                checked={formData.auto_messaging}
                onChange={handleChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="auto_messaging" className="ml-2 block text-sm text-gray-700">
                Enable automated messaging (e.g., check-in instructions)
              </label>
            </div>
          </div>

          {/* Form Actions */}
          <div className="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || (formData.ical_url && !urlTestResult?.success)}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Property'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
} 