#!/usr/bin/env python3
"""
Safe cleanup script that handles foreign key relationships properly
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
from app.models import MessageTemplate, ScheduledMessage

def cleanup_fake_contract_templates_safe():
    """Safely remove fake contract templates and related scheduled messages"""
    app = create_app()
    with app.app_context():
        print("🧹 SAFE CLEANUP: Removing fake contract templates and dependencies")
        print("=" * 70)

        # Find all contract templates with guest-specific names
        fake_templates = MessageTemplate.query.filter(
            MessageTemplate.template_type == 'contract',
            MessageTemplate.name.like('Contract for %')
        ).all()

        print(f"Found {len(fake_templates)} fake contract templates to remove:")

        if not fake_templates:
            print("✅ No fake contract templates found!")
            return

        fake_template_ids = [template.id for template in fake_templates]

        # Find related scheduled messages
        related_scheduled_messages = ScheduledMessage.query.filter(
            ScheduledMessage.template_id.in_(fake_template_ids)
        ).all()

        print(f"Found {len(related_scheduled_messages)} related scheduled messages")

        for template in fake_templates:
            print(f"  ❌ Template: {template.name}")
            print(f"     ID: {template.id}")
            print(f"     Created: {template.created_at}")

        print(f"\n📊 Related scheduled messages:")
        for msg in related_scheduled_messages:
            print(f"  ❌ Message ID: {msg.id}, Status: {msg.status}")

        try:
            print(f"\n🔄 Starting safe cleanup process...")

            # Step 1: Delete related scheduled messages first
            print(f"Step 1: Deleting {len(related_scheduled_messages)} related scheduled messages...")
            for msg in related_scheduled_messages:
                db.session.delete(msg)

            # Step 2: Delete fake templates
            print(f"Step 2: Deleting {len(fake_templates)} fake contract templates...")
            for template in fake_templates:
                db.session.delete(template)

            # Step 3: Commit all changes
            print(f"Step 3: Committing changes...")
            db.session.commit()

            print(f"\n✅ Successfully completed safe cleanup!")
            print(f"   - Deleted {len(related_scheduled_messages)} scheduled messages")
            print(f"   - Deleted {len(fake_templates)} fake contract templates")

            # Show remaining templates
            remaining_contract_templates = MessageTemplate.query.filter_by(template_type='contract').all()
            all_templates = MessageTemplate.query.all()

            print(f"\n📋 CLEANUP SUMMARY:")
            print(f"   - Remaining contract templates: {len(remaining_contract_templates)}")
            print(f"   - Total templates remaining: {len(all_templates)}")

            # Count by type
            type_counts = {}
            for template in all_templates:
                template_type = template.template_type
                type_counts[template_type] = type_counts.get(template_type, 0) + 1

            print(f"\n📊 Templates by type:")
            for template_type, count in type_counts.items():
                print(f"   - {template_type}: {count}")

            # Show remaining contract templates (if any)
            if remaining_contract_templates:
                print(f"\n✅ Remaining contract templates:")
                for template in remaining_contract_templates:
                    print(f"   - {template.name}")

        except Exception as e:
            print(f"❌ Error during cleanup: {str(e)}")
            print(f"Rolling back changes...")
            db.session.rollback()
            raise

if __name__ == "__main__":
    cleanup_fake_contract_templates_safe()