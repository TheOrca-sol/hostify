
from flask import Blueprint, jsonify
from app.models import db, Reservation
from app.utils.automation_triggers import trigger_post_reservation_actions
from app.utils.auth import require_auth
import logging

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/debug/backfill-automations', methods=['POST'])
@require_auth
def backfill_automations():
    """One-time script to backfill automations for existing reservations."""
    try:
        reservations = Reservation.query.all()
        logging.info(f"Found {len(reservations)} reservations to process.")
        
        for r in reservations:
            logging.info(f"Processing reservation {r.id}")
            trigger_post_reservation_actions(r)
            
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'{len(reservations)} reservations processed.'}), 200
    except Exception as e:
        logging.error(f"Backfill failed: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
