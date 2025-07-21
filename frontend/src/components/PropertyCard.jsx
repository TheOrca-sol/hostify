import React, { useState } from 'react'
import { api } from '../services/api'
import { Link } from 'react-router-dom'
import { FileText, RefreshCw, Trash2, AlertTriangle, MessageSquare } from 'lucide-react'
import { toast } from '../components/Toaster'

export default function PropertyCard({ property, onPropertyUpdated, onPropertyDeleted, onSyncComplete }) {
  const [syncing, setSyncing] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [lastSyncResult, setLastSyncResult] = useState(null)
  const [showSyncDetails, setShowSyncDetails] = useState(false)

  const handleSync = async () => {
    setSyncing(true)
    setLastSyncResult(null)
    try {
      const result = await api.syncPropertyCalendar(property.id)
      setLastSyncResult(result)
      if (result.success) {
        if (onPropertyUpdated) {
          onPropertyUpdated()
        }
        if (onSyncComplete) {
          onSyncComplete()
        }
      } else {
        throw new Error(result.error || 'Sync failed')
      }
    } catch (error) {
      console.error('Sync error:', error)
      setLastSyncResult({ success: false, error: error.message })
    } finally {
      setSyncing(false)
    }
  }

  const handleDelete = async () => {
    try {
      setDeleting(true)
      const result = await api.deleteProperty(property.id)
      if (result.success) {
        toast.success('Property deleted successfully')
        if (onPropertyDeleted) {
          onPropertyDeleted(property.id)
        }
      } else {
        throw new Error(result.error || 'Failed to delete property')
      }
    } catch (error) {
      console.error('Delete error:', error)
      toast.error(error.message)
      setShowDeleteConfirm(false)
    } finally {
      setDeleting(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getSyncStatus = () => {
    if (!property.ical_url) return { color: 'gray', text: 'No calendar' }
    if (syncing) return { color: 'yellow', text: 'Syncing...' }
    if (lastSyncResult?.success) return { color: 'green', text: 'Synced' }
    if (lastSyncResult?.success === false) return { color: 'red', text: 'Failed' }
    return { color: 'blue', text: 'Ready' }
  }

  const syncStatus = getSyncStatus()

  return (
    <>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {/* Property Header */}
        <div className="px-6 py-4">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{property.name}</h3>
              {property.address && (
                <p className="mt-1 text-sm text-gray-500">{property.address}</p>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <div className={`px-2 py-1 rounded-full text-xs font-medium bg-${syncStatus.color}-100 text-${syncStatus.color}-800`}>
                {syncStatus.text}
              </div>
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="text-gray-400 hover:text-red-600 focus:outline-none"
              >
                <Trash2 className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Contract Management */}
        <div className="px-6 py-4 border-t border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-medium text-gray-700">Contract Management</h4>
            <Link
              to="/contract-templates"
              className="text-sm text-blue-600 hover:text-blue-800 flex items-center space-x-1"
            >
              <FileText size={16} />
              <span>Manage Templates</span>
            </Link>
          </div>

          <dl className="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Template</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {property.contract_template_id ? (
                  <span className="text-green-600">✓ Set</span>
                ) : (
                  <span className="text-yellow-600">Default Template</span>
                )}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Auto Generation</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {property.auto_contract ? (
                  <span className="text-green-600">Enabled</span>
                ) : (
                  <span className="text-gray-600">Manual</span>
                )}
              </dd>
            </div>
          </dl>
        </div>

        {/* Automated Messaging */}
        <div className="px-6 py-4 border-t border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-medium text-gray-700">Automated Messaging</h4>
            <Link
              to={`/message-templates?property_id=${property.id}`}
              className="text-sm text-blue-600 hover:text-blue-800 flex items-center space-x-1"
            >
              <MessageSquare size={16} />
              <span>Manage Messages</span>
            </Link>
          </div>

          <dl className="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Status</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {property.auto_messaging ? (
                  <span className="text-green-600">✓ Enabled</span>
                ) : (
                  <span className="text-gray-600">Disabled</span>
                )}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Active Templates</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {/* This would require an additional query, for now we can leave it as a placeholder */}
                <span className="text-blue-600">View</span>
              </dd>
            </div>
          </dl>
        </div>

        {/* Calendar Info */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-medium text-gray-700">Calendar Sync</h4>
            <button
              onClick={() => setShowSyncDetails(!showSyncDetails)}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              {showSyncDetails ? 'Hide Details' : 'Show Details'}
            </button>
          </div>

          <dl className="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Calendar URL</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {property.ical_url ? (
                  <span className="text-green-600">✓ Connected</span>
                ) : (
                  <span className="text-gray-400">Not set</span>
                )}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Sync Frequency</dt>
              <dd className="mt-1 text-sm text-gray-900">
                Every {property.sync_frequency || 3} hours
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Last Sync</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {formatDate(property.last_sync)}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Auto Features</dt>
              <dd className="mt-1 text-sm text-gray-900 space-x-2">
                {property.auto_verification && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                    Verification
                  </span>
                )}
                {property.auto_contract && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                    Contracts
                  </span>
                )}
                {!property.auto_verification && !property.auto_contract && (
                  <span className="text-gray-400">Manual mode</span>
                )}
              </dd>
            </div>
          </dl>

          {/* Sync Details */}
          {showSyncDetails && lastSyncResult && (
            <div className="mt-4 border-t border-gray-200 pt-4">
              <h5 className="text-sm font-medium text-gray-700 mb-2">Last Sync Details</h5>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="bg-white p-3 rounded-lg border border-gray-200">
                  <div className="text-lg font-semibold text-blue-600">
                    {lastSyncResult.total_processed || 0}
                  </div>
                  <div className="text-gray-600">Total Processed</div>
                </div>
                <div className="bg-white p-3 rounded-lg border border-gray-200">
                  <div className="text-lg font-semibold text-green-600">
                    {lastSyncResult.new_reservations || 0}
                  </div>
                  <div className="text-gray-600">New Reservations</div>
                </div>
                <div className="bg-white p-3 rounded-lg border border-gray-200">
                  <div className="text-lg font-semibold text-yellow-600">
                    {lastSyncResult.updated_reservations || 0}
                  </div>
                  <div className="text-gray-600">Updated</div>
                </div>
                <div className="bg-white p-3 rounded-lg border border-gray-200">
                  <div className="text-lg font-semibold text-red-600">
                    {lastSyncResult.errors || 0}
                  </div>
                  <div className="text-gray-600">Errors</div>
                </div>
              </div>
              {lastSyncResult.error && (
                <div className="mt-3 text-sm text-red-600">
                  Error: {lastSyncResult.error}
                </div>
              )}
            </div>
          )}

          {/* Sync Button */}
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleSync}
              disabled={syncing || !property.ical_url}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {syncing ? (
                <>
                  <RefreshCw className="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-500" />
                  Syncing...
                </>
              ) : (
                <>
                  <RefreshCw className="-ml-1 mr-2 h-4 w-4" />
                  Sync Now
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900">
                  Delete Property
                </h3>
              </div>
            </div>

            <div className="mt-2">
              <p className="text-sm text-gray-500">
                Are you sure you want to delete <span className="font-medium text-gray-900">{property.name}</span>? This action cannot be undone and will also delete:
              </p>
              <ul className="mt-2 text-sm text-gray-500 list-disc list-inside">
                <li>All reservations for this property</li>
                <li>Guest verification records</li>
                <li>Contract templates and signed contracts</li>
                <li>Calendar sync settings</li>
              </ul>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowDeleteConfirm(false)}
                disabled={deleting}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleting}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md shadow-sm hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
              >
                {deleting ? (
                  <>
                    <RefreshCw className="animate-spin -ml-1 mr-2 h-4 w-4" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="-ml-1 mr-2 h-4 w-4" />
                    Delete Property
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
} 