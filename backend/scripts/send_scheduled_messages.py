import os
import sys
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import time

# Load environment variables first
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import ScheduledMessage
from app.utils.sms import send_sms

def send_due_messages():
    """
    Finds and sends all scheduled messages that are due.
    """
    app = create_app()
    with app.app_context():
        print(f"[{datetime.now()}] Checking for due messages...")
        
        try:
            now = datetime.now(timezone.utc)
            due_messages = ScheduledMessage.query.filter(
                ScheduledMessage.status == 'scheduled',
                ScheduledMessage.scheduled_for <= now
            ).all()

            if not due_messages:
                print("No messages are due to be sent.")
                return

            print(f"Found {len(due_messages)} messages to send.")
            
            for message in due_messages:
                recipient_info = f"guest {message.guest_id}" if message.guest_id else f"{message.template.type} team"
                print(f"  -> Sending message {message.id} for {recipient_info}...")
                
                # Populate template variables
                content = message.template.content
                
                # Get related data
                guest = message.guest
                reservation = message.reservation
                property = reservation.property if reservation else None
                
                # Build variables dict
                variables = {
                    'guest_name': guest.full_name if guest else 'Guest',
                    'property_name': property.name if property else 'Property',
                    'check_in_date': reservation.check_in.strftime('%B %d, %Y') if reservation and reservation.check_in else '',
                    'check_out_date': reservation.check_out.strftime('%B %d, %Y') if reservation and reservation.check_out else '',
                    'check_in_time': reservation.check_in.strftime('%I:%M %p') if reservation and reservation.check_in else '',
                    'check_out_time': reservation.check_out.strftime('%I:%M %p') if reservation and reservation.check_out else '',
                    'property_address': property.address if property else '',
                    'host_name': property.owner.name if property and property.owner else 'Host',
                    'host_phone': property.owner.phone if property and property.owner else '',
                    'verification_link': f"https://hostify.app/verify/{guest.verification_token}" if guest and guest.verification_token else '',
                    'verification_expiry': (datetime.now(timezone.utc) + timedelta(days=7)).strftime('%B %d, %Y at %H:%M UTC') if guest else '',
                    'contract_link': f"https://hostify.app/contract/sign/{guest.verification_token}" if guest and guest.verification_token else '',
                    'contract_expiry': (datetime.now(timezone.utc) + timedelta(days=7)).strftime('%B %d, %Y at %H:%M UTC') if guest else ''
                }
                
                # Replace variables in content (handle both single and double braces)
                for key, value in variables.items():
                    content = content.replace('{' + key + '}', str(value))
                    content = content.replace('{{' + key + '}}', str(value))
                
                # Determine recipients based on message type
                if message.template.type in ['cleaner', 'maintenance']:
                    # Send to team members with appropriate role
                    from app.models import PropertyTeamMember
                    
                    target_role = message.template.type  # 'cleaner' or 'maintenance'
                    team_members = PropertyTeamMember.query.filter(
                        PropertyTeamMember.property_id == property.id,
                        PropertyTeamMember.role == target_role,
                        PropertyTeamMember.is_active == True
                    ).all()
                    
                    if team_members and 'sms' in message.channels:
                        sent_count = 0
                        for team_member in team_members:
                            if team_member.user and team_member.user.phone:
                                result = send_sms(team_member.user.phone, content)
                                if result['success']:
                                    sent_count += 1
                                    print(f"    -> Successfully sent SMS to {target_role} {team_member.user.name} at {team_member.user.phone}")
                                    print(f"    -> Content: {content[:100]}...")
                                else:
                                    print(f"    -> Failed to send SMS to {team_member.user.name}: {result['error']}")
                        
                        if sent_count > 0:
                            message.status = 'sent'
                            message.sent_at = datetime.now(timezone.utc)
                        else:
                            message.status = 'failed'
                            print(f"    -> Failed: No {target_role} team members with phone numbers found.")
                    else:
                        message.status = 'failed'
                        print(f"    -> Failed: No {target_role} team members found for property.")
                else:
                    # Send to guest (for regular guest messages)
                    if 'sms' in message.channels and message.guest and message.guest.phone:
                        result = send_sms(message.guest.phone, content)
                        if result['success']:
                            message.status = 'sent'
                            message.sent_at = datetime.now(timezone.utc)
                            print(f"    -> Successfully sent SMS to guest {message.guest.phone}")
                            print(f"    -> Content: {content[:100]}...")
                        else:
                            message.status = 'failed'
                            print(f"    -> Failed to send SMS: {result['error']}")
                    else:
                        message.status = 'failed'
                        print("    -> Failed: No SMS channel or guest phone number.")

            db.session.commit()
            print("Finished sending messages.")

        except Exception as e:
            db.session.rollback()
            print(f"An error occurred: {e}")

def run_worker(interval_seconds=60):
    """
    Runs the message sender worker indefinitely.
    """
    print("Starting the message sending worker...")
    while True:
        send_due_messages()
        print(f"Worker sleeping for {interval_seconds} seconds...")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_worker()
