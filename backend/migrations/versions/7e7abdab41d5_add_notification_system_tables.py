"""add notification system tables

Revision ID: 7e7abdab41d5
Revises: f6802c217390
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7e7abdab41d5'
down_revision = 'f6802c217390'
branch_labels = None
depends_on = None

def upgrade():
    # Create message_templates table
    op.create_table('message_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('property_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('subject', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('language', sa.Text(), server_default='en', nullable=False),
        sa.Column('channels', postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column('variables', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create scheduled_messages table
    op.create_table('scheduled_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reservation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('guest_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Text(), server_default='scheduled', nullable=False),
        sa.Column('channels', postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivery_status', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['guest_id'], ['guests.id'], ),
        sa.ForeignKeyConstraint(['reservation_id'], ['reservations.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['message_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create message_logs table
    op.create_table('message_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('scheduled_message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('provider_message_id', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['scheduled_message_id'], ['scheduled_messages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for better query performance
    op.create_index('idx_message_templates_user_id', 'message_templates', ['user_id'])
    op.create_index('idx_message_templates_property_id', 'message_templates', ['property_id'])
    op.create_index('idx_message_templates_type', 'message_templates', ['type'])
    op.create_index('idx_scheduled_messages_template_id', 'scheduled_messages', ['template_id'])
    op.create_index('idx_scheduled_messages_reservation_id', 'scheduled_messages', ['reservation_id'])
    op.create_index('idx_scheduled_messages_guest_id', 'scheduled_messages', ['guest_id'])
    op.create_index('idx_scheduled_messages_status', 'scheduled_messages', ['status'])
    op.create_index('idx_message_logs_scheduled_message_id', 'message_logs', ['scheduled_message_id'])
    op.create_index('idx_message_logs_status', 'message_logs', ['status'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_message_logs_status')
    op.drop_index('idx_message_logs_scheduled_message_id')
    op.drop_index('idx_scheduled_messages_status')
    op.drop_index('idx_scheduled_messages_guest_id')
    op.drop_index('idx_scheduled_messages_reservation_id')
    op.drop_index('idx_scheduled_messages_template_id')
    op.drop_index('idx_message_templates_type')
    op.drop_index('idx_message_templates_property_id')
    op.drop_index('idx_message_templates_user_id')

    # Drop tables
    op.drop_table('message_logs')
    op.drop_table('scheduled_messages')
    op.drop_table('message_templates')
