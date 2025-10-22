#!/usr/bin/env node
import 'source-map-support/register';
import * as dotenv from 'dotenv';
import * as path from 'path';
import * as cdk from 'aws-cdk-lib';
import { AuthStack } from '../lib/stacks/auth-stack';
import { ApiStack } from '../lib/stacks/api-stack';
import { DataStack } from '../lib/stacks/data-stack';
import { StorageStack } from '../lib/stacks/storage-stack';

// Load environment variables from .env file
dotenv.config({ path: path.join(__dirname, '../.env') });

const app = new cdk.App();

// Get environment configuration
const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT || process.env.AWS_ACCOUNT_ID,
  region: process.env.CDK_DEFAULT_REGION || process.env.AWS_REGION || 'us-east-1',
};

const projectName = 'MultiAgentOrchestration';
const stage = process.env.STAGE || 'dev';

// Stack naming convention
const stackPrefix = `${projectName}-${stage}`;

// Authentication Stack
const authStack = new AuthStack(app, `${stackPrefix}-Auth`, {
  env,
  description: 'Authentication and authorization infrastructure with Cognito',
  stackName: `${stackPrefix}-Auth`,
});

// Storage Stack (S3 buckets)
const storageStack = new StorageStack(app, `${stackPrefix}-Storage`, {
  env,
  description: 'S3 buckets for image evidence storage',
  stackName: `${stackPrefix}-Storage`,
});

// Data Stack (RDS, DynamoDB, OpenSearch)
const dataStack = new DataStack(app, `${stackPrefix}-Data`, {
  env,
  description: 'Data persistence layer with RDS, DynamoDB, and OpenSearch',
  stackName: `${stackPrefix}-Data`,
});

// API Stack (API Gateway with Lambda authorizer)
const apiStack = new ApiStack(app, `${stackPrefix}-Api`, {
  env,
  description: 'API Gateway with REST endpoints and Lambda authorizer',
  stackName: `${stackPrefix}-Api`,
  userPool: authStack.userPool,
  userPoolClient: authStack.userPoolClient,
  configurationsTable: dataStack.configurationsTable,
  configBackupBucket: storageStack.configBackupBucket,
  database: dataStack.database,
  databaseSecret: dataStack.databaseSecret,
  vpc: dataStack.vpc,
  sessionsTable: dataStack.sessionsTable,
  messagesTable: dataStack.messagesTable,
  queryJobsTable: dataStack.queryJobsTable,
  reportsTable: dataStack.reportsTable,
});

// Add dependencies
apiStack.addDependency(authStack);
apiStack.addDependency(dataStack);
apiStack.addDependency(storageStack);
dataStack.addDependency(storageStack);

// Add tags to all stacks
cdk.Tags.of(app).add('Project', projectName);
cdk.Tags.of(app).add('Stage', stage);
cdk.Tags.of(app).add('ManagedBy', 'CDK');
