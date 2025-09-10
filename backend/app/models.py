"""
Database models for Hostify Property Management Platform
Complete rental management system with properties, reservations, contracts, and guest verification
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import text

db = SQLAlchemy()

class User(db.Model):
    """User/Host information model"""
    __tablename__ = 'users'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    firebase_uid = db.Column(db.Text, unique=True, nullable=False)  # Firebase UID
    email = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    phone = db.Column(db.Text, nullable=True)
    company_name = db.Column(db.Text, nullable=True)
    signature = db.Column(db.Text, nullable=True)  # Base64 encoded signature image
    settings = db.Column(JSON, nullable=True)  # User preferences and settings
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    
    # Relationships
    properties = db.relationship('Property', backref='owner', lazy=True, cascade='all, delete-orphan')
    contract_templates = db.relationship('ContractTemplate', backref='creator', lazy=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'firebase_uid': self.firebase_uid,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'company_name': self.company_name,
            'signature': self.signature,
            'settings': self.settings,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Property(db.Model):
    """Property information model"""
    __tablename__ = 'properties'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    team_id = db.Column(UUID(as_uuid=True), db.ForeignKey('teams.id'), nullable=True)  # Team that manages this property
    name = db.Column(db.Text, nullable=False)
    address = db.Column(db.Text, nullable=True)
    ical_url = db.Column(db.Text, nullable=True)
    sync_frequency = db.Column(db.Integer, nullable=False, default=3)  # Hours between syncs
    contract_template_id = db.Column(UUID(as_uuid=True), db.ForeignKey('contract_templates.id'), nullable=True)
    auto_verification = db.Column(db.Boolean, server_default=text('true'))  # Auto-send verification links
    auto_contract = db.Column(db.Boolean, server_default=text('true'))  # Auto-generate contracts
    auto_messaging = db.Column(db.Boolean, server_default=text('true')) # Auto-send messages
    last_sync = db.Column(db.DateTime(timezone=True), nullable=True)
    settings = db.Column(JSON, nullable=True)  # Property-specific settings
    is_active = db.Column(db.Boolean, server_default=text('true'))  # For soft delete
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    
    # Relationships
    reservations = db.relationship('Reservation', backref='property', lazy=True, cascade='all, delete-orphan')
    sync_logs = db.relationship('SyncLog', backref='property', lazy=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'team_id': str(self.team_id) if self.team_id else None,
            'name': self.name,
            'address': self.address,
            'ical_url': self.ical_url,
            'sync_frequency': self.sync_frequency,
            'contract_template_id': str(self.contract_template_id) if self.contract_template_id else None,
            'auto_verification': self.auto_verification,
            'auto_contract': self.auto_contract,
            'auto_messaging': self.auto_messaging,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'settings': self.settings,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # Include team information
            'team_name': self.team.name if self.team else None,
            'team_color': self.team.color if self.team else None
        }

class Reservation(db.Model):
    """Reservation/Booking model from calendar sync"""
    __tablename__ = 'reservations'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('properties.id'), nullable=False)
    external_id = db.Column(db.Text, nullable=True)  # ID from booking platform
    platform = db.Column(db.Text, nullable=True)  # airbnb, booking.com, vrbo, etc
    guest_name_partial = db.Column(db.Text, nullable=True)  # From calendar (often limited)
    phone_partial = db.Column(db.Text, nullable=True)  # Partial phone from calendar
    reservation_url = db.Column(db.Text, nullable=True)  # Link to platform reservation
    check_in = db.Column(db.DateTime(timezone=True), nullable=False)
    check_out = db.Column(db.DateTime(timezone=True), nullable=False)
    status = db.Column(db.Text, nullable=False, default='confirmed')  # confirmed, cancelled, blocked
    sync_source = db.Column(db.Text, nullable=True)  # Which sync brought this reservation
    raw_data = db.Column(JSON, nullable=True)  # Original calendar event data
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=datetime.utcnow)
    
    # Relationships
    guests = db.relationship('Guest', backref='reservation', lazy=True, cascade='all, delete-orphan')
    contracts = db.relationship('Contract', backref='reservation', lazy=True)
    messages = db.relationship('Message', backref='reservation', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        data = {
            'id': str(self.id),
            'property_id': str(self.property_id),
            'external_id': self.external_id,
            'platform': self.platform,
            'guest_name_partial': self.guest_name_partial,
            'phone_partial': self.phone_partial,
            'reservation_url': self.reservation_url,
            'check_in': self.check_in.isoformat() if self.check_in else None,
            'check_out': self.check_out.isoformat() if self.check_out else None,
            'status': self.status,
            'sync_source': self.sync_source,
            'raw_data': self.raw_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Add property information
        if self.property:
            data['property'] = {
                'id': str(self.property.id),
                'name': self.property.name,
                'address': self.property.address
            }
        
        return data

class Guest(db.Model):
    """Guest information from verification process"""
    __tablename__ = 'guests'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    reservation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('reservations.id'), nullable=False)
    verification_token = db.Column(db.Text, nullable=True)
    full_name = db.Column(db.Text, nullable=True)
    cin_or_passport = db.Column(db.Text, nullable=True)
    birthdate = db.Column(db.Date, nullable=True)
    nationality = db.Column(db.Text, nullable=True)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.Text, nullable=True)
    email = db.Column(db.Text, nullable=True)
    document_type = db.Column(db.Text, nullable=True)  # passport, national_id, etc
    id_document_path = db.Column(db.Text, nullable=True)  # Path to uploaded document
    verification_status = db.Column(db.Text, nullable=False, default='pending')  # pending, verified, expired, in_progress, failed
    verified_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    
    # KYC-related fields for Didit integration
    kyc_session_id = db.Column(db.Text, nullable=True)  # Didit session ID
    kyc_confidence_score = db.Column(db.Float, nullable=True)  # Face match confidence score (0-100)
    kyc_liveness_passed = db.Column(db.Boolean, nullable=True, default=False)  # Liveness detection result
    
    # Relationships
    verification_links = db.relationship('VerificationLink', backref='guest', lazy=True, cascade='all, delete-orphan')
    contracts = db.relationship('Contract', backref='guest', lazy=True)
    messages = db.relationship('Message', backref='guest', lazy=True)
    
    def to_dict(self):
        data = {
            'id': str(self.id),
            'reservation_id': str(self.reservation_id),
            'verification_token': self.verification_token,
            'full_name': self.full_name,
            'cin_or_passport': self.cin_or_passport,
            'birthdate': self.birthdate.isoformat() if self.birthdate else None,
            'nationality': self.nationality,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'document_type': self.document_type,
            'id_document_path': self.id_document_path,
            'verification_status': self.verification_status,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'verification_link_sent': len(self.verification_links) > 0,
            # KYC fields
            'kyc_session_id': self.kyc_session_id,
            'kyc_confidence_score': self.kyc_confidence_score,
            'kyc_liveness_passed': self.kyc_liveness_passed
        }
        
        # Add reservation and property information if reservation exists
        if self.reservation:
            data['reservation'] = self.reservation.to_dict()
            if self.reservation.property:
                data['property'] = self.reservation.property.to_dict()
                data['check_in'] = self.reservation.check_in.isoformat() if self.reservation.check_in else None
                data['check_out'] = self.reservation.check_out.isoformat() if self.reservation.check_out else None
        
        return data

class ContractTemplate(db.Model):
    """Contract templates for different properties/jurisdictions"""
    __tablename__ = 'contract_templates'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.Text, nullable=False)
    template_content = db.Column(db.Text, nullable=False)  # HTML/template content
    language = db.Column(db.Text, nullable=False, default='en')  # en, fr, ar
    legal_jurisdiction = db.Column(db.Text, nullable=True)  # morocco, france, etc
    is_default = db.Column(db.Boolean, server_default=text('false'))
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    
    # Relationships
    properties = db.relationship('Property', backref='contract_template', lazy=True)
    contracts = db.relationship('Contract', backref='template', lazy=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'name': self.name,
            'template_content': self.template_content,
            'language': self.language,
            'legal_jurisdiction': self.legal_jurisdiction,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Contract(db.Model):
    """Generated and signed contracts"""
    __tablename__ = 'contracts'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    reservation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('reservations.id'), nullable=False)
    guest_id = db.Column(UUID(as_uuid=True), db.ForeignKey('guests.id'), nullable=False)
    template_id = db.Column(UUID(as_uuid=True), db.ForeignKey('contract_templates.id'), nullable=False)
    generated_pdf_path = db.Column(db.Text, nullable=True)  # Path to generated contract
    signed_pdf_path = db.Column(db.Text, nullable=True)  # Path to signed contract
    signature_data = db.Column(JSON, nullable=True)  # Signature metadata
    contract_status = db.Column(db.Text, nullable=False, default='generated')  # generated, sent, signed, expired
    sent_at = db.Column(db.DateTime(timezone=True), nullable=True)
    signed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    signature_ip = db.Column(db.Text, nullable=True)  # IP where contract was signed
    audit_trail = db.Column(JSON, nullable=True)  # Complete audit log
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    
    def to_dict(self):
        data = {
            'id': str(self.id),
            'reservation_id': str(self.reservation_id),
            'guest_id': str(self.guest_id),
            'template_id': str(self.template_id),
            'generated_pdf_path': self.generated_pdf_path,
            'signed_pdf_path': self.signed_pdf_path,
            'signature_data': self.signature_data,
            'contract_status': self.contract_status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'signed_at': self.signed_at.isoformat() if self.signed_at else None,
            'signature_ip': self.signature_ip,
            'audit_trail': self.audit_trail,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        # Add guest information
        if self.guest:
            data['guest'] = {
                'id': str(self.guest.id),
                'full_name': self.guest.full_name,
                'email': self.guest.email,
                'phone': self.guest.phone
            }
        
        # Add reservation information
        if self.reservation:
            data['reservation'] = {
                'id': str(self.reservation.id),
                'check_in': self.reservation.check_in.isoformat() if self.reservation.check_in else None,
                'check_out': self.reservation.check_out.isoformat() if self.reservation.check_out else None,
                'status': self.reservation.status
            }
            
            # Add property information
            if self.reservation.property:
                data['property'] = {
                    'id': str(self.reservation.property.id),
                    'name': self.reservation.property.name,
                    'address': self.reservation.property.address
                }
        
        return data

class VerificationLink(db.Model):
    """Verification links sent to guests"""
    __tablename__ = 'verification_links'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    guest_id = db.Column(UUID(as_uuid=True), db.ForeignKey('guests.id'), nullable=False)
    token = db.Column(db.Text, unique=True, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    status = db.Column(db.Text, nullable=False, default='sent')  # sent, used, expired
    contract_generated = db.Column(db.Boolean, server_default=text('false'))
    contract_sent = db.Column(db.Boolean, server_default=text('false'))
    contract_signed = db.Column(db.Boolean, server_default=text('false'))
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    used_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'guest_id': str(self.guest_id),
            'token': self.token,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'status': self.status,
            'contract_generated': self.contract_generated,
            'contract_sent': self.contract_sent,
            'contract_signed': self.contract_signed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'used_at': self.used_at.isoformat() if self.used_at else None
        }

class Message(db.Model):
    """Messages sent to guests (future feature)"""
    __tablename__ = 'messages'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    reservation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('reservations.id'), nullable=False)
    guest_id = db.Column(UUID(as_uuid=True), db.ForeignKey('guests.id'), nullable=True)
    message_type = db.Column(db.Text, nullable=False)  # welcome, checkin, checkout, review
    template_id = db.Column(db.Text, nullable=True)  # Reference to message template
    content = db.Column(db.Text, nullable=False)
    channel = db.Column(db.Text, nullable=False, default='sms')  # sms
    sent_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    delivery_status = db.Column(db.Text, nullable=False, default='sent')  # sent, delivered, failed
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'reservation_id': str(self.reservation_id),
            'guest_id': str(self.guest_id) if self.guest_id else None,
            'message_type': self.message_type,
            'template_id': self.template_id,
            'content': self.content,
            'channel': self.channel,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivery_status': self.delivery_status
        }

class MessageTemplate(db.Model):
    """Message templates for automated communications"""
    __tablename__ = 'message_templates'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('properties.id'), nullable=True)
    name = db.Column(db.Text, nullable=False)
    template_type = db.Column(db.Text, nullable=False)  # 'verification', 'checkin', 'checkout', etc.
    subject = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.Text, nullable=False, server_default='en')
    channels = db.Column(db.ARRAY(db.Text), nullable=False, default=['sms'])  # ['sms']
    variables = db.Column(JSON, nullable=True)
    active = db.Column(db.Boolean, nullable=False, server_default=text('true'))
    
    # Automation fields
    trigger_event = db.Column(db.Text, nullable=True)  # e.g., 'check_in', 'check_out'
    trigger_offset_value = db.Column(db.Integer, nullable=True)
    trigger_offset_unit = db.Column(db.Text, nullable=True)  # e.g., 'days', 'hours'
    trigger_direction = db.Column(db.Text, nullable=True)  # e.g., 'before', 'after'

    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    
    # Relationships
    user = db.relationship('User', backref='message_templates', lazy=True)
    property = db.relationship('Property', backref='message_templates', lazy=True)
    scheduled_messages = db.relationship('ScheduledMessage', backref='template', lazy=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'property_id': str(self.property_id) if self.property_id else None,
            'name': self.name,
            'template_type': self.template_type,
            'subject': self.subject,
            'content': self.content,
            'language': self.language,
            'channels': self.channels,
            'variables': self.variables,
            'active': self.active,
            'trigger_event': self.trigger_event,
            'trigger_offset_value': self.trigger_offset_value,
            'trigger_offset_unit': self.trigger_offset_unit,
            'trigger_direction': self.trigger_direction,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ScheduledMessage(db.Model):
    """Scheduled messages for automated delivery"""
    __tablename__ = 'scheduled_messages'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    template_id = db.Column(UUID(as_uuid=True), db.ForeignKey('message_templates.id'), nullable=False)
    reservation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('reservations.id'), nullable=False)
    guest_id = db.Column(UUID(as_uuid=True), db.ForeignKey('guests.id'), nullable=False)
    scheduled_for = db.Column(db.DateTime(timezone=True), nullable=False)
    status = db.Column(db.Text, nullable=False, server_default='scheduled')  # scheduled, sent, cancelled
    channels = db.Column(db.ARRAY(db.Text), nullable=False)
    sent_at = db.Column(db.DateTime(timezone=True), nullable=True)
    delivery_status = db.Column(JSON, nullable=True)  # Status per channel
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    
    # Relationships
    reservation = db.relationship('Reservation', backref='scheduled_messages', lazy=True)
    guest = db.relationship('Guest', backref=db.backref('scheduled_messages', cascade='all, delete-orphan'), lazy=True)
    logs = db.relationship('MessageLog', backref='scheduled_message', lazy=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'template_id': str(self.template_id),
            'reservation_id': str(self.reservation_id),
            'guest_id': str(self.guest_id),
            'scheduled_for': self.scheduled_for.isoformat() if self.scheduled_for else None,
            'status': self.status,
            'channels': self.channels,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivery_status': self.delivery_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # Include related data
            'template': self.template.to_dict() if hasattr(self, 'template') and self.template else None,
            'guest': self.guest.to_dict() if self.guest else None,
            'reservation': self.reservation.to_dict() if self.reservation else None
        }

class MessageLog(db.Model):
    """Detailed message delivery logs"""
    __tablename__ = 'message_logs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    scheduled_message_id = db.Column(UUID(as_uuid=True), db.ForeignKey('scheduled_messages.id'), nullable=False)
    channel = db.Column(db.Text, nullable=False)  # email, sms, whatsapp
    status = db.Column(db.Text, nullable=False)  # sent, delivered, failed
    provider_message_id = db.Column(db.Text, nullable=True)  # ID from Twilio/SendGrid
    sent_at = db.Column(db.DateTime(timezone=True), nullable=True)
    delivered_at = db.Column(db.DateTime(timezone=True), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'scheduled_message_id': str(self.scheduled_message_id),
            'channel': self.channel,
            'status': self.status,
            'provider_message_id': self.provider_message_id,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SyncLog(db.Model):
    """Background sync operation logs"""
    __tablename__ = 'sync_logs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('properties.id'), nullable=False)
    sync_type = db.Column(db.Text, nullable=False, default='ical')  # ical, manual, api
    status = db.Column(db.Text, nullable=False)  # success, failed, partial
    events_processed = db.Column(db.Integer, nullable=False, default=0)
    errors = db.Column(JSON, nullable=True)  # Error details if any
    started_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    # created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))  # Temporarily commented out until migration
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'property_id': str(self.property_id),
            'sync_type': self.sync_type,
            'status': self.status,
            'events_processed': self.events_processed,
            'errors': self.errors,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.started_at.isoformat() if self.started_at else None  # Use started_at as fallback
        }

class PropertyTeamMember(db.Model):
    """Team members assigned to properties"""
    __tablename__ = 'property_team_members'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('properties.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.Text, nullable=False)  # 'cohost', 'cleaner', 'maintenance', 'assistant', 'agency'
    permissions = db.Column(JSON, nullable=True)  # Custom permissions for this property
    invited_by_user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    invited_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    accepted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    is_active = db.Column(db.Boolean, server_default=text('true'))
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    
    # Relationships
    property = db.relationship('Property', backref='team_members')
    user = db.relationship('User', foreign_keys=[user_id], backref='team_memberships')
    invited_by = db.relationship('User', foreign_keys=[invited_by_user_id])
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'property_id': str(self.property_id),
            'user_id': str(self.user_id),
            'role': self.role,
            'permissions': self.permissions,
            'invited_by_user_id': str(self.invited_by_user_id),
            'invited_at': self.invited_at.isoformat() if self.invited_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # Include related data
            'user_name': self.user.name if self.user else None,
            'user_email': self.user.email if self.user else None,
            'property_name': self.property.name if self.property else None,
            'invited_by_name': self.invited_by.name if self.invited_by else None
        }

class TeamInvitation(db.Model):
    """Invitations sent to join property teams"""
    __tablename__ = 'team_invitations'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('properties.id', ondelete='CASCADE'), nullable=False)
    inviter_user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    invited_email = db.Column(db.Text, nullable=True)  # Made optional for phone invitations
    invited_phone = db.Column(db.Text, nullable=True)  # Added for SMS invitations
    invitation_method = db.Column(db.Text, nullable=False, server_default=text("'email'"))  # 'email' or 'sms'
    role = db.Column(db.Text, nullable=False)
    permissions = db.Column(JSON, nullable=True)
    invitation_token = db.Column(db.Text, unique=True, nullable=False)
    status = db.Column(db.Text, server_default=text("'pending'"))  # 'pending', 'accepted', 'expired', 'revoked'
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    accepted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    
    # Relationships
    property = db.relationship('Property', backref='team_invitations')
    inviter = db.relationship('User', backref='sent_invitations')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'property_id': str(self.property_id),
            'inviter_user_id': str(self.inviter_user_id),
            'invited_email': self.invited_email,
            'invited_phone': self.invited_phone,
            'invitation_method': self.invitation_method,
            'role': self.role,
            'permissions': self.permissions,
            'invitation_token': self.invitation_token,
            'status': self.status,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # Include related data
            'property_name': self.property.name if self.property else None,
            'inviter_name': self.inviter.name if self.inviter else None
        } 

class PhoneVerification(db.Model):
    """Phone verification codes for SMS authentication"""
    __tablename__ = 'phone_verifications'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    phone_number = db.Column(db.Text, nullable=False)  # E.164 format
    verification_code = db.Column(db.Text, nullable=False)  # 6-digit code
    purpose = db.Column(db.Text, nullable=False)  # 'login', 'invitation_accept'
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)  # If linking to existing user
    invitation_token = db.Column(db.Text, nullable=True)  # If for team invitation
    is_verified = db.Column(db.Boolean, server_default=text('false'))
    attempts = db.Column(db.Integer, server_default=text('0'))  # Track failed attempts
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    verified_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    
    # Relationships
    user = db.relationship('User', backref='phone_verifications')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'phone_number': self.phone_number,
            'purpose': self.purpose,
            'user_id': str(self.user_id) if self.user_id else None,
            'invitation_token': self.invitation_token,
            'is_verified': self.is_verified,
            'attempts': self.attempts,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def is_expired(self):
        """Check if verification code has expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    def can_attempt(self):
        """Check if more attempts are allowed (max 3)"""
        return self.attempts < 3 and not self.is_expired() 

