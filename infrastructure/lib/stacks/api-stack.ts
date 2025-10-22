import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';
import * as path from 'path';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';

interface ApiStackProps extends cdk.StackProps {
  userPool: cognito.UserPool;
  userPoolClient: cognito.UserPoolClient;
  configurationsTable: dynamodb.Table;
  configBackupBucket: s3.Bucket;
  database: any; // rds.DatabaseInstance or rds.DatabaseCluster
  databaseSecret: secretsmanager.ISecret;
  vpc: ec2.IVpc;
  sessionsTable: dynamodb.Table;
  messagesTable: dynamodb.Table;
  queryJobsTable: dynamodb.Table;
  reportsTable: dynamodb.Table;
}

export class ApiStack extends cdk.Stack {
  public readonly api: apigateway.RestApi;
  public readonly authorizer: apigateway.RequestAuthorizer;

  constructor(scope: Construct, id: string, props: ApiStackProps) {
    super(scope, id, props);

    // Create Lambda authorizer
    const authorizerFunction = lambda.Function.fromFunctionName(
      this,
      'AuthorizerFunction',
      `${id.replace('-Api', '-Auth')}-Authorizer`
    );

    // Create API Gateway REST API
    this.api = new apigateway.RestApi(this, 'RestApi', {
      restApiName: `${id}-RestApi`,
      description: 'Multi-Agent Orchestration System API',
      deployOptions: {
        stageName: 'v1',
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: true,
        metricsEnabled: true,
        tracingEnabled: true,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: [
          'Content-Type',
          'X-Amz-Date',
          'Authorization',
          'X-Api-Key',
          'X-Amz-Security-Token',
        ],
        allowCredentials: true,
      },
      cloudWatchRole: true,
    });

    // Create Request Authorizer
    this.authorizer = new apigateway.RequestAuthorizer(this, 'RequestAuthorizer', {
      handler: authorizerFunction,
      identitySources: [apigateway.IdentitySource.header('Authorization')],
      authorizerName: `${id}-Authorizer`,
      resultsCacheTtl: cdk.Duration.minutes(5),
    });

    // Create /api/v1 resource
    const apiV1 = this.api.root.addResource('api').addResource('v1');

    // Create actual Lambda functions for endpoints
    const ingestHandler = new PythonFunction(this, 'IngestHandler', {
      functionName: `${this.stackName}-IngestHandler`,
      entry: path.join(__dirname, '../../lambda/orchestration'),
      runtime: lambda.Runtime.PYTHON_3_11,
      index: 'ingest_handler_simple.py',
      handler: 'handler',
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        INCIDENTS_TABLE: `${this.stackName.replace('-Api', '-Data')}-Incidents`,
        BEDROCK_DEFAULT_MODEL: process.env.BEDROCK_DEFAULT_MODEL || 'amazon.nova-lite-v1:0',
        BEDROCK_AGENT_MODEL: process.env.BEDROCK_AGENT_MODEL || 'amazon.nova-micro-v1:0',
      },
      bundling: {
        assetExcludes: [
          '.venv',
          'venv',
          '__pycache__',
          '*.pyc',
          'test_*',
          '.pytest_cache',
          '.coverage',
        ],
      },
      description: 'Handles data ingestion requests',
    });
    
