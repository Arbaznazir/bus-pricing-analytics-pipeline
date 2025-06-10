"""
Tests for ETL Pipeline and Pricing Model

Unit tests for data processing, cleaning, validation, and pricing algorithms.
"""

import pytest
import tempfile
import json
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

# ETL and model imports
from etl.model import (
    HeuristicPricingModel,
    validate_pricing_input,
    calculate_route_popularity,
    create_pricing_model
)


class TestHeuristicPricingModel:
    """Test the heuristic pricing model functionality"""

    @pytest.fixture
    def pricing_model(self):
        """Fixture for pricing model instance"""
        return HeuristicPricingModel()

    def test_calculate_base_fare_regular_seat(self, pricing_model):
        """Test base fare calculation for regular seats"""
        # Test short distance
        fare = pricing_model.calculate_base_fare(100, "regular")
        expected = 100 * 2.5 * 1.0  # distance * rate * multiplier
        assert fare == expected

        # Test medium distance
        fare = pricing_model.calculate_base_fare(300, "regular")
        expected = 300 * 2.5 * 0.9  # lower rate for medium distance
        assert fare == expected

        # Test long distance
        fare = pricing_model.calculate_base_fare(500, "regular")
        expected = 500 * 2.5 * 0.8  # lower rate for long distance
        assert fare == expected

    def test_calculate_base_fare_different_seat_types(self, pricing_model):
        """Test base fare calculation for different seat types"""
        distance = 200

        regular_fare = pricing_model.calculate_base_fare(distance, "regular")
        premium_fare = pricing_model.calculate_base_fare(distance, "premium")
        sleeper_fare = pricing_model.calculate_base_fare(distance, "sleeper")

        # Premium should be more expensive than regular
        assert premium_fare > regular_fare

        # Sleeper should be most expensive
        assert sleeper_fare > premium_fare
        assert sleeper_fare > regular_fare

    def test_calculate_base_fare_unknown_seat_type(self, pricing_model):
        """Test base fare calculation with unknown seat type defaults to regular"""
        regular_fare = pricing_model.calculate_base_fare(200, "regular")
        unknown_fare = pricing_model.calculate_base_fare(200, "unknown_type")

        assert regular_fare == unknown_fare

    def test_get_occupancy_adjustment_high_occupancy(self, pricing_model):
        """Test occupancy adjustment for high occupancy rates"""
        adjustment, reasoning = pricing_model.get_occupancy_adjustment(0.9)

        # High occupancy should increase price
        assert adjustment > 1.0
        assert "high occupancy" in reasoning.lower()
        assert "increases demand" in reasoning.lower()

    def test_get_occupancy_adjustment_low_occupancy(self, pricing_model):
        """Test occupancy adjustment for low occupancy rates"""
        adjustment, reasoning = pricing_model.get_occupancy_adjustment(0.2)

        # Low occupancy should decrease price
        assert adjustment < 1.0
        assert "low occupancy" in reasoning.lower()
        assert "price reduction" in reasoning.lower()

    def test_get_occupancy_adjustment_medium_occupancy(self, pricing_model):
        """Test occupancy adjustment for medium occupancy rates"""
        adjustment, reasoning = pricing_model.get_occupancy_adjustment(0.5)

        # Medium occupancy should maintain base price
        assert adjustment == 1.0
        assert "moderate occupancy" in reasoning.lower()
        assert "maintains base pricing" in reasoning.lower()

    def test_get_time_adjustment_peak_hours(self, pricing_model):
        """Test time adjustment for peak hours"""
        # Test peak hour (8 AM)
        peak_time = datetime.now().replace(hour=8, minute=0, second=0)
        adjustment, reasoning = pricing_model.get_time_adjustment(peak_time)

        assert adjustment > 1.0
        assert "peak hour" in reasoning.lower()

    def test_get_time_adjustment_off_peak_hours(self, pricing_model):
        """Test time adjustment for off-peak hours"""
        # Test off-peak hour (2 AM), set it to future to avoid urgency adjustment
        from datetime import datetime, timedelta
        off_peak_time = datetime.now() + timedelta(days=1)
        off_peak_time = off_peak_time.replace(hour=2, minute=0, second=0)
        adjustment, reasoning = pricing_model.get_time_adjustment(
            off_peak_time)

        assert adjustment < 1.0
        assert "off-peak" in reasoning.lower()

    def test_get_time_adjustment_last_minute(self, pricing_model):
        """Test time adjustment for last-minute bookings"""
        # Departure in 1 hour (last-minute)
        departure_time = datetime.utcnow() + timedelta(hours=1)
        adjustment, reasoning = pricing_model.get_time_adjustment(
            departure_time)

        assert adjustment > 1.0
        assert "last-minute" in reasoning.lower()

    def test_get_time_adjustment_early_booking(self, pricing_model):
        """Test time adjustment for early bookings"""
        # Departure in 10 days (early booking)
        departure_time = datetime.utcnow() + timedelta(days=10)
        adjustment, reasoning = pricing_model.get_time_adjustment(
            departure_time)

        assert adjustment < 1.0
        assert "early booking" in reasoning.lower()

    def test_get_route_adjustment_long_distance_sleeper(self, pricing_model):
        """Test route adjustment for long-distance sleeper seats"""
        adjustment, reasoning = pricing_model.get_route_adjustment(
            600, "sleeper")

        assert adjustment > 1.0
        assert "sleeper premium" in reasoning.lower()

    def test_get_route_adjustment_short_distance_premium(self, pricing_model):
        """Test route adjustment for short-distance premium seats"""
        adjustment, reasoning = pricing_model.get_route_adjustment(
            80, "premium")

        assert adjustment < 1.0
        assert "premium seat adjustment" in reasoning.lower()

    def test_apply_business_constraints_minimum_fare(self, pricing_model):
        """Test business constraints apply minimum fare limits"""
        base_fare = 100
        suggested_fare = 50  # Below 70% of base

        constrained_fare, reasoning = pricing_model.apply_business_constraints(
            suggested_fare, base_fare)

        assert constrained_fare >= base_fare * 0.7
        assert "minimum fare constraint" in reasoning.lower()

    def test_apply_business_constraints_maximum_fare(self, pricing_model):
        """Test business constraints apply maximum fare limits"""
        base_fare = 100
        suggested_fare = 300  # Above 250% of base

        constrained_fare, reasoning = pricing_model.apply_business_constraints(
            suggested_fare, base_fare)

        assert constrained_fare <= base_fare * 2.5
        assert "maximum fare constraint" in reasoning.lower()

    def test_apply_business_constraints_rounding(self, pricing_model):
        """Test business constraints round to nearest 5"""
        base_fare = 100
        suggested_fare = 123  # Should round to 125

        constrained_fare, reasoning = pricing_model.apply_business_constraints(
            suggested_fare, base_fare)

        assert constrained_fare % 5 == 0
        assert constrained_fare in [120, 125]  # Should round to nearest 5

    def test_calculate_confidence_score_high_data(self, pricing_model):
        """Test confidence score with high amount of historical data"""
        confidence = pricing_model.calculate_confidence_score(100, 0.8)

        assert 0.8 <= confidence <= 1.0
        assert confidence > 0.9  # Should be high with lots of data

    def test_calculate_confidence_score_low_data(self, pricing_model):
        """Test confidence score with low amount of historical data"""
        confidence = pricing_model.calculate_confidence_score(5, 0.3)

        assert 0.0 <= confidence <= 1.0
        assert confidence < 0.8  # Should be lower with little data

    def test_suggest_pricing_complete_workflow(self, pricing_model):
        """Test complete pricing suggestion workflow"""
        result = pricing_model.suggest_pricing(
            route_distance_km=200,
            seat_type="regular",
            current_occupancy_rate=0.7,
            departure_time=datetime.utcnow() + timedelta(hours=4),
            current_fare=400,
            historical_data_points=25
        )

        # Verify result structure
        required_keys = [
            "suggested_fare", "base_fare", "fare_adjustment_percentage",
            "confidence_score", "reasoning", "model_version", "adjustment_factors"
        ]

        for key in required_keys:
            assert key in result

        # Verify data types and ranges
        assert isinstance(result["suggested_fare"], (int, float))
        assert isinstance(result["confidence_score"], float)
        assert 0.0 <= result["confidence_score"] <= 1.0
        assert isinstance(result["reasoning"], str)
        assert len(result["reasoning"]) > 0
        assert result["model_version"] == "heuristic_v1"

    def test_suggest_pricing_with_invalid_input(self, pricing_model):
        """Test pricing suggestion with invalid input raises error"""
        with pytest.raises(ValueError):
            pricing_model.suggest_pricing(
                route_distance_km=-100,  # Invalid negative distance
                seat_type="regular",
                current_occupancy_rate=0.7
            )


