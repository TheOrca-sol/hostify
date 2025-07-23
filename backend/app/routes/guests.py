"""
Guest management routes - Updated for property-centric architecture
"""

from flask import Blueprint, request, jsonify, g
from ..utils.database import get_user_guests, create_guest, get_reservation_guests, update_guest, get_guest_by_reservation
from ..utils.auth import require_auth, get_current_user_id
from datetime import datetime

guests_bp = Blueprint('guests', __name__)

# Add CORS support for all routes in this blueprint
@guests_bp.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@guests_bp.route('/guests/<guest_id>', methods=['PUT', 'OPTIONS'])
@require_auth
def update_guest_route(guest_id):
    """
    Update a specific guest's information
    """
    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        # Get guest data
        guest_data = request.get_json()
        if not guest_data:
            return jsonify({'success': False, 'error': 'No guest data provided'}), 400
        
        # Parse birthdate if it's a string
        if isinstance(guest_data.get('birthdate'), str):
            guest_data['birthdate'] = datetime.fromisoformat(guest_data['birthdate']).date()
        
        # Update guest
        success = update_guest(guest_id, guest_data)
        if success:
            # Get the updated guest data to return
            from ..utils.database import get_guest_by_id
            updated_guest = get_guest_by_id(guest_id)
            return jsonify({
                'success': True,
                'message': 'Guest updated successfully',
                'guest': updated_guest
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update guest'}), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to update guest: {str(e)}'
        }), 500

@guests_bp.route('/guests/<guest_id>', methods=['GET'])
@require_auth
def get_guest_route(guest_id):
    """
    Get a specific guest's information
    """
    try:
        from ..utils.database import get_guest_by_id
        guest = get_guest_by_id(guest_id)
        
        if not guest:
            return jsonify({'success': False, 'error': 'Guest not found'}), 404
        
        return jsonify({
            'success': True,
            'guest': guest
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get guest: {str(e)}'
        }), 500

@guests_bp.route('/guests', methods=['GET'])
@require_auth
def get_guests():
    """
    Get all guests for the authenticated user with pagination and filtering.
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search_query = request.args.get('search', None, type=str)
        property_id = request.args.get('property_id', None, type=str)

        result = get_user_guests(
            firebase_uid=g.user_id,
            page=page,
            per_page=per_page,
            search_query=search_query,
            property_id=property_id
        )
        
        return jsonify({
            'success': True,
            'guests': result['guests'],
            'total': result['total'],
            'pages': result['pages'],
            'current_page': result['current_page']
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get guests: {str(e)}'
        }), 500

@guests_bp.route('/reservations/<reservation_id>/guests', methods=['POST'])
@require_auth
def create_reservation_guest(reservation_id):
    """
    Create or update a guest for a specific reservation
    """
    try:
        # Get guest data
        guest_data = request.get_json()
        if not guest_data:
            return jsonify({'success': False, 'error': 'No guest data provided'}), 400
        
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
@require_auth
def get_reservation_guests_route(reservation_id):
    """
    Get all guests for a specific reservation
    """
    try:
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
@require_auth
def create_guest_legacy():
    """
    Legacy endpoint - now requires reservation_id in the data
    """
    try:
        # Get guest data
        guest_data = request.get_json()
        if not guest_data:
            return jsonify({'success': False, 'error': 'No guest data provided'}), 400
            
        # Ensure reservation_id is provided
        reservation_id = guest_data.pop('reservation_id', None)
        if not reservation_id:
            return jsonify({'success': False, 'error': 'reservation_id is required'}), 400
        
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