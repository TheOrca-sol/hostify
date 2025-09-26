import React, { useState, useRef } from 'react'
import { api } from '../services/api'
import { toast } from '../components/Toaster'
import SmartLockVariableSelector from './SmartLockVariableSelector'
import {
  Eye, Save, TestTube, User, Home, Calendar, Lock,
  AlertCircle, CheckCircle, RefreshCw
} from 'lucide-react'

export default function EnhancedMessageTemplateEditor({
  template,
  onSave,
  reservations = [],
  properties = [],
  templateTypes = []
}) {
  const [name, setName] = useState(template?.name || '')
  const [content, setContent] = useState(template?.content || '')
  const [subject, setSubject] = useState(template?.subject || '')
  const [templateType, setTemplateType] = useState(template?.template_type || 'welcome')
  const [propertyId, setPropertyId] = useState(template?.property_id || '')
  const [active, setActive] = useState(template?.active ?? true)
  const [language, setLanguage] = useState(template?.language || 'en')
  const [channels, setChannels] = useState(template?.channels || ['sms'])
  // Automation fields
  const [triggerEvent, setTriggerEvent] = useState(template?.trigger_event || '')
  const [triggerOffsetValue, setTriggerOffsetValue] = useState(template?.trigger_offset_value || 0)
  const [triggerOffsetUnit, setTriggerOffsetUnit] = useState(template?.trigger_offset_unit || 'days')
  const [triggerDirection, setTriggerDirection] = useState(template?.trigger_direction || 'before')

  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null)
  const [selectedReservation, setSelectedReservation] = useState('')
  const [showPreview, setShowPreview] = useState(false)

  const contentRef = useRef(null)

  const insertVariable = (variableText) => {
    if (contentRef.current) {
      const textarea = contentRef.current
      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      const text = textarea.value
      const newText = text.substring(0, start) + variableText + text.substring(end)

      setContent(newText)

      // Restore cursor position after the inserted variable
      setTimeout(() => {
        textarea.focus()
        textarea.setSelectionRange(start + variableText.length, start + variableText.length)
      }, 0)
    } else {
      // Fallback: append to end
      setContent(prev => prev + variableText)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      // Validation
      if (!name.trim()) {
        setError('Template name is required')
        return
      }
      setError(null)

      const templateData = {
        ...template,
        name,
        content,
        subject,
        template_type: templateType,
        property_id: propertyId,
        active,
        language,
        channels,
        trigger_event: triggerEvent,
        trigger_offset_value: triggerOffsetValue,
        trigger_offset_unit: triggerOffsetUnit,
        trigger_direction: triggerDirection
      }

      if (onSave) {
        await onSave(templateData)
        toast.success('Template saved successfully!')
      }
    } catch (error) {
      console.error('Error saving template:', error)
      toast.error('Failed to save template')
    } finally {
      setSaving(false)
    }
  }

  const testTemplate = async () => {
    if (!selectedReservation) {
      toast.error('Please select a reservation to test with')
      return
    }

    try {
      setTesting(true)
      setTestResult(null)

      const result = await api.testSmartLockTemplate(selectedReservation, content)

      if (result.success) {
        setTestResult({
          success: true,
          originalContent: content,
          populatedContent: result.populated_content,
          variables: result.smart_lock_variables
        })
      } else {
        setTestResult({
          success: false,
          error: result.error || 'Failed to test template'
        })
      }
    } catch (error) {
      console.error('Error testing template:', error)
      setTestResult({
        success: false,
        error: 'Failed to test template'
      })
    } finally {
      setTesting(false)
    }
  }

  const getVariableCount = (text) => {
    const matches = text.match(/\{[^}]+\}/g)
    return matches ? matches.length : 0
  }

  const getSmartLockVariableCount = (text) => {
    const smartLockVars = [
      'smart_lock_type', 'smart_lock_passcode', 'smart_lock_instructions',
      'access_method', 'lock_passcode_section', 'smart_lock_details',
      'passcode_valid_from', 'passcode_valid_until'
    ]

    let count = 0
    smartLockVars.forEach(varName => {
      const regex = new RegExp(`\\{${varName}\\}`, 'g')
      const matches = text.match(regex)
      if (matches) count += matches.length
    })

    return count
  }

  return (
    <div className="space-y-6">
      {/* Template Editor Header */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">Message Template Editor</h3>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowPreview(!showPreview)}
                className="text-gray-600 hover:text-gray-900 flex items-center"
              >
                <Eye className="w-4 h-4 mr-2" />
                {showPreview ? 'Hide Preview' : 'Show Preview'}
              </button>
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
                    Save Template
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        <div className="p-6">
          {error && (
            <div className="bg-red-100 text-red-700 p-3 rounded-lg mb-6">
              {error}
            </div>
          )}

          {/* Template Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Template Name *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter template name..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Message Type
              </label>
              <select
                value={templateType}
                onChange={(e) => setTemplateType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {templateTypes.map(type => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Property (Optional)
              </label>
              <select
                value={propertyId}
                onChange={(e) => setPropertyId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Properties</option>
                {properties.map(property => (
                  <option key={property.id} value={property.id}>{property.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Subject Line
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Message subject (for email channels)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="en">English</option>
                <option value="fr">Français</option>
                <option value="ar">العربية</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Channels
              </label>
              <select
                value={channels[0] || 'sms'}
                onChange={(e) => setChannels([e.target.value])}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="sms">SMS</option>
                <option value="email">Email</option>
                <option value="whatsapp">WhatsApp</option>
              </select>
            </div>
            <div className="flex items-center">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={active}
                  onChange={(e) => setActive(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-sm font-medium text-gray-700">
                  Active Template
                </span>
              </label>
            </div>
          </div>

          {/* Content Editor */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="block text-sm font-medium text-gray-700">
                Message Content
              </label>
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span>{getVariableCount(content)} variables</span>
                <span className="flex items-center">
                  <Lock className="w-3 h-3 mr-1" />
                  {getSmartLockVariableCount(content)} smart lock vars
                </span>
              </div>
            </div>

            {/* Basic Variable Buttons */}
            <div className="flex flex-wrap gap-2 mb-2">
              <button type="button" onClick={() => insertVariable('{guest_name}')} className="px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm transition-colors">{'{guest_name}'}</button>
              <button type="button" onClick={() => insertVariable('{property_name}')} className="px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm transition-colors">{'{property_name}'}</button>
              <button type="button" onClick={() => insertVariable('{check_in_date}')} className="px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm transition-colors">{'{check_in_date}'}</button>
              <button type="button" onClick={() => insertVariable('{check_out_date}')} className="px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm transition-colors">{'{check_out_date}'}</button>
              <button type="button" onClick={() => insertVariable('{verification_link}')} className="px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm transition-colors">{'{verification_link}'}</button>
              <button type="button" onClick={() => insertVariable('{host_name}')} className="px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm transition-colors">{'{host_name}'}</button>
            </div>

            <textarea
              ref={contentRef}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Enter your message template content here..."
              rows={12}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm resize-none"
            />

            {/* Template Stats */}
            <div className="flex items-center space-x-4 text-xs text-gray-500 bg-gray-50 p-3 rounded">
              <span>Characters: {content.length}</span>
              <span>Lines: {content.split('\n').length}</span>
              <span>Words: {content.split(/\s+/).filter(word => word.length > 0).length}</span>
            </div>
          </div>

          {/* Automation Rule Builder */}
          <div className="border-t border-gray-200 pt-6 mt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <RefreshCw className="w-5 h-5 mr-2" />
              Automation Rule
            </h3>

            {/* Current Status Display */}
            {template && (
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="text-sm text-blue-800">
                  <strong>Current Automation:</strong>
                  {triggerEvent ? (
                    <span className="ml-2 text-green-600">
                      ✓ Active - Sends {triggerOffsetValue} {triggerOffsetUnit} {triggerDirection} {triggerEvent.replace('_', ' ')}
                    </span>
                  ) : (
                    <span className="ml-2 text-gray-600">
                      ⚠ Manual only - No automation configured
                    </span>
                  )}
                </div>
              </div>
            )}

            <div className="flex flex-wrap items-center gap-4 p-4 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Send this message</span>
              <input
                type="number"
                value={triggerOffsetValue}
                onChange={(e) => setTriggerOffsetValue(parseInt(e.target.value) || 0)}
                className="w-20 border border-gray-300 rounded-lg px-3 py-2 text-sm"
                min="0"
              />
              <select
                value={triggerOffsetUnit}
                onChange={(e) => setTriggerOffsetUnit(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
              >
                <option value="hours">hour(s)</option>
                <option value="days">day(s)</option>
              </select>
              <select
                value={triggerDirection}
                onChange={(e) => setTriggerDirection(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
              >
                <option value="before">before</option>
                <option value="after">after</option>
              </select>
              <select
                value={triggerEvent}
                onChange={(e) => setTriggerEvent(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm min-w-[140px]"
              >
                <option value="">Select Trigger</option>
                <option value="check_in">Check-in</option>
                <option value="check_out">Check-out</option>
                <option value="verification">Verification</option>
              </select>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {triggerEvent ?
                `This message will be sent automatically ${triggerOffsetValue} ${triggerOffsetUnit} ${triggerDirection} ${triggerEvent.replace('_', ' ')}.` :
                "Leave the trigger blank to send this message manually."
              }
            </p>
          </div>
        </div>
      </div>

      {/* Smart Lock Variable Selector */}
      <SmartLockVariableSelector onInsertVariable={insertVariable} />

      {/* Template Testing */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6 border-b border-gray-200">
          <h4 className="text-lg font-medium text-gray-900 flex items-center">
            <TestTube className="w-5 h-5 mr-2" />
            Test Template
          </h4>
          <p className="text-sm text-gray-600 mt-1">
            Test your template with real reservation data to see how variables are populated
          </p>
        </div>

        <div className="p-6 space-y-4">
          {/* Reservation Selector */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Test with Reservation
              </label>
              <select
                value={selectedReservation}
                onChange={(e) => setSelectedReservation(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select a reservation...</option>
                {reservations.map((reservation) => (
                  <option key={reservation.id} value={reservation.id}>
                    {reservation.first_name} {reservation.last_name} - {reservation.property_name || 'Property'}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={testTemplate}
                disabled={testing || !selectedReservation || !content}
                className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:bg-gray-400 flex items-center"
              >
                {testing ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Testing...
                  </>
                ) : (
                  <>
                    <TestTube className="w-4 h-4 mr-2" />
                    Test Template
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Test Results */}
          {testResult && (
            <div className={`border rounded-lg p-4 ${
              testResult.success
                ? 'border-green-200 bg-green-50'
                : 'border-red-200 bg-red-50'
            }`}>
              <div className="flex items-start space-x-3">
                {testResult.success ? (
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                )}
                <div className="flex-1">
                  <h5 className={`font-medium ${
                    testResult.success ? 'text-green-900' : 'text-red-900'
                  }`}>
                    {testResult.success ? 'Template Test Successful' : 'Template Test Failed'}
                  </h5>

                  {testResult.success ? (
                    <div className="mt-3 space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-green-800 mb-1">
                          Populated Content:
                        </label>
                        <div className="bg-white border border-green-200 rounded p-3">
                          <pre className="text-sm text-gray-900 whitespace-pre-wrap font-sans">
                            {testResult.populatedContent}
                          </pre>
                        </div>
                      </div>

                      {testResult.variables && Object.keys(testResult.variables).length > 0 && (
                        <div>
                          <label className="block text-sm font-medium text-green-800 mb-1">
                            Smart Lock Variables Used:
                          </label>
                          <div className="bg-white border border-green-200 rounded p-3">
                            <div className="grid grid-cols-1 gap-2">
                              {Object.entries(testResult.variables).map(([key, value]) => (
                                <div key={key} className="flex items-center space-x-2 text-xs">
                                  <code className="bg-green-100 text-green-800 px-2 py-1 rounded">
                                    {key}
                                  </code>
                                  <span className="text-gray-600">→</span>
                                  <span className="text-gray-900 flex-1 truncate">
                                    {value || '(empty)'}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-red-800 mt-1">{testResult.error}</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Live Preview */}
      {showPreview && (
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6 border-b border-gray-200">
            <h4 className="text-lg font-medium text-gray-900 flex items-center">
              <Eye className="w-5 h-5 mr-2" />
              Live Preview
            </h4>
          </div>
          <div className="p-6">
            <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
              <div className="space-y-3">
                {subject && (
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">SUBJECT</label>
                    <div className="font-medium text-gray-900">{subject}</div>
                  </div>
                )}
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">MESSAGE</label>
                  <div className="whitespace-pre-wrap font-sans text-gray-900">
                    {content || 'Start typing to see preview...'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}