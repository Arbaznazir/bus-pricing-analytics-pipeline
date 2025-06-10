# 🚀 Quick Cloud Deployment Guide

## **Immediate Deployment Options**

Your API image is already built and available on Docker Hub! Let's get you deployed in under 5 minutes.

### **Option 1: Railway (Fastest - 2 minutes)**

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login to Railway
railway login

# 3. Create new project
railway new

# 4. Deploy API
railway up --service api

# 5. Add database
railway add postgresql

# 6. Set environment variables
railway variables set POSTGRES_HOST=${{Postgres.POSTGRES_HOST}}
railway variables set POSTGRES_PORT=${{Postgres.POSTGRES_PORT}}
railway variables set POSTGRES_USER=${{Postgres.POSTGRES_USER}}
railway variables set POSTGRES_PASSWORD=${{Postgres.POSTGRES_PASSWORD}}
railway variables set POSTGRES_DB=${{Postgres.POSTGRES_DB}}
```

### **Option 2: Render (3 minutes)**

1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repo: `https://github.com/Arbaznazir/bus-pricing-analytics-pipeline`
4. Configure:
   - **Name**: `bus-pricing-api`
   - **Runtime**: `Docker`
   - **Dockerfile Path**: `api/Dockerfile`
   - **Plan**: Free

### **Option 3: Local with Your Docker Hub Image**

```bash
# Use your pre-built image immediately
docker-compose -f docker-compose.api-only.yml up -d
```

### **Fix ETL Build Issues**

If you want to build the ETL image again:

```bash
# Use the optimized Dockerfile
docker build -f etl/Dockerfile.optimized -t arbaz4/bus-pricing-etl:latest ./etl

# Or try with different network settings
docker build --network host -t arbaz4/bus-pricing-etl:latest ./etl
```

### **Alternative: Lightweight ETL**

Create a Python-only ETL without Spark:

```bash
# This builds much faster
docker build -f etl/Dockerfile.light -t arbaz4/bus-pricing-etl-light:latest ./etl
```

## **Your Live URLs**

Once deployed, your API will be available at:

- Railway: `https://your-app.railway.app`
- Render: `https://your-app.onrender.com`
- Local: `http://localhost:8000`

## **Test Your Deployment**

```bash
# Health check
curl https://your-app-url/health

# Get routes
curl https://your-app-url/api/v1/routes

# Test pricing
curl -X POST https://your-app-url/api/v1/pricing/suggest \
  -H "Content-Type: application/json" \
  -d '{"route_id": 1, "departure_time": "2024-02-15T10:00:00", "passenger_count": 2}'
```

## **Portfolio Ready URLs**

Add these to your resume/portfolio:

- **Live Demo**: `https://your-app-url`
- **API Docs**: `https://your-app-url/docs`
- **Health Check**: `https://your-app-url/health`
- **GitHub**: `https://github.com/Arbaznazir/bus-pricing-analytics-pipeline`

---

**🎯 Your project is production-ready! The API image is already on Docker Hub and can be deployed immediately.**
