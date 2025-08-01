"""
User management routes
"""
from flask import Blueprint, request, jsonify, g
from ..models import db, User
from ..utils.auth import require_auth
from ..utils.database import get_user_by_firebase_uid

user_bp = Blueprint('user', __name__)

@user_bp.route('/user/profile', methods=['GET'])
@require_auth
def get_user_profile():
    """Get a user's profile data"""
    try:
        user_info = get_user_by_firebase_uid(g.user_id)
        if not user_info:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        user = User.query.filter_by(id=user_info['id']).first()
        if not user:
            return jsonify({'success': False, 'error': 'User profile not found in database'}), 404

        return jsonify({'success': True, 'profile': user.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@user_bp.route('/user/setup', methods=['POST'])
@require_auth
def setup_user_profile():
    """Setup a new user profile"""
    try:
        user_data = request.get_json()
        if not user_data:
            return jsonify({'success': False, 'error': 'No user data provided'}), 400
        
        from ..utils.database import create_user
        user_id = create_user(g.user_id, **user_data)
        
        if user_id:
            return jsonify({'success': True, 'message': 'User profile created successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to create user profile'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to setup user: {str(e)}'}), 500
