"""
Dashboard routes for Hostify
"""

from flask import Blueprint, jsonify, g, request
from flask_cors import cross_origin
from ..utils.auth import require_auth
from ..utils.database import get_user_by_firebase_uid
from ..models import db, Property, Reservation, Guest, SyncLog, ScheduledMessage, Contract, TeamMember, Team
from sqlalchemy import desc, func
from datetime import datetime, timezone, timedelta
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def get_dashboard_stats_route():
    """Get dashboard statistics for the authenticated user"""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get user's properties
        properties = Property.query.filter_by(user_id=user.id, is_active=True).all()
        property_ids = [p.id for p in properties]

        # Get user's teams (as owner or member)
        owned_teams = Team.query.filter_by(organization_id=user.id, is_active=True).all()
        member_teams = TeamMember.query.filter_by(user_id=user.id, is_active=True).all()
        
        # Get properties from teams the user is a member of
        team_property_ids = []
        for member_team in member_teams:
            team_properties = Property.query.filter_by(team_id=member_team.team_id, is_active=True).all()
            team_property_ids.extend([p.id for p in team_properties])

        # Combine all property IDs the user has access to
        all_property_ids = property_ids + team_property_ids

        # Calculate statistics
        total_properties = len(set(all_property_ids))
        
        # Get reservations for all accessible properties
        total_reservations = Reservation.query.filter(
            Reservation.property_id.in_(all_property_ids)
        ).count()
        
        # Get upcoming reservations (next 30 days)
        upcoming_reservations = Reservation.query.filter(
            Reservation.property_id.in_(all_property_ids),
            Reservation.check_in >= datetime.now(timezone.utc),
            Reservation.check_in <= datetime.now(timezone.utc) + timedelta(days=30)
        ).count()
        
        # Get active guests (currently staying)
        now = datetime.now(timezone.utc)
        active_guests = Reservation.query.filter(
            Reservation.property_id.in_(all_property_ids),
            Reservation.check_in <= now,
            Reservation.check_out >= now
        ).count()

        # Calculate occupancy rate for the current month
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month_end = (current_month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        # Get all reservations in current month
        month_reservations = Reservation.query.filter(
            Reservation.property_id.in_(all_property_ids),
            Reservation.check_in <= current_month_end,
            Reservation.check_out >= current_month_start
        ).all()
        
        # Calculate occupancy days
        total_occupancy_days = 0
        total_available_days = 0
        
        for property in properties:
            property_days = (current_month_end - current_month_start).days + 1
            total_available_days += property_days
            
            # Calculate occupied days for this property
            for reservation in month_reservations:
                if reservation.property_id == property.id:
                    overlap_start = max(reservation.check_in, current_month_start)
                    overlap_end = min(reservation.check_out, current_month_end)
                    if overlap_end > overlap_start:
                        total_occupancy_days += (overlap_end - overlap_start).days
        
        occupancy_rate = (total_occupancy_days / total_available_days * 100) if total_available_days > 0 else 0

        stats = {
            'totalProperties': total_properties,
            'totalReservations': total_reservations,
            'upcomingReservations': upcoming_reservations,
            'activeGuests': active_guests,
            'occupancy': {
                'rate': round(occupancy_rate, 1),
                'period': 'month',
                'occupiedDays': total_occupancy_days,
                'totalDays': total_available_days
            }
        }

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get dashboard stats: {str(e)}'
        }), 500

