#!/bin/bash
# =============================================================================
# Gemini Video - Terraform Deployment Script
# Agent 24: Cloud Run Deployment Automation
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check gcloud
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI not found. Install from https://cloud.google.com/sdk/docs/install"
        exit 1
    fi

    # Check terraform
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform not found. Install from https://www.terraform.io/downloads"
        exit 1
    fi

    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
        log_error "Not authenticated with gcloud. Run: gcloud auth login"
        exit 1
    fi

    log_success "All prerequisites met"
}

setup_project() {
    log_info "Setting up GCP project..."

    # Get project ID
    if [ -z "$PROJECT_ID" ]; then
        PROJECT_ID=$(gcloud config get-value project)
        if [ -z "$PROJECT_ID" ]; then
            log_error "PROJECT_ID not set. Run: gcloud config set project YOUR_PROJECT_ID"
            exit 1
        fi
    fi

    log_info "Using project: $PROJECT_ID"

    # Set region
    REGION=${REGION:-us-central1}
    log_info "Using region: $REGION"

    # Enable required APIs
    log_info "Enabling required GCP APIs..."
    gcloud services enable \
        run.googleapis.com \
        compute.googleapis.com \
        sqladmin.googleapis.com \
        redis.googleapis.com \
        secretmanager.googleapis.com \
        cloudbuild.googleapis.com \
        artifactregistry.googleapis.com \
        servicenetworking.googleapis.com \
        vpcaccess.googleapis.com \
        --project=$PROJECT_ID

    log_success "GCP APIs enabled"
}

create_state_bucket() {
    BUCKET_NAME="${PROJECT_ID}-terraform-state"

    if gsutil ls -p $PROJECT_ID gs://$BUCKET_NAME &> /dev/null; then
        log_info "Terraform state bucket already exists: $BUCKET_NAME"
    else
        log_info "Creating Terraform state bucket: $BUCKET_NAME"
        gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME
        gsutil versioning set on gs://$BUCKET_NAME
        log_success "Terraform state bucket created"
    fi
}

create_secrets() {
    log_info "Creating Secret Manager secrets..."

    # Database password
    if ! gcloud secrets describe geminivideo-database-url --project=$PROJECT_ID &> /dev/null; then
        log_warning "Secret geminivideo-database-url not found. Creating placeholder..."
        echo -n "postgresql://geminivideo:CHANGEME@localhost:5432/geminivideo" | \
            gcloud secrets create geminivideo-database-url --data-file=- --project=$PROJECT_ID
    fi

    # Redis URL
    if ! gcloud secrets describe geminivideo-redis-url --project=$PROJECT_ID &> /dev/null; then
        log_warning "Secret geminivideo-redis-url not found. Creating placeholder..."
        echo -n "redis://localhost:6379" | \
            gcloud secrets create geminivideo-redis-url --data-file=- --project=$PROJECT_ID
    fi

    # JWT Secret
    if ! gcloud secrets describe geminivideo-jwt-secret --project=$PROJECT_ID &> /dev/null; then
        log_info "Generating JWT secret..."
        openssl rand -base64 64 | \
            gcloud secrets create geminivideo-jwt-secret --data-file=- --project=$PROJECT_ID
    fi

    # Gemini API Key
    if ! gcloud secrets describe geminivideo-gemini-api-key --project=$PROJECT_ID &> /dev/null; then
        log_warning "Secret geminivideo-gemini-api-key not found. Creating placeholder..."
        echo -n "YOUR_GEMINI_API_KEY_HERE" | \
            gcloud secrets create geminivideo-gemini-api-key --data-file=- --project=$PROJECT_ID
    fi

    # Meta Access Token
    if ! gcloud secrets describe geminivideo-meta-access-token --project=$PROJECT_ID &> /dev/null; then
        log_warning "Secret geminivideo-meta-access-token not found. Creating placeholder..."
        echo -n "YOUR_META_ACCESS_TOKEN_HERE" | \
            gcloud secrets create geminivideo-meta-access-token --data-file=- --project=$PROJECT_ID
    fi

    # Meta App Secret
    if ! gcloud secrets describe geminivideo-meta-app-secret --project=$PROJECT_ID &> /dev/null; then
        log_warning "Secret geminivideo-meta-app-secret not found. Creating placeholder..."
        echo -n "YOUR_META_APP_SECRET_HERE" | \
            gcloud secrets create geminivideo-meta-app-secret --data-file=- --project=$PROJECT_ID
    fi

    log_success "Secrets created (remember to update placeholders!)"
}

setup_terraform() {
    log_info "Setting up Terraform..."

    cd terraform

    # Check if tfvars exists
    if [ ! -f terraform.tfvars ]; then
        log_warning "terraform.tfvars not found. Creating from example..."
        cp terraform.tfvars.example terraform.tfvars

        # Update project_id in tfvars
        sed -i.bak "s/your-gcp-project-id/$PROJECT_ID/g" terraform.tfvars
        sed -i.bak "s/us-central1/$REGION/g" terraform.tfvars

        log_warning "Please edit terraform.tfvars with your actual values!"
        log_warning "Especially: database_password, github_owner"
    fi

    # Initialize Terraform
    log_info "Initializing Terraform..."
    terraform init

    log_success "Terraform initialized"
}

deploy() {
    log_info "Deploying infrastructure with Terraform..."

    cd terraform

    # Validate
    log_info "Validating Terraform configuration..."
    terraform validate

    # Plan
    log_info "Creating Terraform plan..."
    terraform plan -out=tfplan

    # Ask for confirmation
    echo ""
    log_warning "Review the plan above. Do you want to proceed with deployment?"
    read -p "Type 'yes' to continue: " confirm

    if [ "$confirm" != "yes" ]; then
        log_error "Deployment cancelled"
        rm -f tfplan
        exit 1
    fi

    # Apply
    log_info "Applying Terraform configuration..."
    terraform apply tfplan
    rm -f tfplan

    log_success "Infrastructure deployed!"

    # Show outputs
    log_info "Service URLs:"
    terraform output
}

cleanup() {
    log_info "Cleaning up..."
    cd ..
}

# Main execution
main() {
    echo ""
    log_info "====================================="
    log_info "Gemini Video - Terraform Deployment"
    log_info "====================================="
    echo ""

    check_prerequisites
    setup_project
    create_state_bucket
    create_secrets
    setup_terraform

    echo ""
    log_warning "Ready to deploy!"
    log_warning "This will create resources that incur costs."
    echo ""

    read -p "Continue with deployment? (yes/no): " deploy_confirm

    if [ "$deploy_confirm" == "yes" ]; then
        deploy
    else
        log_info "Deployment skipped. You can run this script again when ready."
        log_info "Or run: cd terraform && terraform apply"
    fi

    cleanup

    echo ""
    log_success "====================================="
    log_success "Deployment script completed!"
    log_success "====================================="
    echo ""
    log_info "Next steps:"
    log_info "1. Update Secret Manager secrets with real values"
    log_info "2. Build and push Docker images"
    log_info "3. Set up GitHub Actions for CI/CD"
    log_info "4. Configure custom domain (optional)"
    echo ""
}

# Run main function
main "$@"
