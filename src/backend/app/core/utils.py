"""
Core utility functions for the Molecular Data Management and CRO Integration Platform.

This module provides common helper functions used throughout the application, including
data manipulation, formatting, type conversion, and other general-purpose utilities.
"""

import os
import uuid
import datetime
import json
import typing
import logging
import re
import time

from .exceptions import BaseAppException
from .config import settings

# Set up logging
logger = logging.getLogger(__name__)


def generate_uuid() -> str:
    """Generate a unique identifier string.
    
    Returns:
        str: A unique UUID string
    """
    return str(uuid.uuid4())


def format_datetime(dt: datetime.datetime) -> str:
    """Format a datetime object to ISO 8601 string.
    
    Args:
        dt: Datetime object to format
        
    Returns:
        str: ISO 8601 formatted datetime string
    """
    if dt is None:
        return None
    return dt.isoformat()


def parse_datetime(datetime_str: str) -> datetime.datetime:
    """Parse an ISO 8601 datetime string to datetime object.
    
    Args:
        datetime_str: ISO 8601 formatted datetime string
        
    Returns:
        datetime.datetime: Parsed datetime object
    """
    if not datetime_str:
        return None
    return datetime.datetime.fromisoformat(datetime_str)


def truncate_string(text: str, max_length: int) -> str:
    """Truncate a string to a specified length with ellipsis.
    
    Args:
        text: The string to truncate
        max_length: Maximum length of the string
        
    Returns:
        str: Truncated string
    """
    if text is None:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def safe_json_loads(json_str: str, default_value: typing.Any = None) -> typing.Any:
    """Safely parse a JSON string with error handling.
    
    Args:
        json_str: JSON string to parse
        default_value: Default value to return on error
        
    Returns:
        any: Parsed JSON object or default value on error
    """
    if not json_str:
        return default_value
    
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Error parsing JSON: {e}")
        return default_value


def safe_json_dumps(obj: typing.Any, default_value: str = "{}") -> str:
    """Safely convert an object to a JSON string with error handling.
    
    Args:
        obj: Object to convert to JSON
        default_value: Default value to return on error
        
    Returns:
        str: JSON string or default value on error
    """
    if obj is None:
        return default_value
    
    try:
        return json.dumps(obj)
    except (TypeError, OverflowError) as e:
        logger.error(f"Error converting to JSON: {e}")
        return default_value


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        str: Human-readable file size string
    """
    if size_bytes < 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024
        i += 1
    
    # Round to 2 decimal places for larger units, use integers for bytes
    if i == 0:
        return f"{int(size_bytes)} {units[i]}"
    else:
        return f"{size_bytes:.2f} {units[i]}"


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing invalid characters.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        str: Sanitized filename
    """
    # Keep alphanumeric characters, dot, hyphen, and underscore
    # Replace spaces with underscores
    # Remove all other characters
    if not filename:
        return ""
    
    # Replace spaces with underscores
    filename = filename.replace(" ", "_")
    
    # Keep only alphanumeric, dot, hyphen, and underscore
    pattern = r"[^a-zA-Z0-9._\-]"
    return re.sub(pattern, "", filename)


def get_file_extension(filename: str) -> str:
    """Extract file extension from a filename.
    
    Args:
        filename: The filename to extract extension from
        
    Returns:
        str: File extension (lowercase) or empty string
    """
    if not filename:
        return ""
    
    # Split by dot and get the last part
    parts = filename.rsplit(".", 1)
    if len(parts) > 1:
        return "." + parts[1].lower()
    return ""


def is_valid_file_extension(filename: str, allowed_extensions: list) -> bool:
    """Check if a file extension is in a list of allowed extensions.
    
    Args:
        filename: The filename to check
        allowed_extensions: List of allowed file extensions
        
    Returns:
        bool: True if extension is allowed, False otherwise
    """
    extension = get_file_extension(filename)
    return extension.lower() in [ext.lower() for ext in allowed_extensions]


