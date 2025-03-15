"""
Middleware for audit logging in the Molecular Data Management and CRO Integration Platform.

This middleware captures and records user actions, resource access, and system events to 
maintain a comprehensive audit trail for compliance with regulatory requirements 
such as 21 CFR Part 11 and GDPR.
"""

import time
import json
import re
from typing import Dict, Any, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..core.logging import get_logger, get_correlation_id
from ..models.audit import AuditEventType, Audit
from ..db.session import db_session
from .logging_middleware import get_client_ip
from ..core.config import settings

# Initialize logger
logger = get_logger(__name__)

# Paths to exclude from audit logging
EXCLUDED_PATHS = ['/health', '/metrics', '/docs', '/redoc', '/openapi.json', '/api/v1/auth/login']

# HTTP methods that should trigger audit logging
AUDIT_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']


def should_audit_path(path: str, method: str) -> bool:
    """
    Determine if a path should be audited based on exclusion rules and HTTP method.
    
    Args:
        path: The request path
        method: The HTTP method
        
    Returns:
        True if path should be audited, False otherwise
    """
    # Check if path is in excluded paths
    if path in EXCLUDED_PATHS:
        return False
    
    # Check if path starts with an excluded prefix
    for excluded_path in EXCLUDED_PATHS:
        if path.startswith(excluded_path):
            return False
    
    # Only audit specific HTTP methods
    if method not in AUDIT_METHODS:
        return False
    
    return True


def extract_resource_info(path: str) -> tuple:
    """
    Extract resource type and ID from request path.
    
    Args:
        path: The request path
        
    Returns:
        Tuple containing (resource_type, resource_id) if found, otherwise (None, None)
    """
    # Use regex to match resource paths like '/api/v1/resource_type/{resource_id}'
    pattern = r'/api/v\d+/([a-zA-Z_]+)/?([a-zA-Z0-9-]+)?'
    match = re.match(pattern, path)
    
    if match:
        resource_type = match.group(1)
        resource_id = match.group(2) if match.group(2) else None
        return resource_type, resource_id
    
    return None, None


def determine_event_type(method: str, path: str) -> str:
    """
    Determine the audit event type based on HTTP method and path.
    
    Args:
        method: The HTTP method
        path: The request path
        
    Returns:
        Appropriate AuditEventType value
    """
    # Map HTTP methods to event types
    method_map = {
        'POST': AuditEventType.CREATE,
        'GET': AuditEventType.READ,
        'PUT': AuditEventType.UPDATE,
        'PATCH': AuditEventType.UPDATE,
        'DELETE': AuditEventType.DELETE,
    }
    
    # Check for special paths that indicate specific event types
    if '/api/v1/auth/login' in path:
        return AuditEventType.LOGIN
    elif '/api/v1/auth/logout' in path:
        return AuditEventType.LOGOUT
    elif '/api/v1/submissions' in path and method == 'POST':
        return AuditEventType.SUBMISSION
    elif '/api/v1/documents' in path and 'sign' in path:
        return AuditEventType.DOCUMENT_SIGN
    elif '/api/v1/documents' in path and method == 'POST':
        return AuditEventType.DOCUMENT_UPLOAD
    elif '/api/v1/results' in path and method == 'POST':
        return AuditEventType.RESULT_UPLOAD
    elif '/status' in path and method in ['PUT', 'PATCH']:
        return AuditEventType.STATUS_CHANGE
    elif '/permissions' in path and method in ['POST', 'PUT', 'PATCH']:
        return AuditEventType.PERMISSION_CHANGE
    elif '/export' in path:
        return AuditEventType.EXPORT
    elif '/import' in path:
        return AuditEventType.IMPORT
    
    # Default to method-based mapping
    return method_map.get(method, AuditEventType.READ)


