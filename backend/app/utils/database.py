"""
Database utilities for Hostify Property Management Platform
Updated to support property-centric architecture with reservations and contracts
"""

from datetime import datetime, timezone
from ..models import db, User, Property, Reservation, Guest, VerificationLink, Contract, ContractTemplate, SyncLog, MessageTemplate
import uuid

# User Management
def create_user(firebase_uid, email, name, **kwargs):
    """
    Create a new user and a default verification message template.
    """
    try:
        user = User(
            firebase_uid=firebase_uid,
            email=email,
            name=name,
            phone=kwargs.get('phone'),
            company_name=kwargs.get('company_name'),
            settings=kwargs.get('settings', {})
        )
        db.session.add(user)
        db.session.flush() # Flush to get the user ID before creating the template

        # Create a default verification message template for the new user
        verification_template = MessageTemplate(
            user_id=user.id,
            name="Default Guest Verification",
            template_type="verification_request",
            subject="Verify Your Identity for Your Stay",
            content="Hello {{guest_name}}, please verify your identity for your upcoming stay: {{verification_link}}",
            language="en",
            channels=["sms"],
            variables=["guest_name", "verification_link"]
        )
        db.session.add(verification_template)
        db.session.commit()
        
        return str(user.id)
    
    except Exception as e:
        db.session.rollback()
        print(f"Database error in create_user: {str(e)}")
        return None

def get_user_by_firebase_uid(firebase_uid):
    """
    Get user by Firebase UID
    """
    try:
        user = User.query.filter_by(firebase_uid=firebase_uid).first()
        return user.to_dict() if user else None
    
    except Exception as e:
        print(f"Database error: {str(e)}")
        return None

# Property Management
def create_property(user_id, name, **kwargs):
    """
    Create a new property for a user
    """
    try:
        property = Property(
            user_id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id,
            name=name,
            address=kwargs.get('address'),
            ical_url=kwargs.get('ical_url'),
            sync_frequency=kwargs.get('sync_frequency', 3),
            contract_template_id=kwargs.get('contract_template_id'),
            auto_verification=kwargs.get('auto_verification', True),
            auto_contract=kwargs.get('auto_contract', True),
            settings=kwargs.get('settings', {})
        )
        
        db.session.add(property)
        db.session.commit()
        return str(property.id)
    
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return None

def get_user_properties(user_id):
    """
    Get all properties for a user
    """
    try:
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        properties = Property.query.filter_by(user_id=user_uuid).order_by(Property.created_at.desc()).all()
        return [property.to_dict() for property in properties]
    
    except Exception as e:
        print(f"Database error: {str(e)}")
        return []

def get_property(property_id, user_id=None):
    """
    Get a specific property, optionally filtered by user
    """
    try:
        property_uuid = uuid.UUID(property_id) if isinstance(property_id, str) else property_id
        query = Property.query.filter_by(id=property_uuid)
        
        if user_id:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            query = query.filter_by(user_id=user_uuid)
        
        property = query.first()
        return property.to_dict() if property else None
    
    except Exception as e:
        print(f"Database error: {str(e)}")
        return None

def get_property_by_ical_url(ical_url):
    """
    Get property by iCal URL to check for duplicates.
    """
    try:
        property = Property.query.filter_by(ical_url=ical_url).first()
        return property.to_dict() if property else None
    except Exception as e:
        print(f"Database error: {str(e)}")
        return None

def update_property(property_id, user_id, update_data):
    """
    Update a property
    """
    try:
        property_uuid = uuid.UUID(property_id) if isinstance(property_id, str) else property_id
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        
        property = Property.query.filter_by(id=property_uuid, user_id=user_uuid).first()
        if not property:
            return False
        
        # Update allowed fields
        allowed_fields = ['name', 'address', 'ical_url', 'sync_frequency', 'contract_template_id', 
                         'auto_verification', 'auto_contract', 'settings', 'last_sync']
        for field in allowed_fields:
            if field in update_data:
                setattr(property, field, update_data[field])
        
        db.session.commit()
        return True
    
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return False

