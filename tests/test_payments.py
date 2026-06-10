import pytest

def test_get_payments_unauthorized(client):
    """Test listing payments without authentication."""
    response = client.get("/api/v1/payments")
    # Should fail because no auth token is provided
    assert response.status_code == 401

def test_post_payment_unauthorized(client):
    """Test post payment without authentication."""
    response = client.post("/api/v1/payments", json={
        "order_id": "some-order-id",
        "amount": 1000.0,
        "method": "cash"
    })
    # Should fail because no auth token is provided
    assert response.status_code == 401
