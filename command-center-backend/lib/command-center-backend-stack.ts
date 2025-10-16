import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as actions from 'aws-cdk-lib/aws-cloudwatch-actions';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
import { EnvironmentConfig } from '../config/environment';

interface CommandCenterBackendStackProps extends cdk.StackProps {
  config: EnvironmentConfig;
}

export class CommandCenterBackendStack extends cdk.Stack {
  public readonly table: dynamodb.Table;
  public readonly api: apigateway.RestApi;

  // IAM Roles
  private updatesLambdaRole: iam.Role;
  private queryLambdaRole: iam.Role;
  private actionLambdaRole: iam.Role;

  // Lambda Functions
  public readonly updatesHandlerLambda?: lambda.Function;
  public readonly queryHandlerLambda?: lambda.Function;
  public readonly actionHandlerLambda?: lambda.Function;

  constructor(scope: Construct, id: string, props: CommandCenterBackendStackProps) {
    super(scope, id, props);

    const { config } = props;

    // Create IAM roles with least privilege
    this.createIAMRoles(config);

    // Create DynamoDB table (placeholder - will be implemented in task 2)
    this.table = this.createDynamoDBTable(config);

    // Create Lambda functions
    this.updatesHandlerLambda = this.createUpdatesHandlerLambda(config);

    // Note: We're using direct Nova model invocation with tool calling instead of Bedrock Agents
    // This aligns with the hackathon requirement to use "Amazon SDKs for Agents/Nova Act SDK"

    // Create queryHandlerLambda (task 7) - uses Nova model with Converse API
    this.queryHandlerLambda = this.createQueryHandlerLambda(config);

    // Create actionHandlerLambda (task 8) - uses Nova model with Converse API
    this.actionHandlerLambda = this.createActionHandlerLambda(config);

    // Create API Gateway (placeholder - will be implemented in task 9)
    this.api = this.createAPIGateway(config);

    // Create cost monitoring and alerts
    this.createCostMonitoring(config);

    // Output important values
    this.createOutputs();
  }

