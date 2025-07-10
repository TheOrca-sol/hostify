from flask import Blueprint, request, jsonify, send_file
from ..utils.pdf_generator import generate_police_form
from ..utils.auth import verify_firebase_token
import tempfile
import os

pdf_bp = Blueprint('pdf', __name__)

@pdf_bp.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    """
    Generate PDF police form from guest data
    """
    try:
        # Verify Firebase token (optional for now)
        auth_header = request.headers.get('Authorization')
        if auth_header:
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            user_id = verify_firebase_token(token)
            if not user_id:
                return jsonify({'success': False, 'error': 'Invalid authentication token'}), 401
        
        # Get guest data from request
        guest_data = request.get_json()
        
        if not guest_data:
            return jsonify({'success': False, 'error': 'No guest data provided'}), 400
        
        # Validate required fields
        required_fields = ['full_name', 'cin_or_passport', 'birthdate', 'nationality']
        for field in required_fields:
            if not guest_data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Generate PDF
        pdf_path = generate_police_form(guest_data)
        
        # Return PDF file
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"Fiche-Police-{guest_data['full_name'].replace(' ', '-')}.pdf"
        )
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'PDF generation failed: {str(e)}'
        }), 500 