import React, { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import { toast } from '../components/Toaster'
import { FileText, Send, RefreshCw, Edit2, Search, SlidersHorizontal, UserPlus } from 'lucide-react'
import GuestEditForm from './GuestEditForm'
import { useDebounce } from '../hooks/useDebounce'

export default function GuestList() {
  const [guests, setGuests] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // State for modals and actions
  const [sendingLink, setSendingLink] = useState(null)
  const [editingGuest, setEditingGuest] = useState(null)

  // Filtering and Pagination state
  const [properties, setProperties] = useState([])
  const [selectedProperty, setSelectedProperty] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  
  const debouncedSearchQuery = useDebounce(searchQuery, 500)

  const loadGuests = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = {
        page: currentPage,
        per_page: 9,
        search: debouncedSearchQuery,
        property_id: selectedProperty,
      }

      const response = await api.getGuests(params)
      if (response.success) {
        setGuests(response.guests || [])
        setTotalPages(response.pages || 1)
      } else {
        setError(response.error || 'Failed to load guests')
      }
    } catch (err) {
      setError('An unexpected error occurred.')
    } finally {
      setLoading(false)
    }
  }, [currentPage, debouncedSearchQuery, selectedProperty])

  useEffect(() => {
    loadGuests()
  }, [loadGuests])

  useEffect(() => {
    const loadProperties = async () => {
      const result = await api.getProperties()
      if (result.success) {
        setProperties(result.properties || [])
      }
    }
    loadProperties()
  }, [])

  const handleSendVerificationLink = async (guestId) => {
    setSendingLink(guestId)
    try {
      const response = await api.sendVerificationLink(guestId)
      if (response.success) {
        toast.success('Verification link sent successfully')
        loadGuests() // Refresh list
      } else {
        toast.error(response.error || 'Failed to send link')
      }
    } catch (err) {
      toast.error('Failed to send verification link')
    } finally {
      setSendingLink(null)
    }
  }

  const handleGuestUpdated = () => {
    loadGuests() // Refresh the entire list to ensure data consistency
    toast.success('Guest information updated successfully')
  }
  
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage)
    }
  }

  const getStatusInfo = (guest) => {
    switch (guest.verification_status) {
      case 'verified':
        return { label: 'Verified', color: 'bg-green-100 text-green-800' }
      case 'pending':
        return guest.verification_link_sent
          ? { label: 'Awaiting Verification', color: 'bg-yellow-100 text-yellow-800' }
          : { label: 'Ready to Send', color: 'bg-blue-100 text-blue-800' }
      default:
        return { label: guest.verification_status, color: 'bg-red-100 text-red-800' }
    }
  }

  const GuestCard = ({ guest }) => {
    const status = getStatusInfo(guest)
    return (
      <div className="bg-white shadow rounded-lg p-5 flex flex-col justify-between">
        <div>
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-3 min-w-0">
              <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                <UserPlus className="h-5 w-5 text-gray-500" />
              </div>
              <div className="min-w-0">
                <h3 className="text-md font-semibold text-gray-900 truncate">{guest.full_name || 'Guest'}</h3>
                <p className="text-xs text-gray-500 truncate">{guest.property?.name || 'Unknown Property'}</p>
              </div>
            </div>
            <span className={`px-2 py-1 text-xs font-medium rounded-full text-center ${status.color}`}>
              {status.label}
            </span>
          </div>
          <div className="space-y-2 text-sm text-gray-600">
            <p><strong>Reservation ID:</strong> {guest.reservation?.external_id || 'N/A'}</p>
            <p><strong>Phone:</strong> {guest.phone || guest.reservation?.phone_partial || 'Pending'}</p>
            <p><strong>Email:</strong> {guest.email || 'Pending'}</p>
            <p><strong>Check-in:</strong> {new Date(guest.check_in).toLocaleDateString()}</p>
          </div>
        </div>
        <div className="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between">
          <button onClick={() => setEditingGuest(guest)} className="text-sm font-medium text-blue-600 hover:text-blue-800">
            <Edit2 className="h-4 w-4 inline mr-1" /> Edit
          </button>
          {guest.verification_status === 'pending' && (
            <button
              onClick={() => handleSendVerificationLink(guest.id)}
              disabled={sendingLink === guest.id}
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 disabled:opacity-50"
            >
              {sendingLink === guest.id ? 'Sending...' : 'Send Link'}
            </button>
          )}
        </div>
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
              placeholder="Search by name, email, phone, or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg"
            />
          </div>
        </div>
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
      </div>

      {loading ? (
        <div className="text-center py-12">Loading guests...</div>
      ) : error ? (
        <div className="text-center py-12 text-red-500">{error}</div>
      ) : guests.length === 0 ? (
        <div className="text-center py-12">No guests found.</div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {guests.map((guest) => <GuestCard key={guest.id} guest={guest} />)}
          </div>
          <PaginationControls />
        </>
      )}

      {editingGuest && (
        <GuestEditForm
          guest={editingGuest}
          onClose={() => setEditingGuest(null)}
          onGuestUpdated={handleGuestUpdated}
        />
      )}
    </div>
  )
}