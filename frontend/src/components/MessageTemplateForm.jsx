import React, { useState } from 'react'
import { X } from 'lucide-react'

const VARIABLES = [
  { key: 'guest_name', description: 'Guest\'s full name' },
  { key: 'property_name', description: 'Property name' },
  { key: 'check_in_date', description: 'Check-in date' },
  { key: 'check_out_date', description: 'Check-out date' },
  { key: 'verification_link', description: 'Guest verification link' },
  { key: 'host_name', description: 'Property host name' },
]

export default function MessageTemplateForm({ template, properties, templateTypes, onSubmit, onCancel }) {
  const [formData, setFormData] = useState({
    name: template?.name || '',
    template_type: template?.template_type || 'welcome',
    property_id: template?.property_id || '',
    content: template?.content || '',
    channels: ['sms'],
    language: template?.language || 'en',
    active: template?.active ?? true,
    // Automation fields
    trigger_event: template?.trigger_event || '',
    trigger_offset_value: template?.trigger_offset_value || 1,
    trigger_offset_unit: template?.trigger_offset_unit || 'days',
    trigger_direction: template?.trigger_direction || 'before',
  })

  const [error, setError] = useState(null)

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const insertVariable = (variable) => {
    const textArea = document.getElementById('content')
    const start = textArea.selectionStart
    const newContent = `${formData.content.substring(0, start)}{{${variable}}}${formData.content.substring(start)}`
    setFormData(prev => ({ ...prev, content: newContent }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!formData.name.trim()) {
      setError('Template name is required')
      return
    }
    onSubmit(formData)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">{template ? 'Edit Template' : 'New Template'}</h2>
        <button type="button" onClick={onCancel}><X size={24} /></button>
      </div>

      {error && <div className="bg-red-100 text-red-700 p-3 rounded">{error}</div>}

      {/* Core Details */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium">Template Name</label>
          <input type="text" name="name" value={formData.name} onChange={handleChange} className="w-full border rounded-lg px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm font-medium">Message Type</label>
          <select name="template_type" value={formData.template_type} onChange={handleChange} className="w-full border rounded-lg px-3 py-2">
            {templateTypes.map(type => <option key={type.value} value={type.value}>{type.label}</option>)}
          </select>
        </div>
      </div>

      {/* Content */}
      <div>
        <label className="block text-sm font-medium">Message Content</label>
        <div className="flex flex-wrap gap-2 mb-2">
          {VARIABLES.map(v => <button key={v.key} type="button" onClick={() => insertVariable(v.key)} className="px-2 py-1 bg-gray-100 rounded text-sm">{`{{${v.key}}}`}</button>)}
        </div>
        <textarea id="content" name="content" value={formData.content} onChange={handleChange} rows={8} className="w-full border rounded-lg px-3 py-2" />
      </div>

      {/* Automation Rule Builder */}
      <div className="border-t pt-4">
        <h3 className="text-lg font-semibold mb-2">Automation Rule</h3>
        <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
          <span>Send this message</span>
          <input
            type="number"
            name="trigger_offset_value"
            value={formData.trigger_offset_value}
            onChange={handleChange}
            className="w-20 border rounded-lg px-3 py-2"
            min="1"
          />
          <select
            name="trigger_offset_unit"
            value={formData.trigger_offset_unit}
            onChange={handleChange}
            className="border rounded-lg px-3 py-2"
          >
            <option value="hours">hour(s)</option>
            <option value="days">day(s)</option>
          </select>
          <select
            name="trigger_direction"
            value={formData.trigger_direction}
            onChange={handleChange}
            className="border rounded-lg px-3 py-2"
          >
            <option value="before">before</option>
            <option value="after">after</option>
          </select>
          <select
            name="trigger_event"
            value={formData.trigger_event}
            onChange={handleChange}
            className="border rounded-lg px-3 py-2"
          >
            <option value="">Select Trigger</option>
            <option value="check_in">Check-in</option>
            <option value="check_out">Check-out</option>
            <option value="verification">Verification</option>
          </select>
        </div>
        <p className="text-xs text-gray-500 mt-2">Leave the trigger blank to send this message manually.</p>
      </div>

      {/* Footer */}
      <div className="flex justify-end gap-4">
        <button type="button" onClick={onCancel} className="px-4 py-2 border rounded-lg">Cancel</button>
        <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg">{template ? 'Update' : 'Create'}</button>
      </div>
    </form>
  )
}