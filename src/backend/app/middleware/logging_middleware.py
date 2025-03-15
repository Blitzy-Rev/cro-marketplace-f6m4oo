"""
Logging middleware for the Molecular Data Management and CRO Integration Platform.

This middleware captures HTTP request and response details, tracks performance metrics,
and provides distributed tracing capabilities through correlation IDs. It ensures
comprehensive logging for monitoring, troubleshooting, and compliance requirements.
"""

import time
import uuid
import json
import typing
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..core.logging import get_logger, get_correlation_id, set_correlation_id
from ..core.config import settings

# Initialize logger
logger = get_logger(__name__)

# Paths to exclude from detailed logging
EXCLUDED_PATHS = ['/health', '/metrics', '/docs', '/redoc', '/openapi.json']


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request headers or connection info.
    
    Args:
        request: The HTTP request object
        
    Returns:
        Client IP address as string
    """
    # Check for X-Forwarded-For header (common when behind a proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs in a comma-separated list
        # The first one is the original client IP
        return forwarded_for.split(",")[0].strip()
    
    # Check for X-Real-IP header (used by some proxies)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to the direct client address
    if request.client:
        return request.client.host
    
    # If all else fails
    return "unknown"


def should_log_path(path: str) -> bool:
    """
    Determine if a path should be logged based on exclusion rules.
    
    Args:
        path: The request path
        
    Returns:
        True if path should be logged, False otherwise
    """
    # Check exact path matches
    if path in EXCLUDED_PATHS:
        return False
    
    # Check path prefixes
    for excluded_path in EXCLUDED_PATHS:
        if path.startswith(excluded_path):
            return False
    
    # Path should be logged
    return True


def truncate_body(body: typing.Any, max_length: int = 1000) -> str:
    """
    Truncate request/response body to prevent excessive logging.
    
    Args:
        body: The body content to truncate
        max_length: Maximum length before truncation
        
    Returns:
        Truncated body as string
    """
    # Convert body to string if it's not already
    if body is None:
        return "None"
    
    try:
        if isinstance(body, bytes):
            body_str = body.decode('utf-8')
        else:
            body_str = str(body)
            
        # Truncate if needed
        if len(body_str) > max_length:
            return f"{body_str[:max_length]}... [truncated, {len(body_str)} characters total]"
        return body_str
    except Exception as e:
        return f"[Error serializing body: {str(e)}]"


def sanitize_headers(headers: dict) -> dict:
    """
    Remove sensitive information from headers before logging.
    
    Args:
        headers: Dictionary of HTTP headers
        
    Returns:
        Sanitized headers dictionary
    """
    # Create a copy to avoid modifying the original
    sanitized = dict(headers)
    
    # List of headers that might contain sensitive information
    sensitive_headers = [
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "api-key",
        "password",
        "x-auth-token",
        "access-token",
        "refresh-token",
    ]
    
    # Redact sensitive header values
    for header in sensitive_headers:
        if header in sanitized:
            sanitized[header] = "[REDACTED]"
    
    return sanitized


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses with performance metrics.
    
    This middleware captures request/response details, measures processing time,
    and implements distributed tracing with correlation IDs.
    """
    
    def __init__(self, app):
        """
        Initialize the logging middleware.
        
        Args:
            app: The ASGI application
        """
        super().__init__(app)
        self.logger = get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next: typing.Callable) -> Response:
        """
        Process each request through the logging middleware.
        
        This method is required by BaseHTTPMiddleware but delegates to async_dispatch
        for consistency with the expected interface.
        
        Args:
            request: The HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            The HTTP response
        """
        return await self.async_dispatch(request, call_next)
    
    async def async_dispatch(self, request: Request, call_next: typing.Callable) -> Response:
        """
        Process each request through the logging middleware.
        
        Args:
            request: The HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            The HTTP response
        """
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Set correlation ID in context for this request
        set_correlation_id(correlation_id)
        
        # Extract request information
        path = request.url.path
        client_ip = get_client_ip(request)
        method = request.method
        query_params = dict(request.query_params)
        
        # Only log details for non-excluded paths
        should_log = should_log_path(path)
        
        # Log request details if needed
        if should_log:
            # Sanitize and log request headers
            headers = sanitize_headers(dict(request.headers))
            
            # Log the request (without body to avoid consuming the stream)
            self.logger.info(
                f"Request received: {method} {path}",
                extra={
                    "correlation_id": correlation_id,
                    "client_ip": client_ip,
                    "method": method,
                    "path": path,
                    "query_params": query_params,
                    "content_type": headers.get("content-type", "unknown"),
                    "content_length": headers.get("content-length", "unknown"),
                }
            )
        
        # Record start time for performance measurement
        start_time = time.time()
        
        try:
            # Process the request with the next handler
            response = await call_next(request)
            
            # Calculate request processing time
            process_time = time.time() - start_time
            process_time_ms = round(process_time * 1000, 2)
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            if should_log:
                # Basic request completion log
                self.logger.info(
                    f"Request completed: {method} {path} - {response.status_code} in {process_time_ms}ms",
                    extra={
                        "correlation_id": correlation_id,
                        "status_code": response.status_code,
                        "process_time_ms": process_time_ms,
                    }
                )
                
                # More detailed response logging in debug mode
                if settings.DEBUG:
                    # Sanitize response headers
                    response_headers = sanitize_headers(dict(response.headers))
                    
                    # Log response details
                    self.logger.debug(
                        f"Response details: {method} {path}",
                        extra={
                            "correlation_id": correlation_id,
                            "response_headers": response_headers,
                            "content_type": response.headers.get("content-type", "unknown"),
                            "content_length": response.headers.get("content-length", "unknown"),
                        }
                    )
            
            return response
            
        except Exception as exc:
            # Calculate processing time even for exceptions
            process_time = time.time() - start_time
            process_time_ms = round(process_time * 1000, 2)
            
            # Log the exception with context
            self.logger.exception(
                f"Request failed: {method} {path} after {process_time_ms}ms",
                extra={
                    "correlation_id": correlation_id,
                    "client_ip": client_ip,
                    "method": method,
                    "path": path,
                    "process_time_ms": process_time_ms,
                    "exception_type": type(exc).__name__,
                }
            )
            
            # Re-raise the exception for the exception handler middleware
            raise