"""
AWS S3 integration module for the Molecular Data Management and CRO Integration Platform.

This module provides a high-level interface for interacting with Amazon S3 storage service,
implementing functionality for uploading, downloading, and managing files in S3 buckets,
generating presigned URLs, and handling S3-specific operations required by the platform.
"""

import boto3  # boto3 ^1.26.0
import botocore  # botocore ^1.29.0
import io  # standard library
import os  # standard library
import uuid  # standard library
import mimetypes  # standard library
from typing import Dict, List  # standard library

from ...core.config import settings  # Import application configuration settings for AWS S3
from ...core.logging import get_logger  # Import logging function for consistent log formatting
from ...core.exceptions import IntegrationException  # Import exception class for integration-related errors
from ...constants.error_messages import INTEGRATION_ERRORS  # Import integration error message constants

# Initialize logger
logger = get_logger(__name__)


def upload_file(file_path: str, key: str, bucket_name: str = None, extra_args: Dict = None) -> bool:
    """
    Upload a file from disk to S3.
    
    Args:
        file_path: Path to the file to upload
        key: S3 object key where the file will be stored
        bucket_name: S3 bucket name (defaults to settings.S3_BUCKET_NAME)
        extra_args: Additional arguments to pass to S3 client (e.g., ContentType, Metadata)
    
    Returns:
        True if upload was successful
        
    Raises:
        IntegrationException: If upload fails
    """
    bucket = bucket_name or settings.S3_BUCKET_NAME
    extra_args = extra_args or {}
    
    try:
        logger.info(f"Uploading file {file_path} to S3 bucket {bucket} with key {key}")
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        s3_client.upload_file(
            Filename=file_path,
            Bucket=bucket,
            Key=key,
            ExtraArgs=extra_args
        )
        logger.info(f"Successfully uploaded file to {bucket}/{key}")
        return True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        logger.error(f"Failed to upload file to S3: {str(e)}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS["S3_OPERATION_FAILED"],
            service_name="AWS S3",
            error_code="s3_upload_failed",
            details={"file_path": file_path, "key": key, "error": str(e)}
        )


def upload_fileobj(fileobj: io.BytesIO, key: str, bucket_name: str = None, extra_args: Dict = None) -> bool:
    """
    Upload a file-like object to S3.
    
    Args:
        fileobj: File-like object to upload
        key: S3 object key where the file will be stored
        bucket_name: S3 bucket name (defaults to settings.S3_BUCKET_NAME)
        extra_args: Additional arguments to pass to S3 client (e.g., ContentType, Metadata)
    
    Returns:
        True if upload was successful
        
    Raises:
        IntegrationException: If upload fails
    """
    bucket = bucket_name or settings.S3_BUCKET_NAME
    extra_args = extra_args or {}
    
    try:
        logger.info(f"Uploading file object to S3 bucket {bucket} with key {key}")
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        s3_client.upload_fileobj(
            Fileobj=fileobj,
            Bucket=bucket,
            Key=key,
            ExtraArgs=extra_args
        )
        logger.info(f"Successfully uploaded file object to {bucket}/{key}")
        return True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        logger.error(f"Failed to upload file object to S3: {str(e)}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS["S3_OPERATION_FAILED"],
            service_name="AWS S3",
            error_code="s3_upload_failed",
            details={"key": key, "error": str(e)}
        )


def download_file(key: str, file_path: str, bucket_name: str = None) -> bool:
    """
    Download a file from S3 to disk.
    
    Args:
        key: S3 object key to download
        file_path: Local path where the file will be saved
        bucket_name: S3 bucket name (defaults to settings.S3_BUCKET_NAME)
    
    Returns:
        True if download was successful
        
    Raises:
        IntegrationException: If download fails
    """
    bucket = bucket_name or settings.S3_BUCKET_NAME
    
    try:
        logger.info(f"Downloading file from S3 bucket {bucket} with key {key} to {file_path}")
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        s3_client.download_file(
            Bucket=bucket,
            Key=key,
            Filename=file_path
        )
        logger.info(f"Successfully downloaded file from {bucket}/{key} to {file_path}")
        return True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        logger.error(f"Failed to download file from S3: {str(e)}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS["S3_OPERATION_FAILED"],
            service_name="AWS S3",
            error_code="s3_download_failed",
            details={"key": key, "file_path": file_path, "error": str(e)}
        )