def sanitize_request_body(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize request body to remove sensitive information before logging.
    
    Args:
        body: The request body dictionary
        
    Returns:
        Sanitized body dictionary
    """
    # Create a copy to avoid modifying the original
    sanitized = body.copy() if body else {}
    
    # List of fields that might contain sensitive information
    sensitive_fields = [
        'password', 
        'password_confirmation',
        'current_password',
        'token',
        'access_token',
        'refresh_token',
        'api_key',
        'secret',
        'credit_card',
        'card_number',
        'cvv',
        'ssn',
        'social_security'
    ]
    
    # Redact sensitive fields
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = '[REDACTED]'
    
    # Check for nested dictionaries
    for key, value in sanitized.items():
        if isinstance(value, dict):
            sanitized[key] = sanitize_request_body(value)
    
    return sanitized


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware for capturing and recording audit events for all API requests.
    
    This middleware intercepts requests, extracts relevant information, and creates
    audit logs for actions that modify data or access sensitive resources.
    """
    
    def __init__(self, app):
        """
        Initialize the audit middleware.
        
        Args:
            app: The ASGI application
        """
        super().__init__(app)
        self.logger = get_logger(__name__)
    
    async def async_dispatch(self, request: Request, call_next) -> Response:
        """
        Process each request through the audit middleware.
        
        Args:
            request: The HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            The HTTP response after middleware processing
        """
        # Check if audit logging is enabled in settings
        if not getattr(settings, 'AUDIT_ENABLED', True):
            return await call_next(request)
        
        # Check if path should be audited
        path = request.url.path
        method = request.method
        
        if not should_audit_path(path, method):
            return await call_next(request)
        
        # Extract user information if authenticated
        user_id = None
        if hasattr(request, 'state') and hasattr(request.state, 'user'):
            user_id = getattr(request.state.user, 'id', None)
        
        # Extract client IP
        ip_address = get_client_ip(request)
        
        # Extract resource information
        resource_type, resource_id = extract_resource_info(path)
        
        # Determine event type
        event_type = determine_event_type(method, path)
        
        # Capture request body for non-GET requests
        request_body = None
        if method != 'GET':
            try:
                # Create a copy of the request
                body_copy = await request.body()
                # Reset the request body for the next middleware
                await request.body()
                
                if body_copy:
                    content_type = request.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        try:
                            request_body = json.loads(body_copy.decode('utf-8'))
                            request_body = sanitize_request_body(request_body)
                        except json.JSONDecodeError:
                            self.logger.warning(
                                f"Failed to parse JSON request body",
                                extra={"correlation_id": get_correlation_id()}
                            )
            except Exception as e:
                self.logger.warning(
                    f"Failed to capture request body: {str(e)}",
                    extra={"correlation_id": get_correlation_id()}
                )
        
        # Process the request
        start_time = time.time()
        try:
            # Call the next middleware or endpoint handler
            response = await call_next(request)
            
            # Record the processing time
            process_time = time.time() - start_time
            
            # Create audit log entry
            description = f"{method} {path} completed in {round(process_time * 1000, 2)}ms with status {response.status_code}"
            
            try:
                # Convert resource_id to UUID if it's a string
                if resource_id and isinstance(resource_id, str):
                    try:
                        import uuid
                        resource_id = uuid.UUID(resource_id)
                    except ValueError:
                        # Not a valid UUID, keep as string
                        pass
                
                # Create the audit log entry
                audit_log = Audit.create_audit_log(
                    user_id=user_id,
                    event_type=event_type,
                    resource_type=resource_type or path.split('/')[-1],
                    resource_id=resource_id,
                    description=description,
                    old_values=None,  # We don't have before values in middleware
                    new_values=request_body,  # Use request body as new values
                    ip_address=ip_address,
                    user_agent=request.headers.get('user-agent')
                )
                
                # Add to session and commit
                db_session.add(audit_log)
                db_session.commit()
                
                self.logger.debug(
                    f"Created audit log: {event_type} for {resource_type} by user {user_id}",
                    extra={"correlation_id": get_correlation_id()}
                )
                
            except Exception as e:
                self.logger.error(
                    f"Failed to create audit log: {str(e)}", 
                    extra={"correlation_id": get_correlation_id()}
                )
                # Don't let audit failure affect the response
                db_session.rollback()
            
            return response
            
        except Exception as exc:
            # Log the exception
            process_time = time.time() - start_time
            description = f"{method} {path} failed after {round(process_time * 1000, 2)}ms with error: {str(exc)}"
            
            try:
                # Create audit log for the error
                audit_log = Audit.create_audit_log(
                    user_id=user_id,
                    event_type=AuditEventType.SYSTEM_ERROR,
                    resource_type=resource_type or path.split('/')[-1],
                    resource_id=resource_id,
                    description=description,
                    old_values=None,
                    new_values=request_body,
                    ip_address=ip_address,
                    user_agent=request.headers.get('user-agent')
                )
                
                db_session.add(audit_log)
                db_session.commit()
                
            except Exception as audit_error:
                self.logger.error(
                    f"Failed to create audit log for exception: {str(audit_error)}",
                    extra={"correlation_id": get_correlation_id()}
                )
                db_session.rollback()
            
            # Re-raise the original exception
            raise