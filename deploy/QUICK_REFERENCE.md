# 🚀 GeminiVideo Deployment - Quick Reference Card

## Emergency Commands

### Deploy
```bash
cd deploy && ./deploy.sh
```

### Rollback
```bash
cd deploy && ./rollback.sh
```

### Health Check
```bash
cd deploy && ./health-check.sh
```

---

## Service Status

### Docker Compose
```bash
# Status
docker-compose ps

# Logs (all services)
docker-compose logs -f

# Logs (specific service)
docker-compose logs -f gateway-api

# Restart service
docker-compose restart gateway-api

# Stop all
docker-compose down

# Start all
docker-compose up -d
```

### Kubernetes
```bash
# Status
kubectl get pods -n geminivideo

# Logs
kubectl logs -f deployment/gateway-api -n geminivideo

# Restart
kubectl rollout restart deployment/gateway-api -n geminivideo

# Scale
kubectl scale deployment/gateway-api --replicas=5 -n geminivideo
```

---

## Health Endpoints

| Service | URL |
|---------|-----|
| Gateway API | http://localhost:8080/health |
| Titan Core | http://localhost:8084/health |
| ML Service | http://localhost:8003/health |
| Video Agent | http://localhost:8082/health |
| Meta Publisher | http://localhost:8083/health |
| Drive Intel | http://localhost:8081/health |

---

## Database

### PostgreSQL
```bash
# Connect
psql $DATABASE_URL

# Check connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Long running queries
psql $DATABASE_URL -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC;"

# Kill query
psql $DATABASE_URL -c "SELECT pg_terminate_backend(PID);"
```

### Migrations
```bash
# Gateway API (Prisma)
cd services/gateway-api
npx prisma migrate deploy
npx prisma generate

# SQL Migrations
for f in database_migrations/*.sql; do
  psql $DATABASE_URL -f $f
done
```

---

## Redis

```bash
# Connect
redis-cli

# Check status
redis-cli ping

# Monitor commands
redis-cli monitor

# Memory info
redis-cli info memory

# Clear cache (DANGEROUS!)
redis-cli FLUSHALL
```

---

## Monitoring

### Prometheus
- URL: http://localhost:9090
- Targets: http://localhost:9090/targets
- Alerts: http://localhost:9090/alerts

### Grafana
- URL: http://localhost:3000
- Default: admin/admin
- Dashboard: GeminiVideo Production Dashboard

### Key Queries
```promql
# Service uptime
up{job="gateway-api"}

# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# CPU usage
100 - (rate(node_cpu_seconds_total{mode="idle"}[5m]) * 100)

# Memory usage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

---

## Troubleshooting

### Service Won't Start
```bash
# Check logs
docker logs <container_name>

# Check port conflicts
netstat -tlnp | grep :8080

# Check disk space
df -h

# Check memory
free -h
```

### High CPU/Memory
```bash
# Docker stats
docker stats

# Process list
docker exec -it <container> top

# Restart service
docker-compose restart <service>
```

### Database Issues
```bash
# Check connectivity
pg_isready -h localhost -p 5432

# Check locks
psql $DATABASE_URL -c "SELECT * FROM pg_locks WHERE NOT GRANTED;"

# Check slow queries
psql $DATABASE_URL -c "SELECT query, query_start FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '1 minute';"
```

### Network Issues
```bash
# Test connectivity
curl http://localhost:8080/health

# Check DNS
nslookup api.geminivideo.com

# Check ports
telnet localhost 8080

# Check firewall
sudo ufw status
```

---

## Deployment Checklist

- [ ] Code reviewed and merged
- [ ] Tests passing in CI
- [ ] Staging deployment successful
- [ ] Database backup created
- [ ] Team notified
- [ ] Monitoring dashboard open
- [ ] Run: `./deploy.sh`
- [ ] Verify: `./health-check.sh`
- [ ] Check logs for errors
- [ ] Monitor for 15 minutes
- [ ] Update deployment log

---

## Emergency Contacts

| Role | Contact | Phone | Slack |
|------|---------|-------|-------|
| DevOps Lead | [Name] | [Phone] | @devops-lead |
| CTO | [Name] | [Phone] | @cto |
| On-Call | [Rotation] | [PagerDuty] | #oncall |

---

## Common Issues & Fixes

### "Port already in use"
```bash
# Find process
lsof -i :8080
# Kill process
kill -9 <PID>
```

### "Cannot connect to database"
```bash
# Check PostgreSQL
docker-compose ps postgres
docker-compose restart postgres
```

### "Out of memory"
```bash
# Check memory
docker stats
# Restart with more memory
docker-compose up -d --scale gateway-api=2
```

### "Disk space full"
```bash
# Clean Docker
docker system prune -a
# Clean logs
sudo journalctl --vacuum-time=2d
```

---

## Useful Aliases

Add to `~/.bashrc`:
```bash
alias gv-deploy='cd /opt/geminivideo/deploy && ./deploy.sh'
alias gv-rollback='cd /opt/geminivideo/deploy && ./rollback.sh'
alias gv-health='cd /opt/geminivideo/deploy && ./health-check.sh'
alias gv-logs='cd /opt/geminivideo && docker-compose logs -f'
alias gv-status='cd /opt/geminivideo && docker-compose ps'
```

---

## File Locations

| Item | Path |
|------|------|
| Application | `/opt/geminivideo` |
| Logs | `/var/log/geminivideo` |
| Deployments | `/var/log/geminivideo/deployments` |
| Backups | `/opt/geminivideo/backups` |
| Secrets | `/opt/geminivideo/.env.production` |

---

## Security

### Rotate Secrets
```bash
# Update .env.production
nano /opt/geminivideo/.env.production

# Restart services
docker-compose restart
```

### Check SSL Certificate
```bash
# Check expiry
echo | openssl s_client -servername geminivideo.com -connect geminivideo.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Audit Logs
```bash
# View deployment history
ls -lah /var/log/geminivideo/deployments/

# View rollback history
ls -lah /var/log/geminivideo/rollbacks/
```

---

**Version**: 1.0.0
**Last Updated**: 2025-12-05
**Keep this card accessible during deployments!**
