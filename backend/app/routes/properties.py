"""
Property management routes for Hostify Property Management Platform
"""

from flask import Blueprint, request, jsonify, g
from ..utils.database import (
    create_property, get_property, update_property,
    get_property_reservations, get_user_by_firebase_uid, create_user,
    delete_property, get_property_by_ical_url
)
from ..utils.auth import require_auth, get_current_user_id
from ..utils.team_management import get_user_properties, check_user_property_permission
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

        # Validate for duplicate iCal URL
        if property_data.get('ical_url'):
            existing_property = get_property_by_ical_url(property_data['ical_url'])
            if existing_property:
                return jsonify({
                    'success': False,
                    'error': 'This iCal link is already in use by another property.'
                }), 409

        # Create property
        property_id = create_property(user.id, **property_data)
        
        if property_id:
            # Get the complete property object to return
            created_property = get_property(property_id, user.id)
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
        
        # Get all properties (owned + assigned) using new team management system
        user_properties_data = get_user_properties(user.id)
        logger.debug(f"Found {len(user_properties_data)} properties for user {user.id}")
        
        # Format the response to include relationship info
        properties = []
        for prop_data in user_properties_data:
            property_dict = prop_data['property'].to_dict()
            property_dict['relationship_type'] = prop_data['relationship_type']
            property_dict['role'] = prop_data['role']
            property_dict['permissions'] = prop_data['permissions']
            properties.append(property_dict)
        
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
        property_data = get_property(property_id, user.id)
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
        success = update_property(property_id, user.id, update_data)
        
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
        reservations = get_property_reservations(property_id, user.id)
        
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
        success = delete_property(property_id, user.id)
        
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