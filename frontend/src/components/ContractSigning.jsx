import React, { useState, useRef, useEffect } from 'react'
import SignaturePad from 'react-signature-canvas'
import { api } from '../services/api'
import { useParams, useNavigate } from 'react-router-dom'
import { FileDown, RefreshCw, CheckCircle, AlertCircle } from 'lucide-react'

export default function ContractSigning({ mode = 'sign' }) {
  const { contractId, token } = useParams()
  const navigate = useNavigate()
  const [contract, setContract] = useState(null)
  const [isSigning, setIsSigning] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const [loadingContract, setLoadingContract] = useState(true)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const signaturePadRef = useRef()

  useEffect(() => {
    loadContract()
  }, [contractId, token])

  const loadContract = async () => {
    try {
      setLoadingContract(true)
      setError('')
      setSuccessMessage('')
      
      const response = token 
        ? await api.getContractByToken(token)
        : await api.getContract(contractId)
      
      if (response.success) {
        setContract(response.contract)
        if (response.contract.status === 'signed') {
          setSuccessMessage('This contract has already been signed.')
        }
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
    if (!contractId) return
    
    try {
      setIsDownloading(true)
      setError('')
      const response = await api.downloadContract(contractId)
      
      if (response.success) {
        const link = document.createElement('a')
        link.href = response.url
        link.download = `contract-${contract.id}.pdf`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(response.url) // Clean up
      } else {
        throw new Error(response.error || 'Failed to download contract')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setIsDownloading(false)
    }
  }
  
  const handleSign = async () => {
    try {
      if (!signaturePadRef.current || signaturePadRef.current.isEmpty()) {
        setError('Please provide your signature before signing.')
        return
      }
      
      setError('')
      setSuccessMessage('')
      setIsSigning(true)
      
      const signatureData = {
        signature_data: {
          signature: signaturePadRef.current.toDataURL('image/png'),
          timestamp: new Date().toISOString()
        }
      }
      
      const result = token
        ? await api.signContractByToken(token, signatureData)
        : await api.signContract(contractId, signatureData.signature_data)
      
      if (result.success) {
        setSuccessMessage('Contract signed successfully! You will be redirected shortly.')
        setTimeout(() => {
          if (token) {
            navigate('/contract-signed-success')
          } else {
            loadContract() // Reload contract for host view
          }
        }, 3000)
      } else {
        throw new Error(result.error || 'Failed to sign contract')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setIsSigning(false)
    }
  }

  if (loadingContract) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-500 mr-3" />
            <div>
              <h2 className="text-lg font-semibold text-red-800 mb-1">Error Loading Contract</h2>
              <p className="text-red-700">{error}</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!contract) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-yellow-500 mr-3" />
            <div>
              <h2 className="text-lg font-semibold text-yellow-800 mb-1">Contract Not Found</h2>
              <p className="text-yellow-700">The contract you're looking for could not be found or may have expired.</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="bg-gray-50 px-6 py-4 border-b">
          <h1 className="text-2xl font-bold text-gray-900">Rental Contract</h1>
          <div className="mt-2 flex flex-wrap gap-4 text-sm text-gray-600">
            <span>Guest: {contract.guest_name}</span>
            <span>Property: {contract.property_name}</span>
            <span>Check-in: {contract.check_in_date}</span>
            <span>Check-out: {contract.check_out_date}</span>
          </div>
        </div>

        {/* Success Message */}
        {successMessage && (
          <div className="p-4 bg-green-50 border-b border-green-200">
            <div className="flex items-center">
              <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
              <p className="text-sm font-medium text-green-800">{successMessage}</p>
            </div>
          </div>
        )}

        {/* Contract Content */}
        <div className="p-6">
          <div className="prose max-w-none">
            <div 
              className="whitespace-pre-wrap text-gray-800 leading-relaxed"
              dangerouslySetInnerHTML={{ __html: contract.content.replace(/\n/g, '<br/>') }}
            />
          </div>
        </div>

        {/* Signature Section */}
        {mode === 'sign' && contract.status !== 'signed' && (
          <div className="border-t bg-gray-50 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Digital Signature</h3>
            
            <div className="bg-white border rounded-lg p-4">
              <SignaturePad
                ref={signaturePadRef}
                canvasProps={{
                  className: 'w-full h-48 border border-gray-300 rounded'
                }}
              />
              
              <div className="mt-4 flex items-center space-x-4">
                <button
                  onClick={handleClear}
                  type="button"
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                >
                  Clear Signature
                </button>
                
                <button
                  onClick={handleSign}
                  disabled={isSigning}
                  type="button"
                  className="px-6 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  {isSigning ? (
                    <>
                      <RefreshCw className="animate-spin -ml-1 mr-2 h-4 w-4 inline" />
                      Signing...
                    </>
                  ) : (
                    'Sign Contract'
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Download Section */}
        {contract.status === 'signed' && (
          <div className="border-t bg-green-50 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-green-800">Contract Signed Successfully!</h3>
                <p className="text-green-700 mt-1">Your contract has been signed and is ready for download.</p>
              </div>
              
              <button
                onClick={handleDownload}
                disabled={isDownloading}
                type="button"
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              >
                <FileDown className="w-4 h-4 mr-2" />
                {isDownloading ? 'Downloading...' : 'Download PDF'}
              </button>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && !successMessage && (
          <div className="border-t bg-red-50 p-6">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-red-500 mr-3" />
              <div className="text-red-800">
                <h3 className="font-semibold">Error</h3>
                <p>{error}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}