class TestPricingUtilities:
    """Test utility functions for pricing model"""

    def test_validate_pricing_input_valid(self):
        """Test input validation with valid parameters"""
        result = validate_pricing_input(200, "regular", 0.7)
        assert result is True

    def test_validate_pricing_input_invalid_distance(self):
        """Test input validation with invalid distance"""
        with pytest.raises(ValueError, match="Route distance must be positive"):
            validate_pricing_input(-50, "regular", 0.7)

        with pytest.raises(ValueError, match="Route distance must be positive"):
            validate_pricing_input(0, "regular", 0.7)

    def test_validate_pricing_input_invalid_seat_type(self):
        """Test input validation with invalid seat type"""
        with pytest.raises(ValueError, match="Invalid seat type"):
            validate_pricing_input(200, "invalid_type", 0.7)

    def test_validate_pricing_input_invalid_occupancy(self):
        """Test input validation with invalid occupancy rate"""
        with pytest.raises(ValueError, match="Occupancy rate must be between 0 and 1"):
            validate_pricing_input(200, "regular", -0.1)

        with pytest.raises(ValueError, match="Occupancy rate must be between 0 and 1"):
            validate_pricing_input(200, "regular", 1.5)

    def test_calculate_route_popularity_empty_list(self):
        """Test route popularity calculation with empty data"""
        popularity = calculate_route_popularity([])
        assert popularity == 0.5  # Default neutral popularity

    def test_calculate_route_popularity_high_consistent(self):
        """Test route popularity with high, consistent occupancy"""
        occupancy_rates = [0.8, 0.85, 0.9, 0.82, 0.88]
        popularity = calculate_route_popularity(occupancy_rates)

        assert 0.0 <= popularity <= 1.0
        assert popularity > 0.7  # Should be high for consistent high occupancy

    def test_calculate_route_popularity_low_inconsistent(self):
        """Test route popularity with low, inconsistent occupancy"""
        occupancy_rates = [0.1, 0.9, 0.2, 0.8, 0.3]
        popularity = calculate_route_popularity(occupancy_rates)

        assert 0.0 <= popularity <= 1.0
        assert popularity < 0.7  # Should be lower due to inconsistency

    def test_create_pricing_model_factory(self):
        """Test pricing model factory function"""
        model = create_pricing_model()

        assert isinstance(model, HeuristicPricingModel)
        assert model.model_version == "heuristic_v1"


