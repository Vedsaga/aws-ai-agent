# Quick Deployment Guide

## One-Command Deployment

Deploy everything with a single command:

```bash
cd command-center-backend
./scripts/full-deploy.sh
```

That's it! The script will:
1. ✓ Verify AWS credentials
2. ✓ Check Bedrock model access
3. ✓ Bootstrap CDK (if needed)
4. ✓ Install dependencies
5. ✓ Build TypeScript
6. ✓ Deploy infrastructure to AWS
7. ✓ Retrieve API credentials
8. ✓ Populate database with simulation data

## What You Get

After deployment completes, you'll have:

- **API Endpoint**: REST API for the dashboard
- **API Key**: Authentication key (saved to `.env.local`)
- **DynamoDB Table**: Pre-populated with 7 days of simulation data
- **Bedrock Agent**: AI assistant for natural language queries
- **Lambda Functions**: 4 serverless functions handling requests

## Prerequisites

You already have:
- ✓ AWS CLI installed
- ✓ AWS credentials configured
- ✓ Node.js 18+

## Deployment Options

### Deploy to specific stage
```bash
./scripts/full-deploy.sh --stage prod
```

### Skip database population
```bash
./scripts/full-deploy.sh --skip-populate
```

### Populate database later
```bash
npm run populate-db
```

## Frontend Integration

After deployment, the script saves credentials to `.env.local`. Copy these values to your frontend:

```bash
# In command-center-backend/.env.local (auto-generated)
API_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

Update your frontend `.env.local`:
```bash
# In command-center-dashboard/.env.local
NEXT_PUBLIC_API_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
NEXT_PUBLIC_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Testing the Deployment

### Quick API test
```bash
# Get the values from .env.local
source .env.local

# Test updates endpoint
curl -X GET "${API_ENDPOINT}/data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: ${API_KEY}"

# Test query endpoint
curl -X POST "${API_ENDPOINT}/agent/query" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text": "What are the most urgent needs?"}'
```

### Run integration tests
```bash
npm run test:integration
```

## Troubleshooting

### Bedrock Access Denied
If you see Bedrock access warnings:
1. Go to AWS Console → Bedrock → Model access
2. Request access to "Claude 3 Sonnet"
3. Wait for approval (usually instant)
4. Re-run deployment

### CDK Bootstrap Failed
```bash
# Manually bootstrap
cdk bootstrap aws://YOUR_ACCOUNT_ID/us-east-1
```

### Deployment Failed
```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name CommandCenterBackendStack \
  --max-items 10

# View detailed logs
cdk deploy --verbose
```

## Cleanup

Remove all resources:
```bash
cdk destroy
```

## Cost Monitoring

The deployment includes automatic cost monitoring:
- Budget alarm at $50 USD
- CloudWatch dashboard for metrics
- Email alerts (if configured)

## Support

- Full documentation: `DEPLOYMENT_GUIDE.md`
- API documentation: `API_DOCUMENTATION.md`
- CloudWatch logs: `aws logs tail /aws/lambda/queryHandlerLambda --follow`
