#!/usr/bin/env python3
"""
Add KYC fields to Guest model for Didit integration
"""

import os
import sys

# Get absolute path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Set environment
os.environ.setdefault('FLASK_APP', 'app')
os.environ.setdefault('FLASK_ENV', 'development')

try:
    from app import create_app, db
    from sqlalchemy import text
    
    app = create_app()
    with app.app_context():
        print("Adding KYC fields to Guest table...")
        
        # Add new KYC-related columns
        db.engine.execute(text("""
            ALTER TABLE guests 
            ADD COLUMN IF NOT EXISTS kyc_session_id TEXT,
            ADD COLUMN IF NOT EXISTS kyc_confidence_score FLOAT,
            ADD COLUMN IF NOT EXISTS kyc_liveness_passed BOOLEAN DEFAULT FALSE;
        """))
        
        print("Successfully added KYC fields!")
        print("New fields:")
        print("- kyc_session_id: Store Didit session ID")
        print("- kyc_confidence_score: Face match confidence score")  
        print("- kyc_liveness_passed: Whether liveness check passed")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()