# Reservation Management
def create_reservation(property_id, **kwargs):
    """
    Create a new reservation for a property
    """
    try:
        reservation = Reservation(
            property_id=uuid.UUID(property_id) if isinstance(property_id, str) else property_id,
            external_id=kwargs.get('external_id'),
            platform=kwargs.get('platform'),
            guest_name_partial=kwargs.get('guest_name_partial'),
            phone_partial=kwargs.get('phone_partial'),
            reservation_url=kwargs.get('reservation_url'),
            check_in=kwargs['check_in'],
            check_out=kwargs['check_out'],
            status=kwargs.get('status', 'confirmed'),
            sync_source=kwargs.get('sync_source'),
            raw_data=kwargs.get('raw_data')
        )
        
        db.session.add(reservation)
        db.session.commit()
        return str(reservation.id)
    
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return None

def get_property_reservations(property_id):
    """
    Get all reservations for a specific property
    """
    try:
        property_uuid = uuid.UUID(property_id) if isinstance(property_id, str) else property_id
        reservations = Reservation.query.filter(
            Reservation.property_id == property_uuid
        ).order_by(Reservation.check_in.desc()).all()
        return [reservation.to_dict() for reservation in reservations]
    
    except Exception as e:
        print(f"Database error: {str(e)}")
        return []

def get_user_reservations(user_id, page=1, per_page=10, search_query=None, property_id=None, filter_type=None):
    """
    Get all reservations for all user properties with pagination and filtering.
    filter_type can be: None (all), 'current', or 'upcoming'
    """
    try:
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        now = datetime.now(timezone.utc)
        
        # Base query with eager loading of property
        query = (db.session.query(Reservation)
                .join(Property)
                .options(db.joinedload(Reservation.property))
                .filter(Property.user_id == user_uuid))
        
        # Apply search filter
        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(
                db.or_(
                    Reservation.guest_name_partial.ilike(search_term),
                    Reservation.external_id.ilike(search_term)
                )
            )

        # Apply property filter
        if property_id:
            query = query.filter(Reservation.property_id == uuid.UUID(property_id))

        # Apply date filters
        if filter_type == 'current':
            query = query.filter(Reservation.check_in <= now, Reservation.check_out >= now)
        elif filter_type == 'upcoming':
            query = query.filter(Reservation.check_in > now)
        
        # Order by check-in date
        query = query.order_by(Reservation.check_in.desc())
        
        # Paginate the results
        paginated_reservations = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Convert to dict and dynamically set status
        reservation_list = []
        for r in paginated_reservations.items:
            r_dict = r.to_dict()
            if r.check_in <= now <= r.check_out:
                r_dict['status'] = 'active'
            reservation_list.append(r_dict)
            
        return {
            'reservations': reservation_list,
            'total': paginated_reservations.total,
            'pages': paginated_reservations.pages,
            'current_page': paginated_reservations.page
        }
    
    except Exception as e:
        print(f"Database error: {str(e)}")
        return {'reservations': [], 'total': 0, 'pages': 0, 'current_page': 1}

# Guest Management (Updated for new structure)
def create_guest(reservation_id, **kwargs):
    """
    Create a guest record for a reservation
    """
    try:
        guest = Guest(
            reservation_id=uuid.UUID(reservation_id) if isinstance(reservation_id, str) else reservation_id,
            verification_token=kwargs.get('verification_token'),
            full_name=kwargs.get('full_name'),
            cin_or_passport=kwargs.get('cin_or_passport'),
            birthdate=kwargs.get('birthdate'),
            nationality=kwargs.get('nationality'),
            address=kwargs.get('address'),
            phone=kwargs.get('phone'),
            email=kwargs.get('email'),
            document_type=kwargs.get('document_type'),
            id_document_path=kwargs.get('id_document_path'),
            verification_status=kwargs.get('verification_status', 'pending')
        )
        
        db.session.add(guest)
        db.session.commit()
        return str(guest.id)
    
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return None

