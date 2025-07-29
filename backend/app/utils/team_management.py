"""
Team management utilities for property collaboration
"""

import uuid
import secrets
from datetime import datetime, timezone, timedelta
from flask import current_app
from ..models import db, Property, PropertyTeamMember, TeamInvitation, User

# Default permissions for each role
DEFAULT_PERMISSIONS = {
    'cohost': {
        'manage_guests': True,
        'manage_reservations': True,
        'manage_contracts': True,
        'schedule_cleaning': True,
        'schedule_maintenance': True,
        'invite_team_members': True,
        'view_financials': True,
        'modify_property_settings': True,
        'delete_property': True,
        'remove_team_members': True
    },
    'agency': {
        'manage_guests': True,
        'manage_reservations': True,
        'manage_contracts': True,
        'schedule_cleaning': True,
        'schedule_maintenance': True,
        'invite_team_members': True,
        'view_financials': True,
        'modify_property_settings': True,
        'delete_property': True,
        'remove_team_members': True
    },
    'cleaner': {
        'view_cleaning_tasks': True,
        'update_cleaning_status': True,
        'upload_photos': True,
        'request_supplies': True,
        'view_property_access': True,
        'manage_guests': False,
        'view_financials': False
    },
    'maintenance': {
        'view_maintenance_tasks': True,
        'update_task_status': True,
        'upload_photos': True,
        'submit_invoices': True,
        'emergency_contact': True,
        'view_property_access': True,
        'manage_guests': False,
        'view_financials': False
    },
    'assistant': {
        'view_reservations': True,
        'view_guest_info': True,
        'view_tasks': True,
        'basic_communication': True,
        'manage_anything': False
    }
}

def get_user_properties(user_id):
    """
    Get all properties a user has access to (owned + assigned)
    Returns list of properties with relationship type
    """
    try:
        # Properties they own
        owned_properties = db.session.query(Property).filter(
            Property.user_id == user_id
        ).all()
        
        # Properties they're assigned to as team members
        assigned_properties = db.session.query(
            Property, PropertyTeamMember.role
        ).join(PropertyTeamMember).filter(
            PropertyTeamMember.user_id == user_id,
            PropertyTeamMember.is_active == True
        ).all()
        
        # Combine results
        properties = []
        
        # Add owned properties
        for prop in owned_properties:
            properties.append({
                'property': prop,
                'relationship_type': 'owner',
                'role': 'owner',
                'permissions': DEFAULT_PERMISSIONS['cohost']  # Owners have all permissions
            })
        
        # Add assigned properties
        for prop, role in assigned_properties:
            team_member = PropertyTeamMember.query.filter_by(
                property_id=prop.id,
                user_id=user_id,
                is_active=True
            ).first()
            
            properties.append({
                'property': prop,
                'relationship_type': 'team_member',
                'role': role,
                'permissions': team_member.permissions or DEFAULT_PERMISSIONS.get(role, {})
            })
        
        return properties
        
    except Exception as e:
        current_app.logger.error(f"Error getting user properties: {e}")
        return []

def check_user_property_permission(user_id, property_id, permission):
    """
    Check if user has specific permission for a property
    """
    try:
        # Convert property_id to UUID if it's a string
        if isinstance(property_id, str):
            import uuid as uuid_module
            property_id = uuid_module.UUID(property_id)
        
        # Check if they own the property
        property_obj = Property.query.filter_by(id=property_id, user_id=user_id).first()
        if property_obj:
            return True  # Owners have all permissions
        
        # Check if they're a team member with the permission
        team_member = PropertyTeamMember.query.filter_by(
            property_id=property_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if team_member:
            permissions = team_member.permissions or DEFAULT_PERMISSIONS.get(team_member.role, {})
            return permissions.get(permission, False)
        
        return False
        
    except Exception as e:
        current_app.logger.error(f"Error checking permission: {e}")
        return False

def invite_team_member(inviter_user_id, property_id, invited_email, role, custom_permissions=None):
    """
    Invite someone to join a property team
    """
    try:
        # Convert property_id to UUID if it's a string
        if isinstance(property_id, str):
            import uuid as uuid_module
            property_id = uuid_module.UUID(property_id)
        
        # Verify inviter has permission
        if not check_user_property_permission(inviter_user_id, property_id, 'invite_team_members'):
            return {'success': False, 'error': 'You do not have permission to invite team members'}
        
        # Check if invitation already exists
        existing_invitation = TeamInvitation.query.filter_by(
            property_id=property_id,
            invited_email=invited_email,
            status='pending'
        ).first()
        
        if existing_invitation:
            return {'success': False, 'error': 'Invitation already sent to this email'}
        
        # Check if user is already a team member
        invited_user = User.query.filter_by(email=invited_email).first()
        if invited_user:
            existing_member = PropertyTeamMember.query.filter_by(
                property_id=property_id,
                user_id=invited_user.id,
                is_active=True
            ).first()
            
            if existing_member:
                return {'success': False, 'error': 'User is already a team member'}
        
        # Create invitation
        invitation_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)  # 7 days to accept
        
        # Use custom permissions or default for role
        permissions = custom_permissions or DEFAULT_PERMISSIONS.get(role, {})
        
        invitation = TeamInvitation(
            property_id=property_id,
            inviter_user_id=inviter_user_id,
            invited_email=invited_email,
            role=role,
            permissions=permissions,
            invitation_token=invitation_token,
            expires_at=expires_at
        )
        
        db.session.add(invitation)
        db.session.commit()
        
        # Send invitation email
        try:
            from .email_service import send_team_invitation_email
            
            # Get inviter and property details
            inviter = User.query.get(inviter_user_id)
            property_obj = Property.query.get(property_id)
            
            email_result = send_team_invitation_email(
                invited_email=invited_email,
                inviter_name=inviter.name if inviter else 'Unknown',
                property_name=property_obj.name if property_obj else 'Unknown Property',
                role=role,
                invitation_token=invitation_token,
                expires_at=expires_at
            )
            
            # Log email sending result
            if email_result['success']:
                current_app.logger.info(f"Invitation email sent to {invited_email} via {email_result.get('method', 'unknown')}")
            else:
                current_app.logger.error(f"Failed to send invitation email: {email_result.get('error')}")
                
        except Exception as email_error:
            current_app.logger.error(f"Error sending invitation email: {email_error}")
            # Don't fail the invitation if email fails
        
        return {
            'success': True,
            'invitation_id': str(invitation.id),
            'invitation_token': invitation_token,
            'expires_at': expires_at.isoformat()
        }
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error inviting team member: {e}")
        return {'success': False, 'error': 'Failed to send invitation'}