def download_fileobj(key: str, fileobj: io.BytesIO, bucket_name: str = None) -> bool:
    """
    Download a file from S3 to a file-like object.
    
    Args:
        key: S3 object key to download
        fileobj: File-like object where the content will be written
        bucket_name: S3 bucket name (defaults to settings.S3_BUCKET_NAME)
    
    Returns:
        True if download was successful
        
    Raises:
        IntegrationException: If download fails
    """
    bucket = bucket_name or settings.S3_BUCKET_NAME
    
    try:
        logger.info(f"Downloading file from S3 bucket {bucket} with key {key} to file object")
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        s3_client.download_fileobj(
            Bucket=bucket,
            Key=key,
            Fileobj=fileobj
        )
        logger.info(f"Successfully downloaded file from {bucket}/{key} to file object")
        return True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        logger.error(f"Failed to download file from S3: {str(e)}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS["S3_OPERATION_FAILED"],
            service_name="AWS S3",
            error_code="s3_download_failed",
            details={"key": key, "error": str(e)}
        )


def get_object(key: str, bucket_name: str = None) -> Dict:
    """
    Get an object from S3 and return its content.
    
    Args:
        key: S3 object key to get
        bucket_name: S3 bucket name (defaults to settings.S3_BUCKET_NAME)
    
    Returns:
        Object data including 'Body' with content stream
        
    Raises:
        IntegrationException: If get operation fails
    """
    bucket = bucket_name or settings.S3_BUCKET_NAME
    
    try:
        logger.info(f"Getting object from S3 bucket {bucket} with key {key}")
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        response = s3_client.get_object(
            Bucket=bucket,
            Key=key
        )
        logger.info(f"Successfully retrieved object from {bucket}/{key}")
        return response
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        logger.error(f"Failed to get object from S3: {str(e)}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS["S3_OPERATION_FAILED"],
            service_name="AWS S3",
            error_code="s3_get_failed",
            details={"key": key, "error": str(e)}
        )


def delete_object(key: str, bucket_name: str = None) -> bool:
    """
    Delete an object from S3.
    
    Args:
        key: S3 object key to delete
        bucket_name: S3 bucket name (defaults to settings.S3_BUCKET_NAME)
    
    Returns:
        True if deletion was successful
        
    Raises:
        IntegrationException: If deletion fails
    """
    bucket = bucket_name or settings.S3_BUCKET_NAME
    
    try:
        logger.info(f"Deleting object from S3 bucket {bucket} with key {key}")
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        s3_client.delete_object(
            Bucket=bucket,
            Key=key
        )
        logger.info(f"Successfully deleted object from {bucket}/{key}")
        return True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        logger.error(f"Failed to delete object from S3: {str(e)}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS["S3_OPERATION_FAILED"],
            service_name="AWS S3",
            error_code="s3_delete_failed",
            details={"key": key, "error": str(e)}
        )


def list_objects(prefix: str = "", bucket_name: str = None) -> List[str]:
    """
    List objects in an S3 bucket with optional prefix.
    
    Args:
        prefix: Key prefix to filter objects (default: list all objects)
        bucket_name: S3 bucket name (defaults to settings.S3_BUCKET_NAME)
    
    Returns:
        List of object keys matching the prefix
        
    Raises:
        IntegrationException: If listing fails
    """
    bucket = bucket_name or settings.S3_BUCKET_NAME
    
    try:
        logger.info(f"Listing objects in S3 bucket {bucket} with prefix '{prefix}'")
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
        )
        
        # Extract keys from the response
        keys = []
        if 'Contents' in response:
            keys = [item['Key'] for item in response['Contents']]
        
        logger.info(f"Successfully listed {len(keys)} objects from {bucket} with prefix '{prefix}'")
        return keys
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        logger.error(f"Failed to list objects from S3: {str(e)}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS["S3_OPERATION_FAILED"],
            service_name="AWS S3",
            error_code="s3_list_failed",
            details={"prefix": prefix, "error": str(e)}
        )


def generate_presigned_url(key: str, bucket_name: str = None, operation: str = 'get_object', 
                         expiration: int = 3600, params: Dict = None) -> str:
    """
    Generate a presigned URL for an S3 object.
    
    Args:
        key: S3 object key
        bucket_name: S3 bucket name (defaults to settings.S3_BUCKET_NAME)
        operation: S3 operation ('get_object' or 'put_object')
        expiration: URL expiration time in seconds (default: 1 hour)
        params: Additional parameters for the operation
    
    Returns:
        Presigned URL for the specified operation
        
    Raises:
        IntegrationException: If URL generation fails
    """
    bucket = bucket_name or settings.S3_BUCKET_NAME
    params = params or {}
    
    try:
        logger.info(f"Generating presigned URL for {operation} on {bucket}/{key}")
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        # Combine the object parameters with any additional params
        client_params = {
            'Bucket': bucket,
            'Key': key,
            **params
        }
        
        url = s3_client.generate_presigned_url(
            ClientMethod=operation,
            Params=client_params,
            ExpiresIn=expiration
        )
        
        logger.info(f"Successfully generated presigned URL for {operation} on {bucket}/{key}")
        return url
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        logger.error(f"Failed to generate presigned URL: {str(e)}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS["S3_OPERATION_FAILED"],
            service_name="AWS S3",
            error_code="s3_presigned_url_failed",
            details={"key": key, "operation": operation, "error": str(e)}
        )


