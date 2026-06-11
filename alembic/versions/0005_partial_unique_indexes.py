"""make unique constraints partial

Revision ID: 0005_partial_unique_indexes
Revises: 0004_featured_sync_snapshots
Create Date: 2026-06-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_partial_unique_indexes"
down_revision = "0004_featured_sync_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing unique constraints
    op.drop_constraint("cars_chassis_number_key", "cars", type_="unique")
    op.drop_constraint("cars_cid_key", "cars", type_="unique")
    
    # Create partial unique indexes
    op.create_index(
        "uq_cars_chassis_number_active",
        "cars",
        ["chassis_number"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL")
    )
    op.create_index(
        "uq_cars_cid_active",
        "cars",
        ["cid"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL")
    )


def downgrade() -> None:
    # Drop partial unique indexes
    op.drop_index("uq_cars_cid_active", table_name="cars")
    op.drop_index("uq_cars_chassis_number_active", table_name="cars")
    
    # Re-create unique constraints
    op.create_unique_constraint("cars_cid_key", "cars", ["cid"])
    op.create_unique_constraint("cars_chassis_number_key", "cars", ["chassis_number"])
