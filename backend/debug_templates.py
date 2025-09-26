#!/usr/bin/env python3
"""
Debug script to check message templates data in the database
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
from app.models import MessageTemplate, Message, ScheduledMessage, MessageLog, User

def debug_templates():
    """Debug message templates data"""
    app = create_app()
    with app.app_context():
        print("🔍 DATABASE DEBUG: Message Templates Analysis")
        print("=" * 60)

        # Get all users first
        users = User.query.all()
        print(f"\n📊 USERS IN DATABASE: {len(users)}")
        for user in users:
            print(f"  - User: {user.name} ({user.email}) - ID: {user.id}")

        # Check message_templates table
        templates = MessageTemplate.query.all()
        print(f"\n📋 MESSAGE TEMPLATES TABLE: {len(templates)} records")
        print("-" * 40)

        for i, template in enumerate(templates, 1):
            print(f"\n#{i} TEMPLATE:")
            print(f"  ID: {template.id}")
            print(f"  User ID: {template.user_id}")
            print(f"  Name: {template.name}")
            print(f"  Type: {template.template_type}")
            print(f"  Subject: {template.subject}")
            print(f"  Content Preview: {template.content[:100]}...")
            print(f"  Channels: {template.channels}")
            print(f"  Active: {template.active}")
            print(f"  Trigger Event: {template.trigger_event}")
            print(f"  Created: {template.created_at}")

        # Check other message tables
        messages = Message.query.all()
        print(f"\n💌 MESSAGES TABLE (sent messages): {len(messages)} records")
        for i, msg in enumerate(messages, 1):
            print(f"  #{i}: Type: {msg.message_type}, Content: {msg.content[:50]}...")

        scheduled = ScheduledMessage.query.all()
        print(f"\n⏰ SCHEDULED MESSAGES TABLE: {len(scheduled)} records")
        for i, msg in enumerate(scheduled, 1):
            print(f"  #{i}: Status: {msg.status}, Scheduled: {msg.scheduled_for}")

        # Check what the API would return
        print(f"\n🔌 API SIMULATION:")
        print("-" * 40)

        # Simulate the API call for each user
        for user in users:
            user_templates = MessageTemplate.query.filter_by(user_id=user.id).order_by(MessageTemplate.created_at.desc()).all()
            print(f"\nAPI Response for {user.name}:")
            print(f"  Templates returned: {len(user_templates)}")

            for template in user_templates:
                template_dict = template.to_dict()
                print(f"  - {template_dict['name']} ({template_dict['template_type']})")
                print(f"    Content: {template_dict['content'][:80]}...")
                print(f"    Created: {template_dict.get('created_at', 'N/A')}")

if __name__ == "__main__":
    debug_templates()