def get_reservation_guests(reservation_id):
    """
    Get all guests for a specific reservation
    """
    try:
        guests = (Guest.query
                 .filter_by(reservation_id=uuid.UUID(reservation_id) if isinstance(reservation_id, str) else reservation_id)
                 .join(Reservation)
                 .join(Property)
                 .options(db.joinedload(Guest.reservation).joinedload(Reservation.property))
                 .all())
        return [guest.to_dict() for guest in guests]
    
    except Exception as e:
        print(f"Database error: {str(e)}")
        return []

def get_guest_by_reservation(reservation_id):
    """
    Get the guest associated with a reservation (assumes one guest per reservation)
    """
    try:
        guest = (Guest.query
                .filter_by(reservation_id=uuid.UUID(reservation_id) if isinstance(reservation_id, str) else reservation_id)
                .join(Reservation)
                .join(Property)
                .options(db.joinedload(Guest.reservation).joinedload(Reservation.property))
                .first())
        return guest.to_dict() if guest else None
    
    except Exception as e:
        print(f"Database error: {str(e)}")
        return None

def update_guest(guest_id, guest_data):
    """
    Update an existing guest record using SQLAlchemy
    """
    try:
        # Convert guest_id to UUID if it's a string
        guest_uuid = uuid.UUID(guest_id) if isinstance(guest_id, str) else guest_id
        
        # Get the guest record
        guest = Guest.query.filter_by(id=guest_uuid).first()
        if not guest:
            return False
        
        # Handle date fields
        if 'birthdate' in guest_data:
            if isinstance(guest_data['birthdate'], str):
                if guest_data['birthdate']:  # Only parse if not empty
                    guest_data['birthdate'] = datetime.fromisoformat(guest_data['birthdate']).date()
                else:
                    guest_data['birthdate'] = None
        
        if 'verified_at' in guest_data:
            if isinstance(guest_data['verified_at'], str):
                if guest_data['verified_at']:  # Only parse if not empty
                    guest_data['verified_at'] = datetime.fromisoformat(guest_data['verified_at'])
                else:
                    guest_data['verified_at'] = None
        
        # Update allowed fields
        allowed_fields = [
            'full_name', 'cin_or_passport', 'birthdate', 'nationality',
            'address', 'phone', 'email', 'document_type', 'id_document_path',
            'verification_status', 'verified_at'
        ]
        
        for field in allowed_fields:
            if field in guest_data:
                setattr(guest, field, guest_data[field])
        
        guest.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating guest: {str(e)}")
        return False

# Verification Links (Updated for new structure)
def create_verification_link(guest_id, token, expires_at):
    """
    Create a verification link for a guest
    """
    try:
        verification_link = VerificationLink(
            guest_id=uuid.UUID(guest_id) if isinstance(guest_id, str) else guest_id,
            token=token,
            expires_at=expires_at
        )
        
        db.session.add(verification_link)
        db.session.commit()
        return str(verification_link.id)
    
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return None

def get_verification_link(token):
    """
    Get verification link by token
    """
    try:
        verification_link = VerificationLink.query.filter_by(token=token).first()
        return verification_link.to_dict() if verification_link else None
    
    except Exception as e:
        print(f"Database error: {str(e)}")
        return None

# Sync Logging
def create_sync_log(property_id, sync_type, status, **kwargs):
    """
    Create a sync log entry
    """
    try:
        sync_log = SyncLog(
            property_id=uuid.UUID(property_id) if isinstance(property_id, str) else property_id,
            sync_type=sync_type,
            status=status,
            events_processed=kwargs.get('events_processed', 0),
            errors=kwargs.get('errors'),
            started_at=kwargs.get('started_at', datetime.utcnow()),
            completed_at=kwargs.get('completed_at')
        )
        
        db.session.add(sync_log)
        db.session.commit()
        return str(sync_log.id)
    
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return None

# Legacy compatibility functions (for gradual migration)
def save_guest(guest_data):
    """
    Legacy function - redirects to new structure
    """
    # This would need reservation_id, but for now return None to prevent errors
    print("Warning: save_guest is deprecated, use create_guest with reservation_id")
    return None

