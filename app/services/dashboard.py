from sqlalchemy.orm import Session

from app.models.car import Car, CarStatus
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.payment import Payment, UserPaymentStatus
from app.models.user import User, UserRole
from app.schemas.dashboard import DashboardStats
from sqlalchemy import func


def get_dashboard_stats(db: Session) -> DashboardStats:
    return DashboardStats(
        total_cars=db.query(Car).count(),
        available_cars=db.query(Car).filter(Car.status == CarStatus.available).count(),
        upcoming_cars=db.query(Car).filter(Car.status == CarStatus.upcoming).count(),
        total_users=db.query(User).filter(User.role != UserRole.admin).count(),
        dealers=db.query(User).filter(User.role == UserRole.dealer).count(),
        total_orders=db.query(Order).count(),
        pending_payments=db.query(Order).filter(Order.payment_status != PaymentStatus.paid).count(),
        pending_orders=db.query(Order).filter(Order.status.in_([OrderStatus.pending, OrderStatus.processing])).count(),
        completed_orders=db.query(Order).filter(Order.status == OrderStatus.completed).count(),
        total_revenue=float(db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.status == UserPaymentStatus.confirmed).scalar() or 0),
    )
