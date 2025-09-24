import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { toast } from '../components/Toaster'
import SmartLockManagement from '../components/SmartLockManagement'
import { Lock, Home, ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function SmartLocks() {
  const navigate = useNavigate()
  const [properties, setProperties] = useState([])
  const [selectedProperty, setSelectedProperty] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadProperties()
  }, [])

  const loadProperties = async () => {
    try {
      setLoading(true)
      const result = await api.getProperties()
      if (result.success) {
        setProperties(result.properties)
        // Auto-select first property if only one exists
        if (result.properties.length === 1) {
          setSelectedProperty(result.properties[0])
        }
      } else {
        toast.error('Failed to load properties')
      }
    } catch (error) {
      console.error('Error loading properties:', error)
      toast.error('Failed to load properties')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-200 rounded w-1/3"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                  <Lock className="w-8 h-8 mr-3 text-blue-600" />
                  Smart Lock Management
                </h1>
                <p className="mt-1 text-gray-600">
                  Manage TTLock smart locks and generate access codes for guests
                </p>
              </div>
            </div>
          </div>
        </div>

        {properties.length === 0 ? (
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <Home className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Properties Found</h3>
            <p className="text-gray-600 mb-6">
              You need to create a property first before you can manage smart locks.
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
            >
              Go to Dashboard
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Property Selection */}
            {!selectedProperty && properties.length > 1 && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Select a Property
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {properties.map((property) => (
                    <div
                      key={property.id}
                      onClick={() => setSelectedProperty(property)}
                      className="border border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <Home className="w-5 h-5 text-gray-400" />
                        <div>
                          <h4 className="font-medium text-gray-900">{property.name}</h4>
                          {property.address && (
                            <p className="text-sm text-gray-600">{property.address}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Selected Property Info */}
            {selectedProperty && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Home className="w-6 h-6 text-blue-600" />
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900">
                        {selectedProperty.name}
                      </h2>
                      {selectedProperty.address && (
                        <p className="text-gray-600">{selectedProperty.address}</p>
                      )}
                    </div>
                  </div>

                  {properties.length > 1 && (
                    <button
                      onClick={() => setSelectedProperty(null)}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      Change Property
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Smart Lock Management Component */}
            {selectedProperty && (
              <SmartLockManagement property={selectedProperty} />
            )}

            {/* Test Instructions */}
            {selectedProperty && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h4 className="text-lg font-medium text-blue-900 mb-3">
                  🧪 Testing TTLock Integration
                </h4>
                <div className="space-y-2 text-blue-800">
                  <p>1. Click "Connect TTLock" to connect your TTLock account</p>
                  <p>2. Enter your TTLock app credentials (phone: +212663401973)</p>
                  <p>3. Your locks will be fetched automatically</p>
                  <p>4. Use "Test Code" button to generate random passcodes</p>
                  <p>5. Check your Flask logs to see the API calls in action</p>
                </div>

                <div className="mt-4 p-3 bg-blue-100 rounded">
                  <p className="text-sm text-blue-700">
                    <strong>Note:</strong> Make sure your backend server is running with ngrok tunnel active
                    for webhook functionality.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}