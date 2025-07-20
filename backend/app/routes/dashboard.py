"""
Dashboard-related routes for Hostify.
"""

from flask import Blueprint, jsonify, g
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
