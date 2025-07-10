"""
Contract management routes for Hostify Property Management Platform
"""

from flask import Blueprint, request, jsonify
from ..utils.database import (
    db, User, Property, Guest, Contract, ContractTemplate,
    get_user_by_firebase_uid
)
from ..utils.auth import verify_firebase_token
from ..utils.pdf import generate_contract_pdf
from datetime import datetime, timezone
import uuid

contracts_bp = Blueprint('contracts', __name__)

@contracts_bp.route('/contract-templates', methods=['POST'])
def create_template():
    """Create a new contract template"""
    try:
        # Verify Firebase token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        firebase_uid = verify_firebase_token(token)
        if not firebase_uid:
            return jsonify({'success': False, 'error': 'Invalid authentication token'}), 401
        
        # Get user record
        user = get_user_by_firebase_uid(firebase_uid)
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
def get_templates():
    """Get all contract templates for the user"""
    try:
        # Verify Firebase token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        firebase_uid = verify_firebase_token(token)
        if not firebase_uid:
            return jsonify({'success': False, 'error': 'Invalid authentication token'}), 401
        
        # Get user record
        user = get_user_by_firebase_uid(firebase_uid)
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
def update_template(template_id):
    """Update a contract template"""
    try:
        # Verify Firebase token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        firebase_uid = verify_firebase_token(token)
        if not firebase_uid:
            return jsonify({'success': False, 'error': 'Invalid authentication token'}), 401
        
        # Get user record
        user = get_user_by_firebase_uid(firebase_uid)
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
def generate_contract(guest_id):
    """Generate a contract for a guest"""
    try:
        # Verify Firebase token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        firebase_uid = verify_firebase_token(token)
        if not firebase_uid:
            return jsonify({'success': False, 'error': 'Invalid authentication token'}), 401
        
        # Get user record
        user = get_user_by_firebase_uid(firebase_uid)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get guest and verify ownership
        guest = Guest.query.filter_by(id=uuid.UUID(guest_id)).first()
        if not guest:
            return jsonify({'success': False, 'error': 'Guest not found'}), 404
        
        # Get reservation and property to verify ownership
        reservation = guest.reservation
        property = reservation.property
        if str(property.user_id) != user['id']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Get template (property-specific or user default)
        template = None
        if property.contract_template_id:
            template = ContractTemplate.query.get(property.contract_template_id)
        
        if not template:
            template = ContractTemplate.query.filter_by(
                user_id=uuid.UUID(user['id']),
                is_default=True
            ).first()
        
        if not template:
            return jsonify({'success': False, 'error': 'No contract template found'}), 404
        
        # Generate PDF
        pdf_path = generate_contract_pdf(template, guest, reservation, property)
        
        # Create contract record
        contract = Contract(
            reservation_id=reservation.id,
            guest_id=guest.id,
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
def sign_contract(contract_id):
    """Sign a contract"""
    try:
        # Get contract data
        signature_data = request.get_json()
        if not signature_data:
            return jsonify({'success': False, 'error': 'No signature data provided'}), 400
        
        # Get contract
        contract = Contract.query.filter_by(id=uuid.UUID(contract_id)).first()
        if not contract:
            return jsonify({'success': False, 'error': 'Contract not found'}), 404
        
        # Update contract
        contract.signature_data = signature_data
        contract.contract_status = 'signed'
        contract.signed_at = datetime.now(timezone.utc)
        contract.signature_ip = request.remote_addr
        
        # Generate signed PDF
        signed_pdf_path = generate_signed_contract_pdf(contract)
        contract.signed_pdf_path = signed_pdf_path
        
        # Update audit trail
        if not contract.audit_trail:
            contract.audit_trail = []
        contract.audit_trail.append({
            'action': 'signed',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'ip': request.remote_addr
        })
        
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
def get_contract(contract_id):
    """Get a specific contract"""
    try:
        # Verify Firebase token (for host access)
        auth_header = request.headers.get('Authorization')
        is_host = False
        if auth_header:
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            firebase_uid = verify_firebase_token(token)
            if firebase_uid:
                user = get_user_by_firebase_uid(firebase_uid)
                if user:
                    is_host = True
        
        # Get contract
        contract = Contract.query.filter_by(id=uuid.UUID(contract_id)).first()
        if not contract:
            return jsonify({'success': False, 'error': 'Contract not found'}), 404
        
        # If host, verify ownership
        if is_host:
            property = contract.reservation.property
            if str(property.user_id) != user['id']:
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