def accept_team_invitation(invitation_token, user_id):
    """
    Accept a team invitation
    """
    try:
        # Find the invitation
        invitation = TeamInvitation.query.filter_by(
            invitation_token=invitation_token,
            status='pending'
        ).first()
        
        if not invitation:
            return {'success': False, 'error': 'Invalid or expired invitation'}
        
        # Check if invitation has expired
        if invitation.expires_at < datetime.now(timezone.utc):
            invitation.status = 'expired'
            db.session.commit()
            return {'success': False, 'error': 'Invitation has expired'}
        
        # Get the user
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        # Verify email matches
        if user.email != invitation.invited_email:
            return {'success': False, 'error': 'Email does not match invitation'}
        
        # Check if already a team member
        existing_member = PropertyTeamMember.query.filter_by(
            property_id=invitation.property_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if existing_member:
            return {'success': False, 'error': 'Already a team member'}
        
        # Create team membership
        team_member = PropertyTeamMember(
            property_id=invitation.property_id,
            user_id=user_id,
            role=invitation.role,
            permissions=invitation.permissions,
            invited_by_user_id=invitation.inviter_user_id,
            accepted_at=datetime.now(timezone.utc)
        )
        
        # Update invitation status
        invitation.status = 'accepted'
        invitation.accepted_at = datetime.now(timezone.utc)
        
        db.session.add(team_member)
        db.session.commit()
        
        # Send acceptance notification to inviter
        try:
            from .email_service import send_invitation_accepted_email
            
            # Get inviter and property details
            inviter = User.query.get(invitation.inviter_user_id)
            property_obj = Property.query.get(invitation.property_id)
            
            if inviter and property_obj:
                send_invitation_accepted_email(
                    inviter_email=inviter.email,
                    invited_user_name=user.name,
                    property_name=property_obj.name,
                    role=invitation.role
                )
                
        except Exception as email_error:
            current_app.logger.error(f"Error sending acceptance notification: {email_error}")
            # Don't fail the acceptance if email fails
        
        return {
            'success': True,
            'team_member_id': str(team_member.id),
            'property_id': str(invitation.property_id),
            'role': invitation.role
        }
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error accepting invitation: {e}")
        return {'success': False, 'error': 'Failed to accept invitation'}

def remove_team_member(remover_user_id, property_id, member_user_id):
    """
    Remove a team member from a property
    """
    try:
        # Convert property_id to UUID if it's a string
        if isinstance(property_id, str):
            import uuid as uuid_module
            property_id = uuid_module.UUID(property_id)
        
        # Check if remover has permission
        if not check_user_property_permission(remover_user_id, property_id, 'remove_team_members'):
            return {'success': False, 'error': 'You do not have permission to remove team members'}
        
        # Find the team member
        team_member = PropertyTeamMember.query.filter_by(
            property_id=property_id,
            user_id=member_user_id,
            is_active=True
        ).first()
        
        if not team_member:
            return {'success': False, 'error': 'Team member not found'}
        
        # Deactivate membership
        team_member.is_active = False
        db.session.commit()
        
        return {'success': True}
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing team member: {e}")
        return {'success': False, 'error': 'Failed to remove team member'}

def get_property_team_members(property_id, user_id):
    """
    Get all team members for a property (if user has access)
    """
    try:
        # Convert property_id to UUID if it's a string
        if isinstance(property_id, str):
            import uuid as uuid_module
            property_id = uuid_module.UUID(property_id)
        
        # Check if user has access to this property
        user_properties = get_user_properties(user_id)
        property_ids = [p['property'].id for p in user_properties]
        
        if property_id not in property_ids:
            return {'success': False, 'error': 'Access denied'}
        
        # Get team members
        team_members = PropertyTeamMember.query.filter_by(
            property_id=property_id,
            is_active=True
        ).all()
        
        return {
            'success': True,
            'team_members': [member.to_dict() for member in team_members]
        }
        
    except Exception as e:
        current_app.logger.error(f"Error getting team members: {e}")
        return {'success': False, 'error': 'Failed to get team members'} 