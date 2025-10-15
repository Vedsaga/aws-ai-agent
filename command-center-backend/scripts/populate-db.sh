#!/bin/bash

# Database population script with validation and rollback capability
# Usage: ./scripts/populate-db.sh [--table-name TABLE_NAME] [--backup] [--rollback BACKUP_ID]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TABLE_NAME=""
CREATE_BACKUP=false
ROLLBACK_BACKUP_ID=""
BACKUP_DIR="./backups"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --table-name)
            TABLE_NAME="$2"
            shift 2
            ;;
        --backup)
            CREATE_BACKUP=true
            shift
            ;;
        --rollback)
            ROLLBACK_BACKUP_ID="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--table-name TABLE_NAME] [--backup] [--rollback BACKUP_ID]"
            echo ""
            echo "Options:"
            echo "  --table-name    DynamoDB table name (auto-detected if not provided)"
            echo "  --backup        Create backup before populating"
            echo "  --rollback      Rollback to specified backup ID"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}=== Database Population Script ===${NC}"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not configured or credentials are invalid${NC}"
    exit 1
fi

# Auto-detect table name if not provided
if [ -z "$TABLE_NAME" ]; then
    echo -e "${BLUE}Auto-detecting table name from CloudFormation stack...${NC}"
    STACK_NAME="CommandCenterBackendStack"
    TABLE_NAME=$(aws cloudformation describe-stacks \
        --stack-name ${STACK_NAME} \
        --query 'Stacks[0].Outputs[?OutputKey==`TableName`].OutputValue' \
        --output text 2>/dev/null)
    
    if [ -z "$TABLE_NAME" ]; then
        echo -e "${RED}Error: Could not auto-detect table name${NC}"
        echo "Please specify table name with --table-name option"
        exit 1
    fi
    echo -e "${GREEN}✓ Detected table: ${TABLE_NAME}${NC}"
else
    echo -e "Table: ${YELLOW}${TABLE_NAME}${NC}"
fi

export TABLE_NAME

# Handle rollback
if [ ! -z "$ROLLBACK_BACKUP_ID" ]; then
    echo ""
    echo -e "${YELLOW}=== Rollback Mode ===${NC}"
    echo -e "Backup ID: ${ROLLBACK_BACKUP_ID}"
    echo ""
    
    BACKUP_FILE="${BACKUP_DIR}/${ROLLBACK_BACKUP_ID}.json"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        echo -e "${RED}Error: Backup file not found: ${BACKUP_FILE}${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}Clearing current table data...${NC}"
    # Scan and delete all items
    aws dynamodb scan --table-name ${TABLE_NAME} --attributes-to-get Day Timestamp \
        --output json | jq -r '.Items[] | @json' | while read item; do
        DAY=$(echo $item | jq -r '.Day.S')
        TIMESTAMP=$(echo $item | jq -r '.Timestamp.S')
        aws dynamodb delete-item --table-name ${TABLE_NAME} \
            --key "{\"Day\":{\"S\":\"${DAY}\"},\"Timestamp\":{\"S\":\"${TIMESTAMP}\"}}" &> /dev/null
    done
    echo -e "${GREEN}✓ Table cleared${NC}"
    
    echo -e "${BLUE}Restoring from backup...${NC}"
    # Restore items from backup
    jq -c '.[]' "$BACKUP_FILE" | while read item; do
        aws dynamodb put-item --table-name ${TABLE_NAME} --item "$item" &> /dev/null
    done
    echo -e "${GREEN}✓ Backup restored${NC}"
    
    echo ""
    echo -e "${GREEN}=== Rollback Complete ===${NC}"
    exit 0
fi

# Create backup if requested
if [ "$CREATE_BACKUP" = true ]; then
    echo ""
    echo -e "${BLUE}Creating backup...${NC}"
    
    mkdir -p "$BACKUP_DIR"
    BACKUP_ID=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_ID}.json"
    
    # Scan and save all items
    aws dynamodb scan --table-name ${TABLE_NAME} --output json | jq '.Items' > "$BACKUP_FILE"
    
    ITEM_COUNT=$(jq 'length' "$BACKUP_FILE")
    echo -e "${GREEN}✓ Backup created: ${BACKUP_ID}${NC}"
    echo -e "  Items backed up: ${ITEM_COUNT}"
    echo -e "  File: ${BACKUP_FILE}"
