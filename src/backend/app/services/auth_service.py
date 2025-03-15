"""
Authentication Service Module

This module provides high-level authentication and authorization functionality for the
Molecular Data Management and CRO Integration Platform. It integrates with both database-based
authentication and AWS Cognito, handling user login, token management, registration, password
management, and role-based access control.
"""

from datetime import datetime
from typing import Dict, Optional, Any, Union
import uuid

# Internal imports
from ..models.user import User
from ..crud.crud_user import user
from ..schemas.token import Token, TokenPayload, TokenData
from ..schemas.user import UserCreate, UserInDB, UserWithPermissions
from ..core.security import (
    create_access_token,
    create_refresh_token,
    validate_access_token,
    validate_refresh_token,
    get_password_hash,
    verify_password,
    validate_password
)
from ..integrations.aws.cognito import CognitoClient
from ..core.config import settings
from ..core.logging import get_logger
from ..core.exceptions import AuthenticationException, ValidationException, IntegrationException
from ..db.session import db_session
from ..constants.error_messages import AUTH_ERRORS

# Set up logging
logger = get_logger(__name__)

# Initialize Cognito client if using Cognito auth
cognito_client = CognitoClient(
    settings.COGNITO_USER_POOL_ID, 
    settings.COGNITO_CLIENT_ID, 
    settings.COGNITO_CLIENT_SECRET
) if settings.AUTH_TYPE == 'cognito' else None


def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    """
    Authenticate a user with username and password using the configured authentication method.
    
    Args:
        username: Email or username of the user
        password: User's password
        
    Returns:
        Authentication response with tokens and user information
        
    Raises:
        AuthenticationException: If authentication fails
    """
    logger.info(f"Authentication attempt for user: {username}")
    
    # Use the appropriate authentication method based on settings
    if settings.AUTH_TYPE == 'database':
        return authenticate_database(username, password)
    elif settings.AUTH_TYPE == 'cognito':
        return authenticate_cognito(username, password)
    else:
        raise ValidationException(
            message=f"Invalid authentication type configured: {settings.AUTH_TYPE}",
            error_code="config_error"
        )


def authenticate_database(username: str, password: str) -> Dict[str, Any]:
    """
    Authenticate a user with username and password using database authentication.
    
    Args:
        username: Email or username of the user
        password: User's password
        
    Returns:
        Authentication response with tokens and user information
        
    Raises:
        AuthenticationException: If authentication fails
    """
    # Authenticate user with database
    db_user = user.authenticate(email=username, password=password)
    
    if not db_user:
        logger.warning(f"Authentication failed for user: {username}")
        raise AuthenticationException(
            message=AUTH_ERRORS.get("INVALID_CREDENTIALS", "Invalid username or password"),
            error_code="invalid_credentials"
        )
    
    if not db_user.is_active:
        logger.warning(f"Inactive user attempted login: {username}")
        raise AuthenticationException(
            message=AUTH_ERRORS.get("ACCOUNT_DISABLED", "Your account has been disabled"),
            error_code="account_disabled"
        )
    
    # Create token data with user information
    token_data = {
        "user_id": str(db_user.id),
        "email": db_user.email,
        "role": db_user.role,
    }
    
    # Generate access token and refresh token
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    logger.info(f"Authentication successful for user: {username}")
    
    # Create response with tokens and user information
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": str(db_user.id),
        "role": db_user.role,
        "email": db_user.email,
        "full_name": db_user.full_name
    }


