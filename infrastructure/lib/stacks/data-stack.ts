import * as cdk from 'aws-cdk-lib';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as opensearch from 'aws-cdk-lib/aws-opensearchservice';
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
  public readonly openSearchDomain: opensearch.Domain;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create VPC for RDS and OpenSearch
    this.vpc = new ec2.Vpc(this, 'Vpc', {
      vpcName: `${id}-Vpc`,
      maxAzs: 2,
      natGateways: 1,
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: 'Public',
          subnetType: ec2.SubnetType.PUBLIC,
        },
        {
          cidrMask: 24,
          name: 'Private',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        },
        {
          cidrMask: 28,
          name: 'Isolated',
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
      ],
    });

    // Create database credentials secret
    this.databaseSecret = new secretsmanager.Secret(this, 'DatabaseSecret', {
      secretName: `${id}-DatabaseCredentials`,
      generateSecretString: {
        secretStringTemplate: JSON.stringify({ username: 'admin' }),
        generateStringKey: 'password',
        excludePunctuation: true,
        includeSpace: false,
        passwordLength: 32,
      },
    });

    // Create RDS PostgreSQL instance - Cost optimized for demo
    // Use environment variables for instance size configuration
    const dbInstanceClass = process.env.DB_INSTANCE_CLASS || 'db.t3.micro';
    const dbMultiAz = process.env.DB_MULTI_AZ === 'true';
    const dbAllocatedStorage = parseInt(process.env.DB_ALLOCATED_STORAGE || '20');
    
    this.database = new rds.DatabaseInstance(this, 'Database', {
      instanceIdentifier: `${id}-PostgreSQL`,
      engine: rds.DatabaseInstanceEngine.postgres({
        version: rds.PostgresEngineVersion.VER_15_4,
      }),
      instanceType: ec2.InstanceType.of(
        ec2.InstanceClass.T3,
        ec2.InstanceSize.MICRO  // Smallest instance for demo
      ),
      vpc: this.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
      },
      multiAz: dbMultiAz,  // Single-AZ for demo to save costs
      allocatedStorage: dbAllocatedStorage,  // Minimal storage
      maxAllocatedStorage: 100,  // Lower max
      storageType: rds.StorageType.GP3,
      storageEncrypted: true,
      credentials: rds.Credentials.fromSecret(this.databaseSecret),
      databaseName: 'multi_agent_orchestration',
      backupRetention: cdk.Duration.days(1),  // Minimal backups
      deleteAutomatedBackups: true,  // Clean up backups on delete
      removalPolicy: cdk.RemovalPolicy.DESTROY,  // Allow deletion for demo
      deletionProtection: false,  // Allow deletion for demo
      enablePerformanceInsights: false,  // Disable to save costs
      cloudwatchLogsExports: [],  // Minimal logging
      autoMinorVersionUpgrade: true,
    });

    // Create Lambda function to initialize database schema
    const dbInitFunction = new lambda.Function(this, 'DbInitFunction', {
      functionName: `${id}-DbInit`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'db_init.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/db-init')),
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      vpc: this.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      },
      environment: {
        DB_SECRET_ARN: this.databaseSecret.secretArn,
        DB_HOST: this.database.dbInstanceEndpointAddress,
        DB_PORT: this.database.dbInstanceEndpointPort,
        DB_NAME: 'multi_agent_orchestration',
      },
      description: 'Initializes database schema with tables and indexes',
    });

    // Grant database access to init function
    this.database.connections.allowFrom(dbInitFunction, ec2.Port.tcp(5432));
    this.databaseSecret.grantRead(dbInitFunction);

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

    // Create OpenSearch Domain for vector search - Cost optimized for demo
    const stage = process.env.STAGE || 'dev';
    const osInstanceType = process.env.OPENSEARCH_INSTANCE_TYPE || 't3.small.search';
    const osInstanceCount = parseInt(process.env.OPENSEARCH_INSTANCE_COUNT || '1');
    const osEbsVolumeSize = parseInt(process.env.OPENSEARCH_EBS_VOLUME_SIZE || '10');
    
    this.openSearchDomain = new opensearch.Domain(this, 'OpenSearchDomain', {
      domainName: `maos-${stage}-search`,
      version: opensearch.EngineVersion.OPENSEARCH_2_11,
      capacity: {
        dataNodes: osInstanceCount,  // Single node for demo
        dataNodeInstanceType: osInstanceType,  // Smallest instance
      },
      ebs: {
        volumeSize: osEbsVolumeSize,  // Minimal storage
        volumeType: ec2.EbsDeviceVolumeType.GP3,
      },
      zoneAwareness: {
        enabled: false,  // Single-AZ for demo
      },
      vpc: this.vpc,
      vpcSubnets: [{
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      }],
      encryptionAtRest: {
        enabled: true,
      },
      nodeToNodeEncryption: true,
      enforceHttps: true,
      logging: {
        slowSearchLogEnabled: false,  // Disable logging to save costs
        appLogEnabled: false,
        slowIndexLogEnabled: false,
      },
      removalPolicy: cdk.RemovalPolicy.DESTROY,  // Allow deletion for demo
    });

    // Create Lambda function to initialize OpenSearch index
    const osInitFunction = new lambda.Function(this, 'OpenSearchInitFunction', {
      functionName: `${id}-OpenSearchInit`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'opensearch_init.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/opensearch-init')),
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      vpc: this.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      },
      environment: {
        OPENSEARCH_ENDPOINT: this.openSearchDomain.domainEndpoint,
      },
      description: 'Initializes OpenSearch index with knn_vector mapping',
    });

    // Grant OpenSearch access to init function
    this.openSearchDomain.grantReadWrite(osInitFunction);
    this.openSearchDomain.connections.allowFrom(osInitFunction, ec2.Port.tcp(443));

    // Outputs
    new cdk.CfnOutput(this, 'DatabaseEndpoint', {
      value: this.database.dbInstanceEndpointAddress,
      description: 'RDS PostgreSQL Endpoint',
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

    new cdk.CfnOutput(this, 'OpenSearchEndpoint', {
      value: this.openSearchDomain.domainEndpoint,
      description: 'OpenSearch Domain Endpoint',
      exportName: `${id}-OpenSearchEndpoint`,
    });

    // Store configuration in SSM Parameter Store
    new cdk.aws_ssm.StringParameter(this, 'DatabaseEndpointParameter', {
      parameterName: '/app/database/endpoint',
      stringValue: this.database.dbInstanceEndpointAddress,
      description: 'RDS PostgreSQL Endpoint',
    });

    new cdk.aws_ssm.StringParameter(this, 'DatabaseSecretArnParameter', {
      parameterName: '/app/database/secret-arn',
      stringValue: this.databaseSecret.secretArn,
      description: 'Database Credentials Secret ARN',
    });

    new cdk.aws_ssm.StringParameter(this, 'OpenSearchEndpointParameter', {
      parameterName: '/app/opensearch/endpoint',
      stringValue: this.openSearchDomain.domainEndpoint,
      description: 'OpenSearch Domain Endpoint',
    });
  }
}
