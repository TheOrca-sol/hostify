// API configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

// API service functions
export const api = {
  // Get auth token from Firebase or OTC
  async getAuthToken() {
    // Check for OTC token first
    const otcToken = localStorage.getItem('otc_token')
    if (otcToken) {
      return otcToken
    }
    
    // Fall back to Firebase token
    const { getCurrentUser, getIdToken } = await import('./auth');
    const user = getCurrentUser();
    if (!user) throw new Error('User not authenticated');
    return await getIdToken();
  },

  // User Management
  async setupUserProfile(profileData) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/user/setup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(profileData)
      });
      return await response.json();
    } catch (error) {
      console.error('Error setting up user profile:', error);
      throw error;
    }
  },

  async getUserProfile() {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/user/profile`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting user profile:', error);
      throw error;
    }
  },

  // Property Management
  async createProperty(propertyData) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/properties`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(propertyData)
      });
      return await response.json();
    } catch (error) {
      console.error('Error creating property:', error);
      throw error;
    }
  },

  async getProperties() {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/properties`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting properties:', error);
      throw error;
    }
  },

  async getProperty(propertyId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/properties/${propertyId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting property:', error);
      throw error;
    }
  },

  async updateProperty(propertyId, updateData) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/properties/${propertyId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(updateData)
      });
      return await response.json();
    } catch (error) {
      console.error('Error updating property:', error);
      throw error;
    }
  },

  async getPropertyReservations(propertyId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/properties/${propertyId}/reservations`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting property reservations:', error);
      throw error;
    }
  },

  // Reservation Management (Updated from Bookings)
  async getReservations(params = {}) {
    try {
      const token = await this.getAuthToken();
      const url = new URL(`${API_BASE_URL}/reservations`);
      Object.keys(params).forEach(key => {
        if (params[key]) {
          url.searchParams.append(key, params[key]);
        }
      });
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting reservations:', error);
      throw error;
    }
  },

  async getReservation(reservationId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/reservations/${reservationId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting reservation:', error);
      throw error;
    }
  },

  async createReservation(reservationData) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/reservations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(reservationData)
      });
      return await response.json();
    } catch (error) {
      console.error('Error creating reservation:', error);
      throw error;
    }
  },

  async getUpcomingReservations() {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/reservations/upcoming`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting upcoming reservations:', error);
      throw error;
    }
  },

  async getCurrentReservations() {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/reservations/current`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting current reservations:', error);
      throw error;
    }
  },

  // Guest Management (Updated for Property-Centric)
  async getGuests(params = {}) {
    try {
      const token = await this.getAuthToken();
      const url = new URL(`${API_BASE_URL}/guests`);
      Object.keys(params).forEach(key => {
        if (params[key]) {
          url.searchParams.append(key, params[key]);
        }
      });

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting guests:', error);
      throw error;
    }
  },

  async getReservationGuests(reservationId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/reservations/${reservationId}/guests`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting reservation guests:', error);
      throw error;
    }
  },

  async addGuestToReservation(reservationId, guestData) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/reservations/${reservationId}/guests`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(guestData)
      });
      return await response.json();
    } catch (error) {
      console.error('Error adding guest to reservation:', error);
      throw error;
    }
  },

  async deleteGuest(guestId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/guests/${guestId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error deleting guest:', error);
      throw error;
    }
  },

  // Guest Management
  async getGuest(guestId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/guests/${guestId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting guest:', error);
      return { success: false, error: error.message };
    }
  },

  async updateGuest(guestId, guestData) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/guests/${guestId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(guestData)
      });
      return await response.json();
    } catch (error) {
      console.error('Error updating guest:', error);
      return { success: false, error: error.message };
    }
  },

  // Verification Links (Updated for Property-Centric)
  async sendVerificationLink(guestId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/verify/${guestId}/send-link`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error sending verification link:', error);
      throw error;
    }
  },

  async getVerificationLinks() {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/verification-links`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting verification links:', error);
      throw error;
    }
  },

  // Calendar Sync (Updated for Property-Specific)
  async syncPropertyCalendar(propertyId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/calendar/sync/${propertyId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error syncing property calendar:', error);
      throw error;
    }
  },

  async syncAllCalendars() {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/calendar/sync-all`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error syncing all calendars:', error);
      throw error;
    }
  },

  // Test iCal URL
  async testIcalUrl(icalUrl) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/calendar/test-ical/${encodeURIComponent(icalUrl)}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error testing iCal URL:', error);
      throw error;
    }
  },

  // Guest Verification Endpoints (Public - No Auth Required)
  async getVerificationInfo(token) {
    try {
      const response = await fetch(`${API_BASE_URL}/get-verification-info/${token}`);
      return await response.json();
    } catch (error) {
      console.error('Error getting verification info:', error);
      throw error;
    }
  },

  async uploadGuestDocument(verificationToken, file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/verify/${verificationToken}/upload`, {
        method: 'POST',
        body: formData
      });
      return await response.json();
    } catch (error) {
      console.error('Error uploading guest document:', error);
      throw error;
    }
  },

  async submitGuestVerification(verificationToken, guestData) {
    try {
      const response = await fetch(`${API_BASE_URL}/verify/${verificationToken}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(guestData)
      });
      return await response.json();
    } catch (error) {
      console.error('Error submitting guest verification:', error);
      throw error;
    }
  },

  // Legacy Methods (For Backward Compatibility - Will Show Migration Info)
  async createVerificationLink(linkData) {
    console.warn('⚠️ DEPRECATED: createVerificationLink() is deprecated. Use createVerificationLinkForReservation() instead.');
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/create-verification-link`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(linkData)
      });
      return await response.json();
    } catch (error) {
      console.error('Error creating verification link (legacy):', error);
      throw error;
    }
  },

  async getBookings() {
    console.warn('⚠️ DEPRECATED: getBookings() is deprecated. Use getReservations() instead.');
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/bookings`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting bookings (legacy):', error);
      throw error;
    }
  },

  async importIcal(icalData) {
    console.warn('⚠️ DEPRECATED: importIcal() is deprecated. Use syncPropertyCalendar() instead.');
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/calendar/import`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(icalData)
      });
      return await response.json();
    } catch (error) {
      console.error('Error importing iCal (legacy):', error);
      throw error;
    }
  },

  // Contract Management
  async getContractTemplates() {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/contract-templates`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting contract templates:', error);
      return { success: false, error: error.message };
    }
  },

  async createContractTemplate(templateData) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/contract-templates`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(templateData)
      });
      return await response.json();
    } catch (error) {
      console.error('Error creating contract template:', error);
      return { success: false, error: error.message };
    }
  },

  async updateContractTemplate(templateId, templateData) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/contract-templates/${templateId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(templateData)
      });
      return await response.json();
    } catch (error) {
      console.error('Error updating contract template:', error);
      return { success: false, error: error.message };
    }
  },

  async deleteContractTemplate(templateId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/contract-templates/${templateId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error deleting contract template:', error);
      return { success: false, error: error.message };
    }
  },

  async generateContractAndScheduleSms(guestId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/contracts/generate-and-schedule-sms/${guestId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error generating contract and scheduling SMS:', error);
      throw error;
    }
  },

  async getContract(contractId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/contracts/${contractId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting contract:', error);
      return { success: false, error: error.message };
    }
  },

  async signContract(contractId, signatureData) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/contracts/${contractId}/sign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(signatureData)
      });
      return await response.json();
    } catch (error) {
      console.error('Error signing contract:', error);
      return { success: false, error: error.message };
    }
  },

  async downloadContract(contractId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/contracts/download/${contractId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to download contract');
      }

      const blob = await response.blob();
      return {
        success: true,
        url: URL.createObjectURL(blob)
      };
    } catch (error) {
      console.error('Error downloading contract:', error);
      return { success: false, error: error.message };
    }
  },

  async regenerateContractPdf(contractId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/contracts/regenerate-pdf/${contractId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to regenerate PDF');
      }

      return await response.json();
    } catch (error) {
      console.error('Error regenerating contract PDF:', error);
      return { success: false, error: error.message };
    }
  },

  async deleteProperty(propertyId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/properties/${propertyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to delete property');
      }
      
      return { success: true };
    } catch (error) {
      console.error('Error deleting property:', error);
      return { success: false, error: error.message };
    }
  },

  // Message Templates
  async getMessageTemplates(params = {}) {
    try {
      const token = await this.getAuthToken();
      const url = new URL(`${API_BASE_URL}/messages/templates`);
      Object.keys(params).forEach(key => {
        if (params[key]) {
          url.searchParams.append(key, params[key]);
        }
      });
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      return data || [];
    } catch (error) {
      console.error('Error getting message templates:', error);
      throw error;
    }
  },

  async getManualMessageTemplates() {
    return this.getMessageTemplates({ manual: true });
  },

  async sendManualMessage(data) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/messages/send-manual`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to send message');
      }
      return await response.json();
    } catch (error) {
      console.error('Error sending manual message:', error);
      throw error;
    }
  },

  async createMessageTemplate(templateData) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/messages/templates`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(templateData)
      });
      return await response.json();
    } catch (error) {
      console.error('Error creating message template:', error);
      throw error;
    }
  },

  async updateMessageTemplate(templateId, templateData) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/messages/templates/${templateId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(templateData)
      });
      return await response.json();
    } catch (error) {
      console.error('Error updating message template:', error);
      throw error;
    }
  },

  async deleteMessageTemplate(templateId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/messages/templates/${templateId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.status === 204) {
        return { success: true };
      }
      return await response.json();
    } catch (error) {
      console.error('Error deleting message template:', error);
      throw error;
    }
  },

  // Message Template APIs
  // Contract Management
  async getPendingContracts() {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/contracts/pending`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting pending contracts:', error);
      return { success: false, error: error.message };
    }
  },

  // Dashboard
  async getDashboardStats() {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/dashboard/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting dashboard stats:', error);
      return { success: false, error: 'Failed to fetch dashboard stats' };
    }
  },

  async getRecentActivity() {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/dashboard/recent-activity`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting recent activity:', error);
      return { success: false, error: 'Failed to fetch recent activity' };
    }
  },

  async getOccupancyData(period = 'month') {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/dashboard/occupancy?period=${period}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error getting occupancy data:', error);
      return { success: false, error: 'Failed to fetch occupancy data' };
    }
  },

  // Auth
  async generateFileToken() {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/auth/generate-file-token`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Error generating file token:', error);
      return { success: false, error: 'Failed to generate file token' };
    }
  },

  async viewGuestDocument(guestId) {
    try {
      const tokenResponse = await this.generateFileToken();
      if (!tokenResponse.success) {
        throw new Error('Failed to generate file token');
      }

      const fileToken = tokenResponse.token;
      
      // Get the guest data to find the actual filename
      const guestResponse = await this.getGuest(guestId);
      if (!guestResponse.success || !guestResponse.guest.id_document_path) {
        throw new Error('No document found for this guest');
      }

      // Extract filename from the stored path
      const fullPath = guestResponse.guest.id_document_path;
      const filename = fullPath.split('/').pop(); // Get the filename from the path
      
      const response = await fetch(`${API_BASE_URL}/uploads/${filename}?token=${fileToken}`, {
        method: 'GET'
      });

      if (!response.ok) {
        throw new Error('Failed to fetch document');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      
      // Open document in new tab
      window.open(url, '_blank');
      
      return { success: true };
    } catch (error) {
      console.error('Error viewing guest document:', error);
      return { success: false, error: error.message };
    }
  },

  // Message Management
  async getScheduledMessages(reservationId = null) {
    try {
      const token = await this.getAuthToken();
      const url = new URL(`${API_BASE_URL}/messages/scheduled`);
      if (reservationId && reservationId !== 'undefined') {
        url.searchParams.append('reservation_id', reservationId);
      }
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to fetch scheduled messages');
      }
      return await response.json();
    } catch (error) {
      console.error('Error getting scheduled messages:', error);
      return { success: false, error: error.message };
    }
  },

  async sendScheduledMessage(messageId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/messages/scheduled/${messageId}/send`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to send message');
      }
      return await response.json();
    } catch (error) {
      console.error('Error sending scheduled message:', error);
      return { success: false, error: error.message };
    }
  },

  async cancelScheduledMessage(messageId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/messages/scheduled/${messageId}/cancel`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to cancel message');
      }
      return await response.json();
    } catch (error) {
      console.error('Error cancelling scheduled message:', error);
      return { success: false, error: error.message };
    }
  },

  // Contract Management
  async getContracts() {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/contracts`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to fetch contracts');
      }
      return await response.json();
    } catch (error) {
      console.error('Error getting contracts:', error);
      return { success: false, error: error.message };
    }
  },

  // Enhanced Multi-Team Management
  async createTeam(teamData) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/teams`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(teamData)
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to create team');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating team:', error);
      return { success: false, error: error.message };
    }
  },

  async getTeams() {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/teams`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to fetch teams');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting teams:', error);
      return { success: false, error: error.message };
    }
  },

  async updateTeam(teamId, updateData) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/teams/${teamId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(updateData)
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to update team');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error updating team:', error);
      return { success: false, error: error.message };
    }
  },

  async deleteTeam(teamId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/teams/${teamId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to delete team');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error deleting team:', error);
      return { success: false, error: error.message };
    }
  },

  async inviteTeamMemberNew(teamId, memberData) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/teams/${teamId}/invite`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(memberData)
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to invite team member');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error inviting team member:', error);
      return { success: false, error: error.message };
    }
  },

  async getTeamMembers(teamId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/teams/${teamId}/members`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to fetch team members');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting team members:', error);
      return { success: false, error: error.message };
    }
  },

  async removeTeamMemberNew(teamId, memberId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/teams/${teamId}/members/${memberId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to remove team member');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error removing team member:', error);
      return { success: false, error: error.message };
    }
  },

  async getTeamProperties(teamId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/teams/${teamId}/properties`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to fetch team properties');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting team properties:', error);
      return { success: false, error: error.message };
    }
  },

  async assignPropertyToTeam(teamId, propertyId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/teams/${teamId}/properties/${propertyId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to assign property to team');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error assigning property to team:', error);
      return { success: false, error: error.message };
    }
  },

  async getTeamPerformance(teamId, dateFrom = null, dateTo = null) {
    try {
      const token = await this.getAuthToken();
      let url = `${API_BASE_URL}/teams/${teamId}/performance`;
      
      const params = new URLSearchParams();
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to fetch team performance');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting team performance:', error);
      return { success: false, error: error.message };
    }
  },

  async getOrganizationPerformanceComparison() {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/teams/performance/comparison`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to fetch performance comparison');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting performance comparison:', error);
      return { success: false, error: error.message };
    }
  },

  // Legacy Team Management (keeping for backward compatibility)
  async inviteTeamMember(propertyId, memberData) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/properties/${propertyId}/team/invite`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(memberData)
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to send invitation');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error inviting team member:', error);
      return { success: false, error: error.message };
    }
  },

  async getPropertyTeamMembers(propertyId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/properties/${propertyId}/team`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to fetch team members');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting team members:', error);
      return { success: false, error: error.message };
    }
  },

  async removeTeamMember(propertyId, memberUserId) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/properties/${propertyId}/team/${memberUserId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to remove team member');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error removing team member:', error);
      return { success: false, error: error.message };
    }
  },

  async acceptInvitation(invitationToken) {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/team/invitations/accept/${invitationToken}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to accept invitation');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error accepting invitation:', error);
      return { success: false, error: error.message };
    }
  },

  async getInvitationDetails(invitationToken) {
    try {
      const response = await fetch(`${API_BASE_URL}/team/invitations/${invitationToken}`);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to fetch invitation details');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting invitation details:', error);
      return { success: false, error: error.message };
    }
  },

  async getMyInvitations() {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/team/my-invitations`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to fetch invitations');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting my invitations:', error);
      return { success: false, error: error.message };
    }
  }
};

export default api; 