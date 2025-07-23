import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { toast } from './Toaster';
import { Send, MessageSquare, UserPlus, Trash2, ChevronDown, ChevronUp, Edit, FileText } from 'lucide-react';
import GuestEditForm from './GuestEditForm';

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
  const [editingGuest, setEditingGuest] = useState(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalGuests, setTotalGuests] = useState(0);
  const [perPage] = useState(10);

  const fetchGuests = useCallback(async (page = 1) => {
    try {
      setLoading(true);
      const response = await api.getGuests({ 
        property_id: propertyId,
        page: page,
        per_page: perPage
      });
      if (response.success) {
        setGuests(response.guests || []);
        setCurrentPage(response.current_page || 1);
        setTotalPages(response.pages || 1);
        setTotalGuests(response.total || 0);
      } else {
        setError(response.error || 'Failed to load guests.');
      }
    } catch (err) {
      setError('An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  }, [propertyId, perPage]);

  useEffect(() => {
    fetchGuests(1);
  }, [fetchGuests]);

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      fetchGuests(newPage);
    }
  };

  const handleSendVerification = async (guestId) => {
    try {
      const result = await api.sendVerificationLink(guestId);
      if (result.success) {
        toast.success('Verification link sent!');
        fetchGuests(currentPage); // Refresh current page
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

  const handleGuestUpdated = (updatedGuest) => {
    setGuests(prevGuests => 
      prevGuests.map(guest => 
        guest.id === updatedGuest.id ? updatedGuest : guest
      )
    );
    toast.success('Guest information updated successfully!');
  };

  const handleViewDocument = async (guest) => {
    if (!guest.id_document_path) {
      toast.error('No document uploaded for this guest');
      return;
    }

    try {
      const result = await api.viewGuestDocument(guest.id);
      if (!result.success) {
        toast.error(result.error || 'Failed to view document');
      }
    } catch (error) {
      toast.error('Failed to view document');
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
          {totalGuests > 0 && (
            <span className="ml-2 text-sm text-gray-500">
              ({totalGuests} total guest{totalGuests !== 1 ? 's' : ''})
            </span>
          )}
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
                    {guest.email && (
                      <div className="text-xs text-gray-400">{guest.email}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{guest.property?.name || 'Unknown Property'}</div>
                    <div className="text-sm text-gray-500">
                      {guest.check_in ? new Date(guest.check_in).toLocaleDateString() : 'N/A'} - {guest.check_out ? new Date(guest.check_out).toLocaleDateString() : 'N/A'}
                    </div>
                    {guest.reservation?.platform && (
                      <div className="text-xs text-gray-400">{guest.reservation.platform}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(guest).color}`}>
                      {getStatusBadge(guest).label}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end items-center space-x-2">
                      <button
                        onClick={() => setEditingGuest(guest)}
                        className="text-blue-600 hover:text-blue-900"
                        title="Edit Guest"
                      >
                        <Edit size={18} />
                      </button>
                      {guest.id_document_path && (
                        <button
                          onClick={() => handleViewDocument(guest)}
                          className="text-green-600 hover:text-green-900"
                          title="View Document"
                        >
                          <FileText size={18} />
                        </button>
                      )}
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
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Personal Information */}
                        <div className="space-y-2">
                          <h4 className="font-semibold text-gray-900 text-sm">Personal Information</h4>
                          <div className="space-y-1 text-sm">
                            <div><span className="font-medium text-gray-700">Full Name:</span> {guest.full_name || 'N/A'}</div>
                            <div><span className="font-medium text-gray-700">Email:</span> {guest.email || 'N/A'}</div>
                            <div><span className="font-medium text-gray-700">Phone:</span> {guest.phone || 'N/A'}</div>
                            <div><span className="font-medium text-gray-700">Nationality:</span> {guest.nationality || 'N/A'}</div>
                            <div><span className="font-medium text-gray-700">Birthdate:</span> {guest.birthdate ? new Date(guest.birthdate).toLocaleDateString() : 'N/A'}</div>
                            <div><span className="font-medium text-gray-700">Address:</span> {guest.address || 'N/A'}</div>
                          </div>
                        </div>
                        
                        {/* Document & Verification Information */}
                        <div className="space-y-2">
                          <h4 className="font-semibold text-gray-900 text-sm">Document & Verification</h4>
                          <div className="space-y-1 text-sm">
                            <div><span className="font-medium text-gray-700">ID/Passport:</span> {guest.cin_or_passport || 'N/A'}</div>
                            <div><span className="font-medium text-gray-700">Document Type:</span> {guest.document_type || 'N/A'}</div>
                            <div><span className="font-medium text-gray-700">Verification Status:</span> 
                              <span className={`ml-1 px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(guest).color}`}>
                                {getStatusBadge(guest).label}
                              </span>
                            </div>
                            {guest.verified_at && (
                              <div><span className="font-medium text-gray-700">Verified At:</span> {new Date(guest.verified_at).toLocaleString()}</div>
                            )}
                            {guest.verification_link_sent && (
                              <div><span className="font-medium text-gray-700">Verification Link:</span> <span className="text-green-600">Sent</span></div>
                            )}
                          </div>
                        </div>
                        
                        {/* Reservation Information */}
                        <div className="space-y-2">
                          <h4 className="font-semibold text-gray-900 text-sm">Reservation Details</h4>
                          <div className="space-y-1 text-sm">
                            <div><span className="font-medium text-gray-700">Property:</span> {guest.property?.name || 'N/A'}</div>
                            <div><span className="font-medium text-gray-700">Check-in:</span> {guest.check_in ? new Date(guest.check_in).toLocaleDateString() : 'N/A'}</div>
                            <div><span className="font-medium text-gray-700">Check-out:</span> {guest.check_out ? new Date(guest.check_out).toLocaleDateString() : 'N/A'}</div>
                            {guest.reservation?.platform && (
                              <div><span className="font-medium text-gray-700">Platform:</span> {guest.reservation.platform}</div>
                            )}
                            {guest.reservation?.external_id && (
                              <div><span className="font-medium text-gray-700">Booking ID:</span> {guest.reservation.external_id}</div>
                            )}
                          </div>
                        </div>
                        
                        {/* System Information */}
                        <div className="space-y-2">
                          <h4 className="font-semibold text-gray-900 text-sm">System Information</h4>
                          <div className="space-y-1 text-sm">
                            <div><span className="font-medium text-gray-700">Guest ID:</span> <span className="font-mono text-xs">{guest.id}</span></div>
                            <div><span className="font-medium text-gray-700">Created:</span> {guest.created_at ? new Date(guest.created_at).toLocaleString() : 'N/A'}</div>
                            {guest.id_document_path && (
                              <div><span className="font-medium text-gray-700">Document Uploaded:</span> <span className="text-green-600">Yes</span></div>
                            )}
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="px-6 py-4 border-t bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing {((currentPage - 1) * perPage) + 1} to {Math.min(currentPage * perPage, totalGuests)} of {totalGuests} guests
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className={`px-3 py-1 text-sm font-medium rounded-md ${
                  currentPage === 1
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                Previous
              </button>
              
              {/* Page Numbers */}
              <div className="flex items-center space-x-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }
                  
                  return (
                    <button
                      key={pageNum}
                      onClick={() => handlePageChange(pageNum)}
                      className={`px-3 py-1 text-sm font-medium rounded-md ${
                        currentPage === pageNum
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>
              
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className={`px-3 py-1 text-sm font-medium rounded-md ${
                  currentPage === totalPages
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}
      
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
      {editingGuest && (
        <GuestEditForm
          guest={editingGuest}
          onClose={() => setEditingGuest(null)}
          onGuestUpdated={handleGuestUpdated}
        />
      )}
    </div>
  );
}