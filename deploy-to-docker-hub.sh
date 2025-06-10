#!/bin/bash

# Bus Pricing Analytics Pipeline - Docker Hub Deployment Script
# This script builds and pushes all Docker images to Docker Hub

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_USERNAME="arbaznazir"
PROJECT_NAME="bus-pricing"
VERSION_TAG="latest"

echo -e "${BLUE}🚀 Bus Pricing Analytics Pipeline - Docker Hub Deployment${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Check if user is logged in to Docker Hub
if ! docker info | grep -q "Username"; then
    echo -e "${YELLOW}⚠️  Please login to Docker Hub first:${NC}"
    echo -e "${BLUE}   docker login${NC}"
    echo ""
    read -p "Press Enter after logging in..."
fi

echo -e "${GREEN}✅ Docker Hub authentication verified${NC}"
echo ""

# Build and push API service
echo -e "${YELLOW}📦 Building API service...${NC}"
docker build -t ${DOCKER_USERNAME}/${PROJECT_NAME}-api:${VERSION_TAG} ./api
docker build -t ${DOCKER_USERNAME}/${PROJECT_NAME}-api:v1.0 ./api

echo -e "${YELLOW}🚀 Pushing API service to Docker Hub...${NC}"
docker push ${DOCKER_USERNAME}/${PROJECT_NAME}-api:${VERSION_TAG}
docker push ${DOCKER_USERNAME}/${PROJECT_NAME}-api:v1.0

echo -e "${GREEN}✅ API service deployed successfully${NC}"
echo ""

# Build and push ETL service
echo -e "${YELLOW}📦 Building ETL service...${NC}"
docker build -t ${DOCKER_USERNAME}/${PROJECT_NAME}-etl:${VERSION_TAG} ./etl
docker build -t ${DOCKER_USERNAME}/${PROJECT_NAME}-etl:v1.0 ./etl

echo -e "${YELLOW}🚀 Pushing ETL service to Docker Hub...${NC}"
docker push ${DOCKER_USERNAME}/${PROJECT_NAME}-etl:${VERSION_TAG}
docker push ${DOCKER_USERNAME}/${PROJECT_NAME}-etl:v1.0

echo -e "${GREEN}✅ ETL service deployed successfully${NC}"
echo ""

# Build and push Scheduler service
echo -e "${YELLOW}📦 Building Scheduler service...${NC}"
docker build -t ${DOCKER_USERNAME}/${PROJECT_NAME}-scheduler:${VERSION_TAG} ./scheduler
docker build -t ${DOCKER_USERNAME}/${PROJECT_NAME}-scheduler:v1.0 ./scheduler

echo -e "${YELLOW}🚀 Pushing Scheduler service to Docker Hub...${NC}"
docker push ${DOCKER_USERNAME}/${PROJECT_NAME}-scheduler:${VERSION_TAG}
docker push ${DOCKER_USERNAME}/${PROJECT_NAME}-scheduler:v1.0

echo -e "${GREEN}✅ Scheduler service deployed successfully${NC}"
echo ""

# Build and push Data Simulator service
echo -e "${YELLOW}📦 Building Data Simulator service...${NC}"
docker build -t ${DOCKER_USERNAME}/${PROJECT_NAME}-simulator:${VERSION_TAG} ./data_simulator
docker build -t ${DOCKER_USERNAME}/${PROJECT_NAME}-simulator:v1.0 ./data_simulator

echo -e "${YELLOW}🚀 Pushing Data Simulator service to Docker Hub...${NC}"
docker push ${DOCKER_USERNAME}/${PROJECT_NAME}-simulator:${VERSION_TAG}
docker push ${DOCKER_USERNAME}/${PROJECT_NAME}-simulator:v1.0

echo -e "${GREEN}✅ Data Simulator service deployed successfully${NC}"
echo ""

# Display deployment summary
echo -e "${GREEN}🎉 All services deployed successfully to Docker Hub!${NC}"
echo ""
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo -e "   • API Service:        ${DOCKER_USERNAME}/${PROJECT_NAME}-api:${VERSION_TAG}"
echo -e "   • ETL Service:        ${DOCKER_USERNAME}/${PROJECT_NAME}-etl:${VERSION_TAG}"
echo -e "   • Scheduler Service:  ${DOCKER_USERNAME}/${PROJECT_NAME}-scheduler:${VERSION_TAG}"
echo -e "   • Simulator Service:  ${DOCKER_USERNAME}/${PROJECT_NAME}-simulator:${VERSION_TAG}"
echo ""
echo -e "${BLUE}🌐 Your images are now available publicly at:${NC}"
echo -e "   https://hub.docker.com/u/${DOCKER_USERNAME}"
echo ""
echo -e "${YELLOW}🚀 Next Steps:${NC}"
echo -e "   1. Deploy to cloud platform using docker-compose.cloud.yml"
echo -e "   2. Use these images for production deployment"
echo -e "   3. Share with teams for easy collaboration"
echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}" 