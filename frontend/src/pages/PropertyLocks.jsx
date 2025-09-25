import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { toast } from '../components/Toaster'
import SmartLockManagement from '../components/SmartLockManagement'
import { Lock, Home, ArrowLeft } from 'lucide-react'

export default function PropertyLocks() {
  const { propertyId } = useParams()
  const navigate = useNavigate()
  const [property, setProperty] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadProperty()
  }, [propertyId])

  const loadProperty = async () => {
    try {
      setLoading(true)
      const result = await api.getProperties()
      if (result.success) {
        const foundProperty = result.properties.find(p => p.id === propertyId)
        if (foundProperty) {
          setProperty(foundProperty)
        } else {
          toast.error('Property not found')
          navigate('/smart-locks')
        }
      } else {
        toast.error('Failed to load property')
        navigate('/smart-locks')
      }
    } catch (error) {
      console.error('Error loading property:', error)
      toast.error('Failed to load property')
      navigate('/smart-locks')
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

  if (!property) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/smart-locks')}
              className="text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <div className="flex items-center space-x-3">
                <Home className="w-6 h-6 text-blue-600" />
                <h1 className="text-3xl font-bold text-gray-900">
                  {property.name}
                </h1>
              </div>
              <p className="mt-1 text-gray-600 flex items-center">
                <Lock className="w-4 h-4 mr-2" />
                Smart Lock Management
                {property.address && (
                  <>
                    <span className="mx-2">•</span>
                    <span>{property.address}</span>
                  </>
                )}
              </p>
            </div>
          </div>
        </div>

        {/* Property Smart Lock Management */}
        <SmartLockManagement property={property} />
      </div>
    </div>
  )
}