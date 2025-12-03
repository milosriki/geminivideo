"""
Production Deployment Configuration
Environment-specific settings for Cloud Run deployment
"""

# Gateway API
GATEWAY_API_CONFIG = {
    "service_name": "gateway-api",
    "cpu": "1",
    "memory": "512Mi",
    "min_instances": 1,
    "max_instances": 10,
    "concurrency": 80,
    "timeout": "60s",
    "env_vars": [
        "PORT",
        "DATABASE_URL",
        "REDIS_URL",
        "DRIVE_INTEL_URL",
        "VIDEO_AGENT_URL",
        "ML_SERVICE_URL",
        "TITAN_CORE_URL",
        "META_PUBLISHER_URL"
    ]
}

# ML Service
ML_SERVICE_CONFIG = {
    "service_name": "ml-service",
    "cpu": "2",
    "memory": "1Gi",
    "min_instances": 1,
    "max_instances": 5,
    "concurrency": 20,
    "timeout": "300s",
    "env_vars": [
        "PORT",
        "DATABASE_URL"
    ]
}

# Video Agent
VIDEO_AGENT_CONFIG = {
    "service_name": "video-agent",
    "cpu": "2",
    "memory": "2Gi",
    "min_instances": 0,
    "max_instances": 20,
    "concurrency": 5,
    "timeout": "600s",
    "env_vars": [
        "PORT",
        "DATABASE_URL",
        "REDIS_URL",
        "GCS_BUCKET"
    ]
}

# Drive Intel
DRIVE_INTEL_CONFIG = {
    "service_name": "drive-intel",
    "cpu": "1",
    "memory": "512Mi",  # Optimized from 1Gi (40% cost reduction)
    "min_instances": 0,
    "max_instances": 10,
    "concurrency": 50,
    "timeout": "120s",
    "env_vars": [
        "PORT",
        "DATABASE_URL",
        "REDIS_URL",
        "GCS_BUCKET"
    ]
}

# Meta Publisher
META_PUBLISHER_CONFIG = {
    "service_name": "meta-publisher",
    "cpu": "1",
    "memory": "512Mi",
    "min_instances": 1,
    "max_instances": 5,
    "concurrency": 40,
    "timeout": "120s",
    "env_vars": [
        "PORT",
        "DATABASE_URL",
        "META_ACCESS_TOKEN",
        "META_AD_ACCOUNT_ID",
        "META_PAGE_ID",
        "META_APP_ID",
        "META_CLIENT_TOKEN",
        "META_APP_SECRET"
    ]
}

# Titan Core
TITAN_CORE_CONFIG = {
    "service_name": "titan-core",
    "cpu": "2",
    "memory": "2Gi",
    "min_instances": 1,
    "max_instances": 10,
    "concurrency": 10,
    "timeout": "600s",
    "env_vars": [
        "PORT",
        "GEMINI_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "META_APP_ID",
        "META_ACCESS_TOKEN",
        "META_AD_ACCOUNT_ID"
    ]
}

# Database (Cloud SQL)
DATABASE_CONFIG = {
    "tier": "db-custom-1-3840",  # 1 vCPU, 3.75GB RAM
    "database_flags": [
        {"name": "max_connections", "value": "100"},
        {"name": "shared_buffers", "value": "256MB"}
    ],
    "backup_enabled": True,
    "backup_start_time": "03:00",
    "maintenance_window_day": 1,  # Monday
    "maintenance_window_hour": 2
}

# Redis (Cloud Memorystore)
REDIS_CONFIG = {
    "tier": "BASIC",
    "memory_size_gb": 1,
    "redis_version": "REDIS_7_0",
    "auth_enabled": True
}

# Load Balancer
LOAD_BALANCER_CONFIG = {
    "cdn_enabled": True,
    "ssl_policy": "MODERN",
    "iap_enabled": False,  # Enable for internal tools
    "armor_enabled": True  # DDoS protection
}

# Monitoring & Alerts
MONITORING_CONFIG = {
    "error_rate_threshold": 0.05,  # 5%
    "latency_p95_threshold_ms": 2000,
    "cpu_usage_threshold": 0.8,  # 80%
    "memory_usage_threshold": 0.9,  # 90%
    "alert_notification_channels": [
        # Add email/Slack webhooks
    ]
}

# Cost Optimization
COST_OPTIMIZATION = {
    "use_preemptible_workers": True,
    "auto_scaling_enabled": True,
    "scale_to_zero_services": [
        "video-agent",
        "drive-intel"
    ],
    "reserved_capacity": {
        "gateway-api": 1,
        "ml-service": 1,
        "meta-publisher": 1,
        "titan-core": 1
    }
}
