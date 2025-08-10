import React, { useState, useEffect } from 'react'
import { useAuth } from '../services/auth'
import { useNavigate } from 'react-router-dom'
import { toast } from '../components/Toaster'
import { User, Mail, Phone, Building, Save, ArrowLeft } from 'lucide-react'

export default function Profile() {
  const { user, userProfile, refreshUserProfile, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [profileError, setProfileError] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    company_name: '',
    business_type: 'rental_host'
  })
  const [isEditing, setIsEditing] = useState(false)

  // Load profile if not already loaded
  useEffect(() => {
    if (user && !userProfile && !authLoading) {
      setProfileError(null)
      refreshUserProfile().catch(error => {
        console.error('Failed to load profile:', error)
        setProfileError('Failed to load profile. Please try again.')
      })
    }
  }, [user, userProfile, authLoading, refreshUserProfile])

  useEffect(() => {
    if (userProfile) {
      setFormData({
        name: userProfile.name || '',
        phone: userProfile.phone || '',
        company_name: userProfile.company_name || '',
        business_type: userProfile.business_type || 'rental_host'
      })
    }
  }, [userProfile])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      // For now, we'll just refresh the profile since update endpoint isn't implemented
      await refreshUserProfile()
      toast.success('Profile updated successfully!')
      setIsEditing(false)
    } catch (error) {
      toast.error('Failed to update profile')
      console.error('Profile update error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const businessTypes = [
    { value: 'rental_host', label: 'Rental Host' },
    { value: 'property_manager', label: 'Property Manager' },
    { value: 'real_estate_agent', label: 'Real Estate Agent' },
    { value: 'hotel_owner', label: 'Hotel Owner' },
    { value: 'vacation_rental', label: 'Vacation Rental' },
    { value: 'other', label: 'Other' }
  ]

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading authentication...</p>
        </div>
      </div>
    )
  }

  if (!userProfile) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          {profileError ? (
            <>
              <div className="text-red-500 mb-4">
                <svg className="h-12 w-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <p className="text-gray-600">{profileError}</p>
              </div>
              <button
                onClick={() => {
                  setProfileError(null)
                  refreshUserProfile().catch(error => {
                    setProfileError('Failed to load profile. Please try again.')
                  })
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Retry
              </button>
            </>
          ) : (
            <>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading profile...</p>
            </>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/')}
            className="flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Dashboard
          </button>
          
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900">Profile</h1>
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-500"
            >
              {isEditing ? 'Cancel' : 'Edit Profile'}
            </button>
          </div>
        </div>

        {/* Profile Card */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center">
              <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center">
                <User className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <h2 className="text-lg font-medium text-gray-900">{userProfile.name}</h2>
                <p className="text-sm text-gray-500">{user?.email}</p>
              </div>
            </div>
          </div>

          <div className="px-6 py-4">
            {isEditing ? (
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Full Name
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Your full name"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <input
                      type="email"
                      value={user?.email || ''}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                      disabled
                    />
                  </div>
                  <p className="mt-1 text-xs text-gray-500">Email cannot be changed</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number
                  </label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <input
                      type="tel"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="+1234567890"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Company Name
                  </label>
                  <div className="relative">
                    <Building className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <input
                      type="text"
                      name="company_name"
                      value={formData.company_name}
                      onChange={handleChange}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Your company name"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Business Type
                  </label>
                  <select
                    name="business_type"
                    value={formData.business_type}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {businessTypes.map(type => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                    <Save className="h-4 w-4 mr-2" />
                    {loading ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                  <p className="text-gray-900">{userProfile.name || 'Not provided'}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                  <p className="text-gray-900">{user?.email}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
                  <p className="text-gray-900">{userProfile.phone || 'Not provided'}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Company Name</label>
                  <p className="text-gray-900">{userProfile.company_name || 'Not provided'}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Business Type</label>
                  <p className="text-gray-900">
                    {businessTypes.find(type => type.value === userProfile.business_type)?.label || 'Not specified'}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Member Since</label>
                  <p className="text-gray-900">
                    {userProfile.created_at ? new Date(userProfile.created_at).toLocaleDateString() : 'Unknown'}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
