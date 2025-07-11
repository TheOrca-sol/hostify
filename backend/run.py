#!/usr/bin/env python3
"""
Hostify Backend Runner
Entry point for the Flask application with Flask-Migrate support
"""

import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
logger.debug("Loading environment variables...")
load_dotenv()

# Debug: Print loaded environment variables
logger.debug("FIREBASE_ADMIN_SDK_JSON exists: %s", bool(os.getenv('FIREBASE_ADMIN_SDK_JSON')))
logger.debug("FIREBASE_SERVICE_ACCOUNT_PATH: %s", os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH'))

from app import create_app
from app.models import db
from flask_migrate import Migrate

# Create the Flask application
app = create_app()
migrate = Migrate(app, db)

@app.route('/')
def home():
    return {"message": "Hostify Backend API", "status": "running", "flask_migrate": "enabled"}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 