fi

# Check if table is empty
echo ""
echo -e "${BLUE}Checking current table state...${NC}"
CURRENT_COUNT=$(aws dynamodb scan --table-name ${TABLE_NAME} --select COUNT --output json | jq -r '.Count')
echo -e "Current item count: ${CURRENT_COUNT}"

if [ "$CURRENT_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Table is not empty${NC}"
    read -p "Do you want to continue and add more data? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 0
    fi
fi

# Run population script
echo ""
echo -e "${BLUE}Running population script...${NC}"
echo ""

npm run build &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: TypeScript build failed${NC}"
    exit 1
fi

node dist/scripts/populate-database.js

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Population script failed${NC}"
    exit 1
fi

# Validation
echo ""
echo -e "${BLUE}Validating data insertion...${NC}"

# Count total items
FINAL_COUNT=$(aws dynamodb scan --table-name ${TABLE_NAME} --select COUNT --output json | jq -r '.Count')
INSERTED_COUNT=$((FINAL_COUNT - CURRENT_COUNT))

echo -e "Items before: ${CURRENT_COUNT}"
echo -e "Items after: ${FINAL_COUNT}"
echo -e "Items inserted: ${INSERTED_COUNT}"

if [ "$INSERTED_COUNT" -le 0 ]; then
    echo -e "${RED}✗ Validation failed: No items were inserted${NC}"
    exit 1
fi

# Validate data distribution across days
echo ""
echo -e "${BLUE}Validating data distribution...${NC}"
for day in {0..6}; do
    DAY_KEY="DAY_${day}"
    DAY_COUNT=$(aws dynamodb query --table-name ${TABLE_NAME} \
        --key-condition-expression "Day = :day" \
        --expression-attribute-values "{\":day\":{\"S\":\"${DAY_KEY}\"}}" \
        --select COUNT --output json | jq -r '.Count')
    echo -e "  ${DAY_KEY}: ${DAY_COUNT} items"
    
    if [ "$DAY_COUNT" -eq 0 ]; then
        echo -e "${YELLOW}  ⚠ Warning: No items found for ${DAY_KEY}${NC}"
    fi
done

# Validate domains
echo ""
echo -e "${BLUE}Validating domains...${NC}"
DOMAINS=("MEDICAL" "FIRE" "STRUCTURAL" "LOGISTICS" "COMMUNICATION")
for domain in "${DOMAINS[@]}"; do
    DOMAIN_COUNT=$(aws dynamodb scan --table-name ${TABLE_NAME} \
        --filter-expression "domain = :domain" \
        --expression-attribute-values "{\":domain\":{\"S\":\"${domain}\"}}" \
        --select COUNT --output json | jq -r '.Count')
    echo -e "  ${domain}: ${DOMAIN_COUNT} items"
done

# Sample a few items to verify structure
echo ""
echo -e "${BLUE}Sampling items to verify structure...${NC}"
SAMPLE=$(aws dynamodb scan --table-name ${TABLE_NAME} --limit 3 --output json | jq '.Items[0]')

REQUIRED_FIELDS=("Day" "Timestamp" "eventId" "domain" "severity" "geojson" "summary")
ALL_PRESENT=true

for field in "${REQUIRED_FIELDS[@]}"; do
    if echo "$SAMPLE" | jq -e ".${field}" > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ ${field}${NC}"
    else
        echo -e "${RED}  ✗ ${field} missing${NC}"
        ALL_PRESENT=false
    fi
done

if [ "$ALL_PRESENT" = false ]; then
    echo -e "${RED}✗ Validation failed: Required fields missing${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== Validation Complete ===${NC}"
echo -e "${GREEN}✓ All checks passed${NC}"
echo ""
echo -e "${YELLOW}Database is ready for use!${NC}"

if [ "$CREATE_BACKUP" = true ]; then
    echo ""
    echo -e "To rollback to this state, run:"
    echo -e "  ./scripts/populate-db.sh --rollback ${BACKUP_ID}"
fi
