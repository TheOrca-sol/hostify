import React, { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import { toast } from './Toaster'
import { Mail, Send, Clock, RefreshCw, XCircle } from 'lucide-react'

export default function CommunicationCenter() {
  const [loading, setLoading] = useState(true)
  const [scheduledMessages, setScheduledMessages] = useState([])
  const [error, setError] = useState(null)
  const [actionInProgress, setActionInProgress] = useState(null) // Tracks message ID for actions

  const loadScheduledMessages = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.getScheduledMessages()

      if (response.success) {
        // Filter for only messages that are still scheduled
        setScheduledMessages(response.messages.filter(m => m.status === 'scheduled') || [])
      } else {
        setError(response.error || 'Failed to load scheduled messages.')
        toast.error(response.error || 'Failed to load scheduled messages.')
      }
    } catch (err) {
      setError('An unexpected error occurred.')
      toast.error('An unexpected error occurred.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadScheduledMessages()
  }, [loadScheduledMessages])

  const handleAction = async (action, messageId, successMsg) => {
    setActionInProgress(messageId)
    try {
      const response = await action(messageId)
      if (response.success) {
        toast.success(successMsg)
        loadScheduledMessages() // Refresh the list
      } else {
        toast.error(response.error || `Failed to perform action.`)
      }
    } catch (error) {
      toast.error(`An error occurred while performing the action.`)
    } finally {
      setActionInProgress(null)
    }
  }

  const MessageCard = ({ msg }) => (
    <div className="bg-white p-4 border border-gray-200 rounded-lg">
      <div className="flex justify-between items-start">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-blue-600">{msg.template?.name || 'Scheduled Message'}</p>
          <p className="text-sm text-gray-700">To: {msg.guest?.full_name || 'Guest'}</p>
          <p className="text-xs text-gray-500">For: {msg.reservation?.property?.name || 'Property'}</p>
        </div>
        <div className="text-right flex-shrink-0">
          <p className="text-sm font-medium text-gray-800">
            {new Date(msg.scheduled_for).toLocaleDateString()}
          </p>
          <p className="text-xs text-gray-500">
            at {new Date(msg.scheduled_for).toLocaleTimeString()}
          </p>
        </div>
      </div>
      <div className="mt-2 p-3 bg-gray-50 rounded text-sm text-gray-600">
        {msg.template?.content.substring(0, 150)}...
      </div>
      <div className="mt-3 flex justify-end space-x-2">
        <button
          onClick={() => handleAction(api.cancelScheduledMessage, msg.id, 'Message cancelled.')}
          disabled={actionInProgress === msg.id}
          className="px-3 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          <XCircle className="h-4 w-4 inline mr-1" /> Cancel
        </button>
        <button
          onClick={() => handleAction(api.sendScheduledMessage, msg.id, 'Message sent successfully!')}
          disabled={actionInProgress === msg.id}
          className="px-3 py-1 text-xs font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
        >
          <Send className="h-4 w-4 inline mr-1" /> Send Now
        </button>
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-gray-900 flex items-center">
          <Clock className="h-5 w-5 mr-2 text-gray-500" />
          Scheduled Messages
        </h2>
        <button onClick={loadScheduledMessages} disabled={loading} className="text-sm font-medium text-blue-600 hover:text-blue-800">
          <RefreshCw className={`h-4 w-4 inline mr-1 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : error ? (
        <div className="text-center py-12 text-red-500">{error}</div>
      ) : scheduledMessages.length === 0 ? (
        <div className="text-center py-12">No messages are currently scheduled.</div>
      ) : (
        <div className="space-y-4">
          {scheduledMessages.map(msg => <MessageCard key={msg.id} msg={msg} />)}
        </div>
      )}
    </div>
  )
}