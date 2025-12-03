# =============================================================================
# Gemini Video - Production Cloud Run Infrastructure
# Agent 24: Cloud Run Deployment Automation
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "geminivideo-terraform-state"
    prefix = "terraform/state"
  }
}

# =============================================================================
# Provider Configuration
# =============================================================================

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# =============================================================================
# Enable Required APIs
# =============================================================================

resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "compute.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudscheduler.googleapis.com",
    "servicenetworking.googleapis.com",
    "vpcaccess.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "cloudtrace.googleapis.com",
  ])

  project = var.project_id
  service = each.value

  disable_on_destroy = false
}

# =============================================================================
# VPC Network Configuration
# =============================================================================

resource "google_compute_network" "vpc_network" {
  name                    = "${var.project_name}-vpc"
  auto_create_subnetworks = false
  project                 = var.project_id

  depends_on = [google_project_service.required_apis]
}

resource "google_compute_subnetwork" "subnet" {
  name          = "${var.project_name}-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc_network.id
  project       = var.project_id

  private_ip_google_access = true
}

# VPC Connector for Cloud Run to access VPC resources
resource "google_vpc_access_connector" "connector" {
  name          = "${var.project_name}-connector"
  region        = var.region
  network       = google_compute_network.vpc_network.name
  ip_cidr_range = "10.8.0.0/28"
  project       = var.project_id

  depends_on = [google_project_service.required_apis]
}

# Reserve IP for Private Service Connection
resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.project_name}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc_network.id
  project       = var.project_id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# =============================================================================
# Cloud SQL PostgreSQL Instance
# =============================================================================

resource "google_sql_database_instance" "postgres" {
  name             = "${var.project_name}-postgres-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region
  project          = var.project_id

  deletion_protection = var.environment == "production" ? true : false

  settings {
    tier              = var.db_tier
    availability_type = var.environment == "production" ? "REGIONAL" : "ZONAL"
    disk_size         = var.db_disk_size
    disk_type         = "PD_SSD"
    disk_autoresize   = true

    backup_configuration {
      enabled                        = true
      start_time                     = "02:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 30
        retention_unit   = "COUNT"
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc_network.id
      require_ssl     = true
    }

    database_flags {
      name  = "max_connections"
      value = "200"
    }

    database_flags {
      name  = "shared_buffers"
      value = "524288" # 512MB in 8KB pages
    }

    database_flags {
      name  = "work_mem"
      value = "16384" # 16MB in KB
    }

    maintenance_window {
      day          = 7 # Sunday
      hour         = 3
      update_track = "stable"
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

resource "google_sql_database" "database" {
  name     = var.database_name
  instance = google_sql_database_instance.postgres.name
  project  = var.project_id
}

resource "google_sql_user" "users" {
  name     = var.database_user
  instance = google_sql_database_instance.postgres.name
  password = var.database_password
  project  = var.project_id
}

# =============================================================================
# Redis Memorystore Instance
# =============================================================================

resource "google_redis_instance" "cache" {
  name               = "${var.project_name}-redis-${var.environment}"
  tier               = var.environment == "production" ? "STANDARD_HA" : "BASIC"
  memory_size_gb     = var.redis_memory_gb
  region             = var.region
  project            = var.project_id
  redis_version      = "REDIS_7_0"
  display_name       = "Gemini Video Redis Cache"
  reserved_ip_range  = "10.0.1.0/29"
  connect_mode       = "PRIVATE_SERVICE_ACCESS"
  auth_enabled       = true
  transit_encryption_mode = "SERVER_AUTHENTICATION"

  authorized_network = google_compute_network.vpc_network.id

  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 3
        minutes = 0
      }
    }
  }

  redis_configs = {
    maxmemory-policy = "allkeys-lru"
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# =============================================================================
# Secret Manager Secrets
# =============================================================================

resource "google_secret_manager_secret" "secrets" {
  for_each = toset([
    "database-url",
    "redis-url",
    "gemini-api-key",
    "meta-access-token",
    "meta-app-secret",
    "jwt-secret",
    "firebase-credentials",
  ])

  secret_id = "${var.project_name}-${each.value}"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

# =============================================================================
# Artifact Registry Repository
# =============================================================================

resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = var.project_name
  description   = "Docker images for Gemini Video services"
  format        = "DOCKER"
  project       = var.project_id

  depends_on = [google_project_service.required_apis]
}

# =============================================================================
# Service Account for Cloud Run Services
# =============================================================================

resource "google_service_account" "cloud_run_sa" {
  account_id   = "${var.project_name}-cloud-run"
  display_name = "Cloud Run Service Account"
  description  = "Service account for Cloud Run services"
  project      = var.project_id
}

# IAM Bindings for Service Account
resource "google_project_iam_member" "cloud_run_permissions" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/redis.editor",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectAdmin",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# =============================================================================
# Cloud Run Service: Gateway API
# =============================================================================

resource "google_cloud_run_v2_service" "gateway_api" {
  name     = "${var.project_name}-gateway-api"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.cloud_run_sa.email

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    scaling {
      min_instance_count = var.gateway_min_instances
      max_instance_count = var.gateway_max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.project_name}/gateway-api:latest"

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      ports {
        container_port = 8080
      }

      env {
        name  = "NODE_ENV"
        value = "production"
      }

      env {
        name  = "PORT"
        value = "8080"
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["database-url"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "REDIS_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["redis-url"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "JWT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["jwt-secret"].secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 10
        timeout_seconds       = 3
        period_seconds        = 5
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 30
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 3
      }
    }

    timeout = "300s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_service.required_apis,
    google_sql_database_instance.postgres,
    google_redis_instance.cache,
  ]
}

# =============================================================================
# Cloud Run Service: Drive Intel
# =============================================================================

resource "google_cloud_run_v2_service" "drive_intel" {
  name     = "${var.project_name}-drive-intel"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.cloud_run_sa.email

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    scaling {
      min_instance_count = var.service_min_instances
      max_instance_count = var.service_max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.project_name}/drive-intel:latest"

      resources {
        limits = {
          cpu    = "4"
          memory = "4Gi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      ports {
        container_port = 8081
      }

      env {
        name  = "PORT"
        value = "8081"
      }

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["gemini-api-key"].secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8081
        }
        initial_delay_seconds = 15
        timeout_seconds       = 5
        period_seconds        = 5
        failure_threshold     = 5
      }
    }

    timeout = "600s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [google_project_service.required_apis]
}

