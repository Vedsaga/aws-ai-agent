import * as cdk from 'aws-cdk-lib';
import * as appsync from 'aws-cdk-lib/aws-appsync';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import * as path from 'path';
import * as fs from 'fs';

interface RealtimeStackProps extends cdk.StackProps {
  userSessionsTable: dynamodb.ITable;
}

export class RealtimeStack extends cdk.Stack {
  public readonly api: appsync.GraphqlApi;
  public readonly statusPublisherFunction: lambda.Function;

  constructor(scope: Construct, id: string, props: RealtimeStackProps) {
    super(scope, id, props);

    // Read GraphQL schema
    const schemaPath = path.join(__dirname, '../../lambda/realtime/schema.graphql');
    const schemaDefinition = fs.readFileSync(schemaPath, 'utf8');

    // Create AppSync API
    this.api = new appsync.GraphqlApi(this, 'RealtimeApi', {
      name: 'multi-agent-realtime-api',
      schema: appsync.SchemaFile.fromAsset(schemaPath),
      authorizationConfig: {
        defaultAuthorization: {
          authorizationType: appsync.AuthorizationType.IAM,
        },
        additionalAuthorizationModes: [
          {
            authorizationType: appsync.AuthorizationType.API_KEY,
            apiKeyConfig: {
              expires: cdk.Expiration.after(cdk.Duration.days(365)),
            },
          },
        ],
      },
      xrayEnabled: true,
      logConfig: {
        fieldLogLevel: appsync.FieldLogLevel.ALL,
      },
    });

    // Create DynamoDB data source for connection tracking
    const connectionDataSource = this.api.addDynamoDbDataSource(
      'ConnectionDataSource',
      props.userSessionsTable
    );

    // Create None data source for mutations
    const noneDataSource = this.api.addNoneDataSource('NoneDataSource');

    // Resolver for publishStatus mutation
    noneDataSource.createResolver('PublishStatusResolver', {
      typeName: 'Mutation',
      fieldName: 'publishStatus',
      requestMappingTemplate: appsync.MappingTemplate.fromString(`
        {
          "version": "2017-02-28",
          "payload": {
            "jobId": $util.toJson($ctx.args.jobId),
            "userId": $util.toJson($ctx.args.userId),
            "agentName": $util.toJson($ctx.args.agentName),
            "status": $util.toJson($ctx.args.status),
            "message": $util.toJson($ctx.args.message),
            "timestamp": "$util.time.nowISO8601()",
            "metadata": $util.toJson($ctx.args.metadata)
          }
        }
      `),
      responseMappingTemplate: appsync.MappingTemplate.fromString(`
        $util.toJson($ctx.result)
      `),
    });

    // Create status publisher Lambda function
    this.statusPublisherFunction = new lambda.Function(this, 'StatusPublisher', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'status_publisher.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/realtime')),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      environment: {
        APPSYNC_API_URL: this.api.graphqlUrl,
        APPSYNC_API_ID: this.api.apiId,
        USER_SESSIONS_TABLE: props.userSessionsTable.tableName,
        AWS_REGION: this.region,
      },
      tracing: lambda.Tracing.ACTIVE,
    });

    // Grant permissions
    props.userSessionsTable.grantReadData(this.statusPublisherFunction);
    
    // Grant AppSync mutation permissions to Lambda
    this.statusPublisherFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['appsync:GraphQL'],
        resources: [
          `${this.api.arn}/types/Mutation/fields/publishStatus`,
        ],
      })
    );

    // Outputs
    new cdk.CfnOutput(this, 'AppSyncApiUrl', {
      value: this.api.graphqlUrl,
      description: 'AppSync GraphQL API URL',
    });

    new cdk.CfnOutput(this, 'AppSyncApiKey', {
      value: this.api.apiKey || 'N/A',
      description: 'AppSync API Key',
    });

    new cdk.CfnOutput(this, 'AppSyncApiId', {
      value: this.api.apiId,
      description: 'AppSync API ID',
    });

    new cdk.CfnOutput(this, 'StatusPublisherFunctionArn', {
      value: this.statusPublisherFunction.functionArn,
      description: 'Status Publisher Lambda Function ARN',
    });
  }
}
