---
inclusion: always
---

# AWS Best Practices for Multi-Agent Orchestration System

## General Guidelines

- Always use AWS CDK for infrastructure (TypeScript)
- Follow AWS Well-Architected Framework principles
- Use serverless services for automatic scaling
- Implement proper error handling and retries
- Enable CloudWatch logging for all Lambda functions

## Lambda Functions

- Use Python 3.11 for all agent functions
- Set appropriate memory (512MB for agents, 256MB for APIs)
- Set timeouts: 5 min for agents, 30s for API handlers
- Use environment variables for configuration
- Implement structured logging (JSON format)
- Cache configurations in memory with TTL

## DynamoDB

- Always include tenant_id in partition key for isolation
- Use GSIs for query patterns
- Enable point-in-time recovery
- Use TTL for session data
- Batch operations when possible

## RDS PostgreSQL

- Use RDS Proxy for connection pooling
- Partition tables by tenant_id
- Create indexes on frequently queried columns
- Use prepared statements to prevent SQL injection
- Enable automated backups

## Security

- Never hardcode credentials - use Secrets Manager
- Use IAM roles for service-to-service auth
- Validate all user inputs
- Sanitize data before logging
- Enable encryption at rest for all data stores

## Cost Optimization

- Use provisioned concurrency only for critical functions
- Set appropriate Lambda reserved concurrency limits
- Use S3 lifecycle policies for old data
- Monitor and set CloudWatch alarms for cost anomalies

## Hackathon-Specific

- Focus on core functionality first
- Use AWS CDK constructs for faster development
- Leverage AWS Bedrock for LLM (no model training needed)
- Use managed services (RDS, OpenSearch) over self-hosted
- Document deployment steps clearly for reproducibility
