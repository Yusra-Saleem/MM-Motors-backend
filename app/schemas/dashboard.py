from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_cars: int
    available_cars: int
    upcoming_cars: int
    total_users: int
    dealers: int
    total_orders: int
    pending_payments: int
    pending_orders: int = 0
    completed_orders: int
    total_revenue: float = 0
