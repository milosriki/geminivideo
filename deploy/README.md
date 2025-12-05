# GeminiVideo Production Deployment System

## Overview

This directory contains the complete production deployment infrastructure for GeminiVideo, a €5M investment-grade AI-powered video advertising platform. The deployment system is designed for **zero-downtime deployments** with **automatic rollback** capabilities.

## 🎯 Key Features

- ✅ **Zero-Downtime Deployment**: Blue-green deployment strategy
- ✅ **Automatic Rollback**: Reverts on failure detection
- ✅ **Health Checks**: Comprehensive health monitoring at every stage
- ✅ **Database Migrations**: Safe, versioned database updates
- ✅ **Multi-Platform Support**: AWS, GCP, DigitalOcean, self-hosted
- ✅ **Kubernetes Ready**: Full K8s manifests included
- ✅ **Production Monitoring**: Prometheus + Grafana dashboards
- ✅ **CI/CD Pipeline**: GitHub Actions workflow

## 📁 Directory Structure

```
deploy/
├── deploy.sh                    # Main deployment script
├── rollback.sh                  # Emergency rollback script
├── Dockerfile.gateway           # Gateway API production image
├── Dockerfile.titan             # Titan Core AI service image
├── Dockerfile.ml                # ML Service image
├── Dockerfile.video             # Video Agent image
├── kubernetes/                  # Kubernetes manifests
│   ├── namespace.yaml          # K8s namespace
│   ├── configmap.yaml          # Configuration
│   ├── secrets.yaml.template   # Secrets template
│   ├── deployment-*.yaml       # Service deployments
│   ├── service.yaml            # K8s services
│   ├── ingress.yaml            # Ingress configuration
│   └── hpa.yaml                # Horizontal Pod Autoscaler
└── monitoring/                  # Monitoring configuration
    ├── prometheus.yml          # Prometheus config
    ├── alerting-rules.yml      # Alert definitions
    └── grafana-dashboard.json  # Grafana dashboard
```

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- docker-compose 2.0+
- PostgreSQL 15+
- Redis 7+
- 5GB+ free disk space
- (Optional) Kubernetes 1.24+

### 1. Configure Environment

```bash
# Copy and configure production environment
cp ../.env.production.example ../.env.production
nano ../.env.production  # Edit with your credentials
```

### 2. Run Deployment

```bash
cd deploy
chmod +x deploy.sh rollback.sh
./deploy.sh
```

The deployment script will:
1. ✅ Run pre-deployment checks
2. ✅ Build Docker images
3. ✅ Run database migrations
4. ✅ Deploy new environment
5. ✅ Run health checks
6. ✅ Switch traffic
7. ✅ Clean up old environment

### 3. Monitor Deployment

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f gateway-api

# Health check
curl http://localhost:8080/health
```

## 🔄 Rollback Procedure

If something goes wrong, rollback immediately:

```bash
./rollback.sh [deployment-id]
```

The rollback script will:
1. ✅ Backup current state
2. ✅ Stop current deployment
3. ✅ Restore previous deployment
4. ✅ (Optional) Restore database
5. ✅ Verify rollback success

## 🐳 Docker Deployment

### Standard Docker Compose

```bash
# Production deployment
docker-compose -f ../docker-compose.production.yml up -d

# Check status
docker-compose -f ../docker-compose.production.yml ps

# View logs
docker-compose -f ../docker-compose.production.yml logs -f
```

### Using Production Dockerfiles

```bash
# Build gateway service
docker build -f Dockerfile.gateway -t geminivideo-gateway:latest ..

# Build all services
for service in gateway titan ml video; do
  docker build -f Dockerfile.$service -t geminivideo-$service:latest ..
done
```

## ☸️ Kubernetes Deployment

### Setup Kubernetes

```bash
# Create namespace
kubectl apply -f kubernetes/namespace.yaml

# Create ConfigMap
kubectl apply -f kubernetes/configmap.yaml

# Create secrets (configure secrets.yaml first!)
cp kubernetes/secrets.yaml.template kubernetes/secrets.yaml
# Edit secrets.yaml with base64-encoded values
kubectl apply -f kubernetes/secrets.yaml
```

### Deploy Services

```bash
# Deploy all services
kubectl apply -f kubernetes/deployment-gateway.yaml
kubectl apply -f kubernetes/deployment-titan.yaml
kubectl apply -f kubernetes/deployment-ml.yaml
kubectl apply -f kubernetes/deployment-video.yaml

# Create services
kubectl apply -f kubernetes/service.yaml

# Setup ingress
kubectl apply -f kubernetes/ingress.yaml

# Enable auto-scaling
kubectl apply -f kubernetes/hpa.yaml
```

### Monitor Kubernetes Deployment

```bash
# Check pods
kubectl get pods -n geminivideo

# Check services
kubectl get services -n geminivideo

# View logs
kubectl logs -f deployment/gateway-api -n geminivideo

