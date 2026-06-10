import pytest
from app.models.order import OrderStatus

def test_get_orders_unauthorized(client):
    """Test listing orders without authentication."""
    response = client.get("/api/v1/orders")
    # Should fail because no auth token is provided
    assert response.status_code == 401

def test_post_order_unauthorized(client):
    """Test post order without authentication."""
    response = client.post("/api/v1/orders", json={
        "car_id": "some-car-id",
        "order_date": "2026-06-04",
        "status": OrderStatus.pending
    })
    # Should fail because no auth token is provided
    assert response.status_code == 401
