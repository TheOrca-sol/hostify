#!/usr/bin/env python3
"""
Cleanup script to remove fake contract templates that were incorrectly created per guest
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
    """Remove fake contract templates and keep only real reusable templates"""
    app = create_app()
    with app.app_context():
        print("🧹 CLEANUP: Removing fake contract templates")
        print("=" * 60)

        # Find all contract templates with guest-specific names
        fake_templates = MessageTemplate.query.filter(
            MessageTemplate.template_type == 'contract',
            MessageTemplate.name.like('Contract for %')
        ).all()

        print(f"Found {len(fake_templates)} fake contract templates to remove:")

        for template in fake_templates:
            print(f"  - ID: {template.id}")
            print(f"    Name: {template.name}")
            print(f"    Content preview: {template.content[:60]}...")
            print(f"    Created: {template.created_at}")

        if fake_templates:
            confirm = input(f"\n❗ Are you sure you want to DELETE these {len(fake_templates)} fake templates? (yes/no): ")

            if confirm.lower() == 'yes':
                try:
                    # Delete all fake contract templates
                    for template in fake_templates:
                        db.session.delete(template)

                    db.session.commit()
                    print(f"✅ Successfully deleted {len(fake_templates)} fake contract templates!")

                    # Show remaining templates
                    remaining = MessageTemplate.query.filter_by(template_type='contract').all()
                    print(f"\n📋 Remaining contract templates: {len(remaining)}")
                    for template in remaining:
                        print(f"  - {template.name} ({template.template_type})")

                except Exception as e:
                    print(f"❌ Error during cleanup: {str(e)}")
                    db.session.rollback()
            else:
                print("❌ Cleanup cancelled.")
        else:
            print("✅ No fake contract templates found!")

        # Show summary of all templates by user
        print(f"\n📊 FINAL TEMPLATE SUMMARY:")
        print("-" * 40)

        all_templates = MessageTemplate.query.order_by(MessageTemplate.created_at.desc()).all()
        template_counts = {}

        for template in all_templates:
            user_id = str(template.user_id)
            if user_id not in template_counts:
                template_counts[user_id] = {'total': 0, 'types': {}}

            template_counts[user_id]['total'] += 1
            template_type = template.template_type
            if template_type not in template_counts[user_id]['types']:
                template_counts[user_id]['types'][template_type] = 0
            template_counts[user_id]['types'][template_type] += 1

        for user_id, counts in template_counts.items():
            print(f"User {user_id}: {counts['total']} templates")
            for template_type, count in counts['types'].items():
                print(f"  - {template_type}: {count}")

if __name__ == "__main__":
    cleanup_fake_contract_templates()