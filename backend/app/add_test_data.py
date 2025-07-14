import os
import sys
from datetime import datetime, timedelta
from uuid import uuid4

sys.path.append(os.path.dirname(__file__))
from models import db, User, Property, Reservation, Guest, Message, ScheduledMessage, MessageTemplate
from flask import Flask
from sqlalchemy.exc import IntegrityError

# --- Flask app setup (for standalone script) ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.ikzbswfeotcocyrhkjrq:Nabster96@aws-0-eu-west-3.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)

with app.app_context():
    db.create_all()

    # 1. Create or get test user
    firebase_uid = '74sDO6gtuohrmjOVjKMcyO5mmH53'  # Real Firebase UID from frontend
    user = User.query.filter_by(firebase_uid=firebase_uid).first()
    if not user:
        user = User(
            firebase_uid=firebase_uid,
            email='testuser@example.com',
            name='Test User',
            phone='0612345678',
            company_name='Test Company',
            settings={}
        )
        db.session.add(user)
        db.session.commit()
        print(f"Created User: {user.id}")
    else:
        print(f"User already exists: {user.id}")

    # 2. Create or get test property
    property_name = 'Test Property'
    prop = Property.query.filter_by(user_id=user.id, name=property_name).first()
    if not prop:
        prop = Property(
            user_id=user.id,
            name=property_name,
            address='123 Test St, Casablanca',
            ical_url='https://example.com/test.ics',
            sync_frequency=3,
            auto_verification=True,
            auto_contract=True,
            settings={}
        )
        db.session.add(prop)
        db.session.commit()
        print(f"Created Property: {prop.id}")
    else:
        print(f"Property already exists: {prop.id}")

    # 3. Create or get test reservation
    check_in = datetime.now() + timedelta(days=1)
    check_out = check_in + timedelta(days=3)
    reservation = Reservation.query.filter_by(property_id=prop.id, check_in=check_in.date()).first()
    if not reservation:
        reservation = Reservation(
            property_id=prop.id,
            external_id=str(uuid4()),
            platform='airbnb',
            guest_name_partial='Ahmed K.',
            phone_partial='06*****78',
            reservation_url='https://airbnb.com/reservation/123',
            check_in=check_in,
            check_out=check_out,
            status='confirmed',
            sync_source='manual',
            raw_data={}
        )
        db.session.add(reservation)
        db.session.commit()
        print(f"Created Reservation: {reservation.id}")
    else:
        print(f"Reservation already exists: {reservation.id}")

    # 4. Create or get test guest
    guest = Guest.query.filter_by(reservation_id=reservation.id, full_name='ayman nciri').first()
    if not guest:
        guest = Guest(
            reservation_id=reservation.id,
            verification_token=str(uuid4()),
            full_name='ayman nciri',
            cin_or_passport='AB123456',
            birthdate=datetime(1990, 5, 20),
            nationality='Moroccan',
            address='456 Guest Ave, Rabat',
            phone='+212694461807',
            email='ayman.nciri@example.com',
            document_type='passport',
            id_document_path='/uploads/ids/ayman_nciri_passport.pdf',
            verification_status='pending',
            verified_at=None,
        )
        db.session.add(guest)
        db.session.commit()
        print(f"Created Guest: {guest.id}")
    else:
        print(f"Guest already exists: {guest.id}")

    # 5. Create or get test message template
    template = MessageTemplate.query.filter_by(user_id=user.id, name='Test Template').first()
    if not template:
        template = MessageTemplate(
            user_id=user.id,
            name='Test Template',
            type='checkin',
            subject='Your upcoming stay at {{property.name}}',
            content='Hello {{guest.full_name}},\n\nThis is a reminder about your check-in on {{reservation.check_in}}.\n\nThanks,\n{{user.name}}',
            channels=['email', 'sms']
        )
        db.session.add(template)
        db.session.commit()
        print(f"Created Message Template: {template.id}")
    else:
        print(f"Message Template already exists: {template.id}")

    # 6. Create or get test scheduled message
    message = ScheduledMessage.query.filter_by(reservation_id=reservation.id, guest_id=guest.id).first()
    if not message:
        message = ScheduledMessage(
            template_id=template.id,
            reservation_id=reservation.id,
            guest_id=guest.id,
            status='scheduled',
            scheduled_for=datetime.now() + timedelta(hours=1),
            channels=['email']
        )
        db.session.add(message)
        db.session.commit()
        print(f"Created Scheduled Message: {message.id}")
    else:
        print(f"Scheduled Message already exists: {message.id}")

    print("Test data setup complete.") 