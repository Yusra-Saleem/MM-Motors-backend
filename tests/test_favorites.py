from datetime import datetime, UTC
import pytest
from app.main import app
from app.db.session import get_db
from app.services.auth import current_user_dependency
from app.models.car import Car, CarStatus
from app.models.user import User, UserRole, AccountStatus
from app.models.favorite import Favorite
from tests.conftest import TestingSessionLocal

def test_favorites_toggle_and_sync(client):
    # 1. Create database sessions and insert test user and car
    db = TestingSessionLocal()
    try:
        # Create test user
        test_user = User(
            id="test-user-uuid",
            name="Favorite Test User",
            email="favorite_test@example.com",
            phone="1234567890",
            role=UserRole.stock_buyer,
            status=AccountStatus.active,
            address="123 Street",
            registration_date=datetime.now(UTC),
            last_active=datetime.now(UTC),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            password_hash="fake-hash"
        )
        db.add(test_user)
        
        # Create test car
        test_car = Car(
            id="test-car-uuid",
            cid="99999999",
            chassis_number="CH-TEST999",
            make="Toyota",
            name="Land Cruiser ZX",
            package="ZX",
            year=2024,
            price=150.0,
            status=CarStatus.available,
            mileage="500 km",
            transmission="Automatic",
            fuel_type="Petrol",
            body_type="SUV",
            drive_type="4WD",
            exterior_color="Pearl White",
            grade="5.0",
            engine_type="V6 Turbo",
            description="Luxury SUV",
            features=[],
            images=[],
            thumbnail=None,
            specifications={},
            featured_flag=False,
            priority_score=0.0,
            engagement_score=0.0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        db.add(test_car)
        db.commit()
    finally:
        db.close()

    # 2. Mock dependency override for current_user_dependency to return our test_user
    async def mock_current_user():
        db = TestingSessionLocal()
        try:
            return db.query(User).filter(User.id == "test-user-uuid").first()
        finally:
            db.close()

    app.dependency_overrides[current_user_dependency] = mock_current_user

    try:
        # 3. Test list favorites (should be empty initially)
        response = client.get("/api/v1/favorites")
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 0

        # 4. Test toggle favorite (should add favorite)
        response = client.post("/api/v1/favorites/toggle", json={"car_id": "test-car-uuid"})
        assert response.status_code == 200
        assert response.json()["data"]["result"] == "added"
        assert response.json()["data"]["favorite"]["car_id"] == "test-car-uuid"

        # 5. Verify database state & rankings sync
        db = TestingSessionLocal()
        try:
            car = db.query(Car).filter(Car.id == "test-car-uuid").first()
            assert car.engagement_score == 2.0  # favorites_count * 2
            
            fav = db.query(Favorite).filter(Favorite.user_id == "test-user-uuid", Favorite.car_id == "test-car-uuid").first()
            assert fav is not None
        finally:
            db.close()

        # 6. Test list favorites again (should contain 1 item)
        response = client.get("/api/v1/favorites")
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 1
        assert response.json()["data"]["items"][0]["car_id"] == "test-car-uuid"

        # 7. Test toggle favorite again (should remove favorite)
        response = client.post("/api/v1/favorites/toggle", json={"car_id": "test-car-uuid"})
        assert response.status_code == 200
        assert response.json()["data"]["result"] == "removed"
        assert response.json()["data"]["favorite"] is None

        # 8. Verify database state & rankings sync after removal
        db = TestingSessionLocal()
        try:
            car = db.query(Car).filter(Car.id == "test-car-uuid").first()
            assert car.engagement_score == 0.0
            
            fav = db.query(Favorite).filter(Favorite.user_id == "test-user-uuid", Favorite.car_id == "test-car-uuid").first()
            assert fav is None
        finally:
            db.close()

    finally:
        # Clean up dependency overrides
        app.dependency_overrides.pop(current_user_dependency, None)
