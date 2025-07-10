"""
Calendar synchronization utilities for Hostify Property Management Platform
Handles iCal parsing and reservation creation from calendar feeds
"""

import requests
import icalendar
from datetime import datetime, timezone
from ..utils.database import create_reservation, get_property_reservations, create_guest
from ..models import Reservation
import re
import uuid

def sync_property_calendar(property_id):
    """
    Sync calendar data for a specific property from its iCal URL
    """
    try:
        from ..utils.database import get_property, update_property
        
        # Get property data
        property_data = get_property(property_id)
        if not property_data:
            return {'success': False, 'error': 'Property not found'}
        
        ical_url = property_data.get('ical_url')
        if not ical_url:
            return {'success': False, 'error': 'Property does not have an iCal URL'}
        
        # Fetch and parse iCal data
        events = parse_ical_from_url(ical_url)
        if not events:
            return {'success': False, 'error': 'No events found in calendar'}
        
        # Get existing reservations for comparison
        existing_reservations = get_property_reservations(property_id)
        existing_external_ids = {r.get('external_id') for r in existing_reservations if r.get('external_id')}
        
        new_reservations = 0
        updated_reservations = 0
        errors = []
        
        for event_data in events:
            try:
                # Check if reservation already exists
                external_id = event_data.get('external_id')
                if external_id in existing_external_ids:
                    # For now, skip updates - could implement update logic here
                    continue
                
                # Create JSON-serializable raw data
                raw_data = {}
                for key, value in event_data.items():
                    if isinstance(value, datetime):
                        raw_data[key] = value.isoformat()
                    else:
                        raw_data[key] = value
                
                # Create new reservation
                reservation_data = {
                    'property_id': property_id,
                    'external_id': external_id,
                    'platform': detect_platform_from_event(event_data),
                    'guest_name_partial': event_data.get('guest_name'),
                    'phone_partial': event_data.get('guest_phone'),
                    'check_in': event_data['check_in'],
                    'check_out': event_data['check_out'],
                    'status': event_data.get('event_type', 'confirmed'),
                    'sync_source': 'ical',
                    'raw_data': raw_data
                }
                
                reservation_id = create_reservation(**reservation_data)
                if reservation_id:
                    # Only create guest record for non-blocked dates
                    if event_data.get('event_type') != 'blocked':
                        # Create initial guest record with available data
                        guest_data = {
                            'full_name': event_data.get('guest_name'),  # Use available name
                            'phone': event_data.get('guest_phone'),     # Use available phone
                            'email': event_data.get('guest_email'),     # May be None
                            'verification_status': 'pending',           # Default status
                            # These fields will be nullable now:
                            'cin_or_passport': None,
                            'birthdate': None,
                            'nationality': None
                        }
                        
                        guest_id = create_guest(reservation_id, **guest_data)
                        if not guest_id:
                            errors.append(f"Created reservation but failed to create guest for event {external_id}")
                    
                    new_reservations += 1
                else:
                    errors.append(f"Failed to create reservation for event {external_id}")
            
            except Exception as e:
                errors.append(f"Error processing event {event_data.get('external_id', 'unknown')}: {str(e)}")
                continue
        
        # Update property last sync time
        update_property(property_id, property_data['user_id'], {
            'last_sync': datetime.utcnow()
        })
        
        return {
            'success': True,
            'events_processed': len(events),
            'new_reservations': new_reservations,
            'updated_reservations': updated_reservations,
            'errors': errors
        }
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def parse_ical_from_url(ical_url):
    """
    Parse iCal data from a URL and extract booking information
    """
    try:
        # Fetch iCal data
        response = requests.get(ical_url, timeout=30)
        response.raise_for_status()
        
        # Parse iCal content
        calendar = icalendar.Calendar.from_ical(response.content)
        
        events = []
        for component in calendar.walk():
            if component.name == "VEVENT":
                event_data = extract_event_data(component)
                if event_data:
                    events.append(event_data)
        
        return events
    
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch iCal data: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to parse iCal data: {str(e)}")

