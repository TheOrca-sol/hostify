"""
Message template and scheduled message management routes
"""

from flask import Blueprint, request, jsonify, g
from ..models import MessageTemplate, ScheduledMessage, Contract, Reservation, Property, db
from ..utils.auth import require_auth
from ..utils.messaging import MessageService, MessageScheduler
from ..utils.database import get_user_by_firebase_uid
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
@messages_bp.route('/templates/<template_id>', methods=['OPTIONS'])
@messages_bp.route('/scheduled', methods=['OPTIONS'])
@messages_bp.route('/scheduled/<message_id>/send', methods=['OPTIONS'])
@messages_bp.route('/scheduled/<message_id>/cancel', methods=['OPTIONS'])
def handle_options():
    return '', 200

@messages_bp.route('/templates', methods=['GET'])
@require_auth
def get_templates():
    """Get all message templates for a user"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        property_id = request.args.get('property_id')
        
        # Query templates
        query = MessageTemplate.query.filter_by(user_id=user['id'])
        if property_id:
            query = query.filter(
                (MessageTemplate.property_id == property_id) |
                (MessageTemplate.property_id.is_(None))
            )
        
        templates = query.order_by(MessageTemplate.created_at.desc()).all()
        return jsonify([template.to_dict() for template in templates])
    except Exception as e:
        print(f"Error in get_templates: {str(e)}")
        return jsonify({"error": "Failed to fetch templates"}), 500

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
        required_fields = ['name', 'type', 'content', 'channels']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create template
        template = MessageTemplate(
            user_id=user['id'],  # Use the database UUID
            property_id=uuid.UUID(data['property_id']) if data.get('property_id') else None,
            name=data['name'],
            type=data['type'],
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
    template = MessageTemplate.query.filter_by(
        id=uuid.UUID(template_id),
        user_id=g.user_id
    ).first_or_404()
    
    data = request.get_json()
    
    # Update fields
    for field in ['name', 'type', 'subject', 'content', 'language', 'channels', 'variables', 'active']:
        if field in data:
            setattr(template, field, data[field])
    
    db.session.commit()
    return jsonify(template.to_dict())

@messages_bp.route('/templates/<template_id>', methods=['DELETE'])
@require_auth
def delete_template(template_id):
    """Delete a message template"""
    template = MessageTemplate.query.filter_by(
        id=uuid.UUID(template_id),
        user_id=g.user_id
    ).first_or_404()
    
    db.session.delete(template)
    db.session.commit()
    return '', 204

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

        # Base query
        query = ScheduledMessage.query.join(Reservation).join(Property).filter(Property.user_id == user['id'])

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