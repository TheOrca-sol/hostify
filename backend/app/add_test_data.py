import os
import sys
from datetime import datetime, timedelta
from uuid import uuid4

sys.path.append(os.path.dirname(__file__))
from models import db, User, Property, Reservation, Guest, Message
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
            name='hamza User',
            phone='+212663250280',
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
    guest = Guest.query.filter_by(reservation_id=reservation.id, full_name='Ahmed Khalil').first()
    if not guest:
        guest = Guest(
            reservation_id=reservation.id,
            verification_token=str(uuid4()),
            full_name='Ahmed Khalil',
            cin_or_passport='AB123456',
            birthdate=datetime(1990, 5, 20),
            nationality='Moroccan',
            address='456 Guest Ave, Rabat',
            phone='0612345678',
            email='ahmed.khalil@example.com',
            document_type='passport',
            id_document_path='/uploads/ids/ahmed_khalil_passport.pdf',
            verification_status='verified',
            verified_at=datetime.now(),
        )
        db.session.add(guest)
        db.session.commit()
        print(f"Created Guest: {guest.id}")
    else:
        print(f"Guest already exists: {guest.id}")

    # 5. Create or get test message
    message = Message.query.filter_by(reservation_id=reservation.id, guest_id=guest.id).first()
    if not message:
        message = Message(
            reservation_id=reservation.id,
            guest_id=guest.id,
            message_type='welcome',
            template_id=None,
            content='Welcome to our property, Ahmed! Your check-in is tomorrow.',
            channel='email',
            delivery_status='sent'
        )
        db.session.add(message)
        db.session.commit()
        print(f"Created Message: {message.id}")
    else:
        print(f"Message already exists: {message.id}")

    print("Test data setup complete.") 