# Bus Pricing Analytics Pipeline - Docker Hub Deployment Script (PowerShell)
# This script builds and pushes all Docker images to Docker Hub

# Configuration
$DOCKER_USERNAME = "arbaz4"
$PROJECT_NAME = "bus-pricing"
$VERSION_TAG = "latest"

Write-Host "🚀 Bus Pricing Analytics Pipeline - Docker Hub Deployment" -ForegroundColor Blue
Write-Host "============================================================" -ForegroundColor Blue
Write-Host ""

# Check if Docker is running
try {
    docker info > $null 2>&1
    Write-Host "✅ Docker is running" -ForegroundColor Green
}
catch {
    Write-Host "❌ Error: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check Docker Hub login
Write-Host "⚠️  Please ensure you're logged in to Docker Hub:" -ForegroundColor Yellow
Write-Host "   docker login" -ForegroundColor Blue
$confirmation = Read-Host "Press Enter if you're logged in, or type 'login' to login now"

if ($confirmation -eq "login") {
    docker login
}

Write-Host "✅ Proceeding with deployment..." -ForegroundColor Green
Write-Host ""

# Function to build and push service
function Deploy-Service {
    param($ServiceName, $Context)
    
    Write-Host "📦 Building $ServiceName service..." -ForegroundColor Yellow
    docker build -t "${DOCKER_USERNAME}/${PROJECT_NAME}-${ServiceName}:${VERSION_TAG}" $Context
    docker build -t "${DOCKER_USERNAME}/${PROJECT_NAME}-${ServiceName}:v1.0" $Context
    
    Write-Host "🚀 Pushing $ServiceName service to Docker Hub..." -ForegroundColor Yellow
    docker push "${DOCKER_USERNAME}/${PROJECT_NAME}-${ServiceName}:${VERSION_TAG}"
    docker push "${DOCKER_USERNAME}/${PROJECT_NAME}-${ServiceName}:v1.0"
    
    Write-Host "✅ $ServiceName service deployed successfully" -ForegroundColor Green
    Write-Host ""
}

# Deploy all services
Deploy-Service "api" "./api"
Deploy-Service "etl" "./etl"
Deploy-Service "scheduler" "./scheduler"
Deploy-Service "simulator" "./data_simulator"

# Display deployment summary
Write-Host "🎉 All services deployed successfully to Docker Hub!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Deployment Summary:" -ForegroundColor Blue
Write-Host "   • API Service:        ${DOCKER_USERNAME}/${PROJECT_NAME}-api:${VERSION_TAG}"
Write-Host "   • ETL Service:        ${DOCKER_USERNAME}/${PROJECT_NAME}-etl:${VERSION_TAG}"
Write-Host "   • Scheduler Service:  ${DOCKER_USERNAME}/${PROJECT_NAME}-scheduler:${VERSION_TAG}"
Write-Host "   • Simulator Service:  ${DOCKER_USERNAME}/${PROJECT_NAME}-simulator:${VERSION_TAG}"
Write-Host ""
Write-Host "🌐 Your images are now available publicly at:" -ForegroundColor Blue
Write-Host "   https://hub.docker.com/u/${DOCKER_USERNAME}"
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Deploy to cloud platform using docker-compose.cloud.yml"
Write-Host "   2. Use these images for production deployment"  
Write-Host "   3. Share with teams for easy collaboration"
Write-Host ""
Write-Host "✅ Deployment Complete!" -ForegroundColor Green

# Show next deployment options
Write-Host ""
Write-Host "🌤️  Cloud Deployment Options:" -ForegroundColor Cyan
Write-Host "   • Railway:           https://railway.app"
Write-Host "   • Render:            https://render.com"
Write-Host "   • DigitalOcean:      https://www.digitalocean.com/products/app-platform"
Write-Host "   • AWS ECS:           https://aws.amazon.com/ecs"
Write-Host "   • Google Cloud Run:  https://cloud.google.com/run"
Write-Host ""
Write-Host "Ready to deploy to any of these platforms!" -ForegroundColor Green 