"""
Message template and scheduled message management routes
"""

from flask import Blueprint, request, jsonify, g
from ..models import MessageTemplate, ScheduledMessage, Contract, Reservation, Property, db
from ..utils.auth import require_auth
from ..utils.messaging import MessageService, MessageScheduler
from ..utils.database import get_user_by_firebase_uid
from ..services.message_template_service import message_template_service
from ..constants import TEMPLATE_TYPES # Import from the new central location
from datetime import datetime, timezone
from sqlalchemy import or_
import uuid

messages_bp = Blueprint('messages', __name__)

# Add CORS support
@messages_bp.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Handle OPTIONS requests for CORS
@messages_bp.route('/templates', methods=['OPTIONS'])
@messages_bp.route('/scheduled', methods=['OPTIONS'])
@messages_bp.route('/scheduled/<message_id>/send', methods=['OPTIONS'])
@messages_bp.route('/scheduled/<message_id>/cancel', methods=['OPTIONS'])
def handle_options():
    return '', 200

@messages_bp.route('/templates/<template_id>', methods=['OPTIONS'])
def handle_template_options(template_id):
    return '', 200

@messages_bp.route('/templates', methods=['GET'])
@require_auth
def get_templates():
    """Get all message templates for a user and the available template types."""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        property_id = request.args.get('property_id')
        manual_only = request.args.get('manual', 'false').lower() == 'true'
        
        query = MessageTemplate.query.filter_by(user_id=user.id)
        
        if property_id:
            query = query.filter(
                (MessageTemplate.property_id == property_id) |
                (MessageTemplate.property_id.is_(None))
            )
        
        if manual_only:
            query = query.filter(MessageTemplate.trigger_event.is_(None))
        
        templates = query.order_by(MessageTemplate.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'templates': [template.to_dict() for template in templates],
            'template_types': TEMPLATE_TYPES
        })
    except Exception as e:
        print(f"Error in get_templates: {str(e)}")
        return jsonify({"success": False, "error": "Failed to fetch templates"}), 500

@messages_bp.route('/templates', methods=['POST'])
@require_auth
def create_template():
    """Create a new message template"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'template_type', 'content', 'channels']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create template
        template = MessageTemplate(
            user_id=user.id,  # Use the database UUID
            property_id=uuid.UUID(data['property_id']) if data.get('property_id') else None,
            name=data['name'],
            template_type=data['template_type'],
            subject=data.get('subject'),
            content=data['content'],
            language=data.get('language', 'en'),
            channels=data['channels'],
            variables=data.get('variables'),
            active=data.get('active', True)
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify(template.to_dict()), 201
    except Exception as e:
        print(f"Error in create_template: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to create template"}), 500

@messages_bp.route('/templates/<template_id>', methods=['PUT'])
@require_auth
def update_template(template_id):
    """Update an existing message template"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        template = MessageTemplate.query.filter_by(
            id=uuid.UUID(template_id),
            user_id=user.id
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        for field in ['name', 'template_type', 'subject', 'content', 'language', 'channels', 'variables', 'active', 'trigger_event', 'trigger_offset_value', 'trigger_offset_unit', 'trigger_direction']:
            if field in data:
                setattr(template, field, data[field])
        
        db.session.commit()
        return jsonify({'success': True, 'template': template.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating template: {str(e)}")
        return jsonify({'error': 'Failed to update template'}), 500

@messages_bp.route('/templates/<template_id>', methods=['DELETE'])
@require_auth
def delete_template(template_id):
    """Delete a message template"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        template = MessageTemplate.query.filter_by(
            id=uuid.UUID(template_id),
            user_id=user.id
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        db.session.delete(template)
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting template: {str(e)}")
        return jsonify({'error': 'Failed to delete template'}), 500

@messages_bp.route('/scheduled', methods=['GET'])
@require_auth
def get_scheduled_messages():
    """Get all scheduled messages for the user's properties"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        reservation_id = request.args.get('reservation_id')

        # Base query with eager loading
        query = ScheduledMessage.query.join(Reservation).join(Property).options(
            db.joinedload(ScheduledMessage.template),
            db.joinedload(ScheduledMessage.guest),
            db.joinedload(ScheduledMessage.reservation).joinedload(Reservation.property)
        ).filter(Property.user_id == user.id)

        # Filter by reservation if provided
        if reservation_id:
            query = query.filter(ScheduledMessage.reservation_id == reservation_id)

        messages = query.order_by(ScheduledMessage.scheduled_for.desc()).all()

        return jsonify({
            'success': True,
            'messages': [message.to_dict() for message in messages]
        })
    except Exception as e:
        print(f"Error getting scheduled messages: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to fetch scheduled messages: {str(e)}'
        }), 500

@messages_bp.route('/scheduled/<message_id>/send', methods=['POST'])
@require_auth
def send_message_now(message_id):
    """Manually send a scheduled message immediately"""
    try:
        message = ScheduledMessage.query.filter_by(id=uuid.UUID(message_id)).first_or_404()
        
        # Update scheduled time to now
        message.scheduled_for = datetime.now(timezone.utc)
        db.session.commit()
        
        # Send message
        message_service = MessageService()
        success = message_service.send_scheduled_message_sync(message)
        
        if success:
            return jsonify({'success': True, 'status': 'sent'})
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send message'
            }), 500
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to send message'
        }), 500

