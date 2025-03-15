from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr  # pydantic version 2.0.0


class Token(BaseModel):
    """Schema for authentication token response containing access and refresh tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    mfa_required: Optional[bool] = None


class TokenPayload(BaseModel):
    """Schema for JWT token payload containing user information and metadata"""
    user_id: UUID
    email: str
    role: str
    token_type: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    exp: Optional[int] = None


class TokenData(BaseModel):
    """Schema for decoded token data with user information"""
    user_id: UUID
    email: Optional[str] = None
    role: Optional[str] = None


class TokenRequest(BaseModel):
    """Schema for authentication request with username and password"""
    username: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request containing a refresh token"""
    refresh_token: str