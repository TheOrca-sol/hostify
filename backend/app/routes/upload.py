"""
File upload routes for Hostify Property Management Platform
"""

from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename
from ..utils.database import get_user_by_firebase_uid
from ..utils.auth import require_auth
import os

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/upload', methods=['POST'])
@require_auth
def upload_file():
    """Upload a file"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(os.getcwd(), 'uploads', user['id'])
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'file_path': file_path
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to upload file: {str(e)}'
        }), 500 