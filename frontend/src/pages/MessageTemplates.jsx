import React, { useState, useEffect } from 'react'
import { Plus, Edit2, Trash2, Send } from 'lucide-react'
import { api } from '../services/api'
import MessageTemplateForm from '../components/MessageTemplateForm'

export default function MessageTemplates() {
  const [templates, setTemplates] = useState([])
  const [templateTypes, setTemplateTypes] = useState([])
  const [properties, setProperties] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState(null)
  const [selectedProperty, setSelectedProperty] = useState(null)

  useEffect(() => {
    fetchTemplates()
    fetchProperties()
  }, [])

  const fetchTemplates = async () => {
    try {
      setLoading(true)
      const response = await api.getMessageTemplates()
      if (response.success) {
        setTemplates(response.templates || [])
        setTemplateTypes(response.template_types || [])
      } else {
        throw new Error(response.error || 'Failed to load message templates')
      }
    } catch (err) {
      setError(err.message)
      toast.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchProperties = async () => {
    try {
      const response = await api.getProperties()
      setProperties(response.properties || [])
    } catch (err) {
      console.error('Failed to load properties:', err)
      setProperties([])
    }
  }

  const handleCreateTemplate = () => {
    setEditingTemplate(null)
    setIsModalOpen(true)
  }

  const handleEditTemplate = (template) => {
    setEditingTemplate(template)
    setIsModalOpen(true)
  }

  const handleDeleteTemplate = async (templateId) => {
    if (!confirm('Are you sure you want to delete this template?')) return

    try {
      await api.deleteMessageTemplate(templateId)
      setTemplates(templates.filter(t => t.id !== templateId))
    } catch (err) {
      console.error('Failed to delete template:', err)
    }
  }

  const handleFormSubmit = async (templateData) => {
    try {
      if (editingTemplate) {
        // Update existing template
        const updated = await api.updateMessageTemplate(editingTemplate.id, templateData)
        setTemplates(templates.map(t => t.id === updated.id ? updated : t))
      } else {
        // Create new template
        const created = await api.createMessageTemplate(templateData)
        setTemplates(prevTemplates => [created, ...(prevTemplates || [])])
      }
      setIsModalOpen(false)
      setEditingTemplate(null)
    } catch (err) {
      console.error('Failed to save template:', err)
      setError('Failed to save template')
    }
  }

  const handlePropertyChange = (propertyId) => {
    const property = propertyId ? properties.find(p => p.id === propertyId) : null
    setSelectedProperty(property)
    fetchTemplates()
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Message Templates</h1>
        <div className="flex items-center gap-4">
          <select
            className="border rounded-lg px-4 py-2"
            value={selectedProperty?.id || ''}
            onChange={(e) => handlePropertyChange(e.target.value)}
          >
            <option value="">All Properties</option>
            {(properties || []).map(property => (
              <option key={property.id} value={property.id}>
                {property.name}
              </option>
            ))}
          </select>
          <button
            onClick={handleCreateTemplate}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700"
          >
            <Plus size={20} />
            New Template
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-8">Loading...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {(templates || []).map(template => (
            <div
              key={template.id}
              className="bg-white rounded-lg shadow-md p-6 border border-gray-200"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold">{template.name}</h3>
                  <p className="text-sm text-gray-500 capitalize">{template.type}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEditTemplate(template)}
                    className="text-gray-600 hover:text-blue-600"
                  >
                    <Edit2 size={18} />
                  </button>
                  <button
                    onClick={() => handleDeleteTemplate(template.id)}
                    className="text-gray-600 hover:text-red-600"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>

              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-600 mb-1">Channels:</h4>
                <div className="flex gap-2">
                  {(template.channels || []).map(channel => (
                    <span
                      key={channel}
                      className="px-2 py-1 bg-gray-100 rounded-full text-xs capitalize"
                    >
                      {channel}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-600 mb-1">Content Preview:</h4>
                <p className="text-sm text-gray-700 line-clamp-3">{template.content}</p>
              </div>

              {template.property_id && (
                <div className="text-xs text-gray-500">
                  Property: {(properties || []).find(p => p.id === template.property_id)?.name || 'Unknown'}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Template Form Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <MessageTemplateForm
              template={editingTemplate}
              properties={properties}
              templateTypes={templateTypes}
              onSubmit={handleFormSubmit}
              onCancel={() => {
                setIsModalOpen(false)
                setEditingTemplate(null)
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
} 