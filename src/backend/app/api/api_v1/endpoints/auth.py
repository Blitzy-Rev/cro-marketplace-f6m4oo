from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from ....schemas.token import Token, TokenRequest, RefreshTokenRequest
from ....schemas.user import UserCreate, User, PasswordChange
from ....schemas.msg import Msg, ResponseMsg, ErrorResponseMsg
from ....services.auth_service import (
    authenticate_user, register_user, refresh_token, change_password,
    forgot_password, reset_password, setup_mfa, verify_mfa_setup,
    sign_out, confirm_registration
)
from ...deps import get_db, get_current_user
from ....core.exceptions import AuthenticationException, ValidationException

router = APIRouter(tags=['authentication'])

@router.post('/login', response_model=Token)
def login(form_data: TokenRequest, db: Session = Depends(get_db)):
    """Authenticate a user and return access and refresh tokens"""
    try:
        auth_response = authenticate_user(form_data.username, form_data.password)
        return Token(
            access_token=auth_response["access_token"],
            refresh_token=auth_response["refresh_token"],
            token_type="bearer",
            mfa_required=auth_response.get("mfa_required")
        )
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post('/register', response_model=ResponseMsg)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user in the system"""
    try:
        register_user(user_data, db)
        return ResponseMsg(
            status="success",
            message="Registration successful. Please check your email for verification code."
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )

@router.post('/confirm-registration', response_model=ResponseMsg)
def confirm_registration_endpoint(username: str, confirmation_code: str):
    """Confirm user registration with verification code"""
    try:
        confirm_registration(username, confirmation_code)
        return ResponseMsg(
            status="success",
            message="Registration confirmed successfully. You can now log in."
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )

@router.post('/refresh', response_model=Token)
def refresh(refresh_request: RefreshTokenRequest):
    """Refresh authentication tokens using a refresh token"""
    try:
        tokens = refresh_token(refresh_request.refresh_token)
        return Token(
            access_token=tokens["access_token"],
            refresh_token=refresh_request.refresh_token,
            token_type="bearer"
        )
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post('/change-password', response_model=ResponseMsg)
def change_password_endpoint(
    password_data: PasswordChange, 
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    try:
        change_password(
            str(current_user.id), 
            password_data.current_password, 
            password_data.new_password
        )
        return ResponseMsg(
            status="success",
            message="Password changed successfully."
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )

@router.post('/forgot-password', response_model=ResponseMsg)
def forgot_password_endpoint(username: str):
    """Initiate forgot password flow"""
    try:
        forgot_password(username)
        return ResponseMsg(
            status="success",
            message="If your account exists, a password reset code has been sent to your email."
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )

@router.post('/reset-password', response_model=ResponseMsg)
def reset_password_endpoint(username: str, confirmation_code: str, new_password: str):
    """Reset password with verification code"""
    try:
        reset_password(username, confirmation_code, new_password)
        return ResponseMsg(
            status="success",
            message="Password has been reset successfully. You can now log in with your new password."
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )

@router.post('/setup-mfa')
def setup_mfa_endpoint(current_user: User = Depends(get_current_user)):
    """Set up MFA for a user"""
    try:
        # In a real implementation, we would extract the access token from
        # the Authorization header. Here, we need to implement that extraction.
        # For demonstration, we're using a placeholder
        from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
        from fastapi import Request
        
        # Extract the actual token from the Authorization header
        # This would typically be implemented as a dependency
        access_token = "Extract from Authorization header"
        
        # Setup MFA
        mfa_setup_info = setup_mfa(access_token)
        
        return mfa_setup_info
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )

@router.post('/verify-mfa', response_model=ResponseMsg)
def verify_mfa_setup_endpoint(
    verification_code: str, 
    current_user: User = Depends(get_current_user)
):
    """Verify MFA setup with a verification code"""
    try:
        # In a real implementation, we would extract the access token from
        # the Authorization header. Here, we need to implement that extraction.
        access_token = "Extract from Authorization header"
        
        # Verify MFA setup
        verify_mfa_setup(access_token, verification_code)
        
        return ResponseMsg(
            status="success",
            message="MFA setup verified successfully."
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )

@router.post('/sign-out', response_model=ResponseMsg)
def sign_out_endpoint(current_user: User = Depends(get_current_user)):
    """Sign out a user from all devices"""
    try:
        # In a real implementation, we would extract the access token from
        # the Authorization header. Here, we need to implement that extraction.
        access_token = "Extract from Authorization header"
        
        # Sign out user
        sign_out(access_token)
        
        return ResponseMsg(
            status="success",
            message="Signed out successfully."
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )

@router.post('/test-token', response_model=Msg)
def test_token(current_user: User = Depends(get_current_user)):
    """Test endpoint to verify token authentication"""
    return Msg(message="Token is valid")