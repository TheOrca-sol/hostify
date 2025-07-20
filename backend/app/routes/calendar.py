"""
Calendar management routes for property iCal sync
Updated for property-centric architecture with reservations
"""

from flask import Blueprint, request, jsonify, g
from app.models import db, Property, SyncLog, User
from app.utils.auth import require_auth
from app.utils.calendar_sync import sync_property_calendar, validate_ical_url
from app.utils.database import get_property_by_ical_url
from datetime import datetime
from flask_cors import cross_origin

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route('/calendar/test-ical/<path:ical_url>', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def test_ical_url(ical_url):
    """Test if an iCal URL is valid, accessible, and not already in use"""
    try:
        # First, check if the iCal URL is already used by another property
        existing_property = get_property_by_ical_url(ical_url)
        if existing_property:
            return jsonify({
                'success': False,
                'error': 'This iCal link is already in use by another property.'
            }), 409  # 409 Conflict

        # If not a duplicate, validate the iCal URL itself
        is_valid = validate_ical_url(ical_url)
        if is_valid:
            return jsonify({
                'success': True,
                'message': 'Valid iCal URL'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid iCal URL or calendar format'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error validating iCal URL: {str(e)}'
        }), 400

@calendar_bp.route('/calendar/sync/<property_id>', methods=['POST', 'OPTIONS'])
@cross_origin()
@require_auth
def sync_calendar(property_id):
    """Manually trigger calendar sync for a property"""
    if not property_id:
        return jsonify({'success': False, 'error': 'Property ID is required'}), 400
        
    # Get the user's ID from their Firebase UID
    user = User.query.filter_by(firebase_uid=g.user_id).first()
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
        
    property = Property.query.get_or_404(property_id)
    
    # Check if property belongs to current user
    if property.user_id != user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Sync calendar
        sync_success = sync_property_calendar(property)
        
        # Log sync attempt
        log = SyncLog(
            property_id=property_id,
            sync_type='manual',
            status='success' if sync_success else 'failed',
            events_processed=0,  # This will be updated by sync_property_calendar
            errors=None if sync_success else {'message': 'Manual sync failed'}
        )
        db.session.add(log)
        db.session.commit()
        
        if sync_success:
            return jsonify({
                'success': True,
                'message': 'Calendar synced successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to sync calendar'
            }), 500
            
    except Exception as e:
        # Log error
        log = SyncLog(
            property_id=property_id,
            sync_type='manual',
            status='failed',
            events_processed=0,
            errors={'message': str(e)}
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': False,
            'error': f'Sync error: {str(e)}'
        }), 500

@calendar_bp.route('/calendar/sync/status/<property_id>', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def get_sync_status(property_id):
    """Get sync status for a property"""
    if not property_id:
        return jsonify({'success': False, 'error': 'Property ID is required'}), 400
        
    property = Property.query.get_or_404(property_id)
    
    # Check if property belongs to current user
    if str(property.user_id) != g.user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    # Get latest sync log
    latest_log = SyncLog.query.filter_by(property_id=property_id)\
        .order_by(SyncLog.created_at.desc())\
        .first()
    
    if not latest_log:
        return jsonify({
            'success': True,
            'last_sync': None,
            'status': 'never',
            'error': None
        })
    
    return jsonify({
        'success': True,
        'last_sync': latest_log.created_at.isoformat(),
        'status': 'success' if latest_log.success else 'failed',
        'error': latest_log.error_message
    })

@calendar_bp.route('/calendar/sync-all', methods=['POST', 'OPTIONS'])
@cross_origin()
@require_auth
def sync_all_calendars():
    """Sync calendars for all properties owned by the user"""
    # Get all properties for the current user
    properties = Property.query.filter_by(user_id=g.user_id).all()
    
    results = []
    for property in properties:
        try:
            success = sync_property_calendar(property)
            
            # Log sync attempt
            log = SyncLog(
                property_id=property.id,
                success=success,
                error_message=None if success else "Bulk sync failed"
            )
            db.session.add(log)
            
            results.append({
                'property_id': property.id,
                'success': success
            })
            
        except Exception as e:
            # Log error
            log = SyncLog(
                property_id=property.id,
                success=False,
                error_message=str(e)
            )
            db.session.add(log)
            
            results.append({
                'property_id': property.id,
                'success': False,
                'error': str(e)
            })
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Calendar sync completed',
        'results': results
    })