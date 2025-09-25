"""
Background job system for automated tasks
"""

import threading
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List
from ..models import Reservation, ReservationPasscode, Property, db
from .passcode_service import passcode_service

# Configure logging
logger = logging.getLogger(__name__)

class BackgroundJobScheduler:
    """Simple background job scheduler for automated tasks"""

    def __init__(self):
        self.running = False
        self.thread = None
        self.check_interval = 300  # Check every 5 minutes

    def start(self):
        """Start the background job scheduler"""
        if self.running:
            logger.warning("Background job scheduler is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Background job scheduler started")

    def stop(self):
        """Stop the background job scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Background job scheduler stopped")

    def _run_scheduler(self):
        """Main scheduler loop"""
        logger.info("Background job scheduler thread started")

        while self.running:
            try:
                # Run all scheduled jobs
                self._check_passcode_generation()
                self._cleanup_expired_passcodes()

                # Sleep for the check interval
                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in background job scheduler: {str(e)}")
                # Continue running even if there's an error
                time.sleep(60)  # Wait 1 minute before trying again

    def _check_passcode_generation(self):
        """Check for reservations that need passcode generation"""
        try:
            logger.debug("Checking for reservations needing passcode generation")

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

            logger.info(f"Found {len(reservations_needing_passcodes)} reservations needing passcode generation")

            # Generate passcodes for qualifying reservations
            for reservation in reservations_needing_passcodes:
                try:
                    logger.info(f"Generating passcode for reservation {reservation.id}")
                    result = passcode_service.generate_reservation_passcode(str(reservation.id))

                    if result.get('success'):
                        logger.info(f"Successfully generated passcode for reservation {reservation.id}")

                        # SMS notifications are handled automatically by the passcode service
                        if result.get('requires_manual_entry'):
                            logger.info(f"Manual passcode entry required for reservation {reservation.id} - SMS sent to host")

                    else:
                        logger.error(f"Failed to generate passcode for reservation {reservation.id}: {result.get('error')}")

                except Exception as e:
                    logger.error(f"Error generating passcode for reservation {reservation.id}: {str(e)}")

        except Exception as e:
            logger.error(f"Error in passcode generation check: {str(e)}")

    def _cleanup_expired_passcodes(self):
        """Clean up expired passcodes and update statuses"""
        try:
            logger.debug("Cleaning up expired passcodes")

            now = datetime.now(timezone.utc)

            # Find expired passcodes that are still marked as active
            expired_passcodes = ReservationPasscode.query.filter(
                ReservationPasscode.valid_until < now,
                ReservationPasscode.status == 'active'
            ).all()

            if expired_passcodes:
                logger.info(f"Found {len(expired_passcodes)} expired passcodes to clean up")

                for passcode in expired_passcodes:
                    try:
                        # Update status to expired
                        passcode.status = 'expired'
                        passcode.updated_at = now

                        # For TTLock passcodes, we could optionally revoke them from the API
                        # but they should already be expired on TTLock's side

                        logger.debug(f"Marked passcode {passcode.id} as expired")

                    except Exception as e:
                        logger.error(f"Error updating expired passcode {passcode.id}: {str(e)}")

                # Commit all changes
                db.session.commit()
                logger.info(f"Successfully cleaned up {len(expired_passcodes)} expired passcodes")

        except Exception as e:
            logger.error(f"Error in passcode cleanup: {str(e)}")
            db.session.rollback()

    def get_status(self) -> Dict:
        """Get scheduler status information"""
        return {
            'running': self.running,
            'check_interval': self.check_interval,
            'thread_alive': self.thread.is_alive() if self.thread else False
        }

# Global scheduler instance
background_scheduler = BackgroundJobScheduler()

def init_background_jobs():
    """Initialize background job system"""
    logger.info("Initializing background job system")
    background_scheduler.start()

def stop_background_jobs():
    """Stop background job system"""
    logger.info("Stopping background job system")
    background_scheduler.stop()