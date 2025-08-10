#!/usr/bin/env python3
"""
Property cleanup utility for Hostify
Identifies and cleans up invalid or orphaned properties
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Load environment variables first
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Property, User

def cleanup_properties():
    """
    Identify and clean up invalid properties
    """
    app = create_app()
    with app.app_context():
        print("=== Property Cleanup Utility ===")
        print(f"Running at: {datetime.now()}")
        
        # 1. Find properties with invalid URLs
        print("\n1. Properties with invalid/example URLs:")
        invalid_url_properties = Property.query.filter(
            Property.ical_url.like('https://example.com%')
        ).all()
        
        for prop in invalid_url_properties:
            print(f"  - {prop.name} (ID: {prop.id}) - URL: {prop.ical_url}")
        
        # 2. Find properties with empty names
        print("\n2. Properties with empty names:")
        empty_name_properties = Property.query.filter(
            (Property.name.is_(None)) | (Property.name == '')
        ).all()
        
        for prop in empty_name_properties:
            print(f"  - Property ID: {prop.id} - Name: '{prop.name}'")
        
        # 3. Find orphaned properties (no valid user)
        print("\n3. Orphaned properties (no valid user):")
        orphaned_properties = []
        all_properties = Property.query.all()
        
        for prop in all_properties:
            user = User.query.get(prop.user_id)
            if not user:
                orphaned_properties.append(prop)
                print(f"  - {prop.name} (ID: {prop.id}) - User ID: {prop.user_id} (not found)")
        
        # 4. Find properties that haven't been synced in a very long time
        print("\n4. Properties with very old last_sync (30+ days):")
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        old_sync_properties = Property.query.filter(
            Property.last_sync < thirty_days_ago,
            Property.last_sync.isnot(None)
        ).all()
        
        for prop in old_sync_properties:
            days_old = (datetime.now(timezone.utc) - prop.last_sync).days
            print(f"  - {prop.name} (ID: {prop.id}) - Last sync: {prop.last_sync} ({days_old} days ago)")
        
        # 5. Summary and cleanup options
        total_invalid = len(invalid_url_properties) + len(empty_name_properties) + len(orphaned_properties)
        
        print(f"\n=== Summary ===")
        print(f"Properties with invalid URLs: {len(invalid_url_properties)}")
        print(f"Properties with empty names: {len(empty_name_properties)}")
        print(f"Orphaned properties: {len(orphaned_properties)}")
        print(f"Properties with old sync: {len(old_sync_properties)}")
        print(f"Total problematic properties: {total_invalid}")
        
        if total_invalid > 0:
            print(f"\n=== Cleanup Options ===")
            print("Run with --fix to automatically clean up these properties:")
            print("  - Properties with example.com URLs will be marked inactive")
            print("  - Properties with empty names will be marked inactive")
            print("  - Orphaned properties will be marked inactive")
            print("  - Properties with old sync will be reset to sync immediately")
        else:
            print("\n✅ No problematic properties found!")

def fix_properties():
    """
    Automatically fix problematic properties
    """
    app = create_app()
    with app.app_context():
        print("=== Fixing Problematic Properties ===")
        
        # 1. Mark properties with invalid URLs as inactive
        invalid_url_count = Property.query.filter(
            Property.ical_url.like('https://example.com%')
        ).update({Property.is_active: False})
        
        # 2. Mark properties with empty names as inactive
        empty_name_count = Property.query.filter(
            (Property.name.is_(None)) | (Property.name == '')
        ).update({Property.is_active: False})
        
        # 3. Mark orphaned properties as inactive
        orphaned_count = 0
        all_properties = Property.query.all()
        for prop in all_properties:
            user = User.query.get(prop.user_id)
            if not user:
                prop.is_active = False
                orphaned_count += 1
        
        # 4. Reset very old sync timestamps
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        old_sync_count = Property.query.filter(
            Property.last_sync < thirty_days_ago,
            Property.last_sync.isnot(None)
        ).update({Property.last_sync: None})
        
        # Commit all changes
        db.session.commit()
        
        print(f"✅ Fixed {invalid_url_count} properties with invalid URLs")
        print(f"✅ Fixed {empty_name_count} properties with empty names")
        print(f"✅ Fixed {orphaned_count} orphaned properties")
        print(f"✅ Reset {old_sync_count} properties with old sync timestamps")
        print(f"✅ Total properties fixed: {invalid_url_count + empty_name_count + orphaned_count}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        fix_properties()
    else:
        cleanup_properties()
