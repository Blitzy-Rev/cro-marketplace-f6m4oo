"""
Authentication middleware for the Molecular Data Management and CRO Integration Platform.

This middleware implements JWT token validation, user authentication, and 
role-based access control for FastAPI applications. It provides both middleware
components and dependency functions for securing API endpoints.
"""

import logging
import re
from typing import List, Optional, Callable

from fastapi import Request, Response, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from ..core.security import validate_access_token, decode_token, validate_role
from ..core.exceptions import AuthenticationException, AuthorizationException
from ..constants.error_messages import AUTH_ERRORS
from ..models.user import User
from ..crud.crud_user import user
from ..db.session import get_db
from ..constants.user_roles import ROLE_HIERARCHY

# Set up logger
logger = logging.getLogger(__name__)

# OAuth2 bearer token scheme
oauth2_scheme = HTTPBearer(auto_error=False)

# Define public paths that don't require authentication
PUBLIC_PATHS = [
    r'^/docs',
    r'^/redoc', 
    r'^/openapi.json',
    r'^/api/v1/auth/login',
    r'^/api/v1/auth/register',
    r'^/api/v1/auth/password-reset',
    r'^/api/v1/health'
]


def is_path_public(path: str) -> bool:
    """
    Check if a request path is in the public paths list (doesn't require authentication)

    Args:
        path: The request path to check

    Returns:
        bool: True if path is public, False otherwise
    """
    for pattern in PUBLIC_PATHS:
        if re.match(pattern, path):
            return True
    return False


def extract_token_from_request(request: Request) -> Optional[str]:
    """
    Extract JWT token from request authorization header

    Args:
        request: The FastAPI request object

    Returns:
        Optional[str]: Extracted token or None if not found
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    # Check if it's a bearer token
    if not auth_header.startswith("Bearer "):
        return None

    # Extract the token part
    token = auth_header.split(" ")[1]
    return token


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> User:
    """
    Dependency function to get the current authenticated user from JWT token

    Args:
        credentials: HTTP Authorization credentials containing the JWT token

    Returns:
        User: Authenticated user object

    Raises:
        AuthenticationException: If authentication fails
    """
    if not credentials:
        raise AuthenticationException(AUTH_ERRORS["MISSING_TOKEN"])

    token = credentials.credentials
    
    try:
        # Validate the token and get payload
        payload = validate_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationException(AUTH_ERRORS["INVALID_TOKEN"])
        
        # Get user from database
        db = next(get_db())
        db_user = user.get(db, id=user_id)
        
        if not db_user:
            raise AuthenticationException(AUTH_ERRORS["INVALID_TOKEN"])
        
        if not db_user.is_active:
            raise AuthenticationException(AUTH_ERRORS["ACCOUNT_DISABLED"])
        
        return db_user
    except JWTError:
        raise AuthenticationException(AUTH_ERRORS["INVALID_TOKEN"])


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency function to get the current active user

    Args:
        current_user: The authenticated user from get_current_user

    Returns:
        User: Current active user

    Raises:
        AuthenticationException: If user is not active
    """
    if not current_user.is_active:
        raise AuthenticationException(AUTH_ERRORS["ACCOUNT_DISABLED"])
    return current_user


def require_roles(allowed_roles: List[str]):
    """
    Dependency function factory to require specific roles for access

    Args:
        allowed_roles: List of roles that are allowed to access the endpoint

    Returns:
        Callable: Dependency function that checks for required roles
    """
    async def check_roles(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role in allowed_roles:
            return current_user
        
        # Check if user's role has permission through role hierarchy
        if has_role_permission(current_user.role, allowed_roles):
            return current_user
        
        # If not in allowed roles and no permission through hierarchy, raise exception
        raise AuthorizationException(AUTH_ERRORS["INSUFFICIENT_PERMISSIONS"])
    
    return check_roles


def has_role_permission(user_role: str, required_roles: List[str]) -> bool:
    """
    Check if a user role has permission based on role hierarchy

    Args:
        user_role: The user's role
        required_roles: List of roles required for the operation

    Returns:
        bool: True if user has permission, False otherwise
    """
    # If user's role is directly in required roles, they have permission
    if user_role in required_roles:
        return True
    
    # Check role hierarchy - if the user's role has subordinate roles
    # that include any of the required roles, then they have permission
    subordinate_roles = ROLE_HIERARCHY.get(user_role, [])
    for required_role in required_roles:
        if required_role in subordinate_roles:
            return True
    
    return False


class AuthMiddleware:
    """
    Middleware for JWT authentication and authorization in FastAPI applications
    """
    
    def __init__(self, app: Callable):
        """
        Initialize the authentication middleware

        Args:
            app: The next middleware in the chain
        """
        self.app = app
    
    async def async_dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request through the authentication middleware

        Args:
            request: The incoming request
            call_next: The next middleware to call

        Returns:
            Response: The response from the next middleware or endpoint
        """
        # Skip authentication for public paths
        if is_path_public(request.url.path):
            return await call_next(request)
        
        # Extract token from request
        token = extract_token_from_request(request)
        if not token:
            raise AuthenticationException(AUTH_ERRORS["MISSING_TOKEN"])
        
        try:
            # Validate the token and get payload
            payload = validate_access_token(token)
            user_id = payload.get("sub")
            
            if not user_id:
                raise AuthenticationException(AUTH_ERRORS["INVALID_TOKEN"])
            
            # Get user from database
            db = next(get_db())
            db_user = user.get(db, id=user_id)
            
            if not db_user:
                raise AuthenticationException(AUTH_ERRORS["INVALID_TOKEN"])
            
            if not db_user.is_active:
                raise AuthenticationException(AUTH_ERRORS["ACCOUNT_DISABLED"])
            
            # Add user to request state
            request.state.user = db_user
            
            # Continue processing the request
            response = await call_next(request)
            return response
            
        except JWTError:
            raise AuthenticationException(AUTH_ERRORS["INVALID_TOKEN"])
        except AuthenticationException:
            # Re-raise authentication exceptions
            raise
        except Exception as e:
            logger.exception("Authentication error: %s", str(e))
            raise AuthenticationException(str(e))
    
    async def __call__(self, scope, receive, send):
        """
        ASGI application interface for the middleware

        Args:
            scope: ASGI scope
            receive: ASGI receive function
            send: ASGI send function

        Returns:
            Callable: ASGI application
        """
        if scope["type"] != "http":
            # Pass through non-http requests (like WebSocket)
            return await self.app(scope, receive, send)
        
        # Create a FastAPI Request object from the scope
        request = Request(scope, receive=receive)
        
        # Process the request through our middleware
        try:
            # Use the dispatch method to process the request
            response = await self.async_dispatch(
                request, 
                lambda r: self.app(scope, receive, send)
            )
            return response
        except Exception as exc:
            # Let FastAPI's exception handlers deal with the exception
            # This will be caught by the exception handler middleware
            raise exc