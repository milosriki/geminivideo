# =============================================================================
# Gemini Video - Terraform Variables
# Agent 24: Cloud Run Deployment Automation
# =============================================================================

# =============================================================================
# Project Configuration
# =============================================================================

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "geminivideo"
}

variable "environment" {
  description = "Environment name (production, staging, development)"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["production", "staging", "development"], var.environment)
    error_message = "Environment must be production, staging, or development."
  }
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

# =============================================================================
# Database Configuration
# =============================================================================

variable "database_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "geminivideo"
}

variable "database_user" {
  description = "PostgreSQL database user"
  type        = string
  default     = "geminivideo"
}

variable "database_password" {
  description = "PostgreSQL database password"
  type        = string
  sensitive   = true
}

variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-custom-2-7680" # 2 vCPUs, 7.5 GB RAM

  validation {
    condition     = can(regex("^db-(custom|f1|g1|n1)", var.db_tier))
    error_message = "Database tier must be a valid Cloud SQL tier."
  }
}

variable "db_disk_size" {
  description = "Database disk size in GB"
  type        = number
  default     = 50

  validation {
    condition     = var.db_disk_size >= 10 && var.db_disk_size <= 65536
    error_message = "Database disk size must be between 10 and 65536 GB."
  }
}

# =============================================================================
# Redis Configuration
# =============================================================================

variable "redis_memory_gb" {
  description = "Redis instance memory in GB"
  type        = number
  default     = 2

  validation {
    condition     = var.redis_memory_gb >= 1 && var.redis_memory_gb <= 300
    error_message = "Redis memory must be between 1 and 300 GB."
  }
}

# =============================================================================
# Cloud Run Scaling Configuration
# =============================================================================

variable "gateway_min_instances" {
  description = "Minimum instances for Gateway API"
  type        = number
  default     = 1

  validation {
    condition     = var.gateway_min_instances >= 0 && var.gateway_min_instances <= 100
    error_message = "Gateway min instances must be between 0 and 100."
  }
}

variable "gateway_max_instances" {
  description = "Maximum instances for Gateway API"
  type        = number
  default     = 10

  validation {
    condition     = var.gateway_max_instances >= 1 && var.gateway_max_instances <= 1000
    error_message = "Gateway max instances must be between 1 and 1000."
  }
}

variable "service_min_instances" {
  description = "Minimum instances for backend services"
  type        = number
  default     = 0

  validation {
    condition     = var.service_min_instances >= 0 && var.service_min_instances <= 100
    error_message = "Service min instances must be between 0 and 100."
  }
}

variable "service_max_instances" {
  description = "Maximum instances for backend services"
  type        = number
  default     = 5

  validation {
    condition     = var.service_max_instances >= 1 && var.service_max_instances <= 1000
    error_message = "Service max instances must be between 1 and 1000."
  }
}

variable "frontend_min_instances" {
  description = "Minimum instances for frontend"
  type        = number
  default     = 1

  validation {
    condition     = var.frontend_min_instances >= 0 && var.frontend_min_instances <= 100
    error_message = "Frontend min instances must be between 0 and 100."
  }
}

variable "frontend_max_instances" {
  description = "Maximum instances for frontend"
  type        = number
  default     = 20

  validation {
    condition     = var.frontend_max_instances >= 1 && var.frontend_max_instances <= 1000
    error_message = "Frontend max instances must be between 1 and 1000."
  }
}

# =============================================================================
# Security Configuration
# =============================================================================

variable "blocked_ip_ranges" {
  description = "List of IP ranges to block in Cloud Armor"
  type        = list(string)
  default = [
    # Add known malicious IP ranges here
    # Example: "192.0.2.0/24"
  ]
}

variable "allowed_cors_origins" {
  description = "Allowed CORS origins"
  type        = list(string)
  default     = []
}

# =============================================================================
# Domain Configuration
# =============================================================================

variable "custom_domain" {
  description = "Custom domain for the application (optional)"
  type        = string
  default     = ""
}

variable "ssl_certificate_name" {
  description = "Name of the SSL certificate (if using custom domain)"
  type        = string
  default     = ""
}

# =============================================================================
# GitHub Configuration
# =============================================================================

variable "github_owner" {
  description = "GitHub repository owner/organization"
  type        = string
  default     = ""
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "geminivideo"
}

# =============================================================================
# Feature Flags
# =============================================================================

variable "enable_cdn" {
  description = "Enable Cloud CDN for frontend"
  type        = bool
  default     = true
}

variable "enable_cloud_armor" {
  description = "Enable Cloud Armor security policies"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Enable advanced monitoring and logging"
  type        = bool
  default     = true
}

variable "enable_backup" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

# =============================================================================
# Cost Optimization
# =============================================================================

variable "enable_cost_alerts" {
  description = "Enable budget alerts"
  type        = bool
  default     = true
}

variable "monthly_budget_amount" {
  description = "Monthly budget amount in USD"
  type        = number
  default     = 500

  validation {
    condition     = var.monthly_budget_amount > 0
    error_message = "Monthly budget must be greater than 0."
  }
}

# =============================================================================
# Tags and Labels
# =============================================================================

variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default = {
    project     = "geminivideo"
    managed_by  = "terraform"
    environment = "production"
  }
}
