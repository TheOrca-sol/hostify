"""
Dashboard-related routes for Hostify.
"""

from flask import Blueprint, jsonify, g, request, current_app
from ..utils.auth import require_auth
from ..utils.database import get_user_by_firebase_uid, get_user_dashboard_stats

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
@require_auth
def get_dashboard_stats():
    """
    Get dashboard statistics for the authenticated user.
    """
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        stats = get_user_dashboard_stats(user['id'])
        if stats is None:
            return jsonify({'success': False, 'error': 'Failed to retrieve dashboard stats'}), 500

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        }), 500

@dashboard_bp.route('/occupancy', methods=['GET'])
@require_auth
def get_occupancy_data():
    """
    Get occupancy data for a specific period
    """
    try:
        # Get the current user using the same pattern as stats endpoint
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get period parameter (default to month)
        period = request.args.get('period', 'month')
        
        # Validate period
        valid_periods = ['week', 'month', 'quarter', 'year']
        if period not in valid_periods:
            return jsonify({'success': False, 'error': f'Invalid period. Must be one of: {valid_periods}'}), 400

        # Calculate occupancy for the specified period
        from ..utils.database import calculate_occupancy_rates
        from datetime import datetime, timezone
        
        occupancy_data = calculate_occupancy_rates(user['id'], datetime.now(timezone.utc), period)
        
        return jsonify({
            'success': True,
            'occupancy': occupancy_data
        })

    except Exception as e:
        current_app.logger.error(f"Error getting occupancy data: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
