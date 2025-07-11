"""
PDF generation and management routes for Hostify Property Management Platform
"""

from flask import Blueprint, request, jsonify, g
from ..utils.database import get_user_by_firebase_uid
from ..utils.auth import require_auth
from ..utils.pdf_generator import generate_pdf

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
        
        # Get PDF data
        pdf_data = request.get_json()
        if not pdf_data:
            return jsonify({'success': False, 'error': 'No PDF data provided'}), 400
        
        # Generate PDF
        pdf_path = generate_pdf(pdf_data)
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