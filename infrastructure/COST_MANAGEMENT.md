# Cost Management Guide - 3 Week Demo Period

## Budget: $100 Credit
## Estimated Cost: $60-65 for 3 weeks
## Buffer: $35-40

## Daily Cost Breakdown

### Always Running (24/7)
- **OpenSearch t3.small**: $1.25/day ($26/3 weeks) ⚠️ Cannot be stopped
- **NAT Gateway**: $1.08/day ($23/3 weeks) ⚠️ Cannot be stopped
- **Other services**: $0.50/day ($10/3 weeks)
- **Subtotal**: $2.83/day

### Can Be Stopped
- **RDS t3.micro**: $0.41/day ($9/3 weeks) ✅ Can stop when not using

**Total if RDS always running**: $3.24/day = $68 for 3 weeks
**Total if RDS stopped 50% of time**: $2.83 + $0.20 = $3.03/day = $64 for 3 weeks

## Cost Saving Strategies

### 1. Stop RDS When Not Using (Recommended)

**Stop RDS overnight or when not demoing:**

```bash
cd infrastructure

# Stop RDS (saves $0.41/day)
./scripts/stop-rds.sh

# Start RDS before demo (takes 2-3 minutes)
./scripts/start-rds.sh
```

**Savings:**
- Stop 12 hours/day: Save $0.20/day = $4.20 over 3 weeks
- Stop 18 hours/day: Save $0.31/day = $6.50 over 3 weeks

**Note:** RDS auto-starts after 7 days of being stopped

### 2. Monitor Costs Daily

**Check current month costs:**

```bash
# Get current month costs
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=SERVICE

# Get total so far this month
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost
```

### 3. Set Up Billing Alerts

**Create alert when costs exceed $80:**

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name demo-cost-alert-80 \
  --alarm-description "Alert when demo costs exceed $80" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=Currency,Value=USD
```

**Create alert when costs exceed $95:**

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name demo-cost-alert-95 \
  --alarm-description "URGENT: Demo costs exceed $95" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 95 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=Currency,Value=USD
```

### 4. Delete Resources After Demo

**IMPORTANT: Delete everything when done to stop all charges:**

```bash
cd infrastructure
npm run destroy
```

**Verify deletion:**

```bash
# Check for remaining stacks
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[?contains(StackName, `MultiAgentOrchestration`)].StackName'

# Check for RDS instances
aws rds describe-db-instances \
  --query 'DBInstances[?contains(DBInstanceIdentifier, `MultiAgentOrchestration`)].DBInstanceIdentifier'

# Check for OpenSearch domains
aws opensearch list-domain-names \
  --query 'DomainNames[?contains(DomainName, `maos`)].DomainName'
```

## Cost Tracking Schedule

### Week 1 (Days 1-7)
- **Day 1**: Deploy infrastructure
- **Day 2**: Development and testing
- **Days 3-7**: Stop RDS overnight
- **Expected cost**: $20-22

### Week 2 (Days 8-14)
- **Days 8-14**: Testing period, stop RDS when not testing
- **Expected cost**: $20-22

### Week 3 (Days 15-21)
- **Days 15-21**: Final testing and demo preparation
- **Keep RDS running during demo days**
- **Expected cost**: $20-22

### After Week 3
- **Immediately destroy all resources**
- **Verify no resources remain**

## What Costs What

### Fixed Costs (Cannot Reduce)
| Service | Cost/Hour | Cost/Day | Cost/3 Weeks |
|---------|-----------|----------|--------------|
| OpenSearch t3.small | $0.052 | $1.25 | $26.21 |
| NAT Gateway | $0.045 | $1.08 | $22.68 |
| **Subtotal** | **$0.097** | **$2.33** | **$48.89** |

### Variable Costs (Can Control)
| Service | Cost/Hour | Cost/Day | Cost/3 Weeks (if always on) |
|---------|-----------|----------|----------------------------|
| RDS t3.micro | $0.017 | $0.41 | $8.57 |
| DynamoDB | On-demand | ~$0.10 | ~$2 |
| Lambda | On-demand | ~$0.05 | ~$1 |
| S3 | Storage | ~$0.05 | ~$1 |
| Bedrock/AI | Usage | ~$0.20 | ~$5 |
| **Subtotal** | | **~$0.81** | **~$17.57** |

### Total
- **Fixed**: $48.89 (cannot reduce)
- **Variable**: $17.57 (can reduce by stopping RDS)
- **Total**: $66.46 for 3 weeks

## Emergency Cost Reduction

If costs are approaching $100:

1. **Stop RDS immediately**: `./scripts/stop-rds.sh`
2. **Reduce Bedrock usage**: Limit AI calls during testing
3. **Delete test data**: Clean up S3 and DynamoDB
4. **Consider destroying and redeploying**: If you have several days without demos

## Cost Optimization Tips

### During Development (Days 1-2)
- Stop RDS overnight: **Save $0.82**
- Limit Bedrock calls: **Save $2-3**

### During Testing (Days 3-14)
- Stop RDS when not testing (16 hours/day): **Save $4.08**
- Use cached data instead of re-running pipelines: **Save $1-2**

### During Demo Period (Days 15-21)
- Keep RDS running during demo days
- Stop RDS overnight: **Save $2.87**

**Total Potential Savings: $10-15**
**Final Cost: $50-55 instead of $65**

## Monitoring Commands

### Check Current Costs
```bash
# Today's costs
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-%d),End=$(date -d tomorrow +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost

# This week's costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -d "7 days ago" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost
```

### Check Resource Status
```bash
# RDS status
aws rds describe-db-instances \
  --db-instance-identifier MultiAgentOrchestration-demo-Data-PostgreSQL \
  --query 'DBInstances[0].DBInstanceStatus'

# OpenSearch status
aws opensearch describe-domain \
  --domain-name maos-demo-search \
  --query 'DomainStatus.Processing'
```

## Questions?

- **Why can't I stop OpenSearch?** AWS doesn't support stopping OpenSearch domains, only deleting them
- **Why can't I stop NAT Gateway?** NAT Gateways are always-on resources, but you need them for Lambda to access internet
- **Can I use smaller instances?** t3.micro (RDS) and t3.small (OpenSearch) are already the minimum
- **What if I go over budget?** Destroy resources immediately with `npm run destroy`

## Summary

✅ **Budget**: $100  
✅ **Estimated Cost**: $50-65 (with RDS stop/start)  
✅ **Buffer**: $35-50  
✅ **Strategy**: Stop RDS when not using, monitor daily, destroy after demo  
✅ **Savings**: $10-15 by stopping RDS strategically  

**You're well within budget!** 🎉
