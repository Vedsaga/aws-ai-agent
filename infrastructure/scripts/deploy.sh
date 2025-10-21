#!/bin/bash

# Multi-Agent Orchestration System - Deployment Script
# This script automates the complete deployment process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed. Please install Node.js 18+"
        exit 1
    fi
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        log_error "Node.js version must be 18 or higher. Current: $(node --version)"
        exit 1
    fi
    log_success "Node.js $(node --version) detected"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install AWS CLI"
        exit 1
    fi
    log_success "AWS CLI $(aws --version | cut -d' ' -f1) detected"
    
    # Check CDK CLI
    if ! command -v cdk &> /dev/null; then
        log_error "AWS CDK CLI is not installed. Run: npm install -g aws-cdk"
        exit 1
    fi
    log_success "AWS CDK $(cdk --version) detected"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.11+"
        exit 1
    fi
    log_success "Python $(python3 --version) detected"
    
    # Verify AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run: aws configure"
        exit 1
    fi
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    AWS_USER=$(aws sts get-caller-identity --query Arn --output text)
    log_success "AWS credentials verified: $AWS_USER"
    log_info "AWS Account: $AWS_ACCOUNT"
}

# Load environment variables
load_environment() {
    log_info "Loading environment configuration..."
    
    if [ ! -f .env ]; then
        log_warning ".env file not found. Creating from .env.example..."
        if [ -f .env.example ]; then
            cp .env.example .env
            log_info "Please edit .env file with your configuration"
            log_info "Required: AWS_ACCOUNT_ID, AWS_REGION, STAGE"
            exit 1
        else
            log_error ".env.example not found"
            exit 1
        fi
    fi
    
    # Source environment variables
    export $(grep -v '^#' .env | xargs)
    
    # Set defaults
    export AWS_REGION=${AWS_REGION:-us-east-1}
    export STAGE=${STAGE:-dev}
    export AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
    
    log_success "Environment loaded: Region=$AWS_REGION, Stage=$STAGE, Account=$AWS_ACCOUNT_ID"
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    
    # Install CDK dependencies
    npm install
    log_success "CDK dependencies installed"
    
    # Build TypeScript
    log_info "Building TypeScript..."
    npm run build
    log_success "TypeScript build complete"
}

# Bootstrap CDK
bootstrap_cdk() {
    log_info "Checking CDK bootstrap status..."
    
    # Check if already bootstrapped
    BOOTSTRAP_STACK="CDKToolkit"
    if aws cloudformation describe-stacks --stack-name $BOOTSTRAP_STACK --region $AWS_REGION &> /dev/null; then
        log_success "CDK already bootstrapped in $AWS_REGION"
    else
        log_info "Bootstrapping CDK in $AWS_REGION..."
        cdk bootstrap aws://${AWS_ACCOUNT_ID}/${AWS_REGION}
        log_success "CDK bootstrap complete"
    fi
}

# Deploy stacks
deploy_stacks() {
    log_info "Deploying CDK stacks..."
    log_warning "This will take approximately 25-30 minutes"
    
    # Deploy all stacks
    log_info "Deploying all stacks..."
    cdk deploy --all --require-approval never
    
    log_success "All stacks deployed successfully"
}

# Initialize database
initialize_database() {
    log_info "Initializing database schema..."
    
    # Get DB init function name from stack outputs
    DB_INIT_FUNCTION=$(aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Data \
        --query 'Stacks[0].Outputs[?OutputKey==`DbInitFunctionName`].OutputValue' \
        --output text \
        --region $AWS_REGION 2>/dev/null || echo "")
    
    if [ -z "$DB_INIT_FUNCTION" ]; then
        log_warning "Database init function not found in stack outputs. Skipping..."
        return
    fi
    
    log_info "Invoking database initialization: $DB_INIT_FUNCTION"
    aws lambda invoke \
        --function-name $DB_INIT_FUNCTION \
        --region $AWS_REGION \
        --log-type Tail \
        db-init-response.json > /dev/null
    
    if [ -f db-init-response.json ]; then
        if grep -q "error" db-init-response.json; then
            log_error "Database initialization failed:"
            cat db-init-response.json
            rm db-init-response.json
            return 1
        else
            log_success "Database initialized successfully"
            rm db-init-response.json
        fi
    fi
}