def create_directory_if_not_exists(directory_path: str) -> bool:
    """Create a directory if it doesn't exist.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
        return True
    except OSError as e:
        logger.error(f"Error creating directory {directory_path}: {e}")
        return False


def flatten_dict(nested_dict: dict, parent_key: str = "") -> dict:
    """Flatten a nested dictionary with dot notation for keys.
    
    Args:
        nested_dict: Nested dictionary to flatten
        parent_key: Parent key prefix
        
    Returns:
        dict: Flattened dictionary
    """
    result = {}
    
    for key, value in nested_dict.items():
        new_key = f"{parent_key}.{key}" if parent_key else key
        
        if isinstance(value, dict):
            # Recursively flatten nested dictionaries
            result.update(flatten_dict(value, new_key))
        else:
            # Add leaf node with full path key
            result[new_key] = value
    
    return result


def chunk_list(items: list, chunk_size: int) -> list:
    """Split a list into chunks of specified size.
    
    Args:
        items: List to split
        chunk_size: Size of each chunk
        
    Returns:
        list: List of chunks (lists)
    """
    if not items:
        return []
    
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def retry_operation(
    operation: typing.Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions_to_retry: tuple = (Exception,)
) -> typing.Any:
    """Retry an operation with exponential backoff.
    
    Args:
        operation: Callable to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Factor to multiply delay for each retry
        exceptions_to_retry: Exceptions that should trigger a retry
        
    Returns:
        any: Result of the operation
        
    Raises:
        Exception: The last exception raised by the operation after all retries
    """
    retry_count = 0
    delay = initial_delay
    
    while True:
        try:
            return operation()
        except exceptions_to_retry as e:
            retry_count += 1
            if retry_count > max_retries:
                logger.error(f"Max retries ({max_retries}) exceeded for operation. Last error: {e}")
                raise
            
            logger.warning(f"Retry {retry_count}/{max_retries} after error: {e}. Waiting {delay} seconds.")
            time.sleep(delay)
            delay *= backoff_factor


def deep_merge_dicts(dict1: dict, dict2: dict) -> dict:
    """Deep merge two dictionaries, with values from dict2 taking precedence.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (values override dict1)
        
    Returns:
        dict: Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = deep_merge_dicts(result[key], value)
        else:
            # Override or add key-value pair from dict2
            result[key] = value
    
    return result


def format_error_message(exception: Exception) -> dict:
    """Format an exception into a standardized error message.
    
    Args:
        exception: The exception to format
        
    Returns:
        dict: Standardized error message dictionary
    """
    error = {
        "error_code": "internal_error",
        "message": str(exception),
        "status_code": 500,
        "details": {}
    }
    
    # If it's our custom exception, use its attributes
    if isinstance(exception, BaseAppException):
        error["error_code"] = exception.error_code
        error["message"] = exception.message
        error["status_code"] = exception.status_code
        if hasattr(exception, "details") and exception.details:
            error["details"] = exception.details
    
    # Add stack trace in debug mode
    if settings.DEBUG:
        import traceback
        error["details"]["traceback"] = traceback.format_exc()
    
    return error


def camel_to_snake(camel_str: str) -> str:
    """Convert a camelCase string to snake_case.
    
    Args:
        camel_str: camelCase string
        
    Returns:
        str: snake_case string
    """
    if not camel_str:
        return ""
    
    # Add underscore before uppercase letters and convert to lowercase
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", camel_str)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def snake_to_camel(snake_str: str) -> str:
    """Convert a snake_case string to camelCase.
    
    Args:
        snake_str: snake_case string
        
    Returns:
        str: camelCase string
    """
    if not snake_str:
        return ""
    
    # Split by underscore and capitalize each part except the first one
    parts = snake_str.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class Timer:
    """Context manager for timing code execution."""
    
    def __init__(self, name: str = "Operation"):
        """Initialize the timer with an optional name.
        
        Args:
            name: Name of the operation being timed
        """
        self.name = name
        self.start_time = None
        self.end_time = None
        self.elapsed_time = None
    
    def __enter__(self) -> "Timer":
        """Start the timer when entering the context.
        
        Returns:
            Timer: Self reference for context manager
        """
        self.start_time = datetime.datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop the timer when exiting the context and log the elapsed time.
        
        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        self.end_time = datetime.datetime.now()
        delta = self.end_time - self.start_time
        self.elapsed_time = delta.total_seconds() * 1000  # Convert to milliseconds
        logger.info(f"{self.name} completed in {self.elapsed_time:.2f} ms")


class Paginator:
    """Utility class for handling pagination of query results."""
    
    def __init__(self, page: int, page_size: int, total_items: int):
        """Initialize the paginator with pagination parameters.
        
        Args:
            page: Current page number (1-based)
            page_size: Number of items per page
            total_items: Total number of items
        """
        self.page = max(1, page)  # Ensure page is at least 1
        self.page_size = page_size
        self.total_items = total_items
        self.total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 0  # Ceiling division
        
        # Validate page is within range
        if self.page > self.total_pages and self.total_pages > 0:
            self.page = self.total_pages
    
    def get_offset(self) -> int:
        """Calculate the offset for database queries.
        
        Returns:
            int: Offset value for query
        """
        return (self.page - 1) * self.page_size
    
    def get_limit(self) -> int:
        """Get the limit value for database queries.
        
        Returns:
            int: Limit value for query
        """
        return self.page_size
    
    def get_pagination_info(self) -> dict:
        """Get pagination metadata for API responses.
        
        Returns:
            dict: Pagination metadata dictionary
        """
        return {
            "page": self.page,
            "page_size": self.page_size,
            "total_items": self.total_items,
            "total_pages": self.total_pages
        }