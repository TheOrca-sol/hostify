"""
SMS Authentication routes for Hostify
Handles phone-based login for cleaners and maintenance workers
"""

from flask import Blueprint, request, jsonify, current_app
from ..utils.sms_auth import SMSAuthService
from ..utils.team_management import invite_team_member
from ..models import TeamInvitation, db
from datetime import datetime, timezone, timedelta
import uuid

sms_auth_bp = Blueprint('sms_auth', __name__)

@sms_auth_bp.route('/login/send-code', methods=['POST'])
def send_login_code():
    """Send SMS verification code for login"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        
        if not phone_number:
            return jsonify({
                'success': False,
                'error': 'Phone number is required'
            }), 400
        
        result = SMSAuthService.send_login_code(phone_number)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"Error in send_login_code: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@sms_auth_bp.route('/login/verify-code', methods=['POST'])
def verify_login_code():
    """Verify SMS code and authenticate user"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        code = data.get('code')
        
        if not phone_number or not code:
            return jsonify({
                'success': False,
                'error': 'Phone number and verification code are required'
            }), 400
        
        result = SMSAuthService.verify_login_code(phone_number, code)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"Error in verify_login_code: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@sms_auth_bp.route('/invitation/send-code', methods=['POST'])
def send_invitation_code():
    """Send SMS verification code for invitation acceptance"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        invitation_token = data.get('invitation_token')
        
        if not phone_number or not invitation_token:
            return jsonify({
                'success': False,
                'error': 'Phone number and invitation token are required'
            }), 400
        
        result = SMSAuthService.send_invitation_code(phone_number, invitation_token)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"Error in send_invitation_code: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@sms_auth_bp.route('/invitation/verify-code', methods=['POST'])
def verify_invitation_code():
    """Verify SMS code and accept invitation"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        code = data.get('code')
        invitation_token = data.get('invitation_token')
        user_name = data.get('user_name', 'Worker')  # Default name if not provided
        
        if not phone_number or not code or not invitation_token:
            return jsonify({
                'success': False,
                'error': 'Phone number, verification code, and invitation token are required'
            }), 400
        
        result = SMSAuthService.verify_invitation_code(phone_number, code, invitation_token, user_name)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"Error in verify_invitation_code: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@sms_auth_bp.route('/invitation/<invitation_token>/details', methods=['GET'])
def get_invitation_details(invitation_token):
    """Get invitation details for SMS invitation"""
    try:
        invitation = TeamInvitation.query.filter_by(
            invitation_token=invitation_token,
            invitation_method='sms',
            status='pending'
        ).first()
        
        if not invitation:
            return jsonify({
                'success': False,
                'error': 'Invitation not found or expired'
            }), 404
        
        if invitation.expires_at < datetime.now(timezone.utc):
            return jsonify({
                'success': False,
                'error': 'Invitation has expired'
            }), 410
        
        return jsonify({
            'success': True,
            'invitation': {
                'property_name': invitation.property.name if invitation.property else 'Unknown Property',
                'role': invitation.role,
                'inviter_name': invitation.inviter.name if invitation.inviter else 'Property Manager',
                'invited_phone': invitation.invited_phone,
                'expires_at': invitation.expires_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_invitation_details: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500 