import os
from twilio.rest import Client

def send_sms(to, body):
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_number = os.environ.get('TWILIO_PHONE_NUMBER')

    if not all([account_sid, auth_token, from_number]):
        print("Twilio environment variables not set")
        return False

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            to=to,
            from_=from_number,
            body=body
        )
        print(f"Message sent to {to}: {message.sid}")
        return True
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False
