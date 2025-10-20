#!/usr/bin/env python3
"""
Fix Lambda function handlers and update code
"""

import boto3
import zipfile
import io
import os

lambda_client = boto3.client('lambda')

def create_zip_from_file(file_path, handler_name):
    """Create a zip file in memory from a single Python file"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add the file with the correct name for the handler
        zip_file.write(file_path, handler_name)
    zip_buffer.seek(0)
    return zip_buffer.read()

def update_lambda(function_name, file_path, handler):
    """Update Lambda function code and handler"""
    try:
        # Extract just the filename for the zip
        handler_file = handler.split('.')[0] + '.py'
        
        # Create zip with correct filename
        zip_content = create_zip_from_file(file_path, handler_file)
        
        # Update function code
        print(f"Updating code for {function_name}...")
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        # Wait for update to complete
        waiter = lambda_client.get_waiter('function_updated')
        waiter.wait(FunctionName=function_name)
        
        # Update handler configuration
        print(f"Updating handler to {handler}...")
        response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Handler=handler
        )
        
        print(f"✓ Updated {function_name}")
        print(f"  Handler: {response['Handler']}")
        print(f"  Last Modified: {response['LastModified']}")
        return True
    except Exception as e:
        print(f"✗ Failed to update {function_name}: {str(e)}")
        return False

print("="*60)
print("FIXING LAMBDA HANDLERS")
print("="*60)

# Update Ingest Handler
print("\n1. Ingest Handler")
update_lambda(
    'MultiAgentOrchestration-dev-Api-IngestHandler',
    'infrastructure/lambda/orchestration/ingest_handler_simple.py',
    'ingest_handler_simple.handler'
)

# Update Query Handler
print("\n2. Query Handler")
update_lambda(
    'MultiAgentOrchestration-dev-Api-QueryHandler',
    'infrastructure/lambda/orchestration/query_handler_simple.py',
    'query_handler_simple.handler'
)

print("\n" + "="*60)
print("✓ ALL LAMBDA FUNCTIONS UPDATED!")
print("="*60)
