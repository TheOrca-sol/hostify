"""
Enhanced multi-team management utilities
"""

import uuid
import secrets
from datetime import datetime, timezone, timedelta
from flask import current_app
from ..models import db, Property, Team, TeamMember, TeamInvitationNew, User, TeamPerformance

# Updated permissions for the new role structure
DEFAULT_PERMISSIONS = {
    'manager': {
        'manage_team': True,
        'manage_team_properties': True,
        'manage_guests': True,
        'manage_reservations': True,
        'manage_contracts': True,
        'schedule_cleaning': True,
        'schedule_maintenance': True,
        'invite_team_members': True,
        'view_team_financials': True,
        'view_team_performance': True,
        'remove_team_members': True,
        'assign_properties': True,
        'modify_team_settings': True
    },
    'cleaner': {
        'view_cleaning_tasks': True,
        'update_cleaning_status': True,
        'upload_photos': True,
        'request_supplies': True,
        'view_assigned_properties': True,
        'view_property_access': True,
        'submit_reports': True,
        'manage_anything': False,
        'view_financials': False
    },
    'maintenance': {
        'view_maintenance_tasks': True,
        'update_task_status': True,
        'upload_photos': True,
        'submit_invoices': True,
        'emergency_contact': True,
        'view_assigned_properties': True,
        'view_property_access': True,
        'request_materials': True,
        'manage_anything': False,
        'view_financials': False
    },
    'assistant': {
        'view_team_reservations': True,
        'view_guest_info': True,
        'view_team_tasks': True,
        'basic_communication': True,
        'update_guest_status': True,
        'view_assigned_properties': True,
        'manage_anything': False,
        'view_financials': False
    }
}

# Team color options for UI
TEAM_COLORS = [
    '#FF6B6B',  # Red
    '#4ECDC4',  # Teal
    '#45B7D1',  # Blue
    '#96CEB4',  # Green
    '#FFEAA7',  # Yellow
    '#DDA0DD',  # Plum
    '#98D8C8',  # Mint
    '#F7DC6F',  # Light Yellow
    '#BB8FCE',  # Light Purple
    '#85C1E9',  # Light Blue
]

def create_team(organization_id, name, description=None, color=None):
    """
    Create a new team for the organization
    """
    try:
        # Validate organization exists
        organization = User.query.get(organization_id)
        if not organization:
            return {'success': False, 'error': 'Organization not found'}
        
        # Check if team name already exists for this organization
        existing_team = Team.query.filter_by(
            organization_id=organization_id,
            name=name,
            is_active=True
        ).first()
        
        if existing_team:
            return {'success': False, 'error': f'Team "{name}" already exists'}
        
        # Assign a color if not provided
        if not color:
            # Get existing team colors and pick a new one
            existing_colors = [t.color for t in Team.query.filter_by(
                organization_id=organization_id,
                is_active=True
            ).all() if t.color]
            
            available_colors = [c for c in TEAM_COLORS if c not in existing_colors]
            color = available_colors[0] if available_colors else TEAM_COLORS[0]
        
        # Create the team
        team = Team(
            organization_id=organization_id,
            name=name,
            description=description,
            color=color,
            settings={}
        )
        
        db.session.add(team)
        db.session.commit()
        
        return {'success': True, 'team': team.to_dict()}
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating team: {e}")
        return {'success': False, 'error': 'Failed to create team'}

def get_organization_teams(organization_id, include_inactive=False):
    """
    Get all teams for an organization
    """
    try:
        query = Team.query.filter_by(organization_id=organization_id)
        
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        teams = query.order_by(Team.created_at.desc()).all()
        
        return {'success': True, 'teams': [team.to_dict() for team in teams]}
        
    except Exception as e:
        current_app.logger.error(f"Error getting organization teams: {e}")
        return {'success': False, 'error': 'Failed to get teams'}

def get_user_teams(user_id):
    """
    Get all teams where user is a member (not owner)
    """
    try:
        # Get teams where user is a member
        team_memberships = TeamMember.query.filter_by(
            user_id=user_id,
            is_active=True
        ).all()
        
        teams = []
        for membership in team_memberships:
            if membership.team and membership.team.is_active:
                team_data = membership.team.to_dict()
                team_data['user_role'] = membership.role
                team_data['user_permissions'] = membership.permissions
                teams.append(team_data)
        
        return {'success': True, 'teams': teams}
        
    except Exception as e:
        current_app.logger.error(f"Error getting user teams: {e}")
        return {'success': False, 'error': 'Failed to get user teams'}

