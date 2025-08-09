"""
Reservation management routes for Hostify Property Management Platform
"""

from flask import Blueprint, request, jsonify, g
from ..utils.database import (
    create_reservation, get_user_reservations, get_property_reservations,
    get_user_by_firebase_uid, get_property
)
from ..utils.auth import require_auth, get_current_user_id
from datetime import datetime, timezone
import logging

# Configure logging
logger = logging.getLogger(__name__)

reservations_bp = Blueprint('reservations', __name__)

@reservations_bp.route('/reservations', methods=['POST'])
@require_auth
def create_reservation_route():
    """
    Create a new reservation for a property
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get reservation data
        reservation_data = request.get_json()
        if not reservation_data:
            return jsonify({'success': False, 'error': 'No reservation data provided'}), 400
        
        # Validate required fields
        required_fields = ['property_id', 'check_in', 'check_out']
        for field in required_fields:
            if not reservation_data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Verify property ownership
        property_data = get_property(reservation_data['property_id'], user.id)
        if not property_data:
            return jsonify({'success': False, 'error': 'Property not found or access denied'}), 404
        
        # Parse dates
        try:
            reservation_data['check_in'] = datetime.fromisoformat(reservation_data['check_in'].replace('Z', '+00:00'))
            reservation_data['check_out'] = datetime.fromisoformat(reservation_data['check_out'].replace('Z', '+00:00'))
        except ValueError as e:
            return jsonify({'success': False, 'error': f'Invalid date format: {str(e)}'}), 400
        
        # Create reservation
        reservation_id = create_reservation(**reservation_data)
        
        if reservation_id:
            return jsonify({
                'success': True,
                'message': 'Reservation created successfully',
                'reservation_id': reservation_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create reservation'}), 500
    
    except Exception as e:
        logger.error(f"Failed to create reservation: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to create reservation: {str(e)}'
        }), 500

@reservations_bp.route('/reservations', methods=['GET'])
@require_auth
def get_reservations():
    """
    Get all reservations for the authenticated user (across all properties)
    with support for pagination, searching, and filtering.
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search_query = request.args.get('search', None, type=str)
        property_id = request.args.get('property_id', None, type=str)
        filter_type = request.args.get('filter_type', None, type=str)

        # Get reservations from database
        result = get_user_reservations(
            user_id=user.id,
            page=page,
            per_page=per_page,
            search_query=search_query,
            property_id=property_id,
            filter_type=filter_type
        )
        
        return jsonify({
            'success': True,
            'reservations': result['reservations'],
            'total': result['total'],
            'pages': result['pages'],
            'current_page': result['current_page']
        })
    
    except Exception as e:
        logger.error(f"Failed to get reservations: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get reservations: {str(e)}'
        }), 500

@reservations_bp.route('/reservations/<reservation_id>', methods=['GET'])
@require_auth
def get_reservation(reservation_id):
    """
    Get a specific reservation with its guests
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get all user reservations and find the requested one
        reservations = get_user_reservations(user.id)
        reservation = next((r for r in reservations if r['id'] == reservation_id), None)
        
        if not reservation:
            return jsonify({'success': False, 'error': 'Reservation not found or access denied'}), 404
        
        # Get guests for this reservation
        from ..utils.database import get_reservation_guests
        guests = get_reservation_guests(reservation_id)
        
        reservation['guests'] = guests
        
        return jsonify({
            'success': True,
            'reservation': reservation
        })
    
    except Exception as e:
        logger.error(f"Failed to get reservation: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get reservation: {str(e)}'
        }), 500

@reservations_bp.route('/reservations/upcoming', methods=['GET'])
@require_auth
def get_upcoming_reservations():
    """
    Get upcoming reservations for the authenticated user
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get upcoming reservations
        reservations = get_user_reservations(user.id, filter_type='upcoming')
        
        return jsonify({
            'success': True,
            'reservations': reservations,
            'total': len(reservations)
        })
    
    except Exception as e:
        logger.error(f"Failed to get upcoming reservations: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get upcoming reservations: {str(e)}'
        }), 500

@reservations_bp.route('/reservations/current', methods=['GET'])
@require_auth
def get_current_reservations():
    """
    Get current (ongoing) reservations for the authenticated user
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get current reservations
        reservations = get_user_reservations(user.id, filter_type='current')
        
        return jsonify({
            'success': True,
            'reservations': reservations,
            'total': len(reservations)
        })
    
    except Exception as e:
        logger.error(f"Failed to get current reservations: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get current reservations: {str(e)}'
        }), 500 