import os
import sys
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import time

# Load environment variables first
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Property
from app.utils.calendar_sync import sync_property_calendar

def sync_due_calendars():
    """
    Finds and syncs all properties that are due for calendar sync.
    """
    app = create_app()
    with app.app_context():
        print(f"[{datetime.now()}] Checking for properties due for calendar sync...")
        
        try:
            now = datetime.now(timezone.utc)
            
            # Get all active properties with calendar URLs
            properties = Property.query.filter(
                Property.is_active == True,
                Property.ical_url.isnot(None),
                Property.ical_url != ''
            ).all()

            if not properties:
                print("No properties with calendar URLs found.")
                return

            synced_count = 0
            error_count = 0
            
            for property in properties:
                try:
                    # Check if it's time to sync this property
                    if should_sync_property(property, now):
                        print(f"Syncing calendar for property: {property.name} (ID: {property.id})")
                        
                        # Perform the sync
                        sync_success = sync_property_calendar(property)
                        
                        if sync_success:
                            # Update last_sync timestamp
                            property.last_sync = now
                            db.session.commit()
                            synced_count += 1
                            print(f"✓ Successfully synced calendar for {property.name}")
                        else:
                            error_count += 1
                            print(f"✗ Failed to sync calendar for {property.name}")
                    else:
                        # Calculate time until next sync
                        next_sync = get_next_sync_time(property)
                        time_until_sync = next_sync - now
                        hours_until_sync = time_until_sync.total_seconds() / 3600
                        print(f"Property {property.name} not due for sync yet. Next sync in {hours_until_sync:.1f} hours")
                        
                except Exception as e:
                    error_count += 1
                    print(f"✗ Error syncing calendar for property {property.name}: {str(e)}")
                    continue

            print(f"Calendar sync completed. Synced: {synced_count}, Errors: {error_count}")
            
        except Exception as e:
            print(f"Error in calendar sync process: {str(e)}")

def should_sync_property(property, now):
    """
    Determine if a property should be synced based on its sync_frequency and last_sync.
    """
    if not property.last_sync:
        # Never synced before, so sync now
        return True
    
    # Calculate when the next sync should happen
    next_sync_time = property.last_sync + timedelta(hours=property.sync_frequency)
    
    # If it's time for the next sync (or past due)
    return now >= next_sync_time

def get_next_sync_time(property):
    """
    Calculate when the next sync should happen for a property.
    """
    if not property.last_sync:
        return datetime.now(timezone.utc)
    
    return property.last_sync + timedelta(hours=property.sync_frequency)

def run_worker(interval_seconds=300):  # Check every 5 minutes
    """
    Runs the calendar sync worker indefinitely.
    """
    print("Starting the calendar sync worker...")
    print(f"Will check for syncs every {interval_seconds} seconds")
    
    while True:
        try:
            sync_due_calendars()
        except Exception as e:
            print(f"Error in calendar sync worker: {str(e)}")
        
        print(f"Worker sleeping for {interval_seconds} seconds...")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        # Run once and exit
        sync_due_calendars()
    else:
        # Run continuously
        run_worker()
