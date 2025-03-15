"""
Utilities for file handling operations in the Molecular Data Management and CRO Integration Platform.

This module provides functions and classes for file operations including:
- File type detection and validation
- File size validation
- CSV file handling
- Temporary file creation
- Secure file operations
- Document management utilities

These utilities support the platform's requirements for CSV molecular data ingestion,
document management, and secure file exchange between pharma and CRO users.
"""

import os
import io
import mimetypes
import tempfile
from typing import List, Dict, Optional, Union, BinaryIO, Generator

import magic  # python-magic 0.4.27

from ..core.exceptions import FileException
from ..constants.error_messages import DOCUMENT_ERRORS, CSV_ERRORS
from ..core.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants
MAX_FILE_SIZE_MB = 100  # Maximum file size in MB

# Allowed file types
ALLOWED_DOCUMENT_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv',
    'text/plain',
    'application/zip',
    'application/x-zip-compressed'
]

ALLOWED_IMAGE_TYPES = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/tiff'
]

ALLOWED_CSV_TYPES = [
    'text/csv',
    'application/csv',
    'application/vnd.ms-excel'  # Excel files can be CSV-like
]


def detect_content_type(file_or_path: Union[str, bytes, BinaryIO], filename: Optional[str] = None) -> str:
    """
    Detect the MIME type of a file based on its content and/or filename.
    
    Args:
        file_or_path: File path, bytes content, or file-like object
        filename: Optional filename to use for fallback MIME type detection
        
    Returns:
        str: Detected MIME type
    """
    content_type = None
    
    try:
        # Detect based on file path
        if isinstance(file_or_path, str) and os.path.isfile(file_or_path):
            content_type = magic.from_file(file_or_path, mime=True)
        
        # Detect based on file content
        elif isinstance(file_or_path, bytes):
            content_type = magic.from_buffer(file_or_path, mime=True)
        
        # Detect based on file-like object
        elif hasattr(file_or_path, 'read') and callable(file_or_path.read):
            # Store current position
            position = file_or_path.tell()
            
            # Read a sample of the file for detection
            sample = file_or_path.read(2048)
            
            # Reset file position
            file_or_path.seek(position)
            
            if isinstance(sample, bytes):
                content_type = magic.from_buffer(sample, mime=True)
    
    except Exception as e:
        logger.warning(f"Error detecting content type: {str(e)}")
    
    # Use mimetypes module as fallback if filename is provided
    if not content_type and filename:
        content_type, _ = mimetypes.guess_type(filename)
    
    # Default to binary if we couldn't detect the type
    if not content_type:
        content_type = 'application/octet-stream'
    
    return content_type


def validate_file_type(file_or_path: Union[str, bytes, BinaryIO], 
                       allowed_types: List[str], 
                       filename: Optional[str] = None) -> bool:
    """
    Validate if a file's content type is in the list of allowed types.
    
    Args:
        file_or_path: File path, bytes content, or file-like object
        allowed_types: List of allowed MIME types
        filename: Optional filename for fallback MIME type detection
        
    Returns:
        bool: True if file type is allowed
        
    Raises:
        FileException: If file type is not allowed
    """
    content_type = detect_content_type(file_or_path, filename)
    
    if content_type not in allowed_types:
        logger.warning(f"Unsupported file format: {content_type}, expected one of {allowed_types}")
        raise FileException(
            message=DOCUMENT_ERRORS['UNSUPPORTED_FILE_FORMAT'],
            error_code='unsupported_file_format',
            details={
                'content_type': content_type,
                'allowed_types': allowed_types
            }
        )
    
    return True


def validate_file_size(file_or_path: Union[str, bytes, BinaryIO], 
                       max_size_mb: Optional[int] = None) -> bool:
    """
    Validate if a file's size is within the maximum allowed size.
    
    Args:
        file_or_path: File path, bytes content, or file-like object
        max_size_mb: Maximum allowed size in MB (defaults to MAX_FILE_SIZE_MB)
        
    Returns:
        bool: True if file size is within limit
        
    Raises:
        FileException: If file is too large
    """
    if max_size_mb is None:
        max_size_mb = MAX_FILE_SIZE_MB
    
    max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
    file_size = get_file_size(file_or_path)
    
    if file_size > max_size_bytes:
        logger.warning(f"File size {file_size} bytes exceeds limit of {max_size_bytes} bytes")
        
        # Determine whether it's a document or CSV file for appropriate error message
        if hasattr(file_or_path, 'name') and file_or_path.name.lower().endswith('.csv'):
            error_message = CSV_ERRORS['FILE_TOO_LARGE']
            error_code = 'csv_file_too_large'
        else:
            error_message = DOCUMENT_ERRORS['DOCUMENT_TOO_LARGE']
            error_code = 'document_too_large'
        
        raise FileException(
            message=error_message,
            error_code=error_code,
            details={
                'file_size': file_size,
                'max_size': max_size_bytes,
                'max_size_mb': max_size_mb
            }
        )
    
    return True


