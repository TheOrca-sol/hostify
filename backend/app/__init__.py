"""
Flask app factory for Hostify Property Management Platform
"""

import os
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    """
    Create and configure the Flask application
    """
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, 
         origins=['http://localhost:5173', 'http://localhost:3000'],
         allow_headers=['Content-Type', 'Authorization'],
         supports_credentials=True)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database configuration
    database_url = os.getenv('DATABASE_URL', 'postgresql://localhost/hostify_dev')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Initialize extensions
    from .models import db
    db.init_app(app)
    
    # Initialize migrations
    migrate = Migrate(app, db)
    
    # Register blueprints
    from .routes.guests import guests_bp
    from .routes.calendar import calendar_bp
    from .routes.verification import verification_bp
    from .routes.properties import properties_bp
    from .routes.reservations import reservations_bp
    from .routes.contracts import contracts_bp
    
    app.register_blueprint(guests_bp, url_prefix='/api')
    app.register_blueprint(calendar_bp, url_prefix='/api')
    app.register_blueprint(verification_bp, url_prefix='/api')
    app.register_blueprint(properties_bp, url_prefix='/api')
    app.register_blueprint(reservations_bp, url_prefix='/api')
    app.register_blueprint(contracts_bp, url_prefix='/api')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'service': 'hostify-api'}
    
    # API info endpoint
    @app.route('/api/info')
    def api_info():
        return {
            'service': 'Hostify Property Management API',
            'version': '2.0.0',
            'architecture': 'property-centric',
            'features': [
                'property_management',
                'reservation_tracking', 
                'guest_verification',
                'contract_generation',
                'calendar_sync'
            ],
            'endpoints': {
                'properties': '/api/properties',
                'reservations': '/api/reservations', 
                'guests': '/api/guests',
                'calendar': '/api/calendar',
                'verification': '/api/verification',
                'contracts': '/api/contracts'
            }
        }
    
    return app 