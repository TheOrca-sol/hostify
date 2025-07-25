"""Add automation fields to message templates

Revision ID: 65615172ff73
Revises: 5fa6d58758ac
Create Date: 2025-07-20 08:12:11.029879

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '65615172ff73'
down_revision = '5fa6d58758ac'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('alembic_version')
    op.drop_index(op.f('idx_message_logs_scheduled_message_id'), table_name='message_logs')
    op.drop_index(op.f('idx_message_logs_status'), table_name='message_logs')
    op.add_column('message_templates', sa.Column('trigger_event', sa.Text(), nullable=True))
    op.add_column('message_templates', sa.Column('trigger_offset_value', sa.Integer(), nullable=True))
    op.add_column('message_templates', sa.Column('trigger_offset_unit', sa.Text(), nullable=True))
    op.add_column('message_templates', sa.Column('trigger_direction', sa.Text(), nullable=True))
    op.drop_index(op.f('idx_message_templates_property_id'), table_name='message_templates')
    op.drop_index(op.f('idx_message_templates_user_id'), table_name='message_templates')
    op.drop_index(op.f('idx_scheduled_messages_guest_id'), table_name='scheduled_messages')
    op.drop_index(op.f('idx_scheduled_messages_reservation_id'), table_name='scheduled_messages')
    op.drop_index(op.f('idx_scheduled_messages_status'), table_name='scheduled_messages')
    op.drop_index(op.f('idx_scheduled_messages_template_id'), table_name='scheduled_messages')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('message_templates', 'trigger_direction')
    op.drop_column('message_templates', 'trigger_offset_unit')
    op.drop_column('message_templates', 'trigger_offset_value')
    op.drop_column('message_templates', 'trigger_event')
    # ### end Alembic commands ###
