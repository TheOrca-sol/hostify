"""consolidate bookings into reservations

Revision ID: consolidate_bookings
Revises: 3de0804e8301
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'consolidate_bookings'
down_revision = '3de0804e8301'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Add missing columns to reservations
    op.add_column('reservations', sa.Column('guest_email', sa.Text(), nullable=True))
    op.add_column('reservations', sa.Column('total_guests', sa.Integer(), nullable=True))
    op.add_column('reservations', sa.Column('notes', sa.Text(), nullable=True))

    # 2. Add temporary property_id to bookings
    op.add_column('bookings', sa.Column('property_id', postgresql.UUID(), nullable=True))
    op.create_foreign_key('bookings_property_id_fkey', 'bookings', 'properties', ['property_id'], ['id'])

    # 3. First update property names in bookings to match properties table
    op.execute("""
        UPDATE bookings 
        SET property_name = 'anfa' 
        WHERE property_name = 'ain diab'
    """)

    # 4. Update property_id in bookings
    op.execute("""
        UPDATE bookings b
        SET property_id = (
            SELECT id FROM properties p 
            WHERE p.name = b.property_name 
            LIMIT 1
        )
    """)

    # 5. Migrate data from bookings to reservations
    op.execute("""
        INSERT INTO reservations (
            property_id,
            external_id,
            platform,
            guest_name_partial,
            phone_partial,
            guest_email,
            check_in,
            check_out,
            status,
            total_guests,
            notes,
            raw_data,
            created_at,
            updated_at
        )
        SELECT 
            property_id,
            external_id,
            booking_source as platform,
            guest_name as guest_name_partial,
            guest_phone as phone_partial,
            guest_email,
            check_in,
            check_out,
            status,
            total_guests,
            notes,
            raw_data,
            created_at,
            updated_at
        FROM bookings
        WHERE NOT EXISTS (
            SELECT 1 FROM reservations r 
            WHERE r.external_id = bookings.external_id
            AND r.check_in = bookings.check_in
        )
    """)

    # 6. Add reservation_id to guests
    op.add_column('guests', sa.Column('reservation_id', postgresql.UUID(), nullable=True))
    op.create_foreign_key('guests_reservation_id_fkey', 'guests', 'reservations', ['reservation_id'], ['id'])

    # 7. Create a default reservation for guests without bookings
    op.execute("""
        WITH default_property AS (
            SELECT id FROM properties LIMIT 1
        )
        INSERT INTO reservations (
            id,
            property_id,
            platform,
            guest_name_partial,
            status,
            check_in,
            check_out,
            created_at
        )
        SELECT 
            gen_random_uuid(),
            (SELECT id FROM default_property),
            'manual',
            'Legacy Guest',
            'completed',
            NOW(),
            NOW() + INTERVAL '1 day',
            NOW()
        FROM guests g
        WHERE g.booking_id IS NULL
        AND NOT EXISTS (
            SELECT 1 FROM reservations r2 
            WHERE r2.id = g.reservation_id
        );
    """)

    # 8. Update guest records - first those with bookings
    op.execute("""
        UPDATE guests g
        SET reservation_id = (
            SELECT r.id 
            FROM reservations r 
            JOIN bookings b ON b.external_id = r.external_id 
            WHERE b.id = g.booking_id
        )
        WHERE g.booking_id IS NOT NULL;
    """)

    # 9. Update guest records - then those without bookings
    op.execute("""
        UPDATE guests g
        SET reservation_id = (
            SELECT r.id
            FROM reservations r
            WHERE r.platform = 'manual'
            AND r.guest_name_partial = 'Legacy Guest'
            LIMIT 1
        )
        WHERE g.booking_id IS NULL
        AND g.reservation_id IS NULL;
    """)

    # 10. Make reservation_id NOT NULL
    op.alter_column('guests', 'reservation_id', nullable=False)

    # 11. Drop old constraints and columns
    op.drop_constraint('guests_booking_id_fkey', 'guests', type_='foreignkey')
    op.drop_column('guests', 'booking_id')

    # 12. Drop bookings table
    op.drop_table('bookings')

def downgrade():
    # 1. Recreate bookings table
    op.create_table('bookings',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('external_id', sa.Text(), nullable=True),
        sa.Column('guest_name', sa.Text(), nullable=True),
        sa.Column('guest_phone', sa.Text(), nullable=True),
        sa.Column('guest_email', sa.Text(), nullable=True),
        sa.Column('check_in', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('check_out', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('property_name', sa.Text(), nullable=True),
        sa.Column('booking_source', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=True),
        sa.Column('total_guests', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('raw_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Add booking_id back to guests
    op.add_column('guests', sa.Column('booking_id', postgresql.UUID(), nullable=True))
    op.create_foreign_key('guests_booking_id_fkey', 'guests', 'bookings', ['booking_id'], ['id'])

    # 3. Migrate data back from reservations to bookings
    op.execute("""
        INSERT INTO bookings (
            user_id,
            external_id,
            guest_name,
            guest_phone,
            guest_email,
            check_in,
            check_out,
            property_name,
            booking_source,
            status,
            total_guests,
            notes,
            raw_data,
            created_at,
            updated_at
        )
        SELECT 
            p.user_id::text,
            r.external_id,
            r.guest_name_partial,
            r.phone_partial,
            r.guest_email,
            r.check_in,
            r.check_out,
            p.name as property_name,
            r.platform as booking_source,
            r.status,
            r.total_guests,
            r.notes,
            r.raw_data,
            r.created_at,
            r.updated_at
        FROM reservations r
        JOIN properties p ON p.id = r.property_id
    """)

    # 4. Update guest records to point back to bookings
    op.execute("""
        UPDATE guests g
        SET booking_id = (
            SELECT b.id 
            FROM bookings b
            JOIN reservations r ON r.external_id = b.external_id
            WHERE r.id = g.reservation_id
        )
    """)

    # 5. Drop new columns from reservations
    op.drop_column('reservations', 'guest_email')
    op.drop_column('reservations', 'total_guests')
    op.drop_column('reservations', 'notes')

    # 6. Drop reservation_id from guests
    op.drop_constraint('guests_reservation_id_fkey', 'guests', type_='foreignkey')
    op.drop_column('guests', 'reservation_id') 