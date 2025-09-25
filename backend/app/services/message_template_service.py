"""
Enhanced message template service with smart lock integration
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from ..models import Reservation, ReservationPasscode, Property, MessageTemplate
from ..services.passcode_service import passcode_service

# Configure logging
logger = logging.getLogger(__name__)

class MessageTemplateService:
    """Enhanced message template service with smart lock support"""

    def __init__(self):
        pass

    def get_smart_lock_variables(self, reservation_id: str) -> Dict[str, str]:
        """
        Get smart lock related template variables for a reservation
        """
        try:
            reservation = Reservation.query.get(reservation_id)
            if not reservation:
                return self._get_empty_smart_lock_variables()

            property_obj = Property.query.get(reservation.property_id)
            if not property_obj:
                return self._get_empty_smart_lock_variables()

            # Get smart lock configuration
            lock_config = passcode_service.get_property_smart_lock_config(reservation.property_id)

            # Get reservation passcode if it exists
            reservation_passcode = ReservationPasscode.query.filter_by(
                reservation_id=reservation_id
            ).first()

            # Build smart lock variables based on property configuration
            variables = {}

            if lock_config['type'] == 'ttlock':
                variables.update(self._get_ttlock_variables(reservation_passcode, lock_config))
            elif lock_config['type'] == 'manual':
                variables.update(self._get_manual_lock_variables(reservation_passcode, lock_config))
            else:  # traditional
                variables.update(self._get_traditional_access_variables(lock_config))

            return variables

        except Exception as e:
            logger.error(f"Failed to get smart lock variables: {str(e)}")
            return self._get_empty_smart_lock_variables()

    def _get_empty_smart_lock_variables(self) -> Dict[str, str]:
        """Get empty smart lock variables when no smart lock is configured"""
        return {
            'smart_lock_type': 'traditional',
            'smart_lock_passcode': '',
            'smart_lock_instructions': '',
            'access_method': 'traditional',
            'lock_passcode_section': '',
            'smart_lock_details': '',
            'passcode_valid_from': '',
            'passcode_valid_until': ''
        }

    def _get_ttlock_variables(self, reservation_passcode: Optional[ReservationPasscode], lock_config: Dict) -> Dict[str, str]:
        """Get variables for TTLock smart locks"""
        variables = {
            'smart_lock_type': 'ttlock',
            'access_method': 'smart_lock'
        }

        if reservation_passcode and reservation_passcode.passcode:
            # Passcode is available
            valid_from = reservation_passcode.valid_from.strftime('%I:%M %p on %b %d') if reservation_passcode.valid_from else ''
            valid_until = reservation_passcode.valid_until.strftime('%I:%M %p on %b %d') if reservation_passcode.valid_until else ''

            variables.update({
                'smart_lock_passcode': reservation_passcode.passcode,
                'passcode_valid_from': valid_from,
                'passcode_valid_until': valid_until,
                'lock_passcode_section': f"""
🔒 SMART LOCK ACCESS
Your passcode: {reservation_passcode.passcode}
Valid from: {valid_from}
Valid until: {valid_until}

Simply enter this code on the smart lock keypad to unlock the door.""",
                'smart_lock_details': f"""Your accommodation is equipped with a smart lock for keyless entry. Use passcode {reservation_passcode.passcode} to access the property."""
            })

            # Add custom instructions if available
            if lock_config.get('instructions'):
                variables['smart_lock_instructions'] = lock_config['instructions']
                variables['smart_lock_details'] += f"\n\nAdditional instructions: {lock_config['instructions']}"
            else:
                variables['smart_lock_instructions'] = "Enter the passcode on the smart lock keypad and wait for the green light before turning the handle."

        else:
            # Passcode not yet available
            variables.update({
                'smart_lock_passcode': '[Passcode will be provided]',
                'passcode_valid_from': '',
                'passcode_valid_until': '',
                'lock_passcode_section': """
