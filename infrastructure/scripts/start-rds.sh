#!/bin/bash

# Start RDS instance for use
# Takes 2-3 minutes to become available

set -e

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
if [ ! -f .env ]; then
    log_error ".env file not found"
    exit 1
fi

export $(grep -v '^#' .env | xargs)
export AWS_REGION=${AWS_REGION:-us-east-1}
export STAGE=${STAGE:-demo}

# Get DB instance identifier
DB_INSTANCE="MultiAgentOrchestration-${STAGE}-Data-PostgreSQL"

log_info "Starting RDS instance: $DB_INSTANCE"

# Check current status
STATUS=$(aws rds describe-db-instances \
    --db-instance-identifier $DB_INSTANCE \
    --region $AWS_REGION \
    --query 'DBInstances[0].DBInstanceStatus' \
    --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$STATUS" == "NOT_FOUND" ]; then
    log_error "RDS instance not found: $DB_INSTANCE"
    exit 1
fi

if [ "$STATUS" == "available" ]; then
    log_success "RDS instance is already running"
    exit 0
fi

if [ "$STATUS" != "stopped" ]; then
    log_info "RDS instance is in state: $STATUS"
    if [ "$STATUS" == "starting" ]; then
        log_info "Instance is already starting, please wait..."
        exit 0
    fi
    log_error "Cannot start instance in state: $STATUS"
    exit 1
fi

# Start the instance
aws rds start-db-instance \
    --db-instance-identifier $DB_INSTANCE \
    --region $AWS_REGION > /dev/null

log_success "RDS instance is starting..."
log_info "This will take 2-3 minutes to become available"
log_info "You can check status with: aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE --query 'DBInstances[0].DBInstanceStatus'"

# Wait for it to become available
log_info "Waiting for RDS to become available..."
aws rds wait db-instance-available \
    --db-instance-identifier $DB_INSTANCE \
    --region $AWS_REGION

log_success "RDS instance is now available!"
log_info "You can now use the system"

