# Terraform backend configuration for the Molecular Data Management and CRO Integration Platform
# This file defines where and how the Terraform state is stored and managed.
#
# The state file contains sensitive information and should be stored securely with
# appropriate access controls. Using S3 with encryption and DynamoDB for locking
# provides a robust and secure solution for team collaboration.

terraform {
  backend "s3" {
    # S3 bucket where terraform state will be stored
    # Note: This bucket must be created before terraform init
    bucket = "molecule-platform-terraform-state"
    
    # Path to the state file within the bucket
    # In production, consider using workspace-based paths for multi-environment setup
    key = "terraform.tfstate"
    
    # AWS region where the S3 bucket is located
    region = "us-east-1"
    
    # Enable encryption for the state file to secure sensitive data
    encrypt = true
    
    # DynamoDB table used for state locking to prevent concurrent modifications
    # Note: This table must be created before terraform init with a primary key of "LockID"
    dynamodb_table = "molecule-platform-terraform-locks"
    
    # Note: S3 bucket versioning should be enabled on the bucket itself
    # This allows recovery of previous state versions if needed
    # The versioning configuration is not part of the backend configuration,
    # but should be enabled when creating the bucket
  }
}