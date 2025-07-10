"""Calendar synchronization utilities"""

import requests
from icalendar import Calendar
from datetime import datetime, timedelta
from app.models import db, Reservation, SyncLog, Guest
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
        # Fetch the calendar
        response = requests.get(property.ical_url)
        response.raise_for_status()
        
        # Parse the calendar
        calendar = Calendar.from_ical(response.text)
        
        # Process each event
        for event in calendar.walk('VEVENT'):
            start_date = event.get('dtstart').dt
            end_date = event.get('dtend').dt
            summary = str(event.get('summary', ''))
            uid = str(event.get('uid', ''))
            
            # Convert to datetime if date
            if not isinstance(start_date, datetime):
                start_date = datetime.combine(start_date, datetime.min.time())
            if not isinstance(end_date, datetime):
                end_date = datetime.combine(end_date, datetime.min.time())
            
            # Check if reservation exists
            reservation = Reservation.query.filter_by(
                property_id=property.id,
                external_id=uid
            ).first()
            
            if reservation:
                # Update existing reservation
                reservation.check_in = start_date
                reservation.check_out = end_date
                reservation.status = 'confirmed'  # Default to confirmed for calendar events
                reservation.guest_name_partial = summary if summary else reservation.guest_name_partial
            else:
                # Create new reservation
                reservation = Reservation(
                    property_id=property.id,
                    check_in=start_date,
                    check_out=end_date,
                    external_id=uid,
                    status='confirmed',
                    sync_source='ical',
                    guest_name_partial=summary if summary else None
                )
                db.session.add(reservation)
                db.session.flush()  # Get the reservation ID
                
                # Create a guest record if we have a guest name
                if summary:
                    guest = Guest(
                        reservation_id=reservation.id,
                        full_name=summary,
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
        return False 