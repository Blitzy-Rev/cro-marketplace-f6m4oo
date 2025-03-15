import pytest
from unittest import mock
import uuid
import json

from ..conftest import app, client, db_session, test_user, test_admin, admin_token_headers, create_test_user, SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST, CRO_ADMIN, settings  # Import fixtures
# pytest: ^7.0.0
# unittest: standard library
# uuid: standard library
# json: standard library

TEST_USER_EMAIL = "test-user@example.com"
TEST_USER_PASSWORD = "Password123!"
TEST_USER_NAME = "Test User"

@pytest.mark.skipif(settings.AUTH_TYPE == 'cognito', reason='Skip for Cognito auth')
def test_login_success(client, test_user):
    """Test successful login with valid credentials"""
    # Create login data with test user email and password
    login_data = {
        "username": test_user.email,
        "password": TEST_USER_PASSWORD
    }
    # Send POST request to /api/v1/auth/login with login data
    response = client.post("/api/v1/auth/login", data=login_data)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse response JSON
    response_json = response.json()
    # Assert response contains access_token, refresh_token, and token_type
    assert "access_token" in response_json
    assert "refresh_token" in response_json
    assert "token_type" in response_json
    # Assert token_type is 'bearer'
    assert response_json["token_type"] == "bearer"

@pytest.mark.skipif(settings.AUTH_TYPE == 'cognito', reason='Skip for Cognito auth')
def test_login_invalid_credentials(client):
    """Test login failure with invalid credentials"""
    # Create login data with invalid email and password
    login_data = {
        "username": "invalid-user@example.com",
        "password": "wrong_password"
    }
    # Send POST request to /api/v1/auth/login with invalid login data
    response = client.post("/api/v1/auth/login", data=login_data)
    # Assert response status code is 401
    assert response.status_code == 401
    # Parse response JSON
    response_json = response.json()
    # Assert response contains error message about invalid credentials
    assert "detail" in response_json
    assert "Invalid username or password" in response_json["detail"]

@pytest.mark.skipif(settings.AUTH_TYPE == 'cognito', reason='Skip for Cognito auth')
def test_register_success(client, db_session):
    """Test successful user registration"""
    # Create unique email for registration
    unique_email = f"new-user-{uuid.uuid4()}@example.com"
    # Create registration data with email, password, and name
    register_data = {
        "email": unique_email,
        "password": TEST_USER_PASSWORD,
        "full_name": "New Test User"
    }
    # Send POST request to /api/v1/auth/register with registration data
    response = client.post("/api/v1/auth/register", json=register_data)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse response JSON
    response_json = response.json()
    # Assert response contains success status and message
    assert response_json["status"] == "success"
    assert "Registration successful" in response_json["message"]
    # Verify user exists in database
    from src.backend.app.models.user import User
    user = db_session.query(User).filter(User.email == unique_email).first()
    assert user is not None
    assert user.email == unique_email
    assert user.full_name == "New Test User"

@pytest.mark.skipif(settings.AUTH_TYPE == 'cognito', reason='Skip for Cognito auth')
def test_register_existing_user(client, test_user):
    """Test registration failure with existing email"""
    # Create registration data with existing test user email
    register_data = {
        "email": test_user.email,
        "password": "AnotherPassword123!",
        "full_name": "Another Test User"
    }
    # Send POST request to /api/v1/auth/register with registration data
    response = client.post("/api/v1/auth/register", json=register_data)
    # Assert response status code is 400
    assert response.status_code == 400
    # Parse response JSON
    response_json = response.json()
    # Assert response contains error message about existing user
    assert "detail" in response_json
    assert "A user with this email already exists" in response_json["detail"]

