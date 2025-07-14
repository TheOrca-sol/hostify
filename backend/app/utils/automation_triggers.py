
import logging

from app.models import db, Contract, MessageTemplate, ContractTemplate
from datetime import datetime, timedelta

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
