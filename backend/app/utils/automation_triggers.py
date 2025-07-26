import logging

from app.models import db, Contract, MessageTemplate, ContractTemplate
from datetime import datetime, timedelta
from app.utils.automation import AutomationService
from app.models import VerificationLink
from datetime import timezone

def trigger_post_reservation_actions(reservation):
    # 1. Generate a pending contract
    logging.info(f"Checking auto_contract for property {reservation.property.id}")
    if reservation.property.auto_contract:
        logging.info("auto_contract is enabled, searching for a contract template.")
        # Find the contract template for the property, falling back to the user's default
        if reservation.property.contract_template_id:
            template = ContractTemplate.query.get(reservation.property.contract_template_id)
            logging.info(f"Found property-specific template: {template.id}")
        else:
            template = ContractTemplate.query.filter_by(
                user_id=reservation.property.user_id,
                is_default=True
            ).first()
            if template:
                logging.info(f"Found default user template: {template.id}")
            else:
                logging.warning("No contract template found for the property or user.")

        if template:
            contract = Contract(
                reservation_id=reservation.id,
                guest_id=reservation.guests[0].id if reservation.guests else None,
                template_id=template.id,
                contract_status='pending'
            )
            db.session.add(contract)
            logging.info(f"Created pending contract for reservation {reservation.id}")
    else:
        logging.info("auto_contract is disabled for this property.")

    # 2. Schedule initial messages
    logging.info(f"Checking auto_messaging for property {reservation.property.id}")
    if reservation.property.auto_messaging:
        logging.info("auto_messaging is enabled, searching for a 'Welcome Message' template.")
        # Schedule a welcome message
        welcome_template = MessageTemplate.query.filter_by(
            property_id=reservation.property_id,
            name='Welcome Message'
        ).first()

        if welcome_template:
            message = Message(
                reservation_id=reservation.id,
                template_id=welcome_template.id,
                status='scheduled',
                scheduled_for=reservation.check_in - timedelta(days=1)
            )
            db.session.add(message)
            logging.info(f"Scheduled 'Welcome Message' for reservation {reservation.id}")
        else:
            logging.warning("No 'Welcome Message' template found for this property.")
    else:
        logging.info("auto_messaging is disabled for this property.")

    db.session.commit()


def trigger_post_verification_actions(guest):
    """Trigger actions after guest verification is completed"""
    try:
        # 1. Update contract with guest details and generate if auto_contract is enabled
        contract = Contract.query.filter_by(reservation_id=guest.reservation_id).first()
        if contract:
            contract.guest_id = guest.id
            contract.contract_status = 'ready_to_send'
            logging.info(f"Updated contract {contract.id} with guest details.")
        else:
            # Create new contract if auto_contract is enabled
            if guest.reservation.property.auto_contract:
                logging.info("Auto-contract enabled, creating new contract.")
                template = None
                if guest.reservation.property.contract_template_id:
                    template = ContractTemplate.query.get(guest.reservation.property.contract_template_id)
                else:
                    template = ContractTemplate.query.filter_by(
                        user_id=guest.reservation.property.user_id,
                        is_default=True
                    ).first()
                
                if template:
                    contract = Contract(
                        reservation_id=guest.reservation_id,
                        guest_id=guest.id,
                        template_id=template.id,
                        contract_status='ready_to_send'
                    )
                    db.session.add(contract)
                    logging.info(f"Created new contract for guest {guest.id}")
                else:
                    logging.warning("No contract template found for property or user.")

        # 2. Schedule verification-dependent messages
        logging.info(f"Scheduling verification-dependent messages for guest {guest.id}")
        AutomationService.schedule_messages_for_event(guest.id, 'verification')

        # 3. Generate and send contract signing link if contract is ready
        if contract and contract.contract_status == 'ready_to_send':
            logging.info(f"Generating contract signing link for contract {contract.id}")
            # Generate signing token
            import secrets
            signing_token = secrets.token_urlsafe(32)
            
            # Create verification link for contract signing
            verification_link = VerificationLink(
                guest_id=guest.id,
                token=signing_token,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                status='sent',
                contract_generated=True
            )
            db.session.add(verification_link)
            
            # Update contract status
            contract.contract_status = 'sent_for_signing'
            contract.sent_at = datetime.now(timezone.utc)
            
            # Send contract signing SMS
            if guest.phone:
                signing_url = f"http://localhost:3000/contract/sign/{signing_token}"
                contract_message = f"Hello {guest.full_name}, your rental contract is ready for signing: {signing_url}"
                
                from ..utils.sms import send_sms
                sms_result = send_sms(guest.phone, contract_message)
                if sms_result['success']:
                    logging.info(f"Contract signing SMS sent to {guest.phone}")
                else:
                    logging.error(f"Failed to send contract signing SMS: {sms_result.get('error')}")

        db.session.commit()
        logging.info(f"Successfully completed post-verification actions for guest {guest.id}")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in trigger_post_verification_actions: {e}")
        raise