# Initialize OpenSearch
initialize_opensearch() {
    log_info "Initializing OpenSearch index..."
    
    # Get OpenSearch init function name from stack outputs
    OS_INIT_FUNCTION=$(aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Data \
        --query 'Stacks[0].Outputs[?OutputKey==`OpenSearchInitFunctionName`].OutputValue' \
        --output text \
        --region $AWS_REGION 2>/dev/null || echo "")
    
    if [ -z "$OS_INIT_FUNCTION" ]; then
        log_warning "OpenSearch init function not found in stack outputs. Skipping..."
        return
    fi
    
    log_info "Invoking OpenSearch initialization: $OS_INIT_FUNCTION"
    aws lambda invoke \
        --function-name $OS_INIT_FUNCTION \
        --region $AWS_REGION \
        --log-type Tail \
        os-init-response.json > /dev/null
    
    if [ -f os-init-response.json ]; then
        if grep -q "error" os-init-response.json; then
            log_error "OpenSearch initialization failed:"
            cat os-init-response.json
            rm os-init-response.json
            return 1
        else
            log_success "OpenSearch initialized successfully"
            rm os-init-response.json
        fi
    fi
}

# Create test user
create_test_user() {
    log_info "Creating test user..."
    
    # Get credentials from environment
    TEST_USERNAME="${TEST_USERNAME:-testuser}"
    TEST_PASSWORD="${TEST_PASSWORD}"
    
    if [ -z "$TEST_PASSWORD" ]; then
        log_warning "TEST_PASSWORD not set in .env file, skipping test user creation"
        return 0
    fi
    
    # Get User Pool ID
    USER_POOL_ID=$(aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Auth \
        --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
        --output text \
        --region $AWS_REGION)
    
    if [ -z "$USER_POOL_ID" ]; then
        log_error "User Pool ID not found"
        return 1
    fi
    
    # Check if user already exists
    if aws cognito-idp admin-get-user \
        --user-pool-id $USER_POOL_ID \
        --username $TEST_USERNAME \
        --region $AWS_REGION &> /dev/null; then
        log_warning "Test user '$TEST_USERNAME' already exists"
    else
        # Create test user
        aws cognito-idp admin-create-user \
            --user-pool-id $USER_POOL_ID \
            --username $TEST_USERNAME \
            --user-attributes \
                Name=email,Value=test@example.com \
                Name=custom:tenant_id,Value=test-tenant-123 \
            --temporary-password TempPassword123! \
            --region $AWS_REGION > /dev/null
        
        # Set permanent password
        aws cognito-idp admin-set-user-password \
            --user-pool-id $USER_POOL_ID \
            --username $TEST_USERNAME \
            --password "$TEST_PASSWORD" \
            --permanent \
            --region $AWS_REGION > /dev/null
        
        log_success "Test user created: $TEST_USERNAME (password in .env)"
    fi
}

# Display stack outputs
display_outputs() {
    log_info "Retrieving stack outputs..."
    
    echo ""
    echo "=========================================="
    echo "DEPLOYMENT OUTPUTS"
    echo "=========================================="
    
    # Auth Stack
    echo ""
    echo "Auth Stack:"
    aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Auth \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
        --output table \
        --region $AWS_REGION 2>/dev/null || echo "  Not available"
    
    # API Stack
    echo ""
    echo "API Stack:"
    aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Api \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
        --output table \
        --region $AWS_REGION 2>/dev/null || echo "  Not available"
    
    # Storage Stack
    echo ""
    echo "Storage Stack:"
    aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Storage \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
        --output table \
        --region $AWS_REGION 2>/dev/null || echo "  Not available"
    
    # Data Stack
    echo ""
    echo "Data Stack:"
    aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Data \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
        --output table \
        --region $AWS_REGION 2>/dev/null || echo "  Not available"
    
    echo ""
    echo "=========================================="
}

# Main deployment flow
main() {
    echo ""
    echo "=========================================="
    echo "Multi-Agent Orchestration System"
    echo "Automated Deployment Script"
    echo "=========================================="
    echo ""
    
    # Change to infrastructure directory
    cd "$(dirname "$0")/.."
    
    check_prerequisites
    load_environment
    install_dependencies
    bootstrap_cdk
    deploy_stacks
    
    log_info "Waiting 30 seconds for resources to stabilize..."
    sleep 30
    
    initialize_database
    initialize_opensearch
    create_test_user
    
    display_outputs
    
    echo ""
    log_success "Deployment complete!"
    echo ""
    log_info "Next steps:"
    echo "  1. Run seed data script: ./scripts/seed-data.sh"
    echo "  2. Run smoke tests: ./scripts/smoke-test.sh"
    echo "  3. Access API at the URL shown above"
    echo ""
}

# Run main function
main "$@"
