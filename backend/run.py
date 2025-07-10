#!/usr/bin/env python3
"""
Hostify Backend Runner
Entry point for the Flask application with Flask-Migrate support
"""

import os
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