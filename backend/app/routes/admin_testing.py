"""
Admin testing routes for message and template testing
"""

from flask import Blueprint, request, jsonify, g
from ..models import db, MessageTemplate, Reservation, Guest, ScheduledMessage, Property
from ..utils.auth import require_auth
from ..utils.database import get_user_by_firebase_uid
from ..services.message_template_service import message_template_service
from datetime import datetime, timezone, timedelta
import uuid

admin_testing_bp = Blueprint('admin_testing', __name__, url_prefix='/api/admin')

@admin_testing_bp.route('/test-message-preview', methods=['POST'])
@require_auth
def test_message_preview():
    """Preview message template with populated variables"""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        data = request.get_json()
        template_id = data.get('template_id')
        reservation_id = data.get('reservation_id')

        if not template_id or not reservation_id:
            return jsonify({'success': False, 'error': 'template_id and reservation_id required'}), 400

        # Get template
        template = MessageTemplate.query.filter_by(id=template_id, user_id=user.id).first()
        if not template:
            return jsonify({'success': False, 'error': 'Template not found'}), 404

        # Get reservation
        reservation = Reservation.query.join(Property).filter(
            Reservation.id == reservation_id,
            Property.user_id == user.id
        ).first()
        if not reservation:
            return jsonify({'success': False, 'error': 'Reservation not found'}), 404

        # Get guest
        guest = reservation.guests[0] if reservation.guests else None
        property = reservation.property

        # Build basic variables
        variables = {
            'guest_name': guest.full_name if guest else reservation.guest_name_partial or 'Guest',
            'property_name': property.name if property else 'Property',
            'check_in_date': reservation.check_in.strftime('%B %d, %Y') if reservation.check_in else '',
            'check_out_date': reservation.check_out.strftime('%B %d, %Y') if reservation.check_out else '',
            'check_in_time': property.check_in_time.strftime('%H:%M') if property and property.check_in_time else reservation.check_in.strftime('%I:%M %p') if reservation.check_in else '',
            'check_out_time': property.check_out_time.strftime('%H:%M') if property and property.check_out_time else reservation.check_out.strftime('%I:%M %p') if reservation.check_out else '',
            'property_address': property.address if property else '',
            'host_name': property.owner.name if property and property.owner else 'Host',
            'host_phone': property.owner.phone if property and property.owner else '',
            'wifi_name': property.wifi_name if property else '',
            'wifi_password': property.wifi_password if property else '',
            'property_type': property.property_type if property else '',
            'access_instructions': property.access_instructions if property else '',
        }

        # Add smart lock variables
        smart_lock_vars = {}
        try:
            smart_lock_vars = message_template_service.get_smart_lock_variables(str(reservation.id))
            variables.update(smart_lock_vars)
        except Exception as e:
            print(f"Warning: Failed to load smart lock variables: {str(e)}")

        # Populate template content
        populated_content = template.content
        for key, value in variables.items():
            populated_content = populated_content.replace('{' + key + '}', str(value))
            populated_content = populated_content.replace('{{' + key + '}}', str(value))

        return jsonify({
            'success': True,
            'template': {
                'id': str(template.id),
                'name': template.name,
                'type': template.template_type,
                'original_content': template.content,
                'populated_content': populated_content
            },
            'reservation': {
                'id': str(reservation.id),
                'guest_name': guest.full_name if guest else reservation.guest_name_partial,
                'property_name': property.name if property else 'Unknown',
                'check_in': reservation.check_in.isoformat() if reservation.check_in else None,
                'check_out': reservation.check_out.isoformat() if reservation.check_out else None
            },
            'variables': variables,
            'smart_lock_variables': smart_lock_vars
        })

    except Exception as e:
        print(f"Error in test_message_preview: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_testing_bp.route('/send-test-message', methods=['POST'])
@require_auth
def send_test_message():
    """Schedule a test message to be sent immediately"""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        data = request.get_json()
        template_id = data.get('template_id')
        reservation_id = data.get('reservation_id')
        send_immediately = data.get('send_immediately', True)

        if not template_id or not reservation_id:
            return jsonify({'success': False, 'error': 'template_id and reservation_id required'}), 400

        # Verify template and reservation ownership
        template = MessageTemplate.query.filter_by(id=template_id, user_id=user.id).first()
        if not template:
            return jsonify({'success': False, 'error': 'Template not found'}), 404

        reservation = Reservation.query.join(Property).filter(
            Reservation.id == reservation_id,
            Property.user_id == user.id
        ).first()
        if not reservation:
            return jsonify({'success': False, 'error': 'Reservation not found'}), 404

        guest = reservation.guests[0] if reservation.guests else None
        if not guest:
            return jsonify({'success': False, 'error': 'No guest found for reservation'}), 404

        # Schedule the test message
        scheduled_for = datetime.now(timezone.utc) + timedelta(minutes=1 if send_immediately else 60)

        scheduled_message = ScheduledMessage(
            template_id=template.id,
            reservation_id=reservation.id,
            guest_id=guest.id,
            status='scheduled',
            scheduled_for=scheduled_for,
            channels=template.channels or ['sms']
        )

        db.session.add(scheduled_message)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Test message scheduled successfully',
            'scheduled_message': {
                'id': str(scheduled_message.id),
                'scheduled_for': scheduled_message.scheduled_for.isoformat(),
                'template_name': template.name,
                'guest_name': guest.full_name,
                'channels': scheduled_message.channels
            }
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error in send_test_message: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_testing_bp.route('/test-data', methods=['GET'])
@require_auth
def get_test_data():
    """Get reservations and templates for testing"""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get user's reservations
        reservations = Reservation.query.join(Property).filter(
            Property.user_id == user.id
        ).order_by(Reservation.check_in.desc()).limit(20).all()

        # Get user's templates
        templates = MessageTemplate.query.filter_by(user_id=user.id).order_by(MessageTemplate.created_at.desc()).all()

        return jsonify({
            'success': True,
            'reservations': [{
                'id': str(r.id),
                'guest_name': r.guests[0].full_name if r.guests else r.guest_name_partial or 'Unknown Guest',
                'property_name': r.property.name if r.property else 'Unknown Property',
                'check_in': r.check_in.isoformat() if r.check_in else None,
                'check_out': r.check_out.isoformat() if r.check_out else None,
                'status': r.status
            } for r in reservations],
            'templates': [{
                'id': str(t.id),
                'name': t.name,
                'type': t.template_type,
                'active': t.active,
                'content_preview': t.content[:100] + '...' if len(t.content) > 100 else t.content
            } for t in templates]
        })

    except Exception as e:
        print(f"Error in get_test_data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500