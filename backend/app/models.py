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
            'settings': self.settings,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Property(db.Model):
    """Property information model"""
    __tablename__ = 'properties'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.Text, nullable=False)
    address = db.Column(db.Text, nullable=True)
    ical_url = db.Column(db.Text, nullable=True)
    sync_frequency = db.Column(db.Integer, nullable=False, default=3)  # Hours between syncs
    contract_template_id = db.Column(UUID(as_uuid=True), db.ForeignKey('contract_templates.id'), nullable=True)
    auto_verification = db.Column(db.Boolean, server_default=text('true'))  # Auto-send verification links
    auto_contract = db.Column(db.Boolean, server_default=text('true'))  # Auto-generate contracts
    last_sync = db.Column(db.DateTime(timezone=True), nullable=True)
    settings = db.Column(JSON, nullable=True)  # Property-specific settings
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    
    # Relationships
    reservations = db.relationship('Reservation', backref='property', lazy=True, cascade='all, delete-orphan')
    sync_logs = db.relationship('SyncLog', backref='property', lazy=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'name': self.name,
            'address': self.address,
            'ical_url': self.ical_url,
            'sync_frequency': self.sync_frequency,
            'contract_template_id': str(self.contract_template_id) if self.contract_template_id else None,
            'auto_verification': self.auto_verification,
            'auto_contract': self.auto_contract,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'settings': self.settings,
            'created_at': self.created_at.isoformat() if self.created_at else None
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
    messages = db.relationship('Message', backref='reservation', lazy=True)
    
    def to_dict(self):
        return {
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
    verification_status = db.Column(db.Text, nullable=False, default='pending')  # pending, verified, expired
    verified_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    
    # Relationships
    verification_links = db.relationship('VerificationLink', backref='guest', lazy=True)
    contracts = db.relationship('Contract', backref='guest', lazy=True)
    messages = db.relationship('Message', backref='guest', lazy=True)
    
    def to_dict(self):
        return {
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
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

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
        return {
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
    channel = db.Column(db.Text, nullable=False, default='email')  # email, sms, whatsapp
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
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'property_id': str(self.property_id),
            'sync_type': self.sync_type,
            'status': self.status,
            'events_processed': self.events_processed,
            'errors': self.errors,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        } 