def authenticate_cognito(username: str, password: str) -> Dict[str, Any]:
    """
    Authenticate a user with username and password using AWS Cognito.
    
    Args:
        username: Email or username of the user
        password: User's password
        
    Returns:
        Authentication response with tokens and user information
        
    Raises:
        AuthenticationException: If authentication fails
    """
    try:
        # Authenticate with Cognito
        auth_response = cognito_client.authenticate(username, password)
        
        # Handle authentication challenges
        if "challenge" in auth_response:
            challenge_name = auth_response.get("challenge")
            
            logger.info(f"Authentication challenge required for user {username}: {challenge_name}")
            
            return {
                "challenge": challenge_name,
                "session": auth_response.get("session"),
                "challenge_parameters": auth_response.get("challenge_parameters", {}),
                "mfa_required": challenge_name == "SOFTWARE_TOKEN_MFA"
            }
        
        # Get tokens from successful authentication
        access_token = auth_response.get("access_token")
        id_token = auth_response.get("id_token")
        refresh_token = auth_response.get("refresh_token")
        
        # Get user attributes from Cognito
        user_info = cognito_client.get_user(access_token)
        attributes = user_info.get("attributes", {})
        
        # Extract user information
        user_id = attributes.get("sub")
        email = attributes.get("email")
        role = attributes.get("custom:role")
        name = attributes.get("name", "")
        
        logger.info(f"Authentication successful for user: {username}")
        
        # Create response with tokens and user information
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "id_token": id_token,
            "token_type": "bearer",
            "user_id": user_id,
            "role": role,
            "email": email,
            "full_name": name
        }
    
    except Exception as e:
        logger.error(f"Cognito authentication error: {str(e)}")
        raise AuthenticationException(
            message=AUTH_ERRORS.get("INVALID_CREDENTIALS", "Invalid username or password"),
            error_code="invalid_credentials"
        )


def register_user(user_data: UserCreate) -> Dict[str, Any]:
    """
    Register a new user in the system using the configured authentication method.
    
    Args:
        user_data: User data for registration
        
    Returns:
        Registration response with user information
        
    Raises:
        AuthenticationException: If registration fails
    """
    logger.info(f"Registration attempt for email: {user_data.email}")
    
    # Use the appropriate registration method based on settings
    if settings.AUTH_TYPE == 'database':
        return register_database(user_data)
    elif settings.AUTH_TYPE == 'cognito':
        return register_cognito(user_data)
    else:
        raise ValidationException(
            message=f"Invalid authentication type configured: {settings.AUTH_TYPE}",
            error_code="config_error"
        )


def register_database(user_data: UserCreate) -> Dict[str, Any]:
    """
    Register a new user in the database.
    
    Args:
        user_data: User data for registration
        
    Returns:
        Registration response with user information
        
    Raises:
        AuthenticationException: If registration fails
    """
    # Check if user already exists
    existing_user = user.get_by_email(user_data.email)
    if existing_user:
        logger.warning(f"Registration failed - email already exists: {user_data.email}")
        raise AuthenticationException(
            message=AUTH_ERRORS.get("EMAIL_ALREADY_EXISTS", "A user with this email already exists"),
            error_code="email_exists"
        )
    
    # Create new user
    db_user = user.create(user_data)
    
    logger.info(f"User registered successfully: {user_data.email}")
    
    # Return user information
    return {
        "id": str(db_user.id),
        "email": db_user.email,
        "full_name": db_user.full_name,
        "role": db_user.role,
        "is_active": db_user.is_active
    }


def register_cognito(user_data: UserCreate) -> Dict[str, Any]:
    """
    Register a new user in AWS Cognito.
    
    Args:
        user_data: User data for registration
        
    Returns:
        Registration response with user information
        
    Raises:
        AuthenticationException: If registration fails
    """
    try:
        # Additional attributes for Cognito
        attributes = {
            "name": user_data.full_name,
        }
        
        # Add optional organization attributes if available
        if user_data.organization_name:
            attributes["custom:organization_name"] = user_data.organization_name
        
        if user_data.organization_id:
            attributes["custom:organization_id"] = str(user_data.organization_id)
        
        # Register user in Cognito
        registration_response = cognito_client.register(
            username=user_data.email,
            email=user_data.email,
            password=user_data.password,
            role=user_data.role,
            attributes=attributes
        )
        
        logger.info(f"User registered in Cognito: {user_data.email}")
        
        # Registration response
        return {
            "email": user_data.email,
            "full_name": user_data.full_name,
            "role": user_data.role,
            "requires_confirmation": True,
            "user_sub": registration_response.get("UserSub")
        }
    
    except Exception as e:
        logger.error(f"Cognito registration error: {str(e)}")
        if isinstance(e, AuthenticationException):
            raise e
        else:
            raise AuthenticationException(
                message=f"Registration failed: {str(e)}",
                error_code="registration_error"
            )


