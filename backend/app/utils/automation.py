from datetime import datetime, timedelta
from ..models import db, MessageTemplate, ScheduledMessage, Guest

class AutomationService:
    @staticmethod
    def schedule_messages_for_guest(guest_id):
        """
        Finds all automated message templates and schedules them for a specific guest.
        This is the master trigger for the automation sequence.
        """
        try:
            guest = Guest.query.get(guest_id)
            if not guest or not guest.reservation:
                print(f"Automation Error: Guest or reservation not found for guest_id {guest_id}")
                return []

            user_id = guest.reservation.property.user_id
            
            # Find all active, automated templates for this user
            automated_templates = MessageTemplate.query.filter_by(
                user_id=user_id,
                active=True
            ).filter(MessageTemplate.trigger_event.isnot(None)).all()

            if not automated_templates:
                print(f"No automated templates found for user {user_id}.")
                return []

            scheduled_messages = []
            for template in automated_templates:
                # Calculate the scheduled time
                base_time = None
                if template.trigger_event == 'check_in':
                    base_time = guest.reservation.check_in
                elif template.trigger_event == 'check_out':
                    base_time = guest.reservation.check_out
                
                if not base_time:
                    continue

                offset = timedelta()
                if template.trigger_offset_unit == 'days':
                    offset = timedelta(days=template.trigger_offset_value)
                elif template.trigger_offset_unit == 'hours':
                    offset = timedelta(hours=template.trigger_offset_value)

                scheduled_for = base_time - offset if template.trigger_direction == 'before' else base_time + offset

                # Avoid scheduling messages in the past
                if scheduled_for < datetime.utcnow().replace(tzinfo=scheduled_for.tzinfo):
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

                # Create the scheduled message
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
            print(f"Successfully scheduled {len(scheduled_messages)} messages for guest {guest_id}.")
            return [str(msg.id) for msg in scheduled_messages]

        except Exception as e:
            db.session.rollback()
            print(f"Error in schedule_messages_for_guest: {e}")
            return []
