"""
SMS Authentication Service for Hostify
Handles phone verification codes for cleaner/maintenance worker login
"""

import os
import random
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from ..models import db, User, PhoneVerification, TeamInvitation
from .sms import send_sms

class SMSAuthService:
    """Service for SMS-based authentication"""
    
    @staticmethod
    def normalize_phone_number(phone: str) -> str:
        """
        Normalize phone number to E.164 format
        Assumes +212 (Morocco) if no country code provided
        """
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # If starts with 0, assume Moroccan number
        if digits_only.startswith('0'):
            digits_only = '212' + digits_only[1:]
        
        # If no country code, assume Morocco
        if len(digits_only) == 9:
            digits_only = '212' + digits_only
        
        # Add + prefix for E.164 format
        return '+' + digits_only
    
    @staticmethod
    def generate_verification_code() -> str:
        """Generate a 6-digit verification code"""
        return str(random.randint(100000, 999999))
    
    @staticmethod
    def send_login_code(phone_number: str) -> Dict[str, Any]:
        """
        Send SMS verification code for login
        Returns: {'success': bool, 'verification_id': str, 'error': str}
        """
        try:
            # Normalize phone number
            normalized_phone = SMSAuthService.normalize_phone_number(phone_number)
            
            # Check if user exists with this phone number
            user = User.query.filter_by(phone=normalized_phone).first()
            if not user:
                return {
                    'success': False,
                    'error': 'No account found with this phone number. Please contact your property manager.'
                }
            
            # Generate verification code
            code = SMSAuthService.generate_verification_code()
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)  # 10-minute expiry
            
            # Clean up old verification codes for this phone
            PhoneVerification.query.filter_by(
                phone_number=normalized_phone,
                purpose='login'
            ).delete()
            
            # Create new verification record
            verification = PhoneVerification(
                phone_number=normalized_phone,
                verification_code=code,
                purpose='login',
                user_id=user.id,
                expires_at=expires_at
            )
            
            db.session.add(verification)
            db.session.commit()
            
            # Send SMS
            message = f"Your Hostify login code is: {code}\nValid for 10 minutes."
            sms_result = send_sms(normalized_phone, message)
            
            if not sms_result['success']:
                db.session.rollback()
                return {
                    'success': False,
                    'error': f"Failed to send SMS: {sms_result.get('error', 'Unknown error')}"
                }
            
            return {
                'success': True,
                'verification_id': str(verification.id),
                'message': f'Verification code sent to {normalized_phone}'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Error sending verification code: {str(e)}'
            }
    
    @staticmethod
    def verify_login_code(phone_number: str, code: str) -> Dict[str, Any]:
        """
        Verify SMS code and return user data for login
        Returns: {'success': bool, 'user': dict, 'error': str}
        """
        try:
            # Normalize phone number
            normalized_phone = SMSAuthService.normalize_phone_number(phone_number)
            
            # Find verification record
            verification = PhoneVerification.query.filter_by(
                phone_number=normalized_phone,
                purpose='login',
                is_verified=False
            ).order_by(PhoneVerification.created_at.desc()).first()
            
            if not verification:
                return {
                    'success': False,
                    'error': 'No verification code found. Please request a new code.'
                }
            
            # Check if expired
            if verification.is_expired():
                return {
                    'success': False,
                    'error': 'Verification code has expired. Please request a new code.'
                }
            
            # Check attempts limit
            if not verification.can_attempt():
                return {
                    'success': False,
                    'error': 'Too many failed attempts. Please request a new code.'
                }
            
            # Verify code
            if verification.verification_code != code:
                verification.attempts += 1
                db.session.commit()
                remaining_attempts = 3 - verification.attempts
                return {
                    'success': False,
                    'error': f'Invalid code. {remaining_attempts} attempts remaining.'
                }
            
            # Code is correct - mark as verified
            verification.is_verified = True
            verification.verified_at = datetime.now(timezone.utc)
            db.session.commit()
            
            # Get user data
            user = User.query.get(verification.user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'User account not found.'
                }
            
            return {
                'success': True,
                'user': user.to_dict(),
                'message': 'Login successful'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Error verifying code: {str(e)}'
            }
    
    @staticmethod
    def send_invitation_code(phone_number: str, invitation_token: str) -> Dict[str, Any]:
        """
        Send SMS verification code for team invitation acceptance
        Returns: {'success': bool, 'verification_id': str, 'error': str}
        """
        try:
            # Normalize phone number
            normalized_phone = SMSAuthService.normalize_phone_number(phone_number)
            
            # Verify invitation exists and is valid
            invitation = TeamInvitation.query.filter_by(
                invitation_token=invitation_token,
                invited_phone=normalized_phone,
                status='pending'
            ).first()
            
            if not invitation:
                return {
                    'success': False,
                    'error': 'Invalid invitation or phone number.'
                }
            
            if invitation.expires_at < datetime.now(timezone.utc):
                return {
                    'success': False,
                    'error': 'Invitation has expired.'
                }
            
            # Generate verification code
            code = SMSAuthService.generate_verification_code()
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)  # 15-minute expiry for invitations
            
            # Clean up old verification codes for this invitation
            PhoneVerification.query.filter_by(
                phone_number=normalized_phone,
                purpose='invitation_accept',
                invitation_token=invitation_token
            ).delete()
            
            # Create new verification record
            verification = PhoneVerification(
                phone_number=normalized_phone,
                verification_code=code,
                purpose='invitation_accept',
                invitation_token=invitation_token,
                expires_at=expires_at
            )
            
            db.session.add(verification)
            db.session.commit()
            
            # Send SMS
            property_name = invitation.property.name if invitation.property else "property"
            message = f"Your Hostify invitation code for {property_name} is: {code}\nValid for 15 minutes."
            sms_result = send_sms(normalized_phone, message)
            
            if not sms_result['success']:
                db.session.rollback()
                return {
                    'success': False,
                    'error': f"Failed to send SMS: {sms_result.get('error', 'Unknown error')}"
                }
            
            return {
                'success': True,
                'verification_id': str(verification.id),
                'message': f'Verification code sent to {normalized_phone}'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Error sending invitation code: {str(e)}'
            }
    
    @staticmethod
    def verify_invitation_code(phone_number: str, code: str, invitation_token: str, user_name: str) -> Dict[str, Any]:
        """
        Verify SMS code for invitation and create/update user account
        Returns: {'success': bool, 'user': dict, 'error': str}
        """
        try:
            # Normalize phone number
            normalized_phone = SMSAuthService.normalize_phone_number(phone_number)
            
            # Find verification record
            verification = PhoneVerification.query.filter_by(
                phone_number=normalized_phone,
                purpose='invitation_accept',
                invitation_token=invitation_token,
                is_verified=False
            ).order_by(PhoneVerification.created_at.desc()).first()
            
            if not verification:
                return {
                    'success': False,
                    'error': 'No verification code found. Please request a new code.'
                }
            
            # Check if expired
            if verification.is_expired():
                return {
                    'success': False,
                    'error': 'Verification code has expired. Please request a new code.'
                }
            
            # Check attempts limit
            if not verification.can_attempt():
                return {
                    'success': False,
                    'error': 'Too many failed attempts. Please request a new code.'
                }
            
            # Verify code
            if verification.verification_code != code:
                verification.attempts += 1
                db.session.commit()
                remaining_attempts = 3 - verification.attempts
                return {
                    'success': False,
                    'error': f'Invalid code. {remaining_attempts} attempts remaining.'
                }
            
            # Code is correct - find the invitation
            invitation = TeamInvitation.query.filter_by(
                invitation_token=invitation_token,
                invited_phone=normalized_phone,
                status='pending'
            ).first()
            
            if not invitation:
                return {
                    'success': False,
                    'error': 'Invitation not found or already accepted.'
                }
            
            # Create or find user account
            user = User.query.filter_by(phone=normalized_phone).first()
            if not user:
                # Create new user account with phone authentication
                # Generate a unique firebase_uid for phone users
                phone_firebase_uid = f"phone_{normalized_phone.replace('+', '')}"
                
                user = User(
                    firebase_uid=phone_firebase_uid,
                    email=f"phone.{normalized_phone.replace('+', '')}@hostify.local",  # Placeholder email
                    name=user_name,
                    phone=normalized_phone
                )
                db.session.add(user)
                db.session.flush()  # Get the user ID
            
            # Accept the invitation using existing team management logic
            from .team_management import accept_team_invitation
            result = accept_team_invitation(invitation_token, user.id)
            
            if not result['success']:
                db.session.rollback()
                return result
            
            # Mark verification as completed
            verification.is_verified = True
            verification.verified_at = datetime.now(timezone.utc)
            verification.user_id = user.id
            db.session.commit()
            
            return {
                'success': True,
                'user': user.to_dict(),
                'message': 'Account created and invitation accepted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Error verifying invitation code: {str(e)}'
            } 