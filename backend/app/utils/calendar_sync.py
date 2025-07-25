"""Calendar synchronization utilities"""

import requests
from icalendar import Calendar
from datetime import datetime, timedelta
from app.models import db, Reservation, SyncLog, Guest
from .ical_parser import parse_ical_from_url
import logging
import uuid

def validate_ical_url(ical_url):
    """Validate if a URL points to a valid iCal calendar"""
    try:
        # Try to fetch the calendar
        response = requests.get(ical_url, timeout=10)
        response.raise_for_status()  # Raise exception for bad status codes
        
        # Try to parse the calendar
        calendar = Calendar.from_ical(response.text)
        
        # Check if it has any events (not required but good to verify)
        has_events = any(component.name == 'VEVENT' for component in calendar.walk())
        
        return True
    except Exception as e:
        logging.error(f"Error validating iCal URL {ical_url}: {str(e)}")
        return False

def sync_property_calendar(property):
    """Sync a property's calendar from its iCal URL"""
    if not property.ical_url:
        return False
        
    try:
        # Use the centralized iCal parser
        parsed_events = parse_ical_from_url(property.ical_url)
        
        # Process each event
        for event_data in parsed_events:
            # Skip blocked or cancelled events
            if event_data['status'] != 'confirmed':
                continue

            # Check if reservation exists
            reservation = Reservation.query.filter_by(
                property_id=property.id,
                external_id=event_data['external_id']
            ).first()
            
            if reservation:
                # Update existing reservation
                reservation.check_in = event_data['check_in']
                reservation.check_out = event_data['check_out']
                reservation.status = event_data['status']
                reservation.guest_name_partial = event_data['guest_name']
                reservation.phone_partial = event_data['phone_partial']
                reservation.raw_data = event_data['raw_data']
            else:
                # Create new reservation
                reservation = Reservation(
                    property_id=property.id,
                    check_in=event_data['check_in'],
                    check_out=event_data['check_out'],
                    external_id=event_data['external_id'],
                    status=event_data['status'],
                    sync_source='ical',
                    guest_name_partial=event_data['guest_name'],
                    phone_partial=event_data['phone_partial'],
                    raw_data=event_data['raw_data']
                )
                db.session.add(reservation)
                db.session.flush()  # Get the reservation ID
                
                # Create a guest record if we have a guest name
                if event_data['guest_name']:
                    guest = Guest(
                        reservation_id=reservation.id,
                        full_name=event_data['guest_name'],
                        verification_status='pending',
                        verification_token=str(uuid.uuid4())  # Generate a unique token
                    )
                    db.session.add(guest)
        
        # Commit all changes
        db.session.commit()
        
        # Update last sync time
        property.last_sync = datetime.utcnow()
        db.session.commit()
        
        return True
        
    except Exception as e:
        logging.error(f"Error syncing calendar for property {property.id}: {str(e)}")
        db.session.rollback()
        return False 