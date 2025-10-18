#!/bin/bash

# Multi-Agent Orchestration System - Deployment Readiness Check
# This script verifies that the environment is ready for deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CHECKS_PASSED=0
CHECKS_FAILED=0

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((CHECKS_PASSED++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((CHECKS_FAILED++))
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check Node.js
check_nodejs() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -ge 18 ]; then
            log_success "Node.js $(node --version) installed"
        else
            log_error "Node.js version must be 18+. Current: $(node --version)"
        fi
    else
        log_error "Node.js not installed"
    fi
}

# Check Python
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        log_success "Python $(python3 --version) installed"
    else
        log_error "Python 3 not installed"
    fi
}

# Check AWS CLI
check_aws_cli() {
    if command -v aws &> /dev/null; then
        log_success "AWS CLI $(aws --version | cut -d' ' -f1) installed"
    else
        log_error "AWS CLI not installed"
    fi
}

# Check CDK CLI
check_cdk_cli() {
    if command -v cdk &> /dev/null; then
        log_success "AWS CDK $(cdk --version) installed"
    else
        log_error "AWS CDK CLI not installed. Run: npm install -g aws-cdk"
    fi
}

# Check AWS credentials
check_aws_credentials() {
    if aws sts get-caller-identity &> /dev/null; then
        ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
        USER=$(aws sts get-caller-identity --query Arn --output text | cut -d'/' -f2)
        log_success "AWS credentials configured (Account: $ACCOUNT, User: $USER)"
    else
        log_error "AWS credentials not configured. Run: aws configure"
    fi
}

# Check environment file
check_env_file() {
    if [ -f .env ]; then
        log_success ".env file exists"
        
        # Check required variables
        if grep -q "AWS_REGION" .env; then
            REGION=$(grep "AWS_REGION" .env | cut -d'=' -f2)
            log_info "  Region: $REGION"
        else
            log_warning "  AWS_REGION not set in .env"
        fi
        
        if grep -q "STAGE" .env; then
            STAGE=$(grep "STAGE" .env | cut -d'=' -f2)
            log_info "  Stage: $STAGE"
        else
            log_warning "  STAGE not set in .env (will default to 'dev')"
        fi
    else
        log_warning ".env file not found. Will be created from .env.example"
    fi
}

# Check dependencies installed
check_dependencies() {
    if [ -d node_modules ]; then
        log_success "Node.js dependencies installed"
    else
        log_warning "Node.js dependencies not installed. Run: npm install"
    fi
    
    if [ -f dist/bin/app.js ]; then
        log_success "TypeScript compiled"
    else
        log_warning "TypeScript not compiled. Run: npm run build"
    fi
}

# Check CDK bootstrap
check_cdk_bootstrap() {
    if aws sts get-caller-identity &> /dev/null; then
        REGION=${AWS_REGION:-us-east-1}
        ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
        
        if aws cloudformation describe-stacks \
            --stack-name CDKToolkit \
            --region $REGION &> /dev/null; then
            log_success "CDK bootstrapped in $REGION"
        else
            log_warning "CDK not bootstrapped in $REGION. Run: cdk bootstrap"
        fi
    fi
}

# Check service quotas
check_service_quotas() {
    log_info "Checking AWS service quotas..."
    
    # This is informational only
    log_info "  Ensure you have sufficient quotas for:"
    log_info "    - RDS instances (need 1)"
    log_info "    - OpenSearch domains (need 1)"
    log_info "    - Lambda concurrent executions (need 20+)"
    log_info "    - VPC resources (need 1 VPC, subnets, etc.)"
}

# Check scripts are executable
check_scripts() {
    SCRIPTS=("deploy.sh" "seed-data.sh" "smoke-test.sh" "check-readiness.sh")
    
    for script in "${SCRIPTS[@]}"; do
        if [ -x "scripts/$script" ]; then
            log_success "Script $script is executable"
        else
            log_warning "Script $script is not executable. Run: chmod +x scripts/$script"
        fi
    done
}

# Display summary
display_summary() {
    echo ""
    echo "=========================================="
    echo "READINESS CHECK SUMMARY"
    echo "=========================================="
    echo ""
    echo "Checks Passed: $CHECKS_PASSED"
    echo "Checks Failed: $CHECKS_FAILED"
    echo ""
    
    if [ $CHECKS_FAILED -eq 0 ]; then
        log_success "Environment is ready for deployment! ✓"
        echo ""
        log_info "To deploy, run:"
        echo "  npm run deploy:full"
        echo ""
        log_info "Or for manual deployment:"
        echo "  1. npm install"
        echo "  2. npm run build"
        echo "  3. cdk bootstrap (if not done)"
        echo "  4. npm run deploy"
        echo "  5. npm run seed-data"
        echo "  6. npm run smoke-test"
        echo ""
        return 0
    else
        log_error "Some checks failed. Please resolve issues above."
        echo ""
        log_info "Common fixes:"
        echo "  - Install missing software (Node.js, Python, AWS CLI, CDK)"
        echo "  - Configure AWS credentials: aws configure"
        echo "  - Install dependencies: npm install"
        echo "  - Bootstrap CDK: cdk bootstrap"
        echo ""
        return 1
    fi
}

# Main function
main() {
    echo ""
    echo "=========================================="
    echo "Multi-Agent Orchestration System"
    echo "Deployment Readiness Check"
    echo "=========================================="
    echo ""
    
    # Change to infrastructure directory
    cd "$(dirname "$0")/.."
    
    log_info "Checking prerequisites..."
    echo ""
    
    check_nodejs
    check_python
    check_aws_cli
    check_cdk_cli
    check_aws_credentials
    check_env_file
    check_dependencies
    check_cdk_bootstrap
    check_scripts
    
    echo ""
    check_service_quotas
    
    display_summary
}

main "$@"
