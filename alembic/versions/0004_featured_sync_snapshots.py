"""add featured car fields and order snapshots

Revision ID: 0004_featured_sync_snapshots
Revises: 0003_car_soft_delete
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_featured_sync_snapshots"
down_revision = "0003_car_soft_delete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cars", sa.Column("featured_flag", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("cars", sa.Column("priority_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("cars", sa.Column("engagement_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("orders", sa.Column("car_snapshot", sa.JSON(), nullable=True))
    op.create_index("ix_cars_featured_flag", "cars", ["featured_flag"])
    op.create_index("ix_cars_priority_score", "cars", ["priority_score"])


def downgrade() -> None:
    op.drop_index("ix_cars_priority_score", table_name="cars")
    op.drop_index("ix_cars_featured_flag", table_name="cars")
    op.drop_column("orders", "car_snapshot")
    op.drop_column("cars", "engagement_score")
    op.drop_column("cars", "priority_score")
    op.drop_column("cars", "featured_flag")
