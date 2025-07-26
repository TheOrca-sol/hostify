import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Download, Eye, Clock, CheckCircle, XCircle, Send, AlertCircle } from 'lucide-react'

export default function ContractList() {
  const [contracts, setContracts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sendingContract, setSendingContract] = useState(null)
  const [sendError, setSendError] = useState(null)
  const [sendSuccess, setSendSuccess] = useState(null)
  const [regeneratingPdf, setRegeneratingPdf] = useState(null)

  useEffect(() => {
    loadContracts()
  }, [])

  const loadContracts = async () => {
    try {
      setLoading(true)
      const response = await api.getContracts()
      if (response.success) {
        setContracts(response.contracts)
      } else {
        setError(response.error || 'Failed to load contracts')
      }
    } catch (err) {
      setError('Failed to load contracts')
    } finally {
      setLoading(false)
    }
  }

  const handleSendContract = async (guestId) => {
    try {
      setSendingContract(guestId)
      setSendError(null)
      setSendSuccess(null)
      
      const response = await api.generateContractAndScheduleSms(guestId)
      if (response.success) {
        // Reload contracts to show the new one
        await loadContracts()
        setSendSuccess(`Contract sent successfully to guest ${guestId}!`)
      } else {
        setSendError(`Failed to send contract: ${response.error}`)
      }
    } catch (err) {
      setSendError(`Error sending contract: ${err.message || 'Unknown error'}`)
    } finally {
      setSendingContract(null)
    }
  }

  const handleRegeneratePdf = async (contractId) => {
    try {
      setRegeneratingPdf(contractId)
      setSendError(null)
      setSendSuccess(null)
      
      const response = await api.regenerateContractPdf(contractId)
      if (response.success) {
        setSendSuccess('PDF regenerated successfully with signature!')
      } else {
        setSendError(`Failed to regenerate PDF: ${response.error}`)
      }
    } catch (err) {
      setSendError(`Error regenerating PDF: ${err.message || 'Unknown error'}`)
    } finally {
      setRegeneratingPdf(null)
    }
  }

  const getStatusBadge = (contract) => {
    switch (contract.contract_status) {
      case 'generated':
        return { label: 'Generated', color: 'bg-blue-100 text-blue-800' }
      case 'sent_for_signing':
        return { label: 'Sent for Signing', color: 'bg-yellow-100 text-yellow-800' }
      case 'signed':
        return { label: 'Signed', color: 'bg-green-100 text-green-800' }
      case 'expired':
        return { label: 'Expired', color: 'bg-red-100 text-red-800' }
      default:
        return { label: 'Unknown', color: 'bg-gray-100 text-gray-800' }
    }
  }

  const getStatusIcon = (contract) => {
    switch (contract.contract_status) {
      case 'generated':
        return <Clock className="h-4 w-4" />
      case 'sent_for_signing':
        return <Eye className="h-4 w-4" />
      case 'signed':
        return <CheckCircle className="h-4 w-4" />
      case 'expired':
        return <XCircle className="h-4 w-4" />
      default:
        return <Clock className="h-4 w-4" />
    }
  }

  const handleDownloadContract = async (contractId) => {
    try {
      const response = await api.downloadContract(contractId)
      if (response.success) {
        // Create download link from the URL
        const a = document.createElement('a')
        a.href = response.url
        a.download = `contract_${contractId}.pdf`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        // Clean up the URL
        URL.revokeObjectURL(response.url)
      } else {
        console.error('Failed to download contract:', response.error)
        alert('Failed to download contract: ' + (response.error || 'Unknown error'))
      }
    } catch (err) {
      console.error('Error downloading contract:', err)
      alert('Error downloading contract: ' + err.message)
    }
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-2 text-gray-600">Loading contracts...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error}</p>
        <button
          onClick={loadContracts}
          className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    )
  }

  if (contracts.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">No contracts found.</p>
        <p className="text-sm text-gray-500 mt-2">
          Contracts are automatically generated when guests complete verification.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-gray-900">Contracts</h2>
        <button
          onClick={loadContracts}
          className="text-sm font-medium text-blue-600 hover:text-blue-800"
        >
          Refresh
        </button>
      </div>

      {/* Error Message */}
      {sendError && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertCircle className="h-5 w-5 text-red-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error sending contract</h3>
              <div className="mt-2 text-sm text-red-700">
                <p className="break-all">{sendError}</p>
              </div>
              <div className="mt-4">
                <button
                  type="button"
                  onClick={() => setSendError(null)}
                  className="bg-red-50 px-2 py-1.5 rounded-md text-sm font-medium text-red-800 hover:bg-red-100"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Success Message */}
      {sendSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <CheckCircle className="h-5 w-5 text-green-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">Success!</h3>
              <div className="mt-2 text-sm text-green-700">
                <p>{sendSuccess}</p>
              </div>
              <div className="mt-4">
                <button
                  type="button"
                  onClick={() => setSendSuccess(null)}
                  className="bg-green-50 px-2 py-1.5 rounded-md text-sm font-medium text-green-800 hover:bg-green-100"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {contracts.map((contract) => (
            <li key={contract.id}>
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="h-8 w-8 rounded-full bg-gray-300 flex items-center justify-center">
                        {getStatusIcon(contract)}
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="flex items-center">
                        <p className="text-sm font-medium text-gray-900">
                          {contract.guest?.full_name || 'Unknown Guest'}
                        </p>
                        <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(contract).color}`}>
                          {getStatusBadge(contract).label}
                        </span>
                      </div>
                      <div className="mt-1 flex items-center text-sm text-gray-500">
                        <p>
                          {contract.property?.name || 'Unknown Property'} • 
                          {contract.reservation?.check_in && ` Check-in: ${new Date(contract.reservation.check_in).toLocaleDateString()}`}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {/* Send Contract Button - only show if contract is not signed */}
                    {contract.contract_status !== 'signed' && contract.guest?.id && (
                      <button
                        onClick={() => handleSendContract(contract.guest.id)}
                        disabled={sendingContract === contract.guest.id}
                        className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                      >
                        {sendingContract === contract.guest.id ? (
                          <>
                            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                            Sending...
                          </>
                        ) : (
                          <>
                            <Send className="h-3 w-3 mr-1" />
                            Send Contract
                          </>
                        )}
                      </button>
                    )}
                    
                    {/* Download Button - only show if contract is signed */}
                    {contract.contract_status === 'signed' && contract.signed_pdf_path && (
                      <button
                        onClick={() => handleDownloadContract(contract.id)}
                        className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                      >
                        <Download className="h-3 w-3 mr-1" />
                        Download
                      </button>
                    )}
                    
                    {/* Regenerate PDF Button - only show if contract is signed */}
                    {contract.contract_status === 'signed' && contract.signed_pdf_path && (
                      <button
                        onClick={() => handleRegeneratePdf(contract.id)}
                        disabled={regeneratingPdf === contract.id}
                        className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                      >
                        {regeneratingPdf === contract.id ? (
                          <>
                            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                            Regenerating...
                          </>
                        ) : (
                          <>
                            <Download className="h-3 w-3 mr-1" />
                            Regenerate PDF
                          </>
                        )}
                      </button>
                    )}
                    
                    <div className="text-sm text-gray-500">
                      {contract.signed_at && `Signed: ${new Date(contract.signed_at).toLocaleDateString()}`}
                    </div>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
} 