"""
TTLock API Service for smart lock integration using passcodes
"""

import os
import requests
import hashlib
import time
import logging
import random
import string
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from ..models import SmartLock, AccessCode, AccessLog, db

# Configure logging
logger = logging.getLogger(__name__)

class TTLockService:
    """Service class for TTLock API integration using passcodes"""

    def __init__(self):
        self.base_url = "https://euapi.ttlock.com"  # Fixed: was euopen, should be euapi
        self.client_id = os.getenv('TTLOCK_CLIENT_ID')
        self.client_secret = os.getenv('TTLOCK_CLIENT_SECRET')
        self.access_token = None  # Will be obtained via OAuth
        self.current_user = None  # Will be set when needed

        if not all([self.client_id, self.client_secret]):
            logger.warning("TTLock credentials not configured. Set TTLOCK_CLIENT_ID and TTLOCK_CLIENT_SECRET environment variables.")

    def _make_request(self, endpoint: str, method: str = 'POST', params: Dict = None, data: Dict = None, need_auth: bool = True) -> Dict:
        """Make authenticated request to TTLock API"""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            # Add common params
            if params is None:
                params = {}

            params['clientId'] = self.client_id
            params['date'] = int(time.time() * 1000)  # Current timestamp in milliseconds

            # Add access token for authenticated requests
            if need_auth and self.access_token:
                params['accessToken'] = self.access_token

            if method == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=30)
            else:
                response = requests.post(url, params=params, data=data, headers=headers, timeout=30)

            response.raise_for_status()
            result = response.json()

            if result.get('errcode', 0) != 0:
                logger.error(f"TTLock API error: {result.get('errmsg', 'Unknown error')}")
                raise Exception(f"TTLock API error: {result.get('errmsg', 'Unknown error')}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"TTLock API request failed: {str(e)}")
            raise Exception(f"TTLock API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"TTLock API error: {str(e)}")
            raise

    def authenticate_with_app_credentials(self, username: str, password: str) -> Dict:
        """
        Get access token using TTLock app credentials (OAuth flow)
        username: TTLock app username (phone number or email)
        password: TTLock app password (will be MD5 hashed)
        """
        try:
            # Create MD5 hash of password
            password_hash = hashlib.md5(password.encode()).hexdigest()

            # For OAuth, we need to send data as form-encoded POST body
            data = {
                'clientId': self.client_id,
                'clientSecret': self.client_secret,
                'username': username,
                'password': password_hash
            }

            # Special OAuth request - different from regular API calls
            url = f"{self.base_url}/oauth2/token"
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            response = requests.post(url, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()

            if result.get('errcode', 0) != 0:
                logger.error(f"TTLock OAuth error: {result.get('errmsg', 'Unknown error')}")
                return {'success': False, 'error': result.get('errmsg', 'Authentication failed')}

            if 'access_token' in result:
                self.access_token = result['access_token']
                logger.info("Successfully authenticated with TTLock app credentials")
                return {
                    'success': True,
                    'access_token': result['access_token'],
                    'uid': result.get('uid'),
                    'expires_in': result.get('expires_in', 7776000),  # 90 days default
                    'refresh_token': result.get('refresh_token')
                }
            else:
                logger.error("Failed to get access token from TTLock OAuth")
                return {'success': False, 'error': 'Authentication failed'}

        except requests.exceptions.RequestException as e:
            logger.error(f"TTLock OAuth request failed: {str(e)}")
            return {'success': False, 'error': f'Network error: {str(e)}'}
        except Exception as e:
            logger.error(f"TTLock OAuth authentication failed: {str(e)}")
            return {'success': False, 'error': str(e)}

    def set_access_token(self, access_token: str) -> bool:
        """Set access token (for testing or when token is already available)"""
        try:
            self.access_token = access_token

            # Test the token by trying to get locks
            locks = self.get_locks()
            if locks is not None:
                logger.info("Successfully validated TTLock access token")
                return True
            else:
                logger.error("Invalid TTLock access token")
                self.access_token = None
                return False

        except Exception as e:
            logger.error(f"TTLock token validation failed: {str(e)}")
            self.access_token = None
            return False

    def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refresh expired access token"""
        try:
            params = {
                'clientId': self.client_id,
                'clientSecret': self.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }

            response = self._make_request('/oauth2/token', 'POST', params=params, need_auth=False)

            if 'access_token' in response:
                self.access_token = response['access_token']
                logger.info("Successfully refreshed TTLock access token")
                return {
                    'success': True,
                    'access_token': response['access_token'],
                    'expires_in': response.get('expires_in', 7776000),
                    'refresh_token': response.get('refresh_token')
                }
            else:
                logger.error("Failed to refresh TTLock access token")
                return {'success': False, 'error': 'Token refresh failed'}

        except Exception as e:
            logger.error(f"TTLock token refresh failed: {str(e)}")
            return {'success': False, 'error': str(e)}

    def get_locks(self, page_no: int = 1, page_size: int = 20) -> List[Dict]:
        """Get list of locks from TTLock API"""
        try:
            params = {
                'pageNo': page_no,
                'pageSize': page_size
            }

            response = self._make_request('/v3/lock/list', 'POST', params=params)
            return response.get('list', [])

        except Exception as e:
            logger.error(f"Failed to get locks: {str(e)}")
            return []

    def get_lock_detail(self, lock_id: str) -> Optional[Dict]:
        """Get detailed information about a specific lock"""
        try:
            params = {
                'lockId': lock_id
            }

            response = self._make_request('/v3/lock/detail', 'POST', params=params)
            return response

        except Exception as e:
            logger.error(f"Failed to get lock detail: {str(e)}")
            return None

    def generate_random_passcode_api(self, lock_id: str, start_date: int, end_date: int,
                                    password_type: int = 2) -> Optional[Dict]:
        """
        Generate a random passcode using TTLock's random passcode API
        password_type: 1=permanent, 2=timed, 3=one-time, 4=delete, 5=recurring
        """
        try:
            params = {
                'lockId': lock_id,
                'startDate': start_date,
                'endDate': end_date,
                'passwordType': password_type
            }

            response = self._make_request('/v3/lock/getPassword', 'POST', params=params)
            return response

        except Exception as e:
            logger.error(f"Failed to generate random passcode: {str(e)}")
            return None

    def delete_passcode(self, lock_id: str, password_id: str) -> bool:
        """Delete/revoke a passcode"""
        try:
            params = {
                'lockId': lock_id,
                'passwordId': password_id
            }

            response = self._make_request('/v3/lock/deletePassword', 'POST', params=params)
            return True

        except Exception as e:
            logger.error(f"Failed to delete passcode: {str(e)}")
            return False

    def get_lock_records(self, lock_id: str, start_date: int, end_date: int,
                        page_no: int = 1, page_size: int = 20) -> List[Dict]:
        """Get access records for a lock"""
        try:
            params = {
                'lockId': lock_id,
                'startDate': start_date,
                'endDate': end_date,
                'pageNo': page_no,
                'pageSize': page_size
            }

            response = self._make_request('/v3/lock/listRecord', 'POST', params=params)
            return response.get('list', [])

        except Exception as e:
            logger.error(f"Failed to get lock records: {str(e)}")
            return []

    def sync_lock_status(self, smart_lock: SmartLock) -> bool:
        """Sync lock status and battery level from TTLock API"""
        try:
            lock_detail = self.get_lock_detail(smart_lock.ttlock_id)
            if lock_detail:
                # Update lock information
                smart_lock.battery_level = lock_detail.get('electricQuantity')
                smart_lock.lock_version = lock_detail.get('lockVersion')
                smart_lock.status = 'active' if lock_detail.get('lockData') else 'offline'
                smart_lock.updated_at = datetime.now(timezone.utc)

                db.session.commit()
                logger.info(f"Updated lock status for {smart_lock.lock_name}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Failed to sync lock status: {str(e)}")
            return False

    def set_user_context(self, user):
        """Set the current user context for accessing stored credentials"""
        self.current_user = user

    def ensure_authenticated(self):
        """Ensure we have a valid access token, re-authenticate if needed"""
        if not self.current_user:
            logger.error("No user context set for TTLock authentication")
            return False

        # Check if current token is still valid
        if self.current_user.is_ttlock_token_valid():
            self.access_token = self.current_user.ttlock_access_token
            return True

        # Token expired or doesn't exist, try to re-authenticate
        username, password = self.current_user.get_ttlock_credentials()
        if not username or not password:
            logger.error("No stored TTLock credentials found for user")
            return False

        # Re-authenticate with stored credentials
        logger.info("TTLock token expired, re-authenticating with stored credentials")
        auth_result = self.authenticate_with_app_credentials(username, password)

        if auth_result.get('success'):
            # Update stored token info
            self.current_user.update_ttlock_token(
                access_token=auth_result['access_token'],
                expires_in=auth_result.get('expires_in', 3600),  # Default 1 hour
                uid=auth_result.get('uid')
            )

            # Save to database
            from ..models import db
            db.session.commit()

            self.access_token = auth_result['access_token']
            logger.info("TTLock re-authentication successful")
            return True
        else:
            logger.error(f"TTLock re-authentication failed: {auth_result.get('error')}")
            return False

    def generate_random_passcode(self, lock_id: str, start_date: int, end_date: int) -> Dict:
        """Generate a random passcode via TTLock API"""
        try:
            # Ensure we have valid authentication
            if not self.ensure_authenticated():
                return {
                    'success': False,
                    'error': 'TTLock authentication failed. Please reconnect your TTLock account.'
                }

            # Use form data instead of URL params
            data = {
                'clientId': self.client_id,
                'accessToken': self.access_token,
                'lockId': str(lock_id),  # Ensure it's a string
                'keyboardPwdType': '3',  # Period type (temporary passcode) - as string
                'keyboardPwdName': 'Test Code',
                'startDate': str(start_date),  # Convert to string
                'endDate': str(end_date),      # Convert to string
                'date': str(int(time.time() * 1000))  # Convert to string
            }

            # Debug logging
            logger.info(f"Generating passcode for lock {lock_id} with data: {data}")

            # Make POST request with form data
            url = f"{self.base_url}/v3/keyboardPwd/get"
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            import requests
            response = requests.post(url, data=data, headers=headers, timeout=30)

            logger.info(f"TTLock API response status: {response.status_code}")
            logger.info(f"TTLock API response body: {response.text}")

            if response.status_code == 200:
                try:
                    result = response.json()
                    if 'keyboardPwd' in result:
                        return {
                            'success': True,
                            'passcode': result['keyboardPwd'],
                            'keyboardPwdId': result.get('keyboardPwdId')
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'Invalid response format: {result}'
                        }
                except ValueError as e:
                    return {
                        'success': False,
                        'error': f'Invalid JSON response: {response.text}'
                    }
            else:
                error_text = response.text if response.text else f"HTTP {response.status_code}"
                return {
                    'success': False,
                    'error': f'TTLock API error ({response.status_code}): {error_text}'
                }

        except Exception as e:
            logger.error(f"Failed to generate random passcode: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def generate_random_passcode_api(self, lock_id: str, start_date: int, end_date: int, password_type: int = 2) -> Dict:
        """Generate a random passcode via TTLock API (legacy method)"""
        return self.generate_random_passcode(lock_id, start_date, end_date)

    def create_guest_passcode(self, reservation_id: str, smart_lock_id: str,
                             guest_name: str, check_in: datetime, check_out: datetime,
                             guest_phone: str = None, guest_email: str = None,
                             is_one_time: bool = False) -> Optional[str]:
        """Create temporary random passcode for a guest reservation using TTLock API"""
        try:
            smart_lock = SmartLock.query.get(smart_lock_id)
            if not smart_lock:
                raise Exception("Smart lock not found")

            # Convert datetime to TTLock timestamp format (milliseconds)
            start_timestamp = int(check_in.timestamp() * 1000)
            end_timestamp = int(check_out.timestamp() * 1000)

            # Generate random passcode via TTLock API (no custom passcode needed!)
            password_type = 3 if is_one_time else 2  # 3=one-time, 2=timed
            passcode_response = self.generate_random_passcode_api(
                lock_id=smart_lock.ttlock_id,
                start_date=start_timestamp,
                end_date=end_timestamp,
                password_type=password_type
            )

            if passcode_response and 'password' in passcode_response:
                # TTLock generates the passcode for us!
                generated_passcode = str(passcode_response['password'])
                password_id = str(passcode_response.get('passwordId', ''))

                # Create access code record
                access_code = AccessCode(
                    reservation_id=reservation_id,
                    smart_lock_id=smart_lock_id,
                    passcode=generated_passcode,
                    passcode_id=password_id,
                    start_time=check_in,
                    end_time=check_out,
                    guest_phone=guest_phone,
                    guest_email=guest_email,
                    is_one_time=is_one_time,
                    max_usage=1 if is_one_time else None,
                    status='active'
                )

                db.session.add(access_code)
                db.session.commit()

                logger.info(f"Created random passcode {generated_passcode} for guest {guest_name} on lock {smart_lock.lock_name}")
                return str(access_code.id)
            else:
                logger.error(f"Failed to generate random passcode for guest {guest_name}: {passcode_response}")
                return None

        except Exception as e:
            logger.error(f"Failed to create guest passcode: {str(e)}")
            db.session.rollback()
            return None

    def revoke_guest_passcode(self, access_code_id: str) -> bool:
        """Revoke guest passcode"""
        try:
            access_code = AccessCode.query.get(access_code_id)
            if not access_code:
                return False

            smart_lock = SmartLock.query.get(access_code.smart_lock_id)
            if not smart_lock:
                return False

            if access_code.passcode_id and self.delete_passcode(smart_lock.ttlock_id, access_code.passcode_id):
                access_code.status = 'revoked'
                access_code.revoked_at = datetime.now(timezone.utc)
                db.session.commit()

                logger.info(f"Revoked passcode {access_code.passcode}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Failed to revoke guest passcode: {str(e)}")
            return False

    def process_webhook_record(self, webhook_data: Dict) -> bool:
        """Process unlock record received via webhook"""
        try:
            # Log the webhook data for debugging
            logger.info(f"Processing TTLock webhook: {webhook_data}")

            lock_id = webhook_data.get('lockId')
            if not lock_id:
                logger.warning("No lockId found in webhook data")
                return False

            # Try to find the smart lock
            try:
                smart_lock = SmartLock.query.filter_by(ttlock_id=str(lock_id)).first()
                if not smart_lock:
                    logger.warning(f"Received webhook for unknown lock ID: {lock_id}")
                    # Return True anyway since webhook was received successfully
                    return True
            except Exception as db_error:
                logger.error(f"Database error when looking up lock: {db_error}")
                # Return True since webhook was received, even if we can't process it
                return True

            # Extract record information
            record_time = datetime.fromtimestamp(
                webhook_data.get('records', [{}])[0].get('lockDate', time.time() * 1000) / 1000,
                tz=timezone.utc
            ) if webhook_data.get('records') else datetime.now(timezone.utc)

            # Check if this record already exists
            existing_log = AccessLog.query.filter_by(
                smart_lock_id=smart_lock.id,
                timestamp=record_time
            ).first()

            if existing_log:
                return True  # Already processed

            # Map unlock method to action
            unlock_method = webhook_data.get('records', [{}])[0].get('method', 0) if webhook_data.get('records') else 0
            action_map = {
                1: 'unlock',  # Password unlock
                2: 'unlock',  # Key unlock
                3: 'unlock',  # Card unlock
                4: 'unlock',  # Fingerprint unlock
                5: 'unlock',  # App unlock
                6: 'failed_attempt'  # Failed attempt
            }
            action = action_map.get(unlock_method, 'unlock')

            # Try to find matching access code if it was a password unlock
            access_code_id = None
            if unlock_method == 1:  # Password unlock
                password_used = webhook_data.get('records', [{}])[0].get('password')
                if password_used:
                    access_code = AccessCode.query.filter_by(
                        smart_lock_id=smart_lock.id,
                        passcode=str(password_used),
                        status='active'
                    ).first()

                    if access_code:
                        access_code_id = access_code.id
                        # Update usage count
                        access_code.usage_count += 1

                        # Check if it's one-time use or reached max usage
                        if access_code.is_one_time or (access_code.max_usage and access_code.usage_count >= access_code.max_usage):
                            access_code.status = 'expired'

            # Create access log
            access_log = AccessLog(
                smart_lock_id=smart_lock.id,
                access_code_id=access_code_id,
                action=action,
                timestamp=record_time,
                user_info=webhook_data
            )

            db.session.add(access_log)
            db.session.commit()

            logger.info(f"Processed webhook record for lock {smart_lock.lock_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to process webhook record: {str(e)}")
            db.session.rollback()
            return False

    def sync_access_logs(self, smart_lock: SmartLock, days_back: int = 7) -> int:
        """Sync access logs from TTLock API"""
        try:
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days_back)

            start_timestamp = int(start_date.timestamp() * 1000)
            end_timestamp = int(end_date.timestamp() * 1000)

            # Get records from API
            records = self.get_lock_records(
                lock_id=smart_lock.ttlock_id,
                start_date=start_timestamp,
                end_date=end_timestamp
            )

            logs_created = 0
            for record in records:
                # Check if log already exists
                record_time = datetime.fromtimestamp(record.get('lockDate', 0) / 1000, tz=timezone.utc)

                existing_log = AccessLog.query.filter_by(
                    smart_lock_id=smart_lock.id,
                    timestamp=record_time
                ).first()

                if not existing_log:
                    # Map TTLock record type to our action
                    unlock_method = record.get('method', 0)
                    action_map = {
                        1: 'unlock',  # Password
                        2: 'unlock',  # Key
                        3: 'unlock',  # Card
                        4: 'unlock',  # Fingerprint
                        5: 'unlock',  # App
                        6: 'failed_attempt'
                    }
                    action = action_map.get(unlock_method, 'unlock')

                    # Try to match access code for password unlocks
                    access_code_id = None
                    if unlock_method == 1 and record.get('password'):
                        access_code = AccessCode.query.filter_by(
                            smart_lock_id=smart_lock.id,
                            passcode=str(record.get('password'))
                        ).first()
                        if access_code:
                            access_code_id = access_code.id

                    access_log = AccessLog(
                        smart_lock_id=smart_lock.id,
                        access_code_id=access_code_id,
                        action=action,
                        timestamp=record_time,
                        user_info=record
                    )

                    db.session.add(access_log)
                    logs_created += 1

            if logs_created > 0:
                db.session.commit()
                logger.info(f"Synced {logs_created} access logs for lock {smart_lock.lock_name}")

            return logs_created

        except Exception as e:
            logger.error(f"Failed to sync access logs: {str(e)}")
            db.session.rollback()
            return 0

# Global service instance
ttlock_service = TTLockService()