def get_user_guests(firebase_uid, page=1, per_page=10, search_query=None, property_id=None):
    """
    Get all guests for a user with pagination and filtering.
    """
    try:
        user = User.query.filter_by(firebase_uid=firebase_uid).first()
        if not user:
            return {'guests': [], 'total': 0, 'pages': 0, 'current_page': 1}

        query = (db.session.query(Guest)
                 .join(Reservation)
                 .join(Property)
                 .options(db.joinedload(Guest.reservation).joinedload(Reservation.property))
                 .filter(Property.user_id == user.id))

        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(
                db.or_(
                    Guest.full_name.ilike(search_term),
                    Guest.email.ilike(search_term),
                    Guest.phone.ilike(search_term),
                    Reservation.external_id.ilike(search_term)
                )
            )

        if property_id:
            query = query.filter(Property.id == uuid.UUID(property_id))

        paginated_guests = query.order_by(Guest.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

        return {
            'guests': [guest.to_dict() for guest in paginated_guests.items],
            'total': paginated_guests.total,
            'pages': paginated_guests.pages,
            'current_page': paginated_guests.page
        }

    except Exception as e:
        print(f"Database error: {str(e)}")
        return {'guests': [], 'total': 0, 'pages': 0, 'current_page': 1}

def save_guest_verification(guest_data):
    """
    Save guest verification data with token validation
    """
    try:
        guest = Guest(
            user_id=guest_data['user_id'],
            verification_token=guest_data['verification_token'],
            full_name=guest_data['full_name'],
            cin_or_passport=guest_data['cin_or_passport'],
            birthdate=datetime.fromisoformat(guest_data['birthdate']) if isinstance(guest_data['birthdate'], str) else guest_data['birthdate'],
            nationality=guest_data['nationality'],
            address=guest_data.get('address', ''),
            document_type=guest_data.get('document_type', ''),
            verified_at=datetime.now(timezone.utc)
        )
        
        db.session.add(guest)
        db.session.commit()
        return str(guest.id)
    
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return None

def get_user_verification_links(user_id):
    """
    Get all verification links for a user
    """
    try:
        verification_links = VerificationLink.query.filter_by(user_id=user_id).order_by(VerificationLink.created_at.desc()).all()
        return [link.to_dict() for link in verification_links]
    
    except Exception as e:
        print(f"Database error: {str(e)}")
        return []

def use_verification_link(token, guest_id):
    """
    Mark verification link as used
    """
    try:
        verification_link = VerificationLink.query.filter_by(token=token).first()
        if verification_link:
            verification_link.is_used = True
            verification_link.guest_id = uuid.UUID(guest_id) if isinstance(guest_id, str) else guest_id
            verification_link.used_at = datetime.now(timezone.utc)
            db.session.commit()
            return True
        return False
    
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return False

def delete_guest(guest_id, user_id):
    """
    Delete a guest record (with user validation for security)
    """
    try:
        # First check if the guest belongs to the user (security)
        guest = Guest.query.filter_by(id=uuid.UUID(guest_id) if isinstance(guest_id, str) else guest_id, user_id=user_id).first()
        
        if not guest:
            return False  # Guest doesn't exist or doesn't belong to user
        
        # Delete the guest
        db.session.delete(guest)
        db.session.commit()
        return True
    
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return False

def save_booking(booking_data):
    """
    Save booking data using SQLAlchemy models
    """
    try:
        booking = Booking(
            user_id=booking_data['user_id'],
            external_id=booking_data.get('external_id'),
            guest_name=booking_data.get('guest_name'),
            guest_phone=booking_data.get('guest_phone'),
            guest_email=booking_data.get('guest_email'),
            check_in=booking_data['check_in'],
            check_out=booking_data['check_out'],
            property_name=booking_data.get('property_name'),
            booking_source=booking_data.get('booking_source'),
            status=booking_data.get('status', 'confirmed'),
            total_guests=booking_data.get('total_guests'),
            notes=booking_data.get('notes'),
            raw_data=booking_data.get('raw_data')
        )
        
        db.session.add(booking)
        db.session.commit()
        return str(booking.id)
    
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return None

def get_user_bookings(user_id):
    """
    Get all bookings for a specific user
    """
    try:
        bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.check_in.desc()).all()
        return [booking.to_dict() for booking in bookings]
    
    except Exception as e:
        print(f"Database error: {str(e)}")
        return []

