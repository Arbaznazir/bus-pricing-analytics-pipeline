"""
Bus Pricing Pipeline FastAPI Application

Main API service providing endpoints for bus schedule analytics,
seat occupancy data, and dynamic pricing suggestions.
"""

import os
import logging
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

import models
import schemas
import crud

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "bususer")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "buspassword")
POSTGRES_DB = os.getenv("POSTGRES_DB", "busdb")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Create database engine and session
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Bus Pricing Pipeline API",
    description="API for bus schedule analytics, occupancy tracking, and dynamic pricing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get database session
def get_db() -> Session:
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables and setup logging"""
    try:
        models.Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        logger.info("Bus Pricing Pipeline API started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise e


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc):
    """Handle SQLAlchemy database errors"""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Database error occurred", "detail": str(exc)}
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Invalid input", "detail": str(exc)}
    )


# Health check endpoint
@app.get("/health", response_model=schemas.HealthResponse)
async def health_check():
    """Health check endpoint"""
    return schemas.HealthResponse(status="ok", timestamp=datetime.utcnow())


# Route endpoints
@app.get("/routes", response_model=List[schemas.RouteResponse])
async def get_routes(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all available routes"""
    try:
        routes = crud.get_routes(db, skip=skip, limit=limit)
        return routes
    except Exception as e:
        logger.error(f"Error fetching routes: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch routes")


@app.get("/routes/{route_id}", response_model=schemas.RouteResponse)
async def get_route(route_id: int, db: Session = Depends(get_db)):
    """Get a specific route by ID"""
    route = crud.get_route(db, route_id=route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route


# Operator endpoints
@app.get("/operators", response_model=List[schemas.OperatorResponse])
async def get_operators(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all active operators"""
    try:
        operators = crud.get_operators(db, skip=skip, limit=limit)
        return operators
    except Exception as e:
        logger.error(f"Error fetching operators: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch operators")


# Schedule endpoints
@app.get("/schedules/{route_id}", response_model=List[schemas.ScheduleResponse])
async def get_schedules(
    route_id: int,
    date: str = Query(..., pattern=r'^\d{4}-\d{2}-\d{2}$',
                      description="Date in YYYY-MM-DD format"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get schedules for a specific route and date"""
    try:
        # Validate date format
        datetime.strptime(date, '%Y-%m-%d')
        schedules = crud.get_schedules_by_route_and_date(
            db, route_id=route_id, date=date, skip=skip, limit=limit)
        return schedules
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error fetching schedules: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch schedules")


@app.get("/schedules/{schedule_id}/occupancy", response_model=schemas.ScheduleWithOccupancy)
async def get_schedule_with_occupancy(schedule_id: int, db: Session = Depends(get_db)):
    """Get schedule with seat occupancy data"""
    schedule = crud.get_schedule_with_occupancy(db, schedule_id=schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


# Analytics endpoints
@app.get("/analytics/occupancy", response_model=schemas.OccupancyStats)
async def get_occupancy_analytics(
    route_id: Optional[int] = Query(None, description="Filter by route ID"),
    date: Optional[str] = Query(
        None, pattern=r'^\d{4}-\d{2}-\d{2}$', description="Filter by date (YYYY-MM-DD)"),
    seat_type: Optional[schemas.SeatType] = Query(
        None, description="Filter by seat type"),
    db: Session = Depends(get_db)
):
    """Get occupancy analytics with optional filters"""
    try:
        if date:
            # Validate date format
            datetime.strptime(date, '%Y-%m-%d')

        stats = crud.get_occupancy_stats(
            db,
            route_id=route_id,
            date=date,
            seat_type=seat_type.value if seat_type else None
        )
        return stats
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error calculating occupancy analytics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to calculate analytics")


# Pricing endpoints
@app.post("/pricing/suggest", response_model=schemas.PricingSuggestion)
async def suggest_pricing(
    pricing_request: schemas.PricingRequest,
    db: Session = Depends(get_db)
):
    """Get dynamic pricing suggestions based on current conditions"""
    try:
        suggestion = crud.calculate_pricing_suggestion(db, pricing_request)
        logger.info(
            f"Pricing suggestion generated for route {pricing_request.route_id}: {suggestion.suggested_fare}")
        return suggestion
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating pricing suggestion: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to calculate pricing suggestion")


# Data quality endpoints
@app.get("/data-quality/report", response_model=schemas.DataQualityReport)
async def get_data_quality_report(
    days_back: int = Query(
        7, ge=1, le=30, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """Get data quality report for the specified time period"""
    try:
        report = crud.get_data_quality_report(db, days_back=days_back)
        return report
    except Exception as e:
        logger.error(f"Error generating data quality report: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate data quality report")


# Admin endpoints (for ETL and data management)
@app.post("/admin/routes", response_model=schemas.RouteResponse)
async def create_route(route_data: schemas.RouteBase, db: Session = Depends(get_db)):
    """Create or update a route (used by ETL process)"""
    try:
        route = crud.create_or_update_route(db, route_data.dict())
        return route
    except Exception as e:
        logger.error(f"Error creating/updating route: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create/update route")


@app.post("/admin/operators", response_model=schemas.OperatorResponse)
async def create_operator(operator_data: schemas.OperatorBase, db: Session = Depends(get_db)):
    """Create or update an operator (used by ETL process)"""
    try:
        operator = crud.create_or_update_operator(db, operator_data.dict())
        return operator
    except Exception as e:
        logger.error(f"Error creating/updating operator: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create/update operator")


# Statistics endpoints
@app.get("/stats/summary")
async def get_summary_stats(db: Session = Depends(get_db)):
    """Get overall system statistics"""
    try:
        # Count various entities
        total_routes = db.query(models.Route).count()
        total_operators = db.query(models.Operator).filter(
            models.Operator.is_active == True).count()
        total_schedules = db.query(models.Schedule).filter(
            models.Schedule.is_active == True).count()
        total_occupancy_records = db.query(models.SeatOccupancy).count()

        # Recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(hours=24)
        recent_schedules = db.query(models.Schedule).filter(
            models.Schedule.created_at >= yesterday).count()
        recent_occupancy = db.query(models.SeatOccupancy).filter(
            models.SeatOccupancy.created_at >= yesterday).count()

        return {
            "system_status": "operational",
            "total_routes": total_routes,
            "total_operators": total_operators,
            "total_schedules": total_schedules,
            "total_occupancy_records": total_occupancy_records,
            "recent_activity": {
                "schedules_last_24h": recent_schedules,
                "occupancy_records_last_24h": recent_occupancy
            },
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error fetching summary stats: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch summary statistics")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level="info",
        reload=False
    )
