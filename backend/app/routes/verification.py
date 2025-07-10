"""
Verification management routes - Updated for property-centric architecture
Verification links are now tied to guests within reservations
"""

from flask import Blueprint, request, jsonify
from ..utils.database import (
    create_verification_link, get_verification_link, get_user_by_firebase_uid,
    get_reservation_guests, create_guest, get_user_reservations
)
from ..utils.auth import verify_firebase_token
from datetime import datetime, timedelta, timezone
import secrets
import string

verification_bp = Blueprint('verification', __name__)

@verification_bp.route('/create-verification-link', methods=['POST'])
def create_link():
    """
    Create a verification link for a guest (Host only)
    This is now updated to work with reservations
    """
    try:
        # Verify Firebase token (host authentication required)
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        firebase_uid = verify_firebase_token(token)
        if not firebase_uid:
            return jsonify({'success': False, 'error': 'Invalid authentication token'}), 401
        
        # Get user record
        user = get_user_by_firebase_uid(firebase_uid)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get request data
        data = request.get_json() or {}
        reservation_id = data.get('reservation_id')
        guest_name = data.get('guest_name', '')
        expires_hours = data.get('expires_hours', 48)  # Default 48 hours
        
        if not reservation_id:
            return jsonify({'success': False, 'error': 'reservation_id is required'}), 400
        
        # Verify reservation belongs to user
        user_reservations = get_user_reservations(user['id'])
        reservation = next((r for r in user_reservations if r['id'] == reservation_id), None)
        if not reservation:
            return jsonify({'success': False, 'error': 'Reservation not found or access denied'}), 404
        
        # Create a guest record for the verification process
        guest_data = {
            'full_name': guest_name,
            'verification_status': 'pending'
        }
        
        guest_id = create_guest(reservation_id, **guest_data)
        if not guest_id:
            return jsonify({'success': False, 'error': 'Failed to create guest record'}), 500
        
        # Generate secure token
        verification_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        
        # Calculate expiration
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
        
        # Create verification link in database
        link_id = create_verification_link(
            guest_id=guest_id,
            token=verification_token,
            expires_at=expires_at
        )
        
        if link_id:
            # Generate the full verification URL
            base_url = request.url_root.rstrip('/')
            verification_url = f"{base_url}/verify/{verification_token}"
            
            return jsonify({
                'success': True,
                'verification_url': verification_url,
                'verification_token': verification_token,
                'expires_at': expires_at.isoformat(),
                'guest_name': guest_name,
                'guest_id': guest_id,
                'reservation_id': reservation_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create verification link'}), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to create verification link: {str(e)}'
        }), 500

@verification_bp.route('/reservations/<reservation_id>/verification-links', methods=['POST'])
def create_reservation_verification_link(reservation_id):
    """
    Create a verification link for a specific reservation
    """
    try:
        # Verify Firebase token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        firebase_uid = verify_firebase_token(token)
        if not firebase_uid:
            return jsonify({'success': False, 'error': 'Invalid authentication token'}), 401
        
        # Get user record
        user = get_user_by_firebase_uid(firebase_uid)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Verify reservation belongs to user
        user_reservations = get_user_reservations(user['id'])
        reservation = next((r for r in user_reservations if r['id'] == reservation_id), None)
        if not reservation:
            return jsonify({'success': False, 'error': 'Reservation not found or access denied'}), 404
        
        # Get request data
        data = request.get_json() or {}
        guest_name = data.get('guest_name', 'Guest')
        expires_hours = data.get('expires_hours', 48)
        
        # Create a guest record for verification
        guest_data = {
            'full_name': guest_name,
            'verification_status': 'pending'
        }
        
        guest_id = create_guest(reservation_id, **guest_data)
        if not guest_id:
            return jsonify({'success': False, 'error': 'Failed to create guest record'}), 500
        
        # Generate secure token
        verification_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        
        # Calculate expiration
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
        
        # Create verification link
        link_id = create_verification_link(
            guest_id=guest_id,
            token=verification_token,
            expires_at=expires_at
        )
        
        if link_id:
            base_url = request.url_root.rstrip('/')
            verification_url = f"{base_url}/verify/{verification_token}"
            
            return jsonify({
                'success': True,
                'verification_url': verification_url,
                'verification_token': verification_token,
                'expires_at': expires_at.isoformat(),
                'guest_name': guest_name,
                'guest_id': guest_id,
                'reservation_id': reservation_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create verification link'}), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to create verification link: {str(e)}'
        }), 500

@verification_bp.route('/verification-links', methods=['GET'])
def get_verification_links():
    """
    Get all verification links for the authenticated host (across all reservations)
    """
    try:
        # Verify Firebase token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        firebase_uid = verify_firebase_token(token)
        if not firebase_uid:
            return jsonify({'success': False, 'error': 'Invalid authentication token'}), 401
        
        # Get user record
        user = get_user_by_firebase_uid(firebase_uid)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get all guests for user (which includes verification links)
        from ..utils.database import get_user_guests
        guests = get_user_guests(user['id'])
        
        # Extract verification link information
        verification_links = []
        for guest in guests:
            if guest.get('verification_links'):
                for link in guest['verification_links']:
                    verification_links.append({
                        **link,
                        'guest_name': guest.get('full_name'),
                        'guest_id': guest['id'],
                        'reservation_id': guest['reservation_id']
                    })
        
        return jsonify({
            'success': True,
            'verification_links': verification_links,
            'total': len(verification_links)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get verification links: {str(e)}'
        }), 500

