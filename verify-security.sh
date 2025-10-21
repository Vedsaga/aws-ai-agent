#!/bin/bash

################################################################################
# Security Verification Script
# Checks that all security improvements are properly applied
################################################################################

echo "========================================="
echo "Security Verification"
echo "========================================="
echo ""

ERRORS=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# Check 1: .env file exists
echo "Checking environment setup..."
if [ -f ".env" ]; then
    check_pass ".env file exists"
else
    check_fail ".env file not found - run ./setup-env.sh"
fi

# Check 2: .env is in .gitignore
if grep -q "^\.env$" .gitignore 2>/dev/null; then
    check_pass ".env is in .gitignore"
else
    check_fail ".env is not in .gitignore"
fi

# Check 3: config.js is in .gitignore
if grep -q "config\.js" .gitignore 2>/dev/null; then
    check_pass "config.js is in .gitignore"
else
    check_warn "config.js is not in .gitignore"
fi

echo ""
echo "Checking for hardcoded credentials..."

# Check 4: No hardcoded passwords in Python files
if grep -r "TestPassword123!" --include="*.py" --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv . 2>/dev/null | grep -v ".env" | grep -v "SECURITY" | grep -q .; then
    check_fail "Found hardcoded password in Python files"
else
    check_pass "No hardcoded passwords in Python files"
fi

# Check 5: No hardcoded passwords in shell scripts
if grep -r "TestPassword123!" --include="*.sh" --exclude-dir=node_modules --exclude-dir=.git . 2>/dev/null | grep -v ".env" | grep -v "SECURITY" | grep -v "setup-env.sh" | grep -q .; then
    check_fail "Found hardcoded password in shell scripts"
else
    check_pass "No hardcoded passwords in shell scripts"
fi

# Check 6: No hardcoded Cognito Client IDs in code (excluding docs and build artifacts)
if grep -r "6gobbpage9af3nd7ahm3lchkct" --include="*.py" --include="*.sh" --include="*.ts" --include="*.js" --include="*.html" --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv --exclude-dir=.next --exclude-dir=dist --exclude-dir=build . 2>/dev/null | grep -v ".env" | grep -v "SECURITY" | grep -v "setup-env.sh" | grep -v "config.example.js" | grep -q .; then
    check_fail "Found hardcoded Cognito Client ID in code"
else
    check_pass "No hardcoded Cognito Client IDs in code"
fi

# Check 7: No hardcoded API URLs in code (excluding docs and build artifacts)
if grep -r "vluqfpl2zi.execute-api" --include="*.py" --include="*.sh" --include="*.ts" --include="*.js" --include="*.html" --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv --exclude-dir=.next --exclude-dir=dist --exclude-dir=build . 2>/dev/null | grep -v ".env" | grep -v "SECURITY" | grep -v "setup-env.sh" | grep -v "config.example.js" | grep -q .; then
    check_fail "Found hardcoded API URL in code"
else
    check_pass "No hardcoded API URLs in code"
fi

echo ""
echo "Checking configuration files..."

# Check 8: Config directory exists
if [ -d "config" ]; then
    check_pass "config/ directory exists"
else
    check_fail "config/ directory not found"
fi

# Check 9: deployment.json exists
if [ -f "config/deployment.json" ]; then
    check_pass "config/deployment.json exists"
else
    check_fail "config/deployment.json not found"
fi

# Check 10: models.json exists
if [ -f "config/models.json" ]; then
    check_pass "config/models.json exists"
else
    check_fail "config/models.json not found"
fi

echo ""
echo "Checking code uses environment variables..."

# Check 11: TEST.py uses os.environ
if grep -q "os.environ.get" infrastructure/TEST.py 2>/dev/null; then
    check_pass "TEST.py uses environment variables"
else
    check_fail "TEST.py does not use environment variables"
fi

# Check 12: base_agent.py uses environment variables for model ID
if grep -q "os.environ.get.*BEDROCK" infrastructure/lambda/agents/base_agent.py 2>/dev/null; then
    check_pass "base_agent.py uses environment variables for model ID"
else
    check_fail "base_agent.py does not use environment variables for model ID"
fi

# Check 13: orchestrator_handler.py uses environment variables
if grep -q "os.environ.get.*BEDROCK" infrastructure/lambda/orchestration/orchestrator_handler.py 2>/dev/null; then
    check_pass "orchestrator_handler.py uses environment variables"
else
    check_fail "orchestrator_handler.py does not use environment variables"
fi

echo ""
echo "Checking scripts use config files..."

# Check 14: DEPLOY.sh reads config file
if grep -q "config/deployment.json" DEPLOY.sh 2>/dev/null; then
    check_pass "DEPLOY.sh reads from config file"
else
    check_fail "DEPLOY.sh does not read from config file"
fi

# Check 15: seed-dynamodb.py reads config
if grep -q "config/deployment.json\|os.environ.get" infrastructure/scripts/seed-dynamodb.py 2>/dev/null; then
    check_pass "seed-dynamodb.py uses config/environment"
else
    check_fail "seed-dynamodb.py does not use config/environment"
fi

echo ""
echo "========================================="
echo "Verification Summary"
echo "========================================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Your codebase is secure and properly configured."
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warning(s)${NC}"
    echo ""
    echo "No critical issues, but some warnings to address."
    exit 0
else
    echo -e "${RED}✗ $ERRORS error(s)${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS warning(s)${NC}"
    fi
    echo ""
    echo "Please fix the errors above before proceeding."
    echo "Run ./setup-env.sh to set up your environment."
    exit 1
fi
