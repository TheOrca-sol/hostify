import os
import sys
from datetime import datetime, timezone
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
                print(f"  -> Sending message {message.id} for guest {message.guest_id}...")
                
                # Populate template variables
                content = message.template.content
                content = content.replace('{{guest_name}}', message.guest.full_name or 'Guest')
                content = content.replace('{{property_name}}', message.reservation.property.name)
                content = content.replace('{{check_in_date}}', message.reservation.check_in.strftime('%Y-%m-%d'))
                content = content.replace('{{check_out_date}}', message.reservation.check_out.strftime('%Y-%m-%d'))
                
                # Send via SMS
                if 'sms' in message.channels and message.guest.phone:
                    result = send_sms(message.guest.phone, content)
                    if result['success']:
                        message.status = 'sent'
                        message.sent_at = datetime.now(timezone.utc)
                        print(f"    -> Successfully sent SMS to {message.guest.phone}")
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