# Check rollout status
kubectl rollout status deployment/gateway-api -n geminivideo
```

## 📊 Monitoring Setup

### Prometheus

```bash
# Start Prometheus
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v $(pwd)/monitoring/alerting-rules.yml:/etc/prometheus/alerting-rules.yml \
  prom/prometheus

# Access Prometheus UI
open http://localhost:9090
```

### Grafana

```bash
# Start Grafana
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana

# Access Grafana UI (admin/admin)
open http://localhost:3000

# Import dashboard
# Go to Dashboards -> Import -> Upload JSON
# Use monitoring/grafana-dashboard.json
```

### Key Metrics to Monitor

- **Service Availability**: `up{job="gateway-api"}`
- **Request Rate**: `rate(http_requests_total[5m])`
- **Error Rate**: `rate(http_requests_total{status=~"5.."}[5m])`
- **Latency P95**: `histogram_quantile(0.95, http_request_duration_seconds_bucket)`
- **CPU Usage**: `100 - (rate(node_cpu_seconds_total{mode="idle"}[5m]) * 100)`
- **Memory Usage**: `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100`

## 🔐 Security Considerations

### Before Production Deployment

1. ✅ **Update all secrets** in `.env.production`
2. ✅ **Configure Kubernetes secrets** properly
3. ✅ **Enable HTTPS/TLS** on ingress
4. ✅ **Set up firewall rules** (only expose necessary ports)
5. ✅ **Enable authentication** on monitoring endpoints
6. ✅ **Configure backup strategy** for database
7. ✅ **Set up log aggregation** (ELK, Loki, etc.)

### Secret Management

```bash
# Never commit secrets to git!
echo "kubernetes/secrets.yaml" >> ../.gitignore
echo ".env.production" >> ../.gitignore

# Use environment-specific secret management
# - AWS: AWS Secrets Manager
# - GCP: Google Secret Manager
# - Azure: Azure Key Vault
# - K8s: External Secrets Operator
```

## 🧪 Testing Before Production

### 1. Local Testing

```bash
# Test deployment locally
docker-compose -f ../docker-compose.yml up -d

# Run smoke tests
curl http://localhost:8080/health
```

### 2. Staging Deployment

```bash
# Deploy to staging first
DEPLOYMENT_ENV=staging ./deploy.sh

# Run full test suite
pytest ../tests/ -v

# Run load tests
cd ../deploy
./load_test.sh
```

### 3. Production Readiness Checklist

- [ ] All tests passing
- [ ] Staging deployment successful
- [ ] Database migrations tested
- [ ] Rollback procedure tested
- [ ] Monitoring configured
- [ ] Alerting configured
- [ ] Backup strategy in place
- [ ] Disaster recovery plan documented
- [ ] Team notified

## 🚨 Troubleshooting

### Deployment Fails

```bash
# Check logs
docker-compose logs -f

# Check service health
curl http://localhost:8080/health

# Check database connectivity
psql $DATABASE_URL -c "SELECT 1"

# Check Redis connectivity
redis-cli ping
```

### Service Not Starting

```bash
# Check container status
docker ps -a

# View container logs
docker logs <container_id>

# Check resource usage
docker stats

# Restart service
docker-compose restart gateway-api
```

### Database Migration Issues

```bash
# Check migration status
cd ../services/gateway-api
npx prisma migrate status

# Reset migrations (DESTRUCTIVE!)
npx prisma migrate reset

# Apply pending migrations
npx prisma migrate deploy
```

### High CPU/Memory Usage

```bash
# Check resource usage
docker stats

# Scale down if needed
docker-compose up -d --scale gateway-api=1

# Check for memory leaks
docker exec -it geminivideo-gateway-api sh
top
```

## 📞 Support

### Emergency Contacts

- **DevOps Lead**: [Your Contact]
- **CTO**: [Your Contact]
- **On-Call Rotation**: [PagerDuty/OpsGenie]

### Runbooks

- [Service Down](https://docs.geminivideo.com/runbooks/service-down)
- [High Error Rate](https://docs.geminivideo.com/runbooks/high-error-rate)
- [Database Issues](https://docs.geminivideo.com/runbooks/database)
- [Performance Issues](https://docs.geminivideo.com/runbooks/performance)

## 📝 Deployment Checklist

Use this checklist for each production deployment:

- [ ] Code reviewed and approved
- [ ] All tests passing in CI
- [ ] Staging deployment successful
- [ ] Database migrations tested
- [ ] Backup created before deployment
- [ ] Team notified of deployment window
- [ ] Monitoring dashboard open
- [ ] Rollback plan ready
- [ ] Post-deployment verification plan ready
- [ ] Incident response team on standby

## 🎓 Additional Resources

- [Architecture Documentation](../ARCHITECTURE.md)
- [API Documentation](../docs/api/)
- [Security Guide](../SECURITY.md)
- [Performance Tuning](../docs/performance.md)
- [Disaster Recovery](../docs/disaster-recovery.md)

## 📄 License

Proprietary - GeminiVideo Platform
