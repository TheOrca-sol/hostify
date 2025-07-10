"""
Guest management routes - Updated for property-centric architecture
"""

from flask import Blueprint, request, jsonify
from ..utils.database import get_user_guests, create_guest, get_reservation_guests, update_guest, get_guest_by_reservation
from ..utils.auth import verify_firebase_token
from datetime import datetime

guests_bp = Blueprint('guests', __name__)

@guests_bp.route('/guests', methods=['GET'])
def get_guests():
    """
    Get all guests for the authenticated user (across all properties)
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
        
        # Get guests from database using Firebase UID directly
        guests = get_user_guests(firebase_uid)
        
        return jsonify({
            'success': True,
            'guests': guests,
            'total': len(guests)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get guests: {str(e)}'
        }), 500

@guests_bp.route('/reservations/<reservation_id>/guests', methods=['POST'])
def create_reservation_guest():
    """
    Create or update a guest for a specific reservation
    """
    try:
        # Verify Firebase token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        user_id = verify_firebase_token(token)
        if not user_id:
            return jsonify({'success': False, 'error': 'Invalid authentication token'}), 401
        
        # Get guest data
        guest_data = request.get_json()
        if not guest_data:
            return jsonify({'success': False, 'error': 'No guest data provided'}), 400
        
        reservation_id = request.view_args['reservation_id']
        
        # Parse birthdate if it's a string
        if isinstance(guest_data.get('birthdate'), str):
            guest_data['birthdate'] = datetime.fromisoformat(guest_data['birthdate']).date()
        
        # Check if guest already exists for this reservation
        existing_guest = get_guest_by_reservation(reservation_id)
        
        if existing_guest:
            # Update existing guest
            success = update_guest(existing_guest['id'], guest_data)
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Guest updated successfully',
                    'guest_id': existing_guest['id']
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to update guest'}), 500
        else:
            # Create new guest
            guest_id = create_guest(reservation_id, **guest_data)
            if guest_id:
                return jsonify({
                    'success': True,
                    'message': 'Guest created successfully',
                    'guest_id': guest_id
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to create guest'}), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to create/update guest: {str(e)}'
        }), 500

@guests_bp.route('/reservations/<reservation_id>/guests', methods=['GET'])
def get_reservation_guests_route():
    """
    Get all guests for a specific reservation
    """
    try:
        # Verify Firebase token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        user_id = verify_firebase_token(token)
        if not user_id:
            return jsonify({'success': False, 'error': 'Invalid authentication token'}), 401
        
        reservation_id = request.view_args['reservation_id']
        
        # Get guests for this reservation
        guests = get_reservation_guests(reservation_id)
        
        return jsonify({
            'success': True,
            'guests': guests,
            'total': len(guests)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get reservation guests: {str(e)}'
        }), 500

# Legacy endpoint for backward compatibility
@guests_bp.route('/guests', methods=['POST'])
def create_guest_legacy():
    """
    Legacy endpoint - now requires reservation_id in the data
    """
    try:
        # Verify Firebase token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        user_id = verify_firebase_token(token)
        if not user_id:
            return jsonify({'success': False, 'error': 'Invalid authentication token'}), 401
        
        # Get guest data
        guest_data = request.get_json()
        if not guest_data:
            return jsonify({'success': False, 'error': 'No guest data provided'}), 400
        
        # Check for reservation_id
        reservation_id = guest_data.get('reservation_id')
        if not reservation_id:
            return jsonify({'success': False, 'error': 'reservation_id is required'}), 400
        
        # Validate required fields
        required_fields = ['full_name', 'cin_or_passport', 'birthdate', 'nationality']
        for field in required_fields:
            if not guest_data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Parse birthdate if it's a string
        if isinstance(guest_data.get('birthdate'), str):
            guest_data['birthdate'] = datetime.fromisoformat(guest_data['birthdate']).date()
        
        # Create guest
        guest_id = create_guest(reservation_id, **guest_data)
        
        if guest_id:
            return jsonify({
                'success': True,
                'message': 'Guest created successfully',
                'guest_id': guest_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create guest'}), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to create guest: {str(e)}'
        }), 500 