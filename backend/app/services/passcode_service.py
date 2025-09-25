"""
Passcode generation service for reservation smart lock integration
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List, Tuple
from ..models import Reservation, Property, SmartLock, ReservationPasscode, User, db
from .ttlock_service import ttlock_service
from ..utils.database import get_user_by_id

# Configure logging
logger = logging.getLogger(__name__)

class PasscodeService:
    """Service for generating and managing reservation passcodes"""

    def __init__(self):
        self.ttlock_service = ttlock_service

    def calculate_passcode_validity(self, check_in: datetime, check_out: datetime) -> Tuple[datetime, datetime]:
        """
        Calculate passcode validity period based on reservation times
        Valid from: check-in - 1 hour
        Valid until: check-out + 1 hour
        """
        valid_from = check_in - timedelta(hours=1)
        valid_until = check_out + timedelta(hours=1)
        return valid_from, valid_until

    def should_generate_passcode(self, reservation: Reservation) -> bool:
        """
        Check if we should generate a passcode for this reservation
        Generate 2-3 hours before check-in
        """
        if not reservation.check_in:
            return False

        now = datetime.now(timezone.utc)
        # Generate 3 hours before check-in
        generation_time = reservation.check_in - timedelta(hours=3)

        return now >= generation_time

    def get_property_smart_lock_config(self, property_id: str) -> Dict:
        """Get smart lock configuration for a property"""
        try:
            property_obj = Property.query.get(property_id)
            if not property_obj:
                return {'type': 'traditional', 'locks': []}

            # Get assigned smart locks for this property
            smart_locks = SmartLock.query.filter_by(
                property_id=property_id,
                status='active'
            ).all()

            return {
                'type': property_obj.smart_lock_type,
                'instructions': property_obj.smart_lock_instructions,
                'settings': property_obj.smart_lock_settings or {},
                'locks': [lock.to_dict() for lock in smart_locks]
            }

        except Exception as e:
            logger.error(f"Failed to get property smart lock config: {str(e)}")
            return {'type': 'traditional', 'locks': []}

    def generate_ttlock_passcode(self, reservation: Reservation, smart_locks: List[SmartLock]) -> Dict:
        """
        Generate TTLock passcode for multiple locks (same passcode for all)
        """
        try:
            if not smart_locks:
                return {'success': False, 'error': 'No smart locks available'}

            # Calculate passcode validity
            valid_from, valid_until = self.calculate_passcode_validity(
                reservation.check_in, reservation.check_out
            )

            # Convert to TTLock timestamp format (milliseconds)
            start_timestamp = int(valid_from.timestamp() * 1000)
            end_timestamp = int(valid_until.timestamp() * 1000)

            # Get property owner for TTLock authentication
            property_obj = Property.query.get(reservation.property_id)
            if not property_obj:
                return {'success': False, 'error': 'Property not found'}

            user = get_user_by_id(property_obj.user_id)
            if not user:
                return {'success': False, 'error': 'Property owner not found'}

            # Set user context for TTLock service
            self.ttlock_service.set_user_context(user)

            # Generate passcode for the first lock (we'll use the same code for all)
            primary_lock = smart_locks[0]
            passcode_result = self.ttlock_service.generate_random_passcode(
                lock_id=primary_lock.ttlock_id,
                start_date=start_timestamp,
                end_date=end_timestamp
            )

            if not passcode_result.get('success'):
                return {
                    'success': False,
                    'error': f"TTLock API error: {passcode_result.get('error', 'Unknown error')}"
                }

            passcode = passcode_result.get('passcode')
            ttlock_password_id = passcode_result.get('keyboardPwdId')

            if not passcode:
                return {'success': False, 'error': 'No passcode returned from TTLock API'}

            # For additional locks, we need to set the same passcode
            # Note: TTLock API might not support setting custom passcodes
            # For now, we'll generate individual passcodes for each lock
            # In production, you might need to use a different approach

            lock_passcodes = []
            for lock in smart_locks:
                if lock.id == primary_lock.id:
                    # Use the already generated passcode
                    lock_passcodes.append({
                        'lock_id': lock.id,
                        'passcode': passcode,
                        'ttlock_password_id': ttlock_password_id
                    })
                else:
                    # Generate passcode for additional locks
                    additional_result = self.ttlock_service.generate_random_passcode(
                        lock_id=lock.ttlock_id,
                        start_date=start_timestamp,
                        end_date=end_timestamp
                    )

                    if additional_result.get('success'):
                        lock_passcodes.append({
                            'lock_id': lock.id,
                            'passcode': additional_result.get('passcode'),
                            'ttlock_password_id': additional_result.get('keyboardPwdId')
                        })
                    else:
                        logger.warning(f"Failed to generate passcode for lock {lock.id}: {additional_result.get('error')}")

            # Create ReservationPasscode record
            reservation_passcode = ReservationPasscode(
                reservation_id=reservation.id,
                property_id=reservation.property_id,
                passcode=passcode,  # Use primary passcode as the main one
                valid_from=valid_from,
                valid_until=valid_until,
                generation_method='ttlock',
                status='active',
                ttlock_access_codes={
                    'lock_passcodes': lock_passcodes,
                    'primary_lock_id': primary_lock.id
                }
            )

            db.session.add(reservation_passcode)
            db.session.commit()

            logger.info(f"Generated TTLock passcode for reservation {reservation.id}: {passcode}")

            # Send notification to host about successful passcode generation
            try:
                from .notification_service import notification_service
                notification_service.send_passcode_ready_notification(str(reservation_passcode.id))
            except Exception as notify_error:
                logger.warning(f"Failed to send passcode ready notification: {str(notify_error)}")

            return {
                'success': True,
                'passcode': passcode,
                'valid_from': valid_from.isoformat(),
                'valid_until': valid_until.isoformat(),
                'lock_count': len(lock_passcodes),
                'reservation_passcode_id': str(reservation_passcode.id)
            }

        except Exception as e:
            logger.error(f"Failed to generate TTLock passcode: {str(e)}")
            db.session.rollback()

            # Send failure notification to host
            try:
                from .notification_service import notification_service
                notification_service.send_ttlock_failure_notification(str(reservation.id), str(e))
            except Exception as notify_error:
                logger.warning(f"Failed to send TTLock failure notification: {str(notify_error)}")

            return {'success': False, 'error': str(e)}

    def create_manual_passcode_entry(self, reservation: Reservation) -> Dict:
        """
        Create manual passcode entry for properties with manual smart locks
        """
        try:
            # Calculate passcode validity
            valid_from, valid_until = self.calculate_passcode_validity(
                reservation.check_in, reservation.check_out
            )

            # Create ReservationPasscode record with null passcode (manual entry pending)
            reservation_passcode = ReservationPasscode(
                reservation_id=reservation.id,
                property_id=reservation.property_id,
                passcode=None,  # Will be entered manually by host
                valid_from=valid_from,
                valid_until=valid_until,
                generation_method='manual',
                status='pending'  # Waiting for host to enter passcode
            )

            db.session.add(reservation_passcode)
            db.session.commit()

            logger.info(f"Created manual passcode entry for reservation {reservation.id}")

            # Send notification to host requesting manual passcode entry
            try:
                from .notification_service import notification_service
                notification_service.send_manual_passcode_notification(str(reservation_passcode.id))
            except Exception as notify_error:
                logger.warning(f"Failed to send manual passcode notification: {str(notify_error)}")

            return {
                'success': True,
                'valid_from': valid_from.isoformat(),
                'valid_until': valid_until.isoformat(),
                'reservation_passcode_id': str(reservation_passcode.id),
                'requires_manual_entry': True
            }

        except Exception as e:
            logger.error(f"Failed to create manual passcode entry: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def generate_reservation_passcode(self, reservation_id: str) -> Dict:
        """
        Main method to generate passcode for a reservation based on property configuration
        """
        try:
            reservation = Reservation.query.get(reservation_id)
            if not reservation:
                return {'success': False, 'error': 'Reservation not found'}

            # Check if passcode already exists
            existing_passcode = ReservationPasscode.query.filter_by(
                reservation_id=reservation_id
            ).first()

            if existing_passcode:
                return {
                    'success': False,
                    'error': 'Passcode already exists for this reservation',
                    'existing_passcode_id': str(existing_passcode.id)
                }

            # Get property smart lock configuration
            lock_config = self.get_property_smart_lock_config(reservation.property_id)

            if lock_config['type'] == 'ttlock':
                # Generate TTLock passcode
                smart_locks = [SmartLock(**lock_data) for lock_data in lock_config['locks']]
                smart_lock_objects = SmartLock.query.filter_by(
                    property_id=reservation.property_id,
                    status='active'
                ).all()

                if not smart_lock_objects:
                    return {
                        'success': False,
                        'error': 'No active TTLock smart locks found for this property'
                    }

                return self.generate_ttlock_passcode(reservation, smart_lock_objects)

            elif lock_config['type'] == 'manual':
                # Create manual passcode entry
                return self.create_manual_passcode_entry(reservation)

            else:  # 'traditional'
                # Traditional access - no passcode needed
                return {
                    'success': True,
                    'message': 'Traditional access - no passcode required',
                    'access_method': 'traditional'
                }

        except Exception as e:
            logger.error(f"Failed to generate reservation passcode: {str(e)}")
            return {'success': False, 'error': str(e)}

    def update_manual_passcode(self, reservation_passcode_id: str, passcode: str) -> Dict:
        """
        Update manual passcode entry with host-provided passcode
        """
        try:
            reservation_passcode = ReservationPasscode.query.get(reservation_passcode_id)
            if not reservation_passcode:
                return {'success': False, 'error': 'Reservation passcode not found'}

            if reservation_passcode.generation_method != 'manual':
                return {'success': False, 'error': 'Not a manual passcode entry'}

            reservation_passcode.passcode = passcode
            reservation_passcode.status = 'active'
            reservation_passcode.updated_at = datetime.now(timezone.utc)

            db.session.commit()

            logger.info(f"Updated manual passcode for reservation {reservation_passcode.reservation_id}")

            return {
                'success': True,
                'message': 'Manual passcode updated successfully',
                'passcode': passcode
            }

        except Exception as e:
            logger.error(f"Failed to update manual passcode: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def get_reservation_passcode(self, reservation_id: str) -> Optional[Dict]:
        """
        Get passcode information for a reservation
        """
        try:
            reservation_passcode = ReservationPasscode.query.filter_by(
                reservation_id=reservation_id
            ).first()

            if not reservation_passcode:
                return None

            return reservation_passcode.to_dict()

        except Exception as e:
            logger.error(f"Failed to get reservation passcode: {str(e)}")
            return None

    def revoke_reservation_passcode(self, reservation_id: str) -> Dict:
        """
        Revoke/delete passcode for a reservation
        """
        try:
            reservation_passcode = ReservationPasscode.query.filter_by(
                reservation_id=reservation_id
            ).first()

            if not reservation_passcode:
                return {'success': False, 'error': 'No passcode found for this reservation'}

            # If it's a TTLock passcode, delete from TTLock API
            if reservation_passcode.generation_method == 'ttlock' and reservation_passcode.ttlock_access_codes:
                lock_passcodes = reservation_passcode.ttlock_access_codes.get('lock_passcodes', [])

                # Get property owner for TTLock authentication
                property_obj = Property.query.get(reservation_passcode.property_id)
                if property_obj:
                    user = get_user_by_id(property_obj.user_id)
                    if user:
                        self.ttlock_service.set_user_context(user)

                        # Delete passcodes from TTLock API
                        for lock_data in lock_passcodes:
                            if lock_data.get('ttlock_password_id'):
                                smart_lock = SmartLock.query.get(lock_data['lock_id'])
                                if smart_lock:
                                    self.ttlock_service.delete_passcode(
                                        smart_lock.ttlock_id,
                                        lock_data['ttlock_password_id']
                                    )

            # Update status to revoked
            reservation_passcode.status = 'revoked'
            reservation_passcode.updated_at = datetime.now(timezone.utc)

            db.session.commit()

            logger.info(f"Revoked passcode for reservation {reservation_id}")

            return {'success': True, 'message': 'Passcode revoked successfully'}

        except Exception as e:
            logger.error(f"Failed to revoke reservation passcode: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def get_pending_manual_passcodes(self, user_id: str) -> List[Dict]:
        """
        Get all pending manual passcode entries for a user's properties
        """
        try:
            # Get user's properties
            properties = Property.query.filter_by(user_id=user_id).all()
            property_ids = [str(prop.id) for prop in properties]

            # Get pending manual passcodes
            pending_passcodes = ReservationPasscode.query.filter(
                ReservationPasscode.property_id.in_(property_ids),
                ReservationPasscode.generation_method == 'manual',
                ReservationPasscode.status == 'pending'
            ).all()

            result = []
            for passcode_entry in pending_passcodes:
                reservation = Reservation.query.get(passcode_entry.reservation_id)
                property_obj = Property.query.get(passcode_entry.property_id)

                if reservation and property_obj:
                    result.append({
                        'id': str(passcode_entry.id),
                        'reservation_id': str(reservation.id),
                        'property_name': property_obj.name,
                        'guest_name': f"{reservation.first_name} {reservation.last_name}",
                        'check_in': passcode_entry.valid_from.isoformat(),
                        'check_out': passcode_entry.valid_until.isoformat(),
                        'created_at': passcode_entry.created_at.isoformat()
                    })

            return result

        except Exception as e:
            logger.error(f"Failed to get pending manual passcodes: {str(e)}")
            return []

# Global service instance
passcode_service = PasscodeService()