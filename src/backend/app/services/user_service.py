"""
Service layer for user management in the Molecular Data Management and CRO Integration Platform.

This module provides high-level business logic for user operations including creation,
authentication, profile management, and role-based access control.
"""

from typing import Optional, Dict, List, Any
from uuid import UUID
from sqlalchemy.orm import Session
import pyotp  # pyotp ^2.8.0

# Internal imports
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate, PasswordChange
from ..crud.crud_user import user
from ..core.security import create_access_token, create_refresh_token, validate_password
from ..db.session import db_session, get_db
from ..core.exceptions import AuthenticationException, ValidationException, NotFoundException, ConflictException
from ..constants.error_messages import AUTH_ERRORS
from ..constants.user_roles import ALL_ROLES, PHARMA_ROLES, CRO_ROLES
from ..core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


def create_user(user_in: UserCreate, db: Optional[Session] = None) -> User:
    """
    Create a new user with validated data
    
    Args:
        user_in: User data for creation
        db: Optional database session
        
    Returns:
        Created user instance
        
    Raises:
        ConflictException: If a user with the same email already exists
    """
    db_session_local = db or db_session
    
    # Check if user with this email already exists
    existing_user = user.get_by_email(email=user_in.email, db=db_session_local)
    if existing_user:
        raise ConflictException(
            message=AUTH_ERRORS["EMAIL_ALREADY_EXISTS"],
            error_code="email_already_exists"
        )
    
    # Create new user
    db_user = user.create(obj_in=user_in, db=db_session_local)
    
    logger.info(f"Created new user: {db_user.email} with role: {db_user.role}")
    
    return db_user


def get_user_by_id(user_id: UUID, db: Optional[Session] = None) -> Optional[User]:
    """
    Get a user by ID
    
    Args:
        user_id: User ID to look up
        db: Optional database session
        
    Returns:
        User instance if found, None otherwise
    """
    db_session_local = db or db_session
    return db_session_local.query(User).filter(User.id == user_id).first()


def get_user_by_email(email: str, db: Optional[Session] = None) -> Optional[User]:
    """
    Get a user by email address
    
    Args:
        email: Email address to look up
        db: Optional database session
        
    Returns:
        User instance if found, None otherwise
    """
    db_session_local = db or db_session
    return user.get_by_email(email=email, db=db_session_local)


def authenticate_user(email: str, password: str, db: Optional[Session] = None) -> Optional[User]:
    """
    Authenticate a user with email and password
    
    Args:
        email: User's email address
        password: User's password
        db: Optional database session
        
    Returns:
        Authenticated user or None if authentication fails
    """
    db_session_local = db or db_session
    
    # Use the CRUD authenticate method
    db_user = user.authenticate(email, password, db=db_session_local)
    
    if db_user:
        # Update last login timestamp
        db_user.update_last_login()
        db_session_local.add(db_user)
        db_session_local.commit()
        
        logger.info(f"User authenticated: {email}")
    else:
        logger.warning(f"Failed authentication attempt: {email}")
    
    return db_user


def update_user(db_user: User, user_in: UserUpdate, db: Optional[Session] = None) -> User:
    """
    Update user information
    
    Args:
        db_user: Existing user to update
        user_in: User data for updating
        db: Optional database session
        
    Returns:
        Updated user instance
    """
    db_session_local = db or db_session
    
    # Update the user using the CRUD update method
    updated_user = user.update(db_obj=db_user, obj_in=user_in, db=db_session_local)
    
    logger.info(f"Updated user: {updated_user.email}")
    
    return updated_user


