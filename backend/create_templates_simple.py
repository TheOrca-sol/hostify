#!/usr/bin/env python3
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
    from app.models import User, MessageTemplate
    
    app = create_app()
    with app.app_context():
        print("Creating test message templates...")
        
        # Get all users
        users = User.query.all()
        if not users:
            print("No users found.")
            sys.exit(1)
            
        for user in users:
            print(f"Checking user: {user.name} ({user.id})")
            
            # Check existing templates
            existing = MessageTemplate.query.filter_by(user_id=user.id).all()
            print(f"User has {len(existing)} existing templates:")
            for t in existing:
                print(f"  - {t.name} (type: {t.template_type}, trigger: {t.trigger_event})")
            
            # Create templates if none exist
            if len(existing) == 0:
                templates = [
                    {
                        'name': 'Check-in Reminder',
                        'template_type': 'check_in',
                        'content': 'Hi {{guest_name}}! Your check-in is tomorrow at {{property_name}}.',
                        'trigger_event': 'check_in',
                        'trigger_offset_value': 1,
                        'trigger_offset_unit': 'days', 
                        'trigger_direction': 'before'
                    }
                ]
                
                for tpl in templates:
                    template = MessageTemplate(
                        user_id=user.id,
                        name=tpl['name'],
                        template_type=tpl['template_type'],
                        content=tpl['content'],
                        channels=['sms'],
                        active=True,
                        trigger_event=tpl['trigger_event'],
                        trigger_offset_value=tpl['trigger_offset_value'],
                        trigger_offset_unit=tpl['trigger_offset_unit'],
                        trigger_direction=tpl['trigger_direction']
                    )
                    db.session.add(template)
                    print(f"Created template: {tpl['name']}")
                
                db.session.commit()
                print("Templates created successfully!")
                
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()