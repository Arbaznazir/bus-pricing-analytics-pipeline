.PHONY: help build start stop restart logs demo test clean generate-data run-etl

# Default target
help:
	@echo "🚀 Bus Pricing Pipeline - Available Commands"
	@echo "============================================="
	@echo ""
	@echo "🛠️  Development Commands:"
	@echo "  make build          - Build all Docker containers"
	@echo "  make start          - Start all services (database + API)"
	@echo "  make start-all      - Start all services including scheduler"
	@echo "  make stop           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs from all services"
	@echo ""
	@echo "🧪 Testing & Demo Commands:"
	@echo "  make demo           - Run the complete demo script"
	@echo "  make demo-quick     - Run quick demo (essential features)"
	@echo "  make test           - Run all tests"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-api       - Run API tests only"
	@echo ""
	@echo "📊 Data Pipeline Commands:"
	@echo "  make generate-data  - Generate sample data"
	@echo "  make run-etl        - Run ETL processing manually"
	@echo "  make db-init        - Initialize database with sample data"
	@echo ""
	@echo "🔧 Utility Commands:"
	@echo "  make health         - Check system health"
	@echo "  make clean          - Clean up containers and volumes"
	@echo "  make clean-data     - Clean up data directories only"
	@echo "  make shell-api      - Shell into API container"
	@echo "  make shell-db       - Shell into database container"
	@echo ""
	@echo "📖 Documentation:"
	@echo "  make docs           - Open API documentation in browser"
	@echo "  make api-url        - Show API endpoint URL"
	@echo ""

# Build all containers
build:
	@echo "🔨 Building all Docker containers..."
	docker-compose build

# Start core services (database + API)
start:
	@echo "🚀 Starting core services (database + API)..."
	docker-compose up -d db api
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@make health

# Start all services including scheduler
start-all:
	@echo "🚀 Starting all services..."
	docker-compose up -d
	@echo "⏳ Waiting for services to be ready..."
	@sleep 15
	@make health

# Stop all services
stop:
	@echo "⏹️  Stopping all services..."
	docker-compose down

# Restart all services
restart:
	@echo "🔄 Restarting all services..."
	docker-compose restart
	@sleep 10
	@make health

# View logs
logs:
	@echo "📋 Viewing logs from all services..."
	docker-compose logs --tail=50 -f

# View logs for specific service
logs-api:
	docker-compose logs --tail=100 -f api

logs-db:
	docker-compose logs --tail=100 -f db

logs-etl:
	docker-compose logs --tail=100 -f etl

logs-scheduler:
	docker-compose logs --tail=100 -f scheduler

# Run demo script
demo:
	@echo "🎬 Running complete demo..."
	python demo.py

# Run quick demo
demo-quick:
	@echo "⚡ Running quick demo..."
	python demo.py --quick

# Run all tests
test:
	@echo "🧪 Running all tests..."
	pytest -v

# Run unit tests only
test-unit:
	@echo "🧪 Running unit tests..."
	pytest -v -m unit

# Run API tests only
test-api:
	@echo "🧪 Running API tests..."
	pytest -v tests/test_api.py

# Run ETL tests only
test-etl:
	@echo "🧪 Running ETL tests..."
	pytest -v tests/test_etl.py

# Generate sample data
generate-data:
	@echo "📊 Generating sample data..."
	docker-compose run --rm data_simulator
	@echo "✅ Sample data generated in ./data/raw/"

# Run ETL processing
run-etl:
	@echo "⚙️  Running ETL processing..."
	docker-compose run --rm etl
	@echo "✅ ETL processing completed"

# Initialize database with sample data
db-init:
	@echo "🗄️  Initializing database..."
	@make generate-data
	@make run-etl
	@echo "✅ Database initialized with sample data"

# Check system health
health:
	@echo "🏥 Checking system health..."
	@echo "Database status:"
	@docker-compose exec -T db pg_isready -U bususer -d busdb || echo "❌ Database not ready"
	@echo ""
	@echo "API status:"
	@curl -s http://localhost:8000/health | python -m json.tool || echo "❌ API not ready"

# Clean up everything
clean:
	@echo "🧹 Cleaning up containers and volumes..."
	docker-compose down -v --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup completed"

# Clean up data directories only
clean-data:
	@echo "🧹 Cleaning up data directories..."
	rm -rf data/raw/* data/processed/* data/error/* 2>/dev/null || true
	@echo "✅ Data directories cleaned"

# Shell into API container
shell-api:
	@echo "🐚 Opening shell in API container..."
	docker-compose exec api /bin/bash

# Shell into database container
shell-db:
	@echo "🐚 Opening shell in database container..."
	docker-compose exec db psql -U bususer -d busdb

# Open API documentation
docs:
	@echo "📖 Opening API documentation..."
	@echo "Swagger UI: http://localhost:8000/docs"
	@echo "ReDoc: http://localhost:8000/redoc"
	@if command -v xdg-open > /dev/null; then \
		xdg-open http://localhost:8000/docs; \
	elif command -v open > /dev/null; then \
		open http://localhost:8000/docs; \
	else \
		echo "Please open http://localhost:8000/docs in your browser"; \
	fi

# Show API URL
api-url:
	@echo "🌐 API Endpoints:"
	@echo "  Health Check: http://localhost:8000/health"
	@echo "  Documentation: http://localhost:8000/docs"
	@echo "  API Root: http://localhost:8000/"

# Development setup
dev-setup:
	@echo "🛠️  Setting up development environment..."
	cp .env.example .env
	pip install -r requirements.txt
	pip install -r api/requirements.txt
	@echo "✅ Development environment ready"

# Production deployment preparation
prod-setup:
	@echo "🚀 Preparing for production deployment..."
	@echo "1. Update .env with production values"
	@echo "2. Configure proper secrets management"
	@echo "3. Set up monitoring and alerting"
	@echo "4. Configure load balancer"
	@echo "5. Set up backup strategy"

# Quick start (complete setup and demo)
quickstart: build start-all
	@echo "🎯 Running complete quickstart..."
	@sleep 20
	@make generate-data
	@make run-etl
	@make demo-quick
	@echo ""
	@echo "🎉 Quickstart completed successfully!"
	@echo "📖 API Documentation: http://localhost:8000/docs"

# Show project status
status:
	@echo "📊 Project Status:"
	@echo "=================="
	@echo ""
	@echo "🐳 Docker Containers:"
	docker-compose ps
	@echo ""
	@echo "💾 Data Volumes:"
	@ls -la data/ 2>/dev/null || echo "No data directory found"
	@echo ""
	@echo "🌐 API Health:"
	@curl -s http://localhost:8000/health 2>/dev/null | python -m json.tool || echo "API not available" 