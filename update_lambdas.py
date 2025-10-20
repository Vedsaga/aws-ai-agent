#!/usr/bin/env python3
"""
Update Lambda functions directly with new code
"""

import boto3
import zipfile
import io
import os

lambda_client = boto3.client('lambda')

def create_zip_from_file(file_path):
    """Create a zip file in memory from a single Python file"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(file_path, os.path.basename(file_path))
    zip_buffer.seek(0)
    return zip_buffer.read()

def update_lambda_function(function_name, zip_content):
    """Update Lambda function code"""
    try:
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        print(f"✓ Updated {function_name}")
        print(f"  Last Modified: {response['LastModified']}")
        print(f"  Version: {response['Version']}")
        return True
    except Exception as e:
        print(f"✗ Failed to update {function_name}: {str(e)}")
        return False

# Update Ingest Handler
print("Updating Ingest Handler...")
ingest_zip = create_zip_from_file('infrastructure/lambda/orchestration/ingest_handler_simple.py')
update_lambda_function('MultiAgentOrchestration-dev-Api-IngestHandler', ingest_zip)

# Update Query Handler
print("\nUpdating Query Handler...")
query_zip = create_zip_from_file('infrastructure/lambda/orchestration/query_handler_simple.py')
update_lambda_function('MultiAgentOrchestration-dev-Api-QueryHandler', query_zip)

print("\n✓ Lambda functions updated successfully!")