  private createIAMRoles(config: EnvironmentConfig): void {
    // Role for updatesHandlerLambda - needs DynamoDB read access only
    this.updatesLambdaRole = new iam.Role(this, 'UpdatesLambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'Role for updatesHandlerLambda with DynamoDB read access',
      roleName: `${config.stackName}-UpdatesLambdaRole`,
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    // Role for queryHandlerLambda - needs Bedrock invoke access
    this.queryLambdaRole = new iam.Role(this, 'QueryLambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'Role for queryHandlerLambda with Bedrock Agent invoke access',
      roleName: `${config.stackName}-QueryLambdaRole`,
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    // Add Bedrock Runtime invoke permissions for Nova models
    this.queryLambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
      ],
      resources: [
        `arn:aws:bedrock:${config.region}::foundation-model/${config.bedrockModel}`,
        `arn:aws:bedrock:${config.region}::foundation-model/us.amazon.nova-*`,
        `arn:aws:bedrock:${config.region}::foundation-model/amazon.nova-*`,
      ],
    }));

    // Role for actionHandlerLambda - needs Bedrock invoke access (same as query)
    this.actionLambdaRole = new iam.Role(this, 'ActionLambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'Role for actionHandlerLambda with Bedrock Agent invoke access',
      roleName: `${config.stackName}-ActionLambdaRole`,
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    // Add Bedrock Runtime invoke permissions for Nova models
    this.actionLambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
      ],
      resources: [
        `arn:aws:bedrock:${config.region}::foundation-model/${config.bedrockModel}`,
        `arn:aws:bedrock:${config.region}::foundation-model/us.amazon.nova-*`,
        `arn:aws:bedrock:${config.region}::foundation-model/amazon.nova-*`,
      ],
    }));

    // Note: Tool Lambda and Bedrock Agent roles removed - using direct Nova model invocation
  }

  private createDynamoDBTable(config: EnvironmentConfig): dynamodb.Table {
    // Create MasterEventTimeline table with Day (PK) and Timestamp (SK)
    const table = new dynamodb.Table(this, 'MasterEventTimeline', {
      tableName: `${config.stackName}-MasterEventTimeline`,
      partitionKey: {
        name: 'Day',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'Timestamp',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      removalPolicy: config.stage === 'prod'
        ? cdk.RemovalPolicy.RETAIN
        : cdk.RemovalPolicy.DESTROY,
    });

    // Add Global Secondary Index: domain-timestamp-index
    // Enables efficient filtering by domain in the updates endpoint
    table.addGlobalSecondaryIndex({
      indexName: 'domain-timestamp-index',
      partitionKey: {
        name: 'domain',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'Timestamp',
        type: dynamodb.AttributeType.STRING,
      },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // Grant read permissions to Lambda roles that need it
    table.grantReadData(this.updatesLambdaRole);

    return table;
  }

  private createAPIGateway(config: EnvironmentConfig): apigateway.RestApi {
    // Task 9.1: Create REST API in CDK
    // Task 10.1: Configure CloudWatch logging for API Gateway

    // Create CloudWatch Log Group for API Gateway access logs
    const apiLogGroup = new logs.LogGroup(this, 'APIGatewayAccessLogs', {
      logGroupName: `/aws/apigateway/${config.stackName}-API`,
      retention: logs.RetentionDays.TWO_WEEKS,
      removalPolicy: config.stage === 'prod'
        ? cdk.RemovalPolicy.RETAIN
        : cdk.RemovalPolicy.DESTROY,
    });

    // Define API Gateway REST API resource with proper configuration
    const api = new apigateway.RestApi(this, 'CommandCenterAPI', {
      restApiName: `${config.stackName}-API`,
      description: `Command Center Backend API for disaster response - ${config.stage} environment`,
      deployOptions: {
        stageName: config.stage,
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: true,
        metricsEnabled: true,
        tracingEnabled: true,
        throttlingBurstLimit: 100,
        throttlingRateLimit: 50,
        accessLogDestination: new apigateway.LogGroupLogDestination(apiLogGroup),
        accessLogFormat: apigateway.AccessLogFormat.jsonWithStandardFields({
          caller: true,
          httpMethod: true,
          ip: true,
          protocol: true,
          requestTime: true,
          resourcePath: true,
          responseLength: true,
          status: true,
          user: true,
        }),
      },
      // Task 9.3: Set up CORS configuration
      defaultCorsPreflightOptions: {
        allowOrigins: config.stage === 'prod'
          ? ['https://your-production-domain.com'] // Update with actual production domain
          : apigateway.Cors.ALL_ORIGINS, // Allow all origins in dev/staging
        allowMethods: ['GET', 'POST', 'OPTIONS'],
        allowHeaders: [
          'Content-Type',
          'X-Amz-Date',
          'Authorization',
          'X-Api-Key',
          'X-Amz-Security-Token',
        ],
        allowCredentials: false,
        maxAge: cdk.Duration.hours(1),
      },
      cloudWatchRole: true,
      endpointConfiguration: {
        types: [apigateway.EndpointType.REGIONAL],
      },
    });

    // Task 9.2: Configure API routes and integrations
    this.configureAPIRoutes(api);

    return api;
  }

  private configureAPIRoutes(api: apigateway.RestApi): void {
    // Task 9.2: Create API routes and Lambda integrations

    // Create /data resource
    const dataResource = api.root.addResource('data');

    // Create GET /data/updates route → updatesHandlerLambda
    const updatesResource = dataResource.addResource('updates');
    const updatesIntegration = new apigateway.LambdaIntegration(this.updatesHandlerLambda!, {
      proxy: true,
      allowTestInvoke: true,
    });

    updatesResource.addMethod('GET', updatesIntegration, {
      apiKeyRequired: true,
      requestParameters: {
        'method.request.querystring.since': true, // Required parameter
        'method.request.querystring.domain': false, // Optional parameter
      },
      methodResponses: [
        {
          statusCode: '200',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
          },
        },
        {
          statusCode: '400',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
          },
        },
        {
          statusCode: '500',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
          },
        },
      ],
    });

    // Create /agent resource
    const agentResource = api.root.addResource('agent');

    // Create POST /agent/query route → queryHandlerLambda
    const queryResource = agentResource.addResource('query');
    const queryIntegration = new apigateway.LambdaIntegration(this.queryHandlerLambda!, {
      proxy: true,
      allowTestInvoke: true,
    });

    queryResource.addMethod('POST', queryIntegration, {
      apiKeyRequired: true,
      requestValidator: new apigateway.RequestValidator(this, 'QueryRequestValidator', {
        restApi: api,
        requestValidatorName: 'query-request-validator',
        validateRequestBody: true,
        validateRequestParameters: false,
      }),
      methodResponses: [
        {
          statusCode: '200',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
          },
        },
        {
          statusCode: '400',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
          },
        },
        {
          statusCode: '500',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
          },
        },
      ],
    });

    // Create POST /agent/action route → actionHandlerLambda
    const actionResource = agentResource.addResource('action');
    const actionIntegration = new apigateway.LambdaIntegration(this.actionHandlerLambda!, {
      proxy: true,
      allowTestInvoke: true,
    });

    actionResource.addMethod('POST', actionIntegration, {
      apiKeyRequired: true,
      requestValidator: new apigateway.RequestValidator(this, 'ActionRequestValidator', {
        restApi: api,
        requestValidatorName: 'action-request-validator',
        validateRequestBody: true,
        validateRequestParameters: false,
      }),
      methodResponses: [
        {
          statusCode: '200',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
          },
        },
        {
          statusCode: '400',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
          },
        },
        {
          statusCode: '500',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
          },
        },
      ],
    });

    // Task 9.3: Create API Key and Usage Plan for authentication
    const apiKey = api.addApiKey('CommandCenterAPIKey', {
      apiKeyName: `${this.stackName}-APIKey`,
      description: 'API Key for Command Center Dashboard',
    });

    const usagePlan = api.addUsagePlan('CommandCenterUsagePlan', {
      name: `${this.stackName}-UsagePlan`,
      description: 'Usage plan for Command Center API',
      throttle: {
        rateLimit: 50,
        burstLimit: 100,
      },
      quota: {
        limit: 10000,
        period: apigateway.Period.DAY,
      },
    });

    usagePlan.addApiKey(apiKey);
    usagePlan.addApiStage({
      stage: api.deploymentStage,
    });

    // Output the API Key ID (value must be retrieved from AWS Console or CLI)
    new cdk.CfnOutput(this, 'APIKeyId', {
      value: apiKey.keyId,
      description: 'API Key ID (retrieve value from AWS Console)',
      exportName: `${this.stackName}-APIKeyId`,
    });
  }

  private createCostMonitoring(config: EnvironmentConfig): void {
    // Create SNS topic for cost alerts
    const costAlertTopic = new sns.Topic(this, 'CostAlertTopic', {
      displayName: `${config.stackName} Cost Alert`,
      topicName: `${config.stackName}-CostAlert`,
    });

    // Subscribe email to the topic
    costAlertTopic.addSubscription(
      new subscriptions.EmailSubscription(config.costAlertEmail)
    );

    // Create CloudWatch alarm for estimated charges
    const costAlarm = new cloudwatch.Alarm(this, 'CostAlarm', {
      alarmName: `${config.stackName}-CostExceeded`,
      alarmDescription: `Alert when estimated charges exceed $${config.costAlertThreshold}`,
      metric: new cloudwatch.Metric({
        namespace: 'AWS/Billing',
        metricName: 'EstimatedCharges',
        dimensionsMap: {
          Currency: 'USD',
        },
        statistic: 'Maximum',
        period: cdk.Duration.hours(6),
      }),
      threshold: config.costAlertThreshold,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    // Add SNS action to the alarm
    costAlarm.addAlarmAction(new actions.SnsAction(costAlertTopic));

    // Task 10.2: Create Lambda function for automatic resource termination
    const shutdownLambdaRole = new iam.Role(this, 'ShutdownLambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'Role for cost breach shutdown Lambda',
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    // Grant permissions to delete CloudFormation stack
    shutdownLambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'cloudformation:DeleteStack',
        'cloudformation:DescribeStacks',
      ],
      resources: [
        'arn:aws:cloudformation:' + config.region + ':' + config.account + ':stack/' + config.stackName + '/*',
      ],
    }));

    // Create shutdown Lambda function with inline code
    const shutdownCode = 'const { CloudFormationClient, DeleteStackCommand } = require(\'@aws-sdk/client-cloudformation\');\\n\\nexports.handler = async (event) => {\\n  console.log(\'Cost breach shutdown triggered\', { event: JSON.stringify(event) });\\n  \\n  const stackName = process.env.STACK_NAME;\\n  const region = process.env.AWS_REGION;\\n  \\n  if (!stackName) {\\n    console.error(\'STACK_NAME environment variable not set\');\\n    return { statusCode: 500, body: \'Configuration error\' };\\n  }\\n  \\n  try {\\n    const client = new CloudFormationClient({ region });\\n    \\n    console.log(\'Initiating stack deletion\', { stackName });\\n    \\n    const command = new DeleteStackCommand({\\n      StackName: stackName,\\n    });\\n    \\n    await client.send(command);\\n    \\n    console.log(\'Stack deletion initiated successfully\', { stackName });\\n    \\n    return {\\n      statusCode: 200,\\n      body: JSON.stringify({\\n        message: \'Stack deletion initiated due to cost breach\',\\n        stackName,\\n        timestamp: new Date().toISOString(),\\n      }),\\n    };\\n  } catch (error) {\\n    console.error(\'Error deleting stack\', {\\n      error: error.message,\\n      stack: error.stack,\\n      stackName,\\n    });\\n    \\n    return {\\n      statusCode: 500,\\n      body: JSON.stringify({\\n        error: \'Failed to delete stack\',\\n        message: error.message,\\n      }),\\n    };\\n  }\\n};';

    // Create log group for shutdown Lambda
    const shutdownLogGroup = new logs.LogGroup(this, 'CostBreachShutdownLogGroup', {
      logGroupName: `/aws/lambda/${config.stackName}-CostBreachShutdown`,
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const shutdownLambda = new lambda.Function(this, 'CostBreachShutdownLambda', {
      functionName: config.stackName + '-CostBreachShutdown',
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: 'index.handler',
      code: lambda.Code.fromInline(shutdownCode),
      role: shutdownLambdaRole,
      environment: {
        STACK_NAME: config.stackName,
      },
      timeout: cdk.Duration.seconds(30),
      description: 'Automatically shuts down resources when cost threshold is breached',
      logGroup: shutdownLogGroup,
    });

    // Grant SNS permission to invoke the shutdown Lambda
    shutdownLambda.addPermission('AllowSNSInvoke', {
      principal: new iam.ServicePrincipal('sns.amazonaws.com'),
      action: 'lambda:InvokeFunction',
      sourceArn: costAlertTopic.topicArn,
    });

    // Subscribe shutdown Lambda to cost alert topic
    costAlertTopic.addSubscription(
      new subscriptions.LambdaSubscription(shutdownLambda)
    );

    // Create CloudWatch Dashboard
    this.createMonitoringDashboard(config, costAlertTopic);

    // Output cost monitoring information
    new cdk.CfnOutput(this, 'CostAlertTopicArn', {
      value: costAlertTopic.topicArn,
      description: 'SNS Topic ARN for cost alerts',
      exportName: config.stackName + '-CostAlertTopicArn',
    });

    new cdk.CfnOutput(this, 'CostThreshold', {
      value: config.costAlertThreshold.toString(),
      description: 'Cost alert threshold in USD',
    });
  }

  private createUpdatesHandlerLambda(config: EnvironmentConfig): lambda.Function {
    // Create log group explicitly
    const logGroup = new logs.LogGroup(this, 'UpdatesHandlerLogGroup', {
      logGroupName: `/aws/lambda/${config.stackName}-UpdatesHandler`,
      retention: logs.RetentionDays.TWO_WEEKS,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const updatesLambda = new lambda.Function(this, 'UpdatesHandlerLambda', {
      functionName: `${config.stackName}-UpdatesHandler`,
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: 'lib/lambdas/updatesHandler.handler',
      code: lambda.Code.fromAsset('lambda-bundle'),
      role: this.updatesLambdaRole,
      environment: {
        TABLE_NAME: this.table.tableName,
        LOG_LEVEL: config.stage === 'prod' ? 'INFO' : 'DEBUG',
        AWS_NODEJS_CONNECTION_REUSE_ENABLED: '1', // Enable connection reuse for better performance
      },
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      description: 'Handles GET /data/updates endpoint for real-time event updates',
      logGroup: logGroup,
    });

    return updatesLambda;
  }

  // Note: createDatabaseQueryToolLambda removed - tools are now executed inline within query/action handlers

  private createQueryHandlerLambda(config: EnvironmentConfig): lambda.Function {
    // Create log group explicitly
    const logGroup = new logs.LogGroup(this, 'QueryHandlerLogGroup', {
      logGroupName: `/aws/lambda/${config.stackName}-QueryHandler`,
      retention: logs.RetentionDays.TWO_WEEKS,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const queryLambda = new lambda.Function(this, 'QueryHandlerLambda', {
      functionName: `${config.stackName}-QueryHandler`,
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: 'lib/lambdas/queryHandler.handler',
      code: lambda.Code.fromAsset('lambda-bundle'),
      role: this.queryLambdaRole,
      environment: {
        BEDROCK_MODEL: config.bedrockModel,
        TABLE_NAME: this.table.tableName,
        LOG_LEVEL: config.stage === 'prod' ? 'INFO' : 'DEBUG',
        AWS_NODEJS_CONNECTION_REUSE_ENABLED: '1',
      },
      timeout: cdk.Duration.seconds(60), // Longer timeout for model invocation
      memorySize: 512,
      description: 'Handles POST /agent/query endpoint for natural language queries using Nova model',
      logGroup: logGroup,
    });

    // Grant DynamoDB read access
    this.table.grantReadData(queryLambda);

    return queryLambda;
  }

  private createActionHandlerLambda(config: EnvironmentConfig): lambda.Function {
    // Create log group explicitly
    const logGroup = new logs.LogGroup(this, 'ActionHandlerLogGroup', {
      logGroupName: `/aws/lambda/${config.stackName}-ActionHandler`,
      retention: logs.RetentionDays.TWO_WEEKS,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const actionLambda = new lambda.Function(this, 'ActionHandlerLambda', {
      functionName: `${config.stackName}-ActionHandler`,
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: 'lib/lambdas/actionHandler.handler',
      code: lambda.Code.fromAsset('lambda-bundle'),
      role: this.actionLambdaRole,
      environment: {
        BEDROCK_MODEL: config.bedrockModel,
        TABLE_NAME: this.table.tableName,
        LOG_LEVEL: config.stage === 'prod' ? 'INFO' : 'DEBUG',
        AWS_NODEJS_CONNECTION_REUSE_ENABLED: '1',
      },
      timeout: cdk.Duration.seconds(60), // Longer timeout for model invocation
      memorySize: 512,
      description: 'Handles POST /agent/action endpoint for pre-defined actions using Nova model',
      logGroup: logGroup,
    });

    // Grant DynamoDB read access
    this.table.grantReadData(actionLambda);

    return actionLambda;
  }

  // Note: createBedrockAgent removed - using direct Nova model invocation with Converse API instead

  private createOutputs(): void {
    new cdk.CfnOutput(this, 'TableName', {
      value: this.table.tableName,
      description: 'DynamoDB table name',
      exportName: `${this.stackName}-TableName`,
    });

    new cdk.CfnOutput(this, 'APIEndpoint', {
      value: this.api.url,
      description: 'API Gateway endpoint URL',
      exportName: `${this.stackName}-APIEndpoint`,
    });

    new cdk.CfnOutput(this, 'UpdatesLambdaRoleArn', {
      value: this.updatesLambdaRole.roleArn,
      description: 'ARN of the Updates Lambda role',
    });

    new cdk.CfnOutput(this, 'QueryLambdaRoleArn', {
      value: this.queryLambdaRole.roleArn,
      description: 'ARN of the Query Lambda role',
    });

    new cdk.CfnOutput(this, 'ActionLambdaRoleArn', {
      value: this.actionLambdaRole.roleArn,
      description: 'ARN of the Action Lambda role',
    });

    if (this.updatesHandlerLambda) {
      new cdk.CfnOutput(this, 'UpdatesHandlerLambdaArn', {
        value: this.updatesHandlerLambda.functionArn,
        description: 'ARN of the Updates Handler Lambda function',
      });
    }

    if (this.queryHandlerLambda) {
      new cdk.CfnOutput(this, 'QueryHandlerLambdaArn', {
        value: this.queryHandlerLambda.functionArn,
        description: 'ARN of the Query Handler Lambda function',
      });
    }

    if (this.actionHandlerLambda) {
      new cdk.CfnOutput(this, 'ActionHandlerLambdaArn', {
        value: this.actionHandlerLambda.functionArn,
        description: 'ARN of the Action Handler Lambda function',
      });
    }
  }

  private createMonitoringDashboard(config: EnvironmentConfig, costAlertTopic: sns.Topic): void {
    // Create comprehensive CloudWatch Dashboard
    const dashboard = new cloudwatch.Dashboard(this, 'MonitoringDashboard', {
      dashboardName: `${config.stackName}-Monitoring`,
    });

    // API Gateway Metrics
    const apiRequestsWidget = new cloudwatch.GraphWidget({
      title: 'API Gateway - Requests',
      left: [
        this.api.metricCount({
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 12,
    });

    const apiLatencyWidget = new cloudwatch.GraphWidget({
      title: 'API Gateway - Latency',
      left: [
        this.api.metricLatency({
          statistic: 'Average',
          period: cdk.Duration.minutes(5),
        }),
        this.api.metricLatency({
          statistic: 'p99',
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 12,
    });

    const apiErrorsWidget = new cloudwatch.GraphWidget({
      title: 'API Gateway - Errors',
      left: [
        this.api.metricClientError({
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
        }),
        this.api.metricServerError({
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 12,
    });

    // Lambda Metrics - Updates Handler
    const updatesInvocationsWidget = new cloudwatch.GraphWidget({
      title: 'Updates Lambda - Invocations',
      left: [
        this.updatesHandlerLambda!.metricInvocations({
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 8,
    });

    const updatesDurationWidget = new cloudwatch.GraphWidget({
      title: 'Updates Lambda - Duration',
      left: [
        this.updatesHandlerLambda!.metricDuration({
          statistic: 'Average',
          period: cdk.Duration.minutes(5),
        }),
        this.updatesHandlerLambda!.metricDuration({
          statistic: 'p99',
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 8,
    });

    const updatesErrorsWidget = new cloudwatch.GraphWidget({
      title: 'Updates Lambda - Errors',
      left: [
        this.updatesHandlerLambda!.metricErrors({
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
        }),
        this.updatesHandlerLambda!.metricThrottles({
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 8,
    });

    // Lambda Metrics - Query Handler
    const queryInvocationsWidget = new cloudwatch.GraphWidget({
      title: 'Query Lambda - Invocations',
      left: [
        this.queryHandlerLambda!.metricInvocations({
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 8,
    });

    const queryDurationWidget = new cloudwatch.GraphWidget({
      title: 'Query Lambda - Duration',
      left: [
        this.queryHandlerLambda!.metricDuration({
          statistic: 'Average',
          period: cdk.Duration.minutes(5),
        }),
        this.queryHandlerLambda!.metricDuration({
          statistic: 'p99',
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 8,
    });

    const queryErrorsWidget = new cloudwatch.GraphWidget({
      title: 'Query Lambda - Errors',
      left: [
        this.queryHandlerLambda!.metricErrors({
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
        }),
        this.queryHandlerLambda!.metricThrottles({
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 8,
    });

    // Lambda Metrics - Action Handler
    const actionInvocationsWidget = new cloudwatch.GraphWidget({
      title: 'Action Lambda - Invocations',
      left: [
        this.actionHandlerLambda!.metricInvocations({
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 8,
    });

    const actionDurationWidget = new cloudwatch.GraphWidget({
      title: 'Action Lambda - Duration',
      left: [
        this.actionHandlerLambda!.metricDuration({
          statistic: 'Average',
          period: cdk.Duration.minutes(5),
        }),
        this.actionHandlerLambda!.metricDuration({
          statistic: 'p99',
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 8,
    });

    const actionErrorsWidget = new cloudwatch.GraphWidget({
      title: 'Action Lambda - Errors',
      left: [
        this.actionHandlerLambda!.metricErrors({
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
        }),
        this.actionHandlerLambda!.metricThrottles({
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 8,
    });

    // Note: Tool Lambda metrics removed - tools are now executed inline within query/action handlers

    // DynamoDB Metrics
    const dynamoReadCapacityWidget = new cloudwatch.GraphWidget({
      title: 'DynamoDB - Read Capacity',
      left: [
        new cloudwatch.Metric({
          namespace: 'AWS/DynamoDB',
          metricName: 'ConsumedReadCapacityUnits',
          dimensionsMap: {
            TableName: this.table.tableName,
          },
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 12,
    });

    const dynamoWriteCapacityWidget = new cloudwatch.GraphWidget({
      title: 'DynamoDB - Write Capacity',
      left: [
        new cloudwatch.Metric({
          namespace: 'AWS/DynamoDB',
          metricName: 'ConsumedWriteCapacityUnits',
          dimensionsMap: {
            TableName: this.table.tableName,
          },
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 12,
    });

    const dynamoThrottlesWidget = new cloudwatch.GraphWidget({
      title: 'DynamoDB - Throttles',
      left: [
        new cloudwatch.Metric({
          namespace: 'AWS/DynamoDB',
          metricName: 'ReadThrottleEvents',
          dimensionsMap: {
            TableName: this.table.tableName,
          },
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
        }),
        new cloudwatch.Metric({
          namespace: 'AWS/DynamoDB',
          metricName: 'WriteThrottleEvents',
          dimensionsMap: {
            TableName: this.table.tableName,
          },
          statistic: 'Sum',
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 12,
    });

    // Cost Monitoring Widget
    const costWidget = new cloudwatch.SingleValueWidget({
      title: 'Estimated Monthly Charges',
      metrics: [
        new cloudwatch.Metric({
          namespace: 'AWS/Billing',
          metricName: 'EstimatedCharges',
          dimensionsMap: {
            Currency: 'USD',
          },
          statistic: 'Maximum',
          period: cdk.Duration.hours(6),
        }),
      ],
      width: 12,
      height: 6,
    });

    // Add all widgets to dashboard
    dashboard.addWidgets(
      costWidget,
      new cloudwatch.TextWidget({
        markdown: '# Cost Alert Configuration\\n\\n**Threshold:** $' + config.costAlertThreshold + '\\n**Alert Email:** ' + config.costAlertEmail + '\\n**Auto-Shutdown:** Enabled\\n\\nWhen costs exceed the threshold, an email alert will be sent and resources will be automatically terminated to prevent further charges.',
        width: 12,
        height: 6,
      })
    );

    dashboard.addWidgets(apiRequestsWidget, apiLatencyWidget);
    dashboard.addWidgets(apiErrorsWidget, new cloudwatch.TextWidget({
      markdown: '# API Gateway Metrics\\n\\nMonitor request volume, latency, and error rates for the Command Center API.\\n\\n**Target Latency:** < 500ms (p95)\\n**Error Rate:** < 1%',
      width: 12,
    }));

    dashboard.addWidgets(updatesInvocationsWidget, updatesDurationWidget, updatesErrorsWidget);
    dashboard.addWidgets(queryInvocationsWidget, queryDurationWidget, queryErrorsWidget);
    dashboard.addWidgets(actionInvocationsWidget, actionDurationWidget, actionErrorsWidget);
    dashboard.addWidgets(dynamoReadCapacityWidget, dynamoWriteCapacityWidget);
    dashboard.addWidgets(dynamoThrottlesWidget, new cloudwatch.TextWidget({
      markdown: '# DynamoDB Metrics\\n\\nMonitor read/write capacity consumption and throttling events.\\n\\n**Billing Mode:** Pay-per-request\\n**Throttles:** Should be 0 under normal operation',
      width: 12,
    }));

    new cdk.CfnOutput(this, 'DashboardURL', {
      value: 'https://console.aws.amazon.com/cloudwatch/home?region=' + config.region + '#dashboards:name=' + config.stackName + '-Monitoring',
      description: 'CloudWatch Dashboard URL',
    });
  }
}
