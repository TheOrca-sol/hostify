"""
Team management routes for property collaboration
"""

from flask import Blueprint, request, jsonify, g
from ..utils.auth import require_auth
from ..utils.database import get_user_by_firebase_uid
from ..utils.team_management import (
    invite_team_member, accept_team_invitation, remove_team_member,
    get_property_team_members, check_user_property_permission
)
from ..models import TeamInvitation
import logging

logger = logging.getLogger(__name__)
team_bp = Blueprint('team', __name__)

@team_bp.route('/properties/<property_id>/team/invite', methods=['POST'])
@require_auth
def invite_team_member_route(property_id):
    """
    Invite someone to join a property team
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get invitation data
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # Validate required fields
        invited_email = data.get('email')
        invited_phone = data.get('phone')
        invitation_method = data.get('invitation_method', 'email')  # 'email' or 'sms'
        role = data.get('role')
        custom_permissions = data.get('permissions')

        # Check that either email or phone is provided based on method
        if invitation_method == 'email':
            if not invited_email or not role:
                return jsonify({'success': False, 'error': 'Email and role are required for email invitations'}), 400
        elif invitation_method == 'sms':
            if not invited_phone or not role:
                return jsonify({'success': False, 'error': 'Phone number and role are required for SMS invitations'}), 400
        else:
            return jsonify({'success': False, 'error': 'Invalid invitation method. Must be "email" or "sms"'}), 400

        # Valid roles
        valid_roles = ['cohost', 'agency', 'cleaner', 'maintenance', 'assistant']
        if role not in valid_roles:
            return jsonify({'success': False, 'error': f'Invalid role. Must be one of: {valid_roles}'}), 400

        # Send invitation based on method
        if invitation_method == 'sms':
            from ..utils.team_management import invite_team_member_sms
            result = invite_team_member_sms(
                inviter_user_id=user['id'],
                property_id=property_id,
                invited_phone=invited_phone,
                role=role,
                custom_permissions=custom_permissions
            )
            contact_info = invited_phone
        else:
            result = invite_team_member(
                inviter_user_id=user['id'],
                property_id=property_id,
                invited_email=invited_email,
                role=role,
                custom_permissions=custom_permissions
            )
            contact_info = invited_email

        if result['success']:
            return jsonify({
                'success': True,
                'message': f'Invitation sent to {contact_info}',
                'invitation_token': result.get('invitation_token'),
                'invitation_url': result.get('invitation_url'),
                'method': invitation_method
            })
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error inviting team member: {e}")
        return jsonify({'success': False, 'error': 'Failed to send invitation'}), 500

@team_bp.route('/properties/<property_id>/team', methods=['GET'])
@require_auth
def get_team_members(property_id):
    """
    Get all team members for a property
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get team members
        result = get_property_team_members(property_id, user['id'])
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 403

    except Exception as e:
        logger.error(f"Error getting team members: {e}")
        return jsonify({'success': False, 'error': 'Failed to get team members'}), 500

@team_bp.route('/properties/<property_id>/team/<member_user_id>', methods=['DELETE'])
@require_auth
def remove_team_member_route(property_id, member_user_id):
    """
    Remove a team member from a property
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Remove team member
        result = remove_team_member(
            remover_user_id=user['id'],
            property_id=property_id,
            member_user_id=member_user_id
        )

        if result['success']:
            return jsonify({'success': True, 'message': 'Team member removed successfully'})
        else:
            return jsonify(result), 403

    except Exception as e:
        logger.error(f"Error removing team member: {e}")
        return jsonify({'success': False, 'error': 'Failed to remove team member'}), 500

@team_bp.route('/team/invitations/accept/<invitation_token>', methods=['POST'])
@require_auth
def accept_invitation(invitation_token):
    """
    Accept a team invitation
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Accept invitation
        result = accept_team_invitation(invitation_token, user['id'])

        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Invitation accepted successfully',
                'property_id': result['property_id'],
                'role': result['role']
            })
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error accepting invitation: {e}")
        return jsonify({'success': False, 'error': 'Failed to accept invitation'}), 500

@team_bp.route('/team/invitations/<invitation_token>', methods=['GET'])
def get_invitation_details(invitation_token):
    """
    Get invitation details (for the invitation page)
    """
    try:
        # Find invitation
        invitation = TeamInvitation.query.filter_by(
            invitation_token=invitation_token,
            status='pending'
        ).first()

        if not invitation:
            return jsonify({'success': False, 'error': 'Invalid or expired invitation'}), 404

        # Check if expired
        from datetime import datetime, timezone
        if invitation.expires_at < datetime.now(timezone.utc):
            invitation.status = 'expired'
            from ..models import db
            db.session.commit()
            return jsonify({'success': False, 'error': 'Invitation has expired'}), 410

        return jsonify({
            'success': True,
            'invitation': {
                'id': str(invitation.id),
                'property_name': invitation.property.name,
                'property_address': invitation.property.address,
                'role': invitation.role,
                'inviter_name': invitation.inviter.name,
                'invited_email': invitation.invited_email,
                'expires_at': invitation.expires_at.isoformat(),
                'permissions': invitation.permissions
            }
        })

    except Exception as e:
        logger.error(f"Error getting invitation details: {e}")
        return jsonify({'success': False, 'error': 'Failed to get invitation details'}), 500

@team_bp.route('/team/my-invitations', methods=['GET'])
@require_auth 
def get_my_invitations():
    """
    Get pending invitations for the current user
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get pending invitations for this user's email
        invitations = TeamInvitation.query.filter_by(
            invited_email=user['email'],
            status='pending'
        ).all()

        # Filter out expired invitations
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        valid_invitations = []
        
        for invitation in invitations:
            if invitation.expires_at > now:
                valid_invitations.append(invitation.to_dict())
            else:
                invitation.status = 'expired'

        from ..models import db
        db.session.commit()

        return jsonify({
            'success': True,
            'invitations': valid_invitations
        })

    except Exception as e:
        logger.error(f"Error getting user invitations: {e}")
        return jsonify({'success': False, 'error': 'Failed to get invitations'}), 500 