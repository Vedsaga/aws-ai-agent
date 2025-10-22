#!/bin/bash

# Seed Builtin Data Script
# Seeds builtin agents and sample domain into RDS database

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load environment
load_environment() {
    if [ ! -f .env ]; then
        log_error ".env file not found. Run deploy.sh first."
        exit 1
    fi
    
    export $(grep -v '^#' .env | xargs)
    export AWS_REGION=${AWS_REGION:-us-east-1}
    export STAGE=${STAGE:-dev}
}

# Get stack outputs
get_stack_outputs() {
    log_info "Retrieving stack outputs..."
    
    # Get RDS details from Data stack
    DB_SECRET_ARN=$(aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Data \
        --query 'Stacks[0].Outputs[?OutputKey==`DatabaseSecretArn`].OutputValue' \
        --output text \
        --region $AWS_REGION 2>/dev/null || echo "")
    
    DB_HOST=$(aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Data \
        --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
        --output text \
        --region $AWS_REGION 2>/dev/null || echo "")
    
    DB_PORT=$(aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Data \
        --query 'Stacks[0].Outputs[?OutputKey==`DatabasePort`].OutputValue' \
        --output text \
        --region $AWS_REGION 2>/dev/null || echo "5432")
    
    DB_NAME=$(aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Data \
        --query 'Stacks[0].Outputs[?OutputKey==`DatabaseName`].OutputValue' \
        --output text \
        --region $AWS_REGION 2>/dev/null || echo "multi_agent_orchestration")
    
    if [ -z "$DB_SECRET_ARN" ] || [ -z "$DB_HOST" ]; then
        log_error "Failed to retrieve database outputs. Ensure Storage stack is deployed."
        exit 1
    fi
    
    export DB_SECRET_ARN
    export DB_HOST
    export DB_PORT
    export DB_NAME
    
    log_success "Stack outputs retrieved"
    log_info "Database: $DB_HOST:$DB_PORT/$DB_NAME"
}

# Run seed script
run_seed_script() {
    log_info "Running seed script..."
    
    # Check if Python script exists
    if [ ! -f scripts/seed-builtin-data.py ]; then
        log_error "seed-builtin-data.py not found"
        exit 1
    fi
    
    # Make script executable
    chmod +x scripts/seed-builtin-data.py
    
    # Run Python script
    python3 scripts/seed-builtin-data.py
    
    if [ $? -eq 0 ]; then
        log_success "Seed script completed successfully"
    else
        log_error "Seed script failed"
        exit 1
    fi
}

# Main function
main() {
    echo ""
    echo "=========================================="
    echo "DomainFlow - Seed Builtin Data"
    echo "=========================================="
    echo ""
    
    # Change to infrastructure directory
    cd "$(dirname "$0")/.."
    
    load_environment
    get_stack_outputs
    run_seed_script
    
    echo ""
    log_success "Builtin data seeded successfully!"
    echo ""
    log_info "Seeded:"
    echo "  • 3 Ingestion agents (geo, temporal, entity)"
    echo "  • 6 Query agents (who, what, where, when, why, how)"
    echo "  • 3 Management agents (task_assigner, status_updater, task_details_editor)"
    echo "  • 1 Sample domain (civic_complaints)"
    echo ""
}

main "$@"
