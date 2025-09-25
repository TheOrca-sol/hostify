import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { toast } from '../components/Toaster'
import ReservationPasscodeManager from '../components/ReservationPasscodeManager'
import {
  ArrowLeft, User, MapPin, Calendar, Clock, Phone, Mail,
  CreditCard, Lock, Home, Edit, Trash2
} from 'lucide-react'

export default function ReservationDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [reservation, setReservation] = useState(null)
  const [property, setProperty] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (id) {
      loadReservationDetails()
    }
  }, [id])

  const loadReservationDetails = async () => {
    try {
      setLoading(true)
      setError(null)

      const result = await api.getReservation(id)

      if (result.success && result.reservation) {
        setReservation(result.reservation)

        // Load property details if we have a property_id
        if (result.reservation.property_id) {
          const propertyResult = await api.getProperty(result.reservation.property_id)
          if (propertyResult.success) {
            setProperty(propertyResult.property)
          }
        }
      } else {
        setError(result.error || 'Reservation not found')
      }
    } catch (err) {
      console.error('Error loading reservation details:', err)
      setError('Failed to load reservation details')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Not set'
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const formatDateTime = (dateString) => {
    if (!dateString) return 'Not set'
    return new Date(dateString).toLocaleString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  const getStatusColor = (status) => {
    const colors = {
      confirmed: 'text-green-700 bg-green-100',
      pending: 'text-yellow-700 bg-yellow-100',
      checked_in: 'text-blue-700 bg-blue-100',
      checked_out: 'text-gray-700 bg-gray-100',
      cancelled: 'text-red-700 bg-red-100'
    }
    return colors[status] || 'text-gray-700 bg-gray-100'
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse space-y-6">
            {/* Header */}
            <div className="flex items-center space-x-4">
              <div className="w-6 h-6 bg-gray-200 rounded"></div>
              <div className="h-8 bg-gray-200 rounded w-1/3"></div>
            </div>

            {/* Main content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <div className="space-y-4">
                    <div className="h-6 bg-gray-200 rounded w-1/4"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                  </div>
                </div>
              </div>
              <div className="space-y-6">
                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <div className="space-y-4">
                    <div className="h-6 bg-gray-200 rounded w-1/3"></div>
                    <div className="h-20 bg-gray-200 rounded"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
            <div className="text-red-500 text-xl mb-4">⚠️</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Reservation</h3>
            <p className="text-gray-600 mb-6">{error}</p>
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!reservation) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Reservation Not Found</h3>
            <p className="text-gray-600 mb-6">The requested reservation could not be found.</p>
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="text-gray-600 hover:text-gray-900 p-2 rounded-lg hover:bg-gray-100"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Reservation Details
                </h1>
                <p className="text-gray-600">
                  {reservation.first_name} {reservation.last_name} • {property?.name || 'Property'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(reservation.status)}`}>
                {reservation.status?.charAt(0).toUpperCase() + reservation.status?.slice(1)}
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Guest Information */}
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  <User className="w-5 h-5 mr-2" />
                  Guest Information
                </h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Name</label>
                    <p className="text-gray-900 mt-1">{reservation.first_name} {reservation.last_name}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Email</label>
                    <p className="text-gray-900 mt-1 flex items-center">
                      <Mail className="w-4 h-4 mr-2" />
                      {reservation.email || 'Not provided'}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Phone</label>
                    <p className="text-gray-900 mt-1 flex items-center">
                      <Phone className="w-4 h-4 mr-2" />
                      {reservation.phone || 'Not provided'}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Guests</label>
                    <p className="text-gray-900 mt-1">{reservation.guest_count || 1} guest{(reservation.guest_count || 1) === 1 ? '' : 's'}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Reservation Details */}
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  <Calendar className="w-5 h-5 mr-2" />
                  Reservation Details
                </h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Check-in</label>
                    <p className="text-gray-900 mt-1">{formatDateTime(reservation.check_in)}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Check-out</label>
                    <p className="text-gray-900 mt-1">{formatDateTime(reservation.check_out)}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Total Amount</label>
                    <p className="text-gray-900 mt-1 flex items-center">
                      <CreditCard className="w-4 h-4 mr-2" />
                      ${reservation.total_amount || '0.00'}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Platform</label>
                    <p className="text-gray-900 mt-1">{reservation.platform || 'Direct'}</p>
                  </div>
                </div>

                {reservation.notes && (
                  <div className="mt-6">
                    <label className="text-sm font-medium text-gray-700">Notes</label>
                    <p className="text-gray-900 mt-1">{reservation.notes}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Smart Lock Access */}
            <ReservationPasscodeManager reservation={reservation} />
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Property Information */}
            {property && (
              <div className="bg-white rounded-lg shadow-sm border">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900 flex items-center">
                    <Home className="w-5 h-5 mr-2" />
                    Property
                  </h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-gray-900">{property.name}</h4>
                      {property.address && (
                        <p className="text-gray-600 mt-1 flex items-start">
                          <MapPin className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                          {property.address}
                        </p>
                      )}
                    </div>

                    {property.description && (
                      <div>
                        <label className="text-sm font-medium text-gray-700">Description</label>
                        <p className="text-gray-900 mt-1 text-sm">{property.description}</p>
                      </div>
                    )}

                    <button
                      onClick={() => navigate(`/properties/${property.id}`)}
                      className="w-full bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 text-sm"
                    >
                      View Property Details
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
              </div>
              <div className="p-6">
                <div className="space-y-3">
                  <button
                    onClick={() => navigate(`/reservations/${reservation.id}/edit`)}
                    className="w-full bg-blue-100 text-blue-700 px-4 py-2 rounded-lg hover:bg-blue-200 text-sm flex items-center justify-center"
                  >
                    <Edit className="w-4 h-4 mr-2" />
                    Edit Reservation
                  </button>

                  <button
                    onClick={() => navigate(`/messages?reservation=${reservation.id}`)}
                    className="w-full bg-green-100 text-green-700 px-4 py-2 rounded-lg hover:bg-green-200 text-sm flex items-center justify-center"
                  >
                    <Mail className="w-4 h-4 mr-2" />
                    Send Message
                  </button>

                  <button
                    className="w-full bg-red-100 text-red-700 px-4 py-2 rounded-lg hover:bg-red-200 text-sm flex items-center justify-center"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Cancel Reservation
                  </button>
                </div>
              </div>
            </div>

            {/* Timeline/History */}
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  <Clock className="w-5 h-5 mr-2" />
                  History
                </h3>
              </div>
              <div className="p-6">
                <div className="space-y-3">
                  <div className="flex items-center space-x-3 text-sm">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-gray-600">
                      Created: {formatDate(reservation.created_at)}
                    </span>
                  </div>
                  {reservation.updated_at && reservation.updated_at !== reservation.created_at && (
                    <div className="flex items-center space-x-3 text-sm">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span className="text-gray-600">
                        Last updated: {formatDate(reservation.updated_at)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}