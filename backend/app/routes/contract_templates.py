"""
Contract template management routes
"""
from flask import Blueprint, request, jsonify, g
from ..models import db, ContractTemplate
from ..utils.auth import require_auth
from ..utils.database import get_user_by_firebase_uid
import uuid
import logging

contract_templates_bp = Blueprint('contract_templates', __name__, url_prefix='/contract-templates')

@contract_templates_bp.route('', methods=['OPTIONS', 'GET'])
@contract_templates_bp.route('/', methods=['OPTIONS', 'GET'])
@require_auth
def get_contract_templates():
    """Get all contract templates for a user"""
    if request.method == 'OPTIONS':
        return '', 200
    try:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug(f"g.user_id from token: {g.user_id}")
        
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        logging.debug(f"User object from database: {user}")
        logging.debug(f"User ID to be used in query: {user['id']}")

        user_uuid = uuid.UUID(user['id']) # Convert string to UUID object
        templates = ContractTemplate.query.filter_by(user_id=user_uuid).all()
        return jsonify({'success': True, 'templates': [template.to_dict() for template in templates]})
    except Exception as e:
        logging.error(f"Error in get_contract_templates: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contract_templates_bp.route('/', methods=['POST'])
@require_auth
def create_contract_template():
    """Create a new contract template"""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        data = request.get_json()
        if not data or not data.get('name') or not data.get('template_content'):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        template = ContractTemplate(
            user_id=uuid.UUID(user['id']),
            name=data['name'],
            template_content=data['template_content'],
            language=data.get('language', 'en'),
            legal_jurisdiction=data.get('legal_jurisdiction')
        )
        db.session.add(template)
        db.session.commit()
        return jsonify({'success': True, 'template': template.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@contract_templates_bp.route('/<template_id>', methods=['PUT'])
@require_auth
def update_contract_template(template_id):
    """Update an existing contract template"""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        user_uuid = uuid.UUID(user['id'])
        template = ContractTemplate.query.filter_by(id=uuid.UUID(template_id), user_id=user_uuid).first_or_404()
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No update data provided'}), 400

        template.name = data.get('name', template.name)
        template.template_content = data.get('template_content', template.template_content)
        template.language = data.get('language', template.language)
        template.legal_jurisdiction = data.get('legal_jurisdiction', template.legal_jurisdiction)
        
        db.session.commit()
        return jsonify({'success': True, 'template': template.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@contract_templates_bp.route('/<template_id>', methods=['DELETE'])
@require_auth
def delete_contract_template(template_id):
    """Delete a contract template"""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        user_uuid = uuid.UUID(user['id'])
        template = ContractTemplate.query.filter_by(id=uuid.UUID(template_id), user_id=user_uuid).first_or_404()
        db.session.delete(template)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Template deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
