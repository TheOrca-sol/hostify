"""
Message handling utilities for Hostify
"""

import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from ..models import MessageTemplate, ScheduledMessage, Message, MessageLog, db
from sqlalchemy import and_

class MessageService:
    """Service for sending and managing messages"""
    
    def __init__(self):
        """Initialize message service with Twilio and SendGrid clients"""
        self.twilio_client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
    
    def send_scheduled_message_sync(self, scheduled_message: ScheduledMessage) -> bool:
        """Send a scheduled message immediately"""
        try:
            # Get message content
            template = scheduled_message.template
            if not template:
                return False
                
            # Create message record
            message = Message(
                reservation_id=scheduled_message.reservation_id,
                guest_id=scheduled_message.guest_id,
                message_type=template.type,
                template_id=str(template.id),
                content=self._populate_variables(template.content, scheduled_message),
                channel='sms'
            )
            
            db.session.add(message)
            scheduled_message.status = 'sent'
            scheduled_message.sent_at = datetime.now(timezone.utc)
            db.session.commit()
            
            return True
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            return False
            
    def _populate_variables(self, content, scheduled_message):
        """Replace template variables with actual values"""
        # Get related data
        reservation = scheduled_message.reservation
        guest = scheduled_message.guest
        property = reservation.property if reservation else None
        
        # Build variables dict
        variables = {
            'guest_name': guest.full_name if guest else '',
            'property_name': property.name if property else '',
            'check_in_date': reservation.check_in.strftime('%B %d, %Y') if reservation and reservation.check_in else '',
            'check_out_date': reservation.check_out.strftime('%B %d, %Y') if reservation and reservation.check_out else '',
            'check_in_time': reservation.check_in.strftime('%I:%M %p') if reservation and reservation.check_in else '',
            'check_out_time': reservation.check_out.strftime('%I:%M %p') if reservation and reservation.check_out else '',
            'property_address': property.address if property else '',
            'host_name': property.owner.name if property and property.owner else '',
            'host_phone': property.owner.phone if property and property.owner else '',
            'verification_link': f"https://hostify.app/verify/{guest.verification_token}" if guest and guest.verification_token else '',
            'verification_expiry': (datetime.now(timezone.utc) + timedelta(days=7)).strftime('%B %d, %Y at %H:%M UTC') if guest else '',
            'contract_link': f"https://hostify.app/contract/sign/{guest.verification_token}" if guest and guest.verification_token else '',
            'contract_expiry': (datetime.now(timezone.utc) + timedelta(days=7)).strftime('%B %d, %Y at %H:%M UTC') if guest else ''
        }
        
        # Add smart lock variables
        try:
            from ..services.message_template_service import message_template_service
            if reservation:
                smart_lock_vars = message_template_service.get_smart_lock_variables(str(reservation.id))
                variables.update(smart_lock_vars)
        except Exception as e:
            print(f"Warning: Failed to load smart lock variables: {str(e)}")

        # Replace variables in content
        for key, value in variables.items():
            content = content.replace('{' + key + '}', str(value))

        return content
    
    def _send_sms_sync(self, to_phone: str, content: str) -> str:
        """Send SMS using Twilio (synchronous version)"""
        message = self.twilio_client.messages.create(
            body=content,
            from_=self.twilio_phone,
            to=to_phone
        )
        return message.sid
    
    def _log_delivery(
        self,
        scheduled_message_id: str,
        channel: str,
        status: str,
        provider_message_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Log message delivery attempt"""
        log = MessageLog(
            scheduled_message_id=scheduled_message_id,
            channel=channel,
            status=status,
            provider_message_id=provider_message_id,
            error_message=error_message,
            sent_at=datetime.now(timezone.utc) if status != 'failed' else None
        )
        db.session.add(log)
        db.session.commit()

def create_default_verification_templates(user_id):
    """Create default verification message templates for a new user"""
    templates = [
        {
            'name': 'Guest Verification Request',
            'type': 'verification_request',
            'content': """Dear {guest_name},

We hope you're excited about your upcoming stay at {property_name}! To ensure a smooth check-in process, we need to verify your identity as per local regulations.

Please click the link below to complete your verification:
{verification_link}

This link will expire on {verification_expiry}.

The verification process is quick and secure:
1. Upload a photo of your ID (passport or national ID)
2. Confirm your personal details
3. Review and sign the rental contract

If you have any questions, please don't hesitate to contact us:
Host: {host_name}
Phone: {host_phone}

Best regards,
The {property_name} Team""",
            'channels': ['sms'],
            'language': 'en'
        },
        {
            'name': 'Verification Reminder',
            'type': 'verification_reminder',
            'content': """Dear {guest_name},

This is a friendly reminder to complete your identity verification for your upcoming stay at {property_name}.

Your verification link:
{verification_link}

This link will expire on {verification_expiry}. Please complete the verification as soon as possible to ensure a smooth check-in.

Need help? Contact us:
Host: {host_name}
Phone: {host_phone}

Best regards,
The {property_name} Team""",
            'channels': ['sms'],
            'language': 'en'
        },
        {
            'name': 'Verification Complete',
            'type': 'verification_complete',
            'content': """Dear {guest_name},

Thank you for completing your identity verification for {property_name}. Your rental contract is now being prepared and will be sent to you shortly for digital signature.

Your stay details:
Check-in: {check_in_date}
Check-out: {check_out_date}
Property: {property_address}

We'll send you the contract signing link soon. If you have any questions in the meantime, please contact:
Host: {host_name}
Phone: {host_phone}

Best regards,
The {property_name} Team""",
            'channels': ['sms'],
            'language': 'en'
        },
        {
            'name': 'Contract Ready for Signing',
            'type': 'contract_ready',
            'content': """Dear {guest_name},

Your rental contract for {property_name} is ready for your signature. Please review and sign the contract using the link below:

{contract_link}

The contract signing link will expire on {contract_expiry}. Please complete this step as soon as possible.

Stay Details:
Check-in: {check_in_date}
Check-out: {check_out_date}
Property: {property_address}

If you have any questions about the contract, please contact:
Host: {host_name}
Phone: {host_phone}

Best regards,
The {property_name} Team""",
            'channels': ['sms'],
            'language': 'en'
        },
        {
            'name': 'Contract Signing Reminder',
            'type': 'contract_reminder',
            'content': """Dear {guest_name},

This is a reminder to sign your rental contract for {property_name}. Please complete this step to finalize your booking.

Sign your contract here:
{contract_link}

This link will expire on {contract_expiry}.

Need help? Contact us:
Host: {host_name}
Phone: {host_phone}

Best regards,
The {property_name} Team""",
            'channels': ['sms'],
            'language': 'en'
        },
        {
            'name': 'Contract Signed Confirmation',
            'type': 'contract_signed',
            'content': """Dear {guest_name},

Thank you for signing the rental contract for {property_name}. Your booking is now complete!

Stay Details:
Check-in: {check_in_date}
Check-out: {check_out_date}
Property: {property_address}

We'll send you check-in instructions closer to your arrival date. If you need anything in the meantime, please contact:
Host: {host_name}
Phone: {host_phone}

We look forward to welcoming you!

Best regards,
The {property_name} Team""",
            'channels': ['sms'],
            'language': 'en'
        }
    ]
    
    # Create templates
    created_templates = []
    for template_data in templates:
        template = MessageTemplate(
            user_id=user_id,
            property_id=None,  # Default templates are available for all properties
            name=template_data['name'],
            type=template_data['type'],
            content=template_data['content'],
            language=template_data['language'],
            channels=template_data['channels'],
            variables={},
            active=True
        )
        db.session.add(template)
        created_templates.append(template)
    
    try:
        db.session.commit()
        return created_templates
    except Exception as e:
        print(f"Error creating default templates: {str(e)}")
        db.session.rollback()
        return []

class MessageScheduler:
    """Service for scheduling automated messages"""
    
    @staticmethod
    def schedule_verification_messages(guest_id):
        """Schedule verification-related messages for a guest"""
        try:
            from ..models import Guest, MessageTemplate
            
            guest = Guest.query.get(guest_id)
            if not guest or not guest.reservation or not guest.reservation.property:
                return []
                
            property = guest.reservation.property
            user_id = property.user_id
            
            # Find verification templates
            templates = MessageTemplate.query.filter(
                and_(
                    MessageTemplate.user_id == user_id,
                    MessageTemplate.template_type.in_([
                        'verification_request',
                        'verification_reminder',
                        'verification_complete',
                        'contract_ready',
                        'contract_reminder',
                        'contract_signed'
                    ]),
                    or_(
                        MessageTemplate.property_id == property.id,
                        MessageTemplate.property_id.is_(None)
                    )
                )
            ).all()
            
            # Schedule messages
            now = datetime.utcnow()
            scheduled_messages = []
            
            for template in templates:
                # Set scheduling delays based on message type
                delay = {
                    'verification_request': timedelta(minutes=0),  # Immediate
                    'verification_reminder': timedelta(days=2),  # After 2 days if not verified
                    'verification_complete': timedelta(minutes=0),  # Immediate after verification
                    'contract_ready': timedelta(minutes=5),  # 5 minutes after verification
                    'contract_reminder': timedelta(days=2),  # 2 days after contract ready
                    'contract_signed': timedelta(minutes=0)  # Immediate after signing
                }.get(template.template_type)
                
                if delay is not None:
                    scheduled_message = ScheduledMessage(
                        template_id=template.id,
                        reservation_id=guest.reservation_id,
                        guest_id=guest.id,
                        scheduled_for=now + delay,
                        channels=template.channels
                    )
                    db.session.add(scheduled_message)
                    scheduled_messages.append(scheduled_message)
            
            db.session.commit()
            return [msg.id for msg in scheduled_messages]
            
        except Exception as e:
            print(f"Error scheduling verification messages: {str(e)}")
            db.session.rollback()
            return []
    
    @staticmethod
    def schedule_reservation_messages_sync(reservation_id):
        """Schedule all relevant messages for a reservation"""
        try:
            from ..models import Reservation, MessageTemplate
            
            reservation = Reservation.query.get(reservation_id)
            if not reservation or not reservation.property:
                return []
                
            property = reservation.property
            user_id = property.user_id
            
            # Find all applicable templates
            templates = MessageTemplate.query.filter(
                and_(
                    MessageTemplate.user_id == user_id,
                    MessageTemplate.template_type.in_([
                        'welcome',
                        'checkin',
                        'during_stay',
                        'checkout',
                        'review_request',
                        'cleaner',
                        'maintenance'
                    ]),
                    or_(
                        MessageTemplate.property_id == property.id,
                        MessageTemplate.property_id.is_(None)
                    )
                )
            ).all()
            
            # Schedule messages
            now = datetime.utcnow()
            check_in = reservation.check_in
            check_out = reservation.check_out
            
            scheduled_messages = []
            
            for template in templates:
                # Set scheduling based on message type
                schedule_time = {
                    'welcome': now,  # Immediate
                    'checkin': check_in - timedelta(days=1),  # Day before check-in
                    'during_stay': check_in + timedelta(days=1),  # Day after check-in
                    'checkout': check_out - timedelta(days=1),  # Day before check-out
                    'review_request': check_out + timedelta(days=1),  # Day after check-out
                    'cleaner': check_out,  # At check-out time
                    'maintenance': check_out  # At check-out time (or could be different timing)
                }.get(template.template_type)
                
                if schedule_time and schedule_time > now:
                    # Create scheduled message
                    # For cleaner/maintenance messages, don't assign guest_id
                    guest_id = None
                    if template.template_type not in ['cleaner', 'maintenance']:
                        guest_id = reservation.guests[0].id if reservation.guests else None
                    
                    scheduled_message = ScheduledMessage(
                        template_id=template.id,
                        reservation_id=reservation.id,
                        guest_id=guest_id,
                        scheduled_for=schedule_time,
                        channels=template.channels
                    )
                    db.session.add(scheduled_message)
                    scheduled_messages.append(scheduled_message)
            
            db.session.commit()
            return [msg.id for msg in scheduled_messages]
            
        except Exception as e:
            print(f"Error scheduling reservation messages: {str(e)}")
            db.session.rollback()
            return [] 