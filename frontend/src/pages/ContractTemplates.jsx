import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import ContractTemplateForm from '../components/ContractTemplateForm'

export default function ContractTemplates() {
  const [templates, setTemplates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editingTemplate, setEditingTemplate] = useState(null)
  const [showForm, setShowForm] = useState(false)
  
  useEffect(() => {
    loadTemplates()
  }, [])
  
  const loadTemplates = async () => {
    try {
      setLoading(true)
      const result = await api.getContractTemplates()
      
      if (result.success) {
        setTemplates(result.templates)
      } else {
        throw new Error(result.error || 'Failed to load templates')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }
  
  const handleTemplateCreated = (template) => {
    setTemplates(prev => [...prev, template])
    setShowForm(false)
  }
  
  const handleTemplateUpdated = (updatedTemplate) => {
    setTemplates(prev => prev.map(t => 
      t.id === updatedTemplate.id ? updatedTemplate : t
    ))
    setEditingTemplate(null)
  }
  
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Contract Templates
        </h1>
        
        {!showForm && !editingTemplate && (
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 rounded-lg text-white bg-primary-600 hover:bg-primary-700"
          >
            Create Template
          </button>
        )}
      </div>
      
      {error && (
        <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6">
          {error}
        </div>
      )}
      
      {/* Template Form */}
      {(showForm || editingTemplate) && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-medium text-gray-900">
              {editingTemplate ? 'Edit Template' : 'Create New Template'}
            </h2>
            
            <button
              onClick={() => {
                setShowForm(false)
                setEditingTemplate(null)
              }}
              className="text-gray-500 hover:text-gray-700"
            >
              Cancel
            </button>
          </div>
          
          <ContractTemplateForm
            initialTemplate={editingTemplate}
            onTemplateCreated={editingTemplate ? handleTemplateUpdated : handleTemplateCreated}
          />
        </div>
      )}
      
      {/* Templates List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading templates...</p>
        </div>
      ) : templates.length > 0 ? (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {templates.map(template => (
              <li key={template.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">
                      {template.name}
                      {template.is_default && (
                        <span className="ml-2 px-2 py-1 text-xs font-medium text-primary-700 bg-primary-100 rounded-full">
                          Default
                        </span>
                      )}
                    </h3>
                    
                    <div className="mt-1 text-sm text-gray-500">
                      Language: {template.language.toUpperCase()} |
                      Jurisdiction: {template.legal_jurisdiction}
                    </div>
                  </div>
                  
                  <button
                    onClick={() => setEditingTemplate(template)}
                    className="px-3 py-1 text-sm text-primary-600 hover:text-primary-700"
                  >
                    Edit
                  </button>
                </div>
                
                <div className="mt-2">
                  <pre className="text-xs text-gray-600 font-mono bg-gray-50 p-3 rounded-lg overflow-auto max-h-24">
                    {template.template_content.substring(0, 200)}
                    {template.template_content.length > 200 ? '...' : ''}
                  </pre>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : !showForm && (
        <div className="text-center py-12">
          <p className="text-gray-500">No templates yet. Create your first template!</p>
        </div>
      )}
    </div>
  )
} 