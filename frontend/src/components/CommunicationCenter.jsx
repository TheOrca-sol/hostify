import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { toast } from './Toaster'
import { Mail, FileText, Send, AlertCircle, CheckCircle, Clock, RefreshCw } from 'lucide-react'

export default function CommunicationCenter() {
  const [loading, setLoading] = useState(true)
  const [pendingMessages, setPendingMessages] = useState([])
  const [sentMessages, setSentMessages] = useState([])
  const [pendingContracts, setPendingContracts] = useState([])
  const [activeTab, setActiveTab] = useState('pending')
  const [sendingMessage, setSendingMessage] = useState(null)

  useEffect(() => {
    loadCommunicationData()
  }, [])

  const loadCommunicationData = async () => {
    try {
      setLoading(true)
      const [messagesRes, contractsRes] = await Promise.all([
        api.getScheduledMessages(), // No reservation_id needed
        api.getPendingContracts()
      ])

      // Handle messages
      if (messagesRes.success) {
        const { pending, sent } = (messagesRes.messages || []).reduce((acc, msg) => {
          if (msg.status === 'scheduled') {
            acc.pending.push(msg)
          } else {
            acc.sent.push(msg)
          }
          return acc
        }, { pending: [], sent: [] })

        setPendingMessages(pending)
        setSentMessages(sent)
      } else {
        toast.error(messagesRes.error || 'Failed to load messages')
      }

      // Handle contracts
      if (contractsRes.success) {
        setPendingContracts(contractsRes.contracts || [])
      } else {
        toast.error(contractsRes.error || 'Failed to load contracts')
      }
    } catch (error) {
      console.error('Error loading communication data:', error)
      toast.error('Failed to load communication data. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleSendMessage = async (messageId) => {
    try {
      setSendingMessage(messageId)
      const response = await api.sendScheduledMessage(messageId)
      if (response.success) {
        toast.success('Message sent successfully')
        loadCommunicationData()  // Refresh data
      } else {
        toast.error(response.error || 'Failed to send message')
      }
    } catch (error) {
      console.error('Error sending message:', error)
      toast.error('Failed to send message')
    } finally {
      setSendingMessage(null)
    }
  }

  const handleCancelMessage = async (messageId) => {
    try {
      const response = await api.cancelScheduledMessage(messageId)
      if (response.success) {
        toast.success('Message cancelled')
        loadCommunicationData()  // Refresh data
      } else {
        toast.error(response.error || 'Failed to cancel message')
      }
    } catch (error) {
      console.error('Error cancelling message:', error)
      toast.error('Failed to cancel message')
    }
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-2 text-sm text-gray-500">Loading communication center...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-gray-900">Communication Center</h2>
        <div className="flex items-center space-x-4">
          <button
            onClick={loadCommunicationData}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <RefreshCw className="-ml-0.5 mr-2 h-4 w-4" /> Refresh
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('pending')}
            className={`${
              activeTab === 'pending'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
          >
            <Clock className="h-5 w-5 mr-2" />
            Pending ({pendingMessages.length + pendingContracts.length})
          </button>
          <button
            onClick={() => setActiveTab('sent')}
            className={`${
              activeTab === 'sent'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
          >
            <CheckCircle className="h-5 w-5 mr-2" />
            Sent History ({sentMessages.length})
          </button>
        </nav>
      </div>

      {/* Content Area */}
      <div className="space-y-6">
        {activeTab === 'pending' && (
          <>
            {/* Pending Messages */}
            {pendingMessages.length > 0 && (
              <div className="bg-white shadow rounded-lg divide-y divide-gray-200">
                <div className="p-4 bg-gray-50 rounded-t-lg">
                  <h3 className="text-lg font-medium text-gray-900 flex items-center">
                    <Mail className="h-5 w-5 mr-2 text-gray-500" />
                    Pending Messages
                  </h3>
                </div>
                <div className="divide-y divide-gray-200">
                  {pendingMessages.map((message) => (
                    <div key={message.id} className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900">
                            {message.template?.name || 'Message'}
                          </h4>
                          <p className="text-sm text-gray-500">
                            To: {message.guest?.full_name || 'Guest'} ({message.guest?.email})
                          </p>
                          <p className="text-sm text-gray-500">
                            Scheduled: {new Date(message.scheduled_for).toLocaleString()}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleSendMessage(message.id)}
                            disabled={sendingMessage === message.id}
                            className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                          >
                            {sendingMessage === message.id ? (
                              <>
                                <RefreshCw className="animate-spin -ml-1 mr-2 h-4 w-4" />
                                Sending...
                              </>
                            ) : (
                              <>
                                <Send className="-ml-1 mr-2 h-4 w-4" />
                                Send Now
                              </>
                            )}
                          </button>
                          <button
                            onClick={() => handleCancelMessage(message.id)}
                            className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Pending Contracts */}
            {pendingContracts.length > 0 && (
              <div className="bg-white shadow rounded-lg divide-y divide-gray-200">
                <div className="p-4 bg-gray-50 rounded-t-lg">
                  <h3 className="text-lg font-medium text-gray-900 flex items-center">
                    <FileText className="h-5 w-5 mr-2 text-gray-500" />
                    Pending Contracts
                  </h3>
                </div>
                <div className="divide-y divide-gray-200">
                  {pendingContracts.map((contract) => (
                    <div key={contract.id} className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900">
                            Contract for {contract.guest?.full_name || 'Guest'}
                          </h4>
                          <p className="text-sm text-gray-500">
                            Status: {contract.contract_status}
                          </p>
                          <p className="text-sm text-gray-500">
                            Generated: {new Date(contract.created_at).toLocaleString()}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => window.open(`/contracts/${contract.id}`, '_blank')}
                            className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                          >
                            <FileText className="-ml-1 mr-2 h-4 w-4" />
                            View Contract
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {pendingMessages.length === 0 && pendingContracts.length === 0 && (
              <div className="text-center py-12">
                <div className="bg-gray-100 p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                  <CheckCircle className="h-8 w-8 text-gray-400" />
                </div>
                <h3 className="text-lg font-medium text-gray-900">No Pending Items</h3>
                <p className="mt-2 text-sm text-gray-500">
                  All messages and contracts have been sent or processed.
                </p>
              </div>
            )}
          </>
        )}

        {activeTab === 'sent' && (
          <div className="bg-white shadow rounded-lg divide-y divide-gray-200">
            <div className="p-4 bg-gray-50 rounded-t-lg">
              <h3 className="text-lg font-medium text-gray-900">Message History</h3>
            </div>
            {sentMessages.length > 0 ? (
              <div className="divide-y divide-gray-200">
                {sentMessages.map((message) => (
                  <div key={message.id} className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">
                          {message.template?.name || 'Message'}
                        </h4>
                        <p className="text-sm text-gray-500">
                          To: {message.guest?.full_name || 'Guest'} ({message.guest?.email})
                        </p>
                        <p className="text-sm text-gray-500">
                          Sent: {new Date(message.sent_at).toLocaleString()}
                        </p>
                        <div className="mt-1 flex items-center">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            message.delivery_status === 'delivered'
                              ? 'bg-green-100 text-green-800'
                              : message.delivery_status === 'failed'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {message.delivery_status}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-6 text-center">
                <p className="text-sm text-gray-500">No messages have been sent yet.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
} 