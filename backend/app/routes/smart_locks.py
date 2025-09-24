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
        property_id = auth_data.get('property_id')  # Which property to associate locks with

        if not username or not password:
            return jsonify({'success': False, 'error': 'TTLock app username and password required'}), 400

        if not property_id:
            return jsonify({'success': False, 'error': 'property_id is required'}), 400

        # Verify property ownership
        property_obj = Property.query.filter_by(id=property_id, user_id=user.id).first()
        if not property_obj:
            return jsonify({'success': False, 'error': 'Property not found or access denied'}), 404

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
                        # Create new lock
                        lock_version_data = lock_data.get('lockVersion')
                        lock_version_str = None
                        if isinstance(lock_version_data, dict):
                            # Convert dict to string representation
                            lock_version_str = f"v{lock_version_data.get('protocolVersion', 'unknown')}"
                        elif lock_version_data:
                            lock_version_str = str(lock_version_data)

                        smart_lock = SmartLock(
                            property_id=property_id,
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
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'TTLock account disconnected successfully'
        })

    except Exception as e:
        logger.error(f"Failed to disconnect TTLock account: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500