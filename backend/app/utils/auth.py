import os
import json
from functools import wraps
from flask import request, jsonify, current_app
import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase Admin SDK
cred_path = os.path.join(os.path.dirname(__file__), '..', 'hostify-797ff-firebase-adminsdk-fbsvc-8e07c589eb.json')
if not firebase_admin._apps:
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        raise RuntimeError("Firebase credentials file not found")

def verify_firebase_token(token):
    """Legacy function for backward compatibility"""
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token['uid']
    except Exception as e:
        current_app.logger.error(f"Token verification error: {str(e)}")
        return None

def require_auth(f):
    """Decorator to require Firebase authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip authentication for OPTIONS requests
        if request.method == 'OPTIONS':
            response = jsonify({'status': 'ok'})
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept')
            response.headers.add('Access-Control-Max-Age', '86400')  # Cache preflight requests for 24 hours
            return response, 200
            
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'No token provided'}), 401

        token = auth_header.split('Bearer ')[1]
        try:
            # Verify the Firebase ID token
            decoded_token = auth.verify_id_token(token)
            
            # Add user info to request
            request.user = {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'name': decoded_token.get('name')
            }
            
            # Call the protected function
            return f(*args, **kwargs)
            
        except auth.ExpiredIdTokenError:
            return jsonify({'success': False, 'error': 'Token has expired'}), 401
        except auth.RevokedIdTokenError:
            return jsonify({'success': False, 'error': 'Token has been revoked'}), 401
        except auth.InvalidIdTokenError:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        except Exception as e:
            current_app.logger.error(f"Auth error: {str(e)}")
            return jsonify({'success': False, 'error': 'Authentication failed'}), 401

    return decorated_function

def get_current_user():
    """Get current authenticated user info"""
    if hasattr(request, 'user'):
        return request.user
    return None

def initialize_firebase():
    """Legacy function for backward compatibility"""
    return True if firebase_admin._apps else False

def get_user_info(user_id):
    """Legacy function for backward compatibility"""
    try:
        user = auth.get_user(user_id)
        return {
            'uid': user.uid,
            'email': user.email,
            'display_name': user.display_name,
            'email_verified': user.email_verified
        }
    except Exception as e:
        current_app.logger.error(f"Get user info error: {str(e)}")
        return None 