import os
import json
from functools import wraps
from flask import request, jsonify, current_app, g
import firebase_admin
from firebase_admin import credentials, auth
import logging
from flask import g
from functools import wraps
from firebase_admin import auth
from ..models import User, db
from .messaging import create_default_verification_templates
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Debug: Print environment variables
logger.debug("FIREBASE_ADMIN_SDK_JSON: %s", bool(os.getenv('FIREBASE_ADMIN_SDK_JSON')))
logger.debug("FIREBASE_SERVICE_ACCOUNT_PATH: %s", os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH'))

# Initialize Firebase Admin SDK
try:
    # Try individual Firebase config variables first (more reliable for Railway)
    firebase_project_id = os.getenv('FIREBASE_PROJECT_ID')
    firebase_private_key = os.getenv('FIREBASE_PRIVATE_KEY')
    firebase_client_email = os.getenv('FIREBASE_CLIENT_EMAIL')
    
    if firebase_project_id and firebase_private_key and firebase_client_email:
        logger.debug("Using individual Firebase environment variables")
        cred_dict = {
            "type": "service_account",
            "project_id": firebase_project_id,
            "private_key": firebase_private_key.replace('\\n', '\n'),
            "client_email": firebase_client_email,
            "client_id": "",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
        }
        cred = credentials.Certificate(cred_dict)
    # Fallback to JSON from environment variable
    elif os.getenv('FIREBASE_ADMIN_SDK_JSON'):
        cred_json = os.getenv('FIREBASE_ADMIN_SDK_JSON')
        logger.debug("Using FIREBASE_ADMIN_SDK_JSON")
        # Clean and validate the JSON string
        try:
            # First try direct parsing
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
        except json.JSONDecodeError:
            # If that fails, try handling escaped characters
            cred_json_cleaned = cred_json.replace('\\n', '\n').replace('\\"', '"')
            try:
                cred_dict = json.loads(cred_json_cleaned)
                cred = credentials.Certificate(cred_dict)
            except json.JSONDecodeError as e:
                logger.error("Failed to parse Firebase JSON even after cleaning: %s", str(e))
                logger.error("JSON string length: %d, error at position: %d", len(cred_json), getattr(e, 'pos', -1))
                if hasattr(e, 'pos') and e.pos < len(cred_json):
                    logger.error("Character at error position: %r", cred_json[e.pos:e.pos+10])
                # Fall back to service account file
                logger.warning("Falling back to service account file due to JSON parsing error")
                service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
                if service_account_path and os.path.exists(service_account_path):
                    cred = credentials.Certificate(service_account_path)
                else:
                    raise
    else:
        logger.debug("Falling back to FIREBASE_SERVICE_ACCOUNT_PATH")
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
        if not service_account_path:
            raise ValueError("Neither FIREBASE_ADMIN_SDK_JSON nor FIREBASE_SERVICE_ACCOUNT_PATH are set")
        cred = credentials.Certificate(service_account_path)
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        logger.debug("Firebase initialized successfully")

except Exception as e:
    logger.error("Firebase initialization error: %s", str(e))
    raise

def verify_firebase_token(token):
    """Verify a Firebase ID token and return the decoded token"""
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token['uid']
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return None

def get_current_user_id():
    """Get the current user's Firebase UID"""
    return g.user_id if hasattr(g, 'user_id') else None

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
            
            # Store user info in Flask's g object
            g.user_id = decoded_token['uid']
            g.user = {
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
    return g.user if hasattr(g, 'user') else None

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

def get_or_create_user(firebase_user):
    """Get or create a user record from Firebase user data"""
    try:
        # Check if user exists
        user = User.query.filter_by(firebase_uid=firebase_user.uid).first()
        
        if user:
            return user.to_dict()
            
        # Create new user
        new_user = User(
            firebase_uid=firebase_user.uid,
            email=firebase_user.email,
            name=firebase_user.display_name or firebase_user.email.split('@')[0],
            phone=firebase_user.phone_number
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Create default message templates for the new user
        create_default_verification_templates(new_user.id)
        
        return new_user.to_dict()
        
    except Exception as e:
        print(f"Error in get_or_create_user: {str(e)}")
        db.session.rollback()
        return None