def _check_verification_link_validity(link_info):
    """Helper function to check if verification link is valid"""
    if not link_info:
        return False, 'Invalid verification link', 404
    
    # Check if expired
    expires_at = link_info['expires_at']
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    
    # Ensure timezone awareness
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        return False, 'Verification link has expired', 410
    
    # Check if already used
    if link_info.get('status') == 'used':
        return False, 'Verification link has already been used', 410
    
    return True, None, None

@verification_bp.route('/verify/<token>', methods=['GET'])
def get_verification_info(token):
    """
    Get verification link info (Guest access - no auth required)
    """
    try:
        # Get verification link info
        link_info = get_verification_link(token)
        
        # Check validity
        is_valid, error_msg, status_code = _check_verification_link_validity(link_info)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), status_code
        
        # Get guest information
        from ..utils.database import db, Guest
        guest = Guest.query.filter_by(id=link_info['guest_id']).first()
        guest_name = guest.full_name if guest and guest.full_name else 'Guest'
        
        return jsonify({
            'success': True,
            'guest_name': guest_name,
            'expires_at': link_info['expires_at'],
            'created_at': link_info['created_at']
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get verification info: {str(e)}'
        }), 500

@verification_bp.route('/verify/<token>/upload', methods=['POST'])
def verify_guest_upload(token):
    """
    Upload and process guest ID document (Guest access - no auth required)
    """
    try:
        # Verify the token is valid
        link_info = get_verification_link(token)
        
        # Check validity
        is_valid, error_msg, status_code = _check_verification_link_validity(link_info)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), status_code
        
        # Process the uploaded file (same as existing upload logic)
        from ..utils.ocr import process_id_document
        import tempfile
        import os
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file type
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS):
            return jsonify({'success': False, 'error': 'Invalid file type. Only PNG, JPG, and JPEG are allowed'}), 400
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Process the image using OCR
            extracted_data = process_id_document(temp_path)
            
            # Handle new response format
            if not extracted_data.get('success'):
                return jsonify({
                    'success': False,
                    'error': extracted_data.get('error', 'OCR processing failed'),
                    'confidence_score': extracted_data.get('confidence_score', 0),
                    'validation': extracted_data.get('validation', {}),
                    'verification_token': token
                }), 500
            
            return jsonify({
                'success': True,
                'data': extracted_data.get('data', {}),
                'confidence_score': extracted_data.get('confidence_score', 0),
                'validation': extracted_data.get('validation', {}),
                'suggestions': extracted_data.get('suggestions', []),
                'processing_quality': extracted_data.get('processing_quality', {}),
                'message': 'ID document processed successfully',
                'verification_token': token
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'OCR processing failed: {str(e)}'
            }), 500
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }), 500

@verification_bp.route('/verify/<token>/submit', methods=['POST'])
def submit_guest_verification(token):
    """
    Submit final guest verification data (Guest access - no auth required)
    """
    try:
        # Verify the token is valid
        link_info = get_verification_link(token)
        
        # Check validity
        is_valid, error_msg, status_code = _check_verification_link_validity(link_info)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), status_code
        
        # Get guest data
        guest_data = request.get_json()
        if not guest_data:
            return jsonify({'success': False, 'error': 'No guest data provided'}), 400
        
        # Validate required fields
        required_fields = ['full_name', 'cin_or_passport', 'birthdate', 'nationality']
        for field in required_fields:
            if not guest_data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Parse birthdate if it's a string
        if isinstance(guest_data.get('birthdate'), str):
            guest_data['birthdate'] = datetime.fromisoformat(guest_data['birthdate']).date()
        
        # Update the guest record
        from ..utils.database import db, Guest, VerificationLink
        guest = Guest.query.filter_by(id=link_info['guest_id']).first()
        if not guest:
            return jsonify({'success': False, 'error': 'Guest record not found'}), 404
        
        # Update guest with verification data
        guest.full_name = guest_data['full_name']
        guest.cin_or_passport = guest_data['cin_or_passport']
        guest.birthdate = guest_data['birthdate']
        guest.nationality = guest_data['nationality']
        guest.address = guest_data.get('address')
        guest.phone = guest_data.get('phone')
        guest.email = guest_data.get('email')
        guest.document_type = guest_data.get('document_type')
        guest.verification_status = 'verified'
        guest.verified_at = datetime.now(timezone.utc)
        
        # Mark verification link as used
        verification_link = VerificationLink.query.filter_by(token=token).first()
        if verification_link:
            verification_link.status = 'used'
            verification_link.used_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Verification completed successfully',
            'guest_id': str(guest.id)
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to submit verification: {str(e)}'
        }), 500 