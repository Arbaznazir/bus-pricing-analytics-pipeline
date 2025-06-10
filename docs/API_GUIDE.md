# 📡 NOVA Bus Pricing Pipeline - API Guide

## 🎯 Overview

The NOVA Bus Pricing API provides comprehensive endpoints for bus schedule analytics, dynamic pricing recommendations, and data quality monitoring. Built with FastAPI, it offers automatic documentation, request validation, and high-performance async operations.

**Base URL**: `http://localhost:8000`  
**Interactive Documentation**: `http://localhost:8000/docs`  
**Alternative Docs**: `http://localhost:8000/redoc`

## 🚀 Quick Start

### Authentication

Currently, the API operates without authentication for demonstration purposes. In production, implement:

- JWT tokens for user authentication
- API keys for service-to-service communication
- Rate limiting for abuse prevention

### Response Format

All API responses follow a consistent JSON structure:

```json
{
  "data": { ... },
  "status": "success|error",
  "message": "Description",
  "timestamp": "2025-06-15T10:30:00Z"
}
```

### Error Handling

HTTP status codes follow REST conventions:

- `200`: Success
- `400`: Bad Request (validation errors)
- `404`: Resource Not Found
- `422`: Unprocessable Entity (invalid data)
- `500`: Internal Server Error

## 📋 Core Endpoints

### 🏥 Health & Status

#### **GET** `/health`

**Purpose**: Check API service health and database connectivity.

**Response**:

