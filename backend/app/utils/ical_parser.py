"""
iCal parser utility for extracting calendar and booking data
"""

import requests
from icalendar import Calendar
from datetime import datetime, timezone
import pytz
import re
from typing import List, Dict, Optional

def fetch_ical_data(ical_url: str) -> str:
    """
    Fetch iCal data from a URL
    
    Args:
        ical_url: The URL to the iCal file
        
    Returns:
        Raw iCal data as string
        
    Raises:
        Exception: If unable to fetch the data
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(ical_url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        raise Exception(f"Failed to fetch iCal data: {str(e)}")

def extract_guest_info_from_summary(summary: str) -> Dict[str, Optional[str]]:
    """
    Extract guest information from event summary using various patterns
    
    Args:
        summary: Event summary text
        
    Returns:
        Dictionary with extracted guest information
    """
    guest_info = {
        'guest_name': None,
        'guest_phone': None,
        'guest_email': None,
        'total_guests': None
    }
    
    # Common patterns for guest names in Airbnb summaries
    name_patterns = [
        r'Reserved\s+for\s+(.+?)(?:\s+\(|$)',  # "Reserved for John Doe"
        r'Reserved\s+(.+?)(?:\s+\(|$)',        # "Reserved John Doe"
        r'Blocked\s+for\s+(.+?)(?:\s+\(|$)',   # "Blocked for John Doe"
        r'Blocked\s+(.+?)(?:\s+\(|$)',         # "Blocked John Doe"
        r'(.+?)\s+\(',                         # "John Doe (something)"
        r'^([A-Z][a-z]+\s+[A-Z][a-z]+)',       # "John Doe" at start
    ]
    
    # Skip if it's just generic text
    if summary.lower() in ['reserved', 'blocked', 'phone number', 'airbnb']:
        return guest_info
    
    for pattern in name_patterns:
        match = re.search(pattern, summary, re.IGNORECASE)
        if match:
            potential_name = match.group(1).strip()
            # Skip if it's just "Phone Number" or similar generic terms
            if potential_name.lower() not in ['phone number', 'airbnb', 'not available']:
                guest_info['guest_name'] = potential_name
                break
    
    # Extract phone numbers
    phone_pattern = r'(\+?[\d\s\-\(\)]{10,})'
    phone_match = re.search(phone_pattern, summary)
    if phone_match:
        guest_info['guest_phone'] = re.sub(r'[^\d+]', '', phone_match.group(1))
    
    # Extract email addresses
    email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    email_match = re.search(email_pattern, summary)
    if email_match:
        guest_info['guest_email'] = email_match.group(1)
    
    # Extract number of guests
    guests_patterns = [
        r'(\d+)\s+guests?',
        r'guests?:\s*(\d+)',
        r'\((\d+)\s+guests?\)'
    ]
    
    for pattern in guests_patterns:
        match = re.search(pattern, summary, re.IGNORECASE)
        if match:
            guest_info['total_guests'] = int(match.group(1))
            break
    
    return guest_info

def extract_phone_from_description(description: str) -> Optional[str]:
    """
    Extract phone number from description text
    
    Args:
        description: Event description text
        
    Returns:
        Phone number if found, None otherwise
    """
    # Look for "Phone Number (Last 4 Digits): XXXX" pattern
    phone_pattern = r'Phone Number.*?(\d{4})'
    match = re.search(phone_pattern, description, re.IGNORECASE)
    if match:
        return f"****{match.group(1)}"  # Return masked phone number
    
    # Look for other phone patterns
    full_phone_pattern = r'(\+?[\d\s\-\(\)]{10,})'
    phone_match = re.search(full_phone_pattern, description)
    if phone_match:
        return re.sub(r'[^\d+]', '', phone_match.group(1))
    
    return None

def parse_ical_events(ical_data: str) -> List[Dict]:
    """
    Parse iCal data and extract booking events
    
    Args:
        ical_data: Raw iCal data as string
        
    Returns:
        List of booking dictionaries
    """
    bookings = []
    
    try:
        calendar = Calendar.from_ical(ical_data)
        
        for component in calendar.walk():
            if component.name == "VEVENT":
                # Extract basic event data
                summary = str(component.get('summary', ''))
                description = str(component.get('description', ''))
                dtstart = component.get('dtstart')
                dtend = component.get('dtend')
                uid = str(component.get('uid', ''))
                
                # Skip if no dates
                if not dtstart or not dtend:
                    continue
                
                # Convert dates to datetime objects
                start_dt = dtstart.dt if hasattr(dtstart, 'dt') else dtstart
                end_dt = dtend.dt if hasattr(dtend, 'dt') else dtend
                
                # Ensure timezone awareness
                if isinstance(start_dt, datetime) and start_dt.tzinfo is None:
                    start_dt = pytz.UTC.localize(start_dt)
                if isinstance(end_dt, datetime) and end_dt.tzinfo is None:
                    end_dt = pytz.UTC.localize(end_dt)
                
                # Handle date-only events (all-day events)
                if not isinstance(start_dt, datetime):
                    start_dt = datetime.combine(start_dt, datetime.min.time())
                    start_dt = pytz.UTC.localize(start_dt)
                if not isinstance(end_dt, datetime):
                    end_dt = datetime.combine(end_dt, datetime.min.time())
                    end_dt = pytz.UTC.localize(end_dt)
                
                # Extract guest information from summary and description
                guest_info = extract_guest_info_from_summary(summary)
                
                # Try to extract phone from description if not found in summary
                if not guest_info['guest_phone'] and description:
                    guest_info['guest_phone'] = extract_phone_from_description(description)
                
                # If no guest name found in summary, try description
                if not guest_info['guest_name'] and description:
                    desc_guest_info = extract_guest_info_from_summary(description)
                    for key, value in desc_guest_info.items():
                        if value and not guest_info[key]:
                            guest_info[key] = value
                
                # For Airbnb blocked events, set guest name as "Blocked Period"
                if summary.lower() in ['airbnb (not available)', 'blocked'] and not guest_info['guest_name']:
                    guest_info['guest_name'] = 'Blocked Period'
                
                # For events with no guest name but phone info in description, use "Guest"
                if not guest_info['guest_name'] and guest_info['guest_phone']:
                    guest_info['guest_name'] = 'Guest'
                
                # Determine booking source
                booking_source = 'unknown'
                if 'airbnb' in summary.lower() or 'airbnb' in description.lower():
                    booking_source = 'airbnb'
                elif 'booking.com' in summary.lower() or 'booking.com' in description.lower():
                    booking_source = 'booking.com'
                elif 'vrbo' in summary.lower() or 'vrbo' in description.lower():
                    booking_source = 'vrbo'
                
                # Determine status
                status = 'confirmed'
                if any(word in summary.lower() for word in ['cancelled', 'canceled', 'blocked', 'not available']):
                    status = 'blocked'
                elif 'pending' in summary.lower():
                    status = 'pending'
                
                booking = {
                    'external_id': uid,
                    'guest_name': guest_info['guest_name'],
                    'guest_phone': guest_info['guest_phone'],
                    'guest_email': guest_info['guest_email'],
                    'check_in': start_dt,
                    'check_out': end_dt,
                    'booking_source': booking_source,
                    'status': status,
                    'total_guests': guest_info['total_guests'],
                    'notes': description if description and description != summary else None,
                    'raw_data': {
                        'summary': summary,
                        'description': description,
                        'uid': uid,
                        'dtstart': start_dt.isoformat(),
                        'dtend': end_dt.isoformat()
                    }
                }
                
                bookings.append(booking)
                
    except Exception as e:
        raise Exception(f"Failed to parse iCal data: {str(e)}")
    
    return bookings

def parse_ical_from_url(ical_url: str) -> List[Dict]:
    """
    Fetch and parse iCal data from a URL
    
    Args:
        ical_url: The URL to the iCal file
        
    Returns:
        List of booking dictionaries
    """
    ical_data = fetch_ical_data(ical_url)
    return parse_ical_events(ical_data) 