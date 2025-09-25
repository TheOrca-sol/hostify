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
  properties = []
}) {
  const [content, setContent] = useState(template?.content || '')
  const [subject, setSubject] = useState(template?.subject || '')
  const [saving, setSaving] = useState(false)
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
      const templateData = {
        ...template,
        content,
        subject
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
          {/* Subject Line */}
          <div className="mb-6">
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