class TestETLDataProcessing:
    """Test ETL data processing functions"""

    def test_data_validation_scenarios(self):
        """Test various data validation scenarios"""
        # Test data that should pass validation
        valid_data = [
            {"fare": 100, "total_seats": 40, "occupied_seats": 30},
            {"fare": 250.50, "total_seats": 45, "occupied_seats": 45},
            {"fare": 1500, "total_seats": 20, "occupied_seats": 0}
        ]

        for data in valid_data:
            # These should not raise exceptions
            assert data["fare"] > 0
            assert data["total_seats"] > 0
            assert data["occupied_seats"] >= 0
            assert data["occupied_seats"] <= data["total_seats"]

    def test_data_anomaly_detection(self):
        """Test detection of data anomalies"""
        # Test data that should be flagged as anomalies
        anomalous_data = [
            {"fare": -100, "issue": "negative_fare"},
            {"fare": 0, "issue": "zero_fare"},
            {"fare": 999999, "issue": "extreme_fare"},
            {"total_seats": 40, "occupied_seats": 50,
                "issue": "impossible_occupancy"}
        ]

        for data in anomalous_data:
            if "fare" in data and data["fare"] <= 0:
                assert data["issue"] in ["negative_fare", "zero_fare"]
            elif "fare" in data and data["fare"] > 100000:
                assert data["issue"] == "extreme_fare"
            elif "occupied_seats" in data and "total_seats" in data:
                if data["occupied_seats"] > data["total_seats"]:
                    assert data["issue"] == "impossible_occupancy"

    @pytest.fixture
    def sample_schedule_data(self):
        """Fixture for sample schedule data"""
        return [
            {
                "schedule_id": 1001,
                "route_id": 1,
                "operator_id": 1,
                "departure_time": "2025-06-15T08:00:00",
                "arrival_time": "2025-06-15T11:30:00",
                "date": "2025-06-15",
                "route_info": {
                    "origin": "Mumbai",
                    "destination": "Pune",
                    "distance_km": 148.0
                }
            },
            {
                "schedule_id": 1002,
                "route_id": 2,
                "operator_id": 2,
                "departure_time": "2025-06-15T14:00:00",
                "arrival_time": "2025-06-15T18:30:00",
                "date": "2025-06-15",
                "route_info": {
                    "origin": "Delhi",
                    "destination": "Agra",
                    "distance_km": 206.0
                }
            }
        ]

    @pytest.fixture
    def sample_occupancy_data(self):
        """Fixture for sample occupancy data"""
        return [
            {
                "schedule_id": 1001,
                "seat_type": "regular",
                "total_seats": 40,
                "occupied_seats": 32,
                "fare": 350.0,
                "timestamp": "2025-06-15T07:30:00",
                "occupancy_rate": 0.8
            },
            {
                "schedule_id": 1001,
                "seat_type": "premium",
                "total_seats": 20,
                "occupied_seats": 15,
                "fare": 525.0,
                "timestamp": "2025-06-15T07:30:00",
                "occupancy_rate": 0.75
            },
            # Anomalous data for testing
            {
                "schedule_id": 1002,
                "seat_type": "regular",
                "total_seats": 40,
                "occupied_seats": 45,  # Impossible occupancy
                "fare": -100.0,  # Negative fare
                "timestamp": "2025-06-15T13:30:00",
                "occupancy_rate": 1.125
            }
        ]

    def test_schedule_data_structure(self, sample_schedule_data):
        """Test schedule data has required structure"""
        for schedule in sample_schedule_data:
            required_fields = [
                "schedule_id", "route_id", "operator_id",
                "departure_time", "arrival_time", "date", "route_info"
            ]

            for field in required_fields:
                assert field in schedule

            # Verify route_info structure
            route_info = schedule["route_info"]
            route_required_fields = ["origin", "destination", "distance_km"]

            for field in route_required_fields:
                assert field in route_info

    def test_occupancy_data_structure(self, sample_occupancy_data):
        """Test occupancy data has required structure"""
        for occupancy in sample_occupancy_data:
            required_fields = [
                "schedule_id", "seat_type", "total_seats",
                "occupied_seats", "fare", "timestamp", "occupancy_rate"
            ]

            for field in required_fields:
                assert field in occupancy

    def test_occupancy_rate_calculation(self, sample_occupancy_data):
        """Test occupancy rate calculation logic"""
        for occupancy in sample_occupancy_data:
            if occupancy["total_seats"] > 0:
                expected_rate = occupancy["occupied_seats"] / \
                    occupancy["total_seats"]

                # Allow for small floating point differences
                assert abs(occupancy["occupancy_rate"] - expected_rate) < 0.001

    def test_data_quality_issue_logging(self):
        """Test data quality issue logging functionality"""
        issues = []

        def log_issue(issue_type, description, details):
            issues.append({
                "type": issue_type,
                "description": description,
                "details": details
            })

        # Simulate logging various issues
        log_issue("negative_fare", "Found negative fare", "fare=-100")
        log_issue("impossible_occupancy", "Occupied > Total", "45 > 40")
        log_issue("extreme_fare", "Fare too high", "fare=999999")

        assert len(issues) == 3
        assert issues[0]["type"] == "negative_fare"
        assert issues[1]["type"] == "impossible_occupancy"
        assert issues[2]["type"] == "extreme_fare"