class Team(db.Model):
    """Team model for organizing property management"""
    __tablename__ = 'teams'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.Text, nullable=True)  # Hex color for UI
    settings = db.Column(JSON, nullable=True)
    is_active = db.Column(db.Boolean, server_default=text('true'))
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    updated_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    
    # Relationships
    organization = db.relationship('User', backref='teams')
    properties = db.relationship('Property', backref='team')
    team_members = db.relationship('TeamMember', backref='team', cascade='all, delete-orphan')
    team_invitations = db.relationship('TeamInvitationNew', backref='team', cascade='all, delete-orphan')
    performance_records = db.relationship('TeamPerformance', backref='team', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'organization_id': str(self.organization_id),
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'settings': self.settings,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # Include related data
            'organization_name': self.organization.name if self.organization else None,
            'properties_count': len([p for p in self.properties if p.is_active]) if self.properties else 0,
            'members_count': len([m for m in self.team_members if m.is_active]) if self.team_members else 0
        }

class TeamMember(db.Model):
    """Team members with role-based access to team resources"""
    __tablename__ = 'team_members'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    team_id = db.Column(UUID(as_uuid=True), db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.Text, nullable=False)  # 'manager', 'cleaner', 'maintenance', 'assistant'
    permissions = db.Column(JSON, nullable=True)
    invited_by_user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    invited_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    accepted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    is_active = db.Column(db.Boolean, server_default=text('true'))
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='team_memberships_new')
    invited_by = db.relationship('User', foreign_keys=[invited_by_user_id])
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'team_id': str(self.team_id),
            'user_id': str(self.user_id),
            'role': self.role,
            'permissions': self.permissions,
            'invited_by_user_id': str(self.invited_by_user_id),
            'invited_at': self.invited_at.isoformat() if self.invited_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # Include related data
            'user_name': self.user.name if self.user else None,
            'user_email': self.user.email if self.user else None,
            'user_phone': self.user.phone if self.user else None,
            'team_name': self.team.name if self.team else None,
            'invited_by_name': self.invited_by.name if self.invited_by else None
        }

