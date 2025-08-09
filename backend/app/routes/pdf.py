"""
PDF generation and management routes for Hostify Property Management Platform
"""

from flask import Blueprint, request, jsonify, g
from ..utils.database import get_user_by_firebase_uid
from ..utils.auth import require_auth
from ..utils.pdf_generator import generate_pdf
from ..models.guest import Guest

pdf_bp = Blueprint('pdf', __name__)

@pdf_bp.route('/generate-pdf', methods=['POST'])
@require_auth
def generate_pdf_endpoint():
    """Generate a PDF document"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get data
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Verify ownership
        guest = Guest.query.get(data['guest_id'])
        if not guest or str(guest.reservation.property.user_id) != user.id:
            return jsonify({'success': False, 'error': 'Guest not found or access denied'}), 403
            
        # Generate PDF
        pdf_path = generate_pdf(data)
        if not pdf_path:
            return jsonify({'success': False, 'error': 'Failed to generate PDF'}), 500
        
        return jsonify({
            'success': True,
            'message': 'PDF generated successfully',
            'pdf_path': pdf_path
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to generate PDF: {str(e)}'
        }), 500 