"""
Guest verification routes for Hostify Property Management Platform
"""

from flask import Blueprint, request, jsonify, g
from ..models import db, User, Guest, Property, Reservation, VerificationLink, MessageTemplate
from ..utils.database import get_user_by_firebase_uid
from ..utils.auth import require_auth
from ..utils.ocr import process_id_document
from ..utils.sms import send_sms
from ..utils.automation import AutomationService
from datetime import datetime, timezone, timedelta
import uuid
import os
from werkzeug.utils import secure_filename

verification_bp = Blueprint('verification', __name__)

@verification_bp.route('/verify/<guest_id>/send-link', methods=['POST'])
@require_auth
def send_verification_link(guest_id):
    """Generate and send a verification link via SMS."""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        guest = Guest.query.get(guest_id)
        if not guest or str(guest.reservation.property.user_id) != user.id:
            return jsonify({'success': False, 'error': 'Guest not found or access denied'}), 404

        if not guest.phone:
            return jsonify({'success': False, 'error': 'Guest has no phone number on file.'}), 400

        # Create a new verification link
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        new_link = VerificationLink(
            guest_id=guest.id,
            token=token,
            expires_at=expires_at,
            status='sent'
        )
        db.session.add(new_link)
        
        # Also update the token on the guest for public-facing routes
        guest.verification_token = token
        db.session.commit()

        verification_url = f"http://localhost:3000/verify/{token}"
        
        # Fetch the verification template from the database
        template = MessageTemplate.query.filter_by(user_id=user.id, template_type='verification_request').first()
        
        if template:
            message_body = template.content.replace('{{guest_name}}', guest.full_name or 'Guest')
            message_body = message_body.replace('{{verification_link}}', verification_url)
        else:
            # Fallback to a hardcoded message if no template is found
            message_body = f"Hello {guest.full_name or 'Guest'}, please verify your identity for your upcoming stay: {verification_url}"

        # Send the SMS
        sms_result = send_sms(guest.phone, message_body)

        if sms_result['success']:
            # This is the master trigger: schedule all other automated messages for this guest
            AutomationService.schedule_messages_for_guest(guest.id)
            return jsonify({'success': True, 'message': 'Verification link sent and automations scheduled.'})
        else:
            return jsonify({'success': False, 'error': sms_result.get('error', 'Failed to send SMS.')}), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

from ..utils.automation_triggers import trigger_post_verification_actions
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
        
        if str(guest.reservation.property.user_id) != user.id:
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

        # Trigger post-verification actions
        trigger_post_verification_actions(guest)
        
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

@verification_bp.route('/get-verification-info/<token>', methods=['GET'])
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

        # Trigger post-verification actions
        trigger_post_verification_actions(guest)

        return jsonify({'success': True, 'message': 'Verification submitted successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Failed to submit verification: {str(e)}'}), 500