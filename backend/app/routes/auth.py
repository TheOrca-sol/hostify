from flask import Blueprint, jsonify, g
from ..utils.auth import require_auth
import jwt
import datetime
from flask import current_app

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/generate-file-token', methods=['POST'])
@require_auth
def generate_file_token():
    """
    Generate a short-lived JWT for temporary file access.
    """
    try:
        # We can add more specific permissions here if needed in the future
        payload = {
            'sub': g.user_id, # The user's Firebase UID
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=60) # Token expires in 60 seconds
        }
        
        # In a real app, you'd use a strong, configured secret key
        secret_key = current_app.config.get('SECRET_KEY', 'your-default-secret-key')
        
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        return jsonify({'success': True, 'token': token})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
