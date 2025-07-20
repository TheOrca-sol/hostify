import os
import sys
from dotenv import load_dotenv

# Load environment variables first
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print("Warning: .env file not found. Make sure your environment variables are set.")

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, MessageTemplate
from app.constants import TEMPLATE_TYPES

def backfill_default_templates():
    """
    Ensures all users have a default template for each message type.
    """
    app = create_app()
    with app.app_context():
        print("Starting backfill process for default message templates...")
        
        try:
            all_users = User.query.all()
            if not all_users:
                print("No users found.")
                return

            print(f"Found {len(all_users)} users. Checking templates for each...")

            specific_content = {
                "verification_request": "Hello {{guest_name}}, please verify your identity for your upcoming stay: {{verification_link}}",
                "welcome": "Welcome, {{guest_name}}! We're excited to host you at {{property_name}} from {{check_in_date}}.",
                "checkin": "Hi {{guest_name}}, just a reminder that check-in for your stay at {{property_name}} is tomorrow. Here are the details: [ADD CHECK-IN DETAILS HERE]",
                "checkout": "Hi {{guest_name}}, this is a reminder that your check-out is tomorrow at {{check_out_time}}. We hope you enjoyed your stay!",
                "review_request": "Thank you for staying with us, {{guest_name}}! We'd appreciate it if you could leave a review about your experience at {{property_name}}."
            }
            
            templates_created_count = 0
            for user in all_users:
                print(f"  -> Checking user '{user.name}'...")
                for t_type in TEMPLATE_TYPES:
                    # Check if a template of this type already exists for the user
                    existing_template = MessageTemplate.query.filter_by(
                        user_id=user.id,
                        template_type=t_type['value']
                    ).first()

                    if not existing_template:
                        templates_created_count += 1
                        print(f"    -> Missing '{t_type['label']}' template. Creating one...")
                        
                        default_content = f"This is the default template for {t_type['label']}. Please edit this content. Regards, {{host_name}}."
                        content = specific_content.get(t_type['value'], default_content)

                        new_template = MessageTemplate(
                            user_id=user.id,
                            name=f"Default {t_type['label']}",
                            template_type=t_type['value'],
                            subject=f"Regarding your stay at {{property_name}}",
                            content=content,
                            language="en",
                            channels=["sms"],
                            variables=["guest_name", "property_name", "check_in_date", "check_out_time", "verification_link", "host_name"]
                        )
                        db.session.add(new_template)

            if templates_created_count > 0:
                db.session.commit()
                print(f"\nSuccessfully created {templates_created_count} new default templates.")
            else:
                print("\nAll users already have a template for every available type. No action was needed.")

            print("Backfill process complete.")

        except Exception as e:
            db.session.rollback()
            print(f"\nAn error occurred: {e}")
            print("Transaction has been rolled back.")

if __name__ == "__main__":
    backfill_default_templates()