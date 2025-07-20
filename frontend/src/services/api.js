// API configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

// API service functions
export const api = {
  // Get auth token from Firebase
  async getAuthToken() {
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
      const response = await fetch(`${API_BASE_URL}/contract/generate-and-schedule-sms/${guestId}`, {
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
      const response = await fetch(`${API_BASE_URL}/contracts/${contractId}/download`, {
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
  async getMessageTemplates(propertyId = null) {
    try {
      const token = await this.getAuthToken();
      const url = propertyId 
        ? `${API_BASE_URL}/messages/templates?property_id=${propertyId}`
        : `${API_BASE_URL}/messages/templates`;
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
  }
};

export default api; 