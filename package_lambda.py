#!/usr/bin/env python3
"""
Package Lambda deployment for quick deployment
"""

import zipfile
import os
import shutil
import sys


def package_lambda():
    """Package the simplified Lambda handler"""

    # Create temp directory
    temp_dir = "/tmp/lambda_deploy"
    os.makedirs(temp_dir, exist_ok=True)

    # Source and destination paths
    source_file = "infrastructure/lambda/config-api/config_handler_simple.py"
    dest_file = os.path.join(temp_dir, "config_handler.py")
    zip_path = os.path.join(temp_dir, "deployment.zip")

    # Check if source exists
    if not os.path.exists(source_file):
        print(f"ERROR: Source file not found: {source_file}")
        sys.exit(1)

    # Copy simplified handler
    print(f"Copying {source_file} to {dest_file}")
    shutil.copy(source_file, dest_file)

    # Create zip file
    print(f"Creating deployment package: {zip_path}")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(dest_file, "config_handler.py")

    size = os.path.getsize(zip_path)
    print(f"✓ Created deployment package: {zip_path}")
    print(f"✓ Size: {size:,} bytes")

    return zip_path


if __name__ == "__main__":
    zip_path = package_lambda()
    print(f"\nDeployment package ready at: {zip_path}")