@dashboard_bp.route('/recent-activity', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def get_recent_activity_route():
    """Get recent activity from multiple sources"""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get user's properties and team properties
        properties = Property.query.filter_by(user_id=user.id, is_active=True).all()
        property_ids = [p.id for p in properties]
        
        # Get team properties
        member_teams = TeamMember.query.filter_by(user_id=user.id, is_active=True).all()
        team_property_ids = []
        for member_team in member_teams:
            team_properties = Property.query.filter_by(team_id=member_team.team_id, is_active=True).all()
            team_property_ids.extend([p.id for p in team_properties])

        all_property_ids = property_ids + team_property_ids
        all_team_ids = [member_team.team_id for member_team in member_teams]
        owned_team_ids = [team.id for team in Team.query.filter_by(organization_id=user.id, is_active=True).all()]

        activities = []
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(days=7)  # Last 7 days

        # 1. Recent Reservations
        recent_reservations = Reservation.query.filter(
            Reservation.property_id.in_(all_property_ids),
            Reservation.created_at >= cutoff_time
        ).order_by(desc(Reservation.created_at)).limit(10).all()

        for reservation in recent_reservations:
            activities.append({
                'id': f'reservation_{reservation.id}',
                'type': 'reservation',
                'title': f'New reservation: {reservation.guest_name_partial or "Guest"}',
                'description': f'Check-in: {reservation.check_in.strftime("%b %d")}',
                'timestamp': reservation.created_at,
                'property_name': reservation.property.name if reservation.property else 'Unknown Property',
                'icon': 'calendar',
                'color': 'blue'
            })

        # 2. Recent Calendar Syncs
        recent_syncs = SyncLog.query.filter(
            SyncLog.property_id.in_(all_property_ids),
            SyncLog.started_at >= cutoff_time,
            SyncLog.status == 'success'
        ).order_by(desc(SyncLog.started_at)).limit(5).all()

        for sync in recent_syncs:
            activities.append({
                'id': f'sync_{sync.id}',
                'type': 'sync',
                'title': f'Calendar synced: {sync.property.name if sync.property else "Unknown Property"}',
                'description': f'{sync.events_processed} events processed',
                'timestamp': sync.started_at,
                'property_name': sync.property.name if sync.property else 'Unknown Property',
                'icon': 'refresh-cw',
                'color': 'green'
            })

        # 3. Recent Communications (Scheduled Messages)
        recent_messages = ScheduledMessage.query.filter(
            ScheduledMessage.status == 'sent',
            ScheduledMessage.sent_at >= cutoff_time
        ).join(Reservation).filter(
            Reservation.property_id.in_(all_property_ids)
        ).order_by(desc(ScheduledMessage.sent_at)).limit(5).all()

        for message in recent_messages:
            activities.append({
                'id': f'message_{message.id}',
                'type': 'communication',
                'title': f'Message sent: {message.template.name if message.template else "Custom message"}',
                'description': f'To: {message.guest.full_name if message.guest else "Guest"}',
                'timestamp': message.sent_at,
                'property_name': message.reservation.property.name if message.reservation and message.reservation.property else 'Unknown Property',
                'icon': 'mail',
                'color': 'purple'
            })

        # 4. Recent Contracts
        recent_contracts = Contract.query.filter(
            Contract.created_at >= cutoff_time
        ).join(Reservation).filter(
            Reservation.property_id.in_(all_property_ids)
        ).order_by(desc(Contract.created_at)).limit(5).all()

        for contract in recent_contracts:
            activities.append({
                'id': f'contract_{contract.id}',
                'type': 'contract',
                'title': f'Contract {contract.contract_status}: {contract.guest.full_name if contract.guest else "Guest"}',
                'description': f'Template: {contract.template.name if contract.template else "Custom"}',
                'timestamp': contract.created_at,
                'property_name': contract.reservation.property.name if contract.reservation and contract.reservation.property else 'Unknown Property',
                'icon': 'file-text',
                'color': 'orange'
            })

        # 5. Team Activities
        team_activities = []
        
        # Team member changes
        recent_team_members = TeamMember.query.filter(
            TeamMember.team_id.in_(all_team_ids + owned_team_ids),
            TeamMember.created_at >= cutoff_time
        ).order_by(desc(TeamMember.created_at)).limit(3).all()

        for member in recent_team_members:
            team_activities.append({
                'id': f'team_member_{member.id}',
                'type': 'team',
                'title': f'Team member added: {member.user.name if member.user else "Unknown"}',
                'description': f'Role: {member.role} in {member.team.name if member.team else "Unknown Team"}',
                'timestamp': member.created_at,
                'property_name': 'Team Management',
                'icon': 'user-plus',
                'color': 'indigo'
            })

        # Property assignments to teams
        recent_assignments = Property.query.filter(
            Property.team_id.in_(all_team_ids + owned_team_ids),
            Property.created_at >= cutoff_time
        ).order_by(desc(Property.created_at)).limit(3).all()

        for prop in recent_assignments:
            if prop.team_id:  # Only if recently assigned to a team
                team_activities.append({
                    'id': f'property_assignment_{prop.id}',
                    'type': 'team',
                    'title': f'Property assigned to team: {prop.name}',
                    'description': f'Team: {prop.team.name if prop.team else "Unknown"}',
                    'timestamp': prop.created_at,
                    'property_name': prop.name,
                    'icon': 'home',
                    'color': 'indigo'
                })

        activities.extend(team_activities)

        # 6. Guest Verifications
        recent_verifications = Guest.query.filter(
            Guest.verification_status == 'verified',
            Guest.verified_at >= cutoff_time
        ).join(Reservation).filter(
            Reservation.property_id.in_(all_property_ids)
        ).order_by(desc(Guest.verified_at)).limit(3).all()

        for guest in recent_verifications:
            activities.append({
                'id': f'verification_{guest.id}',
                'type': 'verification',
                'title': f'Guest verified: {guest.full_name}',
                'description': f'Document: {guest.document_type or "ID"}',
                'timestamp': guest.verified_at,
                'property_name': guest.reservation.property.name if guest.reservation and guest.reservation.property else 'Unknown Property',
                'icon': 'check-circle',
                'color': 'green'
            })

        # 7. Property Changes (new properties, updates)
        recent_property_changes = Property.query.filter(
            Property.user_id == user.id,
            Property.created_at >= cutoff_time
        ).order_by(desc(Property.created_at)).limit(3).all()

        for prop in recent_property_changes:
            activities.append({
                'id': f'property_created_{prop.id}',
                'type': 'property',
                'title': f'New property added: {prop.name}',
                'description': f'Address: {prop.address or "No address"}',
                'timestamp': prop.created_at,
                'property_name': prop.name,
                'icon': 'home',
                'color': 'blue'
            })

        # 8. Contract Status Changes
        recent_contract_status_changes = Contract.query.filter(
            Contract.created_at >= cutoff_time
        ).join(Reservation).filter(
            Reservation.property_id.in_(all_property_ids)
        ).order_by(desc(Contract.created_at)).limit(5).all()

        for contract in recent_contract_status_changes:
            if contract.contract_status == 'signed':
                activities.append({
                    'id': f'contract_signed_{contract.id}',
                    'type': 'contract_signed',
                    'title': f'Contract signed: {contract.guest.full_name if contract.guest else "Guest"}',
                    'description': f'Template: {contract.template.name if contract.template else "Custom"}',
                    'timestamp': contract.signed_at or contract.created_at,
                    'property_name': contract.reservation.property.name if contract.reservation and contract.reservation.property else 'Unknown Property',
                    'icon': 'check-circle',
                    'color': 'green'
                })

        # 9. Message Template Changes
        recent_template_changes = MessageTemplate.query.filter(
            MessageTemplate.user_id == user.id,
            MessageTemplate.created_at >= cutoff_time
        ).order_by(desc(MessageTemplate.created_at)).limit(2).all()

        for template in recent_template_changes:
            activities.append({
                'id': f'template_created_{template.id}',
                'type': 'template',
                'title': f'Message template created: {template.name}',
                'description': f'Type: {template.template_type}',
                'timestamp': template.created_at,
                'property_name': 'Message Templates',
                'icon': 'mail',
                'color': 'purple'
            })

        # Sort all activities by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Return top 20 most recent activities
        return jsonify({
            'success': True,
            'activities': activities[:20]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get recent activity: {str(e)}'
        }), 500

@dashboard_bp.route('/occupancy', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def get_occupancy_rates_route():
    """Get occupancy rates for different periods"""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        period = request.args.get('period', 'month')
        
        # Get user's properties
        properties = Property.query.filter_by(user_id=user.id, is_active=True).all()
        property_ids = [p.id for p in properties]

        now = datetime.now(timezone.utc)
        
        if period == 'week':
            start_date = now - timedelta(days=7)
            end_date = now
        elif period == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        elif period == 'quarter':
            quarter_start_month = ((now.month - 1) // 3) * 3 + 1
            start_date = now.replace(month=quarter_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = (start_date + timedelta(days=95)).replace(day=1) - timedelta(seconds=1)
        else:  # year
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)

        # Get reservations in the period
        reservations = Reservation.query.filter(
            Reservation.property_id.in_(property_ids),
            Reservation.check_in <= end_date,
            Reservation.check_out >= start_date
        ).all()

        # Calculate occupancy
        total_days = (end_date - start_date).days + 1
        total_available_days = total_days * len(properties)
        occupied_days = 0

        for reservation in reservations:
            overlap_start = max(reservation.check_in, start_date)
            overlap_end = min(reservation.check_out, end_date)
            if overlap_end > overlap_start:
                occupied_days += (overlap_end - overlap_start).days

        occupancy_rate = (occupied_days / total_available_days * 100) if total_available_days > 0 else 0

        return jsonify({
            'success': True,
            'occupancy': {
                'rate': round(occupancy_rate, 1),
                'period': period,
                'occupiedDays': occupied_days,
                'totalDays': total_available_days,
                'startDate': start_date.isoformat(),
                'endDate': end_date.isoformat()
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get occupancy data: {str(e)}'
        }), 500