def copy_object(source_key: str, destination_key: str, source_bucket: str = None, 
               destination_bucket: str = None) -> bool:
    """
    Copy an object within S3 or between buckets.
    
    Args:
        source_key: Source S3 object key
        destination_key: Destination S3 object key
        source_bucket: Source S3 bucket name (defaults to settings.S3_BUCKET_NAME)
        destination_bucket: Destination S3 bucket name (defaults to source_bucket)
    
    Returns:
        True if copy was successful
        
    Raises:
        IntegrationException: If copy fails
    """
    source_bucket = source_bucket or settings.S3_BUCKET_NAME
    destination_bucket = destination_bucket or source_bucket
    
    try:
        logger.info(f"Copying object from {source_bucket}/{source_key} to {destination_bucket}/{destination_key}")
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        s3_client.copy_object(
            CopySource={'Bucket': source_bucket, 'Key': source_key},
            Bucket=destination_bucket,
            Key=destination_key
        )
        
        logger.info(f"Successfully copied object from {source_bucket}/{source_key} to {destination_bucket}/{destination_key}")
        return True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        logger.error(f"Failed to copy object in S3: {str(e)}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS["S3_OPERATION_FAILED"],
            service_name="AWS S3",
            error_code="s3_copy_failed",
            details={
                "source_key": source_key,
                "destination_key": destination_key,
                "error": str(e)
            }
        )


def get_object_metadata(key: str, bucket_name: str = None) -> Dict:
    """
    Get metadata for an S3 object.
    
    Args:
        key: S3 object key
        bucket_name: S3 bucket name (defaults to settings.S3_BUCKET_NAME)
    
    Returns:
        Object metadata
        
    Raises:
        IntegrationException: If metadata retrieval fails
    """
    bucket = bucket_name or settings.S3_BUCKET_NAME
    
    try:
        logger.info(f"Getting metadata for object in S3 bucket {bucket} with key {key}")
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        response = s3_client.head_object(
            Bucket=bucket,
            Key=key
        )
        
        logger.info(f"Successfully retrieved metadata for {bucket}/{key}")
        return response
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        logger.error(f"Failed to get object metadata from S3: {str(e)}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS["S3_OPERATION_FAILED"],
            service_name="AWS S3",
            error_code="s3_metadata_failed",
            details={"key": key, "error": str(e)}
        )


