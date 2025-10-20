#!/bin/bash

# AWS Service Monitoring Script
# Continuously checks if AWS services have recovered from outage

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

REGION="us-east-1"
CHECK_INTERVAL=60  # Check every 60 seconds
MAX_CHECKS=360     # Run for up to 6 hours

clear
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BOLD}AWS Service Recovery Monitor${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${CYAN}Monitoring AWS services for recovery...${NC}"
echo -e "${CYAN}Press Ctrl+C to stop monitoring${NC}"
echo ""
echo "Services being monitored:"
echo "  • AWS STS (baseline)"
echo "  • AWS Lambda API"
echo "  • Amazon Cognito"
echo "  • AWS CloudFormation"
echo ""
echo "Check interval: ${CHECK_INTERVAL}s"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

check_count=0
consecutive_successes=0

while [ $check_count -lt $MAX_CHECKS ]; do
    check_count=$((check_count + 1))
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo -e "${BLUE}[Check #$check_count at $timestamp]${NC}"

    # Initialize status flags
    sts_ok=false
    lambda_ok=false
    cognito_ok=false
    cfn_ok=false

    # Test 1: AWS STS (baseline check)
    echo -n "  Testing AWS STS... "
    if aws sts get-caller-identity --region $REGION &>/dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
        sts_ok=true
    else
        echo -e "${RED}✗ FAIL${NC}"
    fi

    # Test 2: AWS Lambda API
    echo -n "  Testing Lambda API... "
    if aws lambda list-functions --region $REGION --max-items 1 &>/dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
        lambda_ok=true
    else
        echo -e "${RED}✗ FAIL${NC}"
    fi

    # Test 3: Amazon Cognito
    echo -n "  Testing Cognito... "
    if aws cognito-idp describe-user-pool --user-pool-id us-east-1_7QZ7Y6Gbl --region $REGION &>/dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
        cognito_ok=true
    else
        echo -e "${RED}✗ FAIL${NC}"
    fi

    # Test 4: CloudFormation
    echo -n "  Testing CloudFormation... "
    if aws cloudformation list-stacks --region $REGION --max-items 1 &>/dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
        cfn_ok=true
    else
        echo -e "${RED}✗ FAIL${NC}"
    fi

    # Check if all services are healthy
    if $sts_ok && $lambda_ok && $cognito_ok && $cfn_ok; then
        consecutive_successes=$((consecutive_successes + 1))
        echo ""
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}${BOLD}✓✓✓ ALL AWS SERVICES ARE BACK ONLINE! ✓✓✓${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""

        if [ $consecutive_successes -ge 2 ]; then
            echo -e "${CYAN}Services have been stable for 2+ checks.${NC}"
            echo ""
            echo -e "${MAGENTA}${BOLD}IMMEDIATE ACTIONS:${NC}"
            echo ""
            echo "1. Deploy fixed Lambda functions:"
            echo -e "   ${YELLOW}./deploy_all_fixes.sh${NC}"
            echo ""
            echo "2. Test APIs:"
            echo -e "   ${YELLOW}./run_tests.sh${NC}"
            echo ""
            echo "3. Record demo video (see EXECUTION_GUIDE.md Hour 3)"
            echo ""
            echo "4. Submit to DevPost (see EXECUTION_GUIDE.md Hour 5)"
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""

            # Play system bell if available
            echo -e "\a\a\a"

            exit 0
        else
            echo -e "${YELLOW}Services recovered! Verifying stability...${NC}"
            echo ""
        fi
    else
        consecutive_successes=0
        echo ""
        echo -e "${YELLOW}AWS services still experiencing issues...${NC}"
        echo ""
    fi

    # Wait before next check
    if [ $check_count -lt $MAX_CHECKS ]; then
        remaining=$((MAX_CHECKS - check_count))
        echo -e "${CYAN}Next check in ${CHECK_INTERVAL}s (${remaining} checks remaining)...${NC}"
        echo ""
        sleep $CHECK_INTERVAL
    fi
done

echo ""
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${RED}Maximum monitoring duration reached${NC}"
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "AWS services did not recover within monitoring period."
echo ""
echo "Options:"
echo "1. Continue monitoring: ./monitor_aws.sh"
echo "2. Proceed with Plan B (documentation-first submission)"
echo "3. Check AWS Service Health: https://status.aws.amazon.com/"
echo ""

exit 1
