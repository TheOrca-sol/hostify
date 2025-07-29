import os
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from flask import current_app

def send_team_invitation_email(
    invited_email, 
    inviter_name, 
    property_name, 
    role, 
    invitation_token,
    expires_at
):
    """
    Send team invitation email
    """
    try:
        # For development, we'll use a simple email template
        # In production, you'd use a service like SendGrid, AWS SES, etc.
        
        subject = f"You're invited to join {property_name} team!"
        
        # Create invitation URL
        base_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        invitation_url = f"{base_url}/invite/{invitation_token}"
        
        # HTML email template
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #3B82F6; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .role-badge {{ 
                    display: inline-block; 
                    padding: 8px 16px; 
                    background-color: #EBF8FF; 
                    color: #2563EB; 
                    border-radius: 20px; 
                    font-weight: bold; 
                    margin: 10px 0; 
                }}
                .cta-button {{ 
                    display: inline-block; 
                    padding: 15px 30px; 
                    background-color: #3B82F6; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 8px; 
                    font-weight: bold; 
                    margin: 20px 0; 
                }}
                .cta-button:hover {{ background-color: #2563EB; }}
                .footer {{ color: #666; font-size: 14px; margin-top: 20px; text-align: center; }}
                .expires {{ color: #DC2626; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏠 You're Invited!</h1>
                </div>
                <div class="content">
                    <h2>Welcome to the Team</h2>
                    <p>Hi there!</p>
                    <p><strong>{inviter_name}</strong> has invited you to join the team for:</p>
                    <h3>🏡 {property_name}</h3>
                    <div class="role-badge">Role: {role.title()}</div>
                    
                    <p>As a <strong>{role}</strong>, you'll have access to manage various aspects of this property through our platform.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{invitation_url}" class="cta-button">Accept Invitation</a>
                    </div>
                    
                    <p><strong>What happens next?</strong></p>
                    <ul>
                        <li>Click the button above to accept the invitation</li>
                        <li>Sign in or create your account</li>
                        <li>Start managing {property_name} with your team</li>
                    </ul>
                    
                    <div class="expires">
                        ⏰ This invitation expires on {expires_at.strftime('%B %d, %Y at %I:%M %p')}
                    </div>
                    
                    <p>If you have any questions, feel free to reach out to {inviter_name}.</p>
                    
                    <div class="footer">
                        <p>This invitation was sent through Hostify - Guest ID Verification System</p>
                        <p>If you didn't expect this invitation, you can safely ignore this email.</p>
                        <p><small>Invitation ID: {invitation_token[:8]}...</small></p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_body = f"""
        You're Invited to Join {property_name}!
        
        Hi there!
        
        {inviter_name} has invited you to join the team for {property_name} as a {role}.
        
        To accept this invitation, please visit:
        {invitation_url}
        
        What happens next:
        1. Click the link above to accept the invitation
        2. Sign in or create your account
        3. Start managing {property_name} with your team
        
        This invitation expires on {expires_at.strftime('%B %d, %Y at %I:%M %p')}.
        
        If you have any questions, feel free to reach out to {inviter_name}.
        
        ---
        This invitation was sent through Hostify - Guest ID Verification System
        If you didn't expect this invitation, you can safely ignore this email.
        """
        
        # For development/testing, we'll log the email instead of sending it
        # In production, replace this with actual email sending logic
        
        if current_app.config.get('TESTING') or os.getenv('FLASK_ENV') == 'development':
            # Log the email for development
            current_app.logger.info(f"""
            =================================
            TEAM INVITATION EMAIL (DEV MODE)
            =================================
            To: {invited_email}
            Subject: {subject}
            Invitation URL: {invitation_url}
            Expires: {expires_at.strftime('%B %d, %Y at %I:%M %p')}
            =================================
            """)
            return {'success': True, 'method': 'logged', 'invitation_url': invitation_url}
        else:
            # Production email sending (implement with your preferred service)
            # Example using SMTP (you'd configure these environment variables):
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            if not all([smtp_server, smtp_username, smtp_password]):
                current_app.logger.warning("SMTP not configured, falling back to logging")
                current_app.logger.info(f"Invitation email for {invited_email}: {invitation_url}")
                return {'success': True, 'method': 'logged_fallback', 'invitation_url': invitation_url}
            
            # Create message
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_username
            msg['To'] = invited_email
            
            # Attach parts
            msg.attach(MimeText(text_body, 'plain'))
            msg.attach(MimeText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            return {'success': True, 'method': 'smtp'}
            
    except Exception as e:
        current_app.logger.error(f"Error sending invitation email: {e}")
        return {'success': False, 'error': str(e)}

def send_invitation_reminder_email(invitation):
    """
    Send a reminder email for pending invitations
    """
    # Implement reminder logic if needed
    pass

def send_invitation_accepted_email(inviter_email, invited_user_name, property_name, role):
    """
    Notify the inviter when someone accepts their invitation
    """
    try:
        subject = f"{invited_user_name} joined your {property_name} team!"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #10B981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Great News!</h1>
                </div>
                <div class="content">
                    <h2>Team Member Joined</h2>
                    <p><strong>{invited_user_name}</strong> has accepted your invitation and joined the <strong>{property_name}</strong> team as a <strong>{role}</strong>.</p>
                    <p>They now have access to the property management dashboard and can start helping you manage your property.</p>
                    <p>Welcome them to the team!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Log for development
        if current_app.config.get('TESTING') or os.getenv('FLASK_ENV') == 'development':
            current_app.logger.info(f"Invitation accepted notification: {invited_user_name} joined {property_name}")
            return {'success': True}
        
        # In production, send actual email
        return {'success': True}
        
    except Exception as e:
        current_app.logger.error(f"Error sending acceptance notification: {e}")
        return {'success': False, 'error': str(e)} 