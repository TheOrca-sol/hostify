import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { toast } from '../components/Toaster'
import { FileText, Send, RefreshCw, Edit2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import GuestEditForm from './GuestEditForm'

export default function GuestList() {
  const [guests, setGuests] = useState([])
  const [loading, setLoading] = useState(true)
  const [sendingLink, setSendingLink] = useState(null)
  const [generatingContract, setGeneratingContract] = useState(null)
  const [editingGuest, setEditingGuest] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadGuests()
  }, [])

  const loadGuests = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.getGuests()
      if (response.success) {
        setGuests(response.guests || [])
      } else {
        setError(response.error || 'Failed to load guests')
        toast.error(response.error || 'Failed to load guests')
      }
    } catch (err) {
      console.error('Error loading guests:', err)
      setError('Failed to load guests')
      toast.error('Failed to load guests')
    } finally {
      setLoading(false)
    }
  }

  const handleSendVerificationLink = async (guest) => {
    try {
      setSendingLink(guest.id)
      const response = await api.createVerificationLinkForReservation(guest.reservation_id, {
        guest_id: guest.id,
        guest_name: guest.full_name,
        guest_email: guest.email
      })
      
      if (response.success) {
        toast.success('Verification link sent successfully')
        loadGuests() // Refresh list to update status
      } else {
        toast.error(response.error || 'Failed to send verification link')
      }
    } catch (err) {
      console.error('Error sending verification link:', err)
      toast.error('Failed to send verification link')
    } finally {
      setSendingLink(null)
    }
  }

  const handleGenerateContract = async (guest) => {
    try {
      setGeneratingContract(guest.id)
      const response = await api.generateContract(guest.reservation_id, guest.id)
      if (response.success) {
        toast.success('Contract generated successfully')
        loadGuests() // Refresh list to update contract status
      } else {
        toast.error(response.error || 'Failed to generate contract')
      }
    } catch (err) {
      console.error('Error generating contract:', err)
      toast.error('Failed to generate contract')
    } finally {
      setGeneratingContract(null)
    }
  }

  const handleGuestUpdated = (updatedGuest) => {
    setGuests(prevGuests => 
      prevGuests.map(guest => 
        guest.id === updatedGuest.id ? updatedGuest : guest
      )
    )
    toast.success('Guest information updated successfully')
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Not available'
    return new Date(dateString).toLocaleDateString()
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-2 text-sm text-gray-500">Loading guests...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="bg-red-100 p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
          <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900">Error Loading Guests</h3>
        <p className="mt-2 text-sm text-gray-500">{error}</p>
        <button
          onClick={loadGuests}
          className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Try Again
        </button>
      </div>
    )
  }

  if (guests.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="bg-gray-100 p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900">No Guests Found</h3>
        <p className="mt-2 text-sm text-gray-500">
          Guests will appear here after they complete the verification process.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-gray-900">Guest Management</h2>
        <div className="flex items-center space-x-4">
          <Link
            to="/contract-templates"
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <FileText className="-ml-0.5 mr-2 h-4 w-4" /> Manage Templates
          </Link>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            Total: {guests.length}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {guests.map((guest) => (
          <div key={guest.id} className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                    <svg className="h-6 w-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900 truncate max-w-[150px]">
                    {guest.full_name || 'Guest'}
                  </h3>
                  <p className="text-sm text-gray-500 truncate max-w-[150px]">
                    {guest.nationality || 'Nationality pending'}
                  </p>
                </div>
              </div>
              <div className="flex flex-col items-end space-y-2">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  guest.verification_status === 'verified'
                    ? 'bg-green-100 text-green-800'
                    : guest.verification_status === 'pending'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {guest.verification_status}
                </span>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setEditingGuest(guest)}
                    className="inline-flex items-center p-1 border border-transparent text-gray-600 hover:text-blue-600 focus:outline-none"
                  >
                    <Edit2 className="h-4 w-4" />
                  </button>
                  {guest.verification_status !== 'verified' && (
                    <button
                      onClick={() => handleSendVerificationLink(guest)}
                      disabled={sendingLink === guest.id}
                      className="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                    >
                      {sendingLink === guest.id ? (
                        <>
                          <RefreshCw className="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-700" />
                          Sending...
                        </>
                      ) : (
                        <>
                          <Send className="-ml-1 mr-2 h-4 w-4" />
                          Send Verification
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Property Information */}
            {guest.property && (
              <div className="mt-4 border-t pt-4">
                <div className="flex items-start space-x-2">
                  <svg className="h-5 w-5 text-gray-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">{guest.property.name}</h4>
                    <p className="text-sm text-gray-500">{guest.property.address}</p>
                    <div className="mt-1 flex items-center text-sm text-gray-500">
                      <svg className="h-4 w-4 text-gray-400 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      {guest.check_in && guest.check_out && (
                        <span>
                          {new Date(guest.check_in).toLocaleDateString()} - {new Date(guest.check_out).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="border-t border-gray-200 pt-4">
              <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
                <div>
                  <dt className="text-sm font-medium text-gray-500">ID/Passport</dt>
                  <dd className="mt-1 text-sm text-gray-900 truncate">{guest.cin_or_passport || 'Pending'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Birthdate</dt>
                  <dd className="mt-1 text-sm text-gray-900">{formatDate(guest.birthdate)}</dd>
                </div>
                {guest.phone && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Phone</dt>
                    <dd className="mt-1 text-sm text-gray-900 truncate">{guest.phone}</dd>
                  </div>
                )}
                {guest.email && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Email</dt>
                    <dd className="mt-1 text-sm text-gray-900 truncate">{guest.email}</dd>
                  </div>
                )}
                {guest.verified_at && (
                  <div className="col-span-2">
                    <dt className="text-sm font-medium text-gray-500">Verified At</dt>
                    <dd className="mt-1 text-sm text-gray-900">{formatDate(guest.verified_at)}</dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Contract Section */}
            <div className="border-t border-gray-200 mt-4 pt-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-700">Contract Status</h4>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  guest.contract_status === 'signed'
                    ? 'bg-green-100 text-green-800'
                    : guest.contract_status === 'pending'
                    ? 'bg-yellow-100 text-yellow-800'
                    : guest.contract_status === 'generated'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {guest.contract_status || 'Not Generated'}
                </span>
              </div>

              {guest.verification_status === 'verified' && !guest.contract_status && (
                <button
                  onClick={() => handleGenerateContract(guest)}
                  disabled={generatingContract === guest.id}
                  className="w-full mt-2 inline-flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {generatingContract === guest.id ? (
                    <>
                      <RefreshCw className="animate-spin -ml-1 mr-2 h-4 w-4" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <FileText className="-ml-1 mr-2 h-4 w-4" />
                      Generate Contract
                    </>
                  )}
                </button>
              )}

              {guest.contract_status === 'generated' && (
                <Link
                  to={`/contracts/${guest.contract_id}/sign`}
                  className="w-full mt-2 inline-flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                  <FileText className="-ml-1 mr-2 h-4 w-4" />
                  Sign Contract
                </Link>
              )}

              {guest.contract_status === 'signed' && (
                <Link
                  to={`/contracts/${guest.contract_id}`}
                  className="w-full mt-2 inline-flex items-center justify-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <FileText className="-ml-1 mr-2 h-4 w-4" />
                  View Contract
                </Link>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Edit Guest Modal */}
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