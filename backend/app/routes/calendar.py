"""
Calendar management routes for property iCal sync
Updated for property-centric architecture with reservations
"""

from flask import Blueprint, request, jsonify
from app.models import db, Property, SyncLog
from app.utils.auth import require_auth
from app.utils.calendar_sync import sync_property_calendar
from datetime import datetime

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route('/sync/<property_id>', methods=['POST'])
@require_auth
def sync_calendar(property_id):
    """Manually trigger calendar sync for a property"""
    if not property_id:
        return jsonify({'error': 'Property ID is required'}), 400
        
    property = Property.query.get_or_404(property_id)
    
    # Check if property belongs to current user
    if str(property.user_id) != request.user['uid']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Sync calendar
        success = sync_property_calendar(property)
        
        # Log sync attempt
        log = SyncLog(
            property_id=property_id,
            success=success,
            error_message=None if success else "Manual sync failed"
        )
        db.session.add(log)
        db.session.commit()
        
        if success:
            return jsonify({'message': 'Calendar synced successfully'})
        else:
            return jsonify({'error': 'Failed to sync calendar'}), 500
            
    except Exception as e:
        # Log error
        log = SyncLog(
            property_id=property_id,
            success=False,
            error_message=str(e)
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'error': f'Sync error: {str(e)}'}), 500

@calendar_bp.route('/sync/status/<property_id>', methods=['GET'])
@require_auth
def get_sync_status(property_id):
    """Get sync status for a property"""
    if not property_id:
        return jsonify({'error': 'Property ID is required'}), 400
        
    property = Property.query.get_or_404(property_id)
    
    # Check if property belongs to current user
    if str(property.user_id) != request.user['uid']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get latest sync log
    latest_log = SyncLog.query.filter_by(property_id=property_id)\
        .order_by(SyncLog.created_at.desc())\
        .first()
    
    if not latest_log:
        return jsonify({
            'last_sync': None,
            'status': 'never',
            'error': None
        })
    
    return jsonify({
        'last_sync': latest_log.created_at.isoformat(),
        'status': 'success' if latest_log.success else 'failed',
        'error': latest_log.error_message
    })

@calendar_bp.route('/sync-all', methods=['POST'])
@require_auth
def sync_all_calendars():
    """Sync calendars for all properties owned by the user"""
    # Get all properties for the current user
    properties = Property.query.filter_by(user_id=request.user['uid']).all()
    
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
        'message': 'Calendar sync completed',
        'results': results
    })