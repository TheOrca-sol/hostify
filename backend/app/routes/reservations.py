"""
Reservation management routes for Hostify Property Management Platform
"""

from flask import Blueprint, request, jsonify, g
from ..utils.database import (
    create_reservation, get_user_reservations, get_property_reservations,
    get_user_by_firebase_uid, get_property
)
from ..utils.auth import require_auth, get_current_user_id
from ..models import SmartLock, AccessCode, db
from ..services.ttlock_service import ttlock_service
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
            # Check if property has smart locks and attempt to generate access codes
            smart_locks = SmartLock.query.filter_by(property_id=reservation_data['property_id']).all()
            access_codes_generated = []
            smart_lock_warnings = []

            if smart_locks:
                logger.info(f"Found {len(smart_locks)} smart locks for property {reservation_data['property_id']}")

                # For each smart lock, attempt to generate a passcode
                for smart_lock in smart_locks:
                    try:
                        # Note: This will require TTLock credentials to be stored securely
                        # For now, we'll create a placeholder record that can be activated later
                        # Generate guest name from reservation data
                        guest_name = reservation_data.get('guest_name') or reservation_data.get('guest_email', 'Guest').split('@')[0]

                        access_code = AccessCode(
                            reservation_id=reservation_id,
                            smart_lock_id=smart_lock.id,
                            passcode=None,  # Will be generated when TTLock connection is available
                            passcode_id=None,
                            start_time=reservation_data['check_in'],
                            end_time=reservation_data['check_out'],
                            guest_phone=reservation_data.get('guest_phone'),
                            guest_email=reservation_data.get('guest_email'),
                            is_one_time=False,
                            status='pending',  # Will be activated when TTLock connection is available
                            access_type='reservation'
                        )

                        db.session.add(access_code)
                        access_codes_generated.append({
                            'smart_lock_id': str(smart_lock.id),
                            'lock_name': smart_lock.lock_name,
                            'status': 'pending',
                            'message': 'Access code will be generated when TTLock connection is available'
                        })

                        logger.info(f"Created pending access code for lock {smart_lock.lock_name}")

                    except Exception as e:
                        logger.error(f"Failed to create access code for lock {smart_lock.lock_name}: {str(e)}")
                        smart_lock_warnings.append({
                            'lock_name': smart_lock.lock_name,
                            'error': str(e)
                        })

                db.session.commit()

            response_data = {
                'success': True,
                'message': 'Reservation created successfully',
                'reservation_id': reservation_id
            }

            # Add smart lock information if applicable
            if smart_locks:
                response_data['smart_locks'] = {
                    'total_locks': len(smart_locks),
                    'access_codes_created': len(access_codes_generated),
                    'access_codes': access_codes_generated,
                    'warnings': smart_lock_warnings,
                    'note': 'Access codes are in pending status. They will be automatically generated when TTLock connection is available.'
                }

            return jsonify(response_data)
        else:
            return jsonify({'success': False, 'error': 'Failed to create reservation'}), 500
    
    except Exception as e:
        logger.error(f"Failed to create reservation: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to create reservation: {str(e)}'
        }), 500

@reservations_bp.route('/reservations/<reservation_id>/access-codes', methods=['GET'])
@require_auth
def get_reservation_access_codes(reservation_id):
    """Get all access codes for a reservation"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get access codes for this reservation
        from ..models import Reservation, Property
        access_codes = db.session.query(AccessCode)\
            .join(SmartLock)\
            .join(Property)\
            .join(Reservation)\
            .filter(
                AccessCode.reservation_id == reservation_id,
                Property.user_id == user.id
            ).all()

        return jsonify({
            'success': True,
            'access_codes': [code.to_dict() for code in access_codes]
        })

    except Exception as e:
        logger.error(f"Failed to get access codes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@reservations_bp.route('/reservations/<reservation_id>/activate-access-codes', methods=['POST'])
@require_auth
def activate_reservation_access_codes(reservation_id):
    """Activate pending access codes for a reservation (requires TTLock credentials)"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get pending access codes for this reservation
        from ..models import Reservation, Property
        pending_codes = db.session.query(AccessCode)\
            .join(SmartLock)\
            .join(Property)\
            .join(Reservation)\
            .filter(
                AccessCode.reservation_id == reservation_id,
                AccessCode.status == 'pending',
                Property.user_id == user.id
            ).all()

        if not pending_codes:
            return jsonify({
                'success': False,
                'error': 'No pending access codes found for this reservation'
            }), 404

        activated_codes = []
        failed_codes = []

        for access_code in pending_codes:
            try:
                # This would generate the actual passcode when TTLock credentials are available
                # For now, we'll mark them as requiring manual activation
                access_code.status = 'requires_ttlock_connection'
                activated_codes.append({
                    'access_code_id': str(access_code.id),
                    'smart_lock_name': access_code.smart_lock.lock_name,
                    'status': 'requires_ttlock_connection',
                    'message': 'Ready for activation - connect TTLock account first'
                })

            except Exception as e:
                failed_codes.append({
                    'access_code_id': str(access_code.id),
                    'error': str(e)
                })

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Updated {len(activated_codes)} access codes',
            'activated_codes': activated_codes,
            'failed_codes': failed_codes,
            'note': 'To complete activation, connect your TTLock account in Smart Locks settings'
        })

    except Exception as e:
        logger.error(f"Failed to activate access codes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

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