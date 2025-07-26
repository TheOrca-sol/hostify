"""
Contract management routes
"""

from flask import Blueprint, request, jsonify, g, send_file, current_app
from ..models import db, Contract, Guest, MessageTemplate, ScheduledMessage, VerificationLink, Reservation, Property, ContractTemplate
from ..utils.auth import require_auth
from ..utils.database import get_user_by_firebase_uid
from ..utils.sms import send_sms
from ..utils.pdf_generator import generate_contract_pdf, generate_signed_contract_pdf
from datetime import datetime, timedelta, timezone
import uuid
import os
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import NotFound, Forbidden, BadRequest

contracts_bp = Blueprint('contracts', __name__)

@contracts_bp.route('', methods=['GET'])
@contracts_bp.route('/', methods=['GET'])
@require_auth
def get_contracts():
    """Get all contracts for the authenticated user"""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get contracts for user's properties with eager loading
        contracts = Contract.query.join(Guest).join(Reservation).join(Property).options(
            joinedload(Contract.guest),
            joinedload(Contract.reservation).joinedload(Reservation.property),
            joinedload(Contract.template)
        ).filter(
            Property.user_id == user['id']
        ).order_by(Contract.created_at.desc()).all()

        return jsonify({
            'success': True, 
            'contracts': [contract.to_dict() for contract in contracts]
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching contracts: {e}", exc_info=True)
        return jsonify({'success': False, 'error': "An unexpected error occurred"}), 500

@contracts_bp.route('/pending', methods=['GET'])
@require_auth
def get_pending_contracts():
    """Get all pending contracts for the authenticated user"""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        contracts = Contract.query.join(Guest).join(Reservation).join(Property).options(
            joinedload(Contract.guest).joinedload(Guest.reservation).joinedload(Reservation.property)
        ).filter(
            Property.user_id == user['id'],
            Contract.contract_status == 'generated'
        ).all()

        return jsonify({'success': True, 'contracts': [contract.to_dict() for contract in contracts]})
    except Exception as e:
        current_app.logger.error(f"Error fetching pending contracts: {e}", exc_info=True)
        return jsonify({'success': False, 'error': "An unexpected error occurred"}), 500

@contracts_bp.route('/<contract_id>', methods=['GET'])
@require_auth
def get_contract(contract_id):
    """Get a specific contract by its ID"""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        try:
            contract_uuid = uuid.UUID(contract_id)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid contract ID format'}), 400

        contract = Contract.query.options(
            joinedload(Contract.guest),
            joinedload(Contract.reservation).joinedload(Reservation.property)
        ).get(contract_uuid)

        if not contract:
            return jsonify({'success': False, 'error': 'Contract not found'}), 404

        # Verify ownership
        if str(contract.guest.reservation.property.user_id) != user['id']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403

        return jsonify({'success': True, 'contract': contract.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error fetching contract {contract_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': "An unexpected error occurred"}), 500

@contracts_bp.route('/sign/<token>', methods=['GET'])
def get_contract_by_token(token):
    """Get contract details for signing using a token"""
    try:
        # Find verification link
        verification_link = VerificationLink.query.filter_by(
            token=token,
            status='sent',
            contract_generated=True
        ).first()
        
        if not verification_link:
            return jsonify({'success': False, 'error': 'Invalid or expired signing link'}), 404
            
        # Check if link is expired
        if verification_link.expires_at < datetime.now(timezone.utc):
            verification_link.status = 'expired'
            db.session.commit()
            return jsonify({'success': False, 'error': 'Signing link has expired'}), 410
            
        # Get guest and contract
        guest = verification_link.guest
        if not guest:
            return jsonify({'success': False, 'error': 'Guest not found'}), 404
            
        contract = Contract.query.filter_by(
            reservation_id=guest.reservation_id,
            guest_id=guest.id
        ).first()
        
        if not contract:
            return jsonify({'success': False, 'error': 'Contract not found'}), 404

        if contract.contract_status == 'signed':
             return jsonify({
                'success': True,
                'contract': {
                    'id': str(contract.id),
                    'guest_name': guest.full_name,
                    'property_name': guest.reservation.property.name if guest.reservation and guest.reservation.property else '',
                    'check_in_date': guest.reservation.check_in.strftime('%B %d, %Y') if guest.reservation and guest.reservation.check_in else '',
                    'check_out_date': guest.reservation.check_out.strftime('%B %d, %Y') if guest.reservation and guest.reservation.check_out else '',
                    'content': "This contract has already been signed.",
                    'status': contract.contract_status
                }
            })
            
        # Get contract template and populate variables
        template = contract.template
        if not template:
            return jsonify({'success': False, 'error': 'Contract template not found'}), 404
            
        # Populate contract content with variables
        populated_content = populate_contract_variables(template.template_content, guest, contract)
        
        return jsonify({
            'success': True,
            'contract': {
                'id': str(contract.id),
                'guest_name': guest.full_name,
                'property_name': guest.reservation.property.name if guest.reservation and guest.reservation.property else '',
                'check_in_date': guest.reservation.check_in.strftime('%B %d, %Y') if guest.reservation and guest.reservation.check_in else '',
                'check_out_date': guest.reservation.check_out.strftime('%B %d, %Y') if guest.reservation and guest.reservation.check_out else '',
                'content': populated_content,
                'status': contract.contract_status
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching contract by token {token}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': "An unexpected error occurred."}), 500

@contracts_bp.route('/sign/<token>', methods=['POST'])
def sign_contract_by_token(token):
    """Handle contract signing by guest using token"""
    try:
        # Find verification link
        verification_link = VerificationLink.query.filter_by(
            token=token,
            status='sent',
            contract_generated=True
        ).first()
        
        if not verification_link:
            return jsonify({'success': False, 'error': 'Invalid or expired signing link'}), 404
            
        # Check if link is expired
        if verification_link.expires_at < datetime.now(timezone.utc):
            verification_link.status = 'expired'
            db.session.commit()
            return jsonify({'success': False, 'error': 'Signing link has expired'}), 410

        if verification_link.status == 'used':
            return jsonify({'success': False, 'error': 'This signing link has already been used.'}), 410
            
        # Get guest and contract
        guest = verification_link.guest
        contract = Contract.query.filter_by(
            reservation_id=guest.reservation_id,
            guest_id=guest.id
        ).first()
        
        if not contract:
            return jsonify({'success': False, 'error': 'Contract not found'}), 404
            
        # Get signature data from request
        data = request.get_json()
        signature_data = data.get('signature_data', {})
        
        # Update contract with signature
        contract.contract_status = 'signed'
        contract.signed_at = datetime.now(timezone.utc)
        contract.signature_data = signature_data
        contract.signature_ip = request.remote_addr
        
        # Update verification link
        verification_link.status = 'used'
        verification_link.used_at = datetime.now(timezone.utc)
        verification_link.contract_signed = True
        
        # Generate signed PDF
        template = contract.template
        populated_content = populate_contract_variables(template.template_content, guest, contract)
        
        # Create signed PDF
        try:
            pdf_path = generate_signed_contract_pdf(populated_content, guest, contract, signature_data)
            contract.signed_pdf_path = pdf_path
        except Exception as pdf_error:
            print(f"Error generating signed PDF: {pdf_error}")
            # Continue without PDF for now
            contract.signed_pdf_path = None
        
        # Send confirmation SMS to guest
        if guest.phone:
            confirmation_message = f"Thank you {guest.full_name}! Your contract for {guest.reservation.property.name} has been signed successfully."
            send_sms(guest.phone, confirmation_message)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contract signed successfully',
            'contract_id': str(contract.id)
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error signing contract with token {token}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': "An unexpected error occurred."}), 500

@contracts_bp.route('/download/<contract_id>', methods=['GET'])
@require_auth
def download_contract(contract_id):
    """Download signed contract PDF"""
    try:
        # Verify user first
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 401

        try:
            contract_uuid = uuid.UUID(contract_id)
        except ValueError:
            return jsonify({'error': 'Invalid contract ID format'}), 400

        # Load contract with all necessary relationships
        contract = Contract.query.options(
            joinedload(Contract.guest),
            joinedload(Contract.reservation).joinedload(Reservation.property),
            joinedload(Contract.template)
        ).get(contract_uuid)

        if not contract:
            return jsonify({'error': 'Contract not found'}), 404

        # Verify ownership immediately
        if str(contract.guest.reservation.property.user_id) != user['id']:
            return jsonify({'error': 'Access denied'}), 403

        # Check if contract is signed
        if contract.contract_status != 'signed':
            return jsonify({'error': 'Contract is not signed yet'}), 400

        # If PDF path is missing or file doesn't exist, regenerate it
        if not contract.signed_pdf_path or not os.path.exists(contract.signed_pdf_path):
            current_app.logger.info(f"Regenerating PDF for contract {contract_id}")
            
            if not contract.template:
                return jsonify({'error': 'Contract template not found'}), 404

            try:
                populated_content = populate_contract_variables(contract.template.template_content, contract.guest, contract)
                pdf_path = generate_signed_contract_pdf(populated_content, contract.guest, contract, contract.signature_data or {})
                contract.signed_pdf_path = pdf_path
                db.session.commit()
            except Exception as pdf_error:
                current_app.logger.error(f"Error regenerating PDF: {pdf_error}", exc_info=True)
                return jsonify({'error': 'Failed to generate contract PDF'}), 500

        # At this point, the PDF should exist
        if contract.signed_pdf_path and os.path.exists(contract.signed_pdf_path):
            response = send_file(
                contract.signed_pdf_path,
                as_attachment=True,
                download_name=f"contract_{contract_id}.pdf",
                mimetype='application/pdf'
            )
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        else:
            current_app.logger.error(f"PDF file missing after regeneration attempt: {contract.signed_pdf_path}")
            return jsonify({'error': 'Contract PDF could not be found or generated'}), 500

    except Exception as e:
        current_app.logger.error(f"Error downloading contract {contract_id}: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@contracts_bp.route('/regenerate-pdf/<contract_id>', methods=['POST'])
@require_auth
def regenerate_contract_pdf(contract_id):
    """Regenerate PDF for an existing signed contract"""
    try:
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        try:
            contract_uuid = uuid.UUID(contract_id)
        except ValueError:
            return jsonify({'error': 'Invalid contract ID format'}), 400

        contract = Contract.query.get(contract_uuid)
        if not contract:
            return jsonify({'error': 'Contract not found'}), 404
            
        # Verify ownership
        if str(contract.guest.reservation.property.user_id) != user['id']:
            return jsonify({'error': 'Access denied'}), 403
            
        # Check if contract is signed
        if contract.contract_status != 'signed':
            return jsonify({'error': 'Contract is not signed yet'}), 400
            
        # Generate new PDF with signature
        template = contract.template
        if not template:
            return jsonify({'error': 'Contract template not found'}), 404
            
        populated_content = populate_contract_variables(template.template_content, contract.guest, contract)
        
        # Generate new PDF with signature
        pdf_path = generate_signed_contract_pdf(populated_content, contract.guest, contract, contract.signature_data or {})
        contract.signed_pdf_path = pdf_path
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'PDF regenerated successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error regenerating PDF for contract {contract_id}: {e}", exc_info=True)
        return jsonify({'error': "An unexpected error occurred."}), 500

@contracts_bp.route('/generate-and-schedule-sms/<guest_id>', methods=['POST'])
@require_auth
def generate_contract_and_schedule_sms(guest_id):
    """Generate a contract and schedule an SMS to be sent to the guest"""
    try:
        # Get user record
        user = get_user_by_firebase_uid(g.user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get guest and verify ownership
        guest = Guest.query.options(joinedload(Guest.reservation).joinedload(Reservation.property)).filter_by(id=uuid.UUID(guest_id)).first()
        if not guest:
            return jsonify({'success': False, 'error': 'Guest not found'}), 404

        # Get reservation and property to verify ownership
        if not guest.reservation or not guest.reservation.property:
            return jsonify({'success': False, 'error': 'Invalid guest data'}), 400

        if str(guest.reservation.property.user_id) != user['id']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403

        # Check if property has a contract template
        if not guest.reservation.property.contract_template_id:
            return jsonify({
                'success': False, 
                'error': f'Property "{guest.reservation.property.name}" does not have a contract template assigned. Please set up a contract template first.'
            }), 400

        # Check if contract already exists for this guest
        existing_contract = Contract.query.filter_by(
            reservation_id=guest.reservation.id,
            guest_id=guest.id
        ).first()
        
        if existing_contract:
            return jsonify({
                'success': False, 
                'error': f'Contract already exists for guest {guest.full_name}'
            }), 400

        # Create a contract
        contract = Contract(
            reservation_id=guest.reservation.id,
            guest_id=guest.id,
            template_id=guest.reservation.property.contract_template_id,
            contract_status='generated'
        )
        db.session.add(contract)
        db.session.commit()

        # Create a verification link for the contract
        verification_link = VerificationLink(
            guest_id=guest.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            contract_generated=True
        )
        db.session.add(verification_link)
        db.session.commit()

        # Create a message template for the contract
        template = MessageTemplate(
            user_id=user['id'],
            name=f"Contract for {guest.full_name}",
            type='contract',
            subject='Your rental contract',
            content=f"Hello {guest.full_name}, please sign your rental contract: http://localhost:5173/sign-contract/{verification_link.token}",
            channels=['sms']
        )
        db.session.add(template)
        db.session.commit()

        # Schedule the SMS
        message = ScheduledMessage(
            template_id=template.id,
            reservation_id=guest.reservation.id,
            guest_id=guest.id,
            status='scheduled',
            scheduled_for=datetime.now(timezone.utc) + timedelta(minutes=1),
            channels=['sms']
        )
        db.session.add(message)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Contract generated and SMS scheduled successfully'})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in generate_contract_and_schedule_sms for guest {guest_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': "An unexpected error occurred while processing your request."
        }), 500

@contracts_bp.route('/generate-and-schedule-sms/<guest_id>', methods=['OPTIONS'])
def generate_contract_options(guest_id):
    """Handle OPTIONS request for contract generation endpoint"""
    return '', 200

def populate_contract_variables(content, guest, contract):
    """Populate contract template variables"""
    reservation = guest.reservation
    property = reservation.property if reservation else None
    
    # Calculate number of nights
    nights = 0
    if reservation and reservation.check_in and reservation.check_out:
        nights = (reservation.check_out - reservation.check_in).days
    
    # Get the actual rental rate from the property or reservation
    nightly_rate = 0
    if property and hasattr(property, 'price_per_night'):
        nightly_rate = property.price_per_night
    elif reservation and hasattr(reservation, 'nightly_rate'):
        nightly_rate = reservation.nightly_rate
    
    total_rent = nights * nightly_rate if nights > 0 and nightly_rate > 0 else 0
    
    variables = {
        'guest_name': guest.full_name or '',
        'guest_cin': guest.cin_or_passport or '',
        'guest_firstname': guest.full_name.split()[0] if guest.full_name else '',
        'guest_address': guest.address or '',
        'guest_phone': guest.phone or '',
        'guest_email': guest.email or '',
        'property_name': property.name if property else '',
        'property_address': property.address if property else '',
        'property_apartment_number': property.apartment_number if property and hasattr(property, 'apartment_number') else '',
        'check_in_date': reservation.check_in.strftime('%d/%m/%Y') if reservation and reservation.check_in else '',
        'check_out_date': reservation.check_out.strftime('%d/%m/%Y') if reservation and reservation.check_out else '',
        'number_of_nights': str(nights),
        'rent_per_night': str(nightly_rate),
        'total_rent': str(total_rent),
        'contract_date': datetime.now(timezone.utc).strftime('%d/%m/%Y'),
        'host_name': property.owner.name if property and property.owner else 'Host'
    }
    
    # Replace variables in content
    for key, value in variables.items():
        content = content.replace('{{' + key + '}}', str(value))
        content = content.replace('{' + key + '}', str(value))
    
    return content