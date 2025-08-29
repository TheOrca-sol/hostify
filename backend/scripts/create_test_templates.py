#!/usr/bin/env python3
"""
Create test message templates for automation testing
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables first
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def create_test_templates():
    """Create test message templates for automation"""
    try:
        from app import create_app, db
        from app.models import User, MessageTemplate
        
        app = create_app()
        with app.app_context():
            print("Creating test message templates...")
            
            # Get all users
            users = User.query.all()
            if not users:
                print("No users found. Please create a user first.")
                return
                
            for user in users:
                print(f"Creating templates for user: {user.name} ({user.id})")
                
                # Check if templates already exist
                existing = MessageTemplate.query.filter_by(user_id=user.id).count()
                if existing > 0:
                    print(f"User already has {existing} templates")
                    continue
                
                templates_to_create = [
                    {
                        'name': 'Check-in Reminder',
                        'template_type': 'check_in',
                        'subject': 'Check-in reminder for {{property_name}}',
                        'content': 'Hi {{guest_name}}! Your check-in is tomorrow at {{property_name}}. Address: {{property_address}}. Any questions? Call {{host_phone}}.',
                        'trigger_event': 'check_in',
                        'trigger_offset_value': 1,
                        'trigger_offset_unit': 'days',
                        'trigger_direction': 'before'
                    },
                    {
                        'name': 'Welcome Message',
                        'template_type': 'check_in',
                        'subject': 'Welcome to {{property_name}}',
                        'content': 'Welcome {{guest_name}}! You can now check in at {{property_name}}. Enjoy your stay!',
                        'trigger_event': 'check_in',
                        'trigger_offset_value': 0,
                        'trigger_offset_unit': 'hours',
                        'trigger_direction': 'after'
                    },
                    {
                        'name': 'Check-out Reminder',
                        'template_type': 'check_out',
                        'subject': 'Check-out reminder',
                        'content': 'Hi {{guest_name}}! Your check-out is today at {{check_out_time}}. Thank you for staying with us!',
                        'trigger_event': 'check_out',
                        'trigger_offset_value': 2,
                        'trigger_offset_unit': 'hours',
                        'trigger_direction': 'before'
                    }
                ]
                
                for template_data in templates_to_create:
                    template = MessageTemplate(
                        user_id=user.id,
                        name=template_data['name'],
                        template_type=template_data['template_type'],
                        subject=template_data['subject'],
                        content=template_data['content'],
                        channels=['sms'],
                        active=True,
                        trigger_event=template_data['trigger_event'],
                        trigger_offset_value=template_data['trigger_offset_value'],
                        trigger_offset_unit=template_data['trigger_offset_unit'],
                        trigger_direction=template_data['trigger_direction']
                    )
                    db.session.add(template)
                    print(f"  Created: {template_data['name']}")
                
                db.session.commit()
                print(f"Successfully created templates for user {user.name}")
                
    except Exception as e:
        print(f"Error creating test templates: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_templates()