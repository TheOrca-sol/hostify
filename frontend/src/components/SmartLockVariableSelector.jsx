import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { toast } from '../components/Toaster'
import { Lock, Plus, Info, Copy, ChevronDown, ChevronUp } from 'lucide-react'

export default function SmartLockVariableSelector({ onInsertVariable }) {
  const [variables, setVariables] = useState({})
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    loadSmartLockVariables()
  }, [])

  const loadSmartLockVariables = async () => {
    try {
      setLoading(true)
      const result = await api.getSmartLockVariables()

      if (result.success) {
        setVariables(result.variables || {})
      } else {
        console.error('Failed to load smart lock variables:', result.error)
      }
    } catch (error) {
      console.error('Error loading smart lock variables:', error)
    } finally {
      setLoading(false)
    }
  }

  const insertVariable = (variableName) => {
    const variableText = `{${variableName}}`
    if (onInsertVariable) {
      onInsertVariable(variableText)
    }
    toast.success(`Inserted {${variableName}}`)
  }

  const copyVariable = (variableName) => {
    const variableText = `{${variableName}}`
    navigator.clipboard.writeText(variableText)
    toast.success('Variable copied to clipboard!')
  }

  const getVariablesByCategory = () => {
    const categorized = {
      'Basic Smart Lock': {
        'smart_lock_type': variables.smart_lock_type || 'Type of smart lock system',
        'smart_lock_passcode': variables.smart_lock_passcode || 'The passcode for smart lock access',
        'access_method': variables.access_method || 'Method of access (smart_lock or traditional)'
      },
      'Formatted Sections': {
        'lock_passcode_section': variables.lock_passcode_section || 'Complete formatted section with passcode details',
        'smart_lock_details': variables.smart_lock_details || 'Detailed information about smart lock access'
      },
      'Instructions & Timing': {
        'smart_lock_instructions': variables.smart_lock_instructions || 'Custom instructions for accessing the smart lock',
        'passcode_valid_from': variables.passcode_valid_from || 'When the passcode becomes valid',
        'passcode_valid_until': variables.passcode_valid_until || 'When the passcode expires'
      }
    }

    return categorized
  }

  if (loading) {
    return (
      <div className="border border-gray-200 rounded-lg p-4">
        <div className="animate-pulse space-y-3">
          <div className="flex items-center space-x-2">
            <div className="w-5 h-5 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-32"></div>
          </div>
          <div className="space-y-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-8 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const categorizedVariables = getVariablesByCategory()

  return (
    <div className="border border-gray-200 rounded-lg">
      {/* Header */}
      <div
        onClick={() => setExpanded(!expanded)}
        className="p-4 border-b border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Lock className="w-5 h-5 text-blue-600" />
            <h4 className="font-medium text-gray-900">Smart Lock Variables</h4>
            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
              {Object.keys(variables).length} available
            </span>
          </div>
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          )}
        </div>
      </div>

      {expanded && (
        <div className="p-4 space-y-4">
          {/* Description */}
          <div className="bg-blue-50 border border-blue-200 rounded p-3">
            <div className="flex items-start space-x-2">
              <Info className="w-4 h-4 text-blue-600 mt-0.5" />
              <div>
                <p className="text-sm text-blue-800">
                  Smart lock variables automatically adapt based on each property's configuration:
                </p>
                <ul className="text-xs text-blue-700 mt-1 space-y-1">
                  <li>• TTLock properties: Show generated passcodes</li>
                  <li>• Manual smart locks: Show host-entered passcodes</li>
                  <li>• Traditional access: Show custom instructions</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Variable Categories */}
          {Object.entries(categorizedVariables).map(([category, categoryVariables]) => (
            <div key={category} className="space-y-2">
              <h5 className="text-sm font-medium text-gray-700 border-b border-gray-200 pb-1">
                {category}
              </h5>
              <div className="grid grid-cols-1 gap-2">
                {Object.entries(categoryVariables).map(([varName, description]) => (
                  <div
                    key={varName}
                    className="flex items-center justify-between p-2 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <code className="text-sm font-mono text-blue-600 bg-blue-100 px-2 py-1 rounded">
                          {`{${varName}}`}
                        </code>
                      </div>
                      <p className="text-xs text-gray-600 mt-1 truncate">
                        {description}
                      </p>
                    </div>
                    <div className="flex items-center space-x-1 ml-2">
                      <button
                        onClick={() => copyVariable(varName)}
                        className="p-1 text-gray-400 hover:text-gray-600 rounded"
                        title="Copy variable"
                      >
                        <Copy className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => insertVariable(varName)}
                        className="p-1 text-blue-600 hover:text-blue-800 rounded"
                        title="Insert variable"
                      >
                        <Plus className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Quick Insert Examples */}
          <div className="border-t border-gray-200 pt-4">
            <h5 className="text-sm font-medium text-gray-700 mb-2">Common Examples</h5>
            <div className="space-y-2">
              <button
                onClick={() => insertVariable('lock_passcode_section')}
                className="w-full text-left p-2 bg-green-50 border border-green-200 rounded text-sm hover:bg-green-100 transition-colors"
              >
                <code className="text-green-700 font-mono">{'{lock_passcode_section}'}</code>
                <span className="text-green-600 ml-2">- Complete passcode section (recommended)</span>
              </button>

              <button
                onClick={() => insertVariable('smart_lock_passcode')}
                className="w-full text-left p-2 bg-orange-50 border border-orange-200 rounded text-sm hover:bg-orange-100 transition-colors"
              >
                <code className="text-orange-700 font-mono">{'{smart_lock_passcode}'}</code>
                <span className="text-orange-600 ml-2">- Just the passcode number</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}