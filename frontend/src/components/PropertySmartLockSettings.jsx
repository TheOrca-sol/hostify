import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { toast } from '../components/Toaster'
import { Lock, Settings, Save, AlertCircle } from 'lucide-react'

export default function PropertySmartLockSettings({ propertyId, onSettingsUpdate = null }) {
  const [settings, setSettings] = useState({
    smart_lock_type: 'traditional',
    smart_lock_instructions: '',
    smart_lock_settings: {}
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [initialLoad, setInitialLoad] = useState(true)

  useEffect(() => {
    if (propertyId) {
      loadSettings()
    }
  }, [propertyId])

  const loadSettings = async () => {
    try {
      setLoading(true)
      const result = await api.getPropertySmartLockSettings(propertyId)

      if (result.success) {
        setSettings({
          smart_lock_type: result.smart_lock_type || 'traditional',
          smart_lock_instructions: result.smart_lock_instructions || '',
          smart_lock_settings: result.smart_lock_settings || {}
        })
      }
    } catch (error) {
      console.error('Error loading smart lock settings:', error)
      if (initialLoad) {
        toast.error('Failed to load smart lock settings')
      }
    } finally {
      setLoading(false)
      setInitialLoad(false)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      const result = await api.updatePropertySmartLockSettings(propertyId, settings)

      if (result.success) {
        toast.success('Smart lock settings updated successfully')
        if (onSettingsUpdate) {
          onSettingsUpdate(settings)
        }
      } else {
        toast.error(result.error || 'Failed to update settings')
      }
    } catch (error) {
      console.error('Error saving smart lock settings:', error)
      toast.error('Failed to save smart lock settings')
    } finally {
      setSaving(false)
    }
  }

  const getSmartLockTypeInfo = (type) => {
    const info = {
      ttlock: {
        label: 'Automated Smart Lock',
        description: 'Fully automated passcode generation. Passcodes are generated automatically 3 hours before check-in.',
        icon: '🔐',
        color: 'text-blue-600 bg-blue-100'
      },
      manual: {
        label: 'Manual Smart Lock',
        description: 'Host manually sets passcodes. You\'ll receive SMS notifications to set passcodes for each reservation.',
        icon: '👤',
        color: 'text-orange-600 bg-orange-100'
      },
      traditional: {
        label: 'Traditional Access',
        description: 'Key-based or lockbox access. No passcode generation needed.',
        icon: '🔑',
        color: 'text-gray-600 bg-gray-100'
      }
    }
    return info[type] || info.traditional
  }

  const getDefaultInstructions = (type) => {
    const defaults = {
      ttlock: 'Enter the provided passcode on the smart lock keypad. Wait for the green light before turning the handle.',
      manual: 'You will receive the smart lock passcode 3 hours before check-in. Enter it on the keypad to unlock.',
      traditional: 'Check-in instructions and key collection details will be provided by the host.'
    }
    return defaults[type] || defaults.traditional
  }

  const handleTypeChange = (newType) => {
    setSettings(prev => ({
      ...prev,
      smart_lock_type: newType,
      smart_lock_instructions: prev.smart_lock_instructions || getDefaultInstructions(newType)
    }))
  }

  if (loading && initialLoad) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="animate-pulse">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-6 h-6 bg-gray-200 rounded"></div>
            <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          </div>
          <div className="space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="h-10 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
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
            <Lock className="w-6 h-6 text-blue-600" />
            <div>
              <h3 className="text-lg font-medium text-gray-900">Smart Lock Configuration</h3>
              <p className="text-sm text-gray-600">Configure how guests access this property</p>
            </div>
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 flex items-center"
          >
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save Settings
              </>
            )}
          </button>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Smart Lock Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Access Method
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {['ttlock', 'manual', 'traditional'].map((type) => {
              const info = getSmartLockTypeInfo(type)
              const isSelected = settings.smart_lock_type === type

              return (
                <div
                  key={type}
                  onClick={() => handleTypeChange(type)}
                  className={`cursor-pointer rounded-lg border-2 p-4 transition-colors ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg ${info.color}`}>
                      {info.icon}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{info.label}</h4>
                      <p className="text-sm text-gray-600 mt-1">{info.description}</p>
                    </div>
                    <div className={`w-4 h-4 rounded-full border-2 ${
                      isSelected
                        ? 'border-blue-500 bg-blue-500'
                        : 'border-gray-300'
                    }`}>
                      {isSelected && (
                        <div className="w-full h-full rounded-full bg-blue-500 flex items-center justify-center">
                          <div className="w-2 h-2 bg-white rounded-full"></div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Access Instructions */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Guest Access Instructions
          </label>
          <p className="text-sm text-gray-500 mb-3">
            These instructions will be included in guest check-in messages and shown during the access process.
          </p>
          <textarea
            value={settings.smart_lock_instructions}
            onChange={(e) => setSettings(prev => ({
              ...prev,
              smart_lock_instructions: e.target.value
            }))}
            placeholder={getDefaultInstructions(settings.smart_lock_type)}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
          />
        </div>

        {/* TTLock Specific Settings */}
        {settings.smart_lock_type === 'ttlock' && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-blue-900">Automated Smart Lock Configuration</h4>
                <p className="text-sm text-blue-800 mt-1">
                  Make sure you have connected your smart lock account and assigned devices to this property
                  in the Smart Locks section. Passcodes will be generated automatically 3 hours before guest check-in.
                </p>
                <ul className="text-sm text-blue-700 mt-2 space-y-1">
                  <li>• Passcodes are valid from 1 hour before check-in to 1 hour after check-out</li>
                  <li>• Same passcode works on all assigned locks for this property</li>
                  <li>• You'll receive SMS notifications when passcodes are generated</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Manual Lock Specific Settings */}
        {settings.smart_lock_type === 'manual' && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-orange-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-orange-900">Manual Smart Lock Setup</h4>
                <p className="text-sm text-orange-800 mt-1">
                  You'll receive SMS notifications when reservations need passcodes. You can set passcodes
                  through the Hostify app or by replying to SMS notifications.
                </p>
                <ul className="text-sm text-orange-700 mt-2 space-y-1">
                  <li>• SMS alerts sent 3 hours before guest check-in</li>
                  <li>• Set passcodes via the reservations dashboard</li>
                  <li>• Guests receive passcode details automatically once set</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Traditional Access Information */}
        {settings.smart_lock_type === 'traditional' && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-gray-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-gray-900">Traditional Access Method</h4>
                <p className="text-sm text-gray-700 mt-1">
                  No automated passcode generation. Include key pickup, lockbox codes, or other access
                  details in your guest instructions above.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}