"""
Database utilities for Hostify Property Management Platform
Updated to support property-centric architecture with reservations and contracts
"""

from datetime import datetime, timezone
from ..models import db, User, Property, Reservation, Guest, VerificationLink, Contract, ContractTemplate, SyncLog
import uuid

# User Management
def create_user(firebase_uid, email, name, **kwargs):
    """
    Create a new user from Firebase authentication
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
        db.session.commit()
        return str(user.id)
    
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
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

def get_user_reservations(user_id, filter_type=None):
    """
    Get all reservations for all user properties
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
        
        # Apply date filters
        if filter_type == 'current':
            # Current reservations: check_in <= now <= check_out
            query = query.filter(
                Reservation.check_in <= now,
                Reservation.check_out >= now
            )
        elif filter_type == 'upcoming':
            # Upcoming reservations: check_in > now
            query = query.filter(
                Reservation.check_in > now
            )
        
        # Order by check-in date
        query = query.order_by(Reservation.check_in.desc())
        
        reservations = query.all()
        return [reservation.to_dict() for reservation in reservations]
    
    except Exception as e:
        print(f"Database error: {str(e)}")
        return []

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
    Update an existing guest record
    """
    try:
        # Build update query dynamically based on provided fields
        update_fields = []
        params = []
        for key, value in guest_data.items():
            if key not in ['id', 'created_at', 'updated_at', 'reservation_id']:
                update_fields.append(f"{key} = %s")
                params.append(value)
        
        # Add guest_id as last parameter
        params.append(guest_id)
        
        update_query = f"""
            UPDATE guests
            SET {', '.join(update_fields)},
                updated_at = NOW()
            WHERE id = %s
            RETURNING id
        """
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(update_query, params)
                conn.commit()
                return True
    except Exception as e:
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

def get_user_guests(firebase_uid):
    """
    Get all guests for user through reservations using Firebase UID
    """
    try:
        # First get the user record by Firebase UID
        user = User.query.filter_by(firebase_uid=firebase_uid).first()
        if not user:
            print(f"User not found for Firebase UID: {firebase_uid}")
            return []
            
        # Now get guests using the user's UUID with eager loading of relationships
        guests = (db.session.query(Guest)
                 .join(Reservation)
                 .join(Property)
                 .options(db.joinedload(Guest.reservation).joinedload(Reservation.property))
                 .filter(Property.user_id == user.id)
                 .all())
        return [guest.to_dict() for guest in guests]
    
    except Exception as e:
        print(f"Database error: {str(e)}")
        return []

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