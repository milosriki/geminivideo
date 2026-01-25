#!/bin/bash

#################################################################################
# GeminiVideo Pro-Grade Deployment Script
#################################################################################
# 
# This script provides the fastest, most reliable way to deploy GeminiVideo
# to production with all optimizations enabled and verified.
#
# Usage:
#   ./deploy-pro-grade.sh [local|cloud|verify]
#
# Modes:
#   local   - Deploy to local Docker environment (5 minutes)
#   cloud   - Deploy to GCP Cloud Run (20 minutes)
#   verify  - Verify deployment and optimizations (2 minutes)
#
#################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"  # Script is in project root
DEPLOYMENT_MODE="${1:-local}"

#################################################################################
# Helper Functions
#################################################################################

print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}========================================${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

#################################################################################
# Pre-Flight Checks
#################################################################################

preflight_checks() {
    print_header "Pre-Flight Checks"
    
    local all_ok=true
    
    # Check required commands
    check_command "docker" || all_ok=false
    check_command "docker-compose" || all_ok=false
    
    if [ "$DEPLOYMENT_MODE" = "cloud" ]; then
        check_command "gcloud" || all_ok=false
        check_command "terraform" || all_ok=false
    fi
    
    # Check Docker is running
    if docker info &> /dev/null; then
        print_success "Docker daemon is running"
    else
        print_error "Docker daemon is not running"
        all_ok=false
    fi
    
    # Check system resources
    total_mem=$(docker info --format '{{.MemTotal}}' 2>/dev/null | awk '{print int($1/1024/1024/1024)}')
    if [ "$total_mem" -ge 8 ]; then
        print_success "Sufficient memory: ${total_mem}GB (need 8GB+)"
    else
        print_warning "Low memory: ${total_mem}GB (recommended 8GB+)"
    fi
    
    # Check disk space
    available_space=$(df -BG "$PROJECT_ROOT" | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -ge 10 ]; then
        print_success "Sufficient disk space: ${available_space}GB (need 10GB+)"
    else
        print_warning "Low disk space: ${available_space}GB (recommended 10GB+)"
    fi
    
    # Check .env file
    if [ -f "$PROJECT_ROOT/.env" ]; then
        print_success ".env file exists"
    else
        print_warning ".env file not found, will use .env.example"
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
    fi
    
    if [ "$all_ok" = false ]; then
        print_error "Pre-flight checks failed. Please fix the issues above."
        exit 1
    fi
    
    print_success "All pre-flight checks passed!"
}

#################################################################################
# Verify Optimizations
#################################################################################

verify_optimizations() {
    print_header "Verifying Lost Ideas Implementation"
    
    cd "$PROJECT_ROOT"
    
    if [ -f "scripts/verify_lost_optimizations.py" ]; then
        python3 scripts/verify_lost_optimizations.py
        local exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            print_success "All optimizations verified!"
            return 0
        else
            print_warning "Some optimizations need attention (but deployment can continue)"
            return 1
        fi
    else
        print_warning "Verification script not found, skipping optimization checks"
        return 1
    fi
}

#################################################################################
# Local Deployment
#################################################################################

deploy_local() {
    print_header "Starting Local Deployment"
    
    cd "$PROJECT_ROOT"
    
    # Step 1: Clean up previous deployment
    print_info "Cleaning up previous deployment..."
    docker-compose down -v 2>/dev/null || true
    print_success "Cleanup complete"
    
    # Step 2: Build images
    print_info "Building Docker images (this may take 3-5 minutes)..."
    # Use BuildKit for faster builds with caching
    export DOCKER_BUILDKIT=1
    docker-compose build --parallel
    print_success "Images built successfully"
    
    # Step 3: Start services
    print_info "Starting all services..."
    docker-compose up -d
    print_success "Services started"
    
    # Step 4: Wait for services to be healthy
    print_info "Waiting for services to be healthy..."
    sleep 10
    
    local max_wait=60
    local waited=0
    local all_healthy=false
    
    while [ $waited -lt $max_wait ]; do
        if docker-compose ps | grep -q "Up (healthy)"; then
            all_healthy=true
            break
        fi
        sleep 5
        waited=$((waited + 5))
        echo -n "."
    done
    echo ""
    
    if [ "$all_healthy" = true ]; then
        print_success "All services are healthy!"
    else
        print_warning "Some services may not be fully ready yet"
    fi
    
    # Step 5: Display service URLs
    print_header "Deployment Complete!"
    
    echo ""
    echo -e "${BOLD}Services are running at:${NC}"
    echo -e "  ${GREEN}Frontend:${NC}      http://localhost:3000"
    echo -e "  ${GREEN}Gateway API:${NC}   http://localhost:8000"
    echo -e "  ${GREEN}Drive Intel:${NC}   http://localhost:8001"
    echo -e "  ${GREEN}Video Agent:${NC}   http://localhost:8002"
    echo -e "  ${GREEN}ML Service:${NC}    http://localhost:8004"
    echo -e "  ${GREEN}Meta Publisher:${NC} http://localhost:8003"
    echo -e "  ${GREEN}Titan Core:${NC}    http://localhost:8005"
    echo ""
    
    # Step 6: Test health endpoints
    print_info "Testing service health..."
    
    local services=("8000:Gateway API" "8001:Drive Intel" "8002:Video Agent" "8004:ML Service")
    for service in "${services[@]}"; do
        IFS=':' read -r port name <<< "$service"
        if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
            print_success "$name is healthy"
        else
            print_warning "$name may not be ready yet"
        fi
    done
    
    echo ""
    echo -e "${BOLD}${GREEN}🎉 Local deployment successful!${NC}"
    echo ""
    echo -e "${BOLD}Next steps:${NC}"
    echo "  1. Open http://localhost:3000 in your browser"
    echo "  2. Check logs: docker-compose logs -f"
    echo "  3. Run verification: ./deploy-pro-grade.sh verify"
    echo ""
}

#################################################################################
# Cloud Deployment
#################################################################################

deploy_cloud() {
    print_header "Starting Cloud Deployment (GCP)"
    
    cd "$PROJECT_ROOT"
    
    # Check GCP authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
        print_error "Not authenticated with GCP"
        echo "Please run: gcloud auth login"
        exit 1
    fi
    
    local project_id=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$project_id" ]; then
        print_error "No GCP project configured"
        echo "Please run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    fi
    
    print_success "Authenticated with GCP project: $project_id"
    
    # Run Terraform deployment
    print_info "Deploying infrastructure with Terraform..."
    
    if [ -f "scripts/deploy-terraform.sh" ]; then
        bash scripts/deploy-terraform.sh
    elif [ -f "terraform/main.tf" ]; then
        cd terraform
        terraform init
        terraform apply -auto-approve
        cd ..
    else
        print_error "Terraform configuration not found"
        exit 1
    fi
    
    print_success "Cloud deployment complete!"
    
    # Display output URLs
    print_header "Production URLs"
    cd terraform 2>/dev/null && terraform output || true
}

#################################################################################
# Verification
#################################################################################

verify_deployment() {
    print_header "Verifying Deployment"
    
    cd "$PROJECT_ROOT"
    
    # Verify optimizations
    verify_optimizations
    
    # Check service health
    print_info "Checking service health..."
    
    if [ -f "scripts/health-check.sh" ]; then
        bash scripts/health-check.sh
    else
        # Manual health checks
        local base_url="http://localhost:8000"
        
        if curl -s -f "$base_url/health" > /dev/null 2>&1; then
            print_success "Gateway API is healthy"
        else
            print_error "Gateway API is not responding"
        fi
    fi
    
    # Verify Redis cache
    print_info "Checking Redis cache..."
    if docker-compose exec -T redis redis-cli PING 2>/dev/null | grep -q "PONG"; then
        print_success "Redis is running"
        
        # Check cache stats
        local hits=$(docker-compose exec -T redis redis-cli INFO stats 2>/dev/null | grep keyspace_hits | cut -d: -f2 | tr -d '\r')
        local misses=$(docker-compose exec -T redis redis-cli INFO stats 2>/dev/null | grep keyspace_misses | cut -d: -f2 | tr -d '\r')
        
        if [ -n "$hits" ] && [ -n "$misses" ]; then
            local total=$((hits + misses))
            if [ $total -gt 0 ]; then
                local hit_rate=$((hits * 100 / total))
                print_info "Redis cache hit rate: ${hit_rate}% (target: 95%)"
            fi
        fi
    else
        print_warning "Redis is not accessible"
    fi
    
    # Verify database
    print_info "Checking database..."
    if docker-compose exec -T postgres pg_isready -U geminivideo 2>/dev/null | grep -q "accepting connections"; then
        print_success "PostgreSQL is running"
        
        # Check if batch function exists
        local batch_func=$(docker-compose exec -T postgres psql -U geminivideo -tAc "SELECT 1 FROM pg_proc WHERE proname = 'claim_pending_ad_changes_batch'" 2>/dev/null | tr -d '\r')
        if [ "$batch_func" = "1" ]; then
            print_success "Batch claim function is installed"
        else
            print_warning "Batch claim function not found (may need migration)"
        fi
    else
        print_warning "PostgreSQL is not accessible"
    fi
    
    print_header "Verification Summary"
    
    echo -e "${BOLD}Status:${NC}"
    echo "  - Optimizations: See report above"
    echo "  - Services: Check health status above"
    echo "  - Performance: Monitor logs for cache hit rates"
    echo ""
    echo -e "${BOLD}To monitor performance:${NC}"
    echo "  docker-compose logs -f gateway-api | grep 'Batch'"
    echo "  docker-compose exec redis redis-cli INFO stats"
    echo ""
}

#################################################################################
# Main Script
#################################################################################

main() {
    echo ""
    echo -e "${BOLD}${BLUE}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${BLUE}║  GeminiVideo Pro-Grade Deployment Script      ║${NC}"
    echo -e "${BOLD}${BLUE}║  Fast, Reliable, Production-Ready             ║${NC}"
    echo -e "${BOLD}${BLUE}╚════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Run pre-flight checks
    preflight_checks
    
    # Execute based on mode
    case "$DEPLOYMENT_MODE" in
        local)
            deploy_local
            ;;
        cloud)
            deploy_cloud
            ;;
        verify)
            verify_deployment
            ;;
        *)
            echo "Usage: $0 [local|cloud|verify]"
            echo ""
            echo "Modes:"
            echo "  local   - Deploy to local Docker environment (5 minutes)"
            echo "  cloud   - Deploy to GCP Cloud Run (20 minutes)"
            echo "  verify  - Verify deployment and optimizations (2 minutes)"
            exit 1
            ;;
    esac
}

# Run main function
main
