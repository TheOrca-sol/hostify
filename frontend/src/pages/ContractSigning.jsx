import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { CheckCircle, AlertCircle, Download, PenTool } from 'lucide-react'

export default function ContractSigning() {
  const { token } = useParams()
  const navigate = useNavigate()
  const [contract, setContract] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [signing, setSigning] = useState(false)
  const [signatureData, setSignatureData] = useState('')
  const [showSignaturePad, setShowSignaturePad] = useState(false)

  useEffect(() => {
    loadContract()
  }, [token])

  const loadContract = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/contracts/sign/${token}`)
      const data = await response.json()
      
      if (data.success) {
        setContract(data.contract)
      } else {
        setError(data.error || 'Failed to load contract')
      }
    } catch (err) {
      setError('Failed to load contract')
    } finally {
      setLoading(false)
    }
  }

  const handleSignContract = async () => {
    if (!signatureData.trim()) {
      setError('Please provide your signature')
      return
    }

    try {
      setSigning(true)
      const response = await fetch(`/api/contracts/sign/${token}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          signature_data: {
            signature: signatureData,
            signed_at: new Date().toISOString(),
            ip_address: 'client-side'
          }
        })
      })

      const data = await response.json()
      
      if (data.success) {
        // Show success message and redirect
        setTimeout(() => {
          navigate('/contract-signed-success')
        }, 2000)
      } else {
        setError(data.error || 'Failed to sign contract')
      }
    } catch (err) {
      setError('Failed to sign contract')
    } finally {
      setSigning(false)
    }
  }

  const handleSignatureChange = (e) => {
    setSignatureData(e.target.value)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading contract...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Error</h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <button
              onClick={() => window.history.back()}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              Go Back
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Rental Contract</h1>
              <p className="text-gray-600 mt-1">
                Please review and sign your rental contract for {contract?.property_name}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Contract ID</p>
              <p className="font-mono text-sm">{contract?.id}</p>
            </div>
          </div>
        </div>

        {/* Contract Details */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Contract Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Guest Name</p>
              <p className="font-medium">{contract?.guest_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Property</p>
              <p className="font-medium">{contract?.property_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Check-in Date</p>
              <p className="font-medium">{contract?.check_in_date}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Check-out Date</p>
              <p className="font-medium">{contract?.check_out_date}</p>
            </div>
          </div>
        </div>

        {/* Contract Content */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Contract Terms</h2>
          <div className="prose max-w-none">
            <div className="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed">
              {contract?.content}
            </div>
          </div>
        </div>

        {/* Signature Section */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Digital Signature</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Full Name (as signature)
              </label>
              <input
                type="text"
                value={signatureData}
                onChange={handleSignatureChange}
                placeholder="Enter your full name to sign"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-yellow-400 mt-0.5" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-yellow-800">Important</h3>
                  <div className="mt-2 text-sm text-yellow-700">
                    <p>
                      By entering your name above and clicking "Sign Contract", you agree to be legally bound by the terms of this rental contract. 
                      This constitutes your digital signature and is legally equivalent to a handwritten signature.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-4">
          <button
            onClick={() => window.history.back()}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSignContract}
            disabled={!signatureData.trim() || signing}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {signing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Signing...</span>
              </>
            ) : (
              <>
                <CheckCircle className="h-4 w-4" />
                <span>Sign Contract</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
} 