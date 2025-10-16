#!/bin/bash

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║              Fix 502 Errors - Automated Script            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Check database
echo "[1/6] Checking database..."
COUNT=$(aws dynamodb scan --table-name CommandCenterBackend-Dev-MasterEventTimeline --select COUNT --output json 2>/dev/null | jq -r '.Count // 0')
echo "Current items in database: $COUNT"

if [ "$COUNT" = "0" ]; then
    echo "❌ Database is empty!"
    echo ""
    echo "[2/6] Populating database..."
    npm run populate-db
    echo "✓ Database populated"
else
    echo "✓ Database has data"
    echo ""
    echo "[2/6] Skipping database population (already has data)"
fi
echo ""

# Step 3: Rebuild
echo "[3/6] Rebuilding TypeScript..."
npm run build
echo "✓ Build complete"
echo ""

# Step 4: Deploy
echo "[4/6] Deploying to AWS..."
cdk deploy --require-approval never
echo "✓ Deployment complete"
echo ""

# Step 5: Wait
echo "[5/6] Waiting 10 seconds for AWS to stabilize..."
sleep 10
echo "✓ Ready to test"
echo ""

# Step 6: Test
echo "[6/6] Testing APIs..."
echo ""
bash scripts/quick-test.sh

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Fix Complete                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "If tests still fail, check logs:"
echo "  aws logs tail /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler --follow"