def confirm_registration(username: str, confirmation_code: str) -> bool:
    """
    Confirm user registration with verification code.
    
    Args:
        username: Email or username of the user
        confirmation_code: Verification code sent to the user
        
    Returns:
        True if confirmation was successful
        
    Raises:
        ValidationException: If not using Cognito authentication
        AuthenticationException: If confirmation fails
    """
    logger.info(f"Registration confirmation attempt for user: {username}")
    
    if settings.AUTH_TYPE != 'cognito':
        raise ValidationException(
            message="Registration confirmation is only available for Cognito authentication",
            error_code="method_not_supported"
        )
    
    try:
        # Confirm registration in Cognito
        result = cognito_client.confirm_registration(username, confirmation_code)
        
        logger.info(f"Registration confirmed for user: {username}")
        return result
    
    except Exception as e:
        logger.error(f"Registration confirmation error: {str(e)}")
        if isinstance(e, AuthenticationException):
            raise e
        else:
            raise AuthenticationException(
                message=f"Registration confirmation failed: {str(e)}",
                error_code="confirmation_error"
            )


def refresh_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh authentication tokens using a refresh token.
    
    Args:
        refresh_token: Valid refresh token
        
    Returns:
        Authentication response with new tokens
        
    Raises:
        AuthenticationException: If token refresh fails
    """
    logger.info("Token refresh attempt")
    
    # Use the appropriate token refresh method based on settings
    if settings.AUTH_TYPE == 'database':
        return refresh_token_database(refresh_token)
    elif settings.AUTH_TYPE == 'cognito':
        return refresh_token_cognito(refresh_token)
    else:
        raise ValidationException(
            message=f"Invalid authentication type configured: {settings.AUTH_TYPE}",
            error_code="config_error"
        )


def refresh_token_database(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh authentication tokens using database authentication.
    
    Args:
        refresh_token: Valid refresh token
        
    Returns:
        Authentication response with new tokens
        
    Raises:
        AuthenticationException: If token refresh fails
    """
    try:
        # Validate refresh token
        payload = validate_refresh_token(refresh_token)
        
        # Extract user_id from token payload
        user_id = payload.get("user_id")
        if not user_id:
            raise AuthenticationException(
                message=AUTH_ERRORS.get("INVALID_TOKEN", "Invalid token format"),
                error_code="invalid_token"
            )
        
        # Get user from database
        db_user = user.get(id=uuid.UUID(user_id))
        if not db_user or not db_user.is_active:
            raise AuthenticationException(
                message=AUTH_ERRORS.get("ACCOUNT_DISABLED", "User not found or inactive"),
                error_code="user_not_found"
            )
        
        # Create token data with user information
        token_data = {
            "user_id": str(db_user.id),
            "email": db_user.email,
            "role": db_user.role,
        }
        
        # Generate new access token (refresh token remains the same)
        access_token = create_access_token(token_data)
        
        logger.info(f"Token refreshed for user: {db_user.email}")
        
        # Create response with new access token and existing refresh token
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        if isinstance(e, AuthenticationException):
            raise e
        else:
            raise AuthenticationException(
                message=AUTH_ERRORS.get("INVALID_TOKEN", "Invalid refresh token"),
                error_code="invalid_token"
            )


