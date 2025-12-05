#!/bin/bash

################################################################################
# Monitoring Stack Setup Script
#
# Installs and configures:
# - Prometheus (metrics collection)
# - Grafana (visualization)
# - Node Exporter (system metrics)
# - Alert Manager (alerting)
#
# Usage: ./setup.sh [docker|kubernetes]
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
MONITORING_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_MODE="${1:-docker}"
PROMETHEUS_VERSION="v2.45.0"
GRAFANA_VERSION="10.0.0"
NODE_EXPORTER_VERSION="1.6.0"

echo -e "${GREEN}=== GeminiVideo Monitoring Stack Setup ===${NC}"
echo "Deploy mode: $DEPLOY_MODE"
echo "Monitoring directory: $MONITORING_DIR"
echo ""

################################################################################
# Helper Functions
################################################################################

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed"
        return 1
    fi
    log_info "$1 is installed"
    return 0
}

################################################################################
# Docker Deployment
################################################################################

deploy_docker() {
    log_info "Deploying monitoring stack with Docker Compose"

    # Check Docker
    check_command docker || exit 1
    check_command docker-compose || exit 1

    # Create docker-compose.yml
    cat > "${MONITORING_DIR}/docker-compose.monitoring.yml" <<EOF
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:${PROMETHEUS_VERSION}
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerts:/etc/prometheus/alerts
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--web.enable-lifecycle'
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:${GRAFANA_VERSION}
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=\${GRAFANA_ADMIN_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_ROOT_URL=\${GRAFANA_ROOT_URL:-http://localhost:3000}
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./dashboards:/etc/grafana/dashboards
    depends_on:
      - prometheus
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:v${NODE_EXPORTER_VERSION}
    container_name: node-exporter
    restart: unless-stopped
    ports:
      - "9100:9100"
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    networks:
      - monitoring

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    restart: unless-stopped
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    networks:
      - monitoring

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: redis-exporter
    restart: unless-stopped
    ports:
      - "9121:9121"
    environment:
      - REDIS_ADDR=\${REDIS_HOST:-redis:6379}
      - REDIS_PASSWORD=\${REDIS_PASSWORD:-}
    networks:
      - monitoring

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: postgres-exporter
    restart: unless-stopped
    ports:
      - "9187:9187"
    environment:
      - DATA_SOURCE_NAME=postgresql://\${POSTGRES_USER:-postgres}:\${POSTGRES_PASSWORD:-postgres}@\${POSTGRES_HOST:-postgres:5432}/\${POSTGRES_DB:-geminivideo}?sslmode=disable
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:

networks:
  monitoring:
    driver: bridge
EOF

    # Create Prometheus configuration
    create_prometheus_config

    # Create AlertManager configuration
    create_alertmanager_config

    # Create Grafana provisioning
    create_grafana_provisioning

    # Start services
    log_info "Starting monitoring services..."
    cd "${MONITORING_DIR}"
    docker-compose -f docker-compose.monitoring.yml up -d

    log_info "Monitoring stack deployed successfully!"
    echo ""
    echo "Access points:"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana: http://localhost:3000 (admin/admin)"
    echo "  AlertManager: http://localhost:9093"
    echo ""
}

################################################################################
# Kubernetes Deployment
################################################################################

deploy_kubernetes() {
    log_info "Deploying monitoring stack to Kubernetes"

    # Check kubectl
    check_command kubectl || exit 1
    check_command helm || exit 1

    # Add Prometheus Helm repo
    log_info "Adding Prometheus Helm repository..."
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo update

    # Create namespace
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

    # Install Prometheus Stack
    log_info "Installing Prometheus Stack..."
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --set prometheus.prometheusSpec.retention=30d \
        --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=50Gi \
        --set grafana.adminPassword="${GRAFANA_ADMIN_PASSWORD:-admin}" \
        --wait

    # Deploy custom dashboards
    log_info "Deploying custom Grafana dashboards..."
    kubectl create configmap grafana-dashboards \
        --from-file="${MONITORING_DIR}/dashboards/" \
        --namespace monitoring \
        --dry-run=client -o yaml | kubectl apply -f -

    log_info "Monitoring stack deployed to Kubernetes!"
    echo ""
    echo "Access Grafana:"
    echo "  kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
    echo "  Then visit: http://localhost:3000"
    echo ""
    echo "Access Prometheus:"
    echo "  kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090"
    echo "  Then visit: http://localhost:9090"
    echo ""
}

################################################################################
# Configuration Files
################################################################################

create_prometheus_config() {
    log_info "Creating Prometheus configuration..."

    cat > "${MONITORING_DIR}/prometheus.yml" <<'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'geminivideo-prod'
    environment: 'production'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

# Load alert rules
rule_files:
  - '/etc/prometheus/alerts/*.yml'

# Scrape configurations
scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Node Exporter
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  # Redis Exporter
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # PostgreSQL Exporter
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Python services (FastAPI)
  - job_name: 'titan-core'
    static_configs:
      - targets: ['titan-core:8080']
    metrics_path: '/metrics'

  - job_name: 'ml-service'
    static_configs:
      - targets: ['ml-service:8000']
    metrics_path: '/metrics'

  - job_name: 'video-agent'
    static_configs:
      - targets: ['video-agent:8000']
    metrics_path: '/metrics'

  # Node.js services (Express)
  - job_name: 'gateway-api'
    static_configs:
      - targets: ['gateway-api:3000']
    metrics_path: '/metrics'

  - job_name: 'meta-publisher'
    static_configs:
      - targets: ['meta-publisher:3001']
    metrics_path: '/metrics'

  - job_name: 'google-ads'
    static_configs:
      - targets: ['google-ads:3002']
    metrics_path: '/metrics'

  - job_name: 'tiktok-ads'
    static_configs:
      - targets: ['tiktok-ads:3003']
    metrics_path: '/metrics'
EOF

    # Create alerts directory
    mkdir -p "${MONITORING_DIR}/alerts"

    # Create alert rules
    cat > "${MONITORING_DIR}/alerts/rules.yml" <<'EOF'
groups:
  - name: api_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
          / sum(rate(http_requests_total[5m])) by (service) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected on {{ $labels.service }}"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected on {{ $labels.service }}"
          description: "P95 latency is {{ $value }}s"

  - name: ai_alerts
    interval: 1m
    rules:
      - alert: HighAICost
        expr: sum(rate(ai_api_cost_total[1h])) * 3600 > 500
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High AI API cost detected"
          description: "Current cost rate is ${{ $value }}/hour"

      - alert: AIAPIErrors
        expr: sum(rate(ai_api_errors_total[5m])) by (provider) > 0.1
        for: 5m
        labels:
          severity: error
        annotations:
          summary: "AI API errors detected for {{ $labels.provider }}"
          description: "Error rate: {{ $value }}/s"

  - name: system_alerts
    interval: 30s
    rules:
      - alert: ServiceDown
        expr: service_health == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.service }} is down"
          description: "Service health check failed"

      - alert: HighDatabaseConnections
        expr: |
          database_connections{state="active"} /
          (database_connections{state="active"} + database_connections{state="idle"}) > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High database connection usage on {{ $labels.service }}"
          description: "Connection pool usage: {{ $value | humanizePercentage }}"

      - alert: HighQueueDepth
        expr: queue_depth > 5000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High queue depth: {{ $labels.queue_name }}"
          description: "Queue depth is {{ $value }}"
EOF
}

