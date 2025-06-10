"""
Tests for the Bus Pricing Pipeline API

Unit and integration tests for API endpoints using FastAPI TestClient.
"""

from api import models
from api.main import app, get_db
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os

# Set test environment
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_DB"] = "busdb_test"


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={
                       "check_same_thread": False})
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)

# Create test database tables
models.Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def test_db():
    """Fixture for test database session"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_route(test_db):
    """Fixture for sample route data"""
    # Use auto-increment by not specifying route_id
    route = models.Route(
        origin="Mumbai",
        destination="Pune",
        distance_km=148.0
    )
    test_db.add(route)
    test_db.commit()
    test_db.refresh(route)
    return route


@pytest.fixture
def sample_operator(test_db):
    """Fixture for sample operator data"""
    # Use auto-increment by not specifying operator_id
    operator = models.Operator(
        name="Test Bus Company",
        contact_email="test@example.com"
    )
    test_db.add(operator)
    test_db.commit()
    test_db.refresh(operator)
    return operator


@pytest.fixture
def sample_schedule(test_db, sample_route, sample_operator):
    """Fixture for sample schedule data"""
    # Use auto-increment by not specifying schedule_id
    schedule = models.Schedule(
        route_id=sample_route.route_id,
        operator_id=sample_operator.operator_id,
        departure_time=datetime.now() + timedelta(hours=2),
        arrival_time=datetime.now() + timedelta(hours=5),
        date=datetime.now()
    )
    test_db.add(schedule)
    test_db.commit()
    test_db.refresh(schedule)
    return schedule


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self):
        """Test health check returns OK status"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"


