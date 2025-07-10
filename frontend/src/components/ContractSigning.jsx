import React, { useState, useRef, useEffect } from 'react'
import SignaturePad from 'react-signature-canvas'
import { api } from '../services/api'
import { useParams } from 'react-router-dom'
import { FileDown, RefreshCw } from 'lucide-react'

export default function ContractSigning({ mode = 'sign' }) {
  const { contractId } = useParams()
  const [contract, setContract] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingContract, setLoadingContract] = useState(true)
  const [error, setError] = useState('')
  const signaturePadRef = useRef()

  useEffect(() => {
    loadContract()
  }, [contractId])

  const loadContract = async () => {
    try {
      setLoadingContract(true)
      setError('')
      const response = await api.getContract(contractId)
      if (response.success) {
        setContract(response.contract)
      } else {
        throw new Error(response.error || 'Failed to load contract')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingContract(false)
    }
  }
  
  const handleClear = () => {
    if (signaturePadRef.current) {
      signaturePadRef.current.clear()
    }
  }

  const handleDownload = async () => {
    try {
      setLoading(true)
      const response = await api.downloadContract(contractId)
      if (response.success) {
        // Create a download link
        const link = document.createElement('a')
        link.href = response.url
        link.download = `contract-${contractId}.pdf`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      } else {
        throw new Error(response.error || 'Failed to download contract')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }
  
  const handleSign = async () => {
    try {
      if (!signaturePadRef.current || signaturePadRef.current.isEmpty()) {
        throw new Error('Please provide your signature')
      }
      
      setError('')
      setLoading(true)
      
      // Get signature data
      const signatureData = {
        signature: signaturePadRef.current.toDataURL(),
        timestamp: new Date().toISOString()
      }
      
      // Sign contract
      const result = await api.signContract(contractId, signatureData)
      
      if (result.success) {
        setContract(result.contract)
      } else {
        throw new Error(result.error || 'Failed to sign contract')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loadingContract) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    )
  }

  if (!contract) {
    return (
      <div className="text-center py-12">
        <div className="bg-red-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900">Contract Not Found</h3>
        <p className="mt-2 text-sm text-gray-500">{error || 'The requested contract could not be found.'}</p>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Contract Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            {contract.property_name} - Rental Contract
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Guest: {contract.guest_name} • Generated: {new Date(contract.created_at).toLocaleDateString()}
          </p>
        </div>

        {mode === 'view' && (
          <button
            onClick={handleDownload}
            disabled={loading}
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <FileDown className="-ml-1 mr-2 h-4 w-4" />
            Download PDF
          </button>
        )}
      </div>
      
      {/* Contract Preview */}
      <div className="border border-gray-200 rounded-lg p-4">
        <iframe
          src={`/api/contracts/${contractId}/preview`}
          className="w-full h-96 border-0"
          title="Contract Preview"
        />
      </div>
      
      {/* Signature Area - Only show in sign mode and if not already signed */}
      {mode === 'sign' && !contract.signed_at && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">
            Sign Contract
          </h3>
          
          <div className="border border-gray-300 rounded-lg">
            <SignaturePad
              ref={signaturePadRef}
              canvasProps={{
                className: 'w-full h-48'
              }}
            />
          </div>
          
          <div className="flex justify-between">
            <button
              type="button"
              onClick={handleClear}
              className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900"
            >
              Clear Signature
            </button>
            
            <button
              type="button"
              onClick={handleSign}
              disabled={loading}
              className={`px-4 py-2 rounded-lg text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 ${
                loading ? 'opacity-75 cursor-not-allowed' : ''
              }`}
            >
              {loading ? (
                <>
                  <RefreshCw className="animate-spin -ml-1 mr-2 h-4 w-4" />
                  Signing...
                </>
              ) : (
                'Sign Contract'
              )}
            </button>
          </div>

          {/* Terms */}
          <div className="text-sm text-gray-500">
            By signing this contract, you agree to all terms and conditions stated in the document above.
            This signature will be legally binding.
          </div>
        </div>
      )}

      {/* Show signature info if contract is signed */}
      {contract.signed_at && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">
                Contract Signed
              </h3>
              <div className="mt-2 text-sm text-green-700">
                <p>Signed by {contract.guest_name} on {new Date(contract.signed_at).toLocaleString()}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
} 