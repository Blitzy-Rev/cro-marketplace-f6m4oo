"""
SQLAlchemy User model for the Molecular Data Management and CRO Integration Platform.

This model defines user accounts with authentication capabilities, role-based access control,
and organization association. It includes methods for password management, user type
identification, and audit tracking.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UUID
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import uuid

# Internal imports
from ..db.base_class import Base
from ..core.security import get_password_hash, verify_password
from ..constants.user_roles import DEFAULT_ROLE, ALL_ROLES, PHARMA_ROLES, CRO_ROLES, ADMIN_ROLES


class User(Base):
    """
    SQLAlchemy model representing a user in the system with authentication and role-based access control.
    
    This model stores user account information, credentials, and permissions. It includes
    methods for password management, role validation, and determining user types based on roles.
    """
    # Basic user information
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Role and permissions
    role = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Organization association
    organization_name = Column(String(255), nullable=True)
    organization_id = Column(UUID, nullable=True, index=True)
    
    # Audit information
    last_login = Column(DateTime, nullable=True)
    
    def __init__(self, **kwargs):
        """Initialize a new User instance with default values."""
        # Set default values
        if 'is_active' not in kwargs:
            kwargs['is_active'] = True
        if 'is_superuser' not in kwargs:
            kwargs['is_superuser'] = False
        if 'role' not in kwargs or kwargs['role'] is None:
            kwargs['role'] = DEFAULT_ROLE
            
        super().__init__(**kwargs)
    
    def set_password(self, password: str) -> None:
        """
        Set the user's password by hashing the provided plain password.
        
        Args:
            password: Plain text password to hash and store
        """
        self.hashed_password = get_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """
        Verify if the provided password matches the stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        return verify_password(password, self.hashed_password)
    
    def update_last_login(self) -> None:
        """Update the user's last login timestamp to current time."""
        self.last_login = datetime.utcnow()
    
    @validates('role')
    def validate_role(self, key: str, role: str) -> str:
        """
        Validate that the role is one of the allowed roles.
        
        Args:
            key: Field name being validated (always 'role')
            role: Role value to validate
            
        Returns:
            Validated role
            
        Raises:
            ValueError: If role is not in the list of allowed roles
        """
        if role is None:
            return DEFAULT_ROLE
            
        if role not in ALL_ROLES:
            allowed_roles = ", ".join(ALL_ROLES)
            raise ValueError(f"Invalid role. Must be one of: {allowed_roles}")
            
        return role
    
    @validates('email')
    def validate_email(self, key: str, email: str) -> str:
        """
        Validate that the email is properly formatted.
        
        Args:
            key: Field name being validated (always 'email')
            email: Email value to validate
            
        Returns:
            Validated email (lowercase)
            
        Raises:
            ValueError: If email is None or does not contain '@'
        """
        if email is None:
            raise ValueError("Email is required")
            
        if '@' not in email:
            raise ValueError("Invalid email format")
            
        # Convert email to lowercase for consistency
        return email.lower()
    
    def is_pharma_user(self) -> bool:
        """
        Check if the user has a pharmaceutical company role.
        
        Returns:
            True if user has a pharma role, False otherwise
        """
        return self.role in PHARMA_ROLES
    
    def is_cro_user(self) -> bool:
        """
        Check if the user has a CRO role.
        
        Returns:
            True if user has a CRO role, False otherwise
        """
        return self.role in CRO_ROLES
    
    def is_admin(self) -> bool:
        """
        Check if the user has an administrator role.
        
        Returns:
            True if user has an admin role or is a superuser, False otherwise
        """
        return self.role in ADMIN_ROLES or self.is_superuser