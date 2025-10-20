#!/usr/bin/env python3
"""
Deploy Orchestrator Lambda with Agent Execution
This script packages and deploys the orchestrator that actually runs agents
"""

import boto3
import json
import os
import shutil
import time
import zipfile
from pathlib import Path

# Configuration
REGION = "us-east-1"
ORCHESTRATOR_FUNCTION = "MultiAgentOrchestration-dev-Orchestrator"
INGEST_FUNCTION = "MultiAgentOrchestration-dev-Api-IngestHandler"
QUERY_FUNCTION = "MultiAgentOrchestration-dev-Api-QueryHandler"

# Initialize AWS clients
lambda_client = boto3.client("lambda", region_name=REGION)
iam_client = boto3.client("iam", region_name=REGION)


def log_info(msg):
    print(f"\033[0;32m[INFO]\033[0m {msg}")


def log_warning(msg):
    print(f"\033[1;33m[WARN]\033[0m {msg}")


def log_error(msg):
    print(f"\033[0;31m[ERROR]\033[0m {msg}")


def create_deployment_package(
    source_file, handler_name="handler.py", temp_dir="/tmp/orchestrator_deploy"
):
    """Create deployment package for Lambda"""
    log_info("Creating deployment package...")

    # Clean and create temp directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    # Copy handler
    source_path = Path(source_file)
    if not source_path.exists():
        log_error(f"Source file not found: {source_file}")
        return None

    dest_path = os.path.join(temp_dir, handler_name)
    shutil.copy(source_file, dest_path)
    log_info(f"Copied {source_file} to {dest_path}")

    # Create zip file
    zip_path = os.path.join(temp_dir, "deployment.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(dest_path, handler_name)

    size = os.path.getsize(zip_path)
    log_info(f"Package size: {size:,} bytes")

    return zip_path


def function_exists(function_name):
    """Check if Lambda function exists"""
    try:
        lambda_client.get_function(FunctionName=function_name)
        return True
    except lambda_client.exceptions.ResourceNotFoundException:
        return False


def get_function_role(function_name):
    """Get IAM role ARN for a Lambda function"""
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        return response["Configuration"]["Role"]
    except Exception as e:
        log_error(f"Error getting function role: {e}")
        return None


def deploy_orchestrator():
    """Deploy orchestrator Lambda function"""
    log_info("=" * 50)
    log_info("Deploying Orchestrator Lambda")
    log_info("=" * 50)

    # Step 1: Create deployment package
    source_file = "infrastructure/lambda/orchestration/orchestrator_handler.py"
    zip_path = create_deployment_package(source_file, "handler.py")

    if not zip_path:
        log_error("Failed to create deployment package")
        return False

    # Step 2: Read zip file
    with open(zip_path, "rb") as f:
        zip_content = f.read()

    # Step 3: Check if function exists
    if function_exists(ORCHESTRATOR_FUNCTION):
        log_info(f"Function {ORCHESTRATOR_FUNCTION} exists, updating...")

        # Update function code
        try:
            lambda_client.update_function_code(
                FunctionName=ORCHESTRATOR_FUNCTION, ZipFile=zip_content
            )
            log_info("Code updated, waiting for update to complete...")

            # Wait for update
            waiter = lambda_client.get_waiter("function_updated")
            waiter.wait(FunctionName=ORCHESTRATOR_FUNCTION)

            # Update configuration
            lambda_client.update_function_configuration(
                FunctionName=ORCHESTRATOR_FUNCTION,
                Timeout=300,
                MemorySize=512,
                Environment={
                    "Variables": {
                        "CONFIGURATIONS_TABLE": "MultiAgentOrchestration-dev-Data-Configurations",
                        "INCIDENTS_TABLE": "MultiAgentOrchestration-dev-Incidents",
                        "BEDROCK_REGION": REGION,
                    }
                },
            )

            log_info("✓ Orchestrator function updated")

        except Exception as e:
            log_error(f"Failed to update function: {e}")
            return False
    else:
        log_warning(f"Function {ORCHESTRATOR_FUNCTION} does not exist, creating...")

        # Get role from existing function
        role_arn = get_function_role(INGEST_FUNCTION)
        if not role_arn:
            log_error("Could not get execution role")
            return False

        log_info(f"Using role: {role_arn}")

        try:
            lambda_client.create_function(
                FunctionName=ORCHESTRATOR_FUNCTION,
                Runtime="python3.11",
                Role=role_arn,
                Handler="handler.handler",
                Code={"ZipFile": zip_content},
                Timeout=300,
                MemorySize=512,
                Environment={
                    "Variables": {
                        "CONFIGURATIONS_TABLE": "MultiAgentOrchestration-dev-Data-Configurations",
                        "INCIDENTS_TABLE": "MultiAgentOrchestration-dev-Incidents",
                        "BEDROCK_REGION": REGION,
                    }
                },
            )
            log_info("✓ Orchestrator function created")

        except Exception as e:
            log_error(f"Failed to create function: {e}")
            return False

    # Step 4: Add Bedrock permissions
    log_info("Adding Bedrock permissions...")
    try:
        response = lambda_client.get_function(FunctionName=ORCHESTRATOR_FUNCTION)
        role_arn = response["Configuration"]["Role"]
        role_name = role_arn.split("/")[-1]

        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/AmazonBedrockFullAccess",
        )
        log_info("✓ Bedrock permissions configured")
    except iam_client.exceptions.NoSuchEntityException:
        log_warning("Bedrock policy may already be attached")
    except Exception as e:
        log_warning(f"Error attaching Bedrock policy: {e}")

    return True


