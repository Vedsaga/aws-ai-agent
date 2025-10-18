#!/bin/bash

# Stop RDS to save costs when not using the system
# RDS will auto-start after 7 days

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

log_info "Stopping RDS instance: $DB_INSTANCE"

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

if [ "$STATUS" == "stopped" ]; then
    log_info "RDS instance is already stopped"
    exit 0
fi

if [ "$STATUS" != "available" ]; then
    log_error "RDS instance is in state: $STATUS (must be 'available' to stop)"
    exit 1
fi

# Stop the instance
aws rds stop-db-instance \
    --db-instance-identifier $DB_INSTANCE \
    --region $AWS_REGION > /dev/null

log_success "RDS instance is stopping..."
log_info "This will save approximately \$0.017/hour (\$0.41/day)"
log_info "Note: RDS will automatically start after 7 days"
log_info "To start it again, run: ./scripts/start-rds.sh"