```json
{
  "status": "healthy",
  "timestamp": "2025-06-15T10:30:00.000Z",
  "database_status": "connected",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

**Use Cases**:

- Load balancer health checks
- Monitoring system integration
- Service availability verification

#### **GET** `/stats/summary`

**Purpose**: Get overall system statistics and data counts.

**Response**:

```json
{
  "total_routes": 8,
  "total_operators": 6,
  "total_schedules": 150,
  "total_occupancy_records": 450,
  "data_quality_score": 0.95,
  "last_updated": "2025-06-15T10:25:00.000Z"
}
```

## 🛣️ Route Management

#### **GET** `/routes`

**Purpose**: Retrieve all available bus routes.

**Query Parameters**:

- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

**Response**:

```json
[
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
  }
]
```

#### **GET** `/routes/{route_id}`

**Purpose**: Get detailed information about a specific route.

**Path Parameters**:

- `route_id`: Unique route identifier

**Response**:

```json
{
  "route_id": 1,
  "origin": "Mumbai",
  "destination": "Pune",
  "distance_km": 148.0,
  "active_schedules": 25,
  "average_occupancy": 0.72,
  "popular_times": ["08:00", "18:00"],
  "price_range": {
    "min": 280.0,
    "max": 650.0
  }
}
```

## 🚌 Operator Management

#### **GET** `/operators`

**Purpose**: Retrieve all bus operators.

**Query Parameters**:

- `active_only` (optional): Filter for active operators only (default: true)
- `skip` (optional): Pagination offset
- `limit` (optional): Results limit

**Response**:

```json
[
  {
    "operator_id": 1,
    "name": "RedBus Express",
    "contact_email": "contact@redbusexpress.com",
    "is_active": true,
    "total_routes": 5,
    "fleet_size": 45
  }
]
```

## 📅 Schedule Management

#### **GET** `/schedules`

**Purpose**: Retrieve bus schedules with optional filtering.

**Query Parameters**:

- `route_id` (optional): Filter by specific route
- `operator_id` (optional): Filter by operator
- `date` (optional): Filter by departure date (YYYY-MM-DD)
- `from_time` (optional): Filter schedules after time (HH:MM)
- `to_time` (optional): Filter schedules before time (HH:MM)

**Response**:

```json
[
  {
    "schedule_id": 1001,
    "route_id": 1,
    "operator_id": 1,
    "departure_time": "2025-06-15T08:00:00",
    "arrival_time": "2025-06-15T11:30:00",
    "route_info": {
      "origin": "Mumbai",
      "destination": "Pune",
      "distance_km": 148.0
    },
    "operator_name": "RedBus Express"
  }
]
```

## 📊 Analytics Endpoints

#### **GET** `/analytics/occupancy`

**Purpose**: Get comprehensive occupancy analytics with filtering options.

**Query Parameters**:

- `route_id` (optional): Specific route analysis
- `operator_id` (optional): Specific operator analysis
- `seat_type` (optional): Filter by seat type (regular, premium, sleeper)
- `days_back` (optional): Historical data period (default: 7)
- `min_occupancy` (optional): Minimum occupancy rate filter
- `max_occupancy` (optional): Maximum occupancy rate filter

**Response**:

```json
{
  "total_schedules": 150,
  "total_seats_available": 6750,
  "total_seats_occupied": 4860,
  "average_occupancy_rate": 0.72,
  "average_fare": 425.5,
  "occupancy_distribution": {
    "0-25%": 15,
    "26-50%": 25,
    "51-75%": 65,
    "76-100%": 45
  },
  "seat_type_breakdown": {
    "regular": {
      "avg_occupancy": 0.75,
      "avg_fare": 350.0,
      "total_seats": 4200
    },
    "premium": {
      "avg_occupancy": 0.68,
      "avg_fare": 525.0,
      "total_seats": 1800
    },
    "sleeper": {
      "avg_occupancy": 0.7,
      "avg_fare": 750.0,
      "total_seats": 750
    }
  },
  "peak_hours": [
    { "hour": 8, "avg_occupancy": 0.85 },
    { "hour": 18, "avg_occupancy": 0.82 }
  ],
  "date_range": {
    "from": "2025-06-08",
    "to": "2025-06-15"
  }
}
```

#### **GET** `/analytics/route/{route_id}`

**Purpose**: Detailed analytics for a specific route.

**Path Parameters**:

- `route_id`: Route identifier

**Query Parameters**:

- `days_back` (optional): Analysis period (default: 7)

**Response**:

```json
{
  "route_id": 1,
  "route_info": {
    "origin": "Mumbai",
    "destination": "Pune",
    "distance_km": 148.0
  },
  "performance_metrics": {
    "total_schedules": 42,
    "average_occupancy_rate": 0.78,
    "revenue_per_km": 12.5,
    "popular_departure_times": ["08:00", "14:00", "18:00"]
  },
  "occupancy_trends": [
    { "date": "2025-06-15", "avg_occupancy": 0.82 },
    { "date": "2025-06-14", "avg_occupancy": 0.75 }
  ],
  "fare_analysis": {
    "average_fare": 375.0,
    "min_fare": 280.0,
    "max_fare": 550.0,
    "fare_by_seat_type": {
      "regular": 350.0,
      "premium": 525.0
    }
  }
}
```

## 💰 Dynamic Pricing Engine

#### **POST** `/pricing/suggest`

**Purpose**: Get intelligent pricing recommendations based on current conditions.

**Request Body**:

```json
{
  "route_id": 1,
  "seat_type": "regular",
  "current_occupancy_rate": 0.75,
  "departure_time": "2025-06-15T08:00:00",
  "current_fare": 350.0,
  "historical_data_points": 30
}
```

**Response**:

```json
{
  "suggested_fare": 385.0,
  "base_fare": 350.0,
  "fare_adjustment_percentage": 10.0,
  "confidence_score": 0.85,
  "reasoning": "High occupancy (75%) during peak hour (8 AM) suggests strong demand. Recommended 10% increase to optimize revenue while maintaining competitiveness.",
  "model_version": "heuristic_v1",
  "adjustment_factors": {
    "occupancy_adjustment": 1.15,
    "time_adjustment": 1.05,
    "route_adjustment": 0.95,
    "business_constraints": "applied"
  },
  "alternative_scenarios": [
    {
      "scenario": "conservative",
      "suggested_fare": 370.0,
      "reasoning": "Lower adjustment for risk-averse pricing"
    },
    {
      "scenario": "aggressive",
      "suggested_fare": 400.0,
      "reasoning": "Maximum revenue optimization"
    }
  ]
}
```

**Validation Rules**:

- `route_id`: Must exist in database
- `seat_type`: One of ["regular", "premium", "sleeper"]
- `current_occupancy_rate`: Between 0.0 and 1.0
- `departure_time`: Valid ISO 8601 datetime
- `current_fare`: Positive number

#### **GET** `/pricing/history`

**Purpose**: Retrieve historical pricing suggestions and their outcomes.

**Query Parameters**:

- `route_id` (optional): Filter by route
- `days_back` (optional): Historical period (default: 30)
- `limit` (optional): Maximum records (default: 50)

**Response**:

```json
[
  {
    "calculation_id": "uuid-123",
    "route_id": 1,
    "seat_type": "regular",
    "suggested_fare": 385.0,
    "confidence_score": 0.85,
    "calculation_timestamp": "2025-06-15T08:00:00Z",
    "input_parameters": {
      "occupancy_rate": 0.75,
      "departure_time": "2025-06-15T08:00:00"
    }
  }
]
```

## 🔍 Data Quality Monitoring

#### **GET** `/data-quality/report`

**Purpose**: Comprehensive data quality assessment and metrics.

**Query Parameters**:

- `days_back` (optional): Report period (default: 7)
- `severity` (optional): Filter by issue severity (low, medium, high)

**Response**:

```json
{
  "overall_quality_score": 0.94,
  "report_period": {
    "from": "2025-06-08",
    "to": "2025-06-15"
  },
  "data_summary": {
    "total_records_processed": 1250,
    "valid_records": 1175,
    "invalid_records": 75,
    "quality_score": 0.94
  },
  "quality_metrics": {
    "completeness": 0.96,
    "accuracy": 0.93,
    "consistency": 0.95,
    "timeliness": 0.98
  },
  "issues": [
    {
      "issue_type": "negative_fare",
      "count": 12,
      "severity": "high",
      "description": "Records with negative fare values",
      "sample_records": ["record_123", "record_456"]
    },
    {
      "issue_type": "impossible_occupancy",
      "count": 8,
      "severity": "medium",
      "description": "Occupied seats exceed total seats",
      "resolution": "Capped occupied seats at total capacity"
    }
  ],
  "recommendations": [
    "Implement stricter input validation for fare values",
    "Add real-time monitoring for occupancy data inconsistencies"
  ]
}
```

#### **GET** `/data-quality/issues`

**Purpose**: Detailed listing of data quality issues with filtering.

**Query Parameters**:

- `issue_type` (optional): Specific issue type
- `severity` (optional): Filter by severity level
- `resolved` (optional): Show only resolved/unresolved issues

**Response**:

```json
[
  {
    "issue_id": "uuid-789",
    "issue_type": "negative_fare",
    "severity": "high",
    "record_id": "schedule_1001",
    "description": "Fare value of -100.0 is invalid",
    "detected_at": "2025-06-15T09:15:00Z",
    "resolved": false,
    "resolution_action": null
  }
]
```

## ⚙️ Administration Endpoints

#### **POST** `/admin/etl/trigger`

**Purpose**: Manually trigger ETL processing pipeline.

**Request Body** (optional):

```json
{
  "force_reprocess": false,
  "specific_files": ["schedules_20250615.json"],
  "quality_check_level": "strict"
}
```

**Response**:

```json
{
  "job_id": "etl_job_20250615_103000",
  "status": "started",
  "estimated_duration_minutes": 15,
  "files_to_process": 3,
  "initiated_by": "admin_user",
  "started_at": "2025-06-15T10:30:00Z"
}
```

#### **GET** `/admin/etl/history`

**Purpose**: Retrieve ETL job execution history and status.

**Query Parameters**:

- `limit` (optional): Maximum jobs to return (default: 20)
- `status` (optional): Filter by job status (success, failed, running)

**Response**:

```json
[
  {
    "job_id": "etl_job_20250615_103000",
    "status": "completed",
    "started_at": "2025-06-15T10:30:00Z",
    "completed_at": "2025-06-15T10:42:00Z",
    "duration_seconds": 720,
    "records_processed": 150,
    "records_valid": 142,
    "records_invalid": 8,
    "quality_issues_found": 3
  }
]
```

## 📋 Request/Response Examples

### Example: Complete Pricing Workflow

**1. Get Route Information**

```bash
curl -X GET "http://localhost:8000/routes/1"
```

**2. Check Current Occupancy**

```bash
curl -X GET "http://localhost:8000/analytics/occupancy?route_id=1&days_back=1"
```

**3. Get Pricing Suggestion**

```bash
curl -X POST "http://localhost:8000/pricing/suggest" \
  -H "Content-Type: application/json" \
  -d '{
    "route_id": 1,
    "seat_type": "regular",
    "current_occupancy_rate": 0.75,
    "departure_time": "2025-06-15T08:00:00",
    "current_fare": 350.0
  }'