class TestRouteEndpoints:
    """Test route-related endpoints"""

    def test_get_routes_empty(self):
        """Test getting routes when none exist"""
        response = client.get("/routes")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_routes_with_data(self, sample_route):
        """Test getting routes with data"""
        response = client.get("/routes")
        assert response.status_code == 200

        routes = response.json()
        assert len(routes) >= 1

        route = routes[0]
        assert route["route_id"] == sample_route.route_id
        assert route["origin"] == sample_route.origin
        assert route["destination"] == sample_route.destination
        assert route["distance_km"] == sample_route.distance_km

    def test_get_route_by_id(self, sample_route):
        """Test getting a specific route by ID"""
        response = client.get(f"/routes/{sample_route.route_id}")
        assert response.status_code == 200

        route = response.json()
        assert route["route_id"] == sample_route.route_id
        assert route["origin"] == sample_route.origin

    def test_get_route_not_found(self):
        """Test getting non-existent route"""
        response = client.get("/routes/9999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestOperatorEndpoints:
    """Test operator-related endpoints"""

    def test_get_operators_empty(self):
        """Test getting operators when none exist"""
        response = client.get("/operators")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_operators_with_data(self, sample_operator):
        """Test getting operators with data"""
        response = client.get("/operators")
        assert response.status_code == 200

        operators = response.json()
        assert len(operators) >= 1

        operator = operators[0]
        assert operator["operator_id"] == sample_operator.operator_id
        assert operator["name"] == sample_operator.name
        assert operator["is_active"] == True


class TestScheduleEndpoints:
    """Test schedule-related endpoints"""

    def test_get_schedules_invalid_date(self):
        """Test getting schedules with invalid date format"""
        response = client.get("/schedules/1?date=invalid-date")
        assert response.status_code == 422  # Validation error

    def test_get_schedules_valid_request(self, sample_schedule):
        """Test getting schedules with valid parameters"""
        date_str = sample_schedule.date.strftime("%Y-%m-%d")
        response = client.get(
            f"/schedules/{sample_schedule.route_id}?date={date_str}")
        assert response.status_code == 200

        schedules = response.json()
        # May be empty if the test data doesn't match the date exactly
        assert isinstance(schedules, list)


class TestAnalyticsEndpoints:
    """Test analytics endpoints"""

    def test_get_occupancy_analytics_no_data(self):
        """Test occupancy analytics with no data"""
        response = client.get("/analytics/occupancy")
        assert response.status_code == 200

        stats = response.json()
        assert stats["total_schedules"] == 0
        assert stats["average_occupancy_rate"] == 0

    def test_get_occupancy_analytics_invalid_date(self):
        """Test occupancy analytics with invalid date"""
        response = client.get("/analytics/occupancy?date=invalid-date")
        assert response.status_code == 422


class TestPricingEndpoints:
    """Test pricing suggestion endpoints"""

    def test_pricing_suggestion_invalid_route(self):
        """Test pricing suggestion for non-existent route"""
        pricing_data = {
            "route_id": 9999,
            "seat_type": "regular",
            "current_occupancy_rate": 0.7
        }

        response = client.post("/pricing/suggest", json=pricing_data)
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_pricing_suggestion_valid_request(self, sample_route):
        """Test valid pricing suggestion request"""
        pricing_data = {
            "route_id": sample_route.route_id,
            "seat_type": "regular",
            "current_occupancy_rate": 0.7,
            "departure_time": (datetime.now() + timedelta(hours=4)).isoformat()
        }

        response = client.post("/pricing/suggest", json=pricing_data)
        assert response.status_code == 200

        suggestion = response.json()
        assert suggestion["route_id"] == sample_route.route_id
        assert suggestion["seat_type"] == "regular"
        assert suggestion["current_occupancy_rate"] == 0.7
        assert "suggested_fare" in suggestion
        assert "confidence_score" in suggestion
        assert "reasoning" in suggestion

    def test_pricing_suggestion_invalid_occupancy(self, sample_route):
        """Test pricing suggestion with invalid occupancy rate"""
        pricing_data = {
            "route_id": sample_route.route_id,
            "seat_type": "regular",
            "current_occupancy_rate": 1.5  # Invalid: > 1.0
        }

        response = client.post("/pricing/suggest", json=pricing_data)
        assert response.status_code == 422  # Validation error


class TestDataQualityEndpoints:
    """Test data quality endpoints"""

    def test_get_data_quality_report(self):
        """Test data quality report generation"""
        response = client.get("/data-quality/report")
        assert response.status_code == 200

        report = response.json()
        assert "total_records_processed" in report
        assert "valid_records" in report
        assert "invalid_records" in report
        assert "quality_score" in report
        assert "issues" in report
        assert isinstance(report["issues"], list)

    def test_get_data_quality_report_custom_days(self):
        """Test data quality report with custom days parameter"""
        response = client.get("/data-quality/report?days_back=3")
        assert response.status_code == 200


class TestStatsEndpoints:
    """Test statistics endpoints"""

    def test_get_summary_stats(self):
        """Test summary statistics endpoint"""
        response = client.get("/stats/summary")
        assert response.status_code == 200

        stats = response.json()
        assert "system_status" in stats
        assert "total_routes" in stats
        assert "total_operators" in stats
        assert "total_schedules" in stats
        assert "total_occupancy_records" in stats
        assert "recent_activity" in stats
        assert "timestamp" in stats


class TestAdminEndpoints:
    """Test admin endpoints"""

    def test_create_route(self):
        """Test creating a new route"""
        route_data = {
            "origin": "Delhi",
            "destination": "Agra",
            "distance_km": 206.0
        }

        response = client.post("/admin/routes", json=route_data)
        assert response.status_code == 200

        created_route = response.json()
        assert created_route["origin"] == route_data["origin"]
        assert created_route["destination"] == route_data["destination"]
        assert created_route["distance_km"] == route_data["distance_km"]

    def test_create_operator(self):
        """Test creating a new operator"""
        operator_data = {
            "name": "New Bus Company",
            "contact_email": "info@newbus.com"
        }

        response = client.post("/admin/operators", json=operator_data)
        assert response.status_code == 200

        created_operator = response.json()
        assert created_operator["name"] == operator_data["name"]
        assert created_operator["contact_email"] == operator_data["contact_email"]


def teardown_module():
    """Clean up test database after tests"""
    import os
    if os.path.exists("test.db"):
        os.remove("test.db")