@messages_bp.route('/scheduled/<message_id>/cancel', methods=['POST'])
@require_auth
def cancel_scheduled_message(message_id):
    """Cancel a scheduled message"""
    try:
        message = ScheduledMessage.query.filter_by(id=uuid.UUID(message_id)).first_or_404()
        
        if message.status == 'scheduled':
            message.status = 'cancelled'
            db.session.commit()
            return jsonify({'success': True, 'status': 'cancelled'})
        else:
            return jsonify({
                'success': False,
                'error': 'Message cannot be cancelled'
            }), 400
    except Exception as e:
        print(f"Error cancelling message: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to cancel message'
        }), 500

@messages_bp.route('/send-manual', methods=['POST'])
@require_auth
def send_manual_message():
    """Send a manual message immediately."""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        data = request.get_json()
        template_id = data.get('template_id')
        reservation_id = data.get('reservation_id')

        if not template_id or not reservation_id:
            return jsonify({'success': False, 'error': 'template_id and reservation_id are required'}), 400

        # Fetch the template and reservation to ensure they exist and belong to the user
        template = MessageTemplate.query.filter_by(id=uuid.UUID(template_id), user_id=user.id).first()
        if not template:
            return jsonify({'success': False, 'error': 'Template not found'}), 404

        reservation = Reservation.query.get(uuid.UUID(reservation_id))
        if not reservation or str(reservation.property.user_id) != user.id:
            return jsonify({'success': False, 'error': 'Reservation not found'}), 404
        
        guest = reservation.guests[0] if reservation.guests else None
        if not guest:
            return jsonify({'success': False, 'error': 'No guest associated with this reservation'}), 404

        # Create a new scheduled message record to be sent immediately
        new_message = ScheduledMessage(
            template_id=template.id,
            reservation_id=reservation.id,
            guest_id=guest.id,
            scheduled_for=datetime.now(timezone.utc),
            status='scheduled', # It will be updated to 'sent' by the service
            channels=template.channels
        )
        db.session.add(new_message)
        db.session.commit()

        # Use the message service to send it now
        message_service = MessageService()
        success = message_service.send_scheduled_message_sync(new_message)

        if success:
            return jsonify({'success': True, 'message': 'Message sent successfully.'})
        else:
            return jsonify({'success': False, 'error': 'Failed to send message.'}), 500

    except Exception as e:
        db.session.rollback()
        print(f"Error in send_manual_message: {str(e)}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred.'}), 500


@messages_bp.route('/schedule-reservation', methods=['POST'])
@require_auth
def schedule_reservation_messages():
    """Schedule all messages for a reservation"""
    try:
        reservation_id = request.json.get('reservation_id')
        if not reservation_id:
            return jsonify({
                'success': False,
                'error': 'reservation_id is required'
            }), 400
        
        scheduled_ids = MessageScheduler.schedule_reservation_messages_sync(reservation_id)
        return jsonify({
            'success': True,
            'status': 'scheduled',
            'message_ids': scheduled_ids
        })
    except Exception as e:
        print(f"Error scheduling messages: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to schedule messages'
        }), 500

@messages_bp.route('/smart-lock-variables', methods=['GET'])
@require_auth
def get_smart_lock_variables():
    """Get available smart lock template variables"""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        variables = message_template_service.get_available_smart_lock_variables()

        return jsonify({
            'success': True,
            'variables': variables
        })

    except Exception as e:
        print(f"Error getting smart lock variables: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get smart lock variables'
        }), 500

@messages_bp.route('/create-smart-lock-templates', methods=['POST'])
@require_auth
def create_smart_lock_templates():
    """Create default smart lock templates for a property"""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        property_id = request.json.get('property_id')
        if not property_id:
            return jsonify({
                'success': False,
                'error': 'property_id is required'
            }), 400

        # Verify user owns the property
        property_obj = Property.query.get(property_id)
        if not property_obj or property_obj.user_id != user.id:
            return jsonify({'error': 'Property not found or access denied'}), 403

        # Create default smart lock templates
        templates = message_template_service.create_default_smart_lock_templates(
            str(user.id), property_id
        )

        return jsonify({
            'success': True,
            'message': f'Created {len(templates)} smart lock templates',
            'templates': templates
        })

    except Exception as e:
        print(f"Error creating smart lock templates: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create smart lock templates'
        }), 500

@messages_bp.route('/test-smart-lock-template', methods=['POST'])
@require_auth
def test_smart_lock_template():
    """Test smart lock template variable population"""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        reservation_id = request.json.get('reservation_id')
        template_content = request.json.get('content', '')

        if not reservation_id:
            return jsonify({
                'success': False,
                'error': 'reservation_id is required'
            }), 400

        # Verify user has access to this reservation
        reservation = Reservation.query.get(reservation_id)
        if not reservation:
            return jsonify({'error': 'Reservation not found'}), 404

        property_obj = Property.query.get(reservation.property_id)
        if not property_obj or property_obj.user_id != user.id:
            return jsonify({'error': 'Reservation not found or access denied'}), 403

        # Populate smart lock variables in template
        populated_content = message_template_service.populate_smart_lock_variables(
            template_content, reservation_id
        )

        # Also get the variables for reference
        smart_lock_vars = message_template_service.get_smart_lock_variables(reservation_id)

        return jsonify({
            'success': True,
            'original_content': template_content,
            'populated_content': populated_content,
            'smart_lock_variables': smart_lock_vars
        })

    except Exception as e:
        print(f"Error testing smart lock template: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to test smart lock template'
        }), 500 