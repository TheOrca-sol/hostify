"""
Enhanced multi-team management routes
"""

from flask import Blueprint, request, jsonify, g
from ..utils.auth import require_auth
from ..utils.database import get_user_by_firebase_uid
from ..utils.team_management_new import (
    create_team, get_organization_teams, get_user_teams,
    invite_team_member, assign_property_to_team, get_team_properties,
    get_team_performance_metrics, get_organization_performance_comparison,
    remove_team_member, update_team, check_team_permission
)
from ..models import Team, TeamMember, Property
import logging

logger = logging.getLogger(__name__)
teams_bp = Blueprint('teams', __name__)

@teams_bp.route('/teams', methods=['POST'])
@require_auth
def create_team_route():
    """
    Create a new team for the organization
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get team data
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        name = data.get('name')
        description = data.get('description')
        color = data.get('color')

        if not name:
            return jsonify({'success': False, 'error': 'Team name is required'}), 400

        # Create team
        result = create_team(
            organization_id=user.id,
            name=name,
            description=description,
            color=color
        )

        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error creating team: {e}")
        return jsonify({'success': False, 'error': 'Failed to create team'}), 500

@teams_bp.route('/teams', methods=['GET'])
@require_auth
def get_teams_route():
    """
    Get all teams for the organization or user
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get teams where user is owner (organization teams)
        owned_teams_result = get_organization_teams(user.id)
        
        # Get teams where user is a member
        member_teams_result = get_user_teams(user.id)
        
        response_data = {
            'success': True,
            'owned_teams': owned_teams_result.get('teams', []) if owned_teams_result['success'] else [],
            'member_teams': member_teams_result.get('teams', []) if member_teams_result['success'] else []
        }
        
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error getting teams: {e}")
        return jsonify({'success': False, 'error': 'Failed to get teams'}), 500

@teams_bp.route('/teams/<team_id>', methods=['PUT'])
@require_auth
def update_team_route(team_id):
    """
    Update team information
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get update data
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # Update team
        result = update_team(team_id, user.id, **data)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error updating team: {e}")
        return jsonify({'success': False, 'error': 'Failed to update team'}), 500

@teams_bp.route('/teams/<team_id>/invite', methods=['POST'])
@require_auth
def invite_team_member_route(team_id):
    """
    Invite someone to join a team
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
        invitation_method = data.get('invitation_method', 'email')
        role = data.get('role')
        custom_permissions = data.get('permissions')

        # Validate role
        valid_roles = ['manager', 'cleaner', 'maintenance', 'assistant']
        if role not in valid_roles:
            return jsonify({'success': False, 'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'}), 400

        # Check that contact info is provided based on method
        if invitation_method == 'email' and not invited_email:
            return jsonify({'success': False, 'error': 'Email is required for email invitations'}), 400
        elif invitation_method == 'sms' and not invited_phone:
            return jsonify({'success': False, 'error': 'Phone number is required for SMS invitations'}), 400

        # Send invitation
        result = invite_team_member(
            inviter_user_id=user.id,
            team_id=team_id,
            invited_email=invited_email,
            invited_phone=invited_phone,
            invitation_method=invitation_method,
            role=role,
            custom_permissions=custom_permissions
        )

        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error inviting team member: {e}")
        return jsonify({'success': False, 'error': 'Failed to send invitation'}), 500

@teams_bp.route('/teams/<team_id>/properties', methods=['GET'])
@require_auth
def get_team_properties_route(team_id):
    """
    Get all properties assigned to a team
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get team properties
        result = get_team_properties(team_id, user.id)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 403

    except Exception as e:
        logger.error(f"Error getting team properties: {e}")
        return jsonify({'success': False, 'error': 'Failed to get team properties'}), 500

@teams_bp.route('/teams/<team_id>/properties/<property_id>', methods=['POST'])
@require_auth
def assign_property_route(team_id, property_id):
    """
    Assign a property to a team
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Assign property to team
        result = assign_property_to_team(user.id, property_id, team_id)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error assigning property to team: {e}")
        return jsonify({'success': False, 'error': 'Failed to assign property'}), 500

@teams_bp.route('/teams/<team_id>/members', methods=['GET'])
@require_auth
def get_team_members_route(team_id):
    """
    Get all members of a team
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Check permission
        if not check_team_permission(user.id, team_id, 'view_team_performance'):
            return jsonify({'success': False, 'error': 'You do not have access to this team'}), 403

        # Get team members
        team_members = TeamMember.query.filter_by(
            team_id=team_id,
            is_active=True
        ).all()

        return jsonify({
            'success': True,
            'members': [member.to_dict() for member in team_members]
        })

    except Exception as e:
        logger.error(f"Error getting team members: {e}")
        return jsonify({'success': False, 'error': 'Failed to get team members'}), 500

@teams_bp.route('/teams/<team_id>/members/<member_id>', methods=['DELETE'])
@require_auth
def remove_team_member_route(team_id, member_id):
    """
    Remove a team member
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Remove team member
        result = remove_team_member(user.id, team_id, member_id)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 403

    except Exception as e:
        logger.error(f"Error removing team member: {e}")
        return jsonify({'success': False, 'error': 'Failed to remove team member'}), 500

@teams_bp.route('/teams/<team_id>/performance', methods=['GET'])
@require_auth
def get_team_performance_route(team_id):
    """
    Get team performance metrics
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Check permission
        if not check_team_permission(user.id, team_id, 'view_team_performance'):
            return jsonify({'success': False, 'error': 'You do not have access to this team performance'}), 403

        # Get date range from query params
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        # Convert strings to dates if provided
        if date_from:
            from datetime import datetime
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        if date_to:
            from datetime import datetime
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()

        # Get performance metrics
        result = get_team_performance_metrics(team_id, date_from, date_to)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error getting team performance: {e}")
        return jsonify({'success': False, 'error': 'Failed to get team performance'}), 500

@teams_bp.route('/teams/performance/comparison', methods=['GET'])
@require_auth
def get_performance_comparison_route():
    """
    Get performance comparison across all organization teams
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get performance comparison
        result = get_organization_performance_comparison(user.id)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error getting performance comparison: {e}")
        return jsonify({'success': False, 'error': 'Failed to get performance comparison'}), 500

@teams_bp.route('/teams/<team_id>', methods=['DELETE'])
@require_auth
def delete_team_route(team_id):
    """
    Delete (deactivate) a team
    """
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Check if user owns the team
        team = Team.query.filter_by(
            id=team_id,
            organization_id=user.id,
            is_active=True
        ).first()

        if not team:
            return jsonify({'success': False, 'error': 'Team not found or you do not have permission'}), 404

        # Deactivate team (soft delete)
        team.is_active = False
        
        # Also deactivate all team members
        team_members = TeamMember.query.filter_by(team_id=team_id, is_active=True).all()
        for member in team_members:
            member.is_active = False
        
        # Unassign properties from team
        properties = Property.query.filter_by(team_id=team_id).all()
        for prop in properties:
            prop.team_id = None

        from ..models import db
        db.session.commit()

        return jsonify({'success': True, 'message': 'Team deleted successfully'})

    except Exception as e:
        from ..models import db
        db.session.rollback()
        logger.error(f"Error deleting team: {e}")
        return jsonify({'success': False, 'error': 'Failed to delete team'}), 500
