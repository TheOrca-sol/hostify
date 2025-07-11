import React, { useState } from 'react'
import { X } from 'lucide-react'

const MESSAGE_TYPES = [
  { value: 'welcome', label: 'Welcome Message' },
  { value: 'verification_request', label: 'Verification Request' },
  { value: 'verification_reminder', label: 'Verification Reminder' },
  { value: 'verification_complete', label: 'Verification Complete' },
  { value: 'contract_ready', label: 'Contract Ready for Signing' },
  { value: 'contract_reminder', label: 'Contract Signing Reminder' },
  { value: 'contract_signed', label: 'Contract Signed Confirmation' },
  { value: 'checkin', label: 'Check-in Instructions' },
  { value: 'during_stay', label: 'During Stay' },
  { value: 'checkout', label: 'Check-out Reminder' },
  { value: 'review_request', label: 'Review Request' },
  { value: 'cleaner', label: 'Cleaner Notification' }
]

const CHANNELS = [
  { value: 'email', label: 'Email' },
  { value: 'sms', label: 'SMS' },
  { value: 'whatsapp', label: 'WhatsApp' }
]

const VARIABLES = [
  { key: 'guest_name', description: 'Guest\'s full name' },
  { key: 'property_name', description: 'Property name' },
  { key: 'check_in_date', description: 'Check-in date' },
  { key: 'check_in_time', description: 'Check-in time' },
  { key: 'check_out_date', description: 'Check-out date' },
  { key: 'check_out_time', description: 'Check-out time' },
  { key: 'property_address', description: 'Property address' },
  { key: 'verification_link', description: 'Guest verification link' },
  { key: 'verification_expiry', description: 'Verification link expiry time' },
  { key: 'contract_link', description: 'Contract signing link' },
  { key: 'contract_expiry', description: 'Contract signing link expiry time' },
  { key: 'host_name', description: 'Property host name' },
  { key: 'host_phone', description: 'Host contact number' }
]

export default function MessageTemplateForm({ template, properties, onSubmit, onCancel }) {
  const [formData, setFormData] = useState({
    name: template?.name || '',
    type: template?.type || 'welcome',
    property_id: template?.property_id || '',
    subject: template?.subject || '',
    content: template?.content || '',
    channels: template?.channels || ['email'],
    language: template?.language || 'en',
    active: template?.active ?? true
  })

  const [error, setError] = useState(null)

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleChannelToggle = (channel) => {
    setFormData(prev => ({
      ...prev,
      channels: prev.channels.includes(channel)
        ? prev.channels.filter(c => c !== channel)
        : [...prev.channels, channel]
    }))
  }

  const insertVariable = (variable) => {
    const textArea = document.getElementById('content')
    const start = textArea.selectionStart
    const end = textArea.selectionEnd
    const text = textArea.value
    const before = text.substring(0, start)
    const after = text.substring(end)
    const newContent = `${before}{${variable}}${after}`
    
    setFormData(prev => ({ ...prev, content: newContent }))
    
    // Reset cursor position
    setTimeout(() => {
      textArea.focus()
      const newCursor = start + variable.length + 2
      textArea.setSelectionRange(newCursor, newCursor)
    }, 0)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    // Validation
    if (!formData.name.trim()) {
      setError('Template name is required')
      return
    }
    if (!formData.content.trim()) {
      setError('Template content is required')
      return
    }
    if (formData.channels.length === 0) {
      setError('At least one channel must be selected')
      return
    }
    if (formData.channels.includes('email') && !formData.subject.trim()) {
      setError('Subject is required for email templates')
      return
    }

    onSubmit(formData)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">
          {template ? 'Edit Template' : 'New Template'}
        </h2>
        <button
          type="button"
          onClick={onCancel}
          className="text-gray-500 hover:text-gray-700"
        >
          <X size={24} />
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Template Name
          </label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            className="w-full border rounded-lg px-3 py-2"
            placeholder="e.g., Welcome Message"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Message Type
          </label>
          <select
            name="type"
            value={formData.type}
            onChange={handleChange}
            className="w-full border rounded-lg px-3 py-2"
          >
            {MESSAGE_TYPES.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Property (Optional)
          </label>
          <select
            name="property_id"
            value={formData.property_id}
            onChange={handleChange}
            className="w-full border rounded-lg px-3 py-2"
          >
            <option value="">All Properties</option>
            {properties.map(property => (
              <option key={property.id} value={property.id}>
                {property.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Language
          </label>
          <select
            name="language"
            value={formData.language}
            onChange={handleChange}
            className="w-full border rounded-lg px-3 py-2"
          >
            <option value="en">English</option>
            <option value="fr">French</option>
            <option value="ar">Arabic</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Delivery Channels
        </label>
        <div className="flex gap-4">
          {CHANNELS.map(channel => (
            <label key={channel.value} className="flex items-center">
              <input
                type="checkbox"
                checked={formData.channels.includes(channel.value)}
                onChange={() => handleChannelToggle(channel.value)}
                className="mr-2"
              />
              {channel.label}
            </label>
          ))}
        </div>
      </div>

      {formData.channels.includes('email') && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Email Subject
          </label>
          <input
            type="text"
            name="subject"
            value={formData.subject}
            onChange={handleChange}
            className="w-full border rounded-lg px-3 py-2"
            placeholder="e.g., Welcome to {property_name}!"
          />
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Message Content
        </label>
        <div className="mb-2">
          <div className="text-sm text-gray-500 mb-2">Available Variables:</div>
          <div className="flex flex-wrap gap-2">
            {VARIABLES.map(variable => (
              <button
                key={variable.key}
                type="button"
                onClick={() => insertVariable(variable.key)}
                className="px-2 py-1 bg-gray-100 rounded text-sm hover:bg-gray-200"
                title={variable.description}
              >
                {'{' + variable.key + '}'}
              </button>
            ))}
          </div>
        </div>
        <textarea
          id="content"
          name="content"
          value={formData.content}
          onChange={handleChange}
          rows={8}
          className="w-full border rounded-lg px-3 py-2"
          placeholder="Enter your message content here..."
        />
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          name="active"
          checked={formData.active}
          onChange={handleChange}
          className="mr-2"
        />
        <label className="text-sm text-gray-700">
          Template is active
        </label>
      </div>

      <div className="flex justify-end gap-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border rounded-lg hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          {template ? 'Update Template' : 'Create Template'}
        </button>
      </div>
    </form>
  )
} 