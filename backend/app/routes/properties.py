"""
Property management routes for Hostify Property Management Platform
"""

from flask import Blueprint, request, jsonify, g
from ..utils.database import (
    create_property, get_user_properties, get_property, update_property,
    get_property_reservations, get_user_by_firebase_uid, create_user,
    delete_property
)
from ..utils.auth import require_auth, get_current_user_id
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

properties_bp = Blueprint('properties', __name__)

@properties_bp.route('/properties', methods=['POST'])
@require_auth
def create_property_route():
    """
    Create a new property for the authenticated user
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
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
@require_auth
def get_properties():
    """
    Get all properties for the authenticated user
    """
    try:
        # Get user record
        logger.debug(f"Looking up user with firebase_uid: {g.user_id}")
        user = get_user_by_firebase_uid(g.user_id)
        
        if not user:
            # Create user if they don't exist
            logger.debug(f"User not found, creating new user for firebase_uid: {g.user_id}")
            user_id = create_user(
                firebase_uid=g.user_id,
                email=g.user.get('email', ''),
                name=g.user.get('name', 'New User')
            )
            user = get_user_by_firebase_uid(g.user_id)
            
        if not user:
            logger.error(f"Failed to get/create user for firebase_uid: {g.user_id}")
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get properties from database
        properties = get_user_properties(user['id'])
        logger.debug(f"Found {len(properties)} properties for user {user['id']}")
        
        return jsonify({
            'success': True,
            'properties': properties,
            'total': len(properties)
        })
    
    except Exception as e:
        logger.error(f"Failed to get properties: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get properties: {str(e)}'
        }), 500

@properties_bp.route('/properties/<property_id>', methods=['GET'])
@require_auth
def get_property_route(property_id):
    """
    Get a specific property for the authenticated user
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
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
@require_auth
def update_property_route(property_id):
    """
    Update a property for the authenticated user
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
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
@require_auth
def get_property_reservations_route(property_id):
    """
    Get all reservations for a specific property
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get property reservations
        reservations = get_property_reservations(property_id, user['id'])
        
        return jsonify({
            'success': True,
            'reservations': reservations,
            'total': len(reservations)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get reservations: {str(e)}'
        }), 500

@properties_bp.route('/properties/<property_id>', methods=['DELETE'])
@require_auth
def delete_property_route(property_id):
    """
    Delete a property for the authenticated user
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Delete property
        success = delete_property(property_id, user['id'])
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Property deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to delete property or property not found'}), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to delete property: {str(e)}'
        }), 500

@properties_bp.route('/user/setup', methods=['POST'])
@require_auth
def setup_user():
    """
    Setup a new user profile
    """
    try:
        # Get user data
        user_data = request.get_json()
        if not user_data:
            return jsonify({'success': False, 'error': 'No user data provided'}), 400
        
        # Create user with Firebase UID
        user_id = create_user(g.user_id, **user_data)
        
        if user_id:
            return jsonify({
                'success': True,
                'message': 'User profile created successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create user profile'}), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to setup user: {str(e)}'
        }), 500

@properties_bp.route('/user/profile', methods=['GET'])
@require_auth
def get_user_profile():
    """
    Get the current user's profile
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': user
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get user profile: {str(e)}'
        }), 500 