def extract_event_data(vevent):
    """
    Extract relevant booking data from an iCal VEVENT component
    """
    try:
        # Get basic event data
        summary = str(vevent.get('summary', ''))
        description = str(vevent.get('description', ''))
        uid = str(vevent.get('uid', ''))
        
        # Extract dates
        dtstart = vevent.get('dtstart')
        dtend = vevent.get('dtend')
        
        if not dtstart or not dtend:
            return None
        
        # Convert dates to datetime objects
        start_date = dtstart.dt
        end_date = dtend.dt
        
        # Handle date-only vs datetime objects
        if not isinstance(start_date, datetime):
            # It's a date object, convert to datetime
            start_date = datetime.combine(start_date, datetime.min.time())
        if not isinstance(end_date, datetime):
            # It's a date object, convert to datetime  
            end_date = datetime.combine(end_date, datetime.min.time())
        
        # Ensure timezone aware (only datetime objects have tzinfo)
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        # Extract guest information from summary and description
        guest_info = extract_guest_info(summary, description)
        
        # Detect if this is a blocked date or actual booking
        event_type = detect_event_type(summary, description)
        
        # Create event data
        event_data = {
            'external_id': uid,
            'guest_name': guest_info.get('name'),
            'guest_phone': guest_info.get('phone'),
            'check_in': start_date,
            'check_out': end_date,
            'summary': summary,
            'description': description,
            'uid': uid,
            'raw_summary': summary,
            'raw_description': description,
            'event_type': event_type
        }
        
        return event_data
    
    except Exception as e:
        print(f"Error extracting event data: {str(e)}")
        return None

def extract_guest_info(summary, description):
    """
    Extract guest name and phone from event summary and description
    """
    guest_info = {}
    
    # Combine text for parsing
    text = f"{summary} {description}".strip()
    
    # Common patterns for guest names (often in summary)
    # Look for patterns like "John Doe" or "Reserved for John Doe"
    name_patterns = [
        r'Reserved for ([A-Z][a-z]+ [A-Z][a-z]+)',
        r'([A-Z][a-z]+ [A-Z][a-z]+)',
        r'Guest: ([A-Z][a-z]+ [A-Z][a-z]+)',
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text)
        if match:
            guest_info['name'] = match.group(1).strip()
            break
    
    # Look for phone numbers
    phone_patterns = [
        r'(\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9})',
        r'(\d{10,})',
        r'Phone[:\s]+([+\d\s\-\(\)]{10,})'
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            guest_info['phone'] = match.group(1).strip()
            break
    
    return guest_info

def detect_event_type(summary, description):
    """
    Detect if this is a blocked date or actual booking
    """
    text = f"{summary} {description}".lower()
    
    # Common patterns for blocked dates
    blocked_patterns = [
        'blocked',
        'not available',
        'unavailable',
        'owner blocked',
        'maintenance',
        'personal use',
        'private',
        'blocked by owner',
        'host blocked',
        'cleaning',
        'repair',
        'reserved by owner'
    ]
    
    for pattern in blocked_patterns:
        if pattern in text:
            return 'blocked'
    
    # If it has guest information or reservation patterns, it's likely a booking
    booking_patterns = [
        'reserved',
        'booked',
        'guest',
        'confirmed',
        'check-in',
        'check-out'
    ]
    
    # If no guest name and contains blocking keywords, likely blocked
    if not any(pattern in text for pattern in booking_patterns):
        # Check if it's just a generic title without guest info
        if len(text.strip()) < 20 and any(word in text for word in ['busy', 'occupied', 'taken']):
            return 'blocked'
    
    return 'booking'

def detect_platform_from_event(event_data):
    """
    Try to detect the booking platform from event data
    """
    summary = event_data.get('summary', '').lower()
    description = event_data.get('description', '').lower()
    uid = event_data.get('uid', '').lower()
    
    text = f"{summary} {description} {uid}"
    
    if 'airbnb' in text:
        return 'airbnb'
    elif 'booking.com' in text or 'booking' in text:
        return 'booking.com'
    elif 'vrbo' in text:
        return 'vrbo'
    elif 'expedia' in text:
        return 'expedia'
    elif 'homeaway' in text:
        return 'homeaway'
    else:
        return 'unknown'

def test_ical_url_access(ical_url):
    """
    Test if an iCal URL is accessible and returns valid data
    """
    try:
        response = requests.get(ical_url, timeout=10)
        response.raise_for_status()
        
        # Try to parse the calendar
        calendar = icalendar.Calendar.from_ical(response.content)
        
        # Count events
        event_count = 0
        for component in calendar.walk():
            if component.name == "VEVENT":
                event_count += 1
        
        return {
            'accessible': True,
            'event_count': event_count,
            'content_length': len(response.content)
        }
    
    except requests.RequestException as e:
        return {
            'accessible': False,
            'error': f"Network error: {str(e)}"
        }
    except Exception as e:
        return {
            'accessible': False,
            'error': f"Parse error: {str(e)}"
        } 