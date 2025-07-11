import React, { useState, useEffect } from 'react'
import { api } from '../services/api'

export default function ReservationsList() {
  const [reservations, setReservations] = useState([])
  const [upcomingReservations, setUpcomingReservations] = useState([])
  const [currentReservations, setCurrentReservations] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeView, setActiveView] = useState('all')

  useEffect(() => {
    loadReservations()
  }, [])

  const loadReservations = async () => {
    try {
      setLoading(true)
      
      // Load all reservations
      const allResult = await api.getReservations()
      if (allResult.success) {
        setReservations(allResult.reservations || [])
      }
      
      // Load upcoming reservations
      const upcomingResult = await api.getUpcomingReservations()
      if (upcomingResult.success) {
        setUpcomingReservations(upcomingResult.reservations || [])
      }
      
      // Load current reservations
      const currentResult = await api.getCurrentReservations()
      if (currentResult.success) {
        setCurrentReservations(currentResult.reservations || [])
      }
      
    } catch (error) {
      console.error('Error loading reservations:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    } catch {
      return 'Invalid Date'
    }
  }

  const getReservationStatus = (reservation) => {
    const checkIn = new Date(reservation.check_in)
    const checkOut = new Date(reservation.check_out)
    const now = new Date()
    
    if (now < checkIn) {
      return { status: 'upcoming', color: 'bg-blue-100 text-blue-800', label: 'Upcoming' }
    } else if (now >= checkIn && now <= checkOut) {
      return { status: 'current', color: 'bg-green-100 text-green-800', label: 'Current' }
    } else {
      return { status: 'past', color: 'bg-gray-100 text-gray-800', label: 'Past' }
    }
  }

  const ReservationCard = ({ reservation }) => {
    const statusInfo = getReservationStatus(reservation)
    
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3 min-w-0 flex-1">
            <div className="h-10 w-10 flex-shrink-0 bg-blue-100 rounded-full flex items-center justify-center">
              <svg className="h-5 w-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a4 4 0 118 0v4m-4 12V11m0 0l-3 3m3-3l3 3" />
              </svg>
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="text-lg font-medium text-gray-900 truncate">
                {reservation.guest_name_partial || 'Guest'}
              </h3>
              <p className="text-sm text-gray-500 truncate">
                {reservation.property && reservation.property.name ? reservation.property.name : 'Unknown Property'} • ID: {reservation.external_id || reservation.id?.slice(0, 8)}
              </p>
            </div>
          </div>
          <div className="ml-2 flex-shrink-0">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.color}`}>
              {statusInfo.label}
            </span>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="min-w-0">
            <p className="text-sm text-gray-500">Check-in</p>
            <p className="text-sm font-medium text-gray-900 truncate">
              {formatDate(reservation.check_in)}
            </p>
          </div>
          <div className="min-w-0">
            <p className="text-sm text-gray-500">Check-out</p>
            <p className="text-sm font-medium text-gray-900 truncate">
              {formatDate(reservation.check_out)}
            </p>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="min-w-0">
            <p className="text-sm text-gray-500">Property</p>
            <div>
              <p className="text-sm font-medium text-gray-900 truncate">
                {reservation.property && reservation.property.name ? reservation.property.name : 'Unknown Property'}
              </p>
              {reservation.property && reservation.property.address && (
                <p className="text-xs text-gray-500 truncate mt-0.5">
                  {reservation.property.address}
                </p>
              )}
            </div>
          </div>
          {reservation.platform && (
            <div className="min-w-0">
              <p className="text-sm text-gray-500">Platform</p>
              <p className="text-sm font-medium text-gray-900 truncate capitalize">
                {reservation.platform}
              </p>
            </div>
          )}
        </div>
        
        {reservation.phone_partial && (
          <div className="mb-4 min-w-0">
            <p className="text-sm text-gray-500">Contact</p>
            <p className="text-sm font-medium text-gray-900 truncate">
              {reservation.phone_partial}
            </p>
          </div>
        )}
        
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <div className="text-xs text-gray-500 truncate min-w-0 flex-1">
            Status: {reservation.status || 'confirmed'}
          </div>
          <button className="text-sm text-blue-600 hover:text-blue-500 font-medium flex-shrink-0 ml-2">
            View Details
          </button>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading reservations...</p>
      </div>
    )
  }

  const views = [
    { id: 'all', name: 'All Reservations', count: reservations.length },
    { id: 'upcoming', name: 'Upcoming', count: upcomingReservations.length },
    { id: 'current', name: 'Current', count: currentReservations.length }
  ]

  const getCurrentReservations = () => {
    switch (activeView) {
      case 'upcoming':
        return upcomingReservations
      case 'current':
        return currentReservations
      default:
        return reservations
    }
  }

  const currentReservationList = getCurrentReservations()

  return (
    <div className="space-y-6">
      {/* View Toggle */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-gray-900">Reservations</h2>
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
          {views.map((view) => (
            <button
              key={view.id}
              onClick={() => setActiveView(view.id)}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                activeView === view.id
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {view.name} ({view.count})
            </button>
          ))}
        </div>
      </div>

      {/* Reservations Grid */}
      {currentReservationList.length === 0 ? (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a4 4 0 118 0v4m-4 12V11m0 0l-3 3m3-3l3 3" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No reservations found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {activeView === 'all' 
              ? 'No reservations have been synced yet.'
              : `No ${activeView} reservations at this time.`
            }
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {currentReservationList.map((reservation) => (
            <ReservationCard key={reservation.id} reservation={reservation} />
          ))}
        </div>
      )}
    </div>
  )
} 