"""add_car_search_indexes

Revision ID: 4b3a617a8e93
Revises: ea24dc931c5f
Create Date: 2026-07-07 01:12:19.125744
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b3a617a8e93'
down_revision = 'ea24dc931c5f'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # ### commands adjusted to only add target car indexes ###
    op.create_index(op.f('ix_cars_make'), 'cars', ['make'], unique=False)
    op.create_index(op.f('ix_cars_year'), 'cars', ['year'], unique=False)
    op.create_index(op.f('ix_cars_price'), 'cars', ['price'], unique=False)
    op.create_index(op.f('ix_cars_status'), 'cars', ['status'], unique=False)
    op.create_index(op.f('ix_cars_transmission'), 'cars', ['transmission'], unique=False)
    op.create_index(op.f('ix_cars_fuel_type'), 'cars', ['fuel_type'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands adjusted to only drop target car indexes ###
    op.drop_index(op.f('ix_cars_fuel_type'), table_name='cars')
    op.drop_index(op.f('ix_cars_transmission'), table_name='cars')
    op.drop_index(op.f('ix_cars_status'), table_name='cars')
    op.drop_index(op.f('ix_cars_price'), table_name='cars')
    op.drop_index(op.f('ix_cars_year'), table_name='cars')
    op.drop_index(op.f('ix_cars_make'), table_name='cars')
    # ### end Alembic commands ###
