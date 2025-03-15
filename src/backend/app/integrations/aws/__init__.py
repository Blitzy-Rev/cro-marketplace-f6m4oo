"""
AWS Service Integration Module for the Molecular Data Management and CRO Integration Platform.

This module provides a unified entry point for all AWS services used in the platform,
including S3 for document storage, SQS for asynchronous message processing, and Cognito
for user authentication and management.
"""

__version__ = "0.1.0"

# Import boto3 for direct AWS SDK access if needed
import boto3  # version ^1.26.0

# Import S3 components
from .s3 import S3Client, upload_file, download_file, generate_presigned_url

# Import SQS components
from .sqs import SQSClient, SQSProducer, SQSConsumer

# Import Cognito components
from .cognito import CognitoClient, register_user, initiate_auth

# Export all imported components
__all__ = [
    "S3Client", "upload_file", "download_file", "generate_presigned_url",
    "SQSClient", "SQSProducer", "SQSConsumer", 
    "CognitoClient", "register_user", "initiate_auth"
]