def get_file_extension(filename: str) -> str:
    """
    Extract the file extension from a filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        str: File extension (lowercase, without dot)
    """
    if not filename:
        return ""
    
    # Split the filename by dot and get the last part
    parts = filename.split('.')
    if len(parts) > 1:
        return parts[-1].lower()
    
    return ""


def is_csv_file(file_or_path: Union[str, bytes, BinaryIO], 
                filename: Optional[str] = None) -> bool:
    """
    Check if a file is a CSV file based on content type and/or extension.
    
    Args:
        file_or_path: File path, bytes content, or file-like object
        filename: Optional filename to check extension
        
    Returns:
        bool: True if file is a CSV file
    """
    # Check MIME type
    content_type = detect_content_type(file_or_path, filename)
    if content_type in ALLOWED_CSV_TYPES:
        return True
    
    # Check file extension if filename is provided
    if filename and get_file_extension(filename) == 'csv':
        return True
    
    # If file_or_path is a file path, check its extension
    if isinstance(file_or_path, str) and os.path.isfile(file_or_path):
        if get_file_extension(file_or_path) == 'csv':
            return True
    
    # If file_or_path is a file-like object with a name attribute, check that
    if hasattr(file_or_path, 'name'):
        if get_file_extension(file_or_path.name) == 'csv':
            return True
    
    return False


def create_temp_file(content: bytes, suffix: Optional[str] = None) -> str:
    """
    Create a temporary file with the given content.
    
    Args:
        content: Bytes content to write to the file
        suffix: Optional file suffix (e.g., '.csv')
        
    Returns:
        str: Path to the temporary file
    """
    try:
        # Create a temporary file with the specified suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            return temp_file.name
    
    except Exception as e:
        logger.error(f"Failed to create temporary file: {str(e)}")
        raise FileException(
            message="Failed to create temporary file",
            error_code="temp_file_creation_failed",
            details={"error": str(e)}
        )


def read_file_chunks(file_or_path: Union[str, BinaryIO], chunk_size: int = 8192) -> Generator[bytes, None, None]:
    """
    Read a file in chunks to handle large files efficiently.
    
    Args:
        file_or_path: File path or file-like object
        chunk_size: Size of each chunk in bytes
        
    Yields:
        Generator[bytes]: Generator yielding file chunks
    """
    file_obj = None
    opened_here = False
    
    try:
        # If it's a string (file path), open the file
        if isinstance(file_or_path, str):
            file_obj = open(file_or_path, 'rb')
            opened_here = True
        else:
            # Assume it's already a file-like object
            file_obj = file_or_path
        
        # Read and yield chunks
        while True:
            chunk = file_obj.read(chunk_size)
            if not chunk:
                break
            yield chunk
    
    finally:
        # Only close the file if we opened it here
        if opened_here and file_obj:
            file_obj.close()


def get_safe_filename(filename: str) -> str:
    """
    Convert a filename to a safe version by removing problematic characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Safe filename
    """
    # Replace spaces with underscores
    safe_name = filename.replace(' ', '_')
    
    # Remove any characters that aren't alphanumeric, underscore, hyphen, or period
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '_-.')
    
    return safe_name


