"""
Contract management routes
"""

from flask import Blueprint, request, jsonify, g
from ..models import db, Contract, Guest, MessageTemplate, ScheduledMessage
from ..utils.auth import require_auth
from ..utils.database import get_user_by_firebase_uid
from ..utils.sms import send_sms
from datetime import datetime, timedelta
import uuid

contracts_bp = Blueprint('contracts', __name__)

@contracts_bp.route('/pending', methods=['GET'])
@require_auth
def get_pending_contracts():
    """Get all pending contracts for the authenticated user"""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        contracts = Contract.query.join(Guest).join(Reservation).join(Property).filter(
            Property.user_id == user['id'],
            Contract.contract_status == 'generated'
        ).all()

        return jsonify({'success': True, 'contracts': [contract.to_dict() for contract in contracts]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@contracts_bp.route('/<contract_id>', methods=['GET'])
def get_contract(contract_id):
    """Get a specific contract by its ID"""
    try:
        contract = Contract.query.get(uuid.UUID(contract_id))
        if not contract:
            return jsonify({'success': False, 'error': 'Contract not found'}), 404
        return jsonify({'success': True, 'contract': contract.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@contracts_bp.route('/<contract_id>/sign', methods=['POST'])
def sign_contract(contract_id):
    """Sign a specific contract"""
    try:
        data = request.get_json()
        signature = data.get('signature')

        if not signature:
            return jsonify({'success': False, 'error': 'Signature is required'}), 400

        contract = Contract.query.get(uuid.UUID(contract_id))
        if not contract:
            return jsonify({'success': False, 'error': 'Contract not found'}), 404

        contract.contract_status = 'signed'
        contract.signed_at = datetime.utcnow()
        contract.signature = signature
        db.session.commit()

        return jsonify({'success': True, 'message': 'Contract signed successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
@contracts_bp.route('/generate-and-schedule-sms/<guest_id>', methods=['POST'])
@require_auth
def generate_contract_and_schedule_sms(guest_id):
    """Generate a contract and schedule an SMS to be sent to the guest"""
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

        # Create a contract
        contract = Contract(
            reservation_id=guest.reservation.id,
            guest_id=guest.id,
            template_id=guest.reservation.property.contract_template_id,
            contract_status='generated'
        )
        db.session.add(contract)
        db.session.commit()

        # Create a message template for the contract
        template = MessageTemplate(
            user_id=user['id'],
            name=f"Contract for {guest.full_name}",
            type='contract',
            subject='Your rental contract',
            content=f"Hello {guest.full_name}, please sign your rental contract: http://localhost:3000/contract/{contract.id}/sign",
            channels=['sms']
        )
        db.session.add(template)
        db.session.commit()

        # Schedule the SMS
        message = ScheduledMessage(
            template_id=template.id,
            reservation_id=guest.reservation.id,
            guest_id=guest.id,
            status='scheduled',
            scheduled_for=datetime.now() + timedelta(minutes=5),
            channels=['sms']
        )
        db.session.add(message)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Contract generated and SMS scheduled successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to generate contract and schedule SMS: {str(e)}'
        }), 500