def invite_team_member(inviter_user_id, team_id, invited_email=None, invited_phone=None, 
                      invitation_method='email', role='cleaner', custom_permissions=None):
    """
    Invite someone to join a team
    """
    try:
        # Validate team exists and inviter has permission
        team = Team.query.get(team_id)
        if not team:
            return {'success': False, 'error': 'Team not found'}
        
        # Check if inviter is organization owner or team manager
        if not check_team_permission(inviter_user_id, team_id, 'invite_team_members'):
            return {'success': False, 'error': 'You do not have permission to invite team members'}
        
        # Validate invitation method and contact info
        if invitation_method == 'email' and not invited_email:
            return {'success': False, 'error': 'Email is required for email invitations'}
        elif invitation_method == 'sms' and not invited_phone:
            return {'success': False, 'error': 'Phone is required for SMS invitations'}
        
        # Check if already invited or member
        existing_member = TeamMember.query.filter_by(
            team_id=team_id,
            user_id=User.query.filter_by(email=invited_email).first().id if invited_email else None,
            is_active=True
        ).first() if invited_email else None
        
        if existing_member:
            return {'success': False, 'error': 'User is already a team member'}
        
        # Generate invitation token
        invitation_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Get permissions for role
        permissions = custom_permissions or DEFAULT_PERMISSIONS.get(role, {})
        
        # Create invitation
        invitation = TeamInvitationNew(
            team_id=team_id,
            inviter_user_id=inviter_user_id,
            invited_email=invited_email,
            invited_phone=invited_phone,
            invitation_method=invitation_method,
            role=role,
            permissions=permissions,
            invitation_token=invitation_token,
            expires_at=expires_at
        )
        
        db.session.add(invitation)
        db.session.commit()
        
        # TODO: Send invitation email/SMS here
        
        return {
            'success': True,
            'invitation': invitation.to_dict(),
            'invitation_link': f"/invite/team/{invitation_token}"
        }
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error inviting team member: {e}")
        return {'success': False, 'error': 'Failed to send invitation'}

def assign_property_to_team(organization_id, property_id, team_id):
    """
    Assign a property to a team
    """
    try:
        # Validate property belongs to organization
        property_obj = Property.query.filter_by(
            id=property_id,
            user_id=organization_id,
            is_active=True
        ).first()
        
        if not property_obj:
            return {'success': False, 'error': 'Property not found'}
        
        # Validate team belongs to organization
        team = Team.query.filter_by(
            id=team_id,
            organization_id=organization_id,
            is_active=True
        ).first()
        
        if not team:
            return {'success': False, 'error': 'Team not found'}
        
        # Assign property to team
        property_obj.team_id = team_id
        db.session.commit()
        
        return {'success': True, 'message': f'Property "{property_obj.name}" assigned to team "{team.name}"'}
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error assigning property to team: {e}")
        return {'success': False, 'error': 'Failed to assign property to team'}

def get_team_properties(team_id, user_id):
    """
    Get all properties assigned to a team (if user has access)
    """
    try:
        # Check if user has access to team
        if not check_team_permission(user_id, team_id, 'view_assigned_properties'):
            return {'success': False, 'error': 'You do not have access to this team'}
        
        # Get team properties
        properties = Property.query.filter_by(
            team_id=team_id,
            is_active=True
        ).order_by(Property.name).all()
        
        return {'success': True, 'properties': [prop.to_dict() for prop in properties]}
        
    except Exception as e:
        current_app.logger.error(f"Error getting team properties: {e}")
        return {'success': False, 'error': 'Failed to get team properties'}

