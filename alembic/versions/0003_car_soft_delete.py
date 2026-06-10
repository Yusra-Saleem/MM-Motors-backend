"""add soft delete support for cars

Revision ID: 0003_car_soft_delete
Revises: 0002_cars_payments_metadata
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_car_soft_delete"
down_revision = "0002_cars_payments_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cars", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_cars_deleted_at", "cars", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_cars_deleted_at", table_name="cars")
    op.drop_column("cars", "deleted_at")
