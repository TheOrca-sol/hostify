"""add_smart_lock_tables

Revision ID: 3553ca96884a
Revises: 54dc17813a9c
Create Date: 2025-09-23 04:01:24.358993

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '3553ca96884a'
down_revision = '54dc17813a9c'
branch_labels = None
depends_on = None


def upgrade():
    # Create smart_locks table
    op.create_table('smart_locks',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('property_id', sa.UUID(), nullable=False),
        sa.Column('ttlock_id', sa.String(255), nullable=False),
        sa.Column('lock_name', sa.String(255), nullable=False),
        sa.Column('gateway_mac', sa.String(255), nullable=True),
        sa.Column('lock_mac', sa.String(255), nullable=False),
        sa.Column('lock_version', sa.String(100), nullable=True),
        sa.Column('battery_level', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ttlock_id')
    )

    # Create access_codes table
    op.create_table('access_codes',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('reservation_id', sa.UUID(), nullable=False),
        sa.Column('smart_lock_id', sa.UUID(), nullable=False),
        sa.Column('passcode', sa.String(20), nullable=True),
        sa.Column('passcode_id', sa.String(255), nullable=True),
        sa.Column('access_type', sa.String(50), nullable=False, server_default='temporary'),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('is_one_time', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_usage', sa.Integer(), nullable=True),
        sa.Column('guest_phone', sa.String(20), nullable=True),
        sa.Column('guest_email', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['reservation_id'], ['reservations.id'], ),
        sa.ForeignKeyConstraint(['smart_lock_id'], ['smart_locks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create access_logs table for tracking lock usage
    op.create_table('access_logs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('smart_lock_id', sa.UUID(), nullable=False),
        sa.Column('access_code_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),  # unlock, lock, failed_attempt
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('user_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['smart_lock_id'], ['smart_locks.id'], ),
        sa.ForeignKeyConstraint(['access_code_id'], ['access_codes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('access_logs')
    op.drop_table('access_codes')
    op.drop_table('smart_locks')
