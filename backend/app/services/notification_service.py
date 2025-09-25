"""
Notification service for smart lock integration
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from ..models import User, Property, Reservation, ReservationPasscode, db
from ..utils.sms import send_sms

# Configure logging
logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications related to smart locks"""

    def __init__(self):
        pass

    def format_phone_number(self, phone: str) -> Optional[str]:
        """Format phone number to E.164 format"""
        if not phone:
            return None

        # Remove any non-digit characters except +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')

        # If it already starts with +, return as is
        if cleaned.startswith('+'):
            return cleaned

        # If it starts with country code (e.g., 212 for Morocco)
        if len(cleaned) >= 10:
            # Assume it needs + prefix
            return f'+{cleaned}'

        return None

    def send_manual_passcode_notification(self, reservation_passcode_id: str) -> Dict:
        """
        Send SMS notification to host requesting manual passcode entry
        """
        try:
            reservation_passcode = ReservationPasscode.query.get(reservation_passcode_id)
            if not reservation_passcode:
                return {'success': False, 'error': 'Reservation passcode not found'}

            reservation = Reservation.query.get(reservation_passcode.reservation_id)
            if not reservation:
                return {'success': False, 'error': 'Reservation not found'}

            property_obj = Property.query.get(reservation_passcode.property_id)
            if not property_obj:
                return {'success': False, 'error': 'Property not found'}

            user = User.query.get(property_obj.user_id)
            if not user:
                return {'success': False, 'error': 'Property owner not found'}

            # Format phone number
            phone_number = self.format_phone_number(user.phone)
            if not phone_number:
                return {'success': False, 'error': 'Valid phone number not found for host'}

            # Format check-in date/time
            check_in_str = reservation.check_in.strftime('%b %d at %I:%M %p') if reservation.check_in else 'TBD'

            # Create SMS message
            guest_name = f"{reservation.first_name} {reservation.last_name}".strip()
            message = f"""🏠 Hostify - Manual Smart Lock Passcode Required

Property: {property_obj.name}
Guest: {guest_name}
Check-in: {check_in_str}

Please set your smart lock passcode and update it in Hostify app:
1. Go to Reservations → {guest_name}
2. Click "Set Passcode"
3. Enter the code you configured

Passcode valid from 1hr before to 1hr after checkout.

Need help? Reply to this message."""

            # Send SMS
            sms_result = send_sms(phone_number, message)

            if sms_result.get('success'):
                # Update notification timestamp
                reservation_passcode.host_notified_at = datetime.now(timezone.utc)
                db.session.commit()

                logger.info(f"Sent manual passcode notification for reservation {reservation.id} to {phone_number}")

                return {
                    'success': True,
                    'message': 'Manual passcode notification sent successfully',
                    'sms_sid': sms_result.get('sid')
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to send SMS: {sms_result.get('error')}"
                }

        except Exception as e:
            logger.error(f"Failed to send manual passcode notification: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def send_ttlock_failure_notification(self, reservation_id: str, error_message: str) -> Dict:
        """
        Send SMS notification to host when TTLock passcode generation fails
        """
        try:
            reservation = Reservation.query.get(reservation_id)
            if not reservation:
                return {'success': False, 'error': 'Reservation not found'}

            property_obj = Property.query.get(reservation.property_id)
            if not property_obj:
                return {'success': False, 'error': 'Property not found'}

            user = User.query.get(property_obj.user_id)
            if not user:
                return {'success': False, 'error': 'Property owner not found'}

            # Format phone number
            phone_number = self.format_phone_number(user.phone)
            if not phone_number:
                return {'success': False, 'error': 'Valid phone number not found for host'}

            # Format check-in date/time
            check_in_str = reservation.check_in.strftime('%b %d at %I:%M %p') if reservation.check_in else 'TBD'

            # Create SMS message
            guest_name = f"{reservation.first_name} {reservation.last_name}".strip()
            message = f"""🔴 Hostify - Smart Lock Issue

Property: {property_obj.name}
Guest: {guest_name}
Check-in: {check_in_str}

⚠️ Failed to generate automatic smart lock passcode.

Error: {error_message[:100]}...

Please:
1. Check your TTLock connection in Hostify
2. Or manually set a passcode
3. Contact guest with access details

Need help? Reply to this message."""

            # Send SMS
            sms_result = send_sms(phone_number, message)

            if sms_result.get('success'):
                logger.info(f"Sent TTLock failure notification for reservation {reservation_id} to {phone_number}")

                return {
                    'success': True,
                    'message': 'TTLock failure notification sent successfully',
                    'sms_sid': sms_result.get('sid')
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to send SMS: {sms_result.get('error')}"
                }

        except Exception as e:
            logger.error(f"Failed to send TTLock failure notification: {str(e)}")
            return {'success': False, 'error': str(e)}

    def send_passcode_ready_notification(self, reservation_passcode_id: str) -> Dict:
        """
        Send SMS notification to host when TTLock passcode is successfully generated
        """
        try:
            reservation_passcode = ReservationPasscode.query.get(reservation_passcode_id)
            if not reservation_passcode:
                return {'success': False, 'error': 'Reservation passcode not found'}

            reservation = Reservation.query.get(reservation_passcode.reservation_id)
            if not reservation:
                return {'success': False, 'error': 'Reservation not found'}

            property_obj = Property.query.get(reservation_passcode.property_id)
            if not property_obj:
                return {'success': False, 'error': 'Property not found'}

            user = User.query.get(property_obj.user_id)
            if not user:
                return {'success': False, 'error': 'Property owner not found'}

            # Format phone number
            phone_number = self.format_phone_number(user.phone)
            if not phone_number:
                return {'success': False, 'error': 'Valid phone number not found for host'}

            # Format dates
            check_in_str = reservation.check_in.strftime('%b %d at %I:%M %p') if reservation.check_in else 'TBD'
            valid_until_str = reservation_passcode.valid_until.strftime('%b %d at %I:%M %p') if reservation_passcode.valid_until else 'TBD'

            # Create SMS message
            guest_name = f"{reservation.first_name} {reservation.last_name}".strip()
            message = f"""✅ Hostify - Smart Lock Passcode Ready

Property: {property_obj.name}
Guest: {guest_name}
Check-in: {check_in_str}

🔒 Passcode: {reservation_passcode.passcode}
Valid until: {valid_until_str}

The passcode has been automatically set on your smart locks. Guest will receive access details in their check-in message.

View in app: Hostify → Reservations → {guest_name}"""

            # Send SMS
            sms_result = send_sms(phone_number, message)

            if sms_result.get('success'):
                # Update notification timestamp
                reservation_passcode.host_notified_at = datetime.now(timezone.utc)
                db.session.commit()

                logger.info(f"Sent passcode ready notification for reservation {reservation.id} to {phone_number}")

                return {
                    'success': True,
                    'message': 'Passcode ready notification sent successfully',
                    'sms_sid': sms_result.get('sid')
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to send SMS: {sms_result.get('error')}"
                }

        except Exception as e:
            logger.error(f"Failed to send passcode ready notification: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def get_notification_history(self, user_id: str, limit: int = 10) -> list:
        """
        Get notification history for a user's properties
        """
        try:
            # Get user's properties
            properties = Property.query.filter_by(user_id=user_id).all()
            property_ids = [str(prop.id) for prop in properties]

            # Get recent passcode records with notifications
            recent_passcodes = ReservationPasscode.query.filter(
                ReservationPasscode.property_id.in_(property_ids),
                ReservationPasscode.host_notified_at.isnot(None)
            ).order_by(
                ReservationPasscode.host_notified_at.desc()
            ).limit(limit).all()

            notifications = []
            for passcode_entry in recent_passcodes:
                reservation = Reservation.query.get(passcode_entry.reservation_id)
                property_obj = Property.query.get(passcode_entry.property_id)

                if reservation and property_obj:
                    notifications.append({
                        'id': str(passcode_entry.id),
                        'reservation_id': str(reservation.id),
                        'property_name': property_obj.name,
                        'guest_name': f"{reservation.first_name} {reservation.last_name}",
                        'notification_type': passcode_entry.generation_method,
                        'sent_at': passcode_entry.host_notified_at.isoformat(),
                        'passcode': passcode_entry.passcode,
                        'status': passcode_entry.status
                    })

            return notifications

        except Exception as e:
            logger.error(f"Failed to get notification history: {str(e)}")
            return []

# Global service instance
notification_service = NotificationService()