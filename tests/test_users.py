import pytest

def test_get_users_unauthorized(client):
    """Test listing users without authentication."""
    response = client.get("/api/v1/users")
    # Should fail because no auth token is provided
    assert response.status_code == 401

def test_post_user_unauthorized(client):
    """Test post user without authentication."""
    response = client.post("/api/v1/users", json={
        "name": "New User",
        "email": "newuser@example.com",
        "phone": "1234567890",
        "password": "password123",
        "role": "dealer"
    })
    # Should fail because no auth token is provided
    assert response.status_code == 401
