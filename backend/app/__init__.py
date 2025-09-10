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
    
    # KYC verification completion page
    @app.route('/api/verification-complete')
    def verification_complete():
        """Success page shown to users after completing Didit verification"""
        return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verification Complete</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 50px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    margin: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .container {
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    max-width: 500px;
                }
                .success-icon { 
                    font-size: 60px; 
                    color: #28a745; 
                    margin-bottom: 20px; 
                }
                h1 { 
                    color: #333; 
                    margin-bottom: 20px; 
                }
                p { 
                    color: #666; 
                    line-height: 1.5; 
                    margin-bottom: 30px; 
                }
                .close-btn {
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                }
                .close-btn:hover {
                    background: #5a6fd8;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✅</div>
                <h1>Verification Complete!</h1>
                <p>Your identity has been successfully verified. Please return to the previous tab - it will update automatically.</p>
                <p><strong>Processing...</strong> Your verification results are being processed and the status will update automatically.</p>
                <button class="close-btn" onclick="window.close()">Close Window</button>
            </div>
            <script>
                // Auto-close after 3 seconds
                setTimeout(() => {
                    window.close();
                }, 3000);
            </script>
        </body>
        </html>
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
    

    return app 