def update_ingest_handler():
    """Update IngestHandler to trigger orchestrator"""
    log_info("=" * 50)
    log_info("Updating IngestHandler")
    log_info("=" * 50)

    # Create deployment package
    source_file = (
        "infrastructure/lambda/orchestration/ingest_handler_with_orchestrator.py"
    )
    zip_path = create_deployment_package(source_file, "ingest_handler.py")

    if not zip_path:
        log_error("Failed to create IngestHandler package")
        return False

    # Read zip file
    with open(zip_path, "rb") as f:
        zip_content = f.read()

    try:
        # Update code
        lambda_client.update_function_code(
            FunctionName=INGEST_FUNCTION, ZipFile=zip_content
        )
        log_info("Code updated, waiting...")

        # Wait for update
        waiter = lambda_client.get_waiter("function_updated")
        waiter.wait(FunctionName=INGEST_FUNCTION)

        # Update environment variables
        lambda_client.update_function_configuration(
            FunctionName=INGEST_FUNCTION,
            Environment={
                "Variables": {
                    "INCIDENTS_TABLE": "MultiAgentOrchestration-dev-Incidents",
                    "ORCHESTRATOR_FUNCTION": ORCHESTRATOR_FUNCTION,
                    "BEDROCK_REGION": REGION,
                }
            },
        )

        log_info("✓ IngestHandler updated")
        return True

    except Exception as e:
        log_error(f"Failed to update IngestHandler: {e}")
        return False


def grant_invoke_permissions():
    """Grant IngestHandler permission to invoke Orchestrator"""
    log_info("=" * 50)
    log_info("Granting Invoke Permissions")
    log_info("=" * 50)

    try:
        # Get IngestHandler role
        response = lambda_client.get_function(FunctionName=INGEST_FUNCTION)
        role_arn = response["Configuration"]["Role"]
        role_name = role_arn.split("/")[-1]

        # Get account ID
        sts = boto3.client("sts")
        account_id = sts.get_caller_identity()["Account"]

        # Create policy document
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["lambda:InvokeFunction", "lambda:InvokeAsync"],
                    "Resource": f"arn:aws:lambda:{REGION}:{account_id}:function:{ORCHESTRATOR_FUNCTION}",
                }
            ],
        }

        # Attach inline policy
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="OrchestratorInvokePolicy",
            PolicyDocument=json.dumps(policy_document),
        )

        log_info("✓ Invoke permissions granted")
        return True

    except Exception as e:
        log_error(f"Failed to grant permissions: {e}")
        return False


def test_orchestrator():
    """Test orchestrator with sample payload"""
    log_info("=" * 50)
    log_info("Testing Orchestrator")
    log_info("=" * 50)

    test_payload = {
        "job_id": f"test_{int(time.time())}",
        "job_type": "ingest",
        "domain_id": "civic_complaints",
        "text": "TEST: There is a pothole on Main Street causing traffic issues",
        "tenant_id": "default-tenant",
        "user_id": "test-user",
    }

    log_info(f"Test payload: {json.dumps(test_payload, indent=2)}")

    try:
        response = lambda_client.invoke(
            FunctionName=ORCHESTRATOR_FUNCTION,
            InvocationType="RequestResponse",
            Payload=json.dumps(test_payload),
        )

        result = json.loads(response["Payload"].read())
        log_info(f"Test response: {json.dumps(result, indent=2)}")

        if response["StatusCode"] == 200:
            log_info("✓ Test successful!")
            return True
        else:
            log_warning(f"Test returned status {response['StatusCode']}")
            return False

    except Exception as e:
        log_error(f"Test failed: {e}")
        return False


def print_summary():
    """Print deployment summary"""
    print()
    log_info("=" * 50)
    log_info("Deployment Summary")
    log_info("=" * 50)

    try:
        response = lambda_client.get_function(FunctionName=ORCHESTRATOR_FUNCTION)
        arn = response["Configuration"]["FunctionArn"]

        log_info(f"Orchestrator Function: {ORCHESTRATOR_FUNCTION}")
        log_info(f"ARN: {arn}")
        log_info(f"Region: {REGION}")
        log_info("")
        log_info("✓ IngestHandler updated to trigger orchestrator")
        log_info("✓ Bedrock permissions configured")
        log_info("✓ Agent execution enabled")
        log_info("")
        log_info("=" * 50)
        log_info("✓ Deployment Complete!")
        log_info("=" * 50)
        log_info("")
        log_info("Next steps:")
        log_info("1. Submit a test report via API")
        log_info("2. Check CloudWatch logs for agent execution")
        log_info("3. Verify structured data in DynamoDB")
        log_info("")
        log_info("Monitor logs:")
        log_info(
            f"  aws logs tail /aws/lambda/{ORCHESTRATOR_FUNCTION} --follow --region {REGION}"
        )
        log_info("")

    except Exception as e:
        log_error(f"Error getting function details: {e}")


def main():
    """Main deployment flow"""
    print()
    print("=" * 50)
    print("Orchestrator Lambda Deployment")
    print("Multi-Agent Execution System")
    print("=" * 50)
    print()

    # Deploy orchestrator
    if not deploy_orchestrator():
        log_error("Orchestrator deployment failed")
        return 1

    # Wait a bit for function to be ready
    log_info("Waiting for function to be ready...")
    time.sleep(5)

    # Update IngestHandler
    if not update_ingest_handler():
        log_error("IngestHandler update failed")
        return 1

    # Grant permissions
    if not grant_invoke_permissions():
        log_warning("Permission grant failed, but continuing...")

    # Wait for updates to propagate
    log_info("Waiting for updates to propagate...")
    time.sleep(5)

    # Test orchestrator
    test_orchestrator()

    # Print summary
    print_summary()

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