def get_booking(booking_id, user_id):
    """
    Get a specific booking for a user
    """
    try:
        booking = Booking.query.filter_by(
            id=uuid.UUID(booking_id) if isinstance(booking_id, str) else booking_id,
            user_id=user_id
        ).first()
        return booking.to_dict() if booking else None
    
    except Exception as e:
        print(f"Database error: {str(e)}")
        return None

def update_booking(booking_id, user_id, update_data):
    """
    Update a booking record
    """
    try:
        booking = Booking.query.filter_by(
            id=uuid.UUID(booking_id) if isinstance(booking_id, str) else booking_id,
            user_id=user_id
        ).first()
        
        if not booking:
            return False
        
        # Update allowed fields
        allowed_fields = ['guest_name', 'guest_phone', 'guest_email', 'status', 'total_guests', 'notes', 'property_name']
        for field in allowed_fields:
            if field in update_data:
                setattr(booking, field, update_data[field])
        
        booking.updated_at = datetime.utcnow()
        db.session.commit()
        return True
    
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return False

def delete_booking(booking_id, user_id):
    """
    Delete a booking record (with user validation for security)
    """
    try:
        booking = Booking.query.filter_by(
            id=uuid.UUID(booking_id) if isinstance(booking_id, str) else booking_id,
            user_id=user_id
        ).first()
        
        if not booking:
            return False
        
        db.session.delete(booking)
        db.session.commit()
        return True
    
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        return False 

def delete_property(property_id, user_id):
    """
    Delete a property and all its associated data (reservations, guests, contracts)
    """
    try:
        property_uuid = uuid.UUID(property_id) if isinstance(property_id, str) else property_id
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        
        # Get the property with user verification
        property = Property.query.filter_by(id=property_uuid, user_id=user_uuid).first()
        if not property:
            return False
        
        # Start a transaction to delete all related data
        try:
            # Get all reservations for this property
            reservations = Reservation.query.filter_by(property_id=property_uuid).all()
            
            for reservation in reservations:
                # Delete all guests and their verification links
                guests = Guest.query.filter_by(reservation_id=reservation.id).all()
                for guest in guests:
                    # Delete verification links
                    VerificationLink.query.filter_by(guest_id=guest.id).delete()
                    # Delete contracts
                    Contract.query.filter_by(guest_id=guest.id).delete()
                    # Delete guest
                    db.session.delete(guest)
                
                # Delete sync logs
                SyncLog.query.filter_by(property_id=property_uuid).delete()
                
                # Delete reservation
                db.session.delete(reservation)
            
            # Finally, delete the property
            db.session.delete(property)
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Transaction error: {str(e)}")
            return False
    
    except Exception as e:
        print(f"Database error: {str(e)}")
        return False

def get_user_dashboard_stats(user_id):
    """
    Get dashboard statistics for a user.
    """
    try:
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        now = datetime.now(timezone.utc)

        total_properties = db.session.query(Property).filter_by(user_id=user_uuid).count()
        
        reservations_query = (db.session.query(Reservation)
                              .join(Property)
                              .filter(Property.user_id == user_uuid))
        
        total_reservations = reservations_query.count()
        
        upcoming_reservations = reservations_query.filter(Reservation.check_in > now).count()
        
        active_guests = reservations_query.filter(Reservation.check_in <= now, Reservation.check_out >= now).count()

        return {
            'totalProperties': total_properties,
            'totalReservations': total_reservations,
            'upcomingReservations': upcoming_reservations,
            'activeGuests': active_guests
        }

    except Exception as e:
        print(f"Database error in get_user_dashboard_stats: {str(e)}")
        return None 