# =============================================================================
# Cloud Run Service: Video Agent
# =============================================================================

resource "google_cloud_run_v2_service" "video_agent" {
  name     = "${var.project_name}-video-agent"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.cloud_run_sa.email

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    scaling {
      min_instance_count = var.service_min_instances
      max_instance_count = var.service_max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.project_name}/video-agent:latest"

      resources {
        limits = {
          cpu    = "4"
          memory = "8Gi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      ports {
        container_port = 8082
      }

      env {
        name  = "PORT"
        value = "8082"
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8082
        }
        initial_delay_seconds = 20
        timeout_seconds       = 5
        period_seconds        = 5
        failure_threshold     = 5
      }
    }

    timeout = "900s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [google_project_service.required_apis]
}

# =============================================================================
# Cloud Run Service: ML Service
# =============================================================================

resource "google_cloud_run_v2_service" "ml_service" {
  name     = "${var.project_name}-ml-service"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.cloud_run_sa.email

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    scaling {
      min_instance_count = var.service_min_instances
      max_instance_count = var.service_max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.project_name}/ml-service:latest"

      resources {
        limits = {
          cpu    = "4"
          memory = "16Gi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      ports {
        container_port = 8003
      }

      env {
        name  = "PORT"
        value = "8003"
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8003
        }
        initial_delay_seconds = 30
        timeout_seconds       = 10
        period_seconds        = 10
        failure_threshold     = 5
      }
    }

    timeout = "900s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [google_project_service.required_apis]
}

# =============================================================================
# Cloud Run Service: Meta Publisher
# =============================================================================

resource "google_cloud_run_v2_service" "meta_publisher" {
  name     = "${var.project_name}-meta-publisher"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.cloud_run_sa.email

    scaling {
      min_instance_count = var.service_min_instances
      max_instance_count = var.service_max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.project_name}/meta-publisher:latest"

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      ports {
        container_port = 8083
      }

      env {
        name  = "PORT"
        value = "8083"
      }

      env {
        name = "META_ACCESS_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["meta-access-token"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "META_APP_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["meta-app-secret"].secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8083
        }
        initial_delay_seconds = 10
        timeout_seconds       = 3
        period_seconds        = 5
        failure_threshold     = 3
      }
    }

    timeout = "300s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [google_project_service.required_apis]
}

# =============================================================================
# Cloud Run Service: Titan Core
# =============================================================================

