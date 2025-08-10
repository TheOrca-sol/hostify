#!/usr/bin/env python3
"""
Start both background workers for Hostify:
1. Calendar sync worker
2. Message sending worker
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
    """Start both background workers"""
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
    
    print(f"Calendar sync worker PID: {calendar_process.pid}")
    print(f"Message sending worker PID: {message_process.pid}")
    print("Workers started successfully!")
    print("Press Ctrl+C to stop all workers")
    
    try:
        # Wait for both processes
        while True:
            # Check if processes are still running
            if calendar_process.poll() is not None:
                print("Calendar sync worker has stopped!")
                break
            if message_process.poll() is not None:
                print("Message sending worker has stopped!")
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping workers...")
        
        # Terminate processes gracefully
        calendar_process.terminate()
        message_process.terminate()
        
        # Wait for them to finish
        try:
            calendar_process.wait(timeout=5)
            message_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("Workers didn't stop gracefully, forcing termination...")
            calendar_process.kill()
            message_process.kill()
        
        print("All workers stopped.")

if __name__ == "__main__":
    start_workers()
