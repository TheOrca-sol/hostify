#!/usr/bin/env python3
"""
Automated cleanup script to remove fake contract templates
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import MessageTemplate

def cleanup_fake_contract_templates():
    """Automatically remove fake contract templates"""
    app = create_app()
    with app.app_context():
        print("🧹 AUTOMATIC CLEANUP: Removing fake contract templates")
        print("=" * 60)

        # Find all contract templates with guest-specific names
        fake_templates = MessageTemplate.query.filter(
            MessageTemplate.template_type == 'contract',
            MessageTemplate.name.like('Contract for %')
        ).all()

        print(f"Found {len(fake_templates)} fake contract templates to remove:")

        deleted_names = []
        for template in fake_templates:
            deleted_names.append(template.name)
            print(f"  ❌ {template.name}")

        if fake_templates:
            try:
                # Delete all fake contract templates
                for template in fake_templates:
                    db.session.delete(template)

                db.session.commit()
                print(f"\n✅ Successfully deleted {len(fake_templates)} fake contract templates!")

                # Show remaining templates
                remaining = MessageTemplate.query.filter_by(template_type='contract').all()
                print(f"\n📋 Remaining contract templates: {len(remaining)}")
                for template in remaining:
                    print(f"  ✅ {template.name}")

                # Show clean template counts
                print(f"\n📊 CLEAN TEMPLATE SUMMARY:")
                print("-" * 40)

                all_templates = MessageTemplate.query.all()
                print(f"Total message templates remaining: {len(all_templates)}")

                # Count by type
                type_counts = {}
                for template in all_templates:
                    template_type = template.template_type
                    type_counts[template_type] = type_counts.get(template_type, 0) + 1

                for template_type, count in type_counts.items():
                    print(f"  - {template_type}: {count}")

            except Exception as e:
                print(f"❌ Error during cleanup: {str(e)}")
                db.session.rollback()
        else:
            print("✅ No fake contract templates found!")

if __name__ == "__main__":
    cleanup_fake_contract_templates()