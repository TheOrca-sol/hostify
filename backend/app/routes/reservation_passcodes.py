"""
Reservation passcode management routes
"""

from flask import Blueprint, request, jsonify, g
from ..services.passcode_service import passcode_service
from ..services.background_jobs import background_scheduler
from ..services.notification_service import notification_service
from ..utils.auth import require_auth
from ..utils.database import get_user_by_firebase_uid
from ..models import Reservation, Property
import logging

# Configure logging
logger = logging.getLogger(__name__)

reservation_passcodes_bp = Blueprint('reservation_passcodes', __name__)

@reservation_passcodes_bp.route('/reservations/<reservation_id>/passcode', methods=['POST'])
@require_auth
def generate_reservation_passcode(reservation_id):
    """Generate passcode for a reservation"""
    try:
        # Get user
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Verify reservation belongs to user
        reservation = Reservation.query.get(reservation_id)
        if not reservation:
            return jsonify({'success': False, 'error': 'Reservation not found'}), 404

        # Check if user owns the property
        property_obj = Property.query.get(reservation.property_id)
        if not property_obj or property_obj.user_id != user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403

        # Generate passcode
        result = passcode_service.generate_reservation_passcode(reservation_id)

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error generating reservation passcode: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@reservation_passcodes_bp.route('/reservations/<reservation_id>/passcode', methods=['GET'])
@require_auth
def get_reservation_passcode(reservation_id):
    """Get passcode information for a reservation"""
    try:
        # Get user
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Verify reservation belongs to user
        reservation = Reservation.query.get(reservation_id)
        if not reservation:
            return jsonify({'success': False, 'error': 'Reservation not found'}), 404

        # Check if user owns the property
        property_obj = Property.query.get(reservation.property_id)
        if not property_obj or property_obj.user_id != user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403

        # Get passcode
        passcode_data = passcode_service.get_reservation_passcode(reservation_id)

        if passcode_data:
            return jsonify({
                'success': True,
                'passcode_data': passcode_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No passcode found for this reservation'
            }), 404

    except Exception as e:
        logger.error(f"Error getting reservation passcode: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@reservation_passcodes_bp.route('/reservation-passcodes/<passcode_id>/manual-update', methods=['PUT'])
@require_auth
def update_manual_passcode(passcode_id):
    """Update manual passcode with host-provided code"""
    try:
        # Get user
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get request data
        data = request.get_json()
        if not data or 'passcode' not in data:
            return jsonify({'success': False, 'error': 'Passcode is required'}), 400

        passcode = data['passcode'].strip()
        if not passcode:
            return jsonify({'success': False, 'error': 'Passcode cannot be empty'}), 400

        # Update manual passcode
        result = passcode_service.update_manual_passcode(passcode_id, passcode)

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error updating manual passcode: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@reservation_passcodes_bp.route('/reservations/<reservation_id>/passcode', methods=['DELETE'])
@require_auth
def revoke_reservation_passcode(reservation_id):
    """Revoke passcode for a reservation"""
    try:
        # Get user
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Verify reservation belongs to user
        reservation = Reservation.query.get(reservation_id)
        if not reservation:
            return jsonify({'success': False, 'error': 'Reservation not found'}), 404

        # Check if user owns the property
        property_obj = Property.query.get(reservation.property_id)
        if not property_obj or property_obj.user_id != user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403

        # Revoke passcode
        result = passcode_service.revoke_reservation_passcode(reservation_id)

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error revoking reservation passcode: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@reservation_passcodes_bp.route('/pending-manual-passcodes', methods=['GET'])
@require_auth
def get_pending_manual_passcodes():
    """Get all pending manual passcode entries for user's properties"""
    try:
        # Get user
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get pending manual passcodes
        pending_passcodes = passcode_service.get_pending_manual_passcodes(str(user.id))

        return jsonify({
            'success': True,
            'pending_passcodes': pending_passcodes,
            'count': len(pending_passcodes)
        })

    except Exception as e:
        logger.error(f"Error getting pending manual passcodes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@reservation_passcodes_bp.route('/background-jobs/status', methods=['GET'])
@require_auth
def get_background_job_status():
    """Get background job scheduler status (admin only)"""
    try:
        # Get user
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get background job status
        status = background_scheduler.get_status()

        return jsonify({
            'success': True,
            'background_jobs': status
        })

    except Exception as e:
        logger.error(f"Error getting background job status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@reservation_passcodes_bp.route('/reservation-passcodes/<passcode_id>/resend-notification', methods=['POST'])
@require_auth
def resend_notification(passcode_id):
    """Resend notification for a reservation passcode"""
    try:
        # Get user
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get request data
        data = request.get_json() or {}
        notification_type = data.get('type', 'auto')  # 'manual', 'ready', or 'auto'

        # Determine which notification to send based on type
        if notification_type == 'manual':
            result = notification_service.send_manual_passcode_notification(passcode_id)
        elif notification_type == 'ready':
            result = notification_service.send_passcode_ready_notification(passcode_id)
        else:
            # Auto-determine based on passcode status
            from ..models import ReservationPasscode
            passcode_entry = ReservationPasscode.query.get(passcode_id)
            if not passcode_entry:
                return jsonify({'success': False, 'error': 'Passcode not found'}), 404

            if passcode_entry.generation_method == 'manual' and not passcode_entry.passcode:
                result = notification_service.send_manual_passcode_notification(passcode_id)
            elif passcode_entry.passcode:
                result = notification_service.send_passcode_ready_notification(passcode_id)
            else:
                return jsonify({'success': False, 'error': 'Cannot determine notification type'}), 400

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error resending notification: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@reservation_passcodes_bp.route('/notification-history', methods=['GET'])
@require_auth
def get_notification_history():
    """Get notification history for user's properties"""
    try:
        # Get user
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        if limit > 50:  # Cap at 50
            limit = 50

        # Get notification history
        notifications = notification_service.get_notification_history(str(user.id), limit)

        return jsonify({
            'success': True,
            'notifications': notifications,
            'count': len(notifications)
        })

    except Exception as e:
        logger.error(f"Error getting notification history: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500