"""
File upload routes for Hostify Property Management Platform
"""

from flask import Blueprint, request, jsonify, g, send_from_directory
from werkzeug.utils import secure_filename
from ..utils.database import get_user_by_firebase_uid, db, Guest, Reservation, Property
from ..utils.auth import require_auth
import os
import uuid

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/uploads/<path:filename>')
@require_auth
def serve_upload(filename):
    """
    Serve an uploaded file securely, checking for user authorization.
    """
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # The guest's ID should be part of the file's path or name.
        # Here, we assume the file path stored in the DB is relative and includes the guest ID.
        # Let's find the guest by the document path.
        
        # This is not perfectly secure if paths are predictable, but works for this structure.
        # A better approach would be to query the guest by ID and then check the path.
        # We assume the filename format is <guest_id>_original_filename.ext
        
        guest_id_str = filename.split('_')[0]
        guest_id = uuid.UUID(guest_id_str)

        guest = (db.session.query(Guest)
                 .join(Reservation)
                 .join(Property)
                 .filter(Guest.id == guest_id, Property.user_id == user['id'])
                 .first())

        if not guest:
            return "Access denied or file not found", 403

        # The actual filename is after the first underscore
        actual_filename = filename.split('_', 1)[1]
        directory = os.path.abspath(os.path.join(os.getcwd(), 'uploads', str(guest.id)))

        return send_from_directory(directory, actual_filename, as_attachment=False)

    except Exception as e:
        return str(e), 500

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