```

### Example: Data Quality Monitoring

**1. Get Quality Report**

```bash
curl -X GET "http://localhost:8000/data-quality/report?days_back=7"
```

**2. Review Specific Issues**

```bash
curl -X GET "http://localhost:8000/data-quality/issues?severity=high"
```

## 🚨 Rate Limiting & Best Practices

### Rate Limits

- **Analytics Endpoints**: 100 requests/minute
- **Pricing Suggestions**: 50 requests/minute
- **Admin Operations**: 10 requests/minute

### Best Practices

1. **Caching**: Cache frequent analytics queries
2. **Pagination**: Use `skip` and `limit` for large datasets
3. **Error Handling**: Implement retry logic with exponential backoff
4. **Monitoring**: Track API usage and performance metrics

## 🔧 Development Tools

### Testing with curl

```bash
# Health check
curl http://localhost:8000/health

# Get all routes
curl http://localhost:8000/routes

# Pricing suggestion
curl -X POST http://localhost:8000/pricing/suggest \
  -H "Content-Type: application/json" \
  -d '{"route_id": 1, "seat_type": "regular", "current_occupancy_rate": 0.8, "departure_time": "2025-06-15T10:00:00", "current_fare": 350.0}'
```

### Interactive Testing

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Python Client Example

```python
import requests

api_base = "http://localhost:8000"

# Get system health
health = requests.get(f"{api_base}/health").json()
print(f"API Status: {health['status']}")

# Get pricing suggestion
pricing_request = {
    "route_id": 1,
    "seat_type": "regular",
    "current_occupancy_rate": 0.75,
    "departure_time": "2025-06-15T08:00:00",
    "current_fare": 350.0
}

response = requests.post(f"{api_base}/pricing/suggest", json=pricing_request)
pricing = response.json()
print(f"Suggested fare: ₹{pricing['suggested_fare']}")
```

---

**📡 This API provides comprehensive access to all bus pricing pipeline functionality** with professional documentation, consistent responses, and production-ready features.
