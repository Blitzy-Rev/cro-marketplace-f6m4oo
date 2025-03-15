"""
Core logging module for the Molecular Data Management and CRO Integration Platform.

This module provides a centralized logging configuration, context-aware loggers,
and utilities for distributed tracing with correlation IDs. It implements structured 
JSON logging with consistent formatting across all application components.
"""

import logging
import json
import sys
import typing
from uuid import uuid4
import contextvars
from datetime import datetime

from .config import settings

# Context variable to store correlation ID across async boundaries
CORRELATION_ID_CTX_VAR = contextvars.ContextVar('correlation_id', default=None)

# Default log format for JSON structured logging
DEFAULT_LOG_FORMAT = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "correlation_id": "%(correlation_id)s", "module": "%(name)s", "message": "%(message)s"}'


class JsonFormatter(logging.Formatter):
    """Custom log formatter that outputs logs in JSON format."""
    
    def __init__(self, fmt: str, datefmt: str = None) -> None:
        """
        Initialize the JSON formatter with format string and datetime format.
        
        Args:
            fmt: Format string for log records
            datefmt: Format string for datetime objects
        """
        super().__init__(fmt=fmt, datefmt=datefmt)
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON string.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted JSON log entry
        """
        # Ensure correlation_id is available in the record
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = get_correlation_id()
            
        # Format the record using the parent formatter
        formatted = super().format(record)
        
        try:
            # Parse the formatted string as JSON and add any additional fields
            log_data = json.loads(formatted)
            
            # Add exception info if available
            if record.exc_info:
                log_data['exception'] = self.formatException(record.exc_info)
                
            # Convert back to JSON string
            return json.dumps(log_data)
        except (json.JSONDecodeError, TypeError):
            # If JSON parsing fails, return the original formatted string
            return formatted
    
    def formatException(self, exc_info) -> str:
        """
        Format an exception for inclusion in a log record.
        
        Args:
            exc_info: Exception information tuple
            
        Returns:
            Formatted exception information
        """
        # Use the parent formatter to format the exception
        formatted_exc = super().formatException(exc_info)
        return formatted_exc


class CorrelationIdFilter(logging.Filter):
    """Log filter that adds correlation ID to log records."""
    
    def __init__(self) -> None:
        """Initialize the correlation ID filter."""
        super().__init__()
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add correlation ID to the log record.
        
        Args:
            record: Log record to modify
            
        Returns:
            Always returns True to include the record
        """
        # Get the current correlation ID and add it to the record
        record.correlation_id = get_correlation_id()
        return True


class RequestContextAdapter(logging.LoggerAdapter):
    """Adapter for loggers that adds request context information to log records."""
    
    def __init__(self, logger: logging.Logger, extra: dict) -> None:
        """
        Initialize the request context adapter with a logger and extra context.
        
        Args:
            logger: The logger to adapt
            extra: Dictionary with extra context information
        """
        super().__init__(logger, extra or {})
        self.extra = extra or {}
    
    def process(self, msg, kwargs) -> typing.Tuple[str, dict]:
        """
        Process the log record by adding request context information.
        
        Args:
            msg: The log message
            kwargs: Additional keyword arguments
            
        Returns:
            Tuple of (message, kwargs) with enhanced context
        """
        # Ensure correlation_id is included in the extra context
        kwargs_copy = kwargs.copy()
        extra = kwargs_copy.get('extra', {})
        
        # Add correlation ID if not present
        if 'correlation_id' not in extra:
            extra['correlation_id'] = get_correlation_id()
        
        # Add all extra context items
        for key, value in self.extra.items():
            extra[key] = value
        
        kwargs_copy['extra'] = extra
        return msg, kwargs_copy


def setup_logging(log_level: str = None) -> None:
    """
    Configure the global logging system with appropriate handlers and formatters.
    
    Args:
        log_level: Optional override for the log level (defaults to settings.LOG_LEVEL)
    """
    # Get log level from settings if not provided
    level = log_level or settings.LOG_LEVEL
    level_value = getattr(logging, level.upper(), logging.INFO)
    
    # Create a JSON formatter
    formatter = JsonFormatter(DEFAULT_LOG_FORMAT)
    
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level_value)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add a stream handler that outputs to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # Add correlation ID filter to the handler
    correlation_filter = CorrelationIdFilter()
    handler.addFilter(correlation_filter)
    
    # Add the handler to the root logger
    root_logger.addHandler(handler)
    
    # Set appropriate log levels for third-party libraries
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('alembic').setLevel(logging.WARNING)
    
    # Log the setup completion
    root_logger.info(
        f"Logging configured: level={level}, app={settings.PROJECT_NAME}, env={settings.ENV}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance configured with the application's logging settings.
    
    Args:
        name: Name for the logger (typically module name)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def get_correlation_id() -> str:
    """
    Get the current correlation ID from context or generate a new one.
    
    Returns:
        Correlation ID for request tracing
    """
    correlation_id = CORRELATION_ID_CTX_VAR.get()
    if correlation_id is None:
        correlation_id = str(uuid4())
        CORRELATION_ID_CTX_VAR.set(correlation_id)
    return correlation_id


def set_correlation_id(correlation_id: str) -> None:
    """
    Set the correlation ID in the current execution context.
    
    Args:
        correlation_id: Correlation ID to set
    """
    CORRELATION_ID_CTX_VAR.set(correlation_id)


def clear_correlation_id() -> None:
    """Clear the correlation ID from the current execution context."""
    CORRELATION_ID_CTX_VAR.set(None)