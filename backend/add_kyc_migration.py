#!/usr/bin/env python3
"""
Add KYC fields to Guest model - Safe migration
"""

import os
import psycopg2
from urllib.parse import urlparse

# Get database URL from .env
def get_database_url():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.strip().startswith('DATABASE_URL='):
                    return line.split('=', 1)[1].strip()
    return None

def add_kyc_fields():
    """Add KYC fields to guests table"""
    try:
        database_url = get_database_url()
        if not database_url:
            print("❌ DATABASE_URL not found in .env file")
            return False
        
        print("🔍 Connecting to database...")
        
        # Parse database URL
        parsed = urlparse(database_url)
        
        # Connect to database
        conn = psycopg2.connect(
            host=parsed.hostname,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password,
            port=parsed.port or 5432
        )
        
        cur = conn.cursor()
        
        print("✅ Connected to database")
        print("📝 Adding KYC fields to guests table...")
        
        # Check if columns already exist
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'guests' 
            AND column_name IN ('kyc_session_id', 'kyc_confidence_score', 'kyc_liveness_passed');
        """)
        
        existing_columns = [row[0] for row in cur.fetchall()]
        
        # Add columns that don't exist
        if 'kyc_session_id' not in existing_columns:
            cur.execute("ALTER TABLE guests ADD COLUMN kyc_session_id TEXT;")
            print("✅ Added kyc_session_id column")
        else:
            print("ℹ️  kyc_session_id column already exists")
            
        if 'kyc_confidence_score' not in existing_columns:
            cur.execute("ALTER TABLE guests ADD COLUMN kyc_confidence_score FLOAT;")
            print("✅ Added kyc_confidence_score column")
        else:
            print("ℹ️  kyc_confidence_score column already exists")
            
        if 'kyc_liveness_passed' not in existing_columns:
            cur.execute("ALTER TABLE guests ADD COLUMN kyc_liveness_passed BOOLEAN DEFAULT FALSE;")
            print("✅ Added kyc_liveness_passed column")
        else:
            print("ℹ️  kyc_liveness_passed column already exists")
        
        # Commit changes
        conn.commit()
        
        # Verify the columns were added
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'guests' 
            AND column_name IN ('kyc_session_id', 'kyc_confidence_score', 'kyc_liveness_passed')
            ORDER BY column_name;
        """)
        
        columns = cur.fetchall()
        if columns:
            print("\n📊 KYC columns in guests table:")
            for col in columns:
                print(f"   • {col[0]} ({col[1]}) - Nullable: {col[2]} - Default: {col[3]}")
        
        cur.close()
        conn.close()
        
        print("\n🎉 KYC fields added successfully!")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    add_kyc_fields()