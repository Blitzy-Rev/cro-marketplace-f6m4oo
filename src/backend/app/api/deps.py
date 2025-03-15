"""
Dependency injection module for FastAPI endpoints in the Molecular Data Management and CRO Integration Platform.

This module provides reusable dependency functions for database sessions, authentication, 
authorization, and other common requirements across API endpoints. It implements a comprehensive
authentication and authorization framework based on JWT tokens and role-based access control.
"""

from typing import Optional, List, Callable
from fastapi import Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

# Internal imports
from ..core.config import settings
from ..core.security import validate_access_token
from ..db.session import get_db
from ..models.user import User
from ..schemas.token import TokenData
from ..core.exceptions import AuthenticationException, AuthorizationException
from ..crud.crud_user import user
from ..constants.user_roles import (
    SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST, 
    CRO_ADMIN, CRO_TECHNICIAN, AUDITOR, ROLE_HIERARCHY
)

# OAuth2 Bearer token scheme for JWT authentication
oauth2_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials containing the JWT token
        db: Database session
        
    Returns:
        Authenticated user object
        
    Raises:
        AuthenticationException: If authentication fails
    """
    if not credentials:
        raise AuthenticationException("Not authenticated")
    
    try:
        # Validate the token and get payload
        payload = validate_access_token(credentials.credentials)
        token_data = TokenData(
            user_id=payload.get("user_id"),
            email=payload.get("email"),
            role=payload.get("role")
        )
    except Exception as e:
        raise AuthenticationException(f"Invalid authentication token: {str(e)}")
    
    # Get user from database
    current_user = user.get(token_data.user_id, db=db)
    if not current_user:
        raise AuthenticationException("User not found")
    
    return current_user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get the current authenticated user and verify they are active.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        Active authenticated user object
        
    Raises:
        AuthenticationException: If user is inactive
    """
    if not current_user.is_active:
        raise AuthenticationException("Inactive user")
    
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to get the current authenticated user and verify they are a superuser.
    
    Args:
        current_user: User from get_current_active_user dependency
        
    Returns:
        Superuser authenticated user object
        
    Raises:
        AuthorizationException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise AuthorizationException("Superuser privileges required")
    
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to get the current authenticated user and verify they have admin privileges.
    
    Args:
        current_user: User from get_current_active_user dependency
        
    Returns:
        Admin authenticated user object
        
    Raises:
        AuthorizationException: If user does not have admin privileges
    """
    if not current_user.is_admin():
        raise AuthorizationException("Admin privileges required")
    
    return current_user


async def get_current_pharma_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to get the current authenticated user and verify they have pharmaceutical company role.
    
    Args:
        current_user: User from get_current_active_user dependency
        
    Returns:
        Pharma user authenticated user object
        
    Raises:
        AuthorizationException: If user does not have pharmaceutical company role
    """
    if not current_user.is_pharma_user():
        raise AuthorizationException("Pharmaceutical company role required")
    
    return current_user


async def get_current_cro_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to get the current authenticated user and verify they have CRO role.
    
    Args:
        current_user: User from get_current_active_user dependency
        
    Returns:
        CRO user authenticated user object
        
    Raises:
        AuthorizationException: If user does not have CRO role
    """
    if not current_user.is_cro_user():
        raise AuthorizationException("CRO role required")
    
    return current_user


def check_role_permission(user_role: str, required_role: str) -> bool:
    """
    Check if a user has permission based on their role and the required role.
    
    Permission is granted if:
    1. User role matches required role exactly
    2. User is a system admin (has access to everything)
    3. Required role is in the user role's hierarchy
    
    Args:
        user_role: User's current role
        required_role: Role required for the operation
        
    Returns:
        True if user has permission, False otherwise
    """
    # Exact match
    if user_role == required_role:
        return True
    
    # System admin override
    if user_role == SYSTEM_ADMIN:
        return True
    
    # Check role hierarchy
    if user_role in ROLE_HIERARCHY and required_role in ROLE_HIERARCHY.get(user_role, []):
        return True
    
    return False


def require_role(required_role: str) -> Callable:
    """
    Factory function to create a dependency that requires a specific role.
    
    Args:
        required_role: Role required for the operation
        
    Returns:
        Dependency function that checks for the required role
    """
    async def role_dependency(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if not check_role_permission(current_user.role, required_role):
            raise AuthorizationException(
                f"Role '{required_role}' required for this operation"
            )
        return current_user
    
    return role_dependency


async def require_organization_access(
    current_user: User = Depends(get_current_active_user),
    organization_id: str = None,
) -> User:
    """
    Dependency to verify user has access to a specific organization.
    
    Args:
        current_user: User from get_current_active_user dependency
        organization_id: Organization ID to check access for
        
    Returns:
        Authenticated user with organization access
        
    Raises:
        AuthorizationException: If user does not have access to the organization
    """
    # System admins have access to all organizations
    if current_user.is_superuser:
        return current_user
    
    # Check if user belongs to the specified organization
    if current_user.organization_id != organization_id:
        raise AuthorizationException(
            "You do not have access to this organization"
        )
    
    return current_user