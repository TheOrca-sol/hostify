"""add_signature_field_to_users

Revision ID: 2b146e4910bf
Revises: 5676e6a585c3
Create Date: 2025-07-29 02:54:08.650290

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2b146e4910bf'
down_revision = '5676e6a585c3'
branch_labels = None
depends_on = None


def upgrade():
    # Add signature column to users table
    op.add_column('users', sa.Column('signature', sa.Text(), nullable=True))


def downgrade():
    # Remove signature column from users table
    op.drop_column('users', 'signature')
