"""
SQLAlchemy database models for the bus pricing system
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Route(Base):
    """Route model representing bus routes"""
    __tablename__ = "routes"

    route_id = Column(Integer, primary_key=True, index=True)
    origin = Column(String(100), nullable=False, index=True)
    destination = Column(String(100), nullable=False, index=True)
    distance_km = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    schedules = relationship("Schedule", back_populates="route")

    def __repr__(self):
        return f"<Route(route_id={self.route_id}, origin={self.origin}, destination={self.destination})>"


class Operator(Base):
    """Operator model representing bus operators"""
    __tablename__ = "operators"

    operator_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    contact_email = Column(String(100), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    schedules = relationship("Schedule", back_populates="operator")

    def __repr__(self):
        return f"<Operator(operator_id={self.operator_id}, name={self.name})>"


class Schedule(Base):
    """Schedule model representing bus schedules"""
    __tablename__ = "schedules"

    schedule_id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.route_id"),
                      nullable=False, index=True)
    operator_id = Column(Integer, ForeignKey(
        "operators.operator_id"), nullable=False, index=True)
    departure_time = Column(DateTime(timezone=True),
                            nullable=False, index=True)
    arrival_time = Column(DateTime(timezone=True), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    route = relationship("Route", back_populates="schedules")
    operator = relationship("Operator", back_populates="schedules")
    seat_occupancy = relationship("SeatOccupancy", back_populates="schedule")

    def __repr__(self):
        return f"<Schedule(schedule_id={self.schedule_id}, route_id={self.route_id}, departure_time={self.departure_time})>"


class SeatOccupancy(Base):
    """Seat occupancy model representing seat occupancy data"""
    __tablename__ = "seat_occupancy"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey(
        "schedules.schedule_id"), nullable=False, index=True)
    # regular, premium, sleeper
    seat_type = Column(String(20), nullable=False, index=True)
    total_seats = Column(Integer, nullable=False)
    occupied_seats = Column(Integer, nullable=False)
    fare = Column(Float, nullable=False)
    occupancy_rate = Column(Float, nullable=True)  # Calculated field
    timestamp = Column(DateTime(timezone=True),
                       server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    schedule = relationship("Schedule", back_populates="seat_occupancy")

    def __repr__(self):
        return f"<SeatOccupancy(id={self.id}, schedule_id={self.schedule_id}, seat_type={self.seat_type}, occupancy_rate={self.occupancy_rate})>"


class DataQualityLog(Base):
    """Data quality log model for tracking data issues"""
    __tablename__ = "data_quality_log"

    id = Column(Integer, primary_key=True, index=True)
    issue_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    record_id = Column(String(100), nullable=True, index=True)
    # low, medium, high, critical
    severity = Column(String(20), nullable=False, default="medium")
    resolved = Column(Boolean, default=False, nullable=False)
    resolution_action = Column(Text, nullable=True)
    detected_at = Column(DateTime(timezone=True),
                         server_default=func.now(), index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<DataQualityLog(id={self.id}, issue_type={self.issue_type}, severity={self.severity})>"


class PricingModelResult(Base):
    """Pricing model results for tracking pricing suggestions"""
    __tablename__ = "pricing_model_results"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey(
        "schedules.schedule_id"), nullable=True, index=True)
    seat_type = Column(String(20), nullable=False)
    current_occupancy_rate = Column(Float, nullable=False)
    current_fare = Column(Float, nullable=True)
    suggested_fare = Column(Float, nullable=False)
    fare_adjustment_percentage = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=False)
    model_version = Column(String(20), nullable=False, default="heuristic_v1")
    calculation_timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationship
    schedule = relationship("Schedule")

    def __repr__(self):
        return f"<PricingModelResult(id={self.id}, schedule_id={self.schedule_id}, suggested_fare={self.suggested_fare})>"


class SystemHealth(Base):
    """System health tracking model"""
    __tablename__ = "system_health"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False)  # healthy, unhealthy, degraded
    response_time_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    checked_at = Column(DateTime(timezone=True),
                        server_default=func.now(), index=True)

    def __repr__(self):
        return f"<SystemHealth(id={self.id}, service_name={self.service_name}, status={self.status})>"
