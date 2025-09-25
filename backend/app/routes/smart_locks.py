"""
Smart lock management routes for TTLock integration
"""

from flask import Blueprint, request, jsonify, g
from ..models import SmartLock, AccessCode, AccessLog, Property, Reservation, db
from ..utils.auth import require_auth
from ..utils.database import get_user_by_firebase_uid
from ..services.ttlock_service import ttlock_service
from datetime import datetime, timezone
import logging

# Configure logging
logger = logging.getLogger(__name__)

smart_locks_bp = Blueprint('smart_locks', __name__)

@smart_locks_bp.route('/ttlock/status', methods=['GET'])
@require_auth
def get_ttlock_connection_status():
    """Get TTLock connection status for the current user"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Check if user has TTLock credentials and if they're valid
        is_connected = user.is_ttlock_token_valid()

        # Get count of user's locks (both assigned and unassigned)
        assigned_locks_count = SmartLock.query.filter_by(user_id=user.id).filter(SmartLock.property_id.isnot(None)).count()
        unassigned_locks_count = SmartLock.query.filter_by(user_id=user.id, property_id=None).count()
        total_locks_count = assigned_locks_count + unassigned_locks_count

        # Get decrypted username if available
        ttlock_username = None
        if is_connected and user.ttlock_username_encrypted:
            try:
                credentials = user.get_ttlock_credentials()
                ttlock_username = credentials['username'] if credentials else None
            except Exception:
                pass  # Ignore decryption errors

        return jsonify({
            'success': True,
            'is_connected': is_connected,
            'assigned_locks_count': assigned_locks_count,
            'unassigned_locks_count': unassigned_locks_count,
            'total_locks_count': total_locks_count,
            'ttlock_username': ttlock_username
        })

    except Exception as e:
        logger.error(f"Error getting TTLock connection status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_locks_bp.route('/ttlock/connect', methods=['POST'])
@require_auth
def connect_ttlock_account():
    """Connect TTLock account using app credentials (OAuth flow)"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get TTLock app credentials from request
        auth_data = request.get_json()
        if not auth_data:
            return jsonify({'success': False, 'error': 'No auth data provided'}), 400

        username = auth_data.get('username')  # TTLock app username (phone number or email)
        password = auth_data.get('password')  # TTLock app password

        if not username or not password:
            return jsonify({'success': False, 'error': 'TTLock app username and password required'}), 400

        # Authenticate with TTLock OAuth
        auth_result = ttlock_service.authenticate_with_app_credentials(username, password)

        if auth_result['success']:
            # Store credentials securely for future use
            user.store_ttlock_credentials(username, password)
            user.update_ttlock_token(
                access_token=auth_result['access_token'],
                expires_in=auth_result.get('expires_in', 3600),
                uid=auth_result.get('uid')
            )

            # Get locks from TTLock API
            ttlock_locks = ttlock_service.get_locks()

            stored_locks = []
            if ttlock_locks:
                # Store each lock in database
                for lock_data in ttlock_locks:
                    # Check if lock already exists
                    existing_lock = SmartLock.query.filter_by(ttlock_id=str(lock_data['lockId'])).first()
                    if existing_lock:
                        # Update existing lock
                        existing_lock.lock_name = lock_data.get('lockName', existing_lock.lock_name)
                        existing_lock.battery_level = lock_data.get('electricQuantity')

                        # Handle lock_version properly
                        lock_version_data = lock_data.get('lockVersion')
                        if isinstance(lock_version_data, dict):
                            existing_lock.lock_version = f"v{lock_version_data.get('protocolVersion', 'unknown')}"
                        elif lock_version_data:
                            existing_lock.lock_version = str(lock_version_data)

                        existing_lock.updated_at = datetime.now(timezone.utc)
                        stored_locks.append(existing_lock.to_dict())
                    else:
                        # Create new lock (unassigned to any property initially)
                        lock_version_data = lock_data.get('lockVersion')
                        lock_version_str = None
                        if isinstance(lock_version_data, dict):
                            # Convert dict to string representation
                            lock_version_str = f"v{lock_version_data.get('protocolVersion', 'unknown')}"
                        elif lock_version_data:
                            lock_version_str = str(lock_version_data)

                        smart_lock = SmartLock(
                            user_id=user.id,  # Assign to user, not specific property
                            property_id=None,  # Initially unassigned
                            ttlock_id=str(lock_data['lockId']),
                            lock_name=lock_data.get('lockName', 'TTLock'),
                            gateway_mac=lock_data.get('gatewayMac'),
                            lock_mac=lock_data.get('lockMac'),
                            lock_version=lock_version_str,
                            battery_level=lock_data.get('electricQuantity'),
                            settings={
                                'auto_lock_time': lock_data.get('autoLockTime'),
                                'special_value': lock_data.get('specialValue'),
                                'protocol_info': lock_data.get('lockVersion') if isinstance(lock_data.get('lockVersion'), dict) else None
                            }
                        )
                        db.session.add(smart_lock)
                        db.session.flush()  # Get the ID
                        stored_locks.append(smart_lock.to_dict())

                db.session.commit()

            return jsonify({
                'success': True,
                'message': 'TTLock account connected successfully',
                'access_token': auth_result['access_token'][:20] + '...',
                'uid': auth_result.get('uid'),
                'expires_in': auth_result.get('expires_in'),
                'locks_count': len(stored_locks),
                'locks': stored_locks
            })
        else:
            return jsonify({
                'success': False,
                'error': auth_result.get('error', 'TTLock authentication failed')
            }), 401

    except Exception as e:
        logger.error(f"TTLock connection failed: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_locks_bp.route('/ttlock/test-token', methods=['POST'])
@require_auth
def test_ttlock_token():
    """Test TTLock API with existing access token"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get access token from request
        token_data = request.get_json()
        if not token_data:
            return jsonify({'success': False, 'error': 'No token data provided'}), 400

        access_token = token_data.get('access_token')
        if not access_token:
            return jsonify({'success': False, 'error': 'access_token is required'}), 400

        # Test access token
        token_valid = ttlock_service.set_access_token(access_token)

        if token_valid:
            # Try to get locks list
            locks = ttlock_service.get_locks()

            return jsonify({
                'success': True,
                'message': 'TTLock access token is valid',
                'access_token': access_token[:20] + '...',
                'locks_count': len(locks) if locks else 0,
                'locks': locks[:3] if locks else []  # Show first 3 locks for testing
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid TTLock access token'}), 401

    except Exception as e:
        logger.error(f"TTLock token test failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_locks_bp.route('/properties/<property_id>/smart-locks', methods=['GET'])
@require_auth
def get_property_smart_locks(property_id):
    """Get all smart locks for a property"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Verify property ownership
        property_obj = Property.query.filter_by(id=property_id, user_id=user.id).first()
        if not property_obj:
            return jsonify({'success': False, 'error': 'Property not found or access denied'}), 404

        # Get smart locks
        smart_locks = SmartLock.query.filter_by(property_id=property_id).all()

        return jsonify({
            'success': True,
            'smart_locks': [lock.to_dict() for lock in smart_locks]
        })

    except Exception as e:
        logger.error(f"Failed to get smart locks: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_locks_bp.route('/properties/<property_id>/smart-locks', methods=['POST'])
@require_auth
def add_smart_lock(property_id):
    """Add a smart lock to a property"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Verify property ownership
        property_obj = Property.query.filter_by(id=property_id, user_id=user.id).first()
        if not property_obj:
            return jsonify({'success': False, 'error': 'Property not found or access denied'}), 404

        # Get lock data
        lock_data = request.get_json()
        if not lock_data:
            return jsonify({'success': False, 'error': 'No lock data provided'}), 400

        # Validate required fields
        required_fields = ['ttlock_id', 'lock_name', 'lock_mac']
        for field in required_fields:
            if not lock_data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

        # Check if lock already exists
        existing_lock = SmartLock.query.filter_by(ttlock_id=lock_data['ttlock_id']).first()
        if existing_lock:
            return jsonify({'success': False, 'error': 'Lock already exists in system'}), 409

        # Verify lock with TTLock API
        lock_detail = ttlock_service.get_lock_detail(lock_data['ttlock_id'])
        if not lock_detail:
            return jsonify({'success': False, 'error': 'Could not verify lock with TTLock API'}), 400

        # Create smart lock record
        smart_lock = SmartLock(
            user_id=user.id,  # ✅ FIX: Assign to user
            property_id=property_id,
            ttlock_id=lock_data['ttlock_id'],
            lock_name=lock_data['lock_name'],
            gateway_mac=lock_data.get('gateway_mac'),
            lock_mac=lock_data['lock_mac'],
            lock_version=lock_detail.get('lockVersion'),
            battery_level=lock_detail.get('electricQuantity'),
            settings=lock_data.get('settings', {})
        )

        db.session.add(smart_lock)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Smart lock added successfully',
            'smart_lock': smart_lock.to_dict()
        })

    except Exception as e:
        logger.error(f"Failed to add smart lock: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_locks_bp.route('/smart-locks/<lock_id>', methods=['PUT'])
@require_auth
def update_smart_lock(lock_id):
    """Update smart lock settings"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get smart lock and verify ownership
        smart_lock = SmartLock.query.join(Property).filter(
            SmartLock.id == lock_id,
            Property.user_id == user.id
        ).first()

        if not smart_lock:
            return jsonify({'success': False, 'error': 'Smart lock not found or access denied'}), 404

        # Get update data
        update_data = request.get_json()
        if not update_data:
            return jsonify({'success': False, 'error': 'No update data provided'}), 400

        # Update allowed fields
        if 'lock_name' in update_data:
            smart_lock.lock_name = update_data['lock_name']
        if 'settings' in update_data:
            smart_lock.settings = update_data['settings']

        smart_lock.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Smart lock updated successfully',
            'smart_lock': smart_lock.to_dict()
        })

    except Exception as e:
        logger.error(f"Failed to update smart lock: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_locks_bp.route('/smart-locks/<lock_id>', methods=['DELETE'])
@require_auth
def remove_smart_lock(lock_id):
    """Remove a smart lock from property"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get smart lock and verify ownership
        smart_lock = SmartLock.query.join(Property).filter(
            SmartLock.id == lock_id,
            Property.user_id == user.id
        ).first()

        if not smart_lock:
            return jsonify({'success': False, 'error': 'Smart lock not found or access denied'}), 404

        # Revoke all active access codes
        active_codes = AccessCode.query.filter_by(
            smart_lock_id=lock_id,
            status='active'
        ).all()

        for code in active_codes:
            ttlock_service.revoke_guest_access(str(code.id))

        # Delete the lock
        db.session.delete(smart_lock)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Smart lock removed successfully'
        })

    except Exception as e:
        logger.error(f"Failed to remove smart lock: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_locks_bp.route('/smart-locks/<lock_id>/sync', methods=['POST'])
@require_auth
def sync_smart_lock(lock_id):
    """Sync smart lock status with TTLock API"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get smart lock and verify ownership
        smart_lock = SmartLock.query.join(Property).filter(
            SmartLock.id == lock_id,
            Property.user_id == user.id
        ).first()

        if not smart_lock:
            return jsonify({'success': False, 'error': 'Smart lock not found or access denied'}), 404

        # Sync status
        success = ttlock_service.sync_lock_status(smart_lock)
        if success:
            return jsonify({
                'success': True,
                'message': 'Smart lock synced successfully',
                'smart_lock': smart_lock.to_dict()
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to sync with TTLock API'}), 500

    except Exception as e:
        logger.error(f"Failed to sync smart lock: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_locks_bp.route('/reservations/<reservation_id>/access-codes', methods=['POST'])
@require_auth
def create_access_code(reservation_id):
    """Create access code for a reservation"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get reservation and verify ownership
        reservation = Reservation.query.join(Property).filter(
            Reservation.id == reservation_id,
            Property.user_id == user.id
        ).first()

        if not reservation:
            return jsonify({'success': False, 'error': 'Reservation not found or access denied'}), 404

        # Get request data
        access_data = request.get_json()
        if not access_data:
            return jsonify({'success': False, 'error': 'No access data provided'}), 400

        smart_lock_id = access_data.get('smart_lock_id')
        if not smart_lock_id:
            return jsonify({'success': False, 'error': 'smart_lock_id is required'}), 400

        # Verify smart lock belongs to the property
        smart_lock = SmartLock.query.filter_by(
            id=smart_lock_id,
            property_id=reservation.property_id
        ).first()

        if not smart_lock:
            return jsonify({'success': False, 'error': 'Smart lock not found for this property'}), 404

        # Get guest information from reservation
        guest_name = reservation.guest_name_partial or 'Guest'
        guest_phone = access_data.get('guest_phone')
        guest_email = access_data.get('guest_email')

        # Create passcode
        is_one_time = access_data.get('is_one_time', False)
        access_code_id = ttlock_service.create_guest_passcode(
            reservation_id=reservation_id,
            smart_lock_id=smart_lock_id,
            guest_name=guest_name,
            check_in=reservation.check_in,
            check_out=reservation.check_out,
            guest_phone=guest_phone,
            guest_email=guest_email,
            is_one_time=is_one_time
        )

        if access_code_id:
            access_code = AccessCode.query.get(access_code_id)
            return jsonify({
                'success': True,
                'message': 'Access code created successfully',
                'access_code': access_code.to_dict()
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create access code'}), 500

    except Exception as e:
        logger.error(f"Failed to create access code: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_locks_bp.route('/access-codes/<access_code_id>', methods=['DELETE'])
@require_auth
def revoke_access_code(access_code_id):
    """Revoke an access code"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get access code and verify ownership
        access_code = AccessCode.query.join(SmartLock, Property).filter(
            AccessCode.id == access_code_id,
            Property.user_id == user.id
        ).first()

        if not access_code:
            return jsonify({'success': False, 'error': 'Access code not found or access denied'}), 404

        # Revoke passcode
        success = ttlock_service.revoke_guest_passcode(access_code_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'Access code revoked successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to revoke access code'}), 500

    except Exception as e:
        logger.error(f"Failed to revoke access code: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_locks_bp.route('/smart-locks/<lock_id>/access-logs', methods=['GET'])
@require_auth
def get_access_logs(lock_id):
    """Get access logs for a smart lock"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get smart lock and verify ownership
        smart_lock = SmartLock.query.join(Property).filter(
            SmartLock.id == lock_id,
            Property.user_id == user.id
        ).first()

        if not smart_lock:
            return jsonify({'success': False, 'error': 'Smart lock not found or access denied'}), 404

        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page

        # Get access logs
        logs_query = AccessLog.query.filter_by(smart_lock_id=lock_id).order_by(AccessLog.timestamp.desc())
        logs_paginated = logs_query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'access_logs': [log.to_dict() for log in logs_paginated.items],
            'total': logs_paginated.total,
            'pages': logs_paginated.pages,
            'current_page': logs_paginated.page,
            'has_next': logs_paginated.has_next,
            'has_prev': logs_paginated.has_prev
        })

    except Exception as e:
        logger.error(f"Failed to get access logs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_locks_bp.route('/smart-locks/<lock_id>/sync-logs', methods=['POST'])
@require_auth
def sync_access_logs(lock_id):
    """Sync access logs from TTLock API"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get smart lock and verify ownership
        smart_lock = SmartLock.query.join(Property).filter(
            SmartLock.id == lock_id,
            Property.user_id == user.id
        ).first()

        if not smart_lock:
            return jsonify({'success': False, 'error': 'Smart lock not found or access denied'}), 404

        # Get optional days_back parameter
        days_back = request.args.get('days_back', 7, type=int)
        days_back = min(max(days_back, 1), 30)  # Between 1 and 30 days

        # Sync logs
        logs_synced = ttlock_service.sync_access_logs(smart_lock, days_back)

        return jsonify({
            'success': True,
            'message': f'Synced {logs_synced} access logs',
            'logs_synced': logs_synced
        })

    except Exception as e:
        logger.error(f"Failed to sync access logs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_locks_bp.route('/smart-locks/<lock_id>/test-passcode', methods=['POST'])
@require_auth
def test_passcode(lock_id):
    """Generate a test passcode for a smart lock"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get smart lock and verify ownership
        smart_lock = SmartLock.query.join(Property).filter(
            SmartLock.id == lock_id,
            Property.user_id == user.id
        ).first()

        if not smart_lock:
            return jsonify({'success': False, 'error': 'Smart lock not found or access denied'}), 404

        # Set user context for TTLock service
        ttlock_service.set_user_context(user)

        # Generate test passcode (valid for 1 hour)
        from datetime import datetime, timezone, timedelta
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=1)

        result = ttlock_service.generate_random_passcode(
            lock_id=smart_lock.ttlock_id,
            start_date=int(start_time.timestamp() * 1000),
            end_date=int(end_time.timestamp() * 1000)
        )

        if result and result.get('success'):
            # Create a temporary reservation record for test codes (or handle null reservation)
            # For test codes, we need to handle the non-nullable reservation_id field
            # Let's create a placeholder reservation or modify the model

            # For now, let's skip database storage for test codes and return the passcode directly
            return jsonify({
                'success': True,
                'message': 'Test passcode generated successfully',
                'passcode': result.get('passcode'),
                'valid_until': end_time.isoformat(),
                'note': 'Test passcode generated but not stored in database (temporary for testing)'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to generate test passcode')
            }), 500

        # # Generate test passcode (valid for 1 hour)
        # from datetime import datetime, timezone, timedelta
        # start_time = datetime.now(timezone.utc)
        # end_time = start_time + timedelta(hours=1)
        #
        # result = ttlock_service.generate_random_passcode(
        #     lock_id=smart_lock.ttlock_id,
        #     start_date=int(start_time.timestamp() * 1000),
        #     end_date=int(end_time.timestamp() * 1000)
        # )
        #
        # if result and result.get('success'):
        #     # Create access code record for tracking
        #     access_code = AccessCode(
        #         smart_lock_id=lock_id,
        #         passcode=result.get('passcode'),
        #         passcode_id=str(result.get('keyboardPwdId')) if result.get('keyboardPwdId') else None,
        #         start_date=start_time,
        #         end_date=end_time,
        #         guest_name='Test Code',
        #         is_one_time=False,
        #         status='active'
        #     )
        #
        #     db.session.add(access_code)
        #     db.session.commit()
        #
        #     return jsonify({
        #         'success': True,
        #         'message': 'Test passcode generated successfully',
        #         'passcode': result.get('passcode'),
        #         'valid_until': end_time.isoformat(),
        #         'access_code_id': str(access_code.id)
        #     })
        # else:
        #     return jsonify({
        #         'success': False,
        #         'error': result.get('error', 'Failed to generate test passcode')
        #     }), 500

    except Exception as e:
        logger.error(f"Failed to generate test passcode: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_locks_bp.route('/ttlock/disconnect', methods=['POST'])
@require_auth
def disconnect_ttlock_account():
    """Disconnect TTLock account and clear stored credentials"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Clear all TTLock credentials
        user.clear_ttlock_credentials()

        # Delete all smart locks associated with this user (complete removal)
        deleted_count = SmartLock.query.filter_by(user_id=user.id).delete()

        db.session.commit()

        logger.info(f"Disconnected TTLock account and deleted {deleted_count} smart locks for user {user.id}")

        return jsonify({
            'success': True,
            'message': 'TTLock account disconnected successfully'
        })

    except Exception as e:
        logger.error(f"Failed to disconnect TTLock account: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_locks_bp.route('/ttlock/sync', methods=['POST'])
@require_auth
def sync_ttlock_locks():
    """Sync locks from TTLock account (fetch new locks and update existing ones)"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Check if user has TTLock credentials
        if not user.is_ttlock_token_valid():
            return jsonify({'success': False, 'error': 'TTLock account not connected or token expired'}), 401

        # Set user context for TTLock service
        ttlock_service.set_user_context(user)

        # Ensure we have a valid access token
        if not ttlock_service.ensure_authenticated():
            return jsonify({'success': False, 'error': 'TTLock authentication failed. Please reconnect your account.'}), 401

        # Debug logging
        logger.info(f"Syncing locks with access token: {ttlock_service.access_token[:20]}..." if ttlock_service.access_token else "No access token available")

        # Fetch locks from TTLock API
        locks_data = ttlock_service.get_locks()
        if not locks_data:
            return jsonify({'success': False, 'error': 'Failed to fetch locks from TTLock API'}), 500

        new_locks_count = 0
        updated_locks_count = 0
        existing_lock_ids = set()

        # Process each lock from TTLock API
        for lock_data in locks_data:
            ttlock_id = str(lock_data['lockId'])

            # Check if lock already exists
            existing_lock = SmartLock.query.filter_by(
                user_id=user.id,
                ttlock_id=ttlock_id
            ).first()

            if existing_lock:
                # Update existing lock
                existing_lock.lock_name = lock_data.get('lockName', existing_lock.lock_name)
                existing_lock.battery_level = lock_data.get('electricQuantity', existing_lock.battery_level)
                existing_lock.updated_at = datetime.now(timezone.utc)

                # Update settings if available
                if 'autoLockTime' in lock_data:
                    settings = existing_lock.settings or {}
                    settings['auto_lock_time'] = lock_data['autoLockTime']
                    existing_lock.settings = settings

                updated_locks_count += 1
                existing_lock_ids.add(ttlock_id)
            else:
                # Create new lock (unassigned initially)
                lock_version_data = lock_data.get('lockVersion')
                if isinstance(lock_version_data, dict):
                    lock_version_str = f"v{lock_version_data.get('protocolVersion', 'unknown')}"
                elif lock_version_data:
                    lock_version_str = str(lock_version_data)
                else:
                    lock_version_str = 'unknown'

                new_lock = SmartLock(
                    user_id=user.id,
                    property_id=None,  # Initially unassigned
                    ttlock_id=ttlock_id,
                    lock_name=lock_data.get('lockName', 'TTLock'),
                    gateway_mac=lock_data.get('gatewayMac'),
                    lock_mac=lock_data.get('lockMac'),
                    lock_version=lock_version_str,
                    battery_level=lock_data.get('electricQuantity'),
                    settings={
                        'auto_lock_time': lock_data.get('autoLockTime'),
                        'privacy_lock': lock_data.get('privacyLock'),
                        'delete_pwd': lock_data.get('deletePwd'),
                        'feature_value': lock_data.get('featureValue'),
                    }
                )

                db.session.add(new_lock)
                new_locks_count += 1
                existing_lock_ids.add(ttlock_id)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Sync completed: {new_locks_count} new locks added, {updated_locks_count} locks updated',
            'new_locks_count': new_locks_count,
            'updated_locks_count': updated_locks_count,
            'total_locks_count': len(existing_lock_ids)
        })

    except Exception as e:
        logger.error(f"Failed to sync TTLock locks: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@smart_locks_bp.route('/smart-locks/unassigned', methods=['GET'])
@require_auth
def get_unassigned_locks():
    """Get all unassigned smart locks for the user"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get unassigned smart locks
        unassigned_locks = SmartLock.query.filter_by(
            user_id=user.id,
            property_id=None
        ).all()

        return jsonify({
            'success': True,
            'unassigned_locks': [lock.to_dict() for lock in unassigned_locks]
        })

    except Exception as e:
        logger.error(f"Failed to get unassigned locks: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_locks_bp.route('/smart-locks/<lock_id>/assign', methods=['POST'])
@require_auth
def assign_lock_to_property(lock_id):
    """Assign a smart lock to a property"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get assignment data
        assign_data = request.get_json()
        if not assign_data:
            return jsonify({'success': False, 'error': 'No assignment data provided'}), 400

        property_id = assign_data.get('property_id')
        if not property_id:
            return jsonify({'success': False, 'error': 'property_id is required'}), 400

        # Verify property ownership
        property_obj = Property.query.filter_by(id=property_id, user_id=user.id).first()
        if not property_obj:
            return jsonify({'success': False, 'error': 'Property not found or access denied'}), 404

        # Get smart lock and verify ownership
        smart_lock = SmartLock.query.filter_by(id=lock_id, user_id=user.id).first()
        if not smart_lock:
            return jsonify({'success': False, 'error': 'Smart lock not found or access denied'}), 404

        # Assign lock to property
        smart_lock.property_id = property_id
        smart_lock.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Smart lock "{smart_lock.lock_name}" assigned to property "{property_obj.name}"',
            'smart_lock': smart_lock.to_dict()
        })

    except Exception as e:
        logger.error(f"Failed to assign lock to property: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_locks_bp.route('/smart-locks/<lock_id>/unassign', methods=['POST'])
@require_auth
def unassign_lock_from_property(lock_id):
    """Remove a smart lock assignment from a property"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Debug logging
        logger.info(f"Unassign request - Lock ID: {lock_id}, User ID: {user.id}")

        # Get smart lock and verify ownership
        smart_lock = SmartLock.query.filter_by(id=lock_id, user_id=user.id).first()

        if not smart_lock:
            # Additional debugging - check if lock exists at all
            any_lock = SmartLock.query.filter_by(id=lock_id).first()
            if any_lock:
                logger.warning(f"Lock {lock_id} exists but belongs to user {any_lock.user_id}, not {user.id}")
            else:
                logger.warning(f"Lock {lock_id} does not exist in database")
            return jsonify({'success': False, 'error': 'Smart lock not found or access denied'}), 404

        # Unassign lock from property
        property_name = smart_lock.property.name if smart_lock.property else 'Unknown Property'
        smart_lock.property_id = None
        smart_lock.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Smart lock "{smart_lock.lock_name}" unassigned from property "{property_name}"',
            'smart_lock': smart_lock.to_dict()
        })

    except Exception as e:
        logger.error(f"Failed to unassign lock from property: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500