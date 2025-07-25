"""Remove subject column from MessageTemplate

Revision ID: 1d690888761f
Revises: 02c87f6ac692
Create Date: 2025-07-21 04:12:08.039729

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1d690888761f'
down_revision = '02c87f6ac692'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('alembic_version')
    op.drop_index(op.f('idx_message_logs_scheduled_message_id'), table_name='message_logs')
    op.drop_index(op.f('idx_message_logs_status'), table_name='message_logs')
    op.drop_index(op.f('idx_message_templates_property_id'), table_name='message_templates')
    op.drop_index(op.f('idx_message_templates_user_id'), table_name='message_templates')
    op.drop_column('message_templates', 'subject')
    op.drop_index(op.f('idx_scheduled_messages_guest_id'), table_name='scheduled_messages')
    op.drop_index(op.f('idx_scheduled_messages_reservation_id'), table_name='scheduled_messages')
    op.drop_index(op.f('idx_scheduled_messages_status'), table_name='scheduled_messages')
    op.drop_index(op.f('idx_scheduled_messages_template_id'), table_name='scheduled_messages')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('idx_scheduled_messages_template_id'), 'scheduled_messages', ['template_id'], unique=False)
    op.create_index(op.f('idx_scheduled_messages_status'), 'scheduled_messages', ['status'], unique=False)
    op.create_index(op.f('idx_scheduled_messages_reservation_id'), 'scheduled_messages', ['reservation_id'], unique=False)
    op.create_index(op.f('idx_scheduled_messages_guest_id'), 'scheduled_messages', ['guest_id'], unique=False)
    op.add_column('message_templates', sa.Column('subject', sa.TEXT(), autoincrement=False, nullable=True))
    op.create_index(op.f('idx_message_templates_user_id'), 'message_templates', ['user_id'], unique=False)
    op.create_index(op.f('idx_message_templates_property_id'), 'message_templates', ['property_id'], unique=False)
    op.create_index(op.f('idx_message_logs_status'), 'message_logs', ['status'], unique=False)
    op.create_index(op.f('idx_message_logs_scheduled_message_id'), 'message_logs', ['scheduled_message_id'], unique=False)
    op.create_table('alembic_version',
    sa.Column('version_num', sa.VARCHAR(length=32), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('version_num', name=op.f('alembic_version_pkc'))
    )
    # ### end Alembic commands ###
