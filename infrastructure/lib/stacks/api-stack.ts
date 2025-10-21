import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';
import * as path from 'path';

interface ApiStackProps extends cdk.StackProps {
  userPool: cognito.UserPool;
  userPoolClient: cognito.UserPoolClient;
  configurationsTable: dynamodb.Table;
  configBackupBucket: s3.Bucket;
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
    const ingestHandler = new lambda.Function(this, 'IngestHandler', {
      functionName: `${this.stackName}-IngestHandler`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'ingest_handler_simple.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/orchestration')),
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        INCIDENTS_TABLE: `${this.stackName.replace('-Api', '-Data')}-Incidents`,
        BEDROCK_DEFAULT_MODEL: process.env.BEDROCK_DEFAULT_MODEL || 'anthropic.claude-3-sonnet-20240229-v1:0',
        BEDROCK_AGENT_MODEL: process.env.BEDROCK_AGENT_MODEL || 'amazon.nova-micro-v1:0',
      },
      description: 'Handles data ingestion requests',
    });
    
    const queryHandler = new lambda.Function(this, 'QueryHandler', {
      functionName: `${this.stackName}-QueryHandler`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'query_handler_simple.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/orchestration')),
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        QUERIES_TABLE: `${this.stackName.replace('-Api', '-Data')}-Queries`,
        BEDROCK_DEFAULT_MODEL: process.env.BEDROCK_DEFAULT_MODEL || 'anthropic.claude-3-sonnet-20240229-v1:0',
        BEDROCK_AGENT_MODEL: process.env.BEDROCK_AGENT_MODEL || 'amazon.nova-micro-v1:0',
      },
      description: 'Handles query requests',
    });
    
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
    const configHandler = new lambda.Function(this, 'ConfigHandler', {
      functionName: `${this.stackName}-ConfigHandler`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'config_handler.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/config-api')),
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        CONFIGURATIONS_TABLE: props.configurationsTable.tableName,
        CONFIG_BACKUP_BUCKET: props.configBackupBucket.bucketName,
      },
      description: 'Handles configuration CRUD operations for agents, playbooks, dependency graphs, and templates',
    });
    
    // Grant permissions to config handler
    props.configurationsTable.grantReadWriteData(configHandler);
    props.configBackupBucket.grantReadWrite(configHandler);

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
}
