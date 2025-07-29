"""add_phone_verification_and_sms_invitations

Revision ID: 35ac2fed4258
Revises: 2b146e4910bf
Create Date: 2025-07-29 08:02:13.485412

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '35ac2fed4258'
down_revision = '2b146e4910bf'
branch_labels = None
depends_on = None


def upgrade():
    # Create phone_verifications table
    op.create_table('phone_verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('phone_number', sa.Text(), nullable=False),
        sa.Column('verification_code', sa.Text(), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('invitation_token', sa.Text(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for phone_verifications
    op.create_index('ix_phone_verifications_phone_number', 'phone_verifications', ['phone_number'])
    op.create_index('ix_phone_verifications_purpose', 'phone_verifications', ['purpose'])
    op.create_index('ix_phone_verifications_expires_at', 'phone_verifications', ['expires_at'])
    
    # Add new columns to team_invitations table
    op.add_column('team_invitations', sa.Column('invited_phone', sa.Text(), nullable=True))
    op.add_column('team_invitations', sa.Column('invitation_method', sa.Text(), nullable=False, server_default=sa.text("'email'")))
    
    # Make invited_email nullable for SMS invitations
    op.alter_column('team_invitations', 'invited_email', nullable=True)


def downgrade():
    # Remove new columns from team_invitations
    op.drop_column('team_invitations', 'invitation_method')
    op.drop_column('team_invitations', 'invited_phone')
    
    # Revert invited_email to nullable=False
    op.alter_column('team_invitations', 'invited_email', nullable=False)
    
    # Drop phone_verifications table
    op.drop_index('ix_phone_verifications_expires_at', table_name='phone_verifications')
    op.drop_index('ix_phone_verifications_purpose', table_name='phone_verifications')
    op.drop_index('ix_phone_verifications_phone_number', table_name='phone_verifications')
    op.drop_table('phone_verifications')
