import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { toast } from './Toaster';
import { Send, MessageSquare, UserPlus, Trash2, ChevronDown, ChevronUp } from 'lucide-react';

// Modal for sending a manual message
const ManualSendModal = ({ guest, onClose, onSend }) => {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        setLoading(true);
        const response = await api.getManualMessageTemplates();
        if (response.success) {
          setTemplates(response.templates || []);
        } else {
          toast.error(response.error || 'Failed to load message templates.');
        }
      } catch (error) {
        toast.error('An unexpected error occurred while fetching templates.');
      } finally {
        setLoading(false);
      }
    };
    fetchTemplates();
  }, []);

  const handleSend = () => {
    if (!selectedTemplate) {
      toast.error('Please select a template to send.');
      return;
    }
    onSend(selectedTemplate, guest.reservation_id);
  };

  const selectedTemplateContent = templates.find(t => t.id === selectedTemplate)?.content || '';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-lg">
        <h2 className="text-xl font-bold mb-4">Send Manual Message to {guest.full_name}</h2>
        {loading ? (
          <div>Loading templates...</div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Select Template</label>
              <select
                value={selectedTemplate}
                onChange={(e) => setSelectedTemplate(e.target.value)}
                className="w-full border rounded-lg px-3 py-2"
              >
                <option value="">-- Choose a template --</option>
                {templates.map(template => (
                  <option key={template.id} value={template.id}>
                    {template.name}
                  </option>
                ))}
              </select>
            </div>
            {selectedTemplateContent && (
              <div className="border p-3 rounded-md bg-gray-50">
                <h4 className="font-semibold text-sm mb-2">Message Preview:</h4>
                <p className="text-sm text-gray-600 whitespace-pre-wrap">{selectedTemplateContent}</p>
              </div>
            )}
          </div>
        )}
        <div className="flex justify-end gap-4 mt-6">
          <button type="button" onClick={onClose} className="px-4 py-2 border rounded-lg">Cancel</button>
          <button
            type="button"
            onClick={handleSend}
            disabled={loading || !selectedTemplate}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:bg-gray-400 flex items-center gap-2"
          >
            <Send size={16} />
            Send Now
          </button>
        </div>
      </div>
    </div>
  );
};

export default function GuestList({ propertyId, onAddGuest }) {
  const [guests, setGuests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedGuest, setExpandedGuest] = useState(null);
  const [isSendModalOpen, setIsSendModalOpen] = useState(false);
  const [sendingGuest, setSendingGuest] = useState(null);

  const fetchGuests = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.getGuests({ property_id: propertyId });
      if (response.success) {
        setGuests(response.guests || []);
      } else {
        setError(response.error || 'Failed to load guests.');
      }
    } catch (err) {
      setError('An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  }, [propertyId]);

  useEffect(() => {
    fetchGuests();
  }, [fetchGuests]);

  const handleSendVerification = async (guestId) => {
    try {
      const result = await api.sendVerificationLink(guestId);
      if (result.success) {
        toast.success('Verification link sent!');
        fetchGuests(); // Refresh to show updated status
      } else {
        toast.error(result.error || 'Failed to send verification link.');
      }
    } catch (error) {
      toast.error('An error occurred while sending the link.');
    }
  };

  const handleManualSend = async (templateId, reservationId) => {
    try {
      await api.sendManualMessage({ template_id: templateId, reservation_id: reservationId });
      toast.success('Message sent successfully!');
      setIsSendModalOpen(false);
      setSendingGuest(null);
    } catch (error) {
      toast.error(error.message || 'Failed to send message.');
    }
  };

  const getStatusBadge = (guest) => {
    switch (guest.verification_status) {
      case 'verified':
        return { label: 'Verified', color: 'bg-green-100 text-green-800' };
      case 'pending':
        return { label: 'Pending', color: 'bg-yellow-100 text-yellow-800' };
      case 'expired':
        return { label: 'Expired', color: 'bg-red-100 text-red-800' };
      default:
        return { label: guest.verification_status, color: 'bg-gray-100 text-gray-800' };
    }
  };

  if (loading) return <div>Loading guests...</div>;
  if (error) return <div className="text-red-500">Error: {error}</div>;

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold flex items-center">
          <MessageSquare className="mr-2" /> Guests
        </h2>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Guest</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reservation</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {guests.map(guest => (
              <React.Fragment key={guest.id}>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{guest.full_name || 'N/A'}</div>
                    <div className="text-sm text-gray-500">{guest.phone || 'No phone'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{guest.property?.name}</div>
                    <div className="text-sm text-gray-500">
                      {new Date(guest.check_in).toLocaleDateString()} - {new Date(guest.check_out).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(guest).color}`}>
                      {getStatusBadge(guest).label}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end items-center space-x-2">
                      {guest.verification_status === 'pending' && !guest.verification_link_sent && (
                        <button onClick={() => handleSendVerification(guest.id)} className="text-indigo-600 hover:text-indigo-900" title="Send Verification Link">
                          <Send size={18} />
                        </button>
                      )}
                      <button
                        onClick={() => {
                          setSendingGuest(guest);
                          setIsSendModalOpen(true);
                        }}
                        className="text-gray-600 hover:text-blue-600"
                        title="Send Manual Message"
                      >
                        <MessageSquare size={18} />
                      </button>
                      <button onClick={() => setExpandedGuest(expandedGuest === guest.id ? null : guest.id)} className="text-gray-500 hover:text-gray-700">
                        {expandedGuest === guest.id ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                      </button>
                    </div>
                  </td>
                </tr>
                {expandedGuest === guest.id && (
                  <tr>
                    <td colSpan="4" className="p-4 bg-gray-50">
                      {/* Expanded content can go here, e.g., guest details */}
                      <div>Email: {guest.email || 'N/A'}</div>
                      <div>Nationality: {guest.nationality || 'N/A'}</div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
      {isSendModalOpen && sendingGuest && (
        <ManualSendModal
          guest={sendingGuest}
          onClose={() => {
            setIsSendModalOpen(false);
            setSendingGuest(null);
          }}
          onSend={handleManualSend}
        />
      )}
    </div>
  );
}