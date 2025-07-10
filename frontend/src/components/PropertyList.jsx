import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import PropertyCard from './PropertyCard'
import PropertyForm from './PropertyForm'

export default function PropertyList({ onSyncComplete }) {
  const [properties, setProperties] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showAddForm, setShowAddForm] = useState(false)

  useEffect(() => {
    loadProperties()
  }, [])

  const loadProperties = async () => {
    try {
      setLoading(true)
      const result = await api.getProperties()
      if (result.success) {
        setProperties(result.properties || [])
      } else {
        setError(result.error || 'Failed to load properties')
      }
    } catch (err) {
      setError('Failed to load properties: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handlePropertyAdded = (newProperty) => {
    if (newProperty && newProperty.id) {
      setProperties([newProperty, ...properties])
      // Call onSyncComplete when a property is added
      if (onSyncComplete) {
        onSyncComplete()
      }
    }
    setShowAddForm(false)
  }

  const handlePropertyUpdated = () => {
    // Refresh properties list
    loadProperties()
  }

  const handlePropertyDeleted = (propertyId) => {
    setProperties(properties.filter(p => p.id !== propertyId))
    // Call onSyncComplete when a property is deleted
    if (onSyncComplete) {
      onSyncComplete()
    }
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading properties...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <div className="mt-2 text-sm text-red-700">
              {error}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Properties</h2>
          <p className="mt-1 text-sm text-gray-600">
            Manage your rental properties and calendar synchronization
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <svg className="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Add Property
        </button>
      </div>

      {/* Properties Grid */}
      {properties.length === 0 ? (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No properties</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by adding your first property.</p>
          <div className="mt-6">
            <button
              onClick={() => setShowAddForm(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Your First Property
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {properties.filter(property => property && property.id).map((property) => (
            <PropertyCard
              key={property.id}
              property={property}
              onPropertyUpdated={handlePropertyUpdated}
              onPropertyDeleted={handlePropertyDeleted}
              onSyncComplete={onSyncComplete}
            />
          ))}
        </div>
      )}

      {/* Add Property Form Modal */}
      {showAddForm && (
        <PropertyForm
          onPropertyAdded={handlePropertyAdded}
          onCancel={() => setShowAddForm(false)}
        />
      )}
    </div>
  )
} 