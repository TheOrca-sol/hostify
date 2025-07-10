import React, { useState } from 'react'
import { api } from '../services/api'

export default function ContractTemplateForm({ onTemplateCreated, initialTemplate = null }) {
  const [formData, setFormData] = useState({
    name: initialTemplate?.name || '',
    template_content: initialTemplate?.template_content || '',
    language: initialTemplate?.language || 'en',
    legal_jurisdiction: initialTemplate?.legal_jurisdiction || 'morocco',
    is_default: initialTemplate?.is_default || false
  })
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    
    try {
      if (!formData.name.trim() || !formData.template_content.trim()) {
        throw new Error('Name and template content are required')
      }
      
      const result = initialTemplate
        ? await api.updateContractTemplate(initialTemplate.id, formData)
        : await api.createContractTemplate(formData)
      
      if (result.success) {
        if (onTemplateCreated) {
          onTemplateCreated(result.template)
        }
        // Clear form if creating new
        if (!initialTemplate) {
          setFormData({
            name: '',
            template_content: '',
            language: 'en',
            legal_jurisdiction: 'morocco',
            is_default: false
          })
        }
      } else {
        throw new Error(result.error || 'Failed to save template')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }
  
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }
  
  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
          {error}
        </div>
      )}
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Template Name
        </label>
        <input
          type="text"
          name="name"
          value={formData.name}
          onChange={handleChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
          placeholder="e.g., Standard Rental Contract"
          required
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Template Content
        </label>
        <textarea
          name="template_content"
          value={formData.template_content}
          onChange={handleChange}
          rows={10}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500 font-mono text-sm"
          placeholder="Enter contract template with variables like {{ guest.name }}, {{ property.name }}, etc."
          required
        />
        <p className="mt-1 text-sm text-gray-500">
          Available variables: guest.*, property.*, reservation.*, host.*
        </p>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Language
          </label>
          <select
            name="language"
            value={formData.language}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="en">English</option>
            <option value="fr">French</option>
            <option value="ar">Arabic</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Legal Jurisdiction
          </label>
          <select
            name="legal_jurisdiction"
            value={formData.legal_jurisdiction}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="morocco">Morocco</option>
            <option value="france">France</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>
      
      <div className="flex items-center">
        <input
          type="checkbox"
          name="is_default"
          checked={formData.is_default}
          onChange={handleChange}
          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
        />
        <label className="ml-2 text-sm text-gray-700">
          Set as default template
        </label>
      </div>
      
      <div className="flex justify-end">
        <button
          type="submit"
          disabled={loading}
          className={`px-4 py-2 rounded-lg text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 ${
            loading ? 'opacity-75 cursor-not-allowed' : ''
          }`}
        >
          {loading ? 'Saving...' : initialTemplate ? 'Update Template' : 'Create Template'}
        </button>
      </div>
    </form>
  )
} 