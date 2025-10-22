#!/usr/bin/env python3
"""Fetch CloudWatch logs for failed Lambda functions"""
import boto3
import json
from datetime import datetime, timedelta

# Initialize CloudWatch Logs client
logs_client = boto3.client('logs', region_name='us-east-1')

# Lambda functions to check
lambda_functions = [
    'MultiAgentOrchestration-dev-Api-AgentHandler',
    'MultiAgentOrchestration-dev-Api-DomainHandler',
    'MultiAgentOrchestration-dev-Orchestration-IngestHandler',
    'MultiAgentOrchestration-dev-Orchestration-QueryHandler'
]

def fetch_recent_logs(function_name, minutes=30):
    """Fetch recent logs for a Lambda function"""
    log_group = f'/aws/lambda/{function_name}'
    
    try:
        # Get log streams
        response = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        if not response['logStreams']:
            print(f"\n{'='*80}")
            print(f"Function: {function_name}")
            print(f"No log streams found")
            return
        
        print(f"\n{'='*80}")
        print(f"Function: {function_name}")
        print(f"{'='*80}")
        
        # Get events from the most recent stream
        for stream in response['logStreams'][:2]:  # Check last 2 streams
            stream_name = stream['logStreamName']
            print(f"\nLog Stream: {stream_name}")
            print(f"{'-'*80}")
            
            try:
                events_response = logs_client.get_log_events(
                    logGroupName=log_group,
                    logStreamName=stream_name,
                    limit=50,
                    startFromHead=False
                )
                
                events = events_response['events']
                if not events:
                    print("No events in this stream")
                    continue
                
                # Print last 20 events
                for event in events[-20:]:
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                    message = event['message'].strip()
                    print(f"[{timestamp}] {message}")
                    
            except Exception as e:
                print(f"Error fetching events: {str(e)}")
                
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"Function: {function_name}")
        print(f"Error: {str(e)}")

# Fetch logs for each function
print("CLOUDWATCH LOGS FOR FAILED LAMBDA FUNCTIONS")
print("="*80)

for function_name in lambda_functions:
    fetch_recent_logs(function_name)

print(f"\n{'='*80}")
print("Log fetch completed")
