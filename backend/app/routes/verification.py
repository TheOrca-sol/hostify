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
from datetime import datetime, timezone
import uuid
import os
from werkzeug.utils import secure_filename

verification_bp = Blueprint('verification', __name__)

@verification_bp.route('/verify-guest/<guest_id>', methods=['POST'])
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
        required_fields = ['id_type', 'id_number', 'full_name', 'nationality']
        for field in required_fields:
            if not verification_data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Update guest record
        guest.id_type = verification_data['id_type']
        guest.id_number = verification_data['id_number']
        guest.full_name = verification_data['full_name']
        guest.nationality = verification_data['nationality']
        guest.date_of_birth = verification_data.get('date_of_birth')
        guest.id_expiry_date = verification_data.get('id_expiry_date')
        guest.verification_status = 'verified'
        guest.verified_at = datetime.now(timezone.utc)
        guest.verification_method = 'manual'
        
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

@verification_bp.route('/verify-guest/<guest_id>/upload-id', methods=['POST'])
@require_auth
def upload_id_document(guest_id):
    """Upload and process a guest's ID document"""
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
        
        # Check if file was uploaded
        if 'id_document' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['id_document']
        if not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Save file temporarily
        filename = secure_filename(f"{guest_id}_{file.filename}")
        upload_folder = os.path.join(os.getcwd(), 'uploads', str(guest.id))
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        try:
            # Process ID document with OCR
            ocr_result = process_id_document(file_path)
            if not ocr_result['success']:
                return jsonify({
                    'success': False,
                    'error': ocr_result.get('error', 'Failed to process ID document'),
                    'confidence_score': ocr_result.get('confidence_score', 0)
                }), 500
            
            extracted_info = ocr_result['data']
            
            # Update guest record with extracted info
            guest.id_type = extracted_info.get('id_type', 'unknown')
            guest.id_number = extracted_info.get('id_number')
            guest.full_name = extracted_info.get('full_name')
            guest.nationality = extracted_info.get('nationality')
            guest.date_of_birth = extracted_info.get('date_of_birth')
            guest.id_expiry_date = extracted_info.get('id_expiry_date')
            guest.verification_status = 'pending_review'
            guest.verification_method = 'ocr'
            guest.ocr_confidence = ocr_result.get('confidence_score', 0)
            guest.id_document_path = file_path
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'ID document processed successfully',
                'guest': guest.to_dict(),
                'extracted_info': extracted_info,
                'confidence_score': ocr_result.get('confidence_score', 0),
                'validation': ocr_result.get('validation', {}),
                'suggestions': ocr_result.get('suggestions', [])
            })
            
        except Exception as e:
            # Clean up file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to process ID document: {str(e)}'
        }), 500

@verification_bp.route('/verify-guest/<guest_id>/status', methods=['GET'])
@require_auth
def get_verification_status(guest_id):
    """Get the verification status of a guest"""
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
        
        return jsonify({
            'success': True,
            'guest': guest.to_dict()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get verification status: {str(e)}'
        }), 500 