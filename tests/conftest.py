"""
pytest configuration and shared fixtures for Bus Pricing Pipeline tests

Provides common test fixtures, database setup/teardown, and testing utilities
for all test modules.
"""

import pytest
import tempfile
import shutil
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
import pandas as pd

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Import application components
from api.main import app, get_db
from api import models
from etl.model import HeuristicPricingModel

# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test_bus_pricing.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={
                            "check_same_thread": False})
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def test_db_engine():
    """Session-scoped test database engine"""
    # Create all tables
    models.Base.metadata.create_all(bind=test_engine)
    yield test_engine
    # Cleanup after all tests
    models.Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_db_session(test_db_engine):
    """Function-scoped database session"""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_client(test_db_session):
    """FastAPI test client with database override"""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def temp_data_dir():
    """Temporary directory for test data files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_routes():
    """Sample route data for testing"""
    return [
        {
            "route_id": 1,
            "origin": "Mumbai",
            "destination": "Pune",
            "distance_km": 148.0
        },
        {
            "route_id": 2,
            "origin": "Delhi",
            "destination": "Agra",
            "distance_km": 206.0
        },
        {
            "route_id": 3,
            "origin": "Bangalore",
            "destination": "Chennai",
            "distance_km": 346.0
        }
    ]


@pytest.fixture
def sample_operators():
    """Sample operator data for testing"""
    return [
        {
            "operator_id": 1,
            "name": "RedBus Express",
            "contact_email": "test@redbus.com",
            "is_active": True
        },
        {
            "operator_id": 2,
            "name": "VRL Travels",
            "contact_email": "test@vrl.com",
            "is_active": True
        }
    ]


@pytest.fixture
def sample_schedules():
    """Sample schedule data for testing"""
    base_date = datetime.now()
    return [
        {
            "schedule_id": 1001,
            "route_id": 1,
            "operator_id": 1,
            "departure_time": base_date + timedelta(hours=2),
            "arrival_time": base_date + timedelta(hours=5),
            "date": base_date,
            "is_active": True
        },
        {
            "schedule_id": 1002,
            "route_id": 2,
            "operator_id": 2,
            "departure_time": base_date + timedelta(hours=8),
            "arrival_time": base_date + timedelta(hours=12),
            "date": base_date,
            "is_active": True
        }
    ]


@pytest.fixture
def sample_seat_occupancy():
    """Sample seat occupancy data for testing"""
    return [
        {
            "schedule_id": 1001,
            "seat_type": "regular",
            "total_seats": 40,
            "occupied_seats": 32,
            "fare": 350.0,
            "occupancy_rate": 0.8,
            "timestamp": datetime.now()
        },
        {
            "schedule_id": 1001,
            "seat_type": "premium",
            "total_seats": 20,
            "occupied_seats": 15,
            "fare": 525.0,
            "occupancy_rate": 0.75,
            "timestamp": datetime.now()
        },
        {
            "schedule_id": 1002,
            "seat_type": "regular",
            "total_seats": 45,
            "occupied_seats": 20,
            "fare": 280.0,
            "occupancy_rate": 0.44,
            "timestamp": datetime.now()
        }
    ]


@pytest.fixture
def sample_raw_data_files(temp_data_dir, sample_schedules, sample_seat_occupancy):
    """Create sample raw data files for ETL testing"""
    raw_dir = Path(temp_data_dir) / "raw"
    raw_dir.mkdir(exist_ok=True)

    # Create schedule files
    schedule_data = {
        "schedules": [
            {
                "schedule_id": schedule["schedule_id"],
                "route_id": schedule["route_id"],
                "operator_id": schedule["operator_id"],
                "departure_time": schedule["departure_time"].isoformat(),
                "arrival_time": schedule["arrival_time"].isoformat(),
                "date": schedule["date"].date().isoformat(),
                "route_info": {
                    "origin": "Mumbai",
                    "destination": "Pune",
                    "distance_km": 148.0
                }
            }
            for schedule in sample_schedules
        ]
    }

    schedule_file = raw_dir / "schedules_20250615.json"
    with open(schedule_file, 'w') as f:
        json.dump(schedule_data, f, indent=2)

    # Create occupancy files
    occupancy_data = {
        "occupancy_records": [
            {
                "schedule_id": occ["schedule_id"],
                "seat_type": occ["seat_type"],
                "total_seats": occ["total_seats"],
                "occupied_seats": occ["occupied_seats"],
                "fare": occ["fare"],
                "timestamp": occ["timestamp"].isoformat(),
                "occupancy_rate": occ["occupancy_rate"]
            }
            for occ in sample_seat_occupancy
        ]
    }

    occupancy_file = raw_dir / "occupancy_20250615.json"
    with open(occupancy_file, 'w') as f:
        json.dump(occupancy_data, f, indent=2)

    # Create metadata files
    routes_metadata = {
        "routes": [
            {"route_id": 1, "origin": "Mumbai",
                "destination": "Pune", "distance_km": 148.0},
            {"route_id": 2, "origin": "Delhi",
                "destination": "Agra", "distance_km": 206.0}
        ]
    }

    operators_metadata = {
        "operators": [
            {"operator_id": 1, "name": "RedBus Express"},
            {"operator_id": 2, "name": "VRL Travels"}
        ]
    }

    with open(raw_dir / "routes_metadata.json", 'w') as f:
        json.dump(routes_metadata, f, indent=2)

    with open(raw_dir / "operators_metadata.json", 'w') as f:
        json.dump(operators_metadata, f, indent=2)

    return {
        "raw_dir": raw_dir,
        "schedule_file": schedule_file,
        "occupancy_file": occupancy_file,
        "routes_metadata": raw_dir / "routes_metadata.json",
        "operators_metadata": raw_dir / "operators_metadata.json"
    }


@pytest.fixture
def loaded_test_data(test_db_session, sample_routes, sample_operators, sample_schedules, sample_seat_occupancy):
    """Load sample data into test database"""
    # Load routes
    for route_data in sample_routes:
        route = models.Route(**route_data)
        test_db_session.add(route)

    # Load operators
    for operator_data in sample_operators:
        operator_data_copy = operator_data.copy()
        operator_data_copy['created_at'] = datetime.now()
        operator_data_copy['updated_at'] = datetime.now()
        operator = models.Operator(**operator_data_copy)
        test_db_session.add(operator)

    # Load schedules
    for schedule_data in sample_schedules:
        schedule_data_copy = schedule_data.copy()
        schedule_data_copy['created_at'] = datetime.now()
        schedule_data_copy['updated_at'] = datetime.now()
        schedule = models.Schedule(**schedule_data_copy)
        test_db_session.add(schedule)

    # Load seat occupancy
    for occupancy_data in sample_seat_occupancy:
        occupancy_data_copy = occupancy_data.copy()
        occupancy_data_copy['created_at'] = datetime.now()
        occupancy = models.SeatOccupancy(**occupancy_data_copy)
        test_db_session.add(occupancy)

    test_db_session.commit()

    return {
        "routes_count": len(sample_routes),
        "operators_count": len(sample_operators),
        "schedules_count": len(sample_schedules),
        "occupancy_count": len(sample_seat_occupancy)
    }


@pytest.fixture
def pricing_model():
    """Pricing model instance for testing"""
    return HeuristicPricingModel()


@pytest.fixture
def mock_environment_variables():
    """Mock environment variables for testing"""
    env_vars = {
        "POSTGRES_HOST": "test_host",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "test_user",
        "POSTGRES_PASSWORD": "test_password",
        "POSTGRES_DB": "test_db",
        "RAW_DATA_PATH": "/tmp/test/raw",
        "PROCESSED_DATA_PATH": "/tmp/test/processed",
        "ERROR_DATA_PATH": "/tmp/test/error",
        "MAX_FARE_THRESHOLD": "50000",
        "MIN_FARE_THRESHOLD": "10",
        "LOG_LEVEL": "DEBUG"
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def sample_anomalous_data():
    """Sample data with anomalies for testing data quality features"""
    return [
        {
            "schedule_id": 9001,
            "seat_type": "regular",
            "total_seats": 40,
            "occupied_seats": 50,  # Impossible: more occupied than total
            "fare": 350.0,
            "timestamp": datetime.now().isoformat()
        },
        {
            "schedule_id": 9002,
            "seat_type": "premium",
            "total_seats": 20,
            "occupied_seats": 15,
            "fare": -100.0,  # Negative fare
            "timestamp": datetime.now().isoformat()
        },
        {
            "schedule_id": 9003,
            "seat_type": "sleeper",
            "total_seats": 30,
            "occupied_seats": 25,
            "fare": 999999.0,  # Extremely high fare
            "timestamp": datetime.now().isoformat()
        },
        {
            "schedule_id": 9004,
            "seat_type": "regular",
            "total_seats": 0,  # Zero total seats
            "occupied_seats": 5,
            "fare": 200.0,
            "timestamp": datetime.now().isoformat()
        }
    ]


class TestDataGenerator:
    """Utility class for generating test data"""

    @staticmethod
    def create_schedule_json(schedules, filename=None):
        """Create a schedule JSON file"""
        data = {
            "schedules": [
                {
                    "schedule_id": s["schedule_id"],
                    "route_id": s["route_id"],
                    "operator_id": s["operator_id"],
                    "departure_time": s["departure_time"].isoformat() if isinstance(s["departure_time"], datetime) else s["departure_time"],
                    "arrival_time": s["arrival_time"].isoformat() if isinstance(s["arrival_time"], datetime) else s["arrival_time"],
                    "date": s["date"].date().isoformat() if isinstance(s["date"], datetime) else s["date"],
                    "route_info": s.get("route_info", {
                        "origin": "Test Origin",
                        "destination": "Test Destination",
                        "distance_km": 200.0
                    })
                }
                for s in schedules
            ]
        }

        if filename:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

        return data

    @staticmethod
    def create_occupancy_json(occupancy_records, filename=None):
        """Create an occupancy JSON file"""
        data = {
            "occupancy_records": [
                {
                    "schedule_id": o["schedule_id"],
                    "seat_type": o["seat_type"],
                    "total_seats": o["total_seats"],
                    "occupied_seats": o["occupied_seats"],
                    "fare": o["fare"],
                    "timestamp": o["timestamp"].isoformat() if isinstance(o["timestamp"], datetime) else o["timestamp"],
                    "occupancy_rate": o.get("occupancy_rate", o["occupied_seats"] / o["total_seats"] if o["total_seats"] > 0 else 0)
                }
                for o in occupancy_records
            ]
        }

        if filename:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

        return data


@pytest.fixture
def test_data_generator():
    """Test data generator utility"""
    return TestDataGenerator()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add default markers"""
    for item in items:
        # Add unit marker if no marker specified
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.unit)


# Custom assertions
class CustomAssertions:
    """Custom assertion helpers for testing"""

    @staticmethod
    def assert_valid_fare(fare, min_fare=0, max_fare=100000):
        """Assert fare is within valid range"""
        assert isinstance(fare, (int, float)
                          ), f"Fare must be numeric, got {type(fare)}"
        assert min_fare <= fare <= max_fare, f"Fare {fare} outside valid range [{min_fare}, {max_fare}]"

    @staticmethod
    def assert_valid_occupancy_rate(rate):
        """Assert occupancy rate is between 0 and 1"""
        assert isinstance(
            rate, (int, float)), f"Occupancy rate must be numeric, got {type(rate)}"
        assert 0 <= rate <= 1, f"Occupancy rate {rate} must be between 0 and 1"

    @staticmethod
    def assert_api_response_structure(response, required_fields):
        """Assert API response has required structure"""
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
        data = response.json()
        for field in required_fields:
            assert field in data, f"Required field '{field}' missing from response"


@pytest.fixture
def assert_helpers():
    """Custom assertion helpers"""
    return CustomAssertions()
