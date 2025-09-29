import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { toast } from './Toaster'
import {
  Play, Eye, Send, Clock, CheckCircle, AlertCircle,
  MessageSquare, User, Home, Calendar
} from 'lucide-react'

export default function AdminTestingPanel() {
  const [reservations, setReservations] = useState([])
  const [templates, setTemplates] = useState([])
  const [selectedReservation, setSelectedReservation] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState('')
  const [previewData, setPreviewData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)

  useEffect(() => {
    loadTestData()
  }, [])

  const loadTestData = async () => {
    try {
      setLoading(true)
      const result = await api.getAdminTestData()
      if (result.success) {
        setReservations(result.reservations || [])
        setTemplates(result.templates || [])
      } else {
        toast.error('Failed to load test data')
      }
    } catch (error) {
      console.error('Error loading test data:', error)
      toast.error('Failed to load test data')
    } finally {
      setLoading(false)
    }
  }

  const previewMessage = async () => {
    if (!selectedReservation || !selectedTemplate) {
      toast.error('Please select both a reservation and template')
      return
    }

    try {
      setLoading(true)
      const result = await api.previewTestMessage({
        reservation_id: selectedReservation,
        template_id: selectedTemplate
      })

      if (result.success) {
        setPreviewData(result)
        toast.success('Message preview generated')
      } else {
        toast.error(result.error || 'Failed to generate preview')
      }
    } catch (error) {
      console.error('Error previewing message:', error)
      toast.error('Failed to generate preview')
    } finally {
      setLoading(false)
    }
  }

  const sendTestMessage = async () => {
    if (!selectedReservation || !selectedTemplate) {
      toast.error('Please select both a reservation and template')
      return
    }

    try {
      setSending(true)
      const result = await api.sendTestMessage({
        reservation_id: selectedReservation,
        template_id: selectedTemplate,
        send_immediately: true
      })

      if (result.success) {
        toast.success('Test message scheduled successfully! It will be sent in ~1 minute.')
        console.log('Scheduled message:', result.scheduled_message)
      } else {
        toast.error(result.error || 'Failed to schedule test message')
      }
    } catch (error) {
      console.error('Error sending test message:', error)
      toast.error('Failed to schedule test message')
    } finally {
      setSending(false)
    }
  }

  const selectedReservationData = reservations.find(r => r.id === selectedReservation)
  const selectedTemplateData = templates.find(t => t.id === selectedTemplate)

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <MessageSquare className="w-5 h-5 mr-2" />
            Admin Testing Panel
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Test message templates with real data instantly
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={loadTestData}
            disabled={loading}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            Refresh Data
          </button>
        </div>
      </div>

      {/* Selection Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Reservation Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Reservation
          </label>
          <select
            value={selectedReservation}
            onChange={(e) => setSelectedReservation(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Choose a reservation...</option>
            {reservations.map((reservation) => (
              <option key={reservation.id} value={reservation.id}>
                {reservation.guest_name} - {reservation.property_name}
                {reservation.check_in && ` (${new Date(reservation.check_in).toLocaleDateString()})`}
              </option>
            ))}
          </select>

          {selectedReservationData && (
            <div className="mt-2 p-3 bg-gray-50 rounded text-xs">
              <div className="flex items-center text-gray-600 mb-1">
                <User className="w-3 h-3 mr-1" />
                <span className="font-medium">{selectedReservationData.guest_name}</span>
              </div>
              <div className="flex items-center text-gray-600 mb-1">
                <Home className="w-3 h-3 mr-1" />
                <span>{selectedReservationData.property_name}</span>
              </div>
              <div className="flex items-center text-gray-600">
                <Calendar className="w-3 h-3 mr-1" />
                <span>
                  {selectedReservationData.check_in && new Date(selectedReservationData.check_in).toLocaleDateString()} -
                  {selectedReservationData.check_out && new Date(selectedReservationData.check_out).toLocaleDateString()}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Template Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Template
          </label>
          <select
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Choose a template...</option>
            {templates.map((template) => (
              <option key={template.id} value={template.id}>
                {template.name} ({template.type})
              </option>
            ))}
          </select>

          {selectedTemplateData && (
            <div className="mt-2 p-3 bg-gray-50 rounded text-xs">
              <div className="font-medium text-gray-700 mb-1">{selectedTemplateData.name}</div>
              <div className="text-gray-600 mb-1">Type: {selectedTemplateData.type}</div>
              <div className="text-gray-500">{selectedTemplateData.content_preview}</div>
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-4 mb-6">
        <button
          onClick={previewMessage}
          disabled={!selectedReservation || !selectedTemplate || loading}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          <Eye className="w-4 h-4 mr-2" />
          {loading ? 'Generating...' : 'Preview Message'}
        </button>

        <button
          onClick={sendTestMessage}
          disabled={!selectedReservation || !selectedTemplate || sending}
          className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          <Send className="w-4 h-4 mr-2" />
          {sending ? 'Scheduling...' : 'Send Test Message'}
        </button>
      </div>

      {/* Preview Results */}
      {previewData && (
        <div className="border-t pt-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Message Preview</h3>

          {/* Original vs Populated Content */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Original Template</h4>
              <div className="p-3 bg-gray-50 rounded-lg border text-sm font-mono">
                {previewData.template.original_content}
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Populated Message</h4>
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm">
                {previewData.template.populated_content}
              </div>
            </div>
          </div>

          {/* Variables Used */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Variables Populated</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {Object.entries(previewData.variables).map(([key, value]) => (
                <div key={key} className="p-2 bg-gray-50 rounded text-xs">
                  <span className="font-mono text-blue-600">{'{'}{key}{'}'}</span>
                  <span className="mx-2">→</span>
                  <span className="text-gray-800">{String(value) || '(empty)'}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Smart Lock Variables */}
          {previewData.smart_lock_variables && Object.keys(previewData.smart_lock_variables).length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
                <CheckCircle className="w-4 h-4 mr-1 text-green-500" />
                Smart Lock Variables ({Object.keys(previewData.smart_lock_variables).length})
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(previewData.smart_lock_variables).map(([key, value]) => (
                  <div key={key} className="p-2 bg-green-50 border border-green-200 rounded text-xs">
                    <span className="font-mono text-green-600">{'{'}{key}{'}'}</span>
                    <span className="mx-2">→</span>
                    <span className="text-gray-800 font-medium">{String(value) || '(empty)'}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}