🔒 SMART LOCK ACCESS
Your smart lock passcode will be sent to you automatically 3 hours before your check-in time.""",
                'smart_lock_details': """Your accommodation features smart lock access. You'll receive your unique passcode automatically before check-in.""",
                'smart_lock_instructions': 'Smart lock passcode will be provided automatically before check-in.'
            })

        return variables

    def _get_manual_lock_variables(self, reservation_passcode: Optional[ReservationPasscode], lock_config: Dict) -> Dict[str, str]:
        """Get variables for manual smart locks"""
        variables = {
            'smart_lock_type': 'manual',
            'access_method': 'smart_lock'
        }

        if reservation_passcode and reservation_passcode.passcode:
            # Manual passcode has been set
            valid_from = reservation_passcode.valid_from.strftime('%I:%M %p on %b %d') if reservation_passcode.valid_from else ''
            valid_until = reservation_passcode.valid_until.strftime('%I:%M %p on %b %d') if reservation_passcode.valid_until else ''

            variables.update({
                'smart_lock_passcode': reservation_passcode.passcode,
                'passcode_valid_from': valid_from,
                'passcode_valid_until': valid_until,
                'lock_passcode_section': f"""
🔒 SMART LOCK ACCESS
Your passcode: {reservation_passcode.passcode}
Valid from: {valid_from}
Valid until: {valid_until}

Enter this code on the smart lock keypad to unlock the door.""",
                'smart_lock_details': f"""Your host has configured a smart lock passcode for your stay: {reservation_passcode.passcode}"""
            })
        else:
            # Manual passcode not yet set
            variables.update({
                'smart_lock_passcode': '[Passcode pending]',
                'passcode_valid_from': '',
                'passcode_valid_until': '',
                'lock_passcode_section': """
🔒 SMART LOCK ACCESS
Your host will provide the smart lock passcode shortly. Please check for updates or contact your host if needed.""",
                'smart_lock_details': """Your accommodation has smart lock access. Your host will provide the passcode details."""
            })

        # Add custom instructions
        if lock_config.get('instructions'):
            variables['smart_lock_instructions'] = lock_config['instructions']
            variables['smart_lock_details'] += f"\n\nInstructions: {lock_config['instructions']}"
        else:
            variables['smart_lock_instructions'] = "Enter the passcode on the smart lock keypad as instructed by your host."

        return variables

    def _get_traditional_access_variables(self, lock_config: Dict) -> Dict[str, str]:
        """Get variables for traditional access methods"""
        variables = {
            'smart_lock_type': 'traditional',
            'smart_lock_passcode': '',
            'access_method': 'traditional',
            'passcode_valid_from': '',
            'passcode_valid_until': '',
            'lock_passcode_section': '',
            'smart_lock_details': 'Traditional key access - your host will provide check-in instructions.'
        }

        # Add custom instructions if available
        if lock_config.get('instructions'):
            variables['smart_lock_instructions'] = lock_config['instructions']
            variables['smart_lock_details'] = lock_config['instructions']
        else:
            variables['smart_lock_instructions'] = 'Your host will provide check-in and access instructions.'

        return variables

    def populate_smart_lock_variables(self, content: str, reservation_id: str) -> str:
        """
        Populate smart lock variables in message template content
        """
        try:
            # Get smart lock variables
            smart_lock_vars = self.get_smart_lock_variables(reservation_id)

            # Replace variables in content
            for key, value in smart_lock_vars.items():
                placeholder = '{' + key + '}'
                content = content.replace(placeholder, str(value))

            return content

        except Exception as e:
            logger.error(f"Failed to populate smart lock variables: {str(e)}")
            return content

    def get_available_smart_lock_variables(self) -> Dict[str, str]:
        """
        Get list of available smart lock template variables with descriptions
        """
        return {
            'smart_lock_type': 'Type of smart lock system (ttlock, manual, traditional)',
            'smart_lock_passcode': 'The passcode for smart lock access',
            'smart_lock_instructions': 'Custom instructions for accessing the smart lock',
            'access_method': 'Method of access (smart_lock or traditional)',
            'lock_passcode_section': 'Complete formatted section with passcode details',
            'smart_lock_details': 'Detailed information about smart lock access',
            'passcode_valid_from': 'When the passcode becomes valid',
            'passcode_valid_until': 'When the passcode expires'
        }

    def create_default_smart_lock_templates(self, user_id: str, property_id: str) -> list:
        """
        Create default smart lock-enabled message templates for a property
        """
        try:
            templates_to_create = [
                {
                    'name': 'Check-in Instructions with Smart Lock',
                    'template_type': 'checkin',
                    'subject': 'Check-in Instructions - {property_name}',
                    'content': """Welcome to {property_name}!

Your check-in details:
📅 Date: {check_in_date}
🕐 Time: {check_in_time}
📍 Address: {property_address}

{lock_passcode_section}

{smart_lock_instructions}

Need help? Contact {host_name} at {host_phone}

Enjoy your stay!""",
                    'trigger_event': 'check_in',
                    'trigger_offset_value': 3,
                    'trigger_offset_unit': 'hours',
                    'trigger_direction': 'before'
                },
                {
                    'name': 'Check-out Reminder with Smart Lock',
                    'template_type': 'checkout',
                    'subject': 'Check-out Reminder - {property_name}',
                    'content': """Thank you for staying at {property_name}!

Check-out details:
📅 Date: {check_out_date}
🕐 Time: {check_out_time}

{smart_lock_details}

Please ensure:
✅ All doors are locked when leaving
✅ All lights and appliances are turned off
✅ Any keys or access cards are left as instructed

Thank you for your stay! We hope to host you again soon.

{host_name}""",
                    'trigger_event': 'check_out',
                    'trigger_offset_value': 2,
                    'trigger_offset_unit': 'hours',
                    'trigger_direction': 'before'
                }
            ]

            created_templates = []
            for template_data in templates_to_create:
                template = MessageTemplate(
                    user_id=user_id,
                    property_id=property_id,
                    **template_data,
                    language='en',
                    channels=['sms'],
                    active=True
                )

                from ..models import db
                db.session.add(template)
                created_templates.append(template)

            db.session.commit()
            logger.info(f"Created {len(created_templates)} default smart lock templates for property {property_id}")

            return [template.to_dict() for template in created_templates]

        except Exception as e:
            logger.error(f"Failed to create default smart lock templates: {str(e)}")
            from ..models import db
            db.session.rollback()
            return []

# Global service instance
message_template_service = MessageTemplateService()