def check_team_permission(user_id, team_id, permission):
    """
    Check if user has a specific permission for a team
    """
    try:
        # Check if user is organization owner
        team = Team.query.get(team_id)
        if team and team.organization_id == user_id:
            return True
        
        # Check team membership permissions
        team_member = TeamMember.query.filter_by(
            team_id=team_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not team_member:
            return False
        
        # Check permissions
        user_permissions = team_member.permissions or DEFAULT_PERMISSIONS.get(team_member.role, {})
        return user_permissions.get(permission, False)
        
    except Exception as e:
        current_app.logger.error(f"Error checking team permission: {e}")
        return False

def get_team_performance_metrics(team_id, date_from=None, date_to=None):
    """
    Get performance metrics for a team
    """
    try:
        from datetime import date, timedelta
        
        # Default date range: last 30 days
        if not date_to:
            date_to = date.today()
        if not date_from:
            date_from = date_to - timedelta(days=30)
        
        # Get performance records
        performance_records = TeamPerformance.query.filter(
            TeamPerformance.team_id == team_id,
            TeamPerformance.date >= date_from,
            TeamPerformance.date <= date_to
        ).order_by(TeamPerformance.date.desc()).all()
        
        # Calculate aggregated metrics
        if not performance_records:
            # Return default metrics if no data
            return {
                'success': True,
                'metrics': {
                    'task_completion_rate': 0,
                    'average_response_time': 0,
                    'guest_satisfaction': 0,
                    'properties_managed': 0,
                    'total_bookings': 0,
                    'revenue': 0,
                    'efficiency_score': 0
                },
                'daily_records': []
            }
        
        # Aggregate metrics
        total_records = len(performance_records)
        metrics = {
            'task_completion_rate': sum(r.metrics.get('task_completion_rate', 0) for r in performance_records) / total_records,
            'average_response_time': sum(r.metrics.get('response_time', 0) for r in performance_records) / total_records,
            'guest_satisfaction': sum(r.metrics.get('guest_satisfaction', 0) for r in performance_records) / total_records,
            'properties_managed': max(r.metrics.get('properties_count', 0) for r in performance_records),
            'total_bookings': sum(r.metrics.get('bookings', 0) for r in performance_records),
            'revenue': sum(r.metrics.get('revenue', 0) for r in performance_records),
            'efficiency_score': sum(r.metrics.get('efficiency_score', 0) for r in performance_records) / total_records
        }
        
        return {
            'success': True,
            'metrics': metrics,
            'daily_records': [r.to_dict() for r in performance_records]
        }
        
    except Exception as e:
        current_app.logger.error(f"Error getting team performance: {e}")
        return {'success': False, 'error': 'Failed to get team performance'}

def get_organization_performance_comparison(organization_id):
    """
    Get performance comparison across all organization teams
    """
    try:
        teams = Team.query.filter_by(
            organization_id=organization_id,
            is_active=True
        ).all()
        
        team_performances = []
        
        for team in teams:
            performance = get_team_performance_metrics(team.id)
            if performance['success']:
                team_data = team.to_dict()
                team_data['performance'] = performance['metrics']
                team_performances.append(team_data)
        
        return {'success': True, 'teams': team_performances}
        
    except Exception as e:
        current_app.logger.error(f"Error getting organization performance comparison: {e}")
        return {'success': False, 'error': 'Failed to get performance comparison'}

def remove_team_member(remover_user_id, team_id, member_user_id):
    """
    Remove a team member from a team
    """
    try:
        # Check permission
        if not check_team_permission(remover_user_id, team_id, 'remove_team_members'):
            return {'success': False, 'error': 'You do not have permission to remove team members'}
        
        # Find team member
        team_member = TeamMember.query.filter_by(
            team_id=team_id,
            user_id=member_user_id,
            is_active=True
        ).first()
        
        if not team_member:
            return {'success': False, 'error': 'Team member not found'}
        
        # Remove member
        team_member.is_active = False
        db.session.commit()
        
        return {'success': True, 'message': 'Team member removed successfully'}
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing team member: {e}")
        return {'success': False, 'error': 'Failed to remove team member'}

def update_team(team_id, user_id, **updates):
    """
    Update team information
    """
    try:
        # Check permission
        if not check_team_permission(user_id, team_id, 'modify_team_settings'):
            return {'success': False, 'error': 'You do not have permission to modify team settings'}
        
        team = Team.query.get(team_id)
        if not team:
            return {'success': False, 'error': 'Team not found'}
        
        # Update allowed fields
        allowed_fields = ['name', 'description', 'color', 'settings']
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(team, field, value)
        
        team.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return {'success': True, 'team': team.to_dict()}
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating team: {e}")
        return {'success': False, 'error': 'Failed to update team'}
