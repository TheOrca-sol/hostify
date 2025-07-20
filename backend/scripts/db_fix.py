import os
import sys
from dotenv import load_dotenv

# Load environment variables first
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db

def run_sql(sql_commands):
    """Connects to the database and runs a list of raw SQL commands."""
    app = create_app()
    with app.app_context():
        try:
            with db.engine.connect() as connection:
                for command in sql_commands:
                    print(f"Executing SQL: {command}")
                    connection.execute(db.text(command))
                connection.commit()
            print("Commands executed successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    commands = [
        "ALTER TABLE message_templates ADD COLUMN IF NOT EXISTS trigger_event TEXT",
        "ALTER TABLE message_templates ADD COLUMN IF NOT EXISTS trigger_offset_value INTEGER",
        "ALTER TABLE message_templates ADD COLUMN IF NOT EXISTS trigger_offset_unit TEXT",
        "ALTER TABLE message_templates ADD COLUMN IF NOT EXISTS trigger_direction TEXT"
    ]
    run_sql(commands)
