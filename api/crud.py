"""
CRUD operations for the Bus Pricing Pipeline

Database operations for routes, schedules, seat occupancy, and analytics.
Includes business logic for pricing suggestions and data quality reporting.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from . import models, schemas

logger = logging.getLogger(__name__)


def get_route(db: Session, route_id: int) -> Optional[models.Route]:
    """Get a single route by ID"""
    return db.query(models.Route).filter(models.Route.route_id == route_id).first()


def get_routes(db: Session, skip: int = 0, limit: int = 100) -> List[models.Route]:
    """Get all routes with pagination"""
    return db.query(models.Route).offset(skip).limit(limit).all()


def get_operators(db: Session, skip: int = 0, limit: int = 100) -> List[models.Operator]:
    """Get all operators with pagination"""
    return db.query(models.Operator).filter(models.Operator.is_active == True).offset(skip).limit(limit).all()


def get_schedules_by_route_and_date(
    db: Session,
    route_id: int,
    date: str,
    skip: int = 0,
    limit: int = 100
) -> List[models.Schedule]:
    """Get schedules for a specific route and date"""
    target_date = datetime.strptime(date, '%Y-%m-%d').date()
    return (
        db.query(models.Schedule)
        .options(joinedload(models.Schedule.route), joinedload(models.Schedule.operator))
        .filter(
            and_(
                models.Schedule.route_id == route_id,
                func.date(models.Schedule.date) == target_date,
                models.Schedule.is_active == True
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_schedule_with_occupancy(db: Session, schedule_id: int) -> Optional[models.Schedule]:
    """Get a schedule with its seat occupancy data"""
    return (
        db.query(models.Schedule)
        .options(
            joinedload(models.Schedule.route),
            joinedload(models.Schedule.operator),
            joinedload(models.Schedule.seat_occupancy)
        )
        .filter(models.Schedule.schedule_id == schedule_id)
        .first()
    )


def get_occupancy_stats(
    db: Session,
    route_id: Optional[int] = None,
    date: Optional[str] = None,
    seat_type: Optional[str] = None
) -> schemas.OccupancyStats:
    """Calculate occupancy statistics with optional filters"""

    # Base query
    query = db.query(models.SeatOccupancy).join(models.Schedule)

    # Apply filters
    filters = []
    if route_id:
        filters.append(models.Schedule.route_id == route_id)

    if date:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        filters.append(func.date(models.Schedule.date) == target_date)

    if seat_type:
        filters.append(models.SeatOccupancy.seat_type == seat_type)

    if filters:
        query = query.filter(and_(*filters))

    # Calculate statistics
    occupancy_records = query.all()

    if not occupancy_records:
        return schemas.OccupancyStats(
            route_id=route_id,
            seat_type=seat_type,
            date_range=date or "all dates",
            total_schedules=0,
            average_occupancy_rate=0,
            min_occupancy_rate=0,
            max_occupancy_rate=0,
            average_fare=0,
            min_fare=0,
            max_fare=0,
            total_seats_available=0,
            total_seats_occupied=0
        )

    # Calculate metrics
    occupancy_rates = [
        record.occupancy_rate or 0 for record in occupancy_records]
    fares = [record.fare for record in occupancy_records]
    total_seats = sum(record.total_seats for record in occupancy_records)
    occupied_seats = sum(record.occupied_seats for record in occupancy_records)

    # Get unique schedule count
    unique_schedules = len(
        set(record.schedule_id for record in occupancy_records))

    return schemas.OccupancyStats(
        route_id=route_id,
        seat_type=seat_type,
        date_range=date or "all dates",
        total_schedules=unique_schedules,
        average_occupancy_rate=round(
            sum(occupancy_rates) / len(occupancy_rates), 3),
        min_occupancy_rate=round(min(occupancy_rates), 3),
        max_occupancy_rate=round(max(occupancy_rates), 3),
        average_fare=round(sum(fares) / len(fares), 2),
        min_fare=round(min(fares), 2),
        max_fare=round(max(fares), 2),
        total_seats_available=total_seats,
        total_seats_occupied=occupied_seats
    )


def calculate_pricing_suggestion(
    db: Session,
    pricing_request: schemas.PricingRequest
) -> schemas.PricingSuggestion:
    """
    Calculate pricing suggestion using heuristic model

    Business logic:
    - High occupancy (>80%) -> increase price up to 50%
    - Low occupancy (<30%) -> decrease price up to 20%
    - Peak hours -> premium pricing
    - Route distance affects base pricing
    """

    # Get route information
    route = get_route(db, pricing_request.route_id)
    if not route:
        raise ValueError(f"Route {pricing_request.route_id} not found")

    # Get historical pricing data for this route and seat type
    historical_data = (
        db.query(models.SeatOccupancy)
        .join(models.Schedule)
        .filter(
            and_(
                models.Schedule.route_id == pricing_request.route_id,
                models.SeatOccupancy.seat_type == pricing_request.seat_type.value
            )
        )
        .order_by(desc(models.SeatOccupancy.timestamp))
        .limit(50)  # Last 50 records
        .all()
    )

    # Calculate base fare from historical data or use provided current fare
    if pricing_request.current_fare:
        base_fare = pricing_request.current_fare
    elif historical_data:
        base_fare = sum(
            record.fare for record in historical_data) / len(historical_data)
    else:
        # Fallback: calculate based on distance and seat type
        rate_per_km = 2.5 if pricing_request.seat_type == schemas.SeatType.REGULAR else 3.5
        base_fare = route.distance_km * rate_per_km

    # Initialize adjustment factors
    occupancy_adjustment = 1.0
    time_adjustment = 1.0
    demand_adjustment = 1.0
    confidence_score = 0.8
    reasoning_parts = []

    # Occupancy-based adjustment
    occupancy_rate = pricing_request.current_occupancy_rate
    if occupancy_rate > 0.8:
        occupancy_adjustment = 1.0 + \
            (occupancy_rate - 0.8) * 2.5  # Up to 50% increase
        reasoning_parts.append(
            f"High occupancy ({occupancy_rate:.1%}) increases demand")
    elif occupancy_rate < 0.3:
        occupancy_adjustment = 1.0 - \
            (0.3 - occupancy_rate) * 0.67  # Up to 20% decrease
        reasoning_parts.append(
            f"Low occupancy ({occupancy_rate:.1%}) suggests price reduction")
    else:
        reasoning_parts.append(
            f"Moderate occupancy ({occupancy_rate:.1%}) maintains base pricing")

    # Time-based adjustment (if departure time provided)
    if pricing_request.departure_time:
        departure_hour = pricing_request.departure_time.hour
        if departure_hour in [7, 8, 9, 17, 18, 19]:  # Peak hours
            time_adjustment = 1.15
            reasoning_parts.append("Peak hour timing increases price")
        elif departure_hour in [22, 23, 0, 1, 2, 3, 4, 5]:  # Off-peak hours
            time_adjustment = 0.9
            reasoning_parts.append("Off-peak timing reduces price")

        # Time to departure factor
        time_to_departure = (pricing_request.departure_time -
                             datetime.utcnow()).total_seconds() / 3600
        if time_to_departure < 2:  # Less than 2 hours
            demand_adjustment = 1.2
            reasoning_parts.append("Last-minute booking premium applied")
            confidence_score = min(confidence_score + 0.1, 1.0)
        elif time_to_departure > 24 * 7:  # More than a week
            demand_adjustment = 0.95
            reasoning_parts.append("Early booking discount applied")

    # Route-specific adjustments
    if route.distance_km > 500:  # Long-distance routes
        if pricing_request.seat_type == schemas.SeatType.SLEEPER:
            demand_adjustment *= 1.1
            reasoning_parts.append("Long-distance sleeper premium")

    # Calculate final suggested fare
    total_adjustment = occupancy_adjustment * time_adjustment * demand_adjustment
    suggested_fare = base_fare * total_adjustment

    # Apply bounds (10% below to 100% above base fare)
    min_fare = base_fare * 0.9
    max_fare = base_fare * 2.0
    suggested_fare = max(min_fare, min(suggested_fare, max_fare))

    # Calculate percentage adjustment
    fare_adjustment_percentage = (
        (suggested_fare - base_fare) / base_fare) * 100

    # Adjust confidence based on data availability
    if len(historical_data) < 10:
        confidence_score *= 0.8
        reasoning_parts.append("Limited historical data reduces confidence")

    reasoning = "; ".join(reasoning_parts)

    # Store the pricing result for future reference
    try:
        pricing_result = models.PricingModelResult(
            schedule_id=None,  # This would be set if we had a specific schedule
            seat_type=pricing_request.seat_type.value,
            current_occupancy_rate=occupancy_rate,
            current_fare=pricing_request.current_fare or base_fare,
            suggested_fare=suggested_fare,
            fare_adjustment_percentage=fare_adjustment_percentage,
            confidence_score=confidence_score,
            reasoning=reasoning
        )
        db.add(pricing_result)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to store pricing result: {e}")
        db.rollback()

    return schemas.PricingSuggestion(
        route_id=pricing_request.route_id,
        seat_type=pricing_request.seat_type.value,
        current_occupancy_rate=occupancy_rate,
        current_fare=pricing_request.current_fare,
        suggested_fare=round(suggested_fare, 2),
        fare_adjustment_percentage=round(fare_adjustment_percentage, 1),
        confidence_score=round(confidence_score, 2),
        reasoning=reasoning
    )


def get_data_quality_report(db: Session, days_back: int = 7) -> schemas.DataQualityReport:
    """Generate a data quality report for the last N days"""

    start_date = datetime.utcnow() - timedelta(days=days_back)

    # Get data quality issues
    quality_issues = (
        db.query(models.DataQualityLog)
        .filter(models.DataQualityLog.detected_at >= start_date)
        .all()
    )

    # Get total records processed (from seat occupancy)
    total_occupancy_records = (
        db.query(models.SeatOccupancy)
        .filter(models.SeatOccupancy.created_at >= start_date)
        .count()
    )

    # Aggregate issues by type
    issue_counts = {}
    for issue in quality_issues:
        issue_type = issue.issue_type
        if issue_type not in issue_counts:
            issue_counts[issue_type] = 0
        issue_counts[issue_type] += 1

    # Create issue summaries
    issue_summaries = []
    for issue_type, count in issue_counts.items():
        severity = "high" if count > total_occupancy_records * \
            0.1 else "medium" if count > total_occupancy_records * 0.05 else "low"
        issue_summaries.append(
            schemas.DataQualityIssue(
                issue_type=issue_type,
                description=f"Issues of type {issue_type} found in data",
                count=count,
                severity=severity
            )
        )

    # Calculate quality score
    total_issues = len(quality_issues)
    if total_occupancy_records > 0:
        quality_score = max(0, 1 - (total_issues / total_occupancy_records))
    else:
        quality_score = 1.0

    return schemas.DataQualityReport(
        total_records_processed=total_occupancy_records,
        valid_records=total_occupancy_records - total_issues,
        invalid_records=total_issues,
        quality_score=round(quality_score, 3),
        issues=issue_summaries
    )


def create_or_update_route(db: Session, route: dict) -> models.Route:
    """Create or update a route"""
    existing_route = (
        db.query(models.Route)
        .filter(
            and_(
                models.Route.origin == route["origin"],
                models.Route.destination == route["destination"]
            )
        )
        .first()
    )

    if existing_route:
        existing_route.distance_km = route["distance_km"]
        existing_route.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_route)
        return existing_route
    else:
        new_route = models.Route(**route)
        db.add(new_route)
        db.commit()
        db.refresh(new_route)
        return new_route


def create_or_update_operator(db: Session, operator: dict) -> models.Operator:
    """Create or update an operator"""
    existing_operator = (
        db.query(models.Operator)
        .filter(models.Operator.name == operator["name"])
        .first()
    )

    if existing_operator:
        for key, value in operator.items():
            if key != "operator_id":
                setattr(existing_operator, key, value)
        existing_operator.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_operator)
        return existing_operator
    else:
        new_operator = models.Operator(**operator)
        db.add(new_operator)
        db.commit()
        db.refresh(new_operator)
        return new_operator
