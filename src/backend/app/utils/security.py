"""
Utility functions for security operations in the Molecular Data Management and CRO Integration Platform.

This module provides additional security helpers that complement the core security functionality,
focusing on data protection, secure file handling, and content security features.
"""

import base64
import hashlib
import hmac
import secrets
from cryptography.fernet import Fernet  # cryptography.fernet version: ^39.0.0
import bleach  # bleach version: ^6.0.0
import magic  # python-magic version: ^0.4.27
from typing import Optional, Dict, List, Union, Any, AnyStr

from ..core.settings import ENCRYPTION_KEY, HASH_SALT
from ..core.logging import get_logger
from ..core.exceptions import SecurityException
from ..constants.error_messages import SECURITY_ERRORS

# Initialize logger
logger = get_logger(__name__)

# Define allowed file types for security validation
ALLOWED_FILE_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/csv',
    'application/json',
    'image/jpeg',
    'image/png'
]

# Maximum file size (100MB)
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024


def encrypt_data(data: AnyStr) -> bytes:
    """
    Encrypt sensitive data using Fernet symmetric encryption.
    
    Args:
        data: Data to encrypt (string or bytes)
        
    Returns:
        Encrypted data as bytes
    """
    # Convert data to bytes if it's a string
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    try:
        # Create a Fernet cipher using the ENCRYPTION_KEY from settings
        cipher = Fernet(ENCRYPTION_KEY)
        
        # Encrypt the data using the cipher
        encrypted_data = cipher.encrypt(data)
        
        return encrypted_data
    except Exception as e:
        logger.error(f"Encryption failed: {str(e)}")
        raise SecurityException(
            message="Failed to encrypt data", 
            error_code="encryption_failed",
            details={"original_error": str(e)}
        )


