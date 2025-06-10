# 🚀 NOVA Bus Pricing Pipeline - Production Deployment Guide

## 📋 Overview

This guide covers deploying the NOVA Bus Pricing Pipeline to production environments with focus on scalability, reliability, and security. The system is designed for containerized deployment with support for cloud platforms and on-premises infrastructure.

## 🎯 Deployment Architecture Options

### 1. **Docker Compose (Recommended for Small-Medium Scale)**

**Use Case**: Single server deployment, development, small production workloads
**Pros**: Simple setup, minimal infrastructure requirements
**Cons**: Limited scalability, single point of failure

### 2. **Kubernetes (Recommended for Enterprise Scale)**

**Use Case**: Multi-server clusters, high availability, auto-scaling
**Pros**: High availability, auto-scaling, rolling updates
**Cons**: Complex setup, requires Kubernetes expertise

### 3. **Cloud Managed Services**

**Use Case**: Fully managed deployment with minimal operational overhead
**Options**: AWS ECS/EKS, Azure Container Instances, Google Cloud Run

## 🐳 Docker Compose Production Deployment

### Prerequisites

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Ubuntu 20.04+** or **CentOS 8+** server
- **Minimum Resources**: 4 CPU cores, 8GB RAM, 50GB storage
- **Recommended Resources**: 8 CPU cores, 16GB RAM, 200GB SSD

### Production Environment Setup

#### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application user
sudo useradd -m -s /bin/bash busapp
sudo usermod -aG docker busapp
```

#### 2. Application Deployment

```bash
# Clone repository
git clone <repository-url> /opt/bus-pricing-pipeline
cd /opt/bus-pricing-pipeline

# Set ownership
sudo chown -R busapp:busapp /opt/bus-pricing-pipeline

# Switch to application user
sudo su - busapp
cd /opt/bus-pricing-pipeline

# Configure production environment
cp .env.example .env.production
```

#### 3. Production Environment Configuration

**File**: `.env.production`

```bash
# Database Configuration
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=busdb_prod
POSTGRES_USER=bususer_prod
POSTGRES_PASSWORD=<STRONG_PASSWORD_HERE>

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Security Settings
ALLOWED_HOSTS=["your-domain.com", "api.your-domain.com"]
CORS_ORIGINS=["https://your-frontend.com"]

# Performance Settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
WORKER_PROCESSES=4

# ETL Configuration
ETL_SCHEDULE_INTERVAL_SECONDS=900  # 15 minutes
MAX_FARE_THRESHOLD=200000
MIN_FARE_THRESHOLD=10

# Monitoring
HEALTH_CHECK_INTERVAL_MINUTES=2
FILE_RETENTION_DAYS=30

# Spark Configuration (for larger datasets)
SPARK_DRIVER_MEMORY=2g
SPARK_EXECUTOR_MEMORY=2g
SPARK_SQL_ADAPTIVE_ENABLED=true
```

#### 4. Production Docker Compose

**File**: `docker-compose.prod.yml`

```yaml
version: "3.8"

services:
  db:
    image: postgres:15
    container_name: bus_pricing_db_prod
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - db_data_prod:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
      - ./backups:/backups
    ports:
      - "127.0.0.1:5432:5432" # Only bind to localhost
    networks:
      - bus_network_prod
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "1.0"

  api:
    build:
      context: ./api
      dockerfile: Dockerfile.prod
    container_name: bus_pricing_api_prod
    depends_on:
      db:
        condition: service_healthy
    environment:
      - POSTGRES_HOST=db
      - POSTGRES_PORT=5432
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
      - API_HOST=${API_HOST}
      - API_PORT=${API_PORT}
      - LOG_LEVEL=${LOG_LEVEL}
      - WORKER_PROCESSES=${WORKER_PROCESSES}
    ports:
      - "127.0.0.1:8000:8000" # Only bind to localhost (behind proxy)
    networks:
      - bus_network_prod
    volumes:
      - ./logs:/app/logs
      - shared_data_prod:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: "1.0"

  etl:
    build:
      context: ./etl
      dockerfile: Dockerfile.prod
    container_name: bus_etl_prod
    depends_on:
      db:
        condition: service_healthy
    environment:
      - POSTGRES_HOST=db
      - POSTGRES_PORT=5432
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
      - RAW_DATA_PATH=/app/data/raw
      - PROCESSED_DATA_PATH=/app/data/processed
      - ERROR_DATA_PATH=/app/data/error
      - SPARK_DRIVER_MEMORY=${SPARK_DRIVER_MEMORY}
      - SPARK_EXECUTOR_MEMORY=${SPARK_EXECUTOR_MEMORY}
      - LOG_LEVEL=${LOG_LEVEL}
    volumes:
      - shared_data_prod:/app/data
      - ./logs:/app/logs
    networks:
      - bus_network_prod
    profiles:
      - manual
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: "2.0"

  scheduler:
    build:
      context: ./scheduler
      dockerfile: Dockerfile.prod
    container_name: bus_scheduler_prod
    depends_on:
      db:
        condition: service_healthy
      api:
        condition: service_healthy
    environment:
      - POSTGRES_HOST=db
      - POSTGRES_PORT=5432
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
      - API_HOST=api
      - API_PORT=8000
      - ETL_SCHEDULE_INTERVAL_SECONDS=${ETL_SCHEDULE_INTERVAL_SECONDS}
      - HEALTH_CHECK_INTERVAL_MINUTES=${HEALTH_CHECK_INTERVAL_MINUTES}
      - LOG_LEVEL=${LOG_LEVEL}
    volumes:
      - shared_data_prod:/app/data
      - ./etl:/app/etl:ro
      - ./data_simulator:/app/data_simulator:ro
      - ./logs:/app/logs
    networks:
      - bus_network_prod
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "0.5"

  nginx:
    image: nginx:alpine
    container_name: bus_nginx_prod
    depends_on:
      - api
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    networks:
      - bus_network_prod
    restart: unless-stopped

