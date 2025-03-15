"""
Service layer for file storage operations in the Molecular Data Management and CRO Integration Platform.

This module provides a high-level interface for storing, retrieving, and managing various types
of files including CSV molecular data, documents, and experimental results. It abstracts the
underlying S3 storage implementation and provides specialized methods for different file types.
"""

import os
import io
import uuid
from typing import Optional, Union, Dict, Any, BinaryIO

from ..integrations.aws.s3 import S3Client
from ..utils.file_handlers import (
    FileHandler, 
    ALLOWED_DOCUMENT_TYPES, 
    ALLOWED_CSV_TYPES, 
    ALLOWED_IMAGE_TYPES
)
from ..core.logging import get_logger
from ..core.exceptions import StorageException

# Configure logger
logger = get_logger(__name__)

# Constants
DEFAULT_EXPIRATION_SECONDS = 3600  # 1 hour
DOCUMENT_FOLDER = "documents"
CSV_FOLDER = "csv"
RESULT_FOLDER = "results"
IMAGE_FOLDER = "images"


class StorageService:
    """
    Service class for file storage operations with specialized methods for different file types.
    """
    
    @property
    def S3Client(self):
        """S3 client instance for storage operations."""
        return self._s3_client
    
    def __init__(self):
        """Initialize the StorageService with S3 client."""
        self._s3_client = S3Client()
        logger.info("StorageService initialized")
    
    def store_file(self, file_content: bytes, folder: str, filename: str, 
                   allowed_types: list, max_size_mb: Optional[int] = None) -> str:
        """
        Store a file in the storage system with validation.
        
        Args:
            file_content: File content as bytes
            folder: Storage folder path
            filename: Original filename
            allowed_types: List of allowed MIME types
            max_size_mb: Maximum file size in MB (optional)
            
        Returns:
            str: Storage URL for the stored file
        """
        try:
            # Create file handler for validation and content type detection
            file_handler = FileHandler.from_bytes(file_content, filename)
            
            # Validate file type and size
            file_handler.validate_type(allowed_types)
            file_handler.validate_size(max_size_mb)
            
            # Generate a unique storage key
            storage_key = self._s3_client.generate_key(folder, filename)
            
            # Get content type
            content_type = file_handler.get_content_type()
            
            # Upload file to S3
            self._s3_client.upload(file_content, storage_key, content_type=content_type)
            
            # Return the storage key (used as URL)
            return storage_key
        
        except Exception as e:
            logger.error(f"Failed to store file '{filename}' in folder '{folder}': {str(e)}")
            raise StorageException(
                message=f"Failed to store file: {str(e)}",
                error_code="file_storage_failed",
                details={
                    "filename": filename,
                    "folder": folder,
                    "error": str(e)
                }
            )
    
    def store_document_file(self, file_content: bytes, filename: str, 
                            max_size_mb: Optional[int] = None) -> str:
        """
        Store a document file with appropriate validation.
        
        Args:
            file_content: Document file content as bytes
            filename: Original filename
            max_size_mb: Maximum file size in MB (optional)
            
        Returns:
            str: Storage URL for the document
        """
        return self.store_file(
            file_content=file_content,
            folder=DOCUMENT_FOLDER,
            filename=filename,
            allowed_types=ALLOWED_DOCUMENT_TYPES,
            max_size_mb=max_size_mb
        )
    
    def store_csv_file(self, file_content: bytes, filename: str, 
                      max_size_mb: Optional[int] = None) -> str:
        """
        Store a CSV file with appropriate validation.
        
        Args:
            file_content: CSV file content as bytes
            filename: Original filename
            max_size_mb: Maximum file size in MB (optional)
            
        Returns:
            str: Storage URL for the CSV file
        """
        return self.store_file(
            file_content=file_content,
            folder=CSV_FOLDER,
            filename=filename,
            allowed_types=ALLOWED_CSV_TYPES,
            max_size_mb=max_size_mb
        )
    
    def store_result_file(self, file_content: bytes, filename: str, 
                         max_size_mb: Optional[int] = None) -> str:
        """
        Store a result file with appropriate validation.
        
        Args:
            file_content: Result file content as bytes
            filename: Original filename
            max_size_mb: Maximum file size in MB (optional)
            
        Returns:
            str: Storage URL for the result file
        """
        return self.store_file(
            file_content=file_content,
            folder=RESULT_FOLDER,
            filename=filename,
            allowed_types=ALLOWED_DOCUMENT_TYPES,  # Results can be documents
            max_size_mb=max_size_mb
        )
    
    def store_image_file(self, file_content: bytes, filename: str, 
                        max_size_mb: Optional[int] = None) -> str:
        """
        Store an image file with appropriate validation.
        
        Args:
            file_content: Image file content as bytes
            filename: Original filename
            max_size_mb: Maximum file size in MB (optional)
            
        Returns:
            str: Storage URL for the image file
        """
        return self.store_file(
            file_content=file_content,
            folder=IMAGE_FOLDER,
            filename=filename,
            allowed_types=ALLOWED_IMAGE_TYPES,
            max_size_mb=max_size_mb
        )
    
    def retrieve_file(self, storage_url: str) -> bytes:
        """
        Retrieve a file from storage by its URL.
        
        Args:
            storage_url: Storage URL (key) of the file
            
        Returns:
            bytes: File content as bytes
        """
        try:
            logger.info(f"Retrieving file from storage: {storage_url}")
            return self._s3_client.download(storage_url)
        
        except Exception as e:
            logger.error(f"Failed to retrieve file from {storage_url}: {str(e)}")
            raise StorageException(
                message=f"Failed to retrieve file: {str(e)}",
                error_code="file_retrieval_failed",
                details={
                    "storage_url": storage_url,
                    "error": str(e)
                }
            )
    
    def delete_file(self, storage_url: str) -> bool:
        """
        Delete a file from storage by its URL.
        
        Args:
            storage_url: Storage URL (key) of the file
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            logger.info(f"Deleting file from storage: {storage_url}")
            return self._s3_client.delete(storage_url)
        
        except Exception as e:
            logger.error(f"Failed to delete file from {storage_url}: {str(e)}")
            raise StorageException(
                message=f"Failed to delete file: {str(e)}",
                error_code="file_deletion_failed",
                details={
                    "storage_url": storage_url,
                    "error": str(e)
                }
            )
    
    def get_download_url(self, storage_url: str, 
                        expiration_seconds: int = DEFAULT_EXPIRATION_SECONDS) -> str:
        """
        Generate a presigned download URL for a file.
        
        Args:
            storage_url: Storage URL (key) of the file
            expiration_seconds: URL expiration time in seconds
            
        Returns:
            str: Presigned download URL
        """
        try:
            logger.info(f"Generating download URL for: {storage_url} with expiration: {expiration_seconds}s")
            return self._s3_client.get_download_url(storage_url, expiration=expiration_seconds)
        
        except Exception as e:
            logger.error(f"Failed to generate download URL for {storage_url}: {str(e)}")
            raise StorageException(
                message=f"Failed to generate download URL: {str(e)}",
                error_code="download_url_generation_failed",
                details={
                    "storage_url": storage_url,
                    "error": str(e)
                }
            )
    
    def get_upload_url(self, folder: str, filename: str, content_type: str, 
                      expiration_seconds: int = DEFAULT_EXPIRATION_SECONDS) -> Dict[str, str]:
        """
        Generate a presigned upload URL for a file.
        
        Args:
            folder: Storage folder path
            filename: Original filename
            content_type: Content type of the file
            expiration_seconds: URL expiration time in seconds
            
        Returns:
            Dict[str, str]: Dictionary with upload URL and storage key
        """
        try:
            logger.info(f"Generating upload URL for file '{filename}' in folder '{folder}'")
            
            # Generate a unique storage key
            storage_key = self._s3_client.generate_key(folder, filename)
            
            # Generate presigned upload URL
            upload_url = self._s3_client.get_upload_url(
                storage_key, content_type=content_type, expiration=expiration_seconds
            )
            
            return {
                "upload_url": upload_url,
                "storage_key": storage_key
            }
        
        except Exception as e:
            logger.error(f"Failed to generate upload URL for '{filename}' in '{folder}': {str(e)}")
            raise StorageException(
                message=f"Failed to generate upload URL: {str(e)}",
                error_code="upload_url_generation_failed",
                details={
                    "folder": folder,
                    "filename": filename,
                    "error": str(e)
                }
            )
    
    def copy_file(self, source_url: str, destination_folder: str, 
                 destination_filename: str) -> str:
        """
        Copy a file within the storage system.
        
        Args:
            source_url: Source storage URL (key)
            destination_folder: Destination folder path
            destination_filename: Destination filename
            
        Returns:
            str: Storage URL for the copied file
        """
        try:
            logger.info(f"Copying file from {source_url} to {destination_folder}/{destination_filename}")
            
            # Generate destination key
            destination_key = self._s3_client.generate_key(destination_folder, destination_filename)
            
            # Copy the file
            self._s3_client.copy(source_url, destination_key)
            
            return destination_key
        
        except Exception as e:
            logger.error(f"Failed to copy file from {source_url}: {str(e)}")
            raise StorageException(
                message=f"Failed to copy file: {str(e)}",
                error_code="file_copy_failed",
                details={
                    "source_url": source_url,
                    "destination_folder": destination_folder,
                    "destination_filename": destination_filename,
                    "error": str(e)
                }
            )