def decrypt_data(encrypted_data: bytes) -> bytes:
    """
    Decrypt data that was encrypted with encrypt_data.
    
    Args:
        encrypted_data: The encrypted data as bytes
        
    Returns:
        Decrypted data as bytes
        
    Raises:
        SecurityException: If decryption fails
    """
    try:
        # Create a Fernet cipher using the ENCRYPTION_KEY from settings
        cipher = Fernet(ENCRYPTION_KEY)
        
        # Try to decrypt the data using the cipher
        decrypted_data = cipher.decrypt(encrypted_data)
        
        return decrypted_data
    except Exception as e:
        # Catch any exceptions and raise SecurityException with appropriate message
        error_msg = f"Failed to decrypt data: {str(e)}"
        logger.error(error_msg)
        raise SecurityException(
            message=error_msg, 
            error_code="decryption_failed",
            details={"original_error": str(e)}
        )


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Length of the token in bytes (default: 32)
        
    Returns:
        Secure random token as a hex string
    """
    # Use secrets.token_hex to generate a secure random token of specified length
    return secrets.token_hex(length)


def compute_hash(data: AnyStr, algorithm: str = 'sha256') -> str:
    """
    Compute a secure hash of data for integrity verification.
    
    Args:
        data: Data to hash (string or bytes)
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Computed hash as a hex string
    """
    # Convert data to bytes if it's a string
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    # Create a hash object using the specified algorithm
    hash_obj = hashlib.new(algorithm)
    
    # Update the hash with the data and the HASH_SALT from settings
    hash_obj.update(data)
    hash_obj.update(HASH_SALT.encode('utf-8'))
    
    # Return the computed hash as a hex string
    return hash_obj.hexdigest()


def verify_hash(data: AnyStr, expected_hash: str, algorithm: str = 'sha256') -> bool:
    """
    Verify that a hash matches the expected value for data integrity.
    
    Args:
        data: Data to verify
        expected_hash: Expected hash value
        algorithm: Hash algorithm used (default: sha256)
        
    Returns:
        True if hash matches, False otherwise
    """
    # Compute the hash of the data using compute_hash with the same algorithm
    computed_hash = compute_hash(data, algorithm)
    
    # Compare the computed hash with the expected hash using a constant-time comparison
    return hmac.compare_digest(computed_hash, expected_hash)


def generate_hmac(data: AnyStr, key: Optional[str] = None) -> str:
    """
    Generate an HMAC for data authentication.
    
    Args:
        data: Data to authenticate
        key: Secret key for HMAC (uses HASH_SALT if None)
        
    Returns:
        HMAC signature as a hex string
    """
    # Convert data to bytes if it's a string
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    # Use the provided key or HASH_SALT from settings if key is None
    hmac_key = key.encode('utf-8') if key is not None else HASH_SALT.encode('utf-8')
    
    # Create an HMAC using SHA-256 and the key
    hmac_obj = hmac.new(hmac_key, data, hashlib.sha256)
    
    # Return the HMAC digest as a hex string
    return hmac_obj.hexdigest()


def verify_hmac(data: AnyStr, signature: str, key: Optional[str] = None) -> bool:
    """
    Verify an HMAC signature for data authentication.
    
    Args:
        data: Data to verify
        signature: HMAC signature to verify
        key: Secret key for HMAC (uses HASH_SALT if None)
        
    Returns:
        True if signature is valid, False otherwise
    """
    # Generate an HMAC for the data using the same key
    computed_signature = generate_hmac(data, key)
    
    # Compare the generated HMAC with the provided signature using a constant-time comparison
    return hmac.compare_digest(computed_signature, signature)


def sanitize_html(html_content: str, 
                 allowed_tags: Optional[List[str]] = None, 
                 allowed_attributes: Optional[Dict[str, List[str]]] = None) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.
    
    Args:
        html_content: HTML content to sanitize
        allowed_tags: List of allowed HTML tags (defaults to a safe subset)
        allowed_attributes: Dictionary of allowed attributes for each tag
        
    Returns:
        Sanitized HTML content
    """
    # Define safe defaults if not provided
    if allowed_tags is None:
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 
                        'em', 'i', 'li', 'ol', 'p', 'strong', 'ul']
    
    if allowed_attributes is None:
        allowed_attributes = {
            'a': ['href', 'title'],
            'abbr': ['title'],
            'acronym': ['title'],
        }
    
    # Use bleach.clean to sanitize the HTML content
    sanitized_content = bleach.clean(
        html_content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    return sanitized_content


def validate_file_type(file_content: bytes, claimed_content_type: str) -> bool:
    """
    Validate that a file's content matches its claimed type for security.
    
    Args:
        file_content: Binary content of the file
        claimed_content_type: Content type claimed by the client
        
    Returns:
        True if file type is valid and matches claimed type, False otherwise
    """
    try:
        # Use python-magic to detect the actual MIME type of the file content
        detected_type = magic.from_buffer(file_content, mime=True)
        
        # Check if the detected type is in the ALLOWED_FILE_TYPES list
        if detected_type not in ALLOWED_FILE_TYPES:
            logger.warning(f"Detected file type {detected_type} is not in the allowed types list")
            return False
        
        # Verify that the detected type matches or is compatible with the claimed type
        if detected_type != claimed_content_type:
            # Special cases for types that might be reported differently but are compatible
            compatible_pairs = [
                ('application/pdf', 'application/pdf'),
                ('text/csv', 'text/csv'),
                ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/docx')
            ]
            
            if (detected_type, claimed_content_type) not in compatible_pairs:
                logger.warning(f"Claimed content type {claimed_content_type} does not match detected type {detected_type}")
                return False
        
        return True
    except Exception as e:
        logger.error(f"Error validating file type: {str(e)}")
        return False


def validate_file_size(file_content_or_size: Union[bytes, int], max_size: Optional[int] = None) -> bool:
    """
    Validate that a file's size is within acceptable limits.
    
    Args:
        file_content_or_size: Either file content as bytes or file size as int
        max_size: Maximum allowed size in bytes (defaults to MAX_FILE_SIZE_BYTES)
        
    Returns:
        True if file size is within limits, False otherwise
    """
    # Determine the file size from the input
    if isinstance(file_content_or_size, bytes):
        file_size = len(file_content_or_size)
    else:
        file_size = file_content_or_size
    
    # Use the provided max_size or the global MAX_FILE_SIZE_BYTES if not specified
    max_allowed_size = max_size if max_size is not None else MAX_FILE_SIZE_BYTES
    
    # Check if the file size is within the maximum allowed size
    if file_size > max_allowed_size:
        logger.warning(f"File size {file_size} exceeds maximum allowed size {max_allowed_size}")
        return False
    
    return True


def secure_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal and command injection.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove any directory components from the filename
    cleaned_name = filename.replace('/', '').replace('\\', '')
    
    # Remove any potentially dangerous characters
    cleaned_name = ''.join(c for c in cleaned_name if c.isalnum() or c in '._- ')
    
    # Ensure the filename is not empty or just an extension
    if not cleaned_name or cleaned_name.startswith('.'):
        cleaned_name = 'unnamed_file' + (cleaned_name if cleaned_name.startswith('.') else '')
    
    return cleaned_name


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging or display purposes.
    
    Args:
        data: Data to mask
        visible_chars: Number of characters to show at start and end
        
    Returns:
        Masked data with only partial visibility
    """
    # Determine the length of the data
    data_length = len(data)
    
    # If data is shorter than twice the visible_chars, show only first and last character
    if data_length <= 2 * visible_chars:
        if data_length <= 2:
            return '*' * data_length
        else:
            return data[0] + '*' * (data_length - 2) + data[-1]
    
    # Otherwise, show the first and last visible_chars characters with asterisks in between
    return data[:visible_chars] + '*' * (data_length - 2 * visible_chars) + data[-visible_chars:]


def generate_secure_id(prefix: str, length: int = 16) -> str:
    """
    Generate a secure ID for sensitive resources.
    
    Args:
        prefix: Prefix for the ID
        length: Length of the random part
        
    Returns:
        Secure ID with prefix
    """
    # Generate a secure random token using generate_secure_token
    token = generate_secure_token(length)
    
    # Combine the prefix with the token
    secure_id = f"{prefix}-{token}"
    
    return secure_id


def is_secure_password(password: str) -> Dict[str, Any]:
    """
    Check if a password meets security requirements.
    
    Args:
        password: Password to check
        
    Returns:
        Dictionary with success flag and messages
    """
    result = {
        "valid": True,
        "messages": []
    }
    
    # Check minimum length (at least 12 characters)
    if len(password) < 12:
        result["valid"] = False
        result["messages"].append("Password must be at least 12 characters long")
    
    # Check for presence of uppercase letters
    if not any(c.isupper() for c in password):
        result["valid"] = False
        result["messages"].append("Password must contain at least one uppercase letter")
    
    # Check for presence of lowercase letters
    if not any(c.islower() for c in password):
        result["valid"] = False
        result["messages"].append("Password must contain at least one lowercase letter")
    
    # Check for presence of digits
    if not any(c.isdigit() for c in password):
        result["valid"] = False
        result["messages"].append("Password must contain at least one digit")
    
    # Check for presence of special characters
    special_chars = "!@#$%^&*()-_=+[]{}|;:'\",.<>/?"
    if not any(c in special_chars for c in password):
        result["valid"] = False
        result["messages"].append("Password must contain at least one special character")
    
    # Check for common passwords or patterns (simplified check)
    common_passwords = ["password", "123456", "qwerty", "admin", "welcome"]
    if password.lower() in common_passwords:
        result["valid"] = False
        result["messages"].append("Password is too common")
    
    # Check for repeating patterns
    if any(password[i] == password[i+1] == password[i+2] for i in range(len(password)-2)):
        result["valid"] = False
        result["messages"].append("Password contains repeating patterns")
    
    return result


def create_audit_event(event_type: str, 
                      user_id: str, 
                      resource_type: str,
                      resource_id: Optional[str] = None,
                      additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a standardized audit event for security logging.
    
    Args:
        event_type: Type of security event
        user_id: ID of the user who performed the action
        resource_type: Type of resource affected
        resource_id: ID of the resource affected (optional)
        additional_data: Additional event data (optional)
        
    Returns:
        Structured audit event data
    """
    import datetime
    
    # Create a dictionary with standard audit fields
    audit_event = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "resource_type": resource_type,
        "event_id": generate_secure_token(16)
    }
    
    # Add resource_id if provided
    if resource_id:
        audit_event["resource_id"] = resource_id
    
    # Add any additional_data if provided
    if additional_data:
        audit_event["details"] = additional_data
    
    return audit_event


