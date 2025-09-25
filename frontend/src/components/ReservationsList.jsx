import React, { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'
import { Search, SlidersHorizontal, Lock } from 'lucide-react'
import { useDebounce } from '../hooks/useDebounce'

export default function ReservationsList() {
  const [reservations, setReservations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filtering and Pagination state
  const [properties, setProperties] = useState([])
  const [activeFilter, setActiveFilter] = useState('all')
  const [selectedProperty, setSelectedProperty] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalReservations, setTotalReservations] = useState(0)

  const debouncedSearchQuery = useDebounce(searchQuery, 500)

  const loadReservations = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = {
        page: currentPage,
        per_page: 9,
        search: debouncedSearchQuery,
        property_id: selectedProperty,
        filter_type: activeFilter === 'all' ? null : activeFilter,
      }

      const result = await api.getReservations(params)
      
      if (result.success) {
        setReservations(result.reservations || [])
        setTotalPages(result.pages || 1)
        setTotalReservations(result.total || 0)
      } else {
        setError(result.error || 'Failed to load reservations')
      }
    } catch (err) {
      console.error('Error loading reservations:', err)
      setError('An unexpected error occurred.')
    } finally {
      setLoading(false)
    }
  }, [currentPage, debouncedSearchQuery, selectedProperty, activeFilter])

  useEffect(() => {
    loadReservations()
  }, [loadReservations])

  useEffect(() => {
    const loadProperties = async () => {
      const result = await api.getProperties()
      if (result.success) {
        setProperties(result.properties || [])
      }
    }
    loadProperties()
  }, [])

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric'
    })
  }

  const getStatusPill = (reservation) => {
    const now = new Date()
    const checkIn = new Date(reservation.check_in)
    const checkOut = new Date(reservation.check_out)

    if (now >= checkIn && now <= checkOut) {
      return { label: 'Current', color: 'bg-green-100 text-green-800' }
    } else if (now < checkIn) {
      return { label: 'Upcoming', color: 'bg-blue-100 text-blue-800' }
    } else {
      return { label: 'Past', color: 'bg-gray-100 text-gray-800' }
    }
  }

  const ReservationCard = ({ reservation }) => {
    const status = getStatusPill(reservation)
    const [passcodeData, setPasscodeData] = useState(null)
    const [loadingPasscode, setLoadingPasscode] = useState(true)

    useEffect(() => {
      const loadPasscodeData = async () => {
        try {
          const result = await api.getReservationPasscode(reservation.id)
          if (result.success) {
            setPasscodeData(result.passcode_data)
          }
        } catch (error) {
          console.error('Error loading passcode data:', error)
        } finally {
          setLoadingPasscode(false)
        }
      }

      loadPasscodeData()
    }, [reservation.id])

    const getPasscodeStatus = () => {
      if (loadingPasscode) {
        return { text: '...', color: 'text-gray-400' }
      }

      if (!passcodeData) {
        return { text: 'No passcode', color: 'text-gray-500' }
      }

      if (passcodeData.passcode) {
        return {
          text: passcodeData.passcode,
          color: 'text-green-600',
          icon: <Lock className="w-3 h-3" />
        }
      }

      return { text: 'Pending', color: 'text-orange-600' }
    }

    const passcodeStatus = getPasscodeStatus()

    return (
      <div className="bg-white border border-gray-200 rounded-lg p-5 flex flex-col justify-between hover:shadow-lg transition-shadow duration-200">
        <div>
          <div className="flex items-start justify-between mb-3">
            <div className="min-w-0">
              <h3 className="text-md font-semibold text-gray-800 truncate">
                {reservation.guest_name_partial || 'Guest'}
              </h3>
              <p className="text-xs text-gray-500 truncate">
                {reservation.property?.name || 'Unknown Property'}
                {reservation.external_id && ` • ${reservation.external_id}`}
              </p>
            </div>
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${status.color}`}>
              {status.label}
            </span>
          </div>
          <div className="space-y-2 text-sm">
            <p><strong>Check-in:</strong> {formatDate(reservation.check_in)}</p>
            <p><strong>Check-out:</strong> {formatDate(reservation.check_out)}</p>
            {reservation.phone_partial && <p><strong>Phone:</strong> {reservation.phone_partial}</p>}
            <div className="flex items-center space-x-2 mt-2 pt-2 border-t border-gray-100">
              <span className="text-xs font-medium text-gray-600">Smart Lock:</span>
              <div className={`flex items-center space-x-1 ${passcodeStatus.color}`}>
                {passcodeStatus.icon}
                <span className="text-xs font-mono">
                  {passcodeStatus.text}
                </span>
              </div>
            </div>
          </div>
        </div>
        <Link
          to={`/reservations/${reservation.id}`}
          className="mt-4 w-full text-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 block"
        >
          View Details
        </Link>
      </div>
    )
  }

  const PaginationControls = () => (
    <div className="flex items-center justify-between mt-6">
      <button
        onClick={() => handlePageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
      >
        Previous
      </button>
      <span className="text-sm text-gray-700">
        Page {currentPage} of {totalPages}
      </span>
      <button
        onClick={() => handlePageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
      >
        Next
      </button>
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="w-full md:w-1/3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by name or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg"
            />
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="h-5 w-5 text-gray-500" />
            <select
              value={selectedProperty}
              onChange={(e) => setSelectedProperty(e.target.value)}
              className="border border-gray-300 rounded-lg py-2 px-3"
            >
              <option value="">All Properties</option>
              {properties.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
            <button onClick={() => setActiveFilter('all')} className={`px-3 py-1.5 text-sm font-medium rounded-md ${activeFilter === 'all' ? 'bg-white shadow' : ''}`}>All</button>
            <button onClick={() => setActiveFilter('upcoming')} className={`px-3 py-1.5 text-sm font-medium rounded-md ${activeFilter === 'upcoming' ? 'bg-white shadow' : ''}`}>Upcoming</button>
            <button onClick={() => setActiveFilter('current')} className={`px-3 py-1.5 text-sm font-medium rounded-md ${activeFilter === 'current' ? 'bg-white shadow' : ''}`}>Current</button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : error ? (
        <div className="text-center py-12 text-red-500">{error}</div>
      ) : reservations.length === 0 ? (
        <div className="text-center py-12">No reservations found.</div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {reservations.map((res) => <ReservationCard key={res.id} reservation={res} />)}
          </div>
          <PaginationControls />
        </>
      )}
    </div>
  )
}