"""
Guest verification routes for Hostify Property Management Platform
"""

from flask import Blueprint, request, jsonify, g
from ..utils.database import (
    db, User, Guest, Property, Reservation,
    get_user_by_firebase_uid
)
from ..utils.auth import require_auth
from ..utils.ocr import process_id_document
from ..utils.sms import send_sms
from datetime import datetime, timezone
import uuid
import os
from werkzeug.utils import secure_filename

verification_bp = Blueprint('verification', __name__)

@verification_bp.route('/verify/<guest_id>/send-link', methods=['POST'])
@require_auth
def send_verification_link(guest_id):
    """Send a verification link to a guest via SMS"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get guest and verify ownership
        guest = Guest.query.filter_by(id=uuid.UUID(guest_id)).first()
        if not guest:
            return jsonify({'success': False, 'error': 'Guest not found'}), 404
        
        # Get reservation and property to verify ownership
        if not guest.reservation or not guest.reservation.property:
            return jsonify({'success': False, 'error': 'Invalid guest data'}), 400
        
        if str(guest.reservation.property.user_id) != user['id']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Generate verification token
        token = str(uuid.uuid4())
        guest.verification_token = token
        db.session.commit()
        
        # Send verification link via SMS
        verification_link = f"http://localhost:3000/verify/{token}"
        message_body = f"Please verify your identity for your upcoming stay: {verification_link}"
        sms_sent = send_sms(guest.phone, message_body)
        
        if sms_sent:
            return jsonify({'success': True, 'message': 'Verification link sent successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to send verification link'}), 500
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to send verification link: {str(e)}'
        }), 500

@verification_bp.route('/verify/guest/<guest_id>', methods=['POST'])
@require_auth
def verify_guest(guest_id):
    """Verify a guest's identity"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get guest and verify ownership
        guest = Guest.query.filter_by(id=uuid.UUID(guest_id)).first()
        if not guest:
            return jsonify({'success': False, 'error': 'Guest not found'}), 404
        
        # Get reservation and property to verify ownership
        if not guest.reservation or not guest.reservation.property:
            return jsonify({'success': False, 'error': 'Invalid guest data'}), 400
        
        if str(guest.reservation.property.user_id) != user['id']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Get verification data
        verification_data = request.get_json()
        if not verification_data:
            return jsonify({'success': False, 'error': 'No verification data provided'}), 400
        
        # Validate required fields
        required_fields = ['document_type', 'cin_or_passport', 'full_name', 'nationality']
        for field in required_fields:
            if not verification_data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Update guest record
        guest.document_type = verification_data['document_type']
        guest.cin_or_passport = verification_data['cin_or_passport']
        guest.full_name = verification_data['full_name']
        guest.nationality = verification_data['nationality']
        guest.birthdate = verification_data.get('birthdate')
        guest.verification_status = 'verified'
        guest.verified_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Guest verified successfully',
            'guest': guest.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to verify guest: {str(e)}'
        }), 500

@verification_bp.route('/verify/<token>/upload', methods=['POST'])
def upload_document(token):
    """Public-facing route for guests to upload their ID documents"""
    try:
        guest = Guest.query.filter_by(verification_token=token).first()
        if not guest:
            return jsonify({'success': False, 'error': 'Invalid verification link'}), 404

        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        filename = secure_filename(f"{guest.id}_{file.filename}")
        upload_folder = os.path.join(os.getcwd(), 'uploads', str(guest.id))
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        try:
            ocr_result = process_id_document(file_path)
            if not ocr_result['success']:
                return jsonify({
                    'success': False,
                    'error': ocr_result.get('error', 'Failed to process ID document'),
                }), 500

            extracted_info = ocr_result['data']
            guest.document_type = extracted_info.get('document_type', 'unknown')
            guest.cin_or_passport = extracted_info.get('cin_or_passport')
            guest.full_name = extracted_info.get('full_name')
            guest.nationality = extracted_info.get('nationality')
            guest.birthdate = extracted_info.get('birthdate')
            guest.verification_status = 'pending_review'
            guest.id_document_path = file_path
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'ID document processed successfully',
                'data': extracted_info
            })

        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to process ID document: {str(e)}'
        }), 500

@verification_bp.route('/verify/get-verification-info/<token>', methods=['GET'])
def get_verification_info(token):
    """Get verification information for a given token"""
    try:
        guest = Guest.query.filter_by(verification_token=token).first()
        if not guest:
            return jsonify({'success': False, 'error': 'Invalid verification link'}), 404

        return jsonify({
            'success': True,
            'guest_id': guest.id,
            'guest_name': guest.full_name,
            'guest_status': guest.verification_status
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get verification info: {str(e)}'
        }), 500

@verification_bp.route('/verify/<token>/submit', methods=['POST'])
def submit_verification(token):
    """Submit guest verification data"""
    try:
        guest = Guest.query.filter_by(verification_token=token).first()
        if not guest:
            return jsonify({'success': False, 'error': 'Invalid verification link'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data submitted'}), 400

        # Update guest information
        guest.full_name = data.get('full_name', guest.full_name)
        guest.birthdate = data.get('birthdate', guest.birthdate)
        guest.cin_or_passport = data.get('cin_or_passport', guest.cin_or_passport)
        guest.nationality = data.get('nationality', guest.nationality)
        guest.verification_status = 'verified'
        guest.verified_at = datetime.now(timezone.utc)
        
        db.session.commit()

        return jsonify({'success': True, 'message': 'Verification submitted successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Failed to submit verification: {str(e)}'}), 500