create_alertmanager_config() {
    log_info "Creating AlertManager configuration..."

    cat > "${MONITORING_DIR}/alertmanager.yml" <<'EOF'
global:
  resolve_timeout: 5m
  smtp_smarthost: '${SMTP_HOST}:${SMTP_PORT}'
  smtp_from: '${ALERT_EMAIL_FROM}'
  smtp_auth_username: '${SMTP_USER}'
  smtp_auth_password: '${SMTP_PASSWORD}'
  smtp_require_tls: true

route:
  group_by: ['alertname', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical'
      continue: true
    - match:
        severity: warning
      receiver: 'warning'

receivers:
  - name: 'default'
    email_configs:
      - to: '${ALERT_EMAIL_TO}'
        headers:
          Subject: '[ALERT] {{ .GroupLabels.alertname }}'

  - name: 'critical'
    email_configs:
      - to: '${ALERT_EMAIL_TO}'
        headers:
          Subject: '[CRITICAL] {{ .GroupLabels.alertname }}'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#alerts-critical'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'warning'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'service']
EOF
}

create_grafana_provisioning() {
    log_info "Creating Grafana provisioning files..."

    mkdir -p "${MONITORING_DIR}/grafana/provisioning/datasources"
    mkdir -p "${MONITORING_DIR}/grafana/provisioning/dashboards"

    # Datasource provisioning
    cat > "${MONITORING_DIR}/grafana/provisioning/datasources/prometheus.yml" <<'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
    jsonData:
      timeInterval: "15s"
EOF

    # Dashboard provisioning
    cat > "${MONITORING_DIR}/grafana/provisioning/dashboards/dashboards.yml" <<'EOF'
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/dashboards
EOF
}

################################################################################
# Main
################################################################################

case "$DEPLOY_MODE" in
    docker)
        deploy_docker
        ;;
    kubernetes|k8s)
        deploy_kubernetes
        ;;
    *)
        log_error "Unknown deploy mode: $DEPLOY_MODE"
        echo "Usage: $0 [docker|kubernetes]"
        exit 1
        ;;
esac

log_info "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure alert channels in .env:"
echo "   - SMTP settings for email alerts"
echo "   - SLACK_WEBHOOK_URL for Slack alerts"
echo "   - PAGERDUTY_INTEGRATION_KEY for PagerDuty"
echo ""
echo "2. Import dashboards in Grafana:"
echo "   - API Performance"
echo "   - AI Costs"
echo "   - Business Metrics"
echo "   - System Health"
echo ""
echo "3. Test alerting:"
echo "   - Trigger a test alert to verify channels"
echo ""
