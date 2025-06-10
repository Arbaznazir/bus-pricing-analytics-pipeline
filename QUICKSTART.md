# 🚀 Quick Start Guide - Bus Pricing Pipeline

This guide will get you up and running with the NOVA Bus Pricing Pipeline in under 10 minutes.

## 📋 Prerequisites

- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Git** for cloning the repository
- **Python 3.9+** (optional, for running demo script locally)
- **8GB RAM** and **2+ CPU cores** recommended

## 🛠️ Quick Setup (5 Minutes)

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd UniProject
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# The default configuration works out of the box
# Optionally edit .env to customize settings
```

### 3. Start All Services

```bash
# Build and start all services (database, API, ETL, scheduler)
docker-compose up --build -d

# Check all services are running
docker-compose ps
```

### 4. Verify System Health

```bash
# Wait for all services to be ready (about 30-60 seconds)
sleep 60

# Check API health
curl http://localhost:8000/health

# Or run the demo script
python demo.py --quick
```

## 🎯 Core Services

| Service       | Port | Description                                     |
| ------------- | ---- | ----------------------------------------------- |
| **API**       | 8000 | FastAPI backend with analytics and pricing      |
| **Database**  | 5432 | PostgreSQL with bus schedule and occupancy data |
| **ETL**       | -    | PySpark-based data processing pipeline          |
| **Scheduler** | -    | Automated job scheduling and monitoring         |

## 🧪 Testing the System

### 1. API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 2. Sample API Calls

```bash
# Get all routes
curl http://localhost:8000/routes

# Get occupancy analytics
curl http://localhost:8000/analytics/occupancy

# Get pricing suggestion
curl -X POST http://localhost:8000/pricing/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "route_id": 1,
    "seat_type": "regular",
    "current_occupancy_rate": 0.8,
    "departure_time": "2025-06-15T10:00:00",
    "current_fare": 350.0
  }'
```

### 3. Run Full Demo

```bash
# Complete demonstration with all features
python demo.py

# Quick demo (essential features only)
python demo.py --quick
```

## 📊 Key Features to Explore

### 1. Dynamic Pricing Engine

Test different scenarios:

- High occupancy → Price increase
- Low occupancy → Price reduction
- Peak hours → Premium pricing
- Last-minute booking → Higher prices
- Early booking → Discounts

### 2. Data Analytics

- Route performance metrics
- Occupancy rate analysis
- Revenue optimization insights
- Data quality monitoring

### 3. Real-time Pipeline

- Automatic data ingestion
- Data validation and cleaning
- Quality issue detection
- Scheduled processing

## 🔧 Development Mode

### 1. Local Development Setup

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install -r api/requirements.txt

# Start database only
docker-compose up -d postgres

# Run API locally for development
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest tests/test_api.py # API tests only
```

### 3. Data Generation

```bash
# Generate sample data
cd data_simulator
python simulator.py

# Run ETL manually
cd etl
python etl_job.py
```

## 🐛 Troubleshooting

### Common Issues

**1. Port Already in Use**

```bash
# Check what's using port 8000
lsof -i :8000

# Kill process if needed
kill -9 <PID>

# Or change port in docker-compose.yml
```

**2. Database Connection Failed**

```bash
# Check database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

**3. Out of Memory**

```bash
# Check resource usage
docker stats

# Reduce PySpark memory in docker-compose.yml
# or increase Docker memory allocation
```

**4. Services Not Starting**

```bash
# Check all service logs
docker-compose logs

# Restart specific service
docker-compose restart api

# Full cleanup and restart
docker-compose down -v
docker-compose up --build
```

### Service Health Checks

```bash
# Check individual service status
docker-compose exec api curl localhost:8000/health
docker-compose exec postgres pg_isready
docker-compose logs scheduler --tail=20
```

## 🔍 Monitoring and Logs

### View Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs api
docker-compose logs etl
docker-compose logs scheduler

# Follow logs in real-time
docker-compose logs -f api
```

### System Resources

```bash
# Resource usage by service
docker stats

# Disk usage
docker system df

# Database size
docker-compose exec postgres psql -U bususer -d busdb -c "
  SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
  FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

## 📈 Performance Optimization

### For Production

1. **Increase Resources**: Allocate more CPU/memory in docker-compose.yml
2. **Database Tuning**: Use the optimized settings from sql/init.sql
3. **Caching**: Enable Redis for API response caching
4. **Load Balancing**: Add multiple API replicas

### For Development

1. **Hot Reload**: Use volume mounts for code changes
2. **Debug Mode**: Set LOG_LEVEL=DEBUG in .env
3. **Profile**: Use built-in performance monitoring endpoints

## 🚨 Data Pipeline Monitoring

### ETL Job Status

```bash
# Check ETL job history
curl http://localhost:8000/admin/etl/history

# Manual ETL trigger
curl -X POST http://localhost:8000/admin/etl/trigger
```

### Data Quality Metrics

```bash
# Get quality report
curl http://localhost:8000/data-quality/report

# View quality issues
curl http://localhost:8000/data-quality/issues
```

## 🎓 Next Steps

1. **Explore the API**: Use Swagger UI to test all endpoints
2. **Review the Code**: Check out the clean, documented codebase
3. **Run Tests**: Execute the comprehensive test suite
4. **Customize**: Modify pricing models and business rules
5. **Scale**: Deploy to cloud infrastructure

## 📞 Getting Help

- **Logs**: Always check `docker-compose logs` first
- **Health**: Use the `/health` endpoint for system status
- **Demo**: Run `python demo.py` to verify functionality
- **Tests**: Execute `pytest` to ensure everything works

---

**🎉 You're all set!** The Bus Pricing Pipeline is now running and ready to demonstrate professional-grade data engineering capabilities.

**API Endpoint**: http://localhost:8000/docs  
**Demo Script**: `python demo.py`  
**System Health**: http://localhost:8000/health