def change_password(db_user: User, password_data: PasswordChange, db: Optional[Session] = None) -> User:
    """
    Change a user's password with verification of current password
    
    Args:
        db_user: User instance to update
        password_data: Password change data with current and new password
        db: Optional database session
        
    Returns:
        User instance with updated password
        
    Raises:
        AuthenticationException: If current password is invalid
        ValidationException: If new password doesn't meet requirements
    """
    db_session_local = db or db_session
    
    # Verify current password
    if not db_user.check_password(password_data.current_password):
        raise AuthenticationException(
            message=AUTH_ERRORS["INVALID_CREDENTIALS"],
            error_code="invalid_credentials"
        )
    
    # Validate new password
    if not validate_password(password_data.new_password):
        raise ValidationException(
            message=AUTH_ERRORS["PASSWORD_TOO_WEAK"],
            error_code="password_too_weak"
        )
    
    # Set new password
    db_user.set_password(password_data.new_password)
    
    # Save changes
    db_session_local.add(db_user)
    db_session_local.commit()
    
    logger.info(f"Password changed for user: {db_user.email}")
    
    return db_user


def deactivate_user(db_user: User, db: Optional[Session] = None) -> User:
    """
    Deactivate a user account
    
    Args:
        db_user: User to deactivate
        db: Optional database session
        
    Returns:
        Deactivated user instance
    """
    db_session_local = db or db_session
    
    # Set active flag to False
    db_user.is_active = False
    
    # Save changes
    db_session_local.add(db_user)
    db_session_local.commit()
    
    logger.info(f"Deactivated user: {db_user.email}")
    
    return db_user


def reactivate_user(db_user: User, db: Optional[Session] = None) -> User:
    """
    Reactivate a deactivated user account
    
    Args:
        db_user: User to reactivate
        db: Optional database session
        
    Returns:
        Reactivated user instance
    """
    db_session_local = db or db_session
    
    # Set active flag to True
    db_user.is_active = True
    
    # Save changes
    db_session_local.add(db_user)
    db_session_local.commit()
    
    logger.info(f"Reactivated user: {db_user.email}")
    
    return db_user


def change_user_role(db_user: User, new_role: str, db: Optional[Session] = None) -> User:
    """
    Change a user's role
    
    Args:
        db_user: User to update
        new_role: New role to assign
        db: Optional database session
        
    Returns:
        User instance with updated role
        
    Raises:
        ValidationException: If the role is invalid
    """
    db_session_local = db or db_session
    
    # Validate role
    if new_role not in ALL_ROLES:
        raise ValidationException(
            message=f"Invalid role. Must be one of: {', '.join(ALL_ROLES)}",
            error_code="invalid_role"
        )
    
    # Set new role
    db_user.role = new_role
    
    # Save changes
    db_session_local.add(db_user)
    db_session_local.commit()
    
    logger.info(f"Changed role for user {db_user.email} to {new_role}")
    
    return db_user