@pytest.mark.skipif(settings.AUTH_TYPE == 'cognito', reason='Skip for Cognito auth')
def test_refresh_token(client, test_user):
    """Test refreshing access token with valid refresh token"""
    # Login to get initial tokens
    login_data = {
        "username": test_user.email,
        "password": TEST_USER_PASSWORD
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    login_response = response.json()
    # Extract refresh token from login response
    refresh_token = login_response["refresh_token"]
    # Create refresh request data with refresh token
    refresh_data = {
        "refresh_token": refresh_token
    }
    # Send POST request to /api/v1/auth/refresh with refresh data
    response = client.post("/api/v1/auth/refresh", json=refresh_data)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse response JSON
    refresh_response = response.json()
    # Assert response contains new access_token and same refresh_token
    assert "access_token" in refresh_response
    assert "refresh_token" in refresh_response
    assert refresh_response["refresh_token"] == refresh_token
    # Assert token_type is 'bearer'
    assert refresh_response["token_type"] == "bearer"

@pytest.mark.skipif(settings.AUTH_TYPE == 'cognito', reason='Skip for Cognito auth')
def test_refresh_token_invalid(client):
    """Test refresh token failure with invalid refresh token"""
    # Create refresh request data with invalid refresh token
    refresh_data = {
        "refresh_token": "invalid_refresh_token"
    }
    # Send POST request to /api/v1/auth/refresh with invalid refresh data
    response = client.post("/api/v1/auth/refresh", json=refresh_data)
    # Assert response status code is 401
    assert response.status_code == 401
    # Parse response JSON
    response_json = response.json()
    # Assert response contains error message about invalid token
    assert "detail" in response_json
    assert "Invalid authentication token" in response_json["detail"]

@pytest.mark.skipif(settings.AUTH_TYPE == 'cognito', reason='Skip for Cognito auth')
def test_change_password(client, db_session):
    """Test changing user password"""
    # Create test user with known password
    from src.backend.app.models.user import User
    from src.backend.app.core.security import get_password_hash
    test_user = User(email="changepassword@example.com", full_name="Change Password User", hashed_password=get_password_hash("old_password"), role=PHARMA_SCIENTIST, is_active=True)
    db_session.add(test_user)
    db_session.commit()
    # Login to get authentication token
    login_data = {
        "username": "changepassword@example.com",
        "password": "old_password"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    login_response = response.json()
    token = login_response["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Create password change data with current and new password
    password_data = {
        "current_password": "old_password",
        "new_password": "new_Password123!"
    }
    # Send POST request to /api/v1/auth/change-password with password data and auth header
    response = client.post("/api/v1/auth/change-password", json=password_data, headers=headers)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse response JSON
    response_json = response.json()
    # Assert response contains success status and message
    assert response_json["status"] == "success"
    assert "Password changed successfully" in response_json["message"]
    # Verify login with new password works
    login_data = {
        "username": "changepassword@example.com",
        "password": "new_Password123!"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200

@pytest.mark.skipif(settings.AUTH_TYPE == 'cognito', reason='Skip for Cognito auth')
def test_change_password_invalid_current(client, admin_token_headers):
    """Test password change failure with invalid current password"""
    # Create password change data with incorrect current password
    password_data = {
        "current_password": "wrong_password",
        "new_password": "new_Password123!"
    }
    # Send POST request to /api/v1/auth/change-password with invalid data and auth header
    response = client.post("/api/v1/auth/change-password", json=password_data, headers=admin_token_headers)
    # Assert response status code is 401
    assert response.status_code == 401
    # Parse response JSON
    response_json = response.json()
    # Assert response contains error message about invalid current password
    assert "detail" in response_json
    assert "Current password is incorrect" in response_json["detail"]

@pytest.mark.skipif(settings.AUTH_TYPE == 'cognito', reason='Skip for Cognito auth')
def test_change_password_weak_new(client, admin_token_headers):
    """Test password change failure with weak new password"""
    # Create password change data with valid current password but weak new password
    password_data = {
        "current_password": TEST_USER_PASSWORD,
        "new_password": "weak"
    }
    # Send POST request to /api/v1/auth/change-password with invalid data and auth header
    response = client.post("/api/v1/auth/change-password", json=password_data, headers=admin_token_headers)
    # Assert response status code is 400
    assert response.status_code == 400
    # Parse response JSON
    response_json = response.json()
    # Assert response contains error message about password requirements
    assert "detail" in response_json
    assert "Password must be at least 12 characters long and include uppercase, lowercase, number, and special characters" in response_json["detail"]

@pytest.mark.skipif(settings.AUTH_TYPE != 'cognito', reason='Only for Cognito auth')
@mock.patch('src.backend.app.services.auth_service.cognito_client.forgot_password')
def test_forgot_password(mock_forgot_password, client, test_user):
    """Test initiating forgot password flow"""
    # Mock cognito_client.forgot_password to return success response
    mock_forgot_password.return_value = {"CodeDeliveryDetails": {"Destination": "test-user@example.com", "DeliveryMedium": "EMAIL"}}
    # Send POST request to /api/v1/auth/forgot-password with test user email
    response = client.post("/api/v1/auth/forgot-password", params={"username": test_user.email})
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse response JSON
    response_json = response.json()
    # Assert response contains success status and message
    assert response_json["status"] == "success"
    assert "If your account exists, a password reset code has been sent to your email" in response_json["message"]
    # Verify mock was called with correct parameters
    mock_forgot_password.assert_called_once_with(test_user.email)

@pytest.mark.skipif(settings.AUTH_TYPE != 'cognito', reason='Only for Cognito auth')
@mock.patch('src.backend.app.services.auth_service.cognito_client.confirm_forgot_password')
def test_reset_password(mock_confirm_forgot_password, client):
    """Test resetting password with verification code"""
    # Mock cognito_client.confirm_forgot_password to return success response
    mock_confirm_forgot_password.return_value = True
    # Create reset password data with username, confirmation code, and new password
    reset_data = {
        "username": "test-user@example.com",
        "confirmation_code": "123456",
        "new_password": "NewPassword123!"
    }
    # Send POST request to /api/v1/auth/reset-password with reset data
    response = client.post("/api/v1/auth/reset-password", params=reset_data)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse response JSON
    response_json = response.json()
    # Assert response contains success status and message
    assert response_json["status"] == "success"
    assert "Password has been reset successfully. You can now log in with your new password" in response_json["message"]
    # Verify mock was called with correct parameters
    mock_confirm_forgot_password.assert_called_once_with("test-user@example.com", "123456", "NewPassword123!")

@pytest.mark.skipif(settings.AUTH_TYPE != 'cognito', reason='Only for Cognito auth')
@mock.patch('src.backend.app.services.auth_service.cognito_client.setup_mfa')
def test_setup_mfa(mock_setup_mfa, client, admin_token_headers):
    """Test setting up MFA for a user"""
    # Mock cognito_client.setup_mfa to return MFA setup information
    mock_setup_mfa.return_value = {"SecretCode": "secret", "QRCodeContent": "qr_code"}
    # Send POST request to /api/v1/auth/setup-mfa with auth header
    response = client.post("/api/v1/auth/setup-mfa", headers=admin_token_headers)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse response JSON
    response_json = response.json()
    # Assert response contains secret code and QR code URL
    assert "SecretCode" in response_json
    assert "QRCodeContent" in response_json
    # Verify mock was called with correct parameters
    mock_setup_mfa.assert_called_once()

@pytest.mark.skipif(settings.AUTH_TYPE != 'cognito', reason='Only for Cognito auth')
@mock.patch('src.backend.app.services.auth_service.cognito_client.verify_mfa_setup')
def test_verify_mfa_setup(mock_verify_mfa_setup, client, admin_token_headers):
    """Test verifying MFA setup with verification code"""
    # Mock cognito_client.verify_mfa_setup to return success response
    mock_verify_mfa_setup.return_value = True
    # Create verification data with verification code
    verification_data = {
        "verification_code": "123456"
    }
    # Send POST request to /api/v1/auth/verify-mfa with verification data and auth header
    response = client.post("/api/v1/auth/verify-mfa", params=verification_data, headers=admin_token_headers)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse response JSON
    response_json = response.json()
    # Assert response contains success status and message
    assert response_json["status"] == "success"
    assert "MFA setup verified successfully" in response_json["message"]
    # Verify mock was called with correct parameters
    mock_verify_mfa_setup.assert_called_once()

@pytest.mark.skipif(settings.AUTH_TYPE != 'cognito', reason='Only for Cognito auth')
@mock.patch('src.backend.app.services.auth_service.cognito_client.sign_out')
def test_sign_out(mock_sign_out, client, admin_token_headers):
    """Test signing out a user from all devices"""
    # Mock cognito_client.sign_out to return success response
    mock_sign_out.return_value = True
    # Send POST request to /api/v1/auth/sign-out with auth header
    response = client.post("/api/v1/auth/sign-out", headers=admin_token_headers)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse response JSON
    response_json = response.json()
    # Assert response contains success status and message
    assert response_json["status"] == "success"
    assert "Signed out successfully" in response_json["message"]
    # Verify mock was called with correct parameters
    mock_sign_out.assert_called_once()

def test_test_token(client, admin_token_headers):
    """Test the test-token endpoint for token validation"""
    # Send POST request to /api/v1/auth/test-token with auth header
    response = client.post("/api/v1/auth/test-token", headers=admin_token_headers)
    # Assert response status code is 200
    assert response.status_code == 200
    # Parse response JSON
    response_json = response.json()
    # Assert response contains message confirming token is valid
    assert "message" in response_json
    assert "Token is valid" in response_json["message"]

def test_test_token_invalid(client):
    """Test the test-token endpoint with invalid token"""
    # Create invalid auth header with made-up token
    invalid_headers = {"Authorization": "Bearer made_up_token"}
    # Send POST request to /api/v1/auth/test-token with invalid auth header
    response = client.post("/api/v1/auth/test-token", headers=invalid_headers)
    # Assert response status code is 401
    assert response.status_code == 401
    # Parse response JSON
    response_json = response.json()
    # Assert response contains error message about invalid token
    assert "detail" in response_json
    assert "Invalid authentication token" in response_json["detail"]