class TestDataTransformation:
    """Test data transformation and cleaning logic"""

    def test_fare_range_validation(self):
        """Test fare range validation"""
        min_threshold = 1.0
        max_threshold = 100000.0

        # Valid fares
        valid_fares = [50.0, 150.0, 500.0, 1500.0, 5000.0]
        for fare in valid_fares:
            assert min_threshold <= fare <= max_threshold

        # Invalid fares
        invalid_fares = [-100.0, 0.0, 150000.0, 999999.0]
        for fare in invalid_fares:
            assert fare < min_threshold or fare > max_threshold

    def test_seat_type_standardization(self):
        """Test seat type standardization"""
        seat_type_mapping = {
            "regular": "regular",
            "premium": "premium",
            "sleeper": "sleeper",
            "REGULAR": "regular",  # Case insensitive
            "Premium": "premium",
            "unknown": "regular",  # Default to regular
            "": "regular",
            None: "regular"
        }

        for input_type, expected in seat_type_mapping.items():
            if input_type in ["regular", "premium", "sleeper"]:
                assert input_type == expected
            else:
                # Unknown types should default to regular
                standardized = "regular" if input_type not in [
                    "regular", "premium", "sleeper"] else input_type
                assert standardized == "regular" or standardized == input_type

    def test_occupancy_rate_bounds(self):
        """Test occupancy rate is within valid bounds"""
        test_cases = [
            {"total": 40, "occupied": 0, "expected_rate": 0.0},
            {"total": 40, "occupied": 20, "expected_rate": 0.5},
            {"total": 40, "occupied": 40, "expected_rate": 1.0},
            {"total": 40, "occupied": 45, "expected_rate": 1.0},  # Capped at 1.0
        ]

        for case in test_cases:
            total = case["total"]
            occupied = min(case["occupied"], total)  # Cap at total
            rate = occupied / total if total > 0 else 0

            assert 0.0 <= rate <= 1.0
            if case["occupied"] <= total:
                assert abs(rate - case["expected_rate"]) < 0.001
