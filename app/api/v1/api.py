from fastapi import APIRouter

from app.api.v1.endpoints import auth, cars, dashboard, favorites, health, orders, payments, users

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(cars.router, prefix="/cars", tags=["cars"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["favorites"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

