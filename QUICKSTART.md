# 🚀 Quick Start Guide - Bus Pricing Analytics Pipeline

This guide will get you up and running with my Bus Pricing Analytics Pipeline in under 5 minutes. Just copy and paste the commands - everything is designed to work out of the box!

## 📋 Prerequisites

- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Git** for cloning the repository
- **Python 3.9+** (for running the demo)
- **8GB RAM** and **2+ CPU cores** recommended

## 🚀 **Method 1: One-Command Setup (Recommended)**

**Copy these commands directly into your terminal:**

```bash
# Clone the repository
git clone https://github.com/Arbaznazir/bus-pricing-analytics-pipeline.git
cd bus-pricing-analytics-pipeline

# Start everything with Docker (this will take 2-3 minutes)
docker-compose up --build -d

# Wait for services to initialize
timeout 60 2>/dev/null || sleep 60

# Run the interactive demo
python demo.py
```

**🎉 That's it! Your system is running!**

**Open these URLs in your browser:**

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🛠️ **Method 2: Step-by-Step Local Development**

**For developers who want to run components locally:**

```bash
# 1. Set up Python environment
python -m venv venv

# 2. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Set up SQLite for local development
export DATABASE_URL="sqlite:///./bus_data.db"

# 5. Initialize the database
python -c "from api.models import Base, engine; Base.metadata.create_all(engine)"

# 6. Start the API server (keep this terminal open)
cd api
python main.py

# 7. Open new terminal, start the scheduler
cd scheduler
python scheduler.py

# 8. Generate some test data
cd data_simulator
python simulator.py

# 9. Run the demo
python demo.py
```

## 🎯 **Verify Everything is Working**

### **1. Check System Health**

```bash
# Quick health check
curl http://localhost:8000/health

# Check all containers are running (if using Docker)
docker-compose ps

# Expected output: All services should show "Up" status
```

### **2. Test Core API Endpoints**

```bash
# Get all available routes
curl http://localhost:8000/routes/

# Create a new route
curl -X POST "http://localhost:8000/routes/" \
     -H "Content-Type: application/json" \
     -d '{
       "route_name": "Mumbai-Pune",
       "origin": "Mumbai",
       "destination": "Pune",
       "distance_km": 148,
       "base_fare": 350.0
     }'

# Test dynamic pricing (copy this exactly)
curl -X POST "http://localhost:8000/pricing/suggest" \
     -H "Content-Type: application/json" \
     -d '{
       "route_id": 1,
       "seat_type": "standard",
       "current_occupancy_rate": 0.85,
       "departure_time": "2024-06-15T08:00:00",
       "current_fare": 350.0
     }'
```

### **3. Explore the Interactive API**

**Open in your browser:** http://localhost:8000/docs

This gives you a beautiful interface where you can:

- Test all API endpoints directly
- See request/response formats
- Download API specifications
- Try different scenarios

## 📊 **Key Features You Can Test**

### **Dynamic Pricing Scenarios**

**Copy these commands to test different pricing scenarios:**

```bash
# High occupancy during peak hours (should increase price)
curl -X POST "http://localhost:8000/pricing/suggest" \
     -H "Content-Type: application/json" \
     -d '{
       "route_id": 1,
       "seat_type": "standard",
       "current_occupancy_rate": 0.9,
       "departure_time": "2024-06-15T08:00:00",
       "current_fare": 300.0
     }'

# Low occupancy during off-peak (should decrease price)
curl -X POST "http://localhost:8000/pricing/suggest" \
     -H "Content-Type: application/json" \
     -d '{
       "route_id": 1,
       "seat_type": "standard",
       "current_occupancy_rate": 0.3,
       "departure_time": "2024-06-15T14:30:00",
       "current_fare": 300.0
     }'

# Last-minute booking (should increase price)
curl -X POST "http://localhost:8000/pricing/suggest" \
     -H "Content-Type: application/json" \
     -d '{
       "route_id": 1,
       "seat_type": "standard",
       "current_occupancy_rate": 0.7,
       "departure_time": "2024-01-15T10:00:00",
       "current_fare": 300.0
     }'
```

### **Analytics & Data Quality**

```bash
# Get occupancy analytics
curl "http://localhost:8000/analytics/occupancy?route_id=1"

# Check data quality report
curl http://localhost:8000/data-quality/report

# Get revenue insights
curl http://localhost:8000/analytics/revenue

# Check system metrics
curl http://localhost:8000/metrics
```

## 🧪 **Run Tests to Validate**

**Execute the complete test suite:**

