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

def backfill_verification_templates():
    """
    Finds all users who do not have a 'verification' message template
    and creates the default one for them.
    """
    app = create_app()
    with app.app_context():
        print("Starting backfill process for verification templates...")
        
        try:
            # Find all users
            all_users = User.query.all()
            if not all_users:
                print("No users found in the database.")
                return

            print(f"Found {len(all_users)} total users. Checking each for templates...")
            
            users_without_template = 0
            for user in all_users:
                # Check if a verification template already exists for this user
                existing_template = MessageTemplate.query.filter_by(
                    user_id=user.id,
                    template_type='verification_request'
                ).first()

                if not existing_template:
                    users_without_template += 1
                    print(f"  -> User '{user.name}' (ID: {user.id}) is missing a verification template. Creating one...")
                    
                    # Create the default verification message template
                    verification_template = MessageTemplate(
                        user_id=user.id,
                        name="Default Guest Verification",
                        template_type="verification_request",
                        subject="Verify Your Identity for Your Stay",
                        content="Hello {{guest_name}}, please verify your identity for your upcoming stay: {{verification_link}}",
                        language="en",
                        channels=["sms"],
                        variables=["guest_name", "verification_link"]
                    )
                    db.session.add(verification_template)
                else:
                    print(f"  -> User '{user.name}' (ID: {user.id}) already has a template. Skipping.")

            if users_without_template > 0:
                db.session.commit()
                print(f"\nSuccessfully created verification templates for {users_without_template} users.")
            else:
                print("\nAll users already have their verification templates. No action was needed.")

            print("Backfill process complete.")

        except Exception as e:
            db.session.rollback()
            print(f"\nAn error occurred: {e}")
            print("Transaction has been rolled back.")

if __name__ == "__main__":
    backfill_verification_templates()
