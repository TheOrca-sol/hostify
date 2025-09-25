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
from app.models import Reservation, ReservationPasscode, Property
from app.services.passcode_service import passcode_service

def check_passcode_generation():
    """Check for reservations that need passcode generation"""
    app = create_app()
    with app.app_context():
        print(f"[{datetime.now()}] Checking for reservations needing passcode generation...")

        try:
            # Get upcoming reservations within the next 4 hours that don't have passcodes yet
            now = datetime.now(timezone.utc)
            cutoff_time = now + timedelta(hours=4)

            # Find reservations that need passcode generation
            reservations_needing_passcodes = []

            # Get reservations with check-in within the next 4 hours
            upcoming_reservations = Reservation.query.filter(
                Reservation.check_in > now,
                Reservation.check_in <= cutoff_time,
                Reservation.status.in_(['confirmed', 'checked_in'])  # Only process active reservations
            ).all()

            for reservation in upcoming_reservations:
                # Check if passcode already exists
                existing_passcode = ReservationPasscode.query.filter_by(
                    reservation_id=reservation.id
                ).first()

                if not existing_passcode:
                    # Check if we should generate passcode (3 hours before check-in)
                    if passcode_service.should_generate_passcode(reservation):
                        reservations_needing_passcodes.append(reservation)

            if not reservations_needing_passcodes:
                print("No reservations need passcode generation at this time.")
                return

            print(f"Found {len(reservations_needing_passcodes)} reservations needing passcode generation")

            # Generate passcodes for qualifying reservations
            for reservation in reservations_needing_passcodes:
                try:
                    guest_info = f"guest {reservation.guest_name_partial}" if reservation.guest_name_partial else f"reservation {reservation.id}"
                    property_info = f"{reservation.property.name}" if reservation.property else "unknown property"
                    print(f"  -> Generating passcode for {guest_info} at {property_info}")

                    result = passcode_service.generate_reservation_passcode(str(reservation.id))

                    if result.get('success'):
                        print(f"    ✓ Successfully generated passcode for reservation {reservation.id}")
                        print(f"    -> Method: {result.get('method', 'unknown')}")

                        if result.get('passcode'):
                            print(f"    -> Passcode: {result.get('passcode')}")

                        # SMS notifications are handled automatically by the passcode service
                        if result.get('requires_manual_entry'):
                            print(f"    -> Manual passcode entry required - SMS sent to host")

                    else:
                        print(f"    ✗ Failed to generate passcode for reservation {reservation.id}: {result.get('error')}")

                except Exception as e:
                    print(f"    ✗ Error generating passcode for reservation {reservation.id}: {str(e)}")

        except Exception as e:
            print(f"Error in passcode generation check: {str(e)}")

def cleanup_expired_passcodes():
    """Clean up expired passcodes and update statuses"""
    app = create_app()
    with app.app_context():
        print(f"[{datetime.now()}] Cleaning up expired passcodes...")

        try:
            now = datetime.now(timezone.utc)

            # Find expired passcodes that are still marked as active
            expired_passcodes = ReservationPasscode.query.filter(
                ReservationPasscode.valid_until < now,
                ReservationPasscode.status == 'active'
            ).all()

            if not expired_passcodes:
                print("No expired passcodes to clean up.")
                return

            print(f"Found {len(expired_passcodes)} expired passcodes to clean up")

            for passcode in expired_passcodes:
                try:
                    # Update status to expired
                    passcode.status = 'expired'
                    passcode.updated_at = now

                    # For TTLock passcodes, they should already be expired on TTLock's side
                    print(f"  -> Marked passcode {passcode.passcode or 'pending'} as expired (reservation {passcode.reservation_id})")

                except Exception as e:
                    print(f"  ✗ Error updating expired passcode {passcode.id}: {str(e)}")

            # Commit all changes
            db.session.commit()
            print(f"Successfully cleaned up {len(expired_passcodes)} expired passcodes")

        except Exception as e:
            print(f"Error in passcode cleanup: {str(e)}")
            db.session.rollback()

def run_automation_cycle():
    """Run one complete automation cycle"""
    try:
        # Check for passcode generation
        check_passcode_generation()

        # Clean up expired passcodes
        cleanup_expired_passcodes()

        print("Smart lock automation cycle completed.")

    except Exception as e:
        print(f"Error in smart lock automation cycle: {str(e)}")

def run_worker(interval_seconds=300):  # Check every 5 minutes
    """
    Runs the smart lock automation worker indefinitely.
    """
    print("Starting the smart lock automation worker...")
    print(f"Will check for passcode generation and cleanup every {interval_seconds} seconds")

    while True:
        try:
            run_automation_cycle()
        except Exception as e:
            print(f"Error in smart lock automation worker: {str(e)}")

        print(f"Worker sleeping for {interval_seconds} seconds...")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        # Run once and exit
        run_automation_cycle()
    else:
        # Run continuously
        run_worker()