class S3Client:
    """
    Client class for interacting with AWS S3 service with simplified interface and error handling.
    """
    
    def __init__(self, bucket_name: str = None):
        """
        Initialize S3 client with AWS credentials from settings.
        
        Args:
            bucket_name: S3 bucket name (defaults to settings.S3_BUCKET_NAME)
        """
        self._bucket_name = bucket_name or settings.S3_BUCKET_NAME
        self._client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        logger.info(f"Initialized S3 client for bucket {self._bucket_name}")
    
    def upload(self, content: bytes, key: str, content_type: str = None, metadata: Dict = None) -> bool:
        """
        Upload file content to S3 bucket.
        
        Args:
            content: File content as bytes
            key: S3 object key where the file will be stored
            content_type: Content type of the file (MIME type)
            metadata: Additional metadata for the object
        
        Returns:
            True if upload was successful
            
        Raises:
            IntegrationException: If upload fails
        """
        file_obj = io.BytesIO(content)
        
        # Prepare extra arguments
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        if metadata:
            extra_args['Metadata'] = metadata
        
        logger.info(f"Uploading {len(content)} bytes to S3 bucket {self._bucket_name} with key {key}")
        
        try:
            return upload_fileobj(
                fileobj=file_obj,
                key=key,
                bucket_name=self._bucket_name,
                extra_args=extra_args
            )
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            raise
    
    def download(self, key: str) -> bytes:
        """
        Download file content from S3 bucket.
        
        Args:
            key: S3 object key to download
        
        Returns:
            File content as bytes
            
        Raises:
            IntegrationException: If download fails
        """
        logger.info(f"Downloading content from S3 bucket {self._bucket_name} with key {key}")
        
        try:
            file_obj = io.BytesIO()
            download_fileobj(
                key=key,
                fileobj=file_obj,
                bucket_name=self._bucket_name
            )
            file_obj.seek(0)
            return file_obj.read()
        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            raise
    
    def delete(self, key: str) -> bool:
        """
        Delete an object from S3 bucket.
        
        Args:
            key: S3 object key to delete
        
        Returns:
            True if deletion was successful
            
        Raises:
            IntegrationException: If deletion fails
        """
        logger.info(f"Deleting object from S3 bucket {self._bucket_name} with key {key}")
        
        try:
            return delete_object(
                key=key,
                bucket_name=self._bucket_name
            )
        except Exception as e:
            logger.error(f"Deletion failed: {str(e)}")
            raise
    
    def list(self, prefix: str = "") -> List[str]:
        """
        List objects in S3 bucket with optional prefix.
        
        Args:
            prefix: Key prefix to filter objects
        
        Returns:
            List of object keys matching the prefix
            
        Raises:
            IntegrationException: If listing fails
        """
        logger.info(f"Listing objects in S3 bucket {self._bucket_name} with prefix '{prefix}'")
        
        try:
            return list_objects(
                prefix=prefix,
                bucket_name=self._bucket_name
            )
        except Exception as e:
            logger.error(f"List operation failed: {str(e)}")
            raise
    
    def get_presigned_url(self, key: str, operation: str = 'get_object', 
                        expiration: int = 3600, params: Dict = None) -> str:
        """
        Generate a presigned URL for an S3 object.
        
        Args:
            key: S3 object key
            operation: S3 operation ('get_object' or 'put_object')
            expiration: URL expiration time in seconds (default: 1 hour)
            params: Additional parameters for the operation
        
        Returns:
            Presigned URL for the specified operation
            
        Raises:
            IntegrationException: If URL generation fails
        """
        logger.info(f"Generating presigned URL for {operation} on {self._bucket_name}/{key}")
        
        try:
            return generate_presigned_url(
                key=key,
                bucket_name=self._bucket_name,
                operation=operation,
                expiration=expiration,
                params=params
            )
        except Exception as e:
            logger.error(f"Presigned URL generation failed: {str(e)}")
            raise
    
    def get_download_url(self, key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for downloading an S3 object.
        
        Args:
            key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Presigned download URL
            
        Raises:
            IntegrationException: If URL generation fails
        """
        return self.get_presigned_url(
            key=key,
            operation='get_object',
            expiration=expiration
        )
    
    def get_upload_url(self, key: str, content_type: str = None, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for uploading to S3.
        
        Args:
            key: S3 object key
            content_type: Content type of the file to be uploaded
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Presigned upload URL
            
        Raises:
            IntegrationException: If URL generation fails
        """
        params = {}
        if content_type:
            params['ContentType'] = content_type
            
        return self.get_presigned_url(
            key=key,
            operation='put_object',
            expiration=expiration,
            params=params
        )
    
    def copy(self, source_key: str, destination_key: str) -> bool:
        """
        Copy an object within the same bucket.
        
        Args:
            source_key: Source S3 object key
            destination_key: Destination S3 object key
        
        Returns:
            True if copy was successful
            
        Raises:
            IntegrationException: If copy fails
        """
        logger.info(f"Copying object within S3 bucket {self._bucket_name} from {source_key} to {destination_key}")
        
        try:
            return copy_object(
                source_key=source_key,
                destination_key=destination_key,
                source_bucket=self._bucket_name,
                destination_bucket=self._bucket_name
            )
        except Exception as e:
            logger.error(f"Copy operation failed: {str(e)}")
            raise
    
    def get_metadata(self, key: str) -> Dict:
        """
        Get metadata for an S3 object.
        
        Args:
            key: S3 object key
        
        Returns:
            Object metadata
            
        Raises:
            IntegrationException: If metadata retrieval fails
        """
        logger.info(f"Getting metadata for object in S3 bucket {self._bucket_name} with key {key}")
        
        try:
            return get_object_metadata(
                key=key,
                bucket_name=self._bucket_name
            )
        except Exception as e:
            logger.error(f"Metadata retrieval failed: {str(e)}")
            raise
    
    def generate_key(self, folder: str, filename: str) -> str:
        """
        Generate a unique key for S3 storage.
        
        Args:
            folder: Folder path within the bucket
            filename: Original filename
        
        Returns:
            Generated S3 key
        """
        # Generate a UUID for uniqueness
        unique_id = str(uuid.uuid4())
        
        # Extract file extension
        _, extension = os.path.splitext(filename)
        
        # Construct key with folder, UUID, and extension
        key = f"{folder.rstrip('/')}/{unique_id}{extension}"
        
        return key