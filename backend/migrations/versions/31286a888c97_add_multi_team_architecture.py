"""add multi-team architecture

Revision ID: 31286a888c97
Revises: 35ac2fed4258
Create Date: 2025-08-09 21:50:51.565419

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '31286a888c97'
down_revision = '35ac2fed4258'
branch_labels = None
depends_on = None


def upgrade():
    # Create teams table
    op.create_table('teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),  # Hex color for UI
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for teams
    op.create_index('idx_teams_organization_id', 'teams', ['organization_id'])
    op.create_index('idx_teams_active', 'teams', ['is_active'])
    
    # Add team_id and is_active columns to properties table
    op.add_column('properties', sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('properties', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    op.create_foreign_key('fk_properties_team_id', 'properties', 'teams', ['team_id'], ['id'])
    op.create_index('idx_properties_team_id', 'properties', ['team_id'])
    op.create_index('idx_properties_active', 'properties', ['is_active'])
    
    # Create team_members table (replaces property_team_members for team-based structure)
    op.create_table('team_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),  # 'manager', 'cleaner', 'maintenance', 'assistant'
        sa.Column('permissions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('invited_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invited_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['invited_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for team_members
    op.create_index('idx_team_members_team_id', 'team_members', ['team_id'])
    op.create_index('idx_team_members_user_id', 'team_members', ['user_id'])
    op.create_index('idx_team_members_active', 'team_members', ['is_active'])
    op.create_index('idx_team_members_role', 'team_members', ['role'])
    
    # Create team_invitations_new table (team-based invitations)
    op.create_table('team_invitations_new',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('inviter_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invited_email', sa.String(255), nullable=True),
        sa.Column('invited_phone', sa.String(20), nullable=True),
        sa.Column('invitation_method', sa.String(10), nullable=False, server_default=sa.text("'email'")),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('permissions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('invitation_token', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['inviter_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invitation_token')
    )
    
    # Create indexes for team_invitations_new
    op.create_index('idx_team_invitations_new_team_id', 'team_invitations_new', ['team_id'])
    op.create_index('idx_team_invitations_new_email', 'team_invitations_new', ['invited_email'])
    op.create_index('idx_team_invitations_new_token', 'team_invitations_new', ['invitation_token'])
    op.create_index('idx_team_invitations_new_status', 'team_invitations_new', ['status'])
    
    # Create team_performance table for analytics
    op.create_table('team_performance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('metrics', postgresql.JSON(astext_type=sa.Text()), nullable=False),  # All performance metrics
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for team_performance
    op.create_index('idx_team_performance_team_id', 'team_performance', ['team_id'])
    op.create_index('idx_team_performance_date', 'team_performance', ['date'])
    op.create_index('idx_team_performance_team_date', 'team_performance', ['team_id', 'date'])


def downgrade():
    # Drop indexes and tables in reverse order
    op.drop_index('idx_team_performance_team_date', table_name='team_performance')
    op.drop_index('idx_team_performance_date', table_name='team_performance')
    op.drop_index('idx_team_performance_team_id', table_name='team_performance')
    op.drop_table('team_performance')
    
    op.drop_index('idx_team_invitations_new_status', table_name='team_invitations_new')
    op.drop_index('idx_team_invitations_new_token', table_name='team_invitations_new')
    op.drop_index('idx_team_invitations_new_email', table_name='team_invitations_new')
    op.drop_index('idx_team_invitations_new_team_id', table_name='team_invitations_new')
    op.drop_table('team_invitations_new')
    
    op.drop_index('idx_team_members_role', table_name='team_members')
    op.drop_index('idx_team_members_active', table_name='team_members')
    op.drop_index('idx_team_members_user_id', table_name='team_members')
    op.drop_index('idx_team_members_team_id', table_name='team_members')
    op.drop_table('team_members')
    
    op.drop_index('idx_properties_active', table_name='properties')
    op.drop_index('idx_properties_team_id', table_name='properties')
    op.drop_constraint('fk_properties_team_id', 'properties', type_='foreignkey')
    op.drop_column('properties', 'is_active')
    op.drop_column('properties', 'team_id')
    
    op.drop_index('idx_teams_active', table_name='teams')
    op.drop_index('idx_teams_organization_id', table_name='teams')
    op.drop_table('teams')
