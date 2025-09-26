import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { toast } from '../components/Toaster'
import { Lock, Plus, Key, Smartphone, Wifi, WifiOff, Battery, BatteryLow, Settings, Trash2 } from 'lucide-react'

export default function SmartLockManagement({ property }) {
  const [locks, setLocks] = useState([])
  const [loading, setLoading] = useState(true)
  const [showConnectForm, setShowConnectForm] = useState(false)
  const [smartLockCredentials, setSmartLockCredentials] = useState({ username: '', password: '' })
  const [connecting, setConnecting] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [disconnecting, setDisconnecting] = useState(false)

  useEffect(() => {
    fetchLocks()
  }, [property.id])

  const fetchLocks = async () => {
    try {
      setLoading(true)

      // Get property-specific locks
      const result = await api.getPropertySmartLocks(property.id)
      if (result.success) {
        setLocks(result.smart_locks || [])
      }

      // Get proper connection status using the dedicated API
      const statusResult = await api.getTTLockConnectionStatus()
      if (statusResult.success) {
        setIsConnected(statusResult.is_connected)
      }

    } catch (error) {
      console.error('Error fetching locks:', error)
      toast.error('Failed to load smart locks')
    } finally {
      setLoading(false)
    }
  }

  const connectSmartLockAccount = async () => {
    try {
      setConnecting(true)
      const result = await api.connectTTLockAccount(smartLockCredentials)

      if (result.success) {
        const message = result.locks_count > 0
          ? `Smart lock account connected! Found ${result.locks_count} locks (unassigned)`
          : 'Smart lock account connected! No locks found'
        toast.success(message)
        setIsConnected(true)
        setShowConnectForm(false)
        setSmartLockCredentials({ username: '', password: '' })

        // Refresh the locks list (this will update connection status)
        await fetchLocks()

        // Notify parent component about new unassigned locks
        if (result.locks_count > 0) {
          setTimeout(() => {
            toast.info('Go to the main Smart Locks page to assign your locks to properties')
          }, 2000)
        }
      } else {
        toast.error(result.error || 'Failed to connect smart lock account')
      }
    } catch (error) {
      console.error('Error connecting smart lock account:', error)
      toast.error('Failed to connect smart lock account')
    } finally {
      setConnecting(false)
    }
  }

  const generateTestPasscode = async (lockId) => {
    try {
      const result = await api.generateTestPasscode(lockId)

      if (result.success) {
        toast.success(`Test passcode: ${result.passcode} (valid until ${new Date(result.valid_until).toLocaleTimeString()})`)
      } else {
        toast.error(result.error || 'Failed to generate test passcode')
      }
    } catch (error) {
      console.error('Error generating test passcode:', error)
      toast.error('Failed to generate test passcode')
    }
  }

  const disconnectSmartLockAccount = async () => {
    try {
      setDisconnecting(true)
      const result = await api.disconnectTTLockAccount()

      if (result.success) {
        toast.success('Smart lock account disconnected and all locks deleted')
        setIsConnected(false)
        setLocks([])
        setSmartLockCredentials({ username: '', password: '' })

        // Refresh the connection status to reflect changes across the app
        await fetchLocks()
      } else {
        toast.error(result.error || 'Failed to disconnect smart lock account')
      }
    } catch (error) {
      console.error('Error disconnecting smart lock account:', error)
      toast.error('Failed to disconnect smart lock account')
    } finally {
      setDisconnecting(false)
    }
  }

  const unassignLock = async (lockId) => {
    try {
      const result = await api.unassignSmartLockFromProperty(lockId)

      if (result.success) {
        toast.success(result.message)
        // Refresh the locks list to remove the unassigned lock
        await fetchLocks()
      } else {
        toast.error(result.error || 'Failed to unassign lock')
      }
    } catch (error) {
      console.error('Error unassigning lock:', error)
      toast.error('Failed to unassign lock')
    }
  }

  const getBatteryIcon = (level) => {
    if (level === null || level === undefined) return <Battery className="w-4 h-4 text-gray-400" />
    if (level < 20) return <BatteryLow className="w-4 h-4 text-red-500" />
    return <Battery className="w-4 h-4 text-green-500" />
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100'
      case 'offline': return 'text-red-600 bg-red-100'
      case 'inactive': return 'text-gray-600 bg-gray-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <Lock className="w-5 h-5 mr-2" />
          Smart Lock Management
        </h3>
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-medium text-gray-900 flex items-center">
          <Lock className="w-5 h-5 mr-2" />
          Smart Lock Management
        </h3>

        {!isConnected && locks.length === 0 && (
          <button
            onClick={() => setShowConnectForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center"
          >
            <Plus className="w-4 h-4 mr-2" />
            Connect Smart Lock
          </button>
        )}
      </div>

      {/* Smart Lock Connection Form */}
      {showConnectForm && (
        <div className="mb-6 p-4 border border-gray-200 rounded-lg bg-gray-50">
          <h4 className="text-md font-medium text-gray-900 mb-4">
            Connect Your Smart Lock Account
          </h4>
          <p className="text-sm text-gray-600 mb-4">
            Enter your smart lock app credentials (phone number or email and password)
          </p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Smart Lock Username (Phone/Email)
              </label>
              <input
                type="text"
                value={smartLockCredentials.username}
                onChange={(e) => setSmartLockCredentials({
                  ...smartLockCredentials,
                  username: e.target.value
                })}
                placeholder="e.g., +212663401973 or email@example.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Smart Lock Password
              </label>
              <input
                type="password"
                value={smartLockCredentials.password}
                onChange={(e) => setSmartLockCredentials({
                  ...smartLockCredentials,
                  password: e.target.value
                })}
                placeholder="Your smart lock app password"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="flex space-x-3">
              <button
                onClick={connectSmartLockAccount}
                disabled={connecting || !smartLockCredentials.username || !smartLockCredentials.password}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 flex items-center"
              >
                {connecting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Connecting...
                  </>
                ) : (
                  <>
                    <Smartphone className="w-4 h-4 mr-2" />
                    Connect Account
                  </>
                )}
              </button>

              <button
                onClick={() => setShowConnectForm(false)}
                className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Smart Locks List */}
      {locks.length === 0 ? (
        <div className="text-center py-8">
          <Lock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h4 className="text-lg font-medium text-gray-900 mb-2">
            {isConnected ? 'No Locks Assigned to This Property' : 'No Smart Locks Connected'}
          </h4>
          <p className="text-gray-600 mb-4">
            {isConnected
              ? 'You have smart locks connected but no locks are assigned to this property. Go to the main Smart Locks page to assign locks.'
              : 'Connect your smart lock account to manage smart locks.'
            }
          </p>
          {!showConnectForm && !isConnected && (
            <button
              onClick={() => setShowConnectForm(true)}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
            >
              Connect Smart Lock Account
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {locks.map((lock) => (
            <div key={lock.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="bg-blue-100 p-2 rounded-lg">
                    <Lock className="w-6 h-6 text-blue-600" />
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-900">{lock.lock_name}</h4>
                    <p className="text-sm text-gray-600">
                      Device ID: {lock.ttlock_id}
                    </p>
                    <p className="text-sm text-gray-600">
                      MAC: {lock.lock_mac}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  {/* Battery Level */}
                  <div className="flex items-center space-x-1">
                    {getBatteryIcon(lock.battery_level)}
                    <span className="text-sm text-gray-600">
                      {lock.battery_level ? `${lock.battery_level}%` : 'N/A'}
                    </span>
                  </div>

                  {/* Status */}
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(lock.status)}`}>
                    {lock.status}
                  </span>

                  {/* Actions */}
                  <div className="flex space-x-2">
                    <button
                      onClick={() => generateTestPasscode(lock.id)}
                      className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 flex items-center"
                    >
                      <Key className="w-3 h-3 mr-1" />
                      Test Code
                    </button>

                    <button
                      onClick={() => unassignLock(lock.id)}
                      className="bg-orange-600 text-white px-3 py-1 rounded text-sm hover:bg-orange-700 flex items-center"
                    >
                      <Trash2 className="w-3 h-3 mr-1" />
                      Unassign
                    </button>

                    <button className="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700 flex items-center">
                      <Settings className="w-3 h-3 mr-1" />
                      Settings
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Connection Status */}
      {isConnected && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center">
            <Wifi className="w-4 h-4 text-green-600 mr-2" />
            <span className="text-sm text-green-800">
              Smart lock account connected {locks.length === 0 ? '(assign locks from main page)' : ''}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}