volumes:
  db_data_prod:
    driver: local
  shared_data_prod:
    driver: local

networks:
  bus_network_prod:
    driver: bridge
```

#### 5. Nginx Reverse Proxy Configuration

**File**: `nginx/nginx.conf`

```nginx
events {
    worker_connections 1024;
}

http {
    upstream api_backend {
        server api:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=pricing_limit:10m rate=5r/s;

    server {
        listen 80;
        server_name your-domain.com api.your-domain.com;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com api.your-domain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Security Headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # API Routes
        location /api/ {
            rewrite ^/api/(.*)$ /$1 break;
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Rate limiting
            limit_req zone=api_limit burst=20 nodelay;
        }

        # Pricing endpoint with stricter limits
        location /api/pricing/ {
            rewrite ^/api/(.*)$ /$1 break;
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Stricter rate limiting for pricing
            limit_req zone=pricing_limit burst=10 nodelay;
        }

        # Health check (no rate limiting)
        location /health {
            proxy_pass http://api_backend;
            access_log off;
        }

        # Documentation
        location /docs {
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

#### 6. SSL Certificate Setup

```bash
# Using Let's Encrypt (free SSL)
sudo apt install certbot

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com -d api.your-domain.com

# Copy certificates to nginx directory
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
sudo chown -R busapp:busapp nginx/ssl
```

#### 7. Deploy Production Environment

```bash
# Deploy with production configuration
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# Verify deployment
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs --tail=50

# Test API accessibility
curl https://your-domain.com/api/health
```

## ☸️ Kubernetes Deployment

### Prerequisites

- **Kubernetes cluster** (1.20+)
- **kubectl** configured for your cluster
- **Helm** 3.0+ (optional, for package management)
- **Persistent storage** configured in cluster

### Kubernetes Manifests

#### 1. Namespace and ConfigMap

**File**: `k8s/namespace.yaml`

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: bus-pricing-prod
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: bus-pricing-config
  namespace: bus-pricing-prod
data:
  POSTGRES_DB: "busdb_prod"
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  LOG_LEVEL: "INFO"
  ETL_SCHEDULE_INTERVAL_SECONDS: "900"
  HEALTH_CHECK_INTERVAL_MINUTES: "2"
```

#### 2. Secrets

**File**: `k8s/secrets.yaml`

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: bus-pricing-secrets
  namespace: bus-pricing-prod
type: Opaque
data:
  POSTGRES_USER: <base64_encoded_username>
  POSTGRES_PASSWORD: <base64_encoded_password>
```

#### 3. PostgreSQL Deployment

**File**: `k8s/postgres.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: bus-pricing-prod
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:15
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              valueFrom:
                configMapKeyRef:
                  name: bus-pricing-config
                  key: POSTGRES_DB
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: bus-pricing-secrets
                  key: POSTGRES_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: bus-pricing-secrets
                  key: POSTGRES_PASSWORD
          volumeMounts:
            - name: postgres-storage
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              memory: "1Gi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
      volumes:
        - name: postgres-storage
          persistentVolumeClaim:
            claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: bus-pricing-prod
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: bus-pricing-prod
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
```

#### 4. API Deployment

**File**: `k8s/api.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: bus-pricing-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
        - name: api
          image: your-registry/bus-pricing-api:latest
          ports:
            - containerPort: 8000
          env:
            - name: POSTGRES_HOST
              value: "postgres-service"
            - name: POSTGRES_PORT
              value: "5432"
            - name: POSTGRES_DB
              valueFrom:
                configMapKeyRef:
                  name: bus-pricing-config
                  key: POSTGRES_DB
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: bus-pricing-secrets
                  key: POSTGRES_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: bus-pricing-secrets
                  key: POSTGRES_PASSWORD
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: bus-pricing-prod
spec:
  selector:
    app: api
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

#### 5. Ingress Configuration

**File**: `k8s/ingress.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: bus-pricing-ingress
  namespace: bus-pricing-prod
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
    - hosts:
        - api.your-domain.com
      secretName: bus-pricing-tls
  rules:
    - host: api.your-domain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 8000
```

### Deploy to Kubernetes

```bash
# Create namespace and secrets
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n bus-pricing-prod --timeout=300s

# Deploy API and other services
kubectl apply -f k8s/api.yaml
kubectl apply -f k8s/scheduler.yaml
kubectl apply -f k8s/ingress.yaml

# Verify deployment
kubectl get pods -n bus-pricing-prod
kubectl get services -n bus-pricing-prod
kubectl get ingress -n bus-pricing-prod
```

## ☁️ Cloud Platform Deployments

### AWS ECS Deployment

```bash
# Build and push to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com

# Build and tag images
docker build -t bus-pricing-api ./api
docker tag bus-pricing-api:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/bus-pricing-api:latest

# Push to ECR
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/bus-pricing-api:latest

# Deploy using ECS CLI or CloudFormation
ecs-cli compose --project-name bus-pricing service up
```

### Google Cloud Run Deployment

```bash
# Build and deploy to Cloud Run
gcloud builds submit --tag gcr.io/your-project/bus-pricing-api ./api
gcloud run deploy bus-pricing-api --image gcr.io/your-project/bus-pricing-api --platform managed --region us-central1
```

## 🔧 Production Configuration

### Environment Variables Security

```bash
# Use external secret management
export POSTGRES_PASSWORD=$(aws secretsmanager get-secret-value --secret-id prod/bus-pricing/db-password --query SecretString --output text)

# Or use Kubernetes secrets
kubectl create secret generic bus-pricing-secrets \
  --from-literal=POSTGRES_PASSWORD='your-secure-password' \
  -n bus-pricing-prod
```

### Database Optimization

**File**: `postgresql.conf` (production settings)

```ini
# Connection Settings
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB

# Write-Ahead Logging
wal_buffers = 16MB
checkpoint_completion_target = 0.9

# Query Planner
default_statistics_target = 100
random_page_cost = 1.1

# Logging
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
```

### Performance Monitoring

```bash
# Install monitoring stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

# Configure custom metrics
kubectl apply -f monitoring/servicemonitor.yaml
```

## 🔒 Security Hardening

### Container Security

```dockerfile
# Production Dockerfile example
FROM python:3.9-slim as base

# Create non-root user
RUN groupadd -r busapp && useradd -r -g busapp busapp

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app
RUN chown -R busapp:busapp /app

# Switch to non-root user
USER busapp

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Network Security

```yaml
# NetworkPolicy example
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: bus-pricing-netpol
  namespace: bus-pricing-prod
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
```

## 📊 Monitoring and Alerting

### Health Checks

```bash
# Application health endpoint
curl -f http://localhost:8000/health || exit 1

# Database connectivity
docker exec postgres pg_isready -U bususer -d busdb || exit 1

# ETL job monitoring
curl -f http://localhost:8000/admin/etl/history | jq '.[] | select(.status == "failed")'
```

### Log Aggregation

```yaml
# Fluentd DaemonSet for log collection
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: bus-pricing-prod
spec:
  selector:
    matchLabels:
      name: fluentd
  template:
    metadata:
      labels:
        name: fluentd
    spec:
      containers:
        - name: fluentd
          image: fluent/fluentd-kubernetes-daemonset:v1-debian-elasticsearch
          env:
            - name: FLUENT_ELASTICSEARCH_HOST
              value: "elasticsearch.logging.svc.cluster.local"
            - name: FLUENT_ELASTICSEARCH_PORT
              value: "9200"
```

## 🔄 Backup and Recovery

### Database Backup

```bash
# Automated backup script
#!/bin/bash
BACKUP_PATH="/backups/$(date +%Y%m%d_%H%M%S)"
docker exec postgres pg_dump -U bususer busdb > "$BACKUP_PATH.sql"
gzip "$BACKUP_PATH.sql"

# Upload to cloud storage
aws s3 cp "$BACKUP_PATH.sql.gz" s3://your-backup-bucket/database/
```

### Disaster Recovery

```bash
# Database restore
docker exec -i postgres psql -U bususer -d busdb < backup.sql

# Full system restore from backup
docker-compose -f docker-compose.prod.yml down
docker volume rm bus-pricing_db_data_prod
docker-compose -f docker-compose.prod.yml up -d db
# Wait for DB to initialize, then restore data
```

## 📈 Scaling Strategies

### Horizontal Scaling

```yaml
# HorizontalPodAutoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: bus-pricing-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### Database Scaling

```yaml
# PostgreSQL read replicas
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-cluster
  namespace: bus-pricing-prod
spec:
  instances: 3
  primaryUpdateStrategy: unsupervised

  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "256MB"
      effective_cache_size: "1GB"
```

---

**🚀 This deployment guide ensures production-ready deployment** with security, scalability, and operational excellence built-in from day one.