def get_file_size(file_or_path: Union[str, bytes, BinaryIO]) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        file_or_path: File path, bytes content, or file-like object
        
    Returns:
        int: File size in bytes
    """
    # If it's a file path, use os.path.getsize
    if isinstance(file_or_path, str) and os.path.isfile(file_or_path):
        return os.path.getsize(file_or_path)
    
    # If it's bytes, use len()
    if isinstance(file_or_path, bytes):
        return len(file_or_path)
    
    # If it's a file-like object, use seek and tell
    if hasattr(file_or_path, 'seek') and hasattr(file_or_path, 'tell'):
        # Store current position
        current_position = file_or_path.tell()
        
        # Seek to the end and get the position (size)
        file_or_path.seek(0, os.SEEK_END)
        size = file_or_path.tell()
        
        # Restore original position
        file_or_path.seek(current_position)
        
        return size
    
    # If all else fails, raise an exception
    raise FileException(
        message="Unable to determine file size",
        error_code="file_size_determination_failed"
    )


def get_file_hash(file_or_path: Union[str, bytes, BinaryIO], hash_algorithm: str = 'sha256') -> str:
    """
    Calculate a hash of file content for integrity verification.
    
    Args:
        file_or_path: File path, bytes content, or file-like object
        hash_algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        str: Hexadecimal hash digest
    """
    # Import hashlib here to avoid circular imports
    import hashlib
    
    # Create hash object
    hasher = hashlib.new(hash_algorithm)
    
    # Process file content based on input type
    if isinstance(file_or_path, str) and os.path.isfile(file_or_path):
        # If it's a file path, read in chunks
        for chunk in read_file_chunks(file_or_path):
            hasher.update(chunk)
    
    elif isinstance(file_or_path, bytes):
        # If it's bytes, update directly
        hasher.update(file_or_path)
    
    elif hasattr(file_or_path, 'read') and callable(file_or_path.read):
        # If it's a file-like object, read in chunks
        # Store current position
        position = file_or_path.tell()
        
        # Seek to the beginning
        file_or_path.seek(0)
        
        # Read in chunks
        for chunk in read_file_chunks(file_or_path):
            hasher.update(chunk)
        
        # Restore position
        file_or_path.seek(position)
    
    else:
        raise FileException(
            message="Unsupported input type for hash calculation",
            error_code="hash_calculation_failed"
        )
    
    # Return hexadecimal digest
    return hasher.hexdigest()


class FileHandler:
    """
    Class for handling file operations with validation and processing capabilities.
    
    This class provides methods for:
    - Loading files from different sources (path, bytes, file-like object)
    - Validating file types and sizes
    - Getting file content and metadata
    - Saving files to disk
    - Creating temporary files
    - Calculating file hashes
    """
    
    def __init__(self, file_or_path: Optional[Union[str, bytes, BinaryIO]] = None, 
                 filename: Optional[str] = None):
        """
        Initialize the FileHandler with optional file content or path.
        
        Args:
            file_or_path: File path, bytes content, or file-like object
            filename: Optional filename for the file
        """
        self._file_path = None
        self._content = None
        self._content_type = None
        self._filename = filename
        self._file_size = None
        
        if file_or_path is not None:
            # Process the input based on its type
            if isinstance(file_or_path, str) and os.path.isfile(file_or_path):
                # It's a file path
                self._file_path = file_or_path
                if not self._filename:
                    self._filename = os.path.basename(file_or_path)
            
            elif isinstance(file_or_path, bytes):
                # It's bytes content
                self._content = file_or_path
                self._file_size = len(file_or_path)
            
            elif hasattr(file_or_path, 'read') and callable(file_or_path.read):
                # It's a file-like object
                # Store current position
                position = file_or_path.tell()
                
                # Read the content
                file_or_path.seek(0)
                self._content = file_or_path.read()
                self._file_size = len(self._content)
                
                # Try to get filename if not provided
                if not self._filename and hasattr(file_or_path, 'name'):
                    self._filename = os.path.basename(file_or_path.name)
                
                # Restore position
                file_or_path.seek(position)
            
            # If we have content, detect content type
            if self._content or self._file_path:
                try:
                    self._content_type = detect_content_type(
                        self._content or self._file_path, 
                        self._filename
                    )
                except Exception as e:
                    logger.warning(f"Failed to detect content type: {str(e)}")
    
    @classmethod
    def from_path(cls, file_path: str) -> 'FileHandler':
        """
        Create a FileHandler instance from a file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            FileHandler: New FileHandler instance
        """
        return cls(file_path)
    
    @classmethod
    def from_bytes(cls, content: bytes, filename: Optional[str] = None) -> 'FileHandler':
        """
        Create a FileHandler instance from bytes content.
        
        Args:
            content: Bytes content
            filename: Optional filename
            
        Returns:
            FileHandler: New FileHandler instance
        """
        return cls(content, filename)
    
    @classmethod
    def from_file(cls, file_obj: BinaryIO, filename: Optional[str] = None) -> 'FileHandler':
        """
        Create a FileHandler instance from a file-like object.
        
        Args:
            file_obj: File-like object
            filename: Optional filename
            
        Returns:
            FileHandler: New FileHandler instance
        """
        return cls(file_obj, filename)
    
    def get_content(self) -> bytes:
        """
        Get the file content as bytes.
        
        Returns:
            bytes: File content
        """
        if self._content is not None:
            return self._content
        
        if self._file_path is not None:
            with open(self._file_path, 'rb') as f:
                self._content = f.read()
            return self._content
        
        raise FileException(
            message="No file content available",
            error_code="no_file_content"
        )
    
    def get_content_type(self) -> str:
        """
        Get the file's content type.
        
        Returns:
            str: Content type (MIME type)
        """
        if self._content_type is not None:
            return self._content_type
        
        if self._content or self._file_path:
            self._content_type = detect_content_type(
                self._content or self._file_path,
                self._filename
            )
            return self._content_type
        
        raise FileException(
            message="Cannot determine content type",
            error_code="content_type_detection_failed"
        )
    
    def get_size(self) -> int:
        """
        Get the file size in bytes.
        
        Returns:
            int: File size in bytes
        """
        if self._file_size is not None:
            return self._file_size
        
        if self._content is not None:
            self._file_size = len(self._content)
            return self._file_size
        
        if self._file_path is not None:
            self._file_size = os.path.getsize(self._file_path)
            return self._file_size
        
        raise FileException(
            message="Cannot determine file size",
            error_code="file_size_determination_failed"
        )
    
    def validate_type(self, allowed_types: List[str]) -> bool:
        """
        Validate if the file type is allowed.
        
        Args:
            allowed_types: List of allowed MIME types
            
        Returns:
            bool: True if file type is allowed
            
        Raises:
            FileException: If file type is not allowed
        """
        content_type = self.get_content_type()
        
        if content_type not in allowed_types:
            logger.warning(f"Unsupported file format: {content_type}, expected one of {allowed_types}")
            raise FileException(
                message=DOCUMENT_ERRORS['UNSUPPORTED_FILE_FORMAT'],
                error_code='unsupported_file_format',
                details={
                    'content_type': content_type,
                    'allowed_types': allowed_types
                }
            )
        
        return True
    
    def validate_size(self, max_size_mb: Optional[int] = None) -> bool:
        """
        Validate if the file size is within limits.
        
        Args:
            max_size_mb: Maximum allowed size in MB (defaults to MAX_FILE_SIZE_MB)
            
        Returns:
            bool: True if file size is within limits
            
        Raises:
            FileException: If file is too large
        """
        if max_size_mb is None:
            max_size_mb = MAX_FILE_SIZE_MB
        
        max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
        file_size = self.get_size()
        
        if file_size > max_size_bytes:
            logger.warning(f"File size {file_size} bytes exceeds limit of {max_size_bytes} bytes")
            
            # Determine whether it's a document or CSV file for appropriate error message
            if self._filename and self._filename.lower().endswith('.csv'):
                error_message = CSV_ERRORS['FILE_TOO_LARGE']
                error_code = 'csv_file_too_large'
            else:
                error_message = DOCUMENT_ERRORS['DOCUMENT_TOO_LARGE']
                error_code = 'document_too_large'
            
            raise FileException(
                message=error_message,
                error_code=error_code,
                details={
                    'file_size': file_size,
                    'max_size': max_size_bytes,
                    'max_size_mb': max_size_mb
                }
            )
        
        return True
    
    def is_csv(self) -> bool:
        """
        Check if the file is a CSV file.
        
        Returns:
            bool: True if file is a CSV file
        """
        # Check MIME type
        content_type = self.get_content_type()
        if content_type in ALLOWED_CSV_TYPES:
            return True
        
        # Check file extension if filename is available
        if self._filename and get_file_extension(self._filename) == 'csv':
            return True
        
        return False
    
    def save_to_path(self, destination_path: str) -> bool:
        """
        Save the file content to a specified path.
        
        Args:
            destination_path: Path to save the file
            
        Returns:
            bool: True if save was successful
        """
        try:
            # Make sure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(destination_path)), exist_ok=True)
            
            # Get the content and write to the destination
            content = self.get_content()
            with open(destination_path, 'wb') as f:
                f.write(content)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to save file to {destination_path}: {str(e)}")
            raise FileException(
                message="Failed to save file",
                error_code="file_save_failed",
                details={"error": str(e), "path": destination_path}
            )
    
    def create_temp_file(self, suffix: Optional[str] = None) -> str:
        """
        Create a temporary file with the file content.
        
        Args:
            suffix: Optional file suffix (e.g., '.csv')
            
        Returns:
            str: Path to temporary file
        """
        content = self.get_content()
        
        # If suffix is not provided but we have a filename, try to use its extension
        if suffix is None and self._filename:
            ext = get_file_extension(self._filename)
            if ext:
                suffix = f".{ext}"
        
        return create_temp_file(content, suffix)
    
    def get_hash(self, hash_algorithm: str = 'sha256') -> str:
        """
        Calculate hash of the file content.
        
        Args:
            hash_algorithm: Hash algorithm to use (default: sha256)
            
        Returns:
            str: Hexadecimal hash digest
        """
        content = self.get_content()
        
        # Import hashlib here to avoid circular imports
        import hashlib
        
        # Create hash object and update with content
        hasher = hashlib.new(hash_algorithm)
        hasher.update(content)
        
        # Return hexadecimal digest
        return hasher.hexdigest()