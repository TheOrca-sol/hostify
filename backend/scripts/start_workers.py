#!/usr/bin/env python3
"""
Start background workers for Hostify:
1. Calendar sync worker
2. Message sending worker
3. Smart lock automation worker
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def start_workers():
    """Start all background workers"""
    print("Starting Hostify background workers...")

    # Get the scripts directory
    scripts_dir = Path(__file__).parent

    # Start calendar sync worker
    calendar_script = scripts_dir / "sync_calendars.py"
    print(f"Starting calendar sync worker: {calendar_script}")
    calendar_process = subprocess.Popen([sys.executable, str(calendar_script)])

    # Start message sending worker
    message_script = scripts_dir / "send_scheduled_messages.py"
    print(f"Starting message sending worker: {message_script}")
    message_process = subprocess.Popen([sys.executable, str(message_script)])

    # Start smart lock automation worker
    smart_lock_script = scripts_dir / "smart_lock_automation.py"
    print(f"Starting smart lock automation worker: {smart_lock_script}")
    smart_lock_process = subprocess.Popen([sys.executable, str(smart_lock_script)])

    print(f"Calendar sync worker PID: {calendar_process.pid}")
    print(f"Message sending worker PID: {message_process.pid}")
    print(f"Smart lock automation worker PID: {smart_lock_process.pid}")
    print("All workers started successfully!")
    print("Press Ctrl+C to stop all workers")
    
    try:
        # Wait for all processes
        while True:
            # Check if processes are still running
            if calendar_process.poll() is not None:
                print("Calendar sync worker has stopped!")
                break
            if message_process.poll() is not None:
                print("Message sending worker has stopped!")
                break
            if smart_lock_process.poll() is not None:
                print("Smart lock automation worker has stopped!")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping all workers...")

        # Terminate processes gracefully
        calendar_process.terminate()
        message_process.terminate()
        smart_lock_process.terminate()

        # Wait for them to finish
        try:
            calendar_process.wait(timeout=5)
            message_process.wait(timeout=5)
            smart_lock_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("Workers didn't stop gracefully, forcing termination...")
            calendar_process.kill()
            message_process.kill()
            smart_lock_process.kill()

        print("All workers stopped.")

if __name__ == "__main__":
    start_workers()
