import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { toast } from '../components/Toaster'
import { Clock, Home, User, Key, Send, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react'

export default function PendingPasscodes() {
  const [pendingPasscodes, setPendingPasscodes] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [updatingPasscode, setUpdatingPasscode] = useState(null)
  const [passcodeInputs, setPasscodeInputs] = useState({})

  useEffect(() => {
    loadPendingPasscodes()
  }, [])

  const loadPendingPasscodes = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }

      const result = await api.getPendingManualPasscodes()

      if (result.success) {
        setPendingPasscodes(result.pending_passcodes || [])
        // Initialize passcode inputs for new items
        const inputs = {}
        result.pending_passcodes?.forEach(item => {
          if (!passcodeInputs[item.id]) {
            inputs[item.id] = ''
          }
        })
        setPasscodeInputs(prev => ({ ...prev, ...inputs }))
      } else {
        toast.error(result.error || 'Failed to load pending passcodes')
      }
    } catch (error) {
      console.error('Error loading pending passcodes:', error)
      toast.error('Failed to load pending passcodes')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const updatePasscodeInput = (passcodeId, value) => {
    setPasscodeInputs(prev => ({
      ...prev,
      [passcodeId]: value
    }))
  }

  const setManualPasscode = async (passcodeId) => {
    const passcode = passcodeInputs[passcodeId]?.trim()
    if (!passcode) {
      toast.error('Please enter a passcode')
      return
    }

    try {
      setUpdatingPasscode(passcodeId)
      const result = await api.updateManualPasscode(passcodeId, passcode)

      if (result.success) {
        toast.success('Passcode set successfully! Guest will be notified.')
        // Remove from pending list and clear input
        setPendingPasscodes(prev => prev.filter(item => item.id !== passcodeId))
        setPasscodeInputs(prev => {
          const newInputs = { ...prev }
          delete newInputs[passcodeId]
          return newInputs
        })
      } else {
        toast.error(result.error || 'Failed to set passcode')
      }
    } catch (error) {
      console.error('Error setting manual passcode:', error)
      toast.error('Failed to set passcode')
    } finally {
      setUpdatingPasscode(null)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  const getUrgencyColor = (checkInDate) => {
    if (!checkInDate) return 'text-gray-600 bg-gray-100'

    const checkIn = new Date(checkInDate)
    const now = new Date()
    const hoursUntil = (checkIn - now) / (1000 * 60 * 60)

    if (hoursUntil <= 6) return 'text-red-600 bg-red-100' // Very urgent
    if (hoursUntil <= 12) return 'text-orange-600 bg-orange-100' // Urgent
    if (hoursUntil <= 24) return 'text-yellow-600 bg-yellow-100' // Soon
    return 'text-blue-600 bg-blue-100' // Not urgent yet
  }

  const getUrgencyText = (checkInDate) => {
    if (!checkInDate) return 'Unknown'

    const checkIn = new Date(checkInDate)
    const now = new Date()
    const hoursUntil = (checkIn - now) / (1000 * 60 * 60)

    if (hoursUntil <= 0) return 'Overdue'
    if (hoursUntil <= 6) return 'Very Urgent'
    if (hoursUntil <= 12) return 'Urgent'
    if (hoursUntil <= 24) return 'Due Soon'
    return 'Scheduled'
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="animate-pulse">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-6 h-6 bg-gray-200 rounded"></div>
            <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          </div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  </div>
                  <div className="h-8 bg-gray-200 rounded w-20"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Clock className="w-6 h-6 text-orange-600" />
            <div>
              <h3 className="text-lg font-medium text-gray-900">Pending Manual Passcodes</h3>
              <p className="text-sm text-gray-600">
                {pendingPasscodes.length === 0
                  ? 'No passcodes pending manual entry'
                  : `${pendingPasscodes.length} reservation${pendingPasscodes.length === 1 ? '' : 's'} need${pendingPasscodes.length === 1 ? 's' : ''} passcode${pendingPasscodes.length === 1 ? '' : 's'}`
                }
              </p>
            </div>
          </div>
          <button
            onClick={() => loadPendingPasscodes(true)}
            disabled={refreshing}
            className="text-gray-600 hover:text-gray-900 p-2 rounded-lg hover:bg-gray-100"
          >
            <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="p-6">
        {pendingPasscodes.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <h4 className="text-lg font-medium text-gray-900 mb-2">All Caught Up!</h4>
            <p className="text-gray-600">
              No manual passcodes are pending. New requests will appear here automatically.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {pendingPasscodes.map((item) => (
              <div
                key={item.id}
                className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
              >
                <div className="flex items-start space-x-4">
                  {/* Urgency Indicator */}
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${getUrgencyColor(item.check_in)} whitespace-nowrap`}>
                    {getUrgencyText(item.check_in)}
                  </div>

                  {/* Reservation Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3 mb-2">
                      <Home className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <span className="font-medium text-gray-900 truncate">{item.property_name}</span>
                    </div>

                    <div className="flex items-center space-x-3 mb-2">
                      <User className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <span className="text-gray-700">{item.guest_name}</span>
                    </div>

                    <div className="text-sm text-gray-500">
                      Check-in: {formatDate(item.check_in)}
                    </div>
                  </div>

                  {/* Passcode Input */}
                  <div className="flex-shrink-0 w-64">
                    <div className="flex space-x-2">
                      <input
                        type="text"
                        value={passcodeInputs[item.id] || ''}
                        onChange={(e) => updatePasscodeInput(item.id, e.target.value)}
                        placeholder="Enter passcode"
                        className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 font-mono"
                        disabled={updatingPasscode === item.id}
                      />
                      <button
                        onClick={() => setManualPasscode(item.id)}
                        disabled={updatingPasscode === item.id || !passcodeInputs[item.id]?.trim()}
                        className="bg-orange-600 text-white px-3 py-2 rounded-lg hover:bg-orange-700 disabled:bg-gray-400 flex items-center text-sm"
                      >
                        {updatingPasscode === item.id ? (
                          <>
                            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                            Setting...
                          </>
                        ) : (
                          <>
                            <Key className="w-3 h-3 mr-1" />
                            Set
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Additional Info for Very Urgent Items */}
                {getUrgencyText(item.check_in) === 'Very Urgent' && (
                  <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-sm">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="w-4 h-4 text-red-600" />
                      <span className="text-red-800 font-medium">
                        Check-in is in less than 6 hours! Guest needs access code soon.
                      </span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}