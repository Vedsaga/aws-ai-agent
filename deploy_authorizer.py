#!/usr/bin/env python3
"""Deploy authorizer with dependencies"""

import os
import sys
import subprocess
import zipfile
import shutil

def deploy_authorizer():
    """Deploy authorizer Lambda with dependencies"""
    
    # Create temp directory
    temp_dir = "/tmp/authorizer_deploy"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    print("Deploying authorizer Lambda...")
    
    # Copy authorizer code
    print("Copying authorizer code...")
    shutil.copy("infrastructure/lambda/authorizer/authorizer.py", temp_dir)
    
    # Install dependencies
    print("Installing dependencies...")
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "-r", "infrastructure/lambda/authorizer/requirements.txt",
        "-t", temp_dir,
        "--quiet"
    ], check=True)
    
    # Create zip
    print("Creating deployment package...")
    zip_path = os.path.join(temp_dir, "deployment.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            # Skip the zip file itself
            if "deployment.zip" in files:
                files.remove("deployment.zip")
            
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    # Deploy
    print("Uploading to Lambda...")
    subprocess.run([
        "aws", "lambda", "update-function-code",
        "--function-name", "MultiAgentOrchestration-dev-Auth-Authorizer",
        "--zip-file", f"fileb://{zip_path}",
        "--no-cli-pager"
    ], check=True)
    
    print("✅ Authorizer deployed successfully!")

if __name__ == "__main__":
    deploy_authorizer()
