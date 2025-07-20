"""
Flask application factory
"""

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from .models import db
from .routes.guests import guests_bp
from .routes.properties import properties_bp
from .routes.contracts import contracts_bp
from .routes.upload import upload_bp
from .routes.verification import verification_bp
from .routes.calendar import calendar_bp
from .routes.reservations import reservations_bp
from .routes.messages import messages_bp
from .routes.user import user_bp
from .routes.dashboard import dashboard_bp
import os

def create_app():
    app = Flask(__name__)
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)
    
    # Register blueprints
    app.register_blueprint(guests_bp, url_prefix='/api')
    app.register_blueprint(properties_bp, url_prefix='/api')
    app.register_blueprint(contracts_bp, url_prefix='/api')
    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(verification_bp, url_prefix='/api')
    app.register_blueprint(calendar_bp, url_prefix='/api')
    app.register_blueprint(reservations_bp, url_prefix='/api')
    app.register_blueprint(messages_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    
    

    return app 