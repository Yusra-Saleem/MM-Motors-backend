"""initial mm motors schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


user_role = postgresql.ENUM("admin", "dealer", "stock_buyer", name="user_role", create_type=False)
account_status = postgresql.ENUM("active", "inactive", "suspended", name="account_status", create_type=False)
car_status = postgresql.ENUM("available", "upcoming", "sold", "pending", name="car_status", create_type=False)
order_status = postgresql.ENUM("pending", "processing", "shipped", "completed", "cancelled", name="order_status", create_type=False)
payment_status = postgresql.ENUM("unpaid", "partial", "paid", "refunded", name="payment_status", create_type=False)
user_payment_status = postgresql.ENUM("confirmed", "pending", name="user_payment_status", create_type=False)


def _create_enum_type(name: str, *values: str) -> None:
    enum_values = ", ".join(f"'{value}'" for value in values)
    op.execute(
        f"""
        DO $$
        BEGIN
            CREATE TYPE {name} AS ENUM ({enum_values});
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END
        $$;
        """
    )


def upgrade() -> None:
    _create_enum_type("user_role", "admin", "dealer", "stock_buyer")
    _create_enum_type("account_status", "active", "inactive", "suspended")
    _create_enum_type("car_status", "available", "upcoming", "sold", "pending")
    _create_enum_type("order_status", "pending", "processing", "shipped", "completed", "cancelled")
    _create_enum_type("payment_status", "unpaid", "partial", "paid", "refunded")
    _create_enum_type("user_payment_status", "confirmed", "pending")

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("status", account_status, nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("avatar", sa.String(length=500), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=False),
        sa.Column("total_orders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_paid", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_balance", sa.Float(), nullable=False, server_default="0"),
        sa.Column("registration_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_active", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "cars",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("cid", sa.String(length=128), nullable=False, unique=True),
        sa.Column("chassis_number", sa.String(length=128), nullable=False, unique=True),
        sa.Column("make", sa.String(length=100), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("package", sa.String(length=200), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("import_year", sa.Integer(), nullable=True),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("status", car_status, nullable=False),
        sa.Column("mileage", sa.String(length=100), nullable=False),
        sa.Column("transmission", sa.String(length=100), nullable=False),
        sa.Column("fuel_type", sa.String(length=100), nullable=False),
        sa.Column("body_type", sa.String(length=100), nullable=False),
        sa.Column("drive_type", sa.String(length=100), nullable=False),
        sa.Column("exterior_color", sa.String(length=100), nullable=False),
        sa.Column("grade", sa.String(length=50), nullable=False),
        sa.Column("engine_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=4000), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("images", sa.JSON(), nullable=False),
        sa.Column("thumbnail", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("car_id", sa.String(length=64), sa.ForeignKey("cars.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("customer_name", sa.String(length=200), nullable=False),
        sa.Column("car_name", sa.String(length=200), nullable=False),
        sa.Column("car_cid", sa.String(length=128), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("paid_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("balance_amount", sa.Float(), nullable=False),
        sa.Column("payment_status", payment_status, nullable=False),
        sa.Column("status", order_status, nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payment_method", sa.String(length=100), nullable=False),
        sa.Column("notes", sa.String(length=4000), nullable=True),
        sa.Column("created_by", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_orders_user_id", "orders", ["user_id"])
    op.create_index("ix_orders_car_id", "orders", ["car_id"])

    op.create_table(
        "payments",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_id", sa.String(length=64), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("method", sa.String(length=100), nullable=False),
        sa.Column("status", user_payment_status, nullable=False),
        sa.Column("notes", sa.String(length=4000), nullable=True),
        sa.Column("created_by", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"])
    op.create_index("ix_payments_order_id", "payments", ["order_id"])

    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("car_id", sa.String(length=64), sa.ForeignKey("cars.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "car_id", name="uq_user_car_favorite"),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("favorites")
    op.drop_index("ix_payments_order_id", table_name="payments")
    op.drop_index("ix_payments_user_id", table_name="payments")
    op.drop_table("payments")
    op.drop_index("ix_orders_car_id", table_name="orders")
    op.drop_index("ix_orders_user_id", table_name="orders")
    op.drop_table("orders")
    op.drop_table("cars")
    op.drop_table("users")

    bind = op.get_bind()
    user_payment_status.drop(bind, checkfirst=True)
    payment_status.drop(bind, checkfirst=True)
    order_status.drop(bind, checkfirst=True)
    car_status.drop(bind, checkfirst=True)
    account_status.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)
