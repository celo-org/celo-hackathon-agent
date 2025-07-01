# Deployment Guide

This guide covers deployment options for AI Project Analyzer across different environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
- [Container Orchestration](#container-orchestration)
- [Cloud Deployment](#cloud-deployment)
- [Monitoring & Logging](#monitoring--logging)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum:**

- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB
- OS: Linux/macOS/Windows with Docker support

**Recommended:**

- CPU: 4+ cores
- RAM: 8GB+
- Storage: 50GB+ SSD
- OS: Ubuntu 20.04+ or similar

### Software Dependencies

- **Docker** 24.0+
- **Docker Compose** 2.20+
- **Git** 2.30+
- **SSL Certificates** (for production)

### External Services

- **Google Gemini API** key
- **GitHub** token (optional, for private repos)
- **Database** (PostgreSQL 15+)
- **Cache** (Redis 7+)

## Environment Configuration

### 1. Base Configuration

```bash
# Copy environment template
cp config/env.production .env.prod

# Edit configuration
vim .env.prod
```

### 2. Required Environment Variables

```bash
# API Keys
GOOGLE_API_KEY=your_gemini_api_key
GITHUB_TOKEN=your_github_token  # Optional

# Database
POSTGRES_USER=analyzer_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=analyzer_db
DATABASE_URL=postgresql://analyzer_user:secure_password@postgres:5432/analyzer_db

# Redis
REDIS_PASSWORD=secure_redis_password
REDIS_URL=redis://:secure_redis_password@redis:6379/0

# Security
JWT_SECRET=your_jwt_secret_key_here
CORS_ORIGINS=https://your-domain.com,https://api.your-domain.com

# Application
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production

# Optional: Monitoring
GRAFANA_PASSWORD=secure_grafana_password
```

### 3. SSL Certificates

```bash
# For production, obtain SSL certificates
mkdir -p docker/ssl

# Using Let's Encrypt (example)
certbot certonly --standalone -d your-domain.com -d api.your-domain.com

# Copy certificates
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem docker/ssl/
```

## Development Deployment

### Quick Start

```bash
# Set up development environment
./scripts/dev-setup.sh

# Start all services
./scripts/docker-dev.sh up

# Check status
./scripts/docker-dev.sh status
```

### Manual Development Setup

```bash
# Install dependencies
./scripts/install.sh

# Configure environment
cp config/env.development .env

# Start individual services
./start.sh --dev
```

### Development URLs

- **Frontend**: http://localhost:5173
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **pgAdmin**: http://localhost:5050 (with admin profile)
- **Redis Commander**: http://localhost:8081 (with admin profile)

## Production Deployment

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create deployment directory
sudo mkdir -p /opt/ai-project-analyzer
sudo chown $USER:$USER /opt/ai-project-analyzer
cd /opt/ai-project-analyzer
```

### 2. Deploy Application

```bash
# Clone repository
git clone https://your-repo-url.git .

# Configure environment
cp config/env.production .env.prod
# Edit .env.prod with your configuration

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Check deployment
docker-compose -f docker-compose.prod.yml ps
```

### 3. Initialize Database

```bash
# Run database migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Create initial admin user (if needed)
docker-compose -f docker-compose.prod.yml exec api python -m packages.api.scripts.create_admin
```

### 4. Configure Reverse Proxy

#### Nginx Configuration

```nginx
# /etc/nginx/sites-available/ai-project-analyzer
server {
    listen 80;
    server_name your-domain.com api.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/ssl/fullchain.pem;
    ssl_certificate_key /path/to/ssl/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /path/to/ssl/fullchain.pem;
    ssl_certificate_key /path/to/ssl/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. Setup Monitoring

```bash
# Start monitoring stack
docker-compose -f docker-compose.prod.yml up -d prometheus grafana loki promtail

# Access Grafana
# URL: http://your-server:3000
# Username: admin
# Password: (from GRAFANA_PASSWORD env var)
```

## Container Orchestration

### Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Create overlay network
docker network create --driver overlay analyzer-network

# Deploy stack
docker stack deploy -c docker-compose.prod.yml analyzer-stack

# Check services
docker service ls
```

### Kubernetes

```yaml
# kubernetes/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-project-analyzer
---
# kubernetes/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: analyzer-config
  namespace: ai-project-analyzer
data:
  DATABASE_URL: "postgresql://user:pass@postgres:5432/analyzer_db"
  REDIS_URL: "redis://redis:6379/0"
  # ... other config
---
# kubernetes/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: analyzer-secrets
  namespace: ai-project-analyzer
type: Opaque
stringData:
  GOOGLE_API_KEY: "your-api-key"
  JWT_SECRET: "your-jwt-secret"
  # ... other secrets
```

```bash
# Deploy to Kubernetes
kubectl apply -f kubernetes/

# Check deployment
kubectl get pods -n ai-project-analyzer
```

## Cloud Deployment

### AWS ECS

```json
{
  "family": "ai-project-analyzer",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "your-ecr-repo/ai-project-analyzer-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://..."
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ai-project-analyzer",
          "awslogs-region": "us-east-1"
        }
      }
    }
  ]
}
```

### Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/ai-project-analyzer-api

gcloud run deploy ai-project-analyzer-api \
  --image gcr.io/PROJECT-ID/ai-project-analyzer-api \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL=$DATABASE_URL \
  --set-env-vars GOOGLE_API_KEY=$GOOGLE_API_KEY \
  --allow-unauthenticated
```

