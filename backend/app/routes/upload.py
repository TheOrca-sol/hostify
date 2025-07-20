"""
File upload routes for Hostify Property Management Platform
"""

from flask import Blueprint, request, jsonify, g, send_from_directory, current_app
from werkzeug.utils import secure_filename
from ..utils.database import get_user_by_firebase_uid, db, Guest, Reservation, Property
from ..utils.auth import require_auth
import os
import uuid
import jwt

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/uploads/<path:filename>')
def serve_upload(filename):
    """
    Serve an uploaded file securely, using a temporary token for authorization.
    """
    token = request.args.get('token')
    if not token:
        return "Authentication token required.", 401

    try:
        secret_key = current_app.config.get('SECRET_KEY', 'your-default-secret-key')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        firebase_uid = payload['sub']
        
        user = get_user_by_firebase_uid(firebase_uid)
        if not user:
            return "Invalid user.", 403

        guest_id_str = filename.split('_')[0]
        guest_id = uuid.UUID(guest_id_str)

        guest = (db.session.query(Guest)
                 .join(Reservation)
                 .join(Property)
                 .filter(Guest.id == guest_id, Property.user_id == user['id'])
                 .first())

        if not guest:
            return "Access denied or file not found.", 403

        # Use the stored path directly for robustness
        full_path = guest.id_document_path
        if not full_path or not os.path.isfile(full_path):
            return "File not found on server.", 404
            
        directory = os.path.dirname(full_path)
        actual_filename = os.path.basename(full_path)

        return send_from_directory(directory, actual_filename, as_attachment=False)

    except jwt.ExpiredSignatureError:
        return "Token has expired.", 401
    except jwt.InvalidTokenError:
        return "Invalid token.", 401
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