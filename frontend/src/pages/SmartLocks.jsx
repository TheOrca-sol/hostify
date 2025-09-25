import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { toast } from '../components/Toaster'
import { Lock, Home, ArrowLeft, Plus, Smartphone, RefreshCw } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function SmartLocks() {
  const navigate = useNavigate()
  const [properties, setProperties] = useState([])
  const [loading, setLoading] = useState(true)
  const [unassignedLocks, setUnassignedLocks] = useState([])
  const [showUnassigned, setShowUnassigned] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [showConnectForm, setShowConnectForm] = useState(false)
  const [ttlockCredentials, setTtlockCredentials] = useState({ username: '', password: '' })
  const [connecting, setConnecting] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [disconnecting, setDisconnecting] = useState(false)

  useEffect(() => {
    loadProperties()
    loadConnectionStatus()
  }, [])

  const loadProperties = async () => {
    try {
      setLoading(true)
      const result = await api.getProperties()
      if (result.success) {
        setProperties(result.properties)
        // Auto-select first property if only one exists
        if (result.properties.length === 1) {
          setSelectedProperty(result.properties[0])
        }
      } else {
        toast.error('Failed to load properties')
      }
    } catch (error) {
      console.error('Error loading properties:', error)
      toast.error('Failed to load properties')
    } finally {
      setLoading(false)
    }
  }

  const loadConnectionStatus = async () => {
    try {
      const statusResult = await api.getTTLockConnectionStatus()
      if (statusResult.success) {
        setIsConnected(statusResult.is_connected)

        // Load unassigned locks if connected
        if (statusResult.is_connected && statusResult.unassigned_locks_count > 0) {
          const unassignedResult = await api.getUnassignedSmartLocks()
          if (unassignedResult.success) {
            setUnassignedLocks(unassignedResult.unassigned_locks || [])
            setShowUnassigned(true)
          }
        } else {
          setUnassignedLocks([])
          setShowUnassigned(false)
        }
      } else {
        console.error('Failed to load connection status:', statusResult.error)
        toast.error('Failed to load TTLock connection status')
      }
    } catch (error) {
      console.error('Error loading connection status:', error)
      toast.error('Failed to load TTLock connection status')
    }
  }

  const connectTTLockAccount = async () => {
    try {
      setConnecting(true)
      const result = await api.connectTTLockAccount(ttlockCredentials)

      if (result.success) {
        const message = result.locks_count > 0
          ? `TTLock account connected! Found ${result.locks_count} locks (unassigned)`
          : 'TTLock account connected! No locks found'
        toast.success(message)
        setIsConnected(true)
        setShowConnectForm(false)
        setTtlockCredentials({ username: '', password: '' })

        // Refresh connection status and unassigned locks
        await loadConnectionStatus()
      } else {
        toast.error(result.error || 'Failed to connect TTLock account')
      }
    } catch (error) {
      console.error('Error connecting TTLock account:', error)
      toast.error('Failed to connect TTLock account')
    } finally {
      setConnecting(false)
    }
  }

  const assignLockToProperty = async (lockId, propertyId) => {
    try {
      const result = await api.assignSmartLockToProperty(lockId, propertyId)
      if (result.success) {
        toast.success(result.message)
        // Refresh connection status and unassigned locks
        await loadConnectionStatus()
      } else {
        toast.error(result.error || 'Failed to assign lock to property')
      }
    } catch (error) {
      console.error('Error assigning lock:', error)
      toast.error('Failed to assign lock to property')
    }
  }

  const syncTTLockAccount = async () => {
    try {
      setSyncing(true)
      const result = await api.syncTTLockAccount()

      if (result.success) {
        toast.success(result.message)
        // Refresh connection status and unassigned locks
        await loadConnectionStatus()
      } else {
        toast.error(result.error || 'Failed to sync TTLock account')
      }
    } catch (error) {
      console.error('Error syncing TTLock account:', error)
      toast.error('Failed to sync TTLock account')
    } finally {
      setSyncing(false)
    }
  }

  const disconnectTTLockAccount = async () => {
    try {
      setDisconnecting(true)
      const result = await api.disconnectTTLockAccount()

      if (result.success) {
        toast.success('TTLock account disconnected and all locks deleted')
        setIsConnected(false)
        setUnassignedLocks([])
        setShowUnassigned(false)
        setTtlockCredentials({ username: '', password: '' })

        // Refresh connection status
        await loadConnectionStatus()
      } else {
        toast.error(result.error || 'Failed to disconnect TTLock account')
      }
    } catch (error) {
      console.error('Error disconnecting TTLock account:', error)
      toast.error('Failed to disconnect TTLock account')
    } finally {
      setDisconnecting(false)
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

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                  <Lock className="w-8 h-8 mr-3 text-blue-600" />
                  Smart Lock Management
                </h1>
                <p className="mt-1 text-gray-600">
                  Manage TTLock smart locks and generate access codes for guests
                </p>
              </div>
            </div>
          </div>
        </div>

        {properties.length === 0 ? (
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <Home className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Properties Found</h3>
            <p className="text-gray-600 mb-6">
              You need to create a property first before you can manage smart locks.
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
            >
              Go to Dashboard
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Global TTLock Connection Section */}
            {!isConnected && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-medium text-blue-900 mb-2 flex items-center">
                      <Lock className="w-5 h-5 mr-2" />
                      Connect TTLock Account
                    </h3>
                    <p className="text-blue-800 text-sm">
                      Connect your TTLock account to manage smart locks across all properties
                    </p>
                  </div>
                  {!showConnectForm && (
                    <button
                      onClick={() => setShowConnectForm(true)}
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Connect TTLock
                    </button>
                  )}
                </div>

                {/* TTLock Connection Form */}
                {showConnectForm && (
                  <div className="border-t border-blue-200 pt-4">
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-blue-900 mb-1">
                          TTLock Username (Phone/Email)
                        </label>
                        <input
                          type="text"
                          value={ttlockCredentials.username}
                          onChange={(e) => setTtlockCredentials({
                            ...ttlockCredentials,
                            username: e.target.value
                          })}
                          placeholder="e.g., +212663401973 or email@example.com"
                          className="w-full px-3 py-2 border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-blue-900 mb-1">
                          TTLock Password
                        </label>
                        <input
                          type="password"
                          value={ttlockCredentials.password}
                          onChange={(e) => setTtlockCredentials({
                            ...ttlockCredentials,
                            password: e.target.value
                          })}
                          placeholder="Your TTLock app password"
                          className="w-full px-3 py-2 border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>

                      <div className="flex space-x-3">
                        <button
                          onClick={connectTTLockAccount}
                          disabled={connecting || !ttlockCredentials.username || !ttlockCredentials.password}
                          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 flex items-center"
                        >
                          {connecting ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                              Connecting...
                            </>
                          ) : (
                            <>
                              <Lock className="w-4 h-4 mr-2" />
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
              </div>
            )}

            {/* Unassigned Locks Section */}
            {showUnassigned && unassignedLocks.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-6">
                <h3 className="text-lg font-medium text-amber-900 mb-4 flex items-center">
                  <Lock className="w-5 h-5 mr-2" />
                  Unassigned Smart Locks ({unassignedLocks.length})
                </h3>
                <p className="text-amber-800 mb-4 text-sm">
                  These locks are connected but not assigned to any property. Select a property below to assign them.
                </p>

                <div className="space-y-3">
                  {unassignedLocks.map((lock) => (
                    <div key={lock.id} className="bg-white border border-amber-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="bg-amber-100 p-2 rounded-lg">
                            <Lock className="w-5 h-5 text-amber-600" />
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900">{lock.lock_name}</h4>
                            <p className="text-sm text-gray-600">TTLock ID: {lock.ttlock_id}</p>
                            <p className="text-sm text-gray-600">MAC: {lock.lock_mac}</p>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2">
                          <select
                            onChange={(e) => {
                              if (e.target.value) {
                                assignLockToProperty(lock.id, e.target.value)
                              }
                            }}
                            className="text-sm border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            defaultValue=""
                          >
                            <option value="">Assign to Property</option>
                            {properties.map((property) => (
                              <option key={property.id} value={property.id}>
                                {property.name}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Properties Grid */}
            {properties.length > 0 && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">
                      Property Smart Locks
                    </h3>
                    <p className="text-gray-600 text-sm">
                      Manage smart locks for each of your properties
                    </p>
                  </div>

                  {/* Action Buttons */}
                  {isConnected && (
                    <div className="flex space-x-3">
                      <button
                        onClick={syncTTLockAccount}
                        disabled={syncing}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 flex items-center text-sm"
                      >
                        <RefreshCw className={`w-4 h-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
                        {syncing ? 'Syncing...' : 'Sync Locks'}
                      </button>

                      <button
                        onClick={disconnectTTLockAccount}
                        disabled={disconnecting}
                        className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:bg-gray-400 flex items-center text-sm"
                      >
                        {disconnecting ? 'Disconnecting...' : 'Disconnect Account'}
                      </button>
                    </div>
                  )}
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {properties.map((property) => (
                    <div
                      key={property.id}
                      onClick={() => navigate(`/properties/${property.id}/locks`)}
                      className="border border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-colors group"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <Home className="w-5 h-5 text-gray-400 group-hover:text-blue-500" />
                          <div>
                            <h4 className="font-medium text-gray-900 group-hover:text-blue-700">
                              {property.name}
                            </h4>
                            {property.address && (
                              <p className="text-sm text-gray-600">{property.address}</p>
                            )}
                          </div>
                        </div>
                        <Lock className="w-4 h-4 text-gray-400 group-hover:text-blue-500" />
                      </div>
                      <div className="text-sm text-gray-500 group-hover:text-blue-600">
                        Click to manage smart locks →
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Test Instructions */}
            {isConnected && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h4 className="text-lg font-medium text-blue-900 mb-3">
                  🧪 Testing TTLock Integration
                </h4>
                <div className="space-y-2 text-blue-800">
                  <p>1. ✅ TTLock account connected successfully</p>
                  <p>2. Click on property cards above to manage individual property locks</p>
                  <p>3. Use "Test Code" button to generate random passcodes</p>
                  <p>4. Use "Unassign" button to move locks between properties</p>
                  <p>5. Check your Flask logs to see the API calls in action</p>
                </div>

                <div className="mt-4 p-3 bg-blue-100 rounded">
                  <p className="text-sm text-blue-700">
                    <strong>Note:</strong> Make sure your backend server is running with ngrok tunnel active
                    for webhook functionality.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}