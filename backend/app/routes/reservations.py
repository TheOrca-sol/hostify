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
        property_data = get_property(reservation_data['property_id'], user['id'])
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
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get reservations from database
        reservations = get_user_reservations(user['id'])
        
        # Optional filtering by date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date or end_date:
            filtered_reservations = []
            for reservation in reservations:
                # Handle both datetime objects and string dates
                check_in_raw = reservation['check_in']
                check_out_raw = reservation['check_out']
                
                if isinstance(check_in_raw, datetime):
                    check_in = check_in_raw
                else:
                    check_in = datetime.fromisoformat(str(check_in_raw).replace('Z', '+00:00'))
                    
                if isinstance(check_out_raw, datetime):
                    check_out = check_out_raw
                else:
                    check_out = datetime.fromisoformat(str(check_out_raw).replace('Z', '+00:00'))
                
                # Check if reservation overlaps with requested date range
                if start_date:
                    filter_start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    if check_out < filter_start:
                        continue
                
                if end_date:
                    filter_end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    if check_in > filter_end:
                        continue
                
                filtered_reservations.append(reservation)
            
            reservations = filtered_reservations
        
        return jsonify({
            'success': True,
            'reservations': reservations,
            'total': len(reservations)
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
        reservations = get_user_reservations(user['id'])
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
        reservations = get_user_reservations(user['id'], filter_type='upcoming')
        
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
        reservations = get_user_reservations(user['id'], filter_type='current')
        
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