    const queryHandler = new PythonFunction(this, 'QueryHandler', {
      functionName: `${this.stackName}-QueryHandler`,
      entry: path.join(__dirname, '../../lambda/orchestration'),
      runtime: lambda.Runtime.PYTHON_3_11,
      index: 'query_handler_simple.py',
      handler: 'handler',
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        QUERIES_TABLE: `${this.stackName.replace('-Api', '-Data')}-Queries`,
        QUERY_JOBS_TABLE: props.queryJobsTable.tableName,
        SESSIONS_TABLE: props.sessionsTable.tableName,
        MESSAGES_TABLE: props.messagesTable.tableName,
        ORCHESTRATOR_FUNCTION: `${this.stackName}-Orchestrator`,
        BEDROCK_DEFAULT_MODEL: process.env.BEDROCK_DEFAULT_MODEL || 'amazon.nova-lite-v1:0',
        BEDROCK_AGENT_MODEL: process.env.BEDROCK_AGENT_MODEL || 'amazon.nova-micro-v1:0',
      },
      bundling: {
        assetExcludes: [
          '.venv',
          'venv',
          '__pycache__',
          '*.pyc',
          'test_*',
          '.pytest_cache',
          '.coverage',
        ],
      },
      description: 'Handles query requests',
    });
    
    // Grant query handler permissions
    props.queryJobsTable.grantReadWriteData(queryHandler);
    props.sessionsTable.grantReadWriteData(queryHandler);
    props.messagesTable.grantReadWriteData(queryHandler);
    
    // Create Orchestrator Lambda (processes agent pipelines)
    const orchestratorHandler = new PythonFunction(this, 'Orchestrator', {
      functionName: `${this.stackName}-Orchestrator`,
      entry: path.join(__dirname, '../../lambda/orchestration'),
      runtime: lambda.Runtime.PYTHON_3_11,
      index: 'orchestrator_handler.py',
      handler: 'handler',
      timeout: cdk.Duration.minutes(5),
      memorySize: 1024,
      vpc: props.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PUBLIC,
      },
      allowPublicSubnet: true,
      environment: {
        CONFIGURATIONS_TABLE: props.configurationsTable.tableName,
        QUERY_JOBS_TABLE: props.queryJobsTable.tableName,
        DB_SECRET_ARN: props.databaseSecret.secretArn,
        DB_HOST: (props.database as any).clusterEndpoint.hostname,
        DB_PORT: '5432',
        DB_NAME: 'multi_agent_orchestration',
        BEDROCK_DEFAULT_MODEL: process.env.BEDROCK_DEFAULT_MODEL || 'amazon.nova-lite-v1:0',
        BEDROCK_AGENT_MODEL: process.env.BEDROCK_AGENT_MODEL || 'amazon.nova-micro-v1:0',
        BEDROCK_ORCHESTRATOR_MODEL: process.env.BEDROCK_ORCHESTRATOR_MODEL || 'amazon.nova-pro-v1:0',
      },
      bundling: {
        assetExcludes: [
          '.venv',
          'venv',
          '__pycache__',
          '*.pyc',
          'test_*',
          '.pytest_cache',
          '.coverage',
        ],
      },
      description: 'Orchestrates agent pipeline execution',
    });
    
    // Grant orchestrator permissions
    props.configurationsTable.grantReadData(orchestratorHandler);
    props.queryJobsTable.grantReadWriteData(orchestratorHandler);
    props.databaseSecret.grantRead(orchestratorHandler);
    orchestratorHandler.addToRolePolicy(new cdk.aws_iam.PolicyStatement({
      actions: ['bedrock:InvokeModel'],
      resources: ['*'],
    }));
    
    // Grant query handler permission to invoke orchestrator
    orchestratorHandler.grantInvoke(queryHandler);
    
    const dataHandler = new lambda.Function(this, 'DataHandler', {
      functionName: `${this.stackName}-DataHandler`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'retrieval_proxy.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/data-api-proxies')),
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      description: 'Handles data retrieval requests',
    });
    
    const toolsHandler = new lambda.Function(this, 'ToolsHandler', {
      functionName: `${this.stackName}-ToolsHandler`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'tool_registry.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/tool-registry')),
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        TOOL_CATALOG_TABLE: `${this.stackName.replace('-Api', '-Data')}-ToolCatalog`,
      },
      description: 'Handles tool registry requests',
    });
    
    // Create actual config handler Lambda
    const configHandler = new PythonFunction(this, 'ConfigHandler', {
      functionName: `${this.stackName}-ConfigHandler`,
      entry: path.join(__dirname, '../../lambda/config-api'),
      runtime: lambda.Runtime.PYTHON_3_11,
      index: 'config_handler.py',
      handler: 'handler',
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        CONFIGURATIONS_TABLE: props.configurationsTable.tableName,
        CONFIG_BACKUP_BUCKET: props.configBackupBucket.bucketName,
      },
      bundling: {
        assetExcludes: [
          '.venv',
          'venv',
          '__pycache__',
          '*.pyc',
          'test_*',
          '.pytest_cache',
          '.coverage',
        ],
      },
      description: 'Handles configuration CRUD operations for agents, playbooks, dependency graphs, and templates',
    });
    
    // Grant permissions to config handler
    props.configurationsTable.grantReadWriteData(configHandler);
    props.configBackupBucket.grantReadWrite(configHandler);

    // Create Agent Handler Lambda
    const agentHandler = new PythonFunction(this, 'AgentHandler', {
      functionName: `${this.stackName}-AgentHandler`,
      entry: path.join(__dirname, '../../lambda/agent-api'),
      runtime: lambda.Runtime.PYTHON_3_11,
      index: 'agent_handler.py',
      handler: 'handler',
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      vpc: props.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PUBLIC,
      },
      allowPublicSubnet: true,
      environment: {
        DB_SECRET_ARN: props.databaseSecret.secretArn,
        DB_HOST: (props.database as any).clusterEndpoint.hostname,
        DB_PORT: '5432',
        DB_NAME: 'multi_agent_orchestration',
      },
      bundling: {
        assetExcludes: [
          '.venv',
          'venv',
          '__pycache__',
          '*.pyc',
          'test_*',
          '.pytest_cache',
          '.coverage',
        ],
      },
      description: 'Handles agent CRUD operations with DAG validation',
    });
    
    // Grant permissions
    props.databaseSecret.grantRead(agentHandler);

    // Create Domain Handler Lambda
    const domainHandler = new PythonFunction(this, 'DomainHandler', {
      functionName: `${this.stackName}-DomainHandler`,
      entry: path.join(__dirname, '../../lambda/domain-api'),
      runtime: lambda.Runtime.PYTHON_3_11,
      index: 'domain_handler.py',
      handler: 'handler',
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      vpc: props.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PUBLIC,
      },
      allowPublicSubnet: true,
      environment: {
        DB_SECRET_ARN: props.databaseSecret.secretArn,
        DB_HOST: (props.database as any).clusterEndpoint.hostname,
        DB_PORT: '5432',
        DB_NAME: 'multi_agent_orchestration',
      },
      bundling: {
        assetExcludes: [
          '.venv',
          'venv',
          '__pycache__',
          '*.pyc',
          'test_*',
          '.pytest_cache',
          '.coverage',
        ],
      },
      description: 'Handles domain CRUD operations with playbook validation',
    });
    
    // Grant permissions
    props.databaseSecret.grantRead(domainHandler);

    // 1. POST /api/v1/ingest
    const ingestResource = apiV1.addResource('ingest');
    ingestResource.addMethod('POST', new apigateway.LambdaIntegration(ingestHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestValidator: this.createRequestValidator('IngestValidator'),
      requestModels: {
        'application/json': this.createIngestModel(),
      },
    });

    // 2. POST /api/v1/query
    const queryResource = apiV1.addResource('query');
    queryResource.addMethod('POST', new apigateway.LambdaIntegration(queryHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestValidator: this.createRequestValidator('QueryValidator'),
      requestModels: {
        'application/json': this.createQueryModel(),
      },
    });

    // 3. GET /api/v1/data
    const dataResource = apiV1.addResource('data');
    dataResource.addMethod('GET', new apigateway.LambdaIntegration(dataHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestParameters: {
        'method.request.querystring.type': false,
        'method.request.querystring.filters': false,
      },
    });

    // 4. POST/GET /api/v1/config
    const configResource = apiV1.addResource('config');
    configResource.addMethod('POST', new apigateway.LambdaIntegration(configHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestValidator: this.createRequestValidator('ConfigPostValidator'),
      requestModels: {
        'application/json': this.createConfigModel(),
      },
    });
    configResource.addMethod('GET', new apigateway.LambdaIntegration(configHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
    });

    // Add {type}/{id} sub-resources for config
    const configTypeResource = configResource.addResource('{type}');
    const configIdResource = configTypeResource.addResource('{id}');
    configIdResource.addMethod('GET', new apigateway.LambdaIntegration(configHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
    });
    configIdResource.addMethod('PUT', new apigateway.LambdaIntegration(configHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
    });
    configIdResource.addMethod('DELETE', new apigateway.LambdaIntegration(configHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
    });

    // 5. POST/GET /api/v1/tools
    const toolsResource = apiV1.addResource('tools');
    toolsResource.addMethod('POST', new apigateway.LambdaIntegration(toolsHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestValidator: this.createRequestValidator('ToolsPostValidator'),
    });
    toolsResource.addMethod('GET', new apigateway.LambdaIntegration(toolsHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
    });

    // 6. Agent Management API - /api/v1/agents
    const agentsResource = apiV1.addResource('agents');
    
    // POST /api/v1/agents - Create agent
    agentsResource.addMethod('POST', new apigateway.LambdaIntegration(agentHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestValidator: this.createRequestValidator('AgentPostValidator'),
      requestModels: {
        'application/json': this.createAgentModel(),
      },
    });
    
    // GET /api/v1/agents - List agents
    agentsResource.addMethod('GET', new apigateway.LambdaIntegration(agentHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestParameters: {
        'method.request.querystring.page': false,
        'method.request.querystring.limit': false,
        'method.request.querystring.agent_class': false,
      },
    });
    
    // /api/v1/agents/{agent_id}
    const agentIdResource = agentsResource.addResource('{agent_id}');
    
    // GET /api/v1/agents/{agent_id} - Get specific agent
    agentIdResource.addMethod('GET', new apigateway.LambdaIntegration(agentHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
    });
    
    // PUT /api/v1/agents/{agent_id} - Update agent
    agentIdResource.addMethod('PUT', new apigateway.LambdaIntegration(agentHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestValidator: this.createRequestValidator('AgentPutValidator'),
    });
    
    // DELETE /api/v1/agents/{agent_id} - Delete agent
    agentIdResource.addMethod('DELETE', new apigateway.LambdaIntegration(agentHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
    });

    // 7. Domain Management API - /api/v1/domains
    const domainsResource = apiV1.addResource('domains');
    
    // POST /api/v1/domains - Create domain
    domainsResource.addMethod('POST', new apigateway.LambdaIntegration(domainHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestValidator: this.createRequestValidator('DomainPostValidator'),
      requestModels: {
        'application/json': this.createDomainModel(),
      },
    });
    
    // GET /api/v1/domains - List domains
    domainsResource.addMethod('GET', new apigateway.LambdaIntegration(domainHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestParameters: {
        'method.request.querystring.page': false,
        'method.request.querystring.limit': false,
      },
    });
    
    // /api/v1/domains/{domain_id}
    const domainIdResource = domainsResource.addResource('{domain_id}');
    
    // GET /api/v1/domains/{domain_id} - Get specific domain
    domainIdResource.addMethod('GET', new apigateway.LambdaIntegration(domainHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
    });
    
    // PUT /api/v1/domains/{domain_id} - Update domain
    domainIdResource.addMethod('PUT', new apigateway.LambdaIntegration(domainHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestValidator: this.createRequestValidator('DomainPutValidator'),
    });
    
    // DELETE /api/v1/domains/{domain_id} - Delete domain
    domainIdResource.addMethod('DELETE', new apigateway.LambdaIntegration(domainHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
    });

    // Create Session Handler Lambda
    const sessionHandler = new PythonFunction(this, 'SessionHandler', {
      functionName: `${this.stackName}-SessionHandler`,
      entry: path.join(__dirname, '../../lambda/session-api'),
      runtime: lambda.Runtime.PYTHON_3_11,
      index: 'session_handler.py',
      handler: 'handler',
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        SESSIONS_TABLE: props.sessionsTable.tableName,
        MESSAGES_TABLE: props.messagesTable.tableName,
      },
      bundling: {
        assetExcludes: [
          '.venv',
          'venv',
          '__pycache__',
          '*.pyc',
          'test_*',
          '.pytest_cache',
          '.coverage',
        ],
      },
      description: 'Handles session CRUD operations with message grounding',
    });
    
    // Grant permissions
    props.sessionsTable.grantReadWriteData(sessionHandler);
    props.messagesTable.grantReadWriteData(sessionHandler);

    // 8. Session Management API - /api/v1/sessions
    const sessionsResource = apiV1.addResource('sessions');
    
    // POST /api/v1/sessions - Create session
    sessionsResource.addMethod('POST', new apigateway.LambdaIntegration(sessionHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestValidator: this.createRequestValidator('SessionPostValidator'),
      requestModels: {
        'application/json': this.createSessionModel(),
      },
    });
    
    // GET /api/v1/sessions - List sessions
    sessionsResource.addMethod('GET', new apigateway.LambdaIntegration(sessionHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestParameters: {
        'method.request.querystring.page': false,
        'method.request.querystring.limit': false,
      },
    });
    
    // /api/v1/sessions/{session_id}
    const sessionIdResource = sessionsResource.addResource('{session_id}');
    
    // GET /api/v1/sessions/{session_id} - Get specific session
    sessionIdResource.addMethod('GET', new apigateway.LambdaIntegration(sessionHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
    });
    
    // PUT /api/v1/sessions/{session_id} - Update session
    sessionIdResource.addMethod('PUT', new apigateway.LambdaIntegration(sessionHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestValidator: this.createRequestValidator('SessionPutValidator'),
    });
    
    // DELETE /api/v1/sessions/{session_id} - Delete session
    sessionIdResource.addMethod('DELETE', new apigateway.LambdaIntegration(sessionHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
    });

    // Create Report Handler Lambda
    const reportHandler = new PythonFunction(this, 'ReportHandler', {
      functionName: `${this.stackName}-ReportHandler`,
      entry: path.join(__dirname, '../../lambda/report-api'),
      runtime: lambda.Runtime.PYTHON_3_11,
      index: 'report_handler.py',
      handler: 'handler',
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        REPORTS_TABLE: props.reportsTable.tableName,
        ORCHESTRATOR_FUNCTION: `${this.stackName}-Orchestrator`,
      },
      bundling: {
        assetExcludes: [
          '.venv',
          'venv',
          '__pycache__',
          '*.pyc',
          'test_*',
          '.pytest_cache',
          '.coverage',
        ],
      },
      description: 'Handles report CRUD operations',
    });
    
    // Grant permissions
    props.reportsTable.grantReadWriteData(reportHandler);
    
    // Grant report handler permission to invoke orchestrator
    orchestratorHandler.grantInvoke(reportHandler);

    // 9. Report Management API - /api/v1/reports
    const reportsResource = apiV1.addResource('reports');
    
    // POST /api/v1/reports - Submit report
    reportsResource.addMethod('POST', new apigateway.LambdaIntegration(reportHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestValidator: this.createRequestValidator('ReportPostValidator'),
      requestModels: {
        'application/json': this.createReportModel(),
      },
    });
    
    // GET /api/v1/reports - List reports
    reportsResource.addMethod('GET', new apigateway.LambdaIntegration(reportHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestParameters: {
        'method.request.querystring.page': false,
        'method.request.querystring.limit': false,
        'method.request.querystring.domain_id': false,
      },
    });
    
    // /api/v1/reports/{incident_id}
    const reportIdResource = reportsResource.addResource('{incident_id}');
    
    // GET /api/v1/reports/{incident_id} - Get specific report
    reportIdResource.addMethod('GET', new apigateway.LambdaIntegration(reportHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
    });
    
    // PUT /api/v1/reports/{incident_id} - Update report
    reportIdResource.addMethod('PUT', new apigateway.LambdaIntegration(reportHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestValidator: this.createRequestValidator('ReportPutValidator'),
    });
    
    // DELETE /api/v1/reports/{incident_id} - Delete report
    reportIdResource.addMethod('DELETE', new apigateway.LambdaIntegration(reportHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
    });

    // Create Query Handler Lambda
    const queryApiHandler = new PythonFunction(this, 'QueryApiHandler', {
      functionName: `${this.stackName}-QueryApiHandler`,
      entry: path.join(__dirname, '../../lambda/query-api'),
      runtime: lambda.Runtime.PYTHON_3_11,
      index: 'query_handler.py',
      handler: 'handler',
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        QUERY_JOBS_TABLE: props.queryJobsTable.tableName,
      },
      bundling: {
        assetExcludes: [
          '.venv',
          'venv',
          '__pycache__',
          '*.pyc',
          'test_*',
          '.pytest_cache',
          '.coverage',
        ],
      },
      description: 'Handles query CRUD operations',
    });
    
    // Grant permissions
    props.queryJobsTable.grantReadWriteData(queryApiHandler);

    // 10. Query Management API - /api/v1/queries
    const queriesResource = apiV1.addResource('queries');
    
    // POST /api/v1/queries - Submit query
    queriesResource.addMethod('POST', new apigateway.LambdaIntegration(queryApiHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestValidator: this.createRequestValidator('QueryApiPostValidator'),
      requestModels: {
        'application/json': this.createQueryApiModel(),
      },
    });
    
    // GET /api/v1/queries - List queries
    queriesResource.addMethod('GET', new apigateway.LambdaIntegration(queryApiHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      requestParameters: {
        'method.request.querystring.page': false,
        'method.request.querystring.limit': false,
        'method.request.querystring.session_id': false,
      },
    });
    
    // /api/v1/queries/{query_id}
    const queryIdResource = queriesResource.addResource('{query_id}');
    
    // GET /api/v1/queries/{query_id} - Get specific query
    queryIdResource.addMethod('GET', new apigateway.LambdaIntegration(queryApiHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
    });
    
    // DELETE /api/v1/queries/{query_id} - Delete query
    queryIdResource.addMethod('DELETE', new apigateway.LambdaIntegration(queryApiHandler), {
      authorizer: this.authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
    });

    // Outputs
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: this.api.url,
      description: 'API Gateway URL',
      exportName: `${id}-ApiUrl`,
    });

    new cdk.CfnOutput(this, 'ApiId', {
      value: this.api.restApiId,
      description: 'API Gateway ID',
      exportName: `${id}-ApiId`,
    });

    // Store API URL in SSM Parameter Store
    new cdk.aws_ssm.StringParameter(this, 'ApiUrlParameter', {
      parameterName: '/app/api/url',
      stringValue: this.api.url,
      description: 'API Gateway URL',
    });
  }

  private createPlaceholderLambda(name: string, description: string): lambda.Function {
    return new lambda.Function(this, name, {
      functionName: `${this.stackName}-${name}`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.handler',
      code: lambda.Code.fromInline(`
def handler(event, context):
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': '{"message": "Placeholder endpoint - to be implemented"}'
    }
      `),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      description: description,
    });
  }

  private createRequestValidator(name: string): apigateway.RequestValidator {
    return new apigateway.RequestValidator(this, name, {
      restApi: this.api,
      requestValidatorName: name,
      validateRequestBody: true,
      validateRequestParameters: true,
    });
  }

  private createIngestModel(): apigateway.Model {
    return new apigateway.Model(this, 'IngestModel', {
      restApi: this.api,
      contentType: 'application/json',
      modelName: 'IngestModel',
      schema: {
        type: apigateway.JsonSchemaType.OBJECT,
        required: ['domain_id', 'text'],
        properties: {
          domain_id: { type: apigateway.JsonSchemaType.STRING },
          text: { type: apigateway.JsonSchemaType.STRING },
          images: {
            type: apigateway.JsonSchemaType.ARRAY,
            items: { type: apigateway.JsonSchemaType.STRING },
          },
        },
      },
    });
  }

  private createQueryModel(): apigateway.Model {
    return new apigateway.Model(this, 'QueryModel', {
      restApi: this.api,
      contentType: 'application/json',
      modelName: 'QueryModel',
      schema: {
        type: apigateway.JsonSchemaType.OBJECT,
        required: ['domain_id', 'question'],
        properties: {
          domain_id: { type: apigateway.JsonSchemaType.STRING },
          question: { type: apigateway.JsonSchemaType.STRING },
        },
      },
    });
  }

  private createConfigModel(): apigateway.Model {
    return new apigateway.Model(this, 'ConfigModel', {
      restApi: this.api,
      contentType: 'application/json',
      modelName: 'ConfigModel',
      schema: {
        type: apigateway.JsonSchemaType.OBJECT,
        required: ['type', 'config'],
        properties: {
          type: { type: apigateway.JsonSchemaType.STRING },
          config: { type: apigateway.JsonSchemaType.OBJECT },
        },
      },
    });
  }

  private createAgentModel(): apigateway.Model {
    return new apigateway.Model(this, 'AgentModel', {
      restApi: this.api,
      contentType: 'application/json',
      modelName: 'AgentModel',
      schema: {
        type: apigateway.JsonSchemaType.OBJECT,
        required: ['agent_name', 'agent_class', 'system_prompt', 'output_schema'],
        properties: {
          agent_name: { type: apigateway.JsonSchemaType.STRING },
          agent_class: { 
            type: apigateway.JsonSchemaType.STRING,
            enum: ['ingestion', 'query', 'management']
          },
          system_prompt: { type: apigateway.JsonSchemaType.STRING },
          tools: {
            type: apigateway.JsonSchemaType.ARRAY,
            items: { type: apigateway.JsonSchemaType.STRING },
          },
          agent_dependencies: {
            type: apigateway.JsonSchemaType.ARRAY,
            items: { type: apigateway.JsonSchemaType.STRING },
          },
          output_schema: { type: apigateway.JsonSchemaType.OBJECT },
          description: { type: apigateway.JsonSchemaType.STRING },
          enabled: { type: apigateway.JsonSchemaType.BOOLEAN },
        },
      },
    });
  }

  private createDomainModel(): apigateway.Model {
    return new apigateway.Model(this, 'DomainModel', {
      restApi: this.api,
      contentType: 'application/json',
      modelName: 'DomainModel',
      schema: {
        type: apigateway.JsonSchemaType.OBJECT,
        required: ['domain_id', 'domain_name', 'ingestion_playbook', 'query_playbook', 'management_playbook'],
        properties: {
          domain_id: { type: apigateway.JsonSchemaType.STRING },
          domain_name: { type: apigateway.JsonSchemaType.STRING },
          description: { type: apigateway.JsonSchemaType.STRING },
          ingestion_playbook: {
            type: apigateway.JsonSchemaType.OBJECT,
            required: ['agent_execution_graph'],
            properties: {
              agent_execution_graph: {
                type: apigateway.JsonSchemaType.OBJECT,
                required: ['nodes', 'edges'],
                properties: {
                  nodes: {
                    type: apigateway.JsonSchemaType.ARRAY,
                    items: { type: apigateway.JsonSchemaType.STRING },
                  },
                  edges: {
                    type: apigateway.JsonSchemaType.ARRAY,
                    items: {
                      type: apigateway.JsonSchemaType.OBJECT,
                      properties: {
                        from: { type: apigateway.JsonSchemaType.STRING },
                        to: { type: apigateway.JsonSchemaType.STRING },
                      },
                    },
                  },
                },
              },
            },
          },
          query_playbook: {
            type: apigateway.JsonSchemaType.OBJECT,
            required: ['agent_execution_graph'],
            properties: {
              agent_execution_graph: {
                type: apigateway.JsonSchemaType.OBJECT,
                required: ['nodes', 'edges'],
                properties: {
                  nodes: {
                    type: apigateway.JsonSchemaType.ARRAY,
                    items: { type: apigateway.JsonSchemaType.STRING },
                  },
                  edges: {
                    type: apigateway.JsonSchemaType.ARRAY,
                    items: {
                      type: apigateway.JsonSchemaType.OBJECT,
                      properties: {
                        from: { type: apigateway.JsonSchemaType.STRING },
                        to: { type: apigateway.JsonSchemaType.STRING },
                      },
                    },
                  },
                },
              },
            },
          },
          management_playbook: {
            type: apigateway.JsonSchemaType.OBJECT,
            required: ['agent_execution_graph'],
            properties: {
              agent_execution_graph: {
                type: apigateway.JsonSchemaType.OBJECT,
                required: ['nodes', 'edges'],
                properties: {
                  nodes: {
                    type: apigateway.JsonSchemaType.ARRAY,
                    items: { type: apigateway.JsonSchemaType.STRING },
                  },
                  edges: {
                    type: apigateway.JsonSchemaType.ARRAY,
                    items: {
                      type: apigateway.JsonSchemaType.OBJECT,
                      properties: {
                        from: { type: apigateway.JsonSchemaType.STRING },
                        to: { type: apigateway.JsonSchemaType.STRING },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
    });
  }

  private createSessionModel(): apigateway.Model {
    return new apigateway.Model(this, 'SessionModel', {
      restApi: this.api,
      contentType: 'application/json',
      modelName: 'SessionModel',
      schema: {
        type: apigateway.JsonSchemaType.OBJECT,
        required: ['domain_id'],
        properties: {
          domain_id: { type: apigateway.JsonSchemaType.STRING },
          title: { type: apigateway.JsonSchemaType.STRING },
        },
      },
    });
  }

  private createReportModel(): apigateway.Model {
    return new apigateway.Model(this, 'ReportModel', {
      restApi: this.api,
      contentType: 'application/json',
      modelName: 'ReportModel',
      schema: {
        type: apigateway.JsonSchemaType.OBJECT,
        required: ['domain_id', 'text'],
        properties: {
          domain_id: { type: apigateway.JsonSchemaType.STRING },
          text: { type: apigateway.JsonSchemaType.STRING },
          images: {
            type: apigateway.JsonSchemaType.ARRAY,
            items: { type: apigateway.JsonSchemaType.STRING },
          },
          source: { type: apigateway.JsonSchemaType.STRING },
        },
      },
    });
  }

  private createQueryApiModel(): apigateway.Model {
    return new apigateway.Model(this, 'QueryApiModel', {
      restApi: this.api,
      contentType: 'application/json',
      modelName: 'QueryApiModel',
      schema: {
        type: apigateway.JsonSchemaType.OBJECT,
        required: ['session_id', 'domain_id', 'question'],
        properties: {
          session_id: { type: apigateway.JsonSchemaType.STRING },
          domain_id: { type: apigateway.JsonSchemaType.STRING },
          question: { type: apigateway.JsonSchemaType.STRING },
        },
      },
    });
  }
}
