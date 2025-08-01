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
from .routes.contract_templates import contract_templates_bp
from .routes.upload import upload_bp
from .routes.verification import verification_bp
from .routes.calendar import calendar_bp
from .routes.reservations import reservations_bp
from .routes.messages import messages_bp
from .routes.user import user_bp
from .routes.dashboard import dashboard_bp
from .routes.auth import auth_bp
from .routes.team import team_bp
from .routes.sms_auth import sms_auth_bp
import os

def create_app():
    app = Flask(__name__)
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a-super-secret-key-for-dev')
    
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
    app.register_blueprint(contracts_bp, url_prefix='/api/contracts')
    app.register_blueprint(contract_templates_bp, url_prefix='/api/contract-templates')
    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(verification_bp, url_prefix='/api')
    app.register_blueprint(calendar_bp, url_prefix='/api')
    app.register_blueprint(reservations_bp, url_prefix='/api')
    app.register_blueprint(messages_bp, url_prefix='/api/messages')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(team_bp, url_prefix='/api')
    app.register_blueprint(sms_auth_bp, url_prefix='/api/sms-auth')
    

    return app 