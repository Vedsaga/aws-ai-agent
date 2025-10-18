#!/bin/bash

# Multi-Agent Orchestration System - Seed Data Script
# This script loads sample domains, agents, and configurations

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
    
    # Get API URL
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Api \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
        --output text \
        --region $AWS_REGION)
    
    # Get User Pool details
    USER_POOL_ID=$(aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Auth \
        --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
        --output text \
        --region $AWS_REGION)
    
    CLIENT_ID=$(aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Auth \
        --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
        --output text \
        --region $AWS_REGION)
    
    # Get DynamoDB table names
    CONFIG_TABLE=$(aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Data \
        --query 'Stacks[0].Outputs[?OutputKey==`ConfigurationsTableName`].OutputValue' \
        --output text \
        --region $AWS_REGION)
    
    if [ -z "$API_URL" ] || [ -z "$USER_POOL_ID" ] || [ -z "$CONFIG_TABLE" ]; then
        log_error "Failed to retrieve stack outputs. Ensure stacks are deployed."
        exit 1
    fi
    
    log_success "Stack outputs retrieved"
}

# Get JWT token
get_jwt_token() {
    log_info "Getting JWT token for testuser..."
    
    TOKEN=$(aws cognito-idp initiate-auth \
        --auth-flow USER_PASSWORD_AUTH \
        --client-id $CLIENT_ID \
        --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
        --region $AWS_REGION \
        --query 'AuthenticationResult.IdToken' \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$TOKEN" ]; then
        log_error "Failed to get JWT token. Ensure testuser exists with password TestPassword123!"
        exit 1
    fi
    
    log_success "JWT token obtained"
}

# Seed tool registry
seed_tools() {
    log_info "Seeding tool registry..."
    
    # Check if seed_tools.json exists
    if [ ! -f lambda/tool-registry/seed_tools.json ]; then
        log_error "seed_tools.json not found"
        return 1
    fi
    
    # Read and post each tool
    python3 << 'EOF'
import json
import boto3
import os

dynamodb = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION'])
table = dynamodb.Table('tool_catalog')

with open('lambda/tool-registry/seed_tools.json', 'r') as f:
    tools = json.load(f)

for tool in tools.get('tools', []):
    try:
        table.put_item(Item=tool)
        print(f"✓ Seeded tool: {tool['tool_name']}")
    except Exception as e:
        print(f"✗ Failed to seed tool {tool.get('tool_name', 'unknown')}: {e}")
EOF
    
    log_success "Tool registry seeded"
}

# Seed agent configurations
seed_agents() {
    log_info "Seeding agent configurations..."
    
    # Check if seed_configs.json exists
    if [ ! -f lambda/config-api/seed_configs.json ]; then
        log_error "seed_configs.json not found"
        return 1
    fi
    
    # Use the config API to seed agents
    python3 << EOF
import json
import requests
import os

api_url = os.environ['API_URL']
token = os.environ['TOKEN']
tenant_id = 'test-tenant-123'

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

with open('lambda/config-api/seed_configs.json', 'r') as f:
    seed_data = json.load(f)

# Seed agents
for agent in seed_data.get('agents', []):
    agent['tenant_id'] = tenant_id
    try:
        response = requests.post(
            f'{api_url}api/v1/config/agent',
            headers=headers,
            json=agent,
            timeout=10
        )
        if response.status_code in [200, 201]:
            print(f"✓ Seeded agent: {agent['agent_name']}")
        else:
            print(f"✗ Failed to seed agent {agent['agent_name']}: {response.status_code}")
    except Exception as e:
        print(f"✗ Failed to seed agent {agent.get('agent_name', 'unknown')}: {e}")

# Seed playbooks
for playbook in seed_data.get('playbooks', []):
    playbook['tenant_id'] = tenant_id
    try:
        response = requests.post(
            f'{api_url}api/v1/config/playbook',
            headers=headers,
            json=playbook,
            timeout=10
        )
        if response.status_code in [200, 201]:
            print(f"✓ Seeded playbook: {playbook['playbook_id']}")
        else:
            print(f"✗ Failed to seed playbook {playbook['playbook_id']}: {response.status_code}")
    except Exception as e:
        print(f"✗ Failed to seed playbook {playbook.get('playbook_id', 'unknown')}: {e}")

# Seed dependency graphs
for graph in seed_data.get('dependency_graphs', []):
    graph['tenant_id'] = tenant_id
    try:
        response = requests.post(
            f'{api_url}api/v1/config/dependency-graph',
            headers=headers,
            json=graph,
            timeout=10
        )
        if response.status_code in [200, 201]:
            print(f"✓ Seeded dependency graph: {graph['graph_id']}")
        else:
            print(f"✗ Failed to seed graph {graph['graph_id']}: {response.status_code}")
    except Exception as e:
        print(f"✗ Failed to seed graph {graph.get('graph_id', 'unknown')}: {e}")
EOF
    
    log_success "Agent configurations seeded"
}

# Seed sample data
seed_sample_data() {
    log_info "Seeding sample incident data..."
    
    # Create a few sample incidents
    python3 << EOF
import requests
import os

api_url = os.environ['API_URL']
token = os.environ['TOKEN']

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

sample_incidents = [
    {
        'domain_id': 'civic-complaints',
        'text': 'There is a large pothole on Main Street near the intersection with Oak Avenue. It has been there for two weeks and is causing damage to vehicles.',
        'images': []
    },
    {
        'domain_id': 'civic-complaints',
        'text': 'Streetlight is out on Elm Street between 5th and 6th Avenue. The area is very dark at night and feels unsafe.',
        'images': []
    },
    {
        'domain_id': 'civic-complaints',
        'text': 'Graffiti on the wall of the community center on Park Boulevard. It appeared yesterday and should be cleaned.',
        'images': []
    }
]

for i, incident in enumerate(sample_incidents, 1):
    try:
        response = requests.post(
            f'{api_url}api/v1/ingest',
            headers=headers,
            json=incident,
            timeout=30
        )
        if response.status_code in [200, 201, 202]:
            print(f"✓ Seeded sample incident {i}")
        else:
            print(f"✗ Failed to seed incident {i}: {response.status_code}")
    except Exception as e:
        print(f"✗ Failed to seed incident {i}: {e}")
EOF
    
    log_success "Sample data seeded"
}

# Main function
main() {
    echo ""
    echo "=========================================="
    echo "Multi-Agent Orchestration System"
    echo "Seed Data Script"
    echo "=========================================="
    echo ""
    
    # Change to infrastructure directory
    cd "$(dirname "$0")/.."
    
    load_environment
    get_stack_outputs
    get_jwt_token
    
    seed_tools
    seed_agents
    
    log_info "Waiting 10 seconds for configurations to propagate..."
    sleep 10
    
    seed_sample_data
    
    echo ""
    log_success "Seed data loaded successfully!"
    echo ""
    log_info "You can now:"
    echo "  1. Run smoke tests: ./scripts/smoke-test.sh"
    echo "  2. Query the API at: ${API_URL}"
    echo "  3. Test with username: testuser, password: TestPassword123!"
    echo ""
}

main "$@"
