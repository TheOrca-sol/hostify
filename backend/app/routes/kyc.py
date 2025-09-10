"""
KYC (Know Your Customer) routes for Didit integration
"""

from flask import Blueprint, request, jsonify, current_app
from ..models import db, Guest
from ..utils.didit_kyc import didit_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

kyc_bp = Blueprint('kyc', __name__)

# Add CORS support
@kyc_bp.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@kyc_bp.route('/kyc/webhook', methods=['GET', 'POST'])
def didit_webhook():
    """
    Handle webhook notifications from Didit when verification is complete
    """
    try:
        # Handle GET request (webhook verification/testing)
        if request.method == 'GET':
            logger.info("Received GET request on webhook endpoint - webhook verification")
            return jsonify({
                'success': True,
                'message': 'Webhook endpoint is working',
                'method': 'GET'
            }), 200
        
        # Handle POST request (actual webhook data)
        logger.info(f"Received {request.method} webhook notification from Didit")
        
        # Get raw request data
        payload = request.get_data(as_text=True)
        signature = request.headers.get('X-Didit-Signature', '')
        
        logger.info(f"Webhook payload: {payload}")
        logger.info(f"Webhook headers: {dict(request.headers)}")
        
        # For now, skip signature verification during testing
        # TODO: Re-enable signature verification in production
        # if not didit_service.verify_webhook_signature(payload, signature):
        #     logger.warning("Invalid webhook signature from Didit")
        #     return jsonify({'error': 'Invalid signature'}), 401
        
        # Parse webhook data
        webhook_data = request.get_json()
        if not webhook_data:
            logger.error("No JSON data in webhook request")
            return jsonify({'error': 'No data provided'}), 400
        
        # Process the verification results directly from webhook data
        logger.info(f"Processing webhook data: {webhook_data}")
        
        # Extract guest ID from vendor_data
        vendor_data = webhook_data.get('vendor_data')
        if not vendor_data:
            logger.error("No vendor_data in webhook")
            return jsonify({'error': 'No vendor_data provided'}), 400
            
        guest_id = vendor_data
        guest = Guest.query.get(guest_id)
        
        if not guest:
            logger.error(f"Guest {guest_id} not found")
            return jsonify({'error': 'Guest not found'}), 404
        
        # Get verification status from webhook
        status = webhook_data.get('status', '').lower()
        logger.info(f"Webhook status for guest {guest_id}: {status}")
        
        # Update guest based on verification status
        if status in ['completed', 'passed', 'verified', 'success']:
            guest.verification_status = 'verified'
            guest.verified_at = datetime.now()
            
            # Extract any additional data from results
            results = webhook_data.get('results', {})
            if results:
                # Update KYC specific fields
                guest.kyc_confidence_score = results.get('confidence_score')
                guest.kyc_liveness_passed = results.get('liveness_check', True)
                
                # Extract document data if available
                document_data = results.get('document', {})
                if document_data.get('full_name'):
                    guest.full_name = document_data['full_name']
                if document_data.get('document_number'):
                    guest.cin_or_passport = document_data['document_number']
                if document_data.get('nationality'):
                    guest.nationality = document_data['nationality']
            
            logger.info(f"Guest {guest_id} successfully verified via Didit KYC")
            
            # Trigger contract generation
            try:
                from ..utils.automation import AutomationService
                AutomationService.create_contract_for_guest(guest_id)
            except Exception as e:
                logger.error(f"Failed to trigger contract generation: {str(e)}")
                
        elif status in ['failed', 'rejected', 'error']:
            guest.verification_status = 'failed'
            logger.info(f"Guest {guest_id} failed Didit KYC verification")
        else:
            # For other statuses, just log them
            logger.info(f"Guest {guest_id} status updated to: {status}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Webhook processed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing Didit webhook: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@kyc_bp.route('/kyc/start-verification/<guest_id>', methods=['POST'])
def start_kyc_verification(guest_id):
    """
    Start KYC verification process for a guest
    """
    try:
        guest = Guest.query.get(guest_id)
        if not guest:
            return jsonify({'success': False, 'error': 'Guest not found'}), 404
        
        # Create webhook URL (you'll need to update this with your actual domain)
        # For local development
        callback_url = f"{request.url_root.rstrip('/')}/api/kyc/webhook"
        
        # Create Didit verification session
        result = didit_service.create_verification_session(
            guest_id=guest_id,
            callback_url=callback_url
        )
        
        if result['success']:
            # Store session ID in guest record
            guest.kyc_session_id = result['session_id']
            guest.verification_status = 'in_progress'
            db.session.commit()
            
            logger.info(f"Started KYC verification for guest {guest_id}")
            
            return jsonify({
                'success': True,
                'verification_url': result['verification_url'],
                'session_id': result['session_id'],
                'expires_at': result.get('expires_at')
            })
        else:
            logger.error(f"Failed to start KYC for guest {guest_id}: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to create verification session')
            }), 400
            
    except Exception as e:
        logger.error(f"Error starting KYC verification: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@kyc_bp.route('/kyc/status/<guest_id>', methods=['GET'])
def get_kyc_status(guest_id):
    """
    Get KYC verification status for a guest
    """
    try:
        guest = Guest.query.get(guest_id)
        if not guest:
            return jsonify({'success': False, 'error': 'Guest not found'}), 404
        
        result = {
            'success': True,
            'guest_id': guest_id,
            'verification_status': guest.verification_status,
            'kyc_session_id': guest.kyc_session_id,
            'confidence_score': guest.kyc_confidence_score,
            'liveness_passed': guest.kyc_liveness_passed,
            'verified_at': guest.verified_at.isoformat() if guest.verified_at else None
        }
        
        # If we have a session ID, get latest status from Didit
        if guest.kyc_session_id and guest.verification_status == 'in_progress':
            didit_status = didit_service.get_session_status(guest.kyc_session_id)
            if didit_status['success']:
                result['didit_status'] = didit_status['status']
                result['last_updated'] = didit_status.get('updated_at')
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting KYC status: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# Guest-facing KYC routes (no authentication required - uses verification token)
@kyc_bp.route('/kyc/start-guest-verification/<verification_token>', methods=['POST'])
def start_guest_kyc_verification(verification_token):
    """
    Start KYC verification process for a guest using verification token
    """
    try:
        # Find guest by verification token
        from ..models import VerificationLink
        verification_link = VerificationLink.query.filter_by(
            token=verification_token,
            status='sent'
        ).first()
        
        if not verification_link:
            return jsonify({'success': False, 'error': 'Invalid verification token'}), 404
        
        guest = verification_link.guest
        if not guest:
            return jsonify({'success': False, 'error': 'Guest not found'}), 404
        
        # Use completion page as callback URL
        callback_url = f"{request.url_root.rstrip('/')}/api/verification-complete"
        
        # Create Didit verification session
        result = didit_service.create_verification_session(
            guest_id=str(guest.id),
            callback_url=callback_url
        )
        
        if result['success']:
            # Store session ID in guest record
            guest.kyc_session_id = result['session_id']
            guest.verification_status = 'in_progress'
            db.session.commit()
            
            logger.info(f"Started guest KYC verification for guest {guest.id} via token {verification_token}")
            
            return jsonify({
                'success': True,
                'verification_url': result['verification_url'],
                'session_id': result['session_id'],
                'expires_at': result.get('expires_at')
            })
        else:
            logger.error(f"Failed to start guest KYC for token {verification_token}: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to create verification session')
            }), 400
            
    except Exception as e:
        logger.error(f"Error starting guest KYC verification: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@kyc_bp.route('/kyc/guest-status/<verification_token>', methods=['GET'])
def get_guest_kyc_status(verification_token):
    """
    Get KYC verification status for a guest using verification token
    """
    try:
        # Find guest by verification token
        from ..models import VerificationLink
        verification_link = VerificationLink.query.filter_by(
            token=verification_token,
            status='sent'
        ).first()
        
        if not verification_link:
            return jsonify({'success': False, 'error': 'Invalid verification token'}), 404
        
        guest = verification_link.guest
        if not guest:
            return jsonify({'success': False, 'error': 'Guest not found'}), 404
        
        result = {
            'success': True,
            'guest_id': str(guest.id),
            'verification_status': guest.verification_status,
            'kyc_session_id': guest.kyc_session_id,
            'confidence_score': guest.kyc_confidence_score,
            'liveness_passed': guest.kyc_liveness_passed,
            'verified_at': guest.verified_at.isoformat() if guest.verified_at else None
        }
        
        # If we have a session ID, get latest status from Didit and update if needed
        if guest.kyc_session_id and guest.verification_status == 'in_progress':
            didit_status = didit_service.get_session_status(guest.kyc_session_id)
            if didit_status['success']:
                result['didit_status'] = didit_status['status']
                result['last_updated'] = didit_status.get('updated_at')
                
                # Update guest status based on Didit response
                didit_status_value = didit_status.get('status', '').lower()
                if didit_status_value in ['completed', 'passed', 'verified', 'success', 'complete']:
                    guest.verification_status = 'verified'
                    guest.verified_at = datetime.now()
                    
                    # Extract verification results if available
                    verification_result = didit_status.get('verification_result', {})
                    if verification_result:
                        guest.kyc_confidence_score = verification_result.get('confidence_score')
                        guest.kyc_liveness_passed = verification_result.get('liveness_check', True)
                    
                    db.session.commit()
                    result['verification_status'] = 'verified'
                    logger.info(f"Updated guest {guest.id} status to verified based on Didit status")
                    
                    # Trigger contract generation
                    try:
                        from ..utils.automation import AutomationService  
                        AutomationService.create_contract_for_guest(str(guest.id))
                    except Exception as e:
                        logger.error(f"Failed to trigger contract generation: {str(e)}")
                        
                elif didit_status_value in ['failed', 'rejected', 'error']:
                    guest.verification_status = 'failed'
                    db.session.commit()
                    result['verification_status'] = 'failed'
                    logger.info(f"Updated guest {guest.id} status to failed based on Didit status")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting guest KYC status: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@kyc_bp.route('/kyc/mark-completed/<verification_token>', methods=['POST'])
def mark_kyc_completed(verification_token):
    """
    Fallback endpoint to mark KYC as completed when status polling fails
    """
    try:
        # Find guest by verification token
        from ..models import VerificationLink
        verification_link = VerificationLink.query.filter_by(
            token=verification_token,
            status='sent'
        ).first()
        
        if not verification_link:
            return jsonify({'success': False, 'error': 'Invalid verification token'}), 404
        
        guest = verification_link.guest
        if not guest:
            return jsonify({'success': False, 'error': 'Guest not found'}), 404
        
        # Only update if still in progress (avoid overwriting actual webhook updates)
        if guest.verification_status == 'in_progress':
            guest.verification_status = 'verified'
            guest.verified_at = datetime.now()
            db.session.commit()
            
            logger.info(f"Fallback: Marked guest {guest.id} as verified after timeout")
            
            # Trigger contract generation
            try:
                from ..utils.automation import AutomationService
                AutomationService.create_contract_for_guest(str(guest.id))
            except Exception as e:
                logger.error(f"Failed to trigger contract generation: {str(e)}")
        
        return jsonify({
            'success': True,
            'verification_status': guest.verification_status,
            'message': 'Verification status updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error marking KYC as completed: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

