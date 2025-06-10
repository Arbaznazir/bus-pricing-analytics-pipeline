"""
Pydantic schemas for request and response models

Defines the data validation and serialization schemas for the
Bus Pricing Pipeline API endpoints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum


class SeatType(str, Enum):
    """Enumeration of seat types"""
    REGULAR = "regular"
    PREMIUM = "premium"
    SLEEPER = "sleeper"


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "ok"
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    version: str = "1.0.0"


class RouteBase(BaseModel):
    """Base route schema"""
    origin: str = Field(..., min_length=1, max_length=100)
    destination: str = Field(..., min_length=1, max_length=100)
    distance_km: float = Field(..., gt=0)


class RouteResponse(RouteBase):
    """Route response schema"""
    route_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class OperatorBase(BaseModel):
    """Base operator schema"""
    name: str = Field(..., min_length=1, max_length=100)
    contact_email: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)


class OperatorResponse(OperatorBase):
    """Operator response schema"""
    operator_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduleBase(BaseModel):
    """Base schedule schema"""
    route_id: int
    operator_id: int
    departure_time: datetime
    arrival_time: datetime
    date: datetime

    @field_validator('arrival_time')
    def arrival_after_departure(cls, v, info):
        if info.data.get('departure_time') and v <= info.data['departure_time']:
            raise ValueError('Arrival time must be after departure time')
        return v


class ScheduleResponse(ScheduleBase):
    """Schedule response schema"""
    schedule_id: int
    is_active: bool
    route: Optional[RouteResponse] = None
    operator: Optional[OperatorResponse] = None

    class Config:
        from_attributes = True


class SeatOccupancyBase(BaseModel):
    """Base seat occupancy schema"""
    seat_type: SeatType
    total_seats: int = Field(..., gt=0)
    occupied_seats: int = Field(..., ge=0)
    fare: float = Field(..., gt=0)

    @field_validator('occupied_seats')
    def occupied_not_exceed_total(cls, v, info):
        if info.data.get('total_seats') and v > info.data['total_seats']:
            raise ValueError('Occupied seats cannot exceed total seats')
        return v


class SeatOccupancyResponse(SeatOccupancyBase):
    """Seat occupancy response schema"""
    id: int
    schedule_id: int
    occupancy_rate: Optional[float] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class ScheduleWithOccupancy(ScheduleResponse):
    """Schedule with occupancy data"""
    seat_occupancy: List[SeatOccupancyResponse] = []


class OccupancyStatsRequest(BaseModel):
    """Request schema for occupancy statistics"""
    route_id: Optional[int] = None
    date: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    seat_type: Optional[SeatType] = None

    @field_validator('date')
    def validate_date_format(cls, v):
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Date must be in YYYY-MM-DD format')
        return v


class OccupancyStats(BaseModel):
    """Occupancy statistics response"""
    route_id: Optional[int] = None
    seat_type: Optional[str] = None
    date_range: str
    total_schedules: int
    average_occupancy_rate: float
    min_occupancy_rate: float
    max_occupancy_rate: float
    average_fare: float
    min_fare: float
    max_fare: float
    total_seats_available: int
    total_seats_occupied: int


class PricingRequest(BaseModel):
    """Pricing suggestion request"""
    route_id: int = Field(..., gt=0)
    seat_type: SeatType
    current_occupancy_rate: float = Field(..., ge=0, le=1)
    departure_time: Optional[datetime] = None
    current_fare: Optional[float] = Field(None, gt=0)

    @field_validator('current_occupancy_rate')
    def validate_occupancy_rate(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Occupancy rate must be between 0 and 1')
        return v


class PricingSuggestion(BaseModel):
    """Pricing suggestion response"""
    route_id: int
    seat_type: str
    current_occupancy_rate: float
    current_fare: Optional[float] = None
    suggested_fare: float
    fare_adjustment_percentage: float
    confidence_score: float = Field(..., ge=0, le=1)
    reasoning: str
    model_version: str = "heuristic_v1"
    calculation_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class DataQualityIssue(BaseModel):
    """Data quality issue response"""
    issue_type: str
    description: str
    count: int
    severity: str  # low, medium, high, critical


class DataQualityReport(BaseModel):
    """Data quality report response"""
    report_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    total_records_processed: int
    valid_records: int
    invalid_records: int
    quality_score: float = Field(..., ge=0, le=1)
    issues: List[DataQualityIssue] = []


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: List[BaseModel]
    total: int
    page: int
    page_size: int
    total_pages: int

    @field_validator('total_pages', mode='before')
    def calculate_total_pages(cls, v, info):
        if info.data.get('total') and info.data.get('page_size'):
            return (info.data['total'] + info.data['page_size'] - 1) // info.data['page_size']
        return v
