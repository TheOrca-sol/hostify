from datetime import datetime, timedelta, timezone
from ..models import db, MessageTemplate, ScheduledMessage, Guest, Contract, ContractTemplate

class AutomationService:
    @staticmethod
    def schedule_messages_for_event(guest_id, event_type):
        """
        Schedules messages for a specific event type (e.g., 'check_in', 'verification').
        """
        try:
            guest = Guest.query.get(guest_id)
            if not guest or not guest.reservation:
                print(f"Automation Error: Guest or reservation not found for guest_id {guest_id}")
                return []

            user_id = guest.reservation.property.user_id
            
            # Find templates for the specific event
            templates = MessageTemplate.query.filter_by(
                user_id=user_id,
                active=True,
                trigger_event=event_type
            ).all()

            if not templates:
                print(f"No automated templates found for event '{event_type}' for user {user_id}.")
                return []

            scheduled_messages = []
            for template in templates:
                base_time = None
                if template.trigger_event == 'check_in':
                    base_time = guest.reservation.check_in
                elif template.trigger_event == 'check_out':
                    base_time = guest.reservation.check_out
                elif template.trigger_event == 'verification':
                    # For verification, schedule immediately
                    base_time = datetime.now(timezone.utc)
                
                if not base_time:
                    continue

                scheduled_for = base_time
                if template.trigger_event != 'verification':
                    offset = timedelta()
                    if template.trigger_offset_unit == 'days':
                        offset = timedelta(days=template.trigger_offset_value)
                    elif template.trigger_offset_unit == 'hours':
                        offset = timedelta(hours=template.trigger_offset_value)
                    
                    scheduled_for = base_time - offset if template.trigger_direction == 'before' else base_time + offset

                # Avoid scheduling messages in the past
                if scheduled_for < datetime.now(timezone.utc):
                    print(f"Skipping template '{template.name}' as its scheduled time is in the past.")
                    continue

                # Avoid creating duplicate scheduled messages
                existing_scheduled = ScheduledMessage.query.filter_by(
                    template_id=template.id,
                    guest_id=guest.id
                ).first()

                if existing_scheduled:
                    print(f"Message for template '{template.name}' already scheduled for this guest. Skipping.")
                    continue

                new_scheduled_message = ScheduledMessage(
                    template_id=template.id,
                    reservation_id=guest.reservation_id,
                    guest_id=guest.id,
                    scheduled_for=scheduled_for,
                    status='scheduled',
                    channels=template.channels
                )
                db.session.add(new_scheduled_message)
                scheduled_messages.append(new_scheduled_message)

            db.session.commit()
            print(f"Successfully scheduled {len(scheduled_messages)} messages for event '{event_type}' for guest {guest_id}.")
            return [str(msg.id) for msg in scheduled_messages]

        except Exception as e:
            db.session.rollback()
            print(f"Error in schedule_messages_for_event: {e}")
            return []

    @staticmethod
    def schedule_messages_for_guest(guest_id):
        """
        Schedules all applicable messages for a guest based on check-in and check-out.
        """
        check_in_ids = AutomationService.schedule_messages_for_event(guest_id, 'check_in')
        check_out_ids = AutomationService.schedule_messages_for_event(guest_id, 'check_out')
        
        # Also create contract if needed
        AutomationService.create_contract_for_guest(guest_id)
        
        return check_in_ids + check_out_ids
    
    @staticmethod
    def create_contract_for_guest(guest_id):
        """
        Create a contract for a guest if property has auto_contract enabled
        """
        try:
            guest = Guest.query.get(guest_id)
            if not guest or not guest.reservation:
                print(f"Contract Creation Error: Guest or reservation not found for guest_id {guest_id}")
                return None

            property = guest.reservation.property
            
            # Check if property has auto contract enabled
            if not property.auto_contract:
                print(f"Auto contract disabled for property {property.name}")
                return None
                
            # Check if contract already exists
            existing_contract = Contract.query.filter_by(
                reservation_id=guest.reservation_id,
                guest_id=guest.id
            ).first()
            
            if existing_contract:
                print(f"Contract already exists for guest {guest_id}")
                return str(existing_contract.id)
            
            # Get contract template for the property
            template = None
            if property.contract_template_id:
                template = ContractTemplate.query.get(property.contract_template_id)
            
            if not template:
                # Get default template for the user
                template = ContractTemplate.query.filter_by(
                    user_id=property.user_id,
                    is_default=True
                ).first()
            
            if not template:
                print(f"No contract template found for property {property.name}")
                return None
            
            # Create contract
            contract = Contract(
                template_id=template.id,
                reservation_id=guest.reservation_id,
                guest_id=guest.id,
                status='pending'
            )
            
            db.session.add(contract)
            db.session.commit()
            
            print(f"Successfully created contract {contract.id} for guest {guest_id}")
            return str(contract.id)
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating contract for guest {guest_id}: {e}")
            return None
