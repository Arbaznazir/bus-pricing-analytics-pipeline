# 🌤️ Cloud Deployment Guide - Bus Pricing Analytics Pipeline

This guide helps you deploy your Bus Pricing Analytics Pipeline to various cloud platforms using Docker.

## 🚀 **Quick Start - Deploy to Docker Hub First**

### **Step 1: Login to Docker Hub**

```bash
# Create account at https://hub.docker.com if you don't have one
docker login
```

### **Step 2: Run Deployment Script**

```powershell
# On Windows (PowerShell)
.\deploy-to-docker-hub.ps1

# On macOS/Linux
chmod +x deploy-to-docker-hub.sh
./deploy-to-docker-hub.sh
```

### **Step 3: Verify Deployment**

Your images will be available at:

- `arbaznazir/bus-pricing-api:latest`
- `arbaznazir/bus-pricing-etl:latest`
- `arbaznazir/bus-pricing-scheduler:latest`
- `arbaznazir/bus-pricing-simulator:latest`

## 🌐 **Cloud Platform Deployment Options**

### **Option 1: Railway (Recommended - Easiest)**

**Why Railway?**

- Free tier available
- Automatic deployment from GitHub
- Built-in PostgreSQL database
- Easy environment management

**Steps:**

1. Go to [railway.app](https://railway.app)
2. Login with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Railway automatically detects Docker setup
7. Add PostgreSQL service
8. Set environment variables
9. Deploy!

**Cost:** Free tier includes $5/month credit

### **Option 2: Render (Great for APIs)**

**Why Render?**

- Free tier for web services
- Automatic SSL certificates
- Built-in monitoring
- Easy database setup

**Steps:**

1. Go to [render.com](https://render.com)
2. Connect GitHub account
3. Create Web Service from repository
4. Choose Docker environment
5. Add PostgreSQL database
6. Configure environment variables
7. Deploy

**Cost:** Free tier available

### **Option 3: DigitalOcean App Platform**

**Why DigitalOcean?**

- Professional cloud infrastructure
- Predictable pricing
- Great performance
- Easy scaling

**Steps:**

1. Go to [DigitalOcean App Platform](https://www.digitalocean.com/products/app-platform)
2. Create account and connect GitHub
3. Create new app from repository
4. Configure services:
   - API service (HTTP)
   - ETL service (Worker)
   - Scheduler service (Worker)
   - PostgreSQL database (Managed)
5. Set environment variables
6. Deploy

**Cost:** Starting from $5/month

### **Option 4: AWS ECS (Enterprise)**

**Why AWS ECS?**

- Enterprise-grade infrastructure
- Extensive AWS ecosystem
- Advanced scaling and monitoring
- Professional deployment

**Setup Guide:**

```bash
# 1. Install AWS CLI
# 2. Configure credentials
aws configure

# 3. Create ECS cluster
aws ecs create-cluster --cluster-name bus-pricing-cluster

# 4. Register task definitions
aws ecs register-task-definition --cli-input-json file://aws-task-definition.json

# 5. Create services
aws ecs create-service --cluster bus-pricing-cluster --service-name bus-pricing-api --task-definition bus-pricing-api
```

**Cost:** Pay-as-you-use pricing

### **Option 5: Google Cloud Run**

**Why Cloud Run?**

- Serverless containers
- Pay only when running
- Automatic scaling
- Google's infrastructure

**Steps:**

1. Enable Cloud Run API
2. Deploy using gcloud CLI:

```bash
gcloud run deploy bus-pricing-api \
  --image arbaznazir/bus-pricing-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Cost:** Pay per request

## 🛠️ **Recommended Deployment: Railway**

Railway is the easiest and most cost-effective for your use case. Here's exactly how to do it:

### **Railway Deployment Steps:**

1. **Prepare your repository:**

   ```bash
   # Ensure docker-compose.cloud.yml is ready
   git add .
   git commit -m "Prepared for Railway deployment"
   git push origin main
   ```

2. **Deploy to Railway:**

   - Visit [railway.app](https://railway.app)
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `bus-pricing-analytics-pipeline` repository
   - Railway will automatically detect your Docker setup

3. **Add PostgreSQL Database:**

   - In Railway dashboard, click "New Service"
   - Select "PostgreSQL"
   - Railway will provision a managed database

4. **Configure Environment Variables:**

   ```
   POSTGRES_HOST=<railway-postgres-host>
   POSTGRES_PORT=5432
   POSTGRES_USER=<railway-postgres-user>
   POSTGRES_PASSWORD=<railway-postgres-password>
   POSTGRES_DB=<railway-postgres-db>
   API_HOST=0.0.0.0
   API_PORT=8000
   ```

5. **Deploy and Access:**
   - Railway provides a public URL
   - Your API will be accessible at: `https://your-app.railway.app`
   - API docs available at: `https://your-app.railway.app/docs`

## 🔧 **Environment Configuration for Cloud**

### **Required Environment Variables:**

```bash
# Database Configuration
POSTGRES_HOST=<your-cloud-db-host>
POSTGRES_PORT=5432
POSTGRES_USER=<your-db-user>
POSTGRES_PASSWORD=<your-db-password>
POSTGRES_DB=<your-db-name>

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# ETL Configuration
MAX_FARE_THRESHOLD=100000
MIN_FARE_THRESHOLD=1
SPARK_DRIVER_MEMORY=512m
SPARK_EXECUTOR_MEMORY=512m

# Scheduler Configuration
ETL_SCHEDULE_INTERVAL_SECONDS=300
CLEANUP_INTERVAL_HOURS=24
HEALTH_CHECK_INTERVAL_MINUTES=5
FILE_RETENTION_DAYS=7
```

## 🚀 **Testing Your Cloud Deployment**

### **1. Health Check:**

```bash
curl https://your-cloud-url/health
```

### **2. API Documentation:**

Visit: `https://your-cloud-url/docs`

### **3. Test Dynamic Pricing:**

```bash
curl -X POST "https://your-cloud-url/pricing/suggest" \
     -H "Content-Type: application/json" \
     -d '{
       "route_id": 1,
       "seat_type": "standard",
       "current_occupancy_rate": 0.85,
       "departure_time": "2024-06-15T08:00:00",
       "current_fare": 350.0
     }'
```

### **4. Analytics Endpoints:**

```bash
curl https://your-cloud-url/analytics/occupancy
curl https://your-cloud-url/data-quality/report
```

## 📊 **Monitoring Your Cloud Deployment**

### **Built-in Monitoring:**

- Health checks at `/health`
- Metrics endpoint at `/metrics`
- System status at `/status`

### **Platform-Specific Monitoring:**

- **Railway**: Built-in metrics dashboard
- **Render**: Automatic health checks and alerts
- **DigitalOcean**: App Platform monitoring
- **AWS**: CloudWatch integration
- **Google Cloud**: Cloud Monitoring

## 💰 **Cost Comparison**

| Platform             | Free Tier         | Paid Starting | Best For            |
| -------------------- | ----------------- | ------------- | ------------------- |
| **Railway**          | $5/month credit   | $5/month      | Development & Demo  |
| **Render**           | 750 hours/month   | $7/month      | APIs & Web Services |
| **DigitalOcean**     | None              | $5/month      | Professional Apps   |
| **AWS ECS**          | 12 months free    | Variable      | Enterprise          |
| **Google Cloud Run** | 2M requests/month | Pay-per-use   | Serverless          |

## 🎯 **Recommendation**

**For your portfolio project, I recommend Railway because:**

- ✅ Free $5/month credit (enough for demo)
- ✅ Automatic deployment from GitHub
- ✅ Built-in PostgreSQL database
- ✅ Easy to share with potential employers
- ✅ Professional URLs for your resume
- ✅ Simple scaling when needed

## 🚀 **Ready to Deploy?**

1. **First**: Run the Docker Hub deployment script
2. **Then**: Choose Railway for easiest deployment
3. **Finally**: Test all endpoints and share your live demo!

Your Bus Pricing Analytics Pipeline will be live on the internet and ready to showcase! 🎉
