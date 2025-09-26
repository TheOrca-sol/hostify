#!/usr/bin/env python3
"""
Create reusable contract message templates for existing users
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
from app.models import MessageTemplate, User

def create_reusable_contract_templates():
    """Create reusable contract templates for all users"""
    app = create_app()
    with app.app_context():
        print("📝 CREATING REUSABLE CONTRACT TEMPLATES")
        print("=" * 60)

        # Get all users
        users = User.query.all()
        print(f"Found {len(users)} users to process")

        created_count = 0
        skipped_count = 0

        for user in users:
            print(f"\nProcessing user: {user.name} ({user.email})")

            # Check if user already has a reusable contract template
            existing_template = MessageTemplate.query.filter_by(
                user_id=user.id,
                template_type='contract',
                name='Contract Signature Request'
            ).first()

            if existing_template:
                print(f"  ✅ User already has reusable contract template")
                skipped_count += 1
                continue

            # Create reusable contract template
            template = MessageTemplate(
                user_id=user.id,
                name='Contract Signature Request',
                template_type='contract',
                subject='Your rental contract is ready',
                content='Hello {guest_name}, please review and sign your rental contract for {property_name}: {contract_link}\n\nThis link will expire in 7 days.\n\nThank you!',
                channels=['sms'],
                active=True,
                trigger_event='contract_generation'
            )

            try:
                db.session.add(template)
                db.session.commit()
                print(f"  ✅ Created reusable contract template for {user.name}")
                created_count += 1
            except Exception as e:
                print(f"  ❌ Failed to create template for {user.name}: {str(e)}")
                db.session.rollback()

        print(f"\n📊 SUMMARY:")
        print(f"  - Created templates: {created_count}")
        print(f"  - Skipped (already exists): {skipped_count}")
        print(f"  - Total users processed: {len(users)}")

        # Show all contract templates now
        all_contract_templates = MessageTemplate.query.filter_by(template_type='contract').all()
        print(f"\n📋 ALL CONTRACT TEMPLATES ({len(all_contract_templates)}):")

        for template in all_contract_templates:
            user = User.query.get(template.user_id)
            user_name = user.name if user else f"User ID {template.user_id}"
            print(f"  - {template.name} (by {user_name})")
            if not template.name == 'Contract Signature Request':
                print(f"    ⚠️  This template should be cleaned up: {template.name}")

if __name__ == "__main__":
    create_reusable_contract_templates()