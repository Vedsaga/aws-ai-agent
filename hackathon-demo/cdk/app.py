#!/usr/bin/env python3
"""
Minimal CDK stack for hackathon demo
DynamoDB + Lambda + API Gateway (no auth)
"""
from aws_cdk import (
    App, Stack, Duration,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_events as events,
    aws_iam as iam,
    RemovalPolicy
)
from constructs import Construct


class HackathonDemoStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # DynamoDB table for reports
        table = dynamodb.Table(
            self, 'ReportsTable',
            table_name='civic-reports',
            partition_key=dynamodb.Attribute(
                name='report_id',
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY  # For demo only
        )
        
        # Event bus for real-time status
        event_bus = events.EventBus(
            self, 'StatusEventBus',
            event_bus_name='domainflow-status'
        )
        
        # Lambda orchestrator
        orchestrator = lambda_.Function(
            self, 'Orchestrator',
            function_name='domainflow-orchestrator',
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler='orchestrator.lambda_handler',
            code=lambda_.Code.from_asset('../lambda'),
            timeout=Duration.seconds(60),
            memory_size=512,
            environment={
                'TABLE_NAME': table.table_name,
                'EVENT_BUS': event_bus.event_bus_name,
                'ORCHESTRATOR_MODEL': 'us.amazon.nova-pro-v1:0',
                'AGENT_MODEL': 'us.amazon.nova-lite-v1:0'
            }
        )
        
        # Grant permissions
        table.grant_read_write_data(orchestrator)
        event_bus.grant_put_events_to(orchestrator)
        
        # Grant Bedrock access
        orchestrator.add_to_role_policy(
            iam.PolicyStatement(
                actions=['bedrock:InvokeModel', 'bedrock:Converse'],
                resources=['*']
            )
        )
        
        # API Gateway (no auth for demo)
        api = apigw.RestApi(
            self, 'Api',
            rest_api_name='domainflow-api',
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS
            )
        )
        
        # POST /orchestrate
        orchestrate = api.root.add_resource('orchestrate')
        orchestrate.add_method(
            'POST',
            apigw.LambdaIntegration(orchestrator)
        )
        
        # GET /reports (list all)
        reports = api.root.add_resource('reports')
        
        list_reports = lambda_.Function(
            self, 'ListReports',
            function_name='domainflow-list-reports',
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler='index.lambda_handler',
            code=lambda_.Code.from_inline(f"""
import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('{table.table_name}')

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    try:
        response = table.scan()
        items = response.get('Items', [])
        
        return {{
            'statusCode': 200,
            'headers': {{
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }},
            'body': json.dumps({{'reports': items}}, default=decimal_default)
        }}
    except Exception as e:
        return {{
            'statusCode': 500,
            'body': json.dumps({{'error': str(e)}})
        }}
"""),
            timeout=Duration.seconds(10)
        )
        
        table.grant_read_data(list_reports)
        reports.add_method('GET', apigw.LambdaIntegration(list_reports))
        
        # Output API endpoint
        from aws_cdk import CfnOutput
        CfnOutput(
            self, 'ApiEndpoint',
            value=api.url,
            description='API Gateway endpoint URL'
        )


app = App()
HackathonDemoStack(app, 'DomainFlowDemo')
app.synth()
