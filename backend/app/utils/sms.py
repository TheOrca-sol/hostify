import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

def send_sms(to_phone_number, message_body):
    """
    Sends an SMS message using Twilio, validating E.164 format.
    """
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        print("Error: Twilio environment variables are not fully configured.")
        return {'success': False, 'error': 'Twilio is not configured.'}

    if not to_phone_number or not to_phone_number.startswith('+'):
        error_msg = "Invalid phone number format. Number must be in E.164 format (e.g., +14155552671)."
        print(f"Error sending SMS: {error_msg}")
        return {'success': False, 'error': error_msg}

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        
        print(f"SMS sent successfully to {to_phone_number}. SID: {message.sid}")
        return {'success': True, 'sid': message.sid}

    except Exception as e:
        print(f"Error sending SMS to {to_phone_number}: {e}")
        return {'success': False, 'error': str(e)}