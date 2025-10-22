import * as cdk from 'aws-cdk-lib';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
// import * as opensearch from 'aws-cdk-lib/aws-opensearchservice'; // Removed for demo
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';
import * as path from 'path';

export class DataStack extends cdk.Stack {
  public readonly database: rds.DatabaseInstance;
  public readonly databaseSecret: secretsmanager.ISecret;
  public readonly vpc: ec2.Vpc;
  public readonly configurationsTable: dynamodb.Table;
  public readonly userSessionsTable: dynamodb.Table;
  public readonly toolCatalogTable: dynamodb.Table;
  public readonly toolPermissionsTable: dynamodb.Table;
  public readonly reportsTable: dynamodb.Table;
  public readonly sessionsTable: dynamodb.Table;
  public readonly messagesTable: dynamodb.Table;
  public readonly queryJobsTable: dynamodb.Table;
  // OpenSearch removed for demo - not critical for agent configuration features
  // public readonly openSearchDomain: opensearch.Domain;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create simplified VPC for demo (no NAT Gateway, but with VPC Endpoints)
    // Using public subnets for RDS to avoid OpenSearch VPC issues
    this.vpc = new ec2.Vpc(this, 'Vpc', {
      vpcName: `${id}-Vpc`,
      maxAzs: 2,
      natGateways: 0,  // COST OPTIMIZATION: No NAT Gateway
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: 'Public',
          subnetType: ec2.SubnetType.PUBLIC,
        },
      ],
    });

    // Add VPC Endpoints for AWS services (Lambda in VPC needs these to access AWS APIs)
    this.vpc.addInterfaceEndpoint('SecretsManagerEndpoint', {
      service: ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
    });

    // Create database credentials secret
    const dbUsername = process.env.DB_USERNAME;
    if (!dbUsername) {
      throw new Error('DB_USERNAME environment variable is required for database setup');
    }
    this.databaseSecret = new secretsmanager.Secret(this, 'DatabaseSecret', {
      secretName: `${id}-DatabaseCredentials`,
      generateSecretString: {
        secretStringTemplate: JSON.stringify({ username: dbUsername }),
        generateStringKey: 'password',
        excludePunctuation: true,
        includeSpace: false,
        passwordLength: 32,
      },
    });

    // COST OPTIMIZATION: Use Aurora Serverless v2 instead of RDS
    // Scales down to 0.5 ACU when idle (~$0.06/hr vs $0.017/hr but auto-scales)
    const cluster = new rds.DatabaseCluster(this, 'Database', {
      engine: rds.DatabaseClusterEngine.auroraPostgres({
        version: rds.AuroraPostgresEngineVersion.VER_15_4,
      }),
      credentials: rds.Credentials.fromSecret(this.databaseSecret),
      defaultDatabaseName: 'multi_agent_orchestration',
      vpc: this.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PUBLIC,  // Changed to PUBLIC for simplified demo
      },
      serverlessV2MinCapacity: 0.5,  // Minimum ACU (cost optimized)
      serverlessV2MaxCapacity: 2,    // Maximum ACU for demo
      writer: rds.ClusterInstance.serverlessV2('writer'),
      backup: {
        retention: cdk.Duration.days(1),  // Minimal backups
      },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      deletionProtection: false,
      storageEncrypted: true,
    });

    // Expose as database property for compatibility
    this.database = cluster as any;
    
    // Allow connections from within the VPC
    cluster.connections.allowFrom(
      ec2.Peer.ipv4(this.vpc.vpcCidrBlock),
      ec2.Port.tcp(5432),
      'Allow PostgreSQL access from within VPC'
    );

    // Create Lambda function to initialize database schema
    // Create psycopg2 Lambda layer
    const psycopg2Layer = new lambda.LayerVersion(this, 'Psycopg2Layer', {
      code: lambda.Code.fromAsset(path.join(__dirname, '../../layers/psycopg2')),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_11],
      description: 'psycopg2-binary for PostgreSQL connectivity',
    });

    const dbInitFunction = new lambda.Function(this, 'DbInitFunction', {
      functionName: `${id}-DbInit`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'db_init.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/db-init')),
      layers: [psycopg2Layer],
      timeout: cdk.Duration.minutes(10),
      memorySize: 512,
      vpc: this.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PUBLIC,  // Changed to PUBLIC for simplified demo
      },
      allowPublicSubnet: true,  // Required for Lambda in public subnet
      environment: {
        DB_SECRET_ARN: this.databaseSecret.secretArn,
        DB_HOST: (this.database as any).clusterEndpoint.hostname,
        DB_PORT: '5432',
        DB_NAME: 'multi_agent_orchestration',
      },
      description: 'Initializes database schema with tables and indexes',
    });

    // Grant database access to init function
    this.database.connections.allowFrom(dbInitFunction, ec2.Port.tcp(5432));
    this.databaseSecret.grantRead(dbInitFunction);

    // Create verification Lambda function
    const dbVerifyFunction = new lambda.Function(this, 'DbVerifyFunction', {
      functionName: `${id}-DbVerify`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'verify_seed.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/db-init')),
      layers: [psycopg2Layer],
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      vpc: this.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PUBLIC,
      },
      allowPublicSubnet: true,
      environment: {
        DB_SECRET_ARN: this.databaseSecret.secretArn,
        DB_HOST: (this.database as any).clusterEndpoint.hostname,
        DB_PORT: '5432',
        DB_NAME: 'multi_agent_orchestration',
      },
      description: 'Verifies database seeding by querying builtin agents and domains',
    });

    // Grant database access to verify function
    this.database.connections.allowFrom(dbVerifyFunction, ec2.Port.tcp(5432));
    this.databaseSecret.grantRead(dbVerifyFunction);

    // DynamoDB Tables

    // 1. Configurations Table
    this.configurationsTable = new dynamodb.Table(this, 'ConfigurationsTable', {
      tableName: `${id}-Configurations`,
      partitionKey: {
        name: 'tenant_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'config_key',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // GSI for config_type queries
    this.configurationsTable.addGlobalSecondaryIndex({
      indexName: 'config-type-index',
      partitionKey: {
        name: 'config_type',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'created_at',
        type: dynamodb.AttributeType.NUMBER,
      },
    });

    // 2. User Sessions Table
    this.userSessionsTable = new dynamodb.Table(this, 'UserSessionsTable', {
      tableName: `${id}-UserSessions`,
      partitionKey: {
        name: 'user_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'session_id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      timeToLiveAttribute: 'expires_at',
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // GSI for tenant_id queries
    this.userSessionsTable.addGlobalSecondaryIndex({
      indexName: 'tenant-id-index',
      partitionKey: {
        name: 'tenant_id',
        type: dynamodb.AttributeType.STRING,
      },
    });

    // 3. Tool Catalog Table
    this.toolCatalogTable = new dynamodb.Table(this, 'ToolCatalogTable', {
      tableName: `${id}-ToolCatalog`,
      partitionKey: {
        name: 'tool_name',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // 4. Tool Permissions Table
    this.toolPermissionsTable = new dynamodb.Table(this, 'ToolPermissionsTable', {
      tableName: `${id}-ToolPermissions`,
      partitionKey: {
        name: 'tenant_agent_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'tool_name',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // 5. Reports Table - Core data documents for ingestion and management
    this.reportsTable = new dynamodb.Table(this, 'ReportsTable', {
      tableName: `${id}-Reports`,
      partitionKey: {
        name: 'incident_id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // GSI for tenant-domain queries
    this.reportsTable.addGlobalSecondaryIndex({
      indexName: 'tenant-domain-index',
      partitionKey: {
        name: 'tenant_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'domain_id',
        type: dynamodb.AttributeType.STRING,
      },
    });

    // GSI for domain-created queries
    this.reportsTable.addGlobalSecondaryIndex({
      indexName: 'domain-created-index',
      partitionKey: {
        name: 'domain_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'created_at',
        type: dynamodb.AttributeType.STRING,
      },
    });

    // 6. Sessions Table - Chat conversation contexts
    this.sessionsTable = new dynamodb.Table(this, 'SessionsTable', {
      tableName: `${id}-Sessions`,
      partitionKey: {
        name: 'session_id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // GSI for user-activity queries
    this.sessionsTable.addGlobalSecondaryIndex({
      indexName: 'user-activity-index',
      partitionKey: {
        name: 'user_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'last_activity',
        type: dynamodb.AttributeType.STRING,
      },
    });

    // 7. Messages Table - Chat messages with grounding references
    this.messagesTable = new dynamodb.Table(this, 'MessagesTable', {
      tableName: `${id}-Messages`,
      partitionKey: {
        name: 'message_id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // GSI for session-timestamp queries
    this.messagesTable.addGlobalSecondaryIndex({
      indexName: 'session-timestamp-index',
      partitionKey: {
        name: 'session_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'timestamp',
        type: dynamodb.AttributeType.STRING,
      },
    });

    // 8. QueryJobs Table - Query execution tracking with results
    this.queryJobsTable = new dynamodb.Table(this, 'QueryJobsTable', {
      tableName: `${id}-QueryJobs`,
      partitionKey: {
        name: 'query_id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // GSI for session-created queries
    this.queryJobsTable.addGlobalSecondaryIndex({
      indexName: 'session-created-index',
      partitionKey: {
        name: 'session_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'created_at',
        type: dynamodb.AttributeType.STRING,
      },
    });

    // OpenSearch removed for demo - not critical for agent configuration features
    // Saves ~$36/month and avoids VPC complexity
    // Vector search functionality can be added later if needed

    // Outputs
    new cdk.CfnOutput(this, 'DatabaseEndpoint', {
      value: (this.database as any).clusterEndpoint.hostname,
      description: 'Aurora Serverless v2 Cluster Endpoint',
      exportName: `${id}-DatabaseEndpoint`,
    });

    new cdk.CfnOutput(this, 'DatabaseSecretArn', {
      value: this.databaseSecret.secretArn,
      description: 'Database Credentials Secret ARN',
      exportName: `${id}-DatabaseSecretArn`,
    });

    new cdk.CfnOutput(this, 'ConfigurationsTableName', {
      value: this.configurationsTable.tableName,
      description: 'Configurations DynamoDB Table Name',
      exportName: `${id}-ConfigurationsTableName`,
    });

    new cdk.CfnOutput(this, 'ReportsTableName', {
      value: this.reportsTable.tableName,
      description: 'Reports DynamoDB Table Name',
      exportName: `${id}-ReportsTableName`,
    });

    new cdk.CfnOutput(this, 'SessionsTableName', {
      value: this.sessionsTable.tableName,
      description: 'Sessions DynamoDB Table Name',
      exportName: `${id}-SessionsTableName`,
    });

    new cdk.CfnOutput(this, 'MessagesTableName', {
      value: this.messagesTable.tableName,
      description: 'Messages DynamoDB Table Name',
      exportName: `${id}-MessagesTableName`,
    });

    new cdk.CfnOutput(this, 'QueryJobsTableName', {
      value: this.queryJobsTable.tableName,
      description: 'QueryJobs DynamoDB Table Name',
      exportName: `${id}-QueryJobsTableName`,
    });

    // OpenSearch output removed - not deployed in demo version
    new cdk.CfnOutput(this, 'OpenSearchEndpoint', {
      value: 'not-deployed-in-demo',
      description: 'OpenSearch Domain Endpoint',
      exportName: `${id}-OpenSearchEndpoint`,
    });

    // Store configuration in SSM Parameter Store
    new cdk.aws_ssm.StringParameter(this, 'DatabaseEndpointParameter', {
      parameterName: '/app/database/endpoint',
      stringValue: (this.database as any).clusterEndpoint.hostname,
      description: 'Aurora Serverless v2 Cluster Endpoint',
    });

    new cdk.aws_ssm.StringParameter(this, 'DatabaseSecretArnParameter', {
      parameterName: '/app/database/secret-arn',
      stringValue: this.databaseSecret.secretArn,
      description: 'Database Credentials Secret ARN',
    });

    // OpenSearch SSM parameter removed - not deployed in demo version
    new cdk.aws_ssm.StringParameter(this, 'OpenSearchEndpointParameter', {
      parameterName: '/app/opensearch/endpoint',
      stringValue: 'not-deployed-in-demo',
      description: 'OpenSearch Domain Endpoint (not deployed in demo)',
    });
  }
}
