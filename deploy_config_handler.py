#!/usr/bin/env python3
"""
Deploy updated config handler Lambda function
"""

import os
import zipfile
import subprocess
from pathlib import Path

def create_lambda_zip():
    """Create deployment package for Lambda"""
    lambda_dir = Path('infrastructure/lambda/config-api')
    zip_path = '/tmp/config-handler.zip'
    
    print(f"Creating deployment package from {lambda_dir}...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(lambda_dir):
            # Skip __pycache__ and other unnecessary files
            if '__pycache__' in root or '.pyc' in root:
                continue
                
            for file in files:
                if file.endswith(('.py', '.txt')):
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(lambda_dir)
                    print(f"  Adding: {arcname}")
                    zipf.write(file_path, arcname)
    
    print(f"✅ Created {zip_path}")
    return zip_path

def deploy_lambda(zip_path):
    """Deploy Lambda function"""
    function_name = 'MultiAgentOrchestration-dev-Api-ConfigHandler'
    
    print(f"\nDeploying to Lambda function: {function_name}...")
    
    result = subprocess.run([
        'aws', 'lambda', 'update-function-code',
        '--function-name', function_name,
        '--zip-file', f'fileb://{zip_path}'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Lambda function updated successfully!")
        print("\nWaiting for function to be ready...")
        
        # Wait for update to complete
        subprocess.run([
            'aws', 'lambda', 'wait', 'function-updated',
            '--function-name', function_name
        ])
        
        print("✅ Function is ready!")
        return True
    else:
        print(f"❌ Deployment failed!")
        print(f"Error: {result.stderr}")
        return False

def main():
    """Main deployment process"""
    print("=" * 80)
    print("Config Handler Lambda Deployment")
    print("=" * 80)
    print()
    
    # Create zip
    zip_path = create_lambda_zip()
    
    # Deploy
    success = deploy_lambda(zip_path)
    
    if success:
        print("\n" + "=" * 80)
        print("Deployment Complete!")
        print("=" * 80)
        print("\nTest the API:")
        print("  curl -H 'Authorization: Bearer $JWT_TOKEN' \\")
        print("    https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/config?type=agent")
        print("\nCheck logs:")
        print("  aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-ConfigHandler --follow")
    else:
        print("\n❌ Deployment failed. Please check the error messages above.")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
