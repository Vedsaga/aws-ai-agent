# Demo/Hackathon Cost-Optimized Deployment

## Configuration

This deployment is optimized for **demo/hackathon use** with 1-2 users for a couple of months.

### Cost Optimizations Applied

1. **RDS PostgreSQL**
   - Instance: `db.t3.micro` (smallest available)
   - Single-AZ (no Multi-AZ redundancy)
   - Storage: 20GB (minimal)
   - No Performance Insights
   - Minimal logging
   - 1-day backup retention

2. **OpenSearch**
   - Instance: `t3.small.search` (smallest practical)
   - Single node (no cluster)
   - Storage: 10GB EBS
   - No logging
   - Single-AZ

3. **DynamoDB**
   - On-demand pricing (pay per request)
   - No reserved capacity

4. **Lambda**
   - Pay per invocation
   - No provisioned concurrency

5. **S3**
   - Standard storage
   - Minimal data expected

6. **API Gateway**
   - Pay per request

7. **Cognito**
   - Free tier (up to 50,000 MAU)

## Estimated Monthly Costs (us-east-1)

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| **RDS PostgreSQL** | t3.micro, Single-AZ, 20GB | **$15-20** |
| **OpenSearch** | 1x t3.small, 10GB EBS | **$35-40** |
| **DynamoDB** | On-demand, <1GB, <100K requests | **$1-3** |
| **S3** | <5GB storage, <1000 requests | **$0.50** |
| **Lambda** | <100K invocations, 512MB avg | **$1-2** |
| **API Gateway** | <10K requests | **$0.50** |
| **Cognito** | <50 users | **Free** |
| **CloudWatch** | Basic logs | **$2-3** |
| **VPC** | NAT Gateway (1) | **$32** |
| **Data Transfer** | <1GB out | **$0.50** |
| **Step Functions** | <1000 executions | **$0.50** |
| **AppSync** | <10K requests | **$0.50** |
| | |
| **TOTAL** | | **~$90-105/month** |

## Cost for 2 Months Demo Period

**Estimated Total: $180-210**

## Additional Cost Savings Tips

### During Demo Period

1. **Stop when not in use** (if possible):
   - RDS can be stopped for up to 7 days (saves ~$15/month when stopped)
   - Note: OpenSearch cannot be stopped, only deleted

2. **Delete after demo**:
   - Run `npm run destroy` to delete all resources
   - Verify deletion in AWS Console

3. **Monitor costs**:
   ```bash
   # Check current month costs
   aws ce get-cost-and-usage \
     --time-period Start=2024-10-01,End=2024-10-31 \
     --granularity MONTHLY \
     --metrics BlendedCost
   ```

### What's NOT Included

These costs do NOT include:
- **Amazon Bedrock** usage (Claude 3 Sonnet):
  - Input: $0.003 per 1K tokens
  - Output: $0.015 per 1K tokens
  - Estimate: $5-10 for demo period with light usage

- **AWS Comprehend** usage:
  - $0.0001 per unit (100 characters)
  - Estimate: $1-2 for demo period

- **Amazon Location Service**:
  - Geocoding: $0.50 per 1,000 requests
  - Estimate: <$1 for demo period

**Total with AI services: $195-225 for 2 months**

## Comparison: Demo vs Production

| Component | Demo Config | Production Config | Savings |
|-----------|-------------|-------------------|---------|
| RDS | t3.micro, Single-AZ | t3.large, Multi-AZ | ~$230/mo |
| OpenSearch | 1x t3.small | 3x m5.large | ~$465/mo |
| NAT Gateway | 1 | 2 (HA) | ~$32/mo |
| Backups | 1 day | 30 days | ~$5/mo |
| Logging | Minimal | Full | ~$10/mo |
| **Total Savings** | | | **~$740/mo** |

## Deployment Command

```bash
cd infrastructure
npm run deploy:full
```

This will deploy with the cost-optimized settings from `.env` file.

## Cleanup After Demo

```bash
cd infrastructure
npm run destroy
```

**Important**: Verify all resources are deleted in AWS Console to avoid ongoing charges.

## Monitoring Costs

Set up a billing alarm:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name demo-cost-alert \
  --alarm-description "Alert when demo costs exceed $150" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 150 \
  --comparison-operator GreaterThanThreshold
```

## Notes

- These are estimates based on minimal usage (1-2 users, few requests per day)
- Actual costs may vary based on usage patterns
- NAT Gateway is the largest fixed cost ($32/mo) - required for Lambda to access internet
- Consider using VPC endpoints to reduce NAT Gateway usage (adds complexity)
- For absolute minimal cost, consider serverless alternatives (Aurora Serverless v2, but has minimum capacity charges)

## Questions?

- Check AWS Cost Explorer for real-time costs
- Set up AWS Budgets for automatic alerts
- Review CloudWatch metrics to optimize resource usage
