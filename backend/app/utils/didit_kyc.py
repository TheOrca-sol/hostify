"""
Didit KYC integration service for advanced identity verification
"""

import os
import requests
import hashlib
import hmac
import json
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class DiditKYCService:
    def __init__(self):
        self.api_key = os.getenv('DIDIT_API_KEY')
        self.webhook_secret = os.getenv('DIDIT_WEBHOOK_SECRET')
        self.base_url = os.getenv('DIDIT_BASE_URL', 'https://verification.didit.me')
        self.workflow_id = os.getenv('DIDIT_WORKFLOW_ID')
        
        if not self.api_key:
            raise ValueError("DIDIT_API_KEY environment variable is required")
        if not self.workflow_id:
            raise ValueError("DIDIT_WORKFLOW_ID environment variable is required - get this from your Didit dashboard")
    
    def _get_headers(self):
        """Get headers for API requests"""
        return {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def create_verification_session(self, guest_id, callback_url=None):
        """
        Create a new verification session for a guest
        
        Args:
            guest_id (str): The guest ID from your system
            callback_url (str, optional): URL to redirect user after completion
            
        Returns:
            dict: Response containing session details and verification URL
        """
        try:
            endpoint = f"{self.base_url}/v2/session/"
            
            # Prepare the request data
            data = {
                'workflow_id': self.workflow_id,
                'vendor_data': str(guest_id)
            }
            
            if callback_url:
                data['callback'] = callback_url
            
            logger.info(f"Creating Didit verification session for guest {guest_id}")
            
            # Debug logging
            logger.info(f"Request URL: {endpoint}")
            logger.info(f"Request headers: {self._get_headers()}")
            logger.info(f"Request data: {data}")
            
            # Make the API request
            response = requests.post(
                endpoint,
                headers=self._get_headers(),
                json=data,
                timeout=30
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 201:  # Didit returns 201 for successful creation
                result = response.json()
                logger.info(f"Successfully created Didit session: {result.get('session_id')}")
                return {
                    'success': True,
                    'session_id': result.get('session_id'),
                    'verification_url': result.get('url'),  # Didit uses 'url' field
                    'session_token': result.get('session_token'),
                    'expires_at': result.get('expires_at'),
                    'status': result.get('status', 'Not Started')
                }
            else:
                logger.error(f"Failed to create Didit session: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'API request failed: {response.status_code}',
                    'details': response.text
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error creating Didit session: {str(e)}")
            return {
                'success': False,
                'error': 'Network error',
                'details': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error creating Didit session: {str(e)}")
            return {
                'success': False,
                'error': 'Internal error',
                'details': str(e)
            }
    
    def get_session_status(self, session_id):
        """
        Get the current status of a verification session
        
        Args:
            session_id (str): The session ID from Didit
            
        Returns:
            dict: Session status and results
        """
        try:
            endpoint = f"{self.base_url}/v2/session/{session_id}/"
            
            logger.info(f"Getting status for Didit session {session_id}")
            
            response = requests.get(
                endpoint,
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'session_id': session_id,
                    'status': result.get('status'),
                    'verification_result': result.get('verification_result'),
                    'extracted_data': result.get('extracted_data'),
                    'confidence_scores': result.get('confidence_scores'),
                    'updated_at': result.get('updated_at')
                }
            else:
                logger.error(f"Failed to get Didit session status: {response.status_code}")
                return {
                    'success': False,
                    'error': f'API request failed: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error getting Didit session status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_webhook_signature(self, payload, signature):
        """
        Verify that a webhook request came from Didit
        
        Args:
            payload (str): The raw request body
            signature (str): The signature from headers
            
        Returns:
            bool: True if signature is valid
        """
        try:
            if not self.webhook_secret:
                logger.warning("DIDIT_WEBHOOK_SECRET not configured")
                return False
            
            # Create expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures securely
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    def process_webhook_data(self, webhook_data):
        """
        Process webhook data from Didit
        
        Args:
            webhook_data (dict): The webhook payload
            
        Returns:
            dict: Processed verification results
        """
        try:
            session_id = webhook_data.get('session_id')
            status = webhook_data.get('status')
            verification_result = webhook_data.get('verification_result', {})
            
            # Extract guest information from vendor_data
            vendor_data = webhook_data.get('vendor_data', {})
            if isinstance(vendor_data, str):
                vendor_data = json.loads(vendor_data)
            
            guest_id = vendor_data.get('guest_id')
            
            # Extract document data
            extracted_data = verification_result.get('extracted_data', {})
            
            return {
                'success': True,
                'guest_id': guest_id,
                'session_id': session_id,
                'status': status,
                'verification_passed': status == 'approved',
                'extracted_data': {
                    'full_name': extracted_data.get('full_name'),
                    'document_number': extracted_data.get('document_number'),
                    'date_of_birth': extracted_data.get('date_of_birth'),
                    'nationality': extracted_data.get('nationality'),
                    'document_type': extracted_data.get('document_type'),
                    'address': extracted_data.get('address')
                },
                'confidence_scores': verification_result.get('confidence_scores', {}),
                'face_match_score': verification_result.get('face_match_score'),
                'liveness_check_passed': verification_result.get('liveness_check_passed', False),
                'processed_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing Didit webhook data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Global instance
didit_service = DiditKYCService()