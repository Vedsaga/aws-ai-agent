import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as sfn from "aws-cdk-lib/aws-stepfunctions";
import * as iam from "aws-cdk-lib/aws-iam";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as logs from "aws-cdk-lib/aws-logs";
import { Construct } from "constructs";
import * as path from "path";

interface OrchestrationStackProps extends cdk.StackProps {
  agentConfigsTable: dynamodb.Table;
  playbookConfigsTable: dynamodb.Table;
  dependencyGraphsTable: dynamodb.Table;
  dbSecretArn: string;
  opensearchEndpoint: string;
  eventBusName: string;
  statusPublisherFunction?: lambda.IFunction;
}

export class OrchestrationStack extends cdk.Stack {
  public readonly stateMachine: sfn.StateMachine;

  constructor(scope: Construct, id: string, props: OrchestrationStackProps) {
    super(scope, id, props);

    // Create Lambda execution role with necessary permissions
    const orchestrationRole = new iam.Role(this, "OrchestrationRole", {
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "service-role/AWSLambdaBasicExecutionRole",
        ),
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "service-role/AWSLambdaVPCAccessExecutionRole",
        ),
      ],
    });

    // Grant DynamoDB permissions
    props.agentConfigsTable.grantReadData(orchestrationRole);
    props.playbookConfigsTable.grantReadData(orchestrationRole);
    props.dependencyGraphsTable.grantReadData(orchestrationRole);

    // Grant Bedrock permissions
    orchestrationRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["bedrock:InvokeModel"],
        resources: ["*"],
      }),
    );

    // Grant Secrets Manager permissions
    orchestrationRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["secretsmanager:GetSecretValue"],
        resources: [props.dbSecretArn],
      }),
    );

    // Grant EventBridge permissions
    orchestrationRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["events:PutEvents"],
        resources: [
          `arn:aws:events:${this.region}:${this.account}:event-bus/${props.eventBusName}`,
        ],
      }),
    );

    // Grant Lambda invoke permissions (for agent invoker)
    orchestrationRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["lambda:InvokeFunction"],
        resources: [
          `arn:aws:lambda:${this.region}:${this.account}:function:*Agent*`,
        ],
      }),
    );

    // Common Lambda environment variables
    const commonEnv: { [key: string]: string } = {
      AGENT_CONFIGS_TABLE: props.agentConfigsTable.tableName,
      PLAYBOOK_CONFIGS_TABLE: props.playbookConfigsTable.tableName,
      DEPENDENCY_GRAPHS_TABLE: props.dependencyGraphsTable.tableName,
      DB_SECRET_ARN: props.dbSecretArn,
      OPENSEARCH_ENDPOINT: props.opensearchEndpoint,
      EVENT_BUS_NAME: props.eventBusName,
      // Bedrock model configuration from environment variables
      BEDROCK_DEFAULT_MODEL: process.env.BEDROCK_DEFAULT_MODEL || 'anthropic.claude-3-sonnet-20240229-v1:0',
      BEDROCK_AGENT_MODEL: process.env.BEDROCK_AGENT_MODEL || 'amazon.nova-micro-v1:0',
      BEDROCK_ORCHESTRATOR_MODEL: process.env.BEDROCK_ORCHESTRATOR_MODEL || 'amazon.nova-pro-v1:0',
      BEDROCK_EMBEDDING_MODEL: process.env.BEDROCK_EMBEDDING_MODEL || 'amazon.titan-embed-text-v1',
    };

    // Add status publisher function ARN if available
    if (props.statusPublisherFunction) {
      commonEnv.STATUS_PUBLISHER_FUNCTION =
        props.statusPublisherFunction.functionName;

      // Grant orchestrator permission to invoke status publisher
      props.statusPublisherFunction.grantInvoke(orchestrationRole);
    }

    // Lambda Layer for common dependencies
    const orchestrationLayer = new lambda.LayerVersion(
      this,
      "OrchestrationLayer",
      {
        code: lambda.Code.fromAsset(
          path.join(__dirname, "../../lambda/orchestration"),
          {
            bundling: {
              image: lambda.Runtime.PYTHON_3_11.bundlingImage,
              command: [
                "bash",
                "-c",
                "pip install -r requirements.txt -t /asset-output/python && cp -r . /asset-output/python",
              ],
            },
          },
        ),
        compatibleRuntimes: [lambda.Runtime.PYTHON_3_11],
        description: "Orchestration dependencies",
      },
    );

    // 1. Load Playbook Lambda
    const loadPlaybookFunction = new lambda.Function(
      this,
      "LoadPlaybookFunction",
      {
        functionName: `${id}-LoadPlaybook`,
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: "load_playbook.handler",
        code: lambda.Code.fromAsset(
          path.join(__dirname, "../../lambda/orchestration"),
        ),
        timeout: cdk.Duration.seconds(30),
        memorySize: 256,
        environment: commonEnv,
        role: orchestrationRole,
        description: "Loads playbook configuration from DynamoDB",
      },
    );

    // 2. Load Dependency Graph Lambda
    const loadDependencyGraphFunction = new lambda.Function(
      this,
      "LoadDependencyGraphFunction",
      {
        functionName: `${id}-LoadDependencyGraph`,
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: "load_dependency_graph.handler",
        code: lambda.Code.fromAsset(
          path.join(__dirname, "../../lambda/orchestration"),
        ),
        timeout: cdk.Duration.seconds(30),
        memorySize: 256,
        environment: commonEnv,
        role: orchestrationRole,
        description: "Loads dependency graph configuration from DynamoDB",
      },
    );

    // 3. Build Execution Plan Lambda
    const buildExecutionPlanFunction = new lambda.Function(
      this,
      "BuildExecutionPlanFunction",
      {
        functionName: `${id}-BuildExecutionPlan`,
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: "build_execution_plan.handler",
        code: lambda.Code.fromAsset(
          path.join(__dirname, "../../lambda/orchestration"),
        ),
        timeout: cdk.Duration.seconds(30),
        memorySize: 256,
        environment: commonEnv,
        role: orchestrationRole,
        description: "Builds execution plan using topological sort",
      },
    );

    // 4. Agent Invoker Lambda
    const agentInvokerFunction = new lambda.Function(
      this,
      "AgentInvokerFunction",
      {
        functionName: `${id}-AgentInvoker`,
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: "agent_invoker.handler",
        code: lambda.Code.fromAsset(
          path.join(__dirname, "../../lambda/orchestration"),
        ),
        timeout: cdk.Duration.minutes(5),
        memorySize: 512,
        environment: {
          ...commonEnv,
          AGENT_LAMBDA_PREFIX: `${id.replace("-Orchestration", "")}-Agent-`,
        },
        role: orchestrationRole,
        description: "Routes execution to specific agents by ID",
      },
    );

    // 5. Result Aggregator Lambda
    const resultAggregatorFunction = new lambda.Function(
      this,
      "ResultAggregatorFunction",
      {
        functionName: `${id}-ResultAggregator`,
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: "result_aggregator.handler",
        code: lambda.Code.fromAsset(
          path.join(__dirname, "../../lambda/orchestration"),
        ),
        timeout: cdk.Duration.seconds(30),
        memorySize: 256,
        environment: commonEnv,
        role: orchestrationRole,
        description: "Aggregates results from all executed agents",
      },
    );

    // 6. Validator Lambda
    const validatorFunction = new lambda.Function(this, "ValidatorFunction", {
      functionName: `${id}-Validator`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: "validator.handler",
      code: lambda.Code.fromAsset(
        path.join(__dirname, "../../lambda/orchestration"),
      ),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      environment: commonEnv,
      role: orchestrationRole,
      description: "Validates agent outputs against schemas",
    });

    // 7. Synthesizer Lambda
    const synthesizerFunction = new lambda.Function(
      this,
      "SynthesizerFunction",
      {
        functionName: `${id}-Synthesizer`,
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: "synthesizer.handler",
        code: lambda.Code.fromAsset(
          path.join(__dirname, "../../lambda/orchestration"),
        ),
        timeout: cdk.Duration.seconds(30),
        memorySize: 256,
        environment: commonEnv,
        role: orchestrationRole,
        description: "Synthesizes validated outputs into single document",
      },
    );

    // 8. Save Results Lambda
    const saveResultsFunction = new lambda.Function(
      this,
      "SaveResultsFunction",
      {
        functionName: `${id}-SaveResults`,
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: "save_results.handler",
        code: lambda.Code.fromAsset(
          path.join(__dirname, "../../lambda/orchestration"),
        ),
        timeout: cdk.Duration.minutes(2),
        memorySize: 512,
        environment: commonEnv,
        role: orchestrationRole,
        description: "Saves results to RDS, OpenSearch, and triggers events",
      },
    );

    // Create Step Functions state machine role
    const stateMachineRole = new iam.Role(this, "StateMachineRole", {
      assumedBy: new iam.ServicePrincipal("states.amazonaws.com"),
    });

    // Grant Lambda invoke permissions to state machine
    [
      loadPlaybookFunction,
      loadDependencyGraphFunction,
      buildExecutionPlanFunction,
      agentInvokerFunction,
      resultAggregatorFunction,
      validatorFunction,
      synthesizerFunction,
      saveResultsFunction,
    ].forEach((fn) => fn.grantInvoke(stateMachineRole));

    // Load state machine definition
    const stateMachineDefinition = require("../../lambda/orchestration/state_machine_definition.json");

    // Replace placeholders with actual ARNs
    const definitionString = JSON.stringify(stateMachineDefinition)
      .replace(
        /\$\{LoadPlaybookFunctionArn\}/g,
        loadPlaybookFunction.functionArn,
      )
      .replace(
        /\$\{LoadDependencyGraphFunctionArn\}/g,
        loadDependencyGraphFunction.functionArn,
      )
      .replace(
        /\$\{BuildExecutionPlanFunctionArn\}/g,
        buildExecutionPlanFunction.functionArn,
      )
      .replace(
        /\$\{AgentInvokerFunctionArn\}/g,
        agentInvokerFunction.functionArn,
      )
      .replace(
        /\$\{ResultAggregatorFunctionArn\}/g,
        resultAggregatorFunction.functionArn,
      )
      .replace(/\$\{ValidatorFunctionArn\}/g, validatorFunction.functionArn)
      .replace(/\$\{SynthesizerFunctionArn\}/g, synthesizerFunction.functionArn)
      .replace(
        /\$\{SaveResultsFunctionArn\}/g,
        saveResultsFunction.functionArn,
      );

    // Create Step Functions state machine
    this.stateMachine = new sfn.StateMachine(
      this,
      "OrchestrationStateMachine",
      {
        stateMachineName: `${id}-StateMachine`,
        definitionBody: sfn.DefinitionBody.fromString(definitionString),
        role: stateMachineRole,
        logs: {
          destination: new logs.LogGroup(this, "StateMachineLogGroup", {
            logGroupName: `/aws/stepfunctions/${id}`,
            retention: logs.RetentionDays.ONE_WEEK,
          }),
          level: sfn.LogLevel.ALL,
          includeExecutionData: true,
        },
        tracingEnabled: true,
        timeout: cdk.Duration.minutes(15),
      },
    );

    // Outputs
    new cdk.CfnOutput(this, "StateMachineArn", {
      value: this.stateMachine.stateMachineArn,
      description: "Orchestration State Machine ARN",
      exportName: `${id}-StateMachineArn`,
    });

    new cdk.CfnOutput(this, "LoadPlaybookFunctionArn", {
      value: loadPlaybookFunction.functionArn,
      description: "Load Playbook Function ARN",
    });

    new cdk.CfnOutput(this, "AgentInvokerFunctionArn", {
      value: agentInvokerFunction.functionArn,
      description: "Agent Invoker Function ARN",
    });
  }
}
