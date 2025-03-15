"""
User Schema Module

This module defines Pydantic schema models for user data validation, serialization, 
and deserialization in the Molecular Data Management and CRO Integration Platform. 
These schemas ensure data integrity for user-related operations throughout the application.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, validator

from ..constants.user_roles import ALL_ROLES, DEFAULT_ROLE
from ..core.security import validate_password


class UserBase(BaseModel):
    """Base Pydantic model for user data with common fields."""
    email: EmailStr
    full_name: str
    organization_name: Optional[str] = None
    organization_id: Optional[UUID] = None
    role: Optional[str] = DEFAULT_ROLE

    @validator('role')
    def validate_role(cls, v):
        """Validate that the role is one of the allowed roles."""
        if v is None:
            return DEFAULT_ROLE
        if v not in ALL_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(ALL_ROLES)}")
        return v


class UserCreate(UserBase):
    """Schema for user creation with password validation."""
    password: str

    @validator('password')
    def validate_password(cls, v):
        """Validate password complexity requirements."""
        if not validate_password(v):
            raise ValueError(
                "Password must be at least 12 characters long and include "
                "uppercase, lowercase, number, and special characters"
            )
        return v


class UserUpdate(BaseModel):
    """Schema for user updates with optional fields."""
    full_name: Optional[str] = None
    password: Optional[str] = None
    organization_name: Optional[str] = None
    organization_id: Optional[UUID] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

    @validator('password')
    def validate_password(cls, v):
        """Validate password complexity requirements if provided."""
        if v is None:
            return None
        if not validate_password(v):
            raise ValueError(
                "Password must be at least 12 characters long and include "
                "uppercase, lowercase, number, and special characters"
            )
        return v

    @validator('role')
    def validate_role(cls, v):
        """Validate that the role is one of the allowed roles if provided."""
        if v is None:
            return None
        if v not in ALL_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(ALL_ROLES)}")
        return v


class UserInDBBase(UserBase):
    """Base schema for user data from database including ID and timestamps."""
    id: UUID
    is_active: bool = True
    is_superuser: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class UserInDB(UserInDBBase):
    """Complete user schema with hashed password for database operations."""
    hashed_password: str


class User(UserInDBBase):
    """User schema for API responses without sensitive information."""
    pass


class UserWithPermissions(User):
    """Extended user schema with permissions for authorization."""
    permissions: Dict[str, Any] = {}


class PasswordChange(BaseModel):
    """Schema for password change requests."""
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password complexity requirements."""
        if not validate_password(v):
            raise ValueError(
                "New password must be at least 12 characters long and include "
                "uppercase, lowercase, number, and special characters"
            )
        return v