### Azure Container Instances

```bash
# Deploy to Azure
az container create \
  --resource-group myResourceGroup \
  --name ai-project-analyzer \
  --image your-registry/ai-project-analyzer-api:latest \
  --dns-name-label ai-project-analyzer \
  --ports 8000 \
  --environment-variables \
    DATABASE_URL=postgresql://... \
    REDIS_URL=redis://... \
  --secure-environment-variables \
    GOOGLE_API_KEY=your-api-key \
    JWT_SECRET=your-jwt-secret
```

## Monitoring & Logging

### Health Checks

```bash
# API health check
curl -f http://your-domain.com/api/health

# Database connectivity
docker-compose exec postgres pg_isready

# Redis connectivity
docker-compose exec redis redis-cli ping
```

### Log Management

```bash
# View logs
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f worker

# Log rotation
docker run --log-driver=syslog \
  --log-opt syslog-address=tcp://your-log-server:514 \
  your-app-image
```

### Metrics & Alerts

- **Prometheus**: Metrics collection
- **Grafana**: Visualization and alerting
- **Loki**: Log aggregation
- **Alert Manager**: Alert routing

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs
docker-compose logs service-name

# Check configuration
docker-compose config

# Validate environment
docker-compose exec service-name env
```

#### 2. Database Connection Issues

```bash
# Test database connectivity
docker-compose exec api python -c "
import psycopg2
conn = psycopg2.connect('$DATABASE_URL')
print('Database connected successfully')
"

# Check database status
docker-compose exec postgres pg_isready
```

#### 3. SSL Certificate Issues

```bash
# Test SSL certificate
openssl s_client -connect your-domain.com:443

# Renew Let's Encrypt certificate
certbot renew --dry-run
```

#### 4. High Memory Usage

```bash
# Check container resource usage
docker stats

# Limit container resources
docker-compose up -d --memory="1g" --cpus="1.0"
```

### Performance Optimization

#### 1. Database Optimization

```sql
-- Enable query optimization
ANALYZE;

-- Check slow queries
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

#### 2. Cache Optimization

```bash
# Monitor Redis usage
docker-compose exec redis redis-cli info memory

# Set memory limits
docker-compose exec redis redis-cli config set maxmemory 1gb
```

#### 3. Application Optimization

- **Worker Scaling**: Increase worker processes for CPU-intensive tasks
- **Connection Pooling**: Configure database connection pooling
- **CDN**: Use CDN for static assets
- **Load Balancing**: Deploy multiple API instances

### Backup & Recovery

```bash
# Database backup
docker-compose exec postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql

# Database restore
docker-compose exec -T postgres psql -U $POSTGRES_USER $POSTGRES_DB < backup.sql

# Volume backup
docker run --rm -v analyzer_postgres_data:/data -v $(pwd):/backup busybox tar czf /backup/postgres-backup.tar.gz /data
```

### Security Hardening

1. **Network Security**: Use firewalls and VPN
2. **Container Security**: Run containers as non-root
3. **Secrets Management**: Use external secret stores
4. **Regular Updates**: Keep base images updated
5. **Audit Logging**: Enable comprehensive logging
6. **Access Control**: Implement proper authentication

For additional support, check the [troubleshooting section](../README.md#troubleshooting) in the main README.
