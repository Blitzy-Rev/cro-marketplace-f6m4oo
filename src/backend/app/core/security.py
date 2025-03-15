"""
Core security module for the Molecular Data Management and CRO Integration Platform.

This module implements JWT token generation, password hashing, authentication utilities,
and other security-related functionality. It serves as the central security component 
for the application's authentication and authorization system.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Union

# JWT handling - python-jose v3.3.0
from jose import jwt, JWTError

# Password hashing - passlib v1.7.4
from passlib.context import CryptContext

# Regular expressions - standard library
import re

# Internal imports
from .config import settings
from .constants import TOKEN_ALGORITHM, PASSWORD_MIN_LENGTH, PASSWORD_REGEX
from .exceptions import AuthenticationException
from ..constants.user_roles import ALL_ROLES

# Set up password hashing context with bcrypt scheme
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Use token algorithm from constants
ALGORITHM = TOKEN_ALGORITHM


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against
        
    Returns:
        True if password matches hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate a password hash for a plain password.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def validate_password(password: str) -> bool:
    """
    Validate password against security requirements.
    
    Password must:
    - Be at least PASSWORD_MIN_LENGTH characters long (12 characters)
    - Match the PASSWORD_REGEX pattern (upper, lower, number, special char)
    
    Args:
        password: The password to validate
        
    Returns:
        True if password meets requirements, False otherwise
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        return False
    
    if not re.match(PASSWORD_REGEX, password):
        return False
    
    return True


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with an expiration time.
    
    Args:
        data: Payload data to include in token
        expires_delta: Optional custom expiration time, otherwise uses settings default
        
    Returns:
        Encoded JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "token_type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token with a longer expiration time.
    
    Args:
        data: Payload data to include in token
        expires_delta: Optional custom expiration time, otherwise uses settings default
        
    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "token_type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded token payload
        
    Raises:
        AuthenticationException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise AuthenticationException("Invalid authentication token")


def validate_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
    """
    Validate that a token is of the expected type.
    
    Args:
        payload: Decoded token payload
        expected_type: Expected token type ("access" or "refresh")
        
    Returns:
        True if token is of expected type, False otherwise
    """
    return "token_type" in payload and payload["token_type"] == expected_type


def is_token_expired(payload: Dict[str, Any]) -> bool:
    """
    Check if a token has expired based on its expiration time.
    
    Args:
        payload: Decoded token payload
        
    Returns:
        True if token is expired, False otherwise
    """
    if "exp" not in payload:
        return True
    
    exp = payload["exp"]
    now = datetime.utcnow().timestamp()
    
    return now > exp


def get_token_expiration(payload: Dict[str, Any]) -> datetime:
    """
    Get the expiration datetime from a token payload.
    
    Args:
        payload: Decoded token payload
        
    Returns:
        Token expiration datetime
    """
    exp = payload["exp"]
    return datetime.fromtimestamp(exp)


def validate_access_token(token: str) -> Dict[str, Any]:
    """
    Validate an access token and return its payload.
    
    Args:
        token: Access token to validate
        
    Returns:
        Validated token payload
        
    Raises:
        AuthenticationException: If token is invalid, expired, or wrong type
    """
    payload = decode_token(token)
    
    if not validate_token_type(payload, "access"):
        raise AuthenticationException("Invalid token type")
    
    if is_token_expired(payload):
        raise AuthenticationException("Token has expired")
    
    return payload


def validate_refresh_token(token: str) -> Dict[str, Any]:
    """
    Validate a refresh token and return its payload.
    
    Args:
        token: Refresh token to validate
        
    Returns:
        Validated token payload
        
    Raises:
        AuthenticationException: If token is invalid, expired, or wrong type
    """
    payload = decode_token(token)
    
    if not validate_token_type(payload, "refresh"):
        raise AuthenticationException("Invalid token type")
    
    if is_token_expired(payload):
        raise AuthenticationException("Token has expired")
    
    return payload


def create_tokens_for_user(user_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Create both access and refresh tokens for a user.
    
    Args:
        user_data: User information to include in token payload
        
    Returns:
        Dictionary containing access and refresh tokens
    """
    token_data = user_data.copy()
    
    # Remove any sensitive data from token payload
    if "password" in token_data:
        del token_data["password"]
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }


def validate_role(role: str) -> bool:
    """
    Validate that a role is in the list of allowed roles.
    
    Args:
        role: Role to validate
        
    Returns:
        True if role is valid, False otherwise
    """
    return role in ALL_ROLES