resource "google_cloud_run_v2_service" "titan_core" {
  name     = "${var.project_name}-titan-core"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.cloud_run_sa.email

    scaling {
      min_instance_count = var.service_min_instances
      max_instance_count = var.service_max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.project_name}/titan-core:latest"

      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      ports {
        container_port = 8084
      }

      env {
        name  = "PORT"
        value = "8084"
      }

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["gemini-api-key"].secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8084
        }
        initial_delay_seconds = 10
        timeout_seconds       = 3
        period_seconds        = 5
        failure_threshold     = 3
      }
    }

    timeout = "300s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [google_project_service.required_apis]
}

# =============================================================================
# Cloud Run Service: Frontend
# =============================================================================

resource "google_cloud_run_v2_service" "frontend" {
  name     = "${var.project_name}-frontend"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.cloud_run_sa.email

    scaling {
      min_instance_count = var.frontend_min_instances
      max_instance_count = var.frontend_max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.project_name}/frontend:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      ports {
        container_port = 80
      }

      startup_probe {
        http_get {
          path = "/"
          port = 80
        }
        initial_delay_seconds = 5
        timeout_seconds       = 3
        period_seconds        = 3
        failure_threshold     = 3
      }
    }

    timeout = "60s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [google_project_service.required_apis]
}

# =============================================================================
# IAM: Allow Public Access to Frontend
# =============================================================================

resource "google_cloud_run_service_iam_member" "frontend_public" {
  project  = var.project_id
  location = google_cloud_run_v2_service.frontend.location
  service  = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# =============================================================================
# IAM: Allow Public Access to Gateway API (with Cloud Armor)
# =============================================================================

resource "google_cloud_run_service_iam_member" "gateway_public" {
  project  = var.project_id
  location = google_cloud_run_v2_service.gateway_api.location
  service  = google_cloud_run_v2_service.gateway_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# =============================================================================
# Cloud Armor Security Policy
# =============================================================================

resource "google_compute_security_policy" "cloud_armor_policy" {
  name    = "${var.project_name}-security-policy"
  project = var.project_id

  # Rule 1: Rate limiting
  rule {
    action   = "throttle"
    priority = 1000

    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }

    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"

      enforce_on_key = "IP"

      rate_limit_threshold {
        count        = 100
        interval_sec = 60
      }
    }

    description = "Rate limit: 100 requests per minute per IP"
  }

  # Rule 2: Block known bad IPs
  rule {
    action   = "deny(403)"
    priority = 2000

    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = var.blocked_ip_ranges
      }
    }

    description = "Block known malicious IP ranges"
  }

  # Rule 3: SQL injection protection
  rule {
    action   = "deny(403)"
    priority = 3000

    match {
      expr {
        expression = "evaluatePreconfiguredExpr('sqli-stable')"
      }
    }

    description = "SQL injection protection"
  }

  # Rule 4: XSS protection
  rule {
    action   = "deny(403)"
    priority = 4000

    match {
      expr {
        expression = "evaluatePreconfiguredExpr('xss-stable')"
      }
    }

    description = "XSS attack protection"
  }

  # Default rule: Allow all other traffic
  rule {
    action   = "allow"
    priority = 2147483647

    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }

    description = "Default allow rule"
  }

  depends_on = [google_project_service.required_apis]
}

# =============================================================================
# Cloud Build Trigger: Deploy on Git Push
# =============================================================================

resource "google_cloudbuild_trigger" "deploy_trigger" {
  name     = "${var.project_name}-deploy-trigger"
  location = var.region
  project  = var.project_id

  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = "^main$"
    }
  }

  filename = "cloudbuild.yaml"

  depends_on = [google_project_service.required_apis]
}

# =============================================================================
# Outputs
# =============================================================================

output "gateway_api_url" {
  description = "Gateway API URL"
  value       = google_cloud_run_v2_service.gateway_api.uri
}

output "frontend_url" {
  description = "Frontend URL"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "redis_host" {
  description = "Redis instance host"
  value       = google_redis_instance.cache.host
}

output "service_urls" {
  description = "All service URLs"
  value = {
    gateway_api    = google_cloud_run_v2_service.gateway_api.uri
    drive_intel    = google_cloud_run_v2_service.drive_intel.uri
    video_agent    = google_cloud_run_v2_service.video_agent.uri
    ml_service     = google_cloud_run_v2_service.ml_service.uri
    meta_publisher = google_cloud_run_v2_service.meta_publisher.uri
    titan_core     = google_cloud_run_v2_service.titan_core.uri
    frontend       = google_cloud_run_v2_service.frontend.uri
  }
}
