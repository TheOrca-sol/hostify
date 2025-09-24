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
from .routes.teams import teams_bp
from .routes.sms_auth import sms_auth_bp
from .routes.kyc import kyc_bp
from .routes.smart_locks import smart_locks_bp
from .routes.webhooks import webhooks_bp
import os
from datetime import datetime

def create_app():
    app = Flask(__name__)
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a-super-secret-key-for-dev')
    
    # Configure CORS
    allowed_origins = [
        "http://localhost:3000",  # Development
        "https://hostify-frontend.vercel.app",  # Production (update with your actual domain)
        os.getenv('FRONTEND_URL', 'http://localhost:3000')  # Environment variable
    ]
    
    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        },
        r"/*": {  # Fallback for any missing routes
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)
    
    # Health check endpoint for Railway
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}, 200
    
    # KYC verification completion endpoint - just closes the window
    @app.route('/api/verification-complete')
    def verification_complete():
        """Simple auto-close page after Didit verification completion"""
        return '''
        <script>
            // Close the window immediately
            window.close();
        </script>
        '''
    
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
    app.register_blueprint(teams_bp, url_prefix='/api')
    app.register_blueprint(sms_auth_bp, url_prefix='/api/sms-auth')
    app.register_blueprint(kyc_bp, url_prefix='/api')
    app.register_blueprint(smart_locks_bp, url_prefix='/api')
    app.register_blueprint(webhooks_bp, url_prefix='/api')

    return app 