"""
Contract management routes for Hostify Property Management Platform
"""

from flask import Blueprint, request, jsonify, g
from ..utils.database import (
    db, User, Property, Guest, Contract, ContractTemplate, Reservation,
    get_user_by_firebase_uid
)
from ..utils.auth import require_auth
from ..utils.pdf import generate_contract_pdf
from datetime import datetime, timezone
import uuid

contracts_bp = Blueprint('contracts', __name__)

@contracts_bp.route('/contract-templates', methods=['POST'])
@require_auth
def create_template():
    """Create a new contract template"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get template data
        template_data = request.get_json()
        if not template_data:
            return jsonify({'success': False, 'error': 'No template data provided'}), 400
        
        # Validate required fields
        required_fields = ['name', 'template_content', 'language']
        for field in required_fields:
            if not template_data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Create template
        template = ContractTemplate(
            user_id=uuid.UUID(user['id']),
            name=template_data['name'],
            template_content=template_data['template_content'],
            language=template_data['language'],
            legal_jurisdiction=template_data.get('legal_jurisdiction'),
            is_default=template_data.get('is_default', False)
        )
        
        # If this is the default template, unset other defaults
        if template.is_default:
            ContractTemplate.query.filter_by(
                user_id=uuid.UUID(user['id']),
                is_default=True
            ).update({'is_default': False})
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contract template created successfully',
            'template': template.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to create template: {str(e)}'
        }), 500

@contracts_bp.route('/contract-templates', methods=['GET'])
@require_auth
def get_templates():
    """Get all contract templates for the user"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get templates
        templates = ContractTemplate.query.filter_by(
            user_id=uuid.UUID(user['id'])
        ).all()
        
        return jsonify({
            'success': True,
            'templates': [t.to_dict() for t in templates]
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get templates: {str(e)}'
        }), 500

@contracts_bp.route('/contract-templates/<template_id>', methods=['PUT'])
@require_auth
def update_template(template_id):
    """Update a contract template"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get template
        template = ContractTemplate.query.filter_by(
            id=uuid.UUID(template_id),
            user_id=uuid.UUID(user['id'])
        ).first()
        
        if not template:
            return jsonify({'success': False, 'error': 'Template not found'}), 404
        
        # Get update data
        update_data = request.get_json()
        if not update_data:
            return jsonify({'success': False, 'error': 'No update data provided'}), 400
        
        # Update allowed fields
        allowed_fields = ['name', 'template_content', 'language', 'legal_jurisdiction', 'is_default']
        for field in allowed_fields:
            if field in update_data:
                setattr(template, field, update_data[field])
        
        # If this is being set as default, unset other defaults
        if update_data.get('is_default'):
            ContractTemplate.query.filter(
                ContractTemplate.user_id == uuid.UUID(user['id']),
                ContractTemplate.id != template.id
            ).update({'is_default': False})
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Template updated successfully',
            'template': template.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to update template: {str(e)}'
        }), 500

@contracts_bp.route('/contracts/generate/<guest_id>', methods=['POST'])
@require_auth
def generate_contract(guest_id):
    """Generate a contract for a guest"""
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
        
        # Get template (either specified or default)
        template_id = request.json.get('template_id')
        if template_id:
            template = ContractTemplate.query.filter_by(
                id=uuid.UUID(template_id),
                user_id=uuid.UUID(user['id'])
            ).first()
        else:
            # Get default template
            template = ContractTemplate.query.filter(
                ContractTemplate.user_id == uuid.UUID(user['id']),
                ContractTemplate.is_default == True
            ).first()
        
        if not template:
            return jsonify({'success': False, 'error': 'No suitable template found'}), 404
        
        # Generate PDF
        pdf_path = generate_contract_pdf(template, guest)
        if not pdf_path:
            return jsonify({'success': False, 'error': 'Failed to generate PDF'}), 500
        
        # Create contract record
        contract = Contract(
            guest_id=guest.id,
            reservation_id=guest.reservation.id,
            template_id=template.id,
            generated_pdf_path=pdf_path,
            contract_status='generated'
        )
        
        db.session.add(contract)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contract generated successfully',
            'contract': contract.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to generate contract: {str(e)}'
        }), 500

@contracts_bp.route('/contracts/<contract_id>/sign', methods=['POST'])
@require_auth
def sign_contract(contract_id):
    """Sign a contract"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get contract and verify ownership
        contract = Contract.query.filter_by(id=uuid.UUID(contract_id)).first()
        if not contract:
            return jsonify({'success': False, 'error': 'Contract not found'}), 404
        
        # Verify ownership through guest -> reservation -> property
        if str(contract.guest.reservation.property.user_id) != user['id']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Get signature data
        signature_data = request.get_json()
        if not signature_data or 'signature' not in signature_data:
            return jsonify({'success': False, 'error': 'No signature provided'}), 400
        
        # Update contract
        contract.signature_data = signature_data
        contract.contract_status = 'signed'
        contract.signed_at = datetime.now(timezone.utc)
        contract.signature_ip = request.remote_addr
        
        # Generate signed PDF
        signed_pdf_path = generate_contract_pdf(
            contract.template,
            contract.guest,
            signature=signature_data['signature']
        )
        
        if not signed_pdf_path:
            return jsonify({'success': False, 'error': 'Failed to generate signed PDF'}), 500
        
        contract.signed_pdf_path = signed_pdf_path
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contract signed successfully',
            'contract': contract.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to sign contract: {str(e)}'
        }), 500

@contracts_bp.route('/contracts/<contract_id>', methods=['GET'])
@require_auth
def get_contract(contract_id):
    """Get a specific contract"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get contract and verify ownership
        contract = Contract.query.filter_by(id=uuid.UUID(contract_id)).first()
        if not contract:
            return jsonify({'success': False, 'error': 'Contract not found'}), 404
        
        # Verify ownership through guest -> reservation -> property
        if str(contract.guest.reservation.property.user_id) != user['id']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        return jsonify({
            'success': True,
            'contract': contract.to_dict()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get contract: {str(e)}'
        }), 500

@contracts_bp.route('/contracts/pending', methods=['GET'])
@require_auth
def get_pending_contracts():
    """Get all pending contracts for the user"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get all properties for the user
        user_properties = Property.query.filter_by(user_id=uuid.UUID(user['id'])).all()
        if not user_properties:
            return jsonify({'success': True, 'contracts': []})

        # Get all reservations for those properties
        property_ids = [p.id for p in user_properties]
        user_reservations = Reservation.query.filter(Reservation.property_id.in_(property_ids)).all()
        if not user_reservations:
            return jsonify({'success': True, 'contracts': []})

        # Get all contracts for those reservations with a 'pending' status
        reservation_ids = [r.id for r in user_reservations]
        pending_contracts = Contract.query.filter(
            Contract.reservation_id.in_(reservation_ids),
            Contract.contract_status == 'pending'
        ).all()

        return jsonify({
            'success': True,
            'contracts': [c.to_dict() for c in pending_contracts]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get pending contracts: {str(e)}'
        }), 500 