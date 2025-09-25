import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { toast } from '../components/Toaster'
import { Lock, Key, Clock, Copy, Send, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react'

export default function ReservationPasscodeManager({ reservation }) {
  const [passcodeData, setPasscodeData] = useState(null)
  const [propertySettings, setPropertySettings] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [manualPasscode, setManualPasscode] = useState('')
  const [updating, setUpdating] = useState(false)
  const [sendingNotification, setSendingNotification] = useState(false)

  useEffect(() => {
    if (reservation) {
      loadData()
    }
  }, [reservation])

  const loadData = async () => {
    try {
      setLoading(true)

      // Load both passcode data and property settings
      const [passcodeResult, settingsResult] = await Promise.all([
        api.getReservationPasscode(reservation.id),
        api.getPropertySmartLockSettings(reservation.property_id)
      ])

      if (passcodeResult.success && passcodeResult.passcode_data) {
        setPasscodeData(passcodeResult.passcode_data)
      }

      if (settingsResult.success) {
        setPropertySettings({
          smart_lock_type: settingsResult.smart_lock_type || 'traditional',
          smart_lock_instructions: settingsResult.smart_lock_instructions || '',
          smart_lock_settings: settingsResult.smart_lock_settings || {}
        })
      }
    } catch (error) {
      console.error('Error loading passcode data:', error)
    } finally {
      setLoading(false)
    }
  }

  const generatePasscode = async () => {
    try {
      setGenerating(true)
      const result = await api.generateReservationPasscode(reservation.id)

      if (result.success) {
        toast.success('Passcode generated successfully!')
        await loadData() // Reload to get updated data
      } else {
        toast.error(result.error || 'Failed to generate passcode')
      }
    } catch (error) {
      console.error('Error generating passcode:', error)
      toast.error('Failed to generate passcode')
    } finally {
      setGenerating(false)
    }
  }

  const updateManualPasscode = async () => {
    if (!manualPasscode.trim()) {
      toast.error('Please enter a passcode')
      return
    }

    try {
      setUpdating(true)
      const result = await api.updateManualPasscode(passcodeData.id, manualPasscode.trim())

      if (result.success) {
        toast.success('Manual passcode updated successfully!')
        setManualPasscode('')
        await loadData()
      } else {
        toast.error(result.error || 'Failed to update passcode')
      }
    } catch (error) {
      console.error('Error updating manual passcode:', error)
      toast.error('Failed to update passcode')
    } finally {
      setUpdating(false)
    }
  }

  const resendNotification = async () => {
    try {
      setSendingNotification(true)
      const result = await api.resendPasscodeNotification(passcodeData.id)

      if (result.success) {
        toast.success('Notification sent successfully!')
      } else {
        toast.error(result.error || 'Failed to send notification')
      }
    } catch (error) {
      console.error('Error sending notification:', error)
      toast.error('Failed to send notification')
    } finally {
      setSendingNotification(false)
    }
  }

  const copyPasscode = (passcode) => {
    navigator.clipboard.writeText(passcode)
    toast.success('Passcode copied to clipboard!')
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

  const getStatusColor = (status) => {
    const colors = {
      pending: 'text-yellow-600 bg-yellow-100',
      active: 'text-green-600 bg-green-100',
      expired: 'text-gray-600 bg-gray-100',
      revoked: 'text-red-600 bg-red-100'
    }
    return colors[status] || colors.pending
  }

  const getSmartLockTypeInfo = (type) => {
    const info = {
      ttlock: { label: 'TTLock Smart Lock', icon: '🔐', color: 'text-blue-600' },
      manual: { label: 'Manual Smart Lock', icon: '👤', color: 'text-orange-600' },
      traditional: { label: 'Traditional Access', icon: '🔑', color: 'text-gray-600' }
    }
    return info[type] || info.traditional
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
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="h-10 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (!propertySettings || propertySettings.smart_lock_type === 'traditional') {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center space-x-3 mb-4">
          <Key className="w-6 h-6 text-gray-600" />
          <h3 className="text-lg font-medium text-gray-900">Property Access</h3>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-lg">
              🔑
            </div>
            <div>
              <h4 className="font-medium text-gray-900">Traditional Access</h4>
              <p className="text-sm text-gray-600">This property uses traditional access methods (keys, lockbox, etc.)</p>
            </div>
          </div>
          {propertySettings?.smart_lock_instructions && (
            <div className="mt-3 p-3 bg-white border border-gray-200 rounded">
              <p className="text-sm text-gray-700">{propertySettings.smart_lock_instructions}</p>
            </div>
          )}
        </div>
      </div>
    )
  }

  const lockInfo = getSmartLockTypeInfo(propertySettings.smart_lock_type)

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Lock className="w-6 h-6 text-blue-600" />
            <div>
              <h3 className="text-lg font-medium text-gray-900">Smart Lock Access</h3>
              <p className="text-sm text-gray-600">Manage passcode for this reservation</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${lockInfo.color} bg-opacity-10`}>
              {lockInfo.icon} {lockInfo.label}
            </span>
          </div>
        </div>
      </div>

      <div className="p-6">
        {!passcodeData ? (
          // No passcode generated yet
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-blue-900">Passcode Not Generated</h4>
                  <p className="text-sm text-blue-800 mt-1">
                    {propertySettings.smart_lock_type === 'ttlock'
                      ? 'TTLock passcode will be generated automatically 3 hours before check-in, or you can generate it now manually.'
                      : 'Generate a manual passcode for this reservation.'
                    }
                  </p>
                </div>
              </div>
            </div>

            <button
              onClick={generatePasscode}
              disabled={generating}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 flex items-center"
            >
              {generating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Generating...
                </>
              ) : (
                <>
                  <Key className="w-4 h-4 mr-2" />
                  Generate Passcode
                </>
              )}
            </button>
          </div>
        ) : (
          // Passcode exists
          <div className="space-y-6">
            {/* Passcode Status */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-gray-900">Passcode Status</h4>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(passcodeData.status)}`}>
                  {passcodeData.status.charAt(0).toUpperCase() + passcodeData.status.slice(1)}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">Valid From</label>
                  <p className="text-sm text-gray-900 mt-1">
                    {formatDate(passcodeData.valid_from)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Valid Until</label>
                  <p className="text-sm text-gray-900 mt-1">
                    {formatDate(passcodeData.valid_until)}
                  </p>
                </div>
              </div>
            </div>

            {/* Passcode Display/Input */}
            {passcodeData.passcode ? (
              // Passcode is available
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-green-900 flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Passcode Ready
                  </h4>
                  <button
                    onClick={resendNotification}
                    disabled={sendingNotification}
                    className="text-green-700 hover:text-green-800 text-sm flex items-center"
                  >
                    {sendingNotification ? (
                      <RefreshCw className="w-4 h-4 mr-1 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4 mr-1" />
                    )}
                    Resend SMS
                  </button>
                </div>

                <div className="bg-white border border-green-300 rounded p-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-gray-700">Access Passcode</label>
                      <p className="text-2xl font-mono font-bold text-gray-900 mt-1">
                        {passcodeData.passcode}
                      </p>
                    </div>
                    <button
                      onClick={() => copyPasscode(passcodeData.passcode)}
                      className="bg-green-100 text-green-700 px-3 py-2 rounded hover:bg-green-200 flex items-center"
                    >
                      <Copy className="w-4 h-4 mr-2" />
                      Copy
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              // Manual passcode entry needed
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <div className="flex items-center space-x-3 mb-4">
                  <AlertCircle className="w-5 h-5 text-orange-600" />
                  <h4 className="font-medium text-orange-900">Manual Passcode Required</h4>
                </div>

                <p className="text-sm text-orange-800 mb-4">
                  Please set the passcode for your smart lock and enter it below. The guest will be notified automatically.
                </p>

                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Enter Passcode
                    </label>
                    <div className="flex space-x-2">
                      <input
                        type="text"
                        value={manualPasscode}
                        onChange={(e) => setManualPasscode(e.target.value)}
                        placeholder="e.g., 123456"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 font-mono"
                      />
                      <button
                        onClick={updateManualPasscode}
                        disabled={updating || !manualPasscode.trim()}
                        className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 disabled:bg-gray-400 flex items-center"
                      >
                        {updating ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Saving...
                          </>
                        ) : (
                          <>
                            <Key className="w-4 h-4 mr-2" />
                            Set Passcode
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Instructions */}
            {propertySettings.smart_lock_instructions && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Guest Instructions</h4>
                <p className="text-sm text-gray-700">{propertySettings.smart_lock_instructions}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}