def search_users(query: str, db: Optional[Session] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    """
    Search users by email or full name
    
    Args:
        query: Search string
        db: Optional database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (pagination)
        
    Returns:
        Dictionary with users and pagination metadata
    """
    db_session_local = db or db_session
    
    return user.search(query=query, db=db_session_local, skip=skip, limit=limit)


def get_users_by_organization(organization_id: UUID, db: Optional[Session] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    """
    Get users belonging to a specific organization
    
    Args:
        organization_id: ID of the organization
        db: Optional database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (pagination)
        
    Returns:
        Dictionary with users and pagination metadata
    """
    db_session_local = db or db_session
    
    return user.get_by_organization(organization_id=organization_id, db=db_session_local, skip=skip, limit=limit)


def generate_mfa_secret(db_user: User, db: Optional[Session] = None) -> Dict[str, str]:
    """
    Generate a new MFA secret for a user
    
    Args:
        db_user: User to generate MFA secret for
        db: Optional database session
        
    Returns:
        Dictionary with MFA secret and provisioning URI
    """
    db_session_local = db or db_session
    
    # Generate new MFA secret
    mfa_secret = pyotp.random_base32()
    
    # Store the secret in the user's record
    db_user.mfa_secret = mfa_secret
    
    # Generate provisioning URI for QR code
    totp = pyotp.TOTP(mfa_secret)
    provisioning_uri = totp.provisioning_uri(name=db_user.email, issuer_name="MoleculeFlow")
    
    # Save changes
    db_session_local.add(db_user)
    db_session_local.commit()
    
    logger.info(f"Generated MFA secret for user: {db_user.email}")
    
    return {
        "secret": mfa_secret,
        "provisioning_uri": provisioning_uri
    }


def verify_mfa_code(db_user: User, mfa_code: str) -> bool:
    """
    Verify a multi-factor authentication code
    
    Args:
        db_user: User to verify MFA code for
        mfa_code: MFA verification code
        
    Returns:
        True if verification is successful, False otherwise
    """
    # Ensure user has MFA secret
    if not hasattr(db_user, 'mfa_secret') or not db_user.mfa_secret:
        return False
    
    # Create TOTP object with user's secret
    totp = pyotp.TOTP(db_user.mfa_secret)
    
    # Verify the code
    return totp.verify(mfa_code)


def enable_mfa(db_user: User, mfa_code: str, db: Optional[Session] = None) -> bool:
    """
    Enable multi-factor authentication for a user
    
    Args:
        db_user: User to enable MFA for
        mfa_code: MFA verification code
        db: Optional database session
        
    Returns:
        True if MFA was enabled successfully
    """
    db_session_local = db or db_session
    
    # Verify the MFA code
    if not verify_mfa_code(db_user, mfa_code):
        return False
    
    # Enable MFA for the user
    db_user.mfa_enabled = True
    
    # Save changes
    db_session_local.add(db_user)
    db_session_local.commit()
    
    logger.info(f"Enabled MFA for user: {db_user.email}")
    
    return True


def disable_mfa(db_user: User, db: Optional[Session] = None) -> bool:
    """
    Disable multi-factor authentication for a user
    
    Args:
        db_user: User to disable MFA for
        db: Optional database session
        
    Returns:
        True if MFA was disabled successfully
    """
    db_session_local = db or db_session
    
    # Disable MFA for the user
    db_user.mfa_enabled = False
    # Clear the MFA secret
    db_user.mfa_secret = None
    
    # Save changes
    db_session_local.add(db_user)
    db_session_local.commit()
    
    logger.info(f"Disabled MFA for user: {db_user.email}")
    
    return True


def generate_auth_tokens(db_user: User) -> Dict[str, str]:
    """
    Generate access and refresh tokens for a user
    
    Args:
        db_user: User to generate tokens for
        
    Returns:
        Dictionary containing access and refresh tokens
    """
    # Create token data with user information
    token_data = {
        "sub": str(db_user.id),
        "email": db_user.email,
        "role": db_user.role,
        "is_active": db_user.is_active
    }
    
    # Generate access and refresh tokens
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


class UserService:
    """
    Service class for user management operations
    """
    
    def create_user(self, user_in: UserCreate, db: Optional[Session] = None) -> User:
        """
        Create a new user with validated data
        
        Args:
            user_in: User data for creation
            db: Optional database session
            
        Returns:
            Created user instance
        """
        return create_user(user_in=user_in, db=db)
    
    def get_user_by_id(self, user_id: UUID, db: Optional[Session] = None) -> Optional[User]:
        """
        Get a user by ID
        
        Args:
            user_id: User ID to look up
            db: Optional database session
            
        Returns:
            User instance if found, None otherwise
        """
        return get_user_by_id(user_id=user_id, db=db)
    
    def get_user_by_email(self, email: str, db: Optional[Session] = None) -> Optional[User]:
        """
        Get a user by email address
        
        Args:
            email: Email address to look up
            db: Optional database session
            
        Returns:
            User instance if found, None otherwise
        """
        return get_user_by_email(email=email, db=db)
    
    def authenticate_user(self, email: str, password: str, db: Optional[Session] = None) -> Optional[User]:
        """
        Authenticate a user with email and password
        
        Args:
            email: User's email address
            password: User's password
            db: Optional database session
            
        Returns:
            Authenticated user or None if authentication fails
        """
        return authenticate_user(email=email, password=password, db=db)
    
    def update_user(self, db_user: User, user_in: UserUpdate, db: Optional[Session] = None) -> User:
        """
        Update user information
        
        Args:
            db_user: Existing user to update
            user_in: User data for updating
            db: Optional database session
            
        Returns:
            Updated user instance
        """
        return update_user(db_user=db_user, user_in=user_in, db=db)
    
    def change_password(self, db_user: User, password_data: PasswordChange, db: Optional[Session] = None) -> User:
        """
        Change a user's password with verification of current password
        
        Args:
            db_user: User instance to update
            password_data: Password change data with current and new password
            db: Optional database session
            
        Returns:
            User instance with updated password
        """
        return change_password(db_user=db_user, password_data=password_data, db=db)
    
    def deactivate_user(self, db_user: User, db: Optional[Session] = None) -> User:
        """
        Deactivate a user account
        
        Args:
            db_user: User to deactivate
            db: Optional database session
            
        Returns:
            Deactivated user instance
        """
        return deactivate_user(db_user=db_user, db=db)
    
    def reactivate_user(self, db_user: User, db: Optional[Session] = None) -> User:
        """
        Reactivate a deactivated user account
        
        Args:
            db_user: User to reactivate
            db: Optional database session
            
        Returns:
            Reactivated user instance
        """
        return reactivate_user(db_user=db_user, db=db)
    
    def change_user_role(self, db_user: User, new_role: str, db: Optional[Session] = None) -> User:
        """
        Change a user's role
        
        Args:
            db_user: User to update
            new_role: New role to assign
            db: Optional database session
            
        Returns:
            User instance with updated role
        """
        return change_user_role(db_user=db_user, new_role=new_role, db=db)
    
    def search_users(self, query: str, db: Optional[Session] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Search users by email or full name
        
        Args:
            query: Search string
            db: Optional database session
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return (pagination)
            
        Returns:
            Dictionary with users and pagination metadata
        """
        return search_users(query=query, db=db, skip=skip, limit=limit)
    
    def get_users_by_organization(self, organization_id: UUID, db: Optional[Session] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Get users belonging to a specific organization
        
        Args:
            organization_id: ID of the organization
            db: Optional database session
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return (pagination)
            
        Returns:
            Dictionary with users and pagination metadata
        """
        return get_users_by_organization(organization_id=organization_id, db=db, skip=skip, limit=limit)
    
    def generate_mfa_secret(self, db_user: User, db: Optional[Session] = None) -> Dict[str, str]:
        """
        Generate a new MFA secret for a user
        
        Args:
            db_user: User to generate MFA secret for
            db: Optional database session
            
        Returns:
            Dictionary with MFA secret and provisioning URI
        """
        return generate_mfa_secret(db_user=db_user, db=db)
    
    def verify_mfa_code(self, db_user: User, mfa_code: str) -> bool:
        """
        Verify a multi-factor authentication code
        
        Args:
            db_user: User to verify MFA code for
            mfa_code: MFA verification code
            
        Returns:
            True if verification is successful, False otherwise
        """
        return verify_mfa_code(db_user=db_user, mfa_code=mfa_code)
    
    def enable_mfa(self, db_user: User, mfa_code: str, db: Optional[Session] = None) -> bool:
        """
        Enable multi-factor authentication for a user
        
        Args:
            db_user: User to enable MFA for
            mfa_code: MFA verification code
            db: Optional database session
            
        Returns:
            True if MFA was enabled successfully
        """
        return enable_mfa(db_user=db_user, mfa_code=mfa_code, db=db)
    
    def disable_mfa(self, db_user: User, db: Optional[Session] = None) -> bool:
        """
        Disable multi-factor authentication for a user
        
        Args:
            db_user: User to disable MFA for
            db: Optional database session
            
        Returns:
            True if MFA was disabled successfully
        """
        return disable_mfa(db_user=db_user, db=db)
    
    def generate_auth_tokens(self, db_user: User) -> Dict[str, str]:
        """
        Generate access and refresh tokens for a user
        
        Args:
            db_user: User to generate tokens for
            
        Returns:
            Dictionary containing access and refresh tokens
        """
        return generate_auth_tokens(db_user=db_user)


# Create a singleton instance of UserService
user_service = UserService()