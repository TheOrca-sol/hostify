"""
Property management routes for Hostify Property Management Platform
"""

from flask import Blueprint, request, jsonify
from ..utils.database import (
    create_property, get_user_properties, get_property, update_property,
    get_property_reservations, get_user_by_firebase_uid, create_user,
    delete_property
)
from ..utils.auth import verify_firebase_token
from datetime import datetime

properties_bp = Blueprint('properties', __name__)

@properties_bp.route('/properties', methods=['POST'])
def create_property_route():
    """
    Create a new property for the authenticated user
    """
    try:
        # Verify Firebase token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        firebase_uid = verify_firebase_token(token)
        if not firebase_uid:
            return jsonify({'success': False, 'error': 'Invalid authentication token'}), 401
        
        # Get or create user record
        user = get_user_by_firebase_uid(firebase_uid)
        if not user:
            return jsonify({'success': False, 'error': 'User not found. Please complete profile setup.'}), 404
        
        # Get property data
        property_data = request.get_json()
        if not property_data:
            return jsonify({'success': False, 'error': 'No property data provided'}), 400
        
        # Validate required fields
        if not property_data.get('name'):
            return jsonify({'success': False, 'error': 'Property name is required'}), 400
        
        # Create property
        property_id = create_property(user['id'], **property_data)
        
        if property_id:
            # Get the complete property object to return
            created_property = get_property(property_id, user['id'])
            return jsonify({
                'success': True,
                'message': 'Property created successfully',
                'property': created_property
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create property'}), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to create property: {str(e)}'
        }), 500

@properties_bp.route('/properties', methods=['GET'])
def get_properties():
    """
    Get all properties for the authenticated user
    """
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
        
        # Get properties from database
        properties = get_user_properties(user['id'])
        
        return jsonify({
            'success': True,
            'properties': properties,
            'total': len(properties)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get properties: {str(e)}'
        }), 500

@properties_bp.route('/properties/<property_id>', methods=['GET'])
def get_property_route(property_id):
    """
    Get a specific property for the authenticated user
    """
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
        
        # Get property
        property_data = get_property(property_id, user['id'])
        if not property_data:
            return jsonify({'success': False, 'error': 'Property not found'}), 404
        
        return jsonify({
            'success': True,
            'property': property_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get property: {str(e)}'
        }), 500

@properties_bp.route('/properties/<property_id>', methods=['PUT'])
def update_property_route(property_id):
    """
    Update a property for the authenticated user
    """
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
        
        # Get update data
        update_data = request.get_json()
        if not update_data:
            return jsonify({'success': False, 'error': 'No update data provided'}), 400
        
        # Update property
        success = update_property(property_id, user['id'], update_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Property updated successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update property or property not found'}), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to update property: {str(e)}'
        }), 500

@properties_bp.route('/properties/<property_id>/reservations', methods=['GET'])
def get_property_reservations_route(property_id):
    """
    Get all reservations for a specific property
    """
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
        
        # Verify property ownership
        property_data = get_property(property_id, user['id'])
        if not property_data:
            return jsonify({'success': False, 'error': 'Property not found or access denied'}), 404
        
        # Get reservations for this property
        reservations = get_property_reservations(property_id)
        
        return jsonify({
            'success': True,
            'reservations': reservations,
            'total': len(reservations),
            'property': property_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get property reservations: {str(e)}'
        }), 500

@properties_bp.route('/properties/<property_id>', methods=['DELETE'])
def delete_property_route(property_id):
    """
    Delete a property and all its associated data (reservations, guests, contracts)
    """
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
        
        # Delete property and all associated data
        success = delete_property(property_id, user['id'])
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Property and all associated data deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to delete property or property not found'}), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to delete property: {str(e)}'
        }), 500

@properties_bp.route('/user/setup', methods=['POST'])
def setup_user():
    """
    Complete user profile setup after Firebase authentication
    """
    try:
        # Verify Firebase token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        firebase_uid = verify_firebase_token(token)
        if not firebase_uid:
            return jsonify({'success': False, 'error': 'Invalid authentication token'}), 401
        
        # Get user data
        user_data = request.get_json()
        if not user_data:
            return jsonify({'success': False, 'error': 'No user data provided'}), 400
        
        # Validate required fields
        required_fields = ['email', 'name']
        for field in required_fields:
            if not user_data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Check if user already exists
        existing_user = get_user_by_firebase_uid(firebase_uid)
        if existing_user:
            return jsonify({
                'success': True,
                'message': 'User already exists',
                'user': existing_user
            })
        
        # Create user record
        user_id = create_user(firebase_uid, **user_data)
        
        if user_id:
            user = get_user_by_firebase_uid(firebase_uid)
            return jsonify({
                'success': True,
                'message': 'User setup completed successfully',
                'user': user
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create user record'}), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to setup user: {str(e)}'
        }), 500

@properties_bp.route('/user/profile', methods=['GET'])
def get_user_profile():
    """
    Get user profile information
    """
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
            return jsonify({'success': False, 'error': 'User not found. Please complete profile setup.'}), 404
        
        return jsonify({
            'success': True,
            'user': user
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get user profile: {str(e)}'
        }), 500 