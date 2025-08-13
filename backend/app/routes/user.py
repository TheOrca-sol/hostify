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
    """Get user profile"""
    try:
        user_info = get_user_by_firebase_uid(g.user_id)
        
        if user_info:
            return jsonify({
                'success': True,
                'profile': user_info.to_dict()
            })
        else:
            return jsonify({'success': False, 'error': 'User profile not found'}), 404
    
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

@user_bp.route('/user/profile', methods=['PUT'])
@require_auth
def update_user_profile():
    """Update user profile"""
    try:
        user_data = request.get_json()
        if not user_data:
            return jsonify({'success': False, 'error': 'No user data provided'}), 400
        
        # Get current user
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Update allowed fields
        allowed_fields = ['name', 'phone', 'company_name', 'business_type', 'signature']
        for field in allowed_fields:
            if field in user_data:
                setattr(user, field, user_data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Profile updated successfully',
            'profile': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Failed to update profile: {str(e)}'}), 500