def refresh_token_cognito(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh authentication tokens using AWS Cognito.
    
    Args:
        refresh_token: Valid refresh token
        
    Returns:
        Authentication response with new tokens
        
    Raises:
        AuthenticationException: If token refresh fails
    """
    try:
        # Refresh tokens with Cognito
        token_response = cognito_client.refresh_tokens(refresh_token)
        
        logger.info("Token refreshed via Cognito")
        
        # Create response with new tokens
        return {
            "access_token": token_response.get("access_token"),
            "id_token": token_response.get("id_token"),
            "refresh_token": refresh_token,  # Keep the same refresh token
            "token_type": "bearer"
        }
    
    except Exception as e:
        logger.error(f"Cognito token refresh error: {str(e)}")
        if isinstance(e, AuthenticationException):
            raise e
        else:
            raise AuthenticationException(
                message=AUTH_ERRORS.get("INVALID_TOKEN", "Invalid refresh token"),
                error_code="invalid_token"
            )


def get_current_user(token: str) -> UserWithPermissions:
    """
    Get current user from access token.
    
    Args:
        token: JWT access token
        
    Returns:
        User information with permissions
        
    Raises:
        AuthenticationException: If token is invalid or user not found
    """
    try:
        # Validate access token
        payload = validate_access_token(token)
        
        # Extract user_id and role from token payload
        user_id = payload.get("user_id")
        role = payload.get("role")
        
        if not user_id:
            raise AuthenticationException(
                message=AUTH_ERRORS.get("INVALID_TOKEN", "Invalid token format"),
                error_code="invalid_token"
            )
        
        # Get user from database
        db_user = user.get(id=uuid.UUID(user_id))
        if not db_user or not db_user.is_active:
            raise AuthenticationException(
                message=AUTH_ERRORS.get("ACCOUNT_DISABLED", "User not found or inactive"),
                error_code="user_not_found"
            )
        
        # Get user permissions based on role
        permissions = get_user_permissions(role or db_user.role)
        
        # Create user with permissions
        user_with_permissions = UserWithPermissions(
            **db_user.to_dict(),
            permissions=permissions
        )
        
        return user_with_permissions
    
    except Exception as e:
        logger.error(f"Error retrieving current user: {str(e)}")
        if isinstance(e, AuthenticationException):
            raise e
        else:
            raise AuthenticationException(
                message=AUTH_ERRORS.get("INVALID_TOKEN", "Invalid token"),
                error_code="invalid_token"
            )


def get_user_permissions(role: str) -> Dict[str, Any]:
    """
    Get permissions for a user based on their role.
    
    Args:
        role: User role
        
    Returns:
        Dictionary of permissions for the user
    """
    # Base permissions for all users
    permissions = {
        "molecules": {
            "view": True,
            "create": False,
            "edit": False,
            "delete": False
        },
        "libraries": {
            "view": True,
            "create": False,
            "edit": False,
            "delete": False
        },
        "submissions": {
            "view": True,
            "create": False,
            "approve": False
        },
        "results": {
            "view": True,
            "upload": False
        },
        "users": {
            "view": False,
            "create": False,
            "edit": False,
            "delete": False
        }
    }
    
    # Add role-specific permissions
    if role == "system_admin":
        # System admin has all permissions
        permissions["molecules"].update({"create": True, "edit": True, "delete": True})
        permissions["libraries"].update({"create": True, "edit": True, "delete": True})
        permissions["submissions"].update({"create": True, "approve": True})
        permissions["results"].update({"upload": True})
        permissions["users"].update({"view": True, "create": True, "edit": True, "delete": True})
        permissions["admin"] = True
    
    elif role == "pharma_admin":
        # Pharma admin has admin permissions for their organization
        permissions["molecules"].update({"create": True, "edit": True, "delete": True})
        permissions["libraries"].update({"create": True, "edit": True, "delete": True})
        permissions["submissions"].update({"create": True, "approve": True})
        permissions["users"].update({"view": True, "create": True, "edit": True})
        permissions["admin"] = True
    
    elif role == "pharma_scientist":
        # Pharma scientist has permissions to work with molecules and make submissions
        permissions["molecules"].update({"create": True, "edit": True})
        permissions["libraries"].update({"create": True, "edit": True})
        permissions["submissions"].update({"create": True})
    
    elif role == "cro_admin":
        # CRO admin can manage their organization and handle results
        permissions["results"].update({"upload": True})
        permissions["users"].update({"view": True, "create": True, "edit": True})
        permissions["admin"] = True
    
    elif role == "cro_technician":
        # CRO technician can upload results
        permissions["results"].update({"upload": True})
    
    elif role == "auditor":
        # Auditor has read-only access
        permissions["audit"] = True
    
    return permissions


def change_password(user_id: str, current_password: str, new_password: str) -> bool:
    """
    Change user password.
    
    Args:
        user_id: User ID
        current_password: Current password
        new_password: New password
        
    Returns:
        True if password change was successful
        
    Raises:
        AuthenticationException: If password change fails
    """
    logger.info(f"Password change attempt for user: {user_id}")
    
    # Use the appropriate password change method based on settings
    if settings.AUTH_TYPE == 'database':
        return change_password_database(user_id, current_password, new_password)
    elif settings.AUTH_TYPE == 'cognito':
        # For Cognito, we need the access token which is not provided in this function signature
        # We would typically handle this differently with Cognito, requiring the access token
        raise ValidationException(
            message="Password change for Cognito requires access token",
            error_code="method_not_supported"
        )
    else:
        raise ValidationException(
            message=f"Invalid authentication type configured: {settings.AUTH_TYPE}",
            error_code="config_error"
        )


def change_password_database(user_id: str, current_password: str, new_password: str) -> bool:
    """
    Change user password in database.
    
    Args:
        user_id: User ID
        current_password: Current password
        new_password: New password
        
    Returns:
        True if password change was successful
        
    Raises:
        AuthenticationException: If password change fails
    """
    try:
        # Get user from database
        db_user = user.get(id=uuid.UUID(user_id))
        if not db_user:
            raise AuthenticationException(
                message="User not found",
                error_code="user_not_found"
            )
        
        # Verify current password
        if not db_user.check_password(current_password):
            raise AuthenticationException(
                message="Current password is incorrect",
                error_code="invalid_password"
            )
        
        # Validate new password
        if not validate_password(new_password):
            raise ValidationException(
                message=AUTH_ERRORS.get("PASSWORD_TOO_WEAK", 
                                        "Password does not meet security requirements"),
                error_code="weak_password"
            )
        
        # Set new password
        db_user.set_password(new_password)
        
        # Update user in database
        db_session.add(db_user)
        db_session.commit()
        
        logger.info(f"Password changed for user: {user_id}")
        return True
    
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        if isinstance(e, (AuthenticationException, ValidationException)):
            raise e
        else:
            raise AuthenticationException(
                message="Password change failed",
                error_code="password_change_error"
            )


def change_password_cognito(user_id: str, current_password: str, new_password: str, access_token: str) -> bool:
    """
    Change user password in AWS Cognito.
    
    Args:
        user_id: User ID (not used for Cognito)
        current_password: Current password
        new_password: New password
        access_token: Valid access token
        
    Returns:
        True if password change was successful
        
    Raises:
        ValidationException: If new password is invalid
        AuthenticationException: If password change fails
    """
    try:
        # Validate new password
        if not validate_password(new_password):
            raise ValidationException(
                message=AUTH_ERRORS.get("PASSWORD_TOO_WEAK", 
                                        "Password does not meet security requirements"),
                error_code="weak_password"
            )
        
        # Change password in Cognito
        result = cognito_client.change_password(access_token, current_password, new_password)
        
        logger.info(f"Password changed in Cognito for user ID: {user_id}")
        return result
    
    except Exception as e:
        logger.error(f"Cognito password change error: {str(e)}")
        if isinstance(e, (AuthenticationException, ValidationException)):
            raise e
        else:
            raise AuthenticationException(
                message="Password change failed",
                error_code="password_change_error"
            )


def forgot_password(username: str) -> Dict[str, Any]:
    """
    Initiate forgot password flow.
    
    Args:
        username: Email or username of the user
        
    Returns:
        Forgot password response with delivery details
        
    Raises:
        ValidationException: If not using Cognito authentication
        AuthenticationException: If forgot password request fails
    """
    logger.info(f"Forgot password attempt for user: {username}")
    
    if settings.AUTH_TYPE != 'cognito':
        raise ValidationException(
            message="Forgot password flow is only available for Cognito authentication",
            error_code="method_not_supported"
        )
    
    try:
        # Initiate forgot password in Cognito
        result = cognito_client.forgot_password(username)
        
        logger.info(f"Forgot password initiated for user: {username}")
        return result
    
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        if isinstance(e, AuthenticationException):
            raise e
        else:
            raise AuthenticationException(
                message="Forgot password request failed",
                error_code="forgot_password_error"
            )


def reset_password(username: str, confirmation_code: str, new_password: str) -> bool:
    """
    Reset password with verification code.
    
    Args:
        username: Email or username of the user
        confirmation_code: Verification code sent to the user
        new_password: New password
        
    Returns:
        True if password reset was successful
        
    Raises:
        ValidationException: If not using Cognito authentication or password is invalid
        AuthenticationException: If password reset fails
    """
    logger.info(f"Password reset attempt for user: {username}")
    
    if settings.AUTH_TYPE != 'cognito':
        raise ValidationException(
            message="Password reset is only available for Cognito authentication",
            error_code="method_not_supported"
        )
    
    try:
        # Validate new password
        if not validate_password(new_password):
            raise ValidationException(
                message=AUTH_ERRORS.get("PASSWORD_TOO_WEAK", 
                                        "Password does not meet security requirements"),
                error_code="weak_password"
            )
        
        # Reset password in Cognito
        result = cognito_client.confirm_forgot_password(username, confirmation_code, new_password)
        
        logger.info(f"Password reset for user: {username}")
        return result
    
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        if isinstance(e, (AuthenticationException, ValidationException)):
            raise e
        else:
            raise AuthenticationException(
                message="Password reset failed",
                error_code="password_reset_error"
            )


def setup_mfa(access_token: str) -> Dict[str, Any]:
    """
    Set up MFA for a user.
    
    Args:
        access_token: Valid access token
        
    Returns:
        MFA setup information including secret code and QR code
        
    Raises:
        ValidationException: If not using Cognito authentication
        AuthenticationException: If MFA setup fails
    """
    logger.info("MFA setup attempt")
    
    if settings.AUTH_TYPE != 'cognito':
        raise ValidationException(
            message="MFA setup is only available for Cognito authentication",
            error_code="method_not_supported"
        )
    
    try:
        # Set up MFA in Cognito
        result = cognito_client.setup_mfa(access_token)
        
        logger.info("MFA setup initiated")
        return result
    
    except Exception as e:
        logger.error(f"MFA setup error: {str(e)}")
        if isinstance(e, AuthenticationException):
            raise e
        else:
            raise AuthenticationException(
                message="MFA setup failed",
                error_code="mfa_setup_error"
            )


def verify_mfa_setup(access_token: str, verification_code: str) -> bool:
    """
    Verify MFA setup with a verification code.
    
    Args:
        access_token: Valid access token
        verification_code: MFA verification code
        
    Returns:
        True if verification was successful
        
    Raises:
        ValidationException: If not using Cognito authentication
        AuthenticationException: If MFA verification fails
    """
    logger.info("MFA verification attempt")
    
    if settings.AUTH_TYPE != 'cognito':
        raise ValidationException(
            message="MFA verification is only available for Cognito authentication",
            error_code="method_not_supported"
        )
    
    try:
        # Verify MFA setup in Cognito
        result = cognito_client.verify_mfa_setup(access_token, verification_code)
        
        logger.info("MFA verification successful")
        return result
    
    except Exception as e:
        logger.error(f"MFA verification error: {str(e)}")
        if isinstance(e, AuthenticationException):
            raise e
        else:
            raise AuthenticationException(
                message="MFA verification failed",
                error_code="mfa_verification_error"
            )


def sign_out(access_token: str) -> bool:
    """
    Sign out a user from all devices.
    
    Args:
        access_token: Valid access token
        
    Returns:
        True if sign out was successful
        
    Raises:
        ValidationException: If authentication type is invalid
        AuthenticationException: If sign out fails
    """
    logger.info("Sign out attempt")
    
    # Use the appropriate sign out method based on settings
    if settings.AUTH_TYPE == 'database':
        # For database auth, we don't need to do anything special for sign out
        # The client should discard the tokens
        return True
    elif settings.AUTH_TYPE == 'cognito':
        return sign_out_cognito(access_token)
    else:
        raise ValidationException(
            message=f"Invalid authentication type configured: {settings.AUTH_TYPE}",
            error_code="config_error"
        )


def sign_out_cognito(access_token: str) -> bool:
    """
    Sign out a user from all devices using AWS Cognito.
    
    Args:
        access_token: Valid access token
        
    Returns:
        True if sign out was successful
        
    Raises:
        AuthenticationException: If sign out fails
    """
    try:
        # Sign out user in Cognito
        result = cognito_client.sign_out(access_token)
        
        logger.info("Cognito sign out successful")
        return result
    
    except Exception as e:
        logger.error(f"Cognito sign out error: {str(e)}")
        if isinstance(e, AuthenticationException):
            raise e
        else:
            raise AuthenticationException(
                message="Sign out failed",
                error_code="sign_out_error"
            )