# Command Center Backend

AWS CDK infrastructure for the Command Center Backend API.

## Prerequisites

- Node.js 18+ and npm
- AWS CLI configured with appropriate credentials
- AWS CDK CLI installed globally: `npm install -g aws-cdk`

## Project Structure

```
command-center-backend/
├── bin/
│   └── app.ts              # CDK app entry point
├── lib/
│   └── command-center-backend-stack.ts  # Main stack definition
├── config/
│   └── environment.ts      # Environment configuration
├── lambda/                 # Lambda function code (to be added)
├── cdk.json               # CDK configuration
├── package.json           # Dependencies
└── tsconfig.json          # TypeScript configuration
```

## Environment Configuration

The stack supports three environments: `dev`, `staging`, and `prod`.

Set the environment using the `STAGE` environment variable:

```bash
export STAGE=dev  # or staging, or prod
```

Configure cost alert email (optional):

```bash
export COST_ALERT_EMAIL=your-email@example.com
```

## Installation

Install dependencies:

```bash
cd command-center-backend
npm install
```

## CDK Commands

### Bootstrap (first time only)

Bootstrap your AWS account for CDK:

```bash
cdk bootstrap
```

### Build

Compile TypeScript to JavaScript:

```bash
npm run build
```

### Synthesize CloudFormation Template

Generate CloudFormation template:

```bash
npm run synth
```

### Deploy

Deploy the stack to AWS:

```bash
# Deploy to dev (default)
npm run deploy

# Deploy to staging
STAGE=staging npm run deploy

# Deploy to prod
STAGE=prod npm run deploy
```

### Diff

Compare deployed stack with current state:

```bash
npm run diff
```

### Destroy

Remove the stack from AWS:

```bash
npm run destroy
```

## IAM Roles

The stack creates four IAM roles with least privilege:

1. **UpdatesLambdaRole** - DynamoDB read access for the updates endpoint
2. **QueryLambdaRole** - Bedrock Agent invoke access for natural language queries
3. **ActionLambdaRole** - Bedrock Agent invoke access for pre-defined actions
4. **ToolLambdaRole** - DynamoDB read access for the Bedrock Agent tool

## Cost Monitoring

The stack includes:

- CloudWatch alarm that triggers when estimated charges exceed $50
- SNS topic for cost alert notifications
- Email subscription to the configured alert email

## Outputs

After deployment, the stack outputs:

- `TableName` - DynamoDB table name
- `APIEndpoint` - API Gateway endpoint URL
- IAM role ARNs for all Lambda functions

## Next Steps

1. Implement Lambda functions (tasks 2-8)
2. Configure Bedrock Agent (task 6)
3. Set up API Gateway routes (task 9)
4. Add monitoring and logging (task 10)
5. Deploy and test (task 11)