```bash
# Run all tests (should show 55 tests passing)
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=. --cov-report=html

# Run specific categories
python -m pytest tests/test_api.py -v      # API tests
python -m pytest tests/test_etl.py -v      # ETL and pricing tests
```

**Expected output:**

```
======================== 55 passed, 0 failed in 0.89s ========================
```

## 🔍 **Understanding the System**

### **Core Services Running**

| **Service**   | **Port** | **Purpose**                                     |
| ------------- | -------- | ----------------------------------------------- |
| **API**       | 8000     | FastAPI backend with analytics and pricing      |
| **Database**  | 5432     | PostgreSQL with bus schedule and occupancy data |
| **ETL**       | -        | PySpark-based data processing pipeline          |
| **Scheduler** | -        | Automated job scheduling and monitoring         |

### **Data Flow Process**

1. **Data Generation**: `data_simulator/` creates realistic bus data
2. **ETL Processing**: `etl/` processes and validates the data
3. **API Layer**: `api/` serves the processed data with dynamic pricing
4. **Scheduling**: `scheduler/` automates the entire pipeline

### **Monitor Real-Time Operations**

```bash
# Watch live logs from all services
docker-compose logs -f

# Watch specific service logs
docker-compose logs -f api
docker-compose logs -f postgres

# Check system performance
docker stats
```

## 🎬 **5-Minute Demo Script**

**Follow this exact sequence for a comprehensive demo:**

```bash
# 1. System Health Check (30 seconds)
echo "=== System Health Check ==="
curl http://localhost:8000/health
docker-compose ps

# 2. Dynamic Pricing Demo (2 minutes)
echo "=== Dynamic Pricing Demo ==="
python demo.py --pricing-scenarios

# 3. Analytics Overview (1 minute)
echo "=== Analytics Overview ==="
curl http://localhost:8000/analytics/occupancy
curl http://localhost:8000/data-quality/report

# 4. API Documentation (1 minute)
echo "=== Open in browser: http://localhost:8000/docs ==="

# 5. Test Results (30 seconds)
echo "=== Test Validation ==="
python -m pytest tests/ --tb=short -q
```

## 🔧 **Development & Customization**

### **Adding New Features**

```bash
# Create a new branch for your feature
git checkout -b feature/my-new-feature

# Make your changes to the code
# Test your changes
python -m pytest tests/ -v

# Run the demo to see your changes
python demo.py
```

### **Customizing for Your Use Case**

**Edit these files to customize:**

- `api/schemas.py` - Data models and validation
- `etl/model.py` - Pricing algorithms and business logic
- `data_simulator/simulator.py` - Test data generation
- `docker-compose.yml` - Service configuration

### **Environment Configuration**

```bash
# Create custom environment file
cp .env.example .env

# Edit .env to customize:
# - Database connection strings
# - API configuration
# - Performance tuning parameters
```

## 🐛 **Troubleshooting Guide**

### **Common Issues & Solutions**

**1. Port 8000 already in use:**

```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml
```

**2. Docker containers not starting:**

```bash
# Check Docker logs
docker-compose logs

# Restart all services
docker-compose down
docker-compose up --build -d
```

**3. Database connection errors:**

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

**4. Python dependencies issues:**

```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### **Performance Issues**

```bash
# Check resource usage
docker stats

# Reduce memory usage in docker-compose.yml:
# - Lower PySpark memory allocation
# - Reduce worker processes
```

## 🚀 **Next Steps**

### **Explore Advanced Features**

1. **Custom Pricing Algorithms**: Modify `etl/model.py`
2. **New Data Sources**: Add ETL jobs in `etl/`
3. **Enhanced Analytics**: Extend API endpoints in `api/main.py`
4. **Production Deployment**: Use `docker-compose.prod.yml`

### **Production Deployment**

```bash
# For production deployment
docker-compose -f docker-compose.prod.yml up -d

# For Kubernetes deployment
kubectl apply -f k8s/
```

### **Integration with Your System**

- **API Integration**: Use the REST endpoints for your applications
- **Database Access**: Connect directly to PostgreSQL for custom queries
- **Data Export**: Use analytics endpoints for reporting
- **Webhook Integration**: Extend API for real-time notifications

---

**🎯 You now have a fully functional bus pricing analytics system running locally!**

**For questions or issues:**

- Check the logs: `docker-compose logs`
- Run validation: `python validate_system.py`
- View documentation: http://localhost:8000/docs

**Ready to explore the system? Start with `python demo.py` for a guided tour!** 🚀
