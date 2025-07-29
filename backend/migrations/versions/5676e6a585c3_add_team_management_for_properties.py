"""Add team management for properties

Revision ID: 5676e6a585c3
Revises: 1d690888761f
Create Date: 2025-07-29 01:28:28.358782

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5676e6a585c3'
down_revision = '1d690888761f'
branch_labels = None
depends_on = None


def upgrade():
    # Create property_team_members table
    op.create_table('property_team_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('property_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('permissions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('invited_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invited_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['invited_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index('idx_property_team_members_property_id', 'property_team_members', ['property_id'])
    op.create_index('idx_property_team_members_user_id', 'property_team_members', ['user_id'])
    op.create_index('idx_property_team_members_active', 'property_team_members', ['is_active'])
    
    # Create team_invitations table
    op.create_table('team_invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('property_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('inviter_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invited_email', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('permissions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('invitation_token', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['inviter_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invitation_token')
    )
    
    # Create indexes for team_invitations
    op.create_index('idx_team_invitations_property_id', 'team_invitations', ['property_id'])
    op.create_index('idx_team_invitations_email', 'team_invitations', ['invited_email'])
    op.create_index('idx_team_invitations_token', 'team_invitations', ['invitation_token'])
    op.create_index('idx_team_invitations_status', 'team_invitations', ['status'])


def downgrade():
    # Drop indexes first
    op.drop_index('idx_team_invitations_status', table_name='team_invitations')
    op.drop_index('idx_team_invitations_token', table_name='team_invitations')
    op.drop_index('idx_team_invitations_email', table_name='team_invitations')
    op.drop_index('idx_team_invitations_property_id', table_name='team_invitations')
    
    op.drop_index('idx_property_team_members_active', table_name='property_team_members')
    op.drop_index('idx_property_team_members_user_id', table_name='property_team_members')
    op.drop_index('idx_property_team_members_property_id', table_name='property_team_members')
    
    # Drop tables
    op.drop_table('team_invitations')
    op.drop_table('property_team_members')
