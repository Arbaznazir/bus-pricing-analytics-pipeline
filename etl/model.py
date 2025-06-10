"""
Pricing Model for Bus Seat Occupancy & Dynamic Pricing

Implements heuristic-based pricing algorithms that consider:
- Current occupancy rates
- Route characteristics  
- Seat types
- Time-based factors
- Historical pricing patterns
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


class HeuristicPricingModel:
    """
    Heuristic-based pricing model for bus seat pricing

    This model uses business rules and heuristics rather than machine learning
    to provide realistic pricing suggestions based on various factors.
    """

    def __init__(self):
        self.model_version = "heuristic_v1"

        # Base pricing parameters (configurable via environment)
        self.base_rates = {
            "regular": 2.5,      # Base rate per km for regular seats
            "premium": 3.5,      # Base rate per km for premium seats
            "sleeper": 4.0       # Base rate per km for sleeper seats
        }

        # Occupancy-based multipliers
        self.occupancy_thresholds = {
            "high": 0.8,         # Above 80% occupancy
            "medium": 0.5,       # 50-80% occupancy
            "low": 0.3           # Below 30% occupancy
        }

        # Time-based factors
        self.peak_hours = [7, 8, 9, 17, 18, 19]      # Peak travel hours
        self.off_peak_hours = [22, 23, 0, 1, 2, 3, 4, 5]  # Off-peak hours

        # Route distance categories
        self.distance_categories = {
            "short": (0, 200),      # Up to 200 km
            "medium": (200, 400),   # 200-400 km
            "long": (400, float('inf'))  # Above 400 km
        }

    def calculate_base_fare(self, distance_km: float, seat_type: str) -> float:
        """
        Calculate base fare based on distance and seat type

        Args:
            distance_km: Route distance in kilometers
            seat_type: Type of seat (regular, premium, sleeper)

        Returns:
            Base fare amount
        """
        if seat_type not in self.base_rates:
            logger.warning(
                f"Unknown seat type: {seat_type}, using regular rate")
            seat_type = "regular"

        # Distance-based rate adjustment
        if distance_km <= self.distance_categories["short"][1]:
            rate_multiplier = 1.0
        elif distance_km <= self.distance_categories["medium"][1]:
            rate_multiplier = 0.9  # Slightly lower rate for medium distance
        else:
            rate_multiplier = 0.8  # Lower rate for long distance

        base_rate = self.base_rates[seat_type] * rate_multiplier
        base_fare = distance_km * base_rate

        return round(base_fare, 2)

    def get_occupancy_adjustment(self, occupancy_rate: float) -> Tuple[float, str]:
        """
        Calculate fare adjustment based on occupancy rate

        Args:
            occupancy_rate: Current occupancy rate (0.0 to 1.0)

        Returns:
            Tuple of (adjustment_factor, reasoning)
        """
        if occupancy_rate >= self.occupancy_thresholds["high"]:
            # High occupancy - increase price
            adjustment = 1.0 + (occupancy_rate - 0.8) * \
                2.5  # Up to 50% increase
            reasoning = f"High occupancy ({occupancy_rate:.1%}) increases demand"
        elif occupancy_rate <= self.occupancy_thresholds["low"]:
            # Low occupancy - decrease price to attract customers
            adjustment = 1.0 - (0.3 - occupancy_rate) * \
                0.67  # Up to 20% decrease
            reasoning = f"Low occupancy ({occupancy_rate:.1%}) suggests price reduction"
        else:
            # Medium occupancy - maintain base pricing
            adjustment = 1.0
            reasoning = f"Moderate occupancy ({occupancy_rate:.1%}) maintains base pricing"

        return round(adjustment, 3), reasoning

    def get_time_adjustment(self, departure_time: Optional[datetime] = None) -> Tuple[float, str]:
        """
        Calculate fare adjustment based on departure time

        Args:
            departure_time: Scheduled departure time

        Returns:
            Tuple of (adjustment_factor, reasoning)
        """
        if not departure_time:
            return 1.0, "No time information available"

        departure_hour = departure_time.hour
        reasoning_parts = []

        # Hour-based adjustment
        if departure_hour in self.peak_hours:
            hour_adjustment = 1.15
            reasoning_parts.append("Peak hour timing increases price")
        elif departure_hour in self.off_peak_hours:
            hour_adjustment = 0.9
            reasoning_parts.append("Off-peak timing reduces price")
        else:
            hour_adjustment = 1.0
            reasoning_parts.append("Standard timing")

        # Time to departure adjustment
        time_to_departure = (
            departure_time - datetime.utcnow()).total_seconds() / 3600

        if time_to_departure < 2:  # Less than 2 hours
            urgency_adjustment = 1.2
            reasoning_parts.append("Last-minute booking premium")
        elif time_to_departure > 24 * 7:  # More than a week
            urgency_adjustment = 0.95
            reasoning_parts.append("Early booking discount")
        else:
            urgency_adjustment = 1.0

        total_adjustment = hour_adjustment * urgency_adjustment
        reasoning = "; ".join(reasoning_parts)

        return round(total_adjustment, 3), reasoning

    def get_route_adjustment(self, distance_km: float, seat_type: str) -> Tuple[float, str]:
        """
        Calculate fare adjustment based on route characteristics

        Args:
            distance_km: Route distance in kilometers
            seat_type: Type of seat

        Returns:
            Tuple of (adjustment_factor, reasoning)
        """
        reasoning_parts = []
        adjustment = 1.0

        # Long-distance route premium for sleeper seats
        if distance_km > 500 and seat_type == "sleeper":
            adjustment *= 1.1
            reasoning_parts.append("Long-distance sleeper premium")

        # Short-distance penalty for premium seats (less value)
        if distance_km < 100 and seat_type == "premium":
            adjustment *= 0.95
            reasoning_parts.append("Short-distance premium seat adjustment")

        if not reasoning_parts:
            reasoning_parts.append("Standard route pricing")

        reasoning = "; ".join(reasoning_parts)
        return round(adjustment, 3), reasoning

    def apply_business_constraints(self,
                                   suggested_fare: float,
                                   base_fare: float) -> Tuple[float, str]:
        """
        Apply business constraints to ensure fare is within acceptable bounds

        Args:
            suggested_fare: Initial suggested fare
            base_fare: Base fare for comparison

        Returns:
            Tuple of (constrained_fare, reasoning)
        """
        reasoning_parts = []

        # Set minimum and maximum bounds
        min_fare = base_fare * 0.7   # Never go below 70% of base
        max_fare = base_fare * 2.5   # Never go above 250% of base

        constrained_fare = suggested_fare

        if suggested_fare < min_fare:
            constrained_fare = min_fare
            reasoning_parts.append(
                f"Applied minimum fare constraint ({min_fare:.2f})")
        elif suggested_fare > max_fare:
            constrained_fare = max_fare
            reasoning_parts.append(
                f"Applied maximum fare constraint ({max_fare:.2f})")

        # Round to nearest 5 (business preference)
        constrained_fare = round(constrained_fare / 5) * 5

        if constrained_fare != suggested_fare:
            reasoning_parts.append("Rounded to nearest 5")

        reasoning = "; ".join(
            reasoning_parts) if reasoning_parts else "No constraints applied"

        return constrained_fare, reasoning

    def calculate_confidence_score(self,
                                   historical_data_points: int,
                                   route_popularity: float = 0.5) -> float:
        """
        Calculate confidence score for the pricing suggestion

        Args:
            historical_data_points: Number of historical data points available
            route_popularity: Route popularity score (0.0 to 1.0)

        Returns:
            Confidence score (0.0 to 1.0)
        """
        base_confidence = 0.7

        # Adjust based on historical data availability
        if historical_data_points >= 50:
            data_confidence = 0.3
        elif historical_data_points >= 20:
            data_confidence = 0.2
        elif historical_data_points >= 10:
            data_confidence = 0.1
        else:
            data_confidence = 0.0

        # Adjust based on route popularity (more popular = more predictable)
        popularity_confidence = route_popularity * 0.1

        total_confidence = base_confidence + data_confidence + popularity_confidence
        return round(min(total_confidence, 1.0), 2)

    def suggest_pricing(self,
                        route_distance_km: float,
                        seat_type: str,
                        current_occupancy_rate: float,
                        departure_time: Optional[datetime] = None,
                        current_fare: Optional[float] = None,
                        historical_data_points: int = 0) -> Dict[str, Any]:
        """
        Main method to calculate pricing suggestion

        Args:
            route_distance_km: Route distance in kilometers
            seat_type: Type of seat (regular, premium, sleeper)
            current_occupancy_rate: Current occupancy rate (0.0 to 1.0)
            departure_time: Scheduled departure time
            current_fare: Current fare (if available)
            historical_data_points: Number of historical data points

        Returns:
            Dictionary containing pricing suggestion and details
        """
        try:
            # Validate input parameters
            validate_pricing_input(
                route_distance_km, seat_type, current_occupancy_rate)
            # Calculate base fare
            base_fare = self.calculate_base_fare(route_distance_km, seat_type)

            # If current fare is provided, use it as base (more accurate)
            if current_fare and current_fare > 0:
                base_fare = current_fare

            # Get adjustment factors
            occupancy_adj, occupancy_reason = self.get_occupancy_adjustment(
                current_occupancy_rate)
            time_adj, time_reason = self.get_time_adjustment(departure_time)
            route_adj, route_reason = self.get_route_adjustment(
                route_distance_km, seat_type)

            # Calculate suggested fare
            total_adjustment = occupancy_adj * time_adj * route_adj
            suggested_fare = base_fare * total_adjustment

            # Apply business constraints
            final_fare, constraint_reason = self.apply_business_constraints(
                suggested_fare, base_fare)

            # Calculate percentage change
            fare_change_pct = ((final_fare - base_fare) / base_fare) * 100

            # Calculate confidence score
            confidence = self.calculate_confidence_score(
                historical_data_points)

            # Compile reasoning
            reasoning_parts = [occupancy_reason, time_reason, route_reason]
            if constraint_reason != "No constraints applied":
                reasoning_parts.append(constraint_reason)

            reasoning = "; ".join(part for part in reasoning_parts if part)

            result = {
                "suggested_fare": final_fare,
                "base_fare": base_fare,
                "fare_adjustment_percentage": round(fare_change_pct, 1),
                "confidence_score": confidence,
                "reasoning": reasoning,
                "model_version": self.model_version,
                "adjustment_factors": {
                    "occupancy": occupancy_adj,
                    "time": time_adj,
                    "route": route_adj,
                    "total": total_adjustment
                }
            }

            logger.info(f"Pricing suggestion calculated: {final_fare:.2f} "
                        f"(change: {fare_change_pct:+.1f}%, confidence: {confidence})")

            return result

        except Exception as e:
            logger.error(f"Error calculating pricing suggestion: {e}")
            raise ValueError(f"Failed to calculate pricing: {str(e)}")


def create_pricing_model() -> HeuristicPricingModel:
    """Factory function to create a pricing model instance"""
    return HeuristicPricingModel()


# Utility functions for data validation and preprocessing
def validate_pricing_input(route_distance_km: float,
                           seat_type: str,
                           current_occupancy_rate: float) -> bool:
    """
    Validate input parameters for pricing calculation

    Args:
        route_distance_km: Route distance
        seat_type: Seat type
        current_occupancy_rate: Occupancy rate

    Returns:
        True if valid, raises ValueError if invalid
    """
    if route_distance_km <= 0:
        raise ValueError("Route distance must be positive")

    if seat_type not in ["regular", "premium", "sleeper"]:
        raise ValueError(f"Invalid seat type: {seat_type}")

    if not 0 <= current_occupancy_rate <= 1:
        raise ValueError("Occupancy rate must be between 0 and 1")

    return True


def calculate_route_popularity(historical_occupancy_rates: list) -> float:
    """
    Calculate route popularity based on historical occupancy rates

    Args:
        historical_occupancy_rates: List of historical occupancy rates

    Returns:
        Popularity score (0.0 to 1.0)
    """
    if not historical_occupancy_rates:
        return 0.5  # Default neutral popularity

    avg_occupancy = statistics.mean(historical_occupancy_rates)
    consistency = 1.0 - \
        statistics.stdev(historical_occupancy_rates) if len(
            historical_occupancy_rates) > 1 else 1.0

    # Combine average occupancy and consistency for popularity score
    popularity = (avg_occupancy * 0.7) + (consistency * 0.3)
    return round(min(max(popularity, 0.0), 1.0), 2)