def log_security_event(event_type: str, 
                      message: str, 
                      context: Optional[Dict[str, Any]] = None,
                      severity: str = "info") -> None:
    """
    Log a security event with appropriate severity and formatting.
    
    Args:
        event_type: Type of security event
        message: Event message
        context: Additional context information
        severity: Log severity level (info, warning, error, critical)
    """
    context_dict = context or {}
    
    # Format the log message with event type and context
    log_message = f"SECURITY_EVENT[{event_type}]: {message}"
    
    # Log the message with the appropriate severity level
    if severity == "info":
        logger.info(log_message, extra=context_dict)
    elif severity == "warning":
        logger.warning(log_message, extra=context_dict)
    elif severity == "error":
        logger.error(log_message, extra=context_dict)
    elif severity == "critical":
        logger.critical(log_message, extra=context_dict)
    else:
        logger.info(log_message, extra=context_dict)
    
    # If severity is 'critical' or 'error', also log to security audit log
    if severity in ["critical", "error"]:
        # This would typically go to a separate security audit log
        # For simplicity, we're just using the same logger
        audit_context = {
            "security_audit": True,
            "event_type": event_type,
            **context_dict
        }
        logger.critical(f"SECURITY_AUDIT: {message}", extra=audit_context)


class SecureFile:
    """Class for handling files with security validations and encryption."""
    
    def __init__(self, content: bytes, filename: str, content_type: str, validate: bool = True):
        """
        Initialize a SecureFile with content validation.
        
        Args:
            content: File content as bytes
            filename: Original filename
            content_type: MIME type of the file
            validate: Whether to perform security validations
            
        Raises:
            SecurityException: If validation fails
        """
        # Store the file content, sanitized filename, and content type
        self._content = content
        self._filename = secure_filename(filename)
        self._content_type = content_type
        self._is_encrypted = False
        
        # If validate is True, perform security validations
        if validate:
            # Validate file size using validate_file_size
            if not validate_file_size(self._content):
                raise SecurityException(
                    message=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES} bytes",
                    error_code="file_size_exceeded"
                )
            
            # Validate file type using validate_file_type
            if not validate_file_type(self._content, self._content_type):
                raise SecurityException(
                    message=f"File type validation failed or mismatched content type: {self._content_type}",
                    error_code="invalid_file_type"
                )
    
    def encrypt(self) -> None:
        """
        Encrypt the file content if not already encrypted.
        """
        # Check if file is already encrypted
        if self._is_encrypted:
            return
        
        # If not encrypted, encrypt the content using encrypt_data
        self._content = encrypt_data(self._content)
        
        # Update _is_encrypted flag
        self._is_encrypted = True
    
    def decrypt(self) -> None:
        """
        Decrypt the file content if encrypted.
        """
        # Check if file is encrypted
        if not self._is_encrypted:
            return
        
        # If encrypted, decrypt the content using decrypt_data
        self._content = decrypt_data(self._content)
        
        # Update _is_encrypted flag
        self._is_encrypted = False
    
    def get_content(self, decrypt_if_needed: bool = True) -> bytes:
        """
        Get the file content, decrypting if necessary.
        
        Args:
            decrypt_if_needed: Whether to decrypt the content if it's encrypted
            
        Returns:
            File content as bytes
        """
        # If content is encrypted and decrypt_if_needed is True, decrypt the content
        if self._is_encrypted and decrypt_if_needed:
            content = decrypt_data(self._content)
            return content
        
        # Otherwise, return the content as is
        return self._content
    
    def get_filename(self) -> str:
        """
        Get the sanitized filename.
        
        Returns:
            Sanitized filename
        """
        return self._filename
    
    def get_content_type(self) -> str:
        """
        Get the content type.
        
        Returns:
            Content type
        """
        return self._content_type
    
    def is_encrypted(self) -> bool:
        """
        Check if the file content is encrypted.
        
        Returns:
            True if encrypted, False otherwise
        """
        return self._is_encrypted
    
    def compute_checksum(self, use_encrypted_content: bool = False) -> str:
        """
        Compute a checksum of the file content for integrity verification.
        
        Args:
            use_encrypted_content: Whether to use the encrypted content for checksum
            
        Returns:
            Checksum as a hex string
        """
        # Determine which content to use based on use_encrypted_content flag
        if use_encrypted_content:
            content = self._content
        else:
            content = self.get_content(decrypt_if_needed=True)
        
        # Compute hash of the content using compute_hash
        return compute_hash(content)
    
    def to_dict(self, include_content: bool = False) -> Dict[str, Any]:
        """
        Convert the SecureFile to a dictionary representation.
        
        Args:
            include_content: Whether to include the file content in the dictionary
            
        Returns:
            Dictionary representation of the file
        """
        # Create a dictionary with filename and content_type
        result = {
            "filename": self._filename,
            "content_type": self._content_type,
            "is_encrypted": self._is_encrypted,
            "content_size": len(self._content)
        }
        
        # Add checksum to the dictionary
        result["checksum"] = self.compute_checksum(use_encrypted_content=True)
        
        # If include_content is True, add base64-encoded content
        if include_content:
            result["content"] = base64.b64encode(self._content).decode('utf-8')
        
        return result