class TeamInvitationNew(db.Model):
    """Team invitations for the new team-based system"""
    __tablename__ = 'team_invitations_new'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    team_id = db.Column(UUID(as_uuid=True), db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    inviter_user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    invited_email = db.Column(db.Text, nullable=True)
    invited_phone = db.Column(db.Text, nullable=True)
    invitation_method = db.Column(db.Text, nullable=False, server_default=text("'email'"))
    role = db.Column(db.Text, nullable=False)
    permissions = db.Column(JSON, nullable=True)
    invitation_token = db.Column(db.Text, unique=True, nullable=False)
    status = db.Column(db.Text, server_default=text("'pending'"))
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    accepted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    
    # Relationships
    inviter = db.relationship('User', backref='sent_team_invitations_new')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'team_id': str(self.team_id),
            'inviter_user_id': str(self.inviter_user_id),
            'invited_email': self.invited_email,
            'invited_phone': self.invited_phone,
            'invitation_method': self.invitation_method,
            'role': self.role,
            'permissions': self.permissions,
            'invitation_token': self.invitation_token,
            'status': self.status,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # Include related data
            'team_name': self.team.name if self.team else None,
            'inviter_name': self.inviter.name if self.inviter else None
        }

class TeamPerformance(db.Model):
    """Team performance metrics for analytics"""
    __tablename__ = 'team_performance'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    team_id = db.Column(UUID(as_uuid=True), db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    metrics = db.Column(JSON, nullable=False)  # All performance metrics as JSON
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'team_id': str(self.team_id),
            'date': self.date.isoformat() if self.date else None,
            'metrics': self.metrics,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # Include related data
            'team_name': self.team.name if self.team else None
        }