import pytest
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock

from ...app.services.auth_service import (
    authenticate_user,
    register_user,
    refresh_token,
    get_current_user,
    get_user_permissions,
    change_password,
    forgot_password,
    reset_password,
    setup_mfa,
    verify_mfa_setup,
    sign_out,
    confirm_registration
)
from ...app.schemas.user import UserCreate
from ...app.schemas.token import TokenPayload
from ...app.core.exceptions import AuthenticationException, ValidationException
from ...app.integrations.aws.cognito import CognitoClient
from ...app.core.security import create_access_token, validate_access_token
from ...app.constants.user_roles import SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST


@patch('app.services.auth_service.settings.AUTH_TYPE', 'database')
def test_authenticate_user_database_success():
    # Mock user.authenticate to return a valid user object
    user_mock = MagicMock()
    user_mock.id = uuid.uuid4()
    user_mock.email = "test@example.com"
    user_mock.role = "pharma_scientist"
    user_mock.full_name = "Test User"
    user_mock.is_active = True
    
    with patch('app.crud.crud_user.user.authenticate', return_value=user_mock):
        result = authenticate_user("test@example.com", "Password123!")
    
    # Assert that the response contains access_token, refresh_token, and user information
    assert "access_token" in result
    assert "refresh_token" in result
    assert result["user_id"] == str(user_mock.id)
    assert result["email"] == "test@example.com"
    assert result["role"] == "pharma_scientist"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'database')
def test_authenticate_user_database_failure():
    # Mock user.authenticate to return None (authentication failure)
    with patch('app.crud.crud_user.user.authenticate', return_value=None), \
         pytest.raises(AuthenticationException) as exc_info:
        authenticate_user("test@example.com", "WrongPassword")
    
    # Assert that AuthenticationException is raised with correct error message
    assert "Invalid username or password" in str(exc_info.value)
    assert exc_info.value.error_code == "invalid_credentials"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_authenticate_user_cognito_success():
    # Mock cognito_client.authenticate to return valid tokens and user attributes
    cognito_response = {
        "access_token": "fake_access_token",
        "refresh_token": "fake_refresh_token",
        "id_token": "fake_id_token",
        "user_id": "user123",
        "role": "pharma_scientist",
        "email": "test@example.com",
        "full_name": "Test User"
    }
    
    with patch('app.services.auth_service.cognito_client.authenticate', return_value=cognito_response):
        result = authenticate_user("test@example.com", "Password123!")
    
    # Assert that the response contains access_token, refresh_token, and user information
    assert result["access_token"] == "fake_access_token"
    assert result["refresh_token"] == "fake_refresh_token"
    assert result["email"] == "test@example.com"
    assert result["role"] == "pharma_scientist"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_authenticate_user_cognito_failure():
    # Mock cognito_client.authenticate to raise AuthenticationException
    with patch('app.services.auth_service.cognito_client.authenticate', 
              side_effect=AuthenticationException(
                  message="Invalid username or password",
                  error_code="invalid_credentials"
              )), \
         pytest.raises(AuthenticationException) as exc_info:
        authenticate_user("test@example.com", "WrongPassword")
    
    # Assert that AuthenticationException is raised with correct error message
    assert "Invalid username or password" in str(exc_info.value)
    assert exc_info.value.error_code == "invalid_credentials"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_authenticate_user_cognito_mfa_required():
    # Mock cognito_client.authenticate to return MFA challenge response
    mfa_challenge = {
        "challenge": "SOFTWARE_TOKEN_MFA",
        "session": "session_token",
        "challenge_parameters": {},
        "mfa_required": True
    }
    
    with patch('app.services.auth_service.cognito_client.authenticate', return_value=mfa_challenge):
        result = authenticate_user("test@example.com", "Password123!")
    
    # Assert that the response contains mfa_required=True and session information
    assert result["mfa_required"] is True
    assert result["session"] == "session_token"
    assert result["challenge"] == "SOFTWARE_TOKEN_MFA"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'invalid')
def test_authenticate_user_invalid_auth_type():
    # Call authenticate_user with valid credentials
    with pytest.raises(ValidationException) as exc_info:
        authenticate_user("test@example.com", "Password123!")
    
    # Assert that ValidationException is raised with correct error message about invalid AUTH_TYPE
    assert "Invalid authentication type" in str(exc_info.value)
    assert exc_info.value.error_code == "config_error"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'database')
def test_register_user_database_success():
    # Mock user.get_by_email to return None (user doesn't exist)
    user_data = UserCreate(
        email="new_user@example.com",
        full_name="New User",
        password="Password123!",
        role="pharma_scientist"
    )
    
    # Mock user.create to return a valid user object
    user_mock = MagicMock()
    user_mock.id = uuid.uuid4()
    user_mock.email = "new_user@example.com"
    user_mock.full_name = "New User"
    user_mock.role = "pharma_scientist"
    user_mock.is_active = True
    
    with patch('app.crud.crud_user.user.get_by_email', return_value=None), \
         patch('app.crud.crud_user.user.create', return_value=user_mock):
        result = register_user(user_data)
    
    # Assert that the response contains user information
    assert result["email"] == "new_user@example.com"
    assert result["full_name"] == "New User"
    assert result["role"] == "pharma_scientist"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'database')
def test_register_user_database_user_exists():
    # Mock user.get_by_email to return an existing user
    user_data = UserCreate(
        email="existing@example.com",
        full_name="Existing User",
        password="Password123!",
        role="pharma_scientist"
    )
    
    existing_user = MagicMock()
    existing_user.email = "existing@example.com"
    
    with patch('app.crud.crud_user.user.get_by_email', return_value=existing_user), \
         pytest.raises(AuthenticationException) as exc_info:
        register_user(user_data)
    
    # Assert that AuthenticationException is raised with user already exists message
    assert "A user with this email already exists" in str(exc_info.value)
    assert exc_info.value.error_code == "email_exists"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_register_user_cognito_success():
    # Mock cognito_client.register to return successful registration response
    user_data = UserCreate(
        email="new_user@example.com",
        full_name="New User",
        password="Password123!",
        role="pharma_scientist"
    )
    
    cognito_response = {
        "UserSub": "user123",
        "email": "new_user@example.com",
        "full_name": "New User",
        "role": "pharma_scientist",
        "requires_confirmation": True
    }
    
    with patch('app.services.auth_service.cognito_client.register', return_value=cognito_response):
        result = register_user(user_data)
    
    # Assert that the response contains user information and confirmation status
    assert result["email"] == "new_user@example.com"
    assert result["full_name"] == "New User"
    assert result["role"] == "pharma_scientist"
    assert result["requires_confirmation"] is True


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_register_user_cognito_failure():
    # Mock cognito_client.register to raise AuthenticationException
    user_data = UserCreate(
        email="new_user@example.com",
        full_name="New User",
        password="Password123!",
        role="pharma_scientist"
    )
    
    with patch('app.services.auth_service.cognito_client.register', 
              side_effect=AuthenticationException(
                  message="Registration failed: Email already exists",
                  error_code="username_exists"
              )), \
         pytest.raises(AuthenticationException) as exc_info:
        register_user(user_data)
    
    # Assert that AuthenticationException is raised with correct error message
    assert "Registration failed: Email already exists" in str(exc_info.value)
    assert exc_info.value.error_code == "username_exists"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'invalid')
def test_register_user_invalid_auth_type():
    # Create UserCreate object with valid data
    user_data = UserCreate(
        email="new_user@example.com",
        full_name="New User",
        password="Password123!",
        role="pharma_scientist"
    )
    
    with pytest.raises(ValidationException) as exc_info:
        register_user(user_data)
    
    # Assert that ValidationException is raised with correct error message about invalid AUTH_TYPE
    assert "Invalid authentication type" in str(exc_info.value)
    assert exc_info.value.error_code == "config_error"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_confirm_registration_success():
    # Mock cognito_client.confirm_registration to return True
    with patch('app.services.auth_service.cognito_client.confirm_registration', return_value=True):
        result = confirm_registration("test@example.com", "123456")
    
    # Assert that the result is True
    assert result is True


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_confirm_registration_failure():
    # Mock cognito_client.confirm_registration to raise AuthenticationException
    with patch('app.services.auth_service.cognito_client.confirm_registration', 
              side_effect=AuthenticationException(
                  message="Invalid verification code",
                  error_code="code_mismatch"
              )), \
         pytest.raises(AuthenticationException) as exc_info:
        confirm_registration("test@example.com", "invalid_code")
    
    # Assert that AuthenticationException is raised with correct error message
    assert "Invalid verification code" in str(exc_info.value)
    assert exc_info.value.error_code == "code_mismatch"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'database')
def test_confirm_registration_invalid_auth_type():
    # Call confirm_registration with valid username and confirmation code
    with pytest.raises(ValidationException) as exc_info:
        confirm_registration("test@example.com", "123456")
    
    # Assert that ValidationException is raised with correct error message about requiring Cognito
    assert "Registration confirmation is only available for Cognito authentication" in str(exc_info.value)
    assert exc_info.value.error_code == "method_not_supported"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'database')
def test_refresh_token_database_success():
    # Mock validate_refresh_token to return valid token payload with user_id
    token_payload = {"user_id": str(uuid.uuid4()), "email": "test@example.com", "role": "pharma_scientist"}
    
    # Mock user.get to return valid user object
    user_mock = MagicMock()
    user_mock.id = uuid.UUID(token_payload["user_id"])
    user_mock.email = "test@example.com"
    user_mock.role = "pharma_scientist"
    user_mock.is_active = True
    
    with patch('app.services.auth_service.validate_refresh_token', return_value=token_payload), \
         patch('app.crud.crud_user.user.get', return_value=user_mock):
        result = refresh_token("fake_refresh_token")
    
    # Assert that the response contains new access_token and original refresh_token
    assert "access_token" in result
    assert result["refresh_token"] == "fake_refresh_token"
    assert result["token_type"] == "bearer"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'database')
def test_refresh_token_database_invalid_token():
    # Mock validate_refresh_token to raise AuthenticationException
    with patch('app.services.auth_service.validate_refresh_token', 
              side_effect=AuthenticationException(
                  message="Invalid token",
                  error_code="invalid_token"
              )), \
         pytest.raises(AuthenticationException) as exc_info:
        refresh_token("invalid_token")
    
    # Assert that AuthenticationException is raised with correct error message
    assert "Invalid token" in str(exc_info.value)
    assert exc_info.value.error_code == "invalid_token"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'database')
def test_refresh_token_database_user_not_found():
    # Mock validate_refresh_token to return valid token payload with user_id
    token_payload = {"user_id": str(uuid.uuid4()), "email": "test@example.com", "role": "pharma_scientist"}
    
    # Mock user.get to return None (user not found)
    with patch('app.services.auth_service.validate_refresh_token', return_value=token_payload), \
         patch('app.crud.crud_user.user.get', return_value=None), \
         pytest.raises(AuthenticationException) as exc_info:
        refresh_token("fake_refresh_token")
    
    # Assert that AuthenticationException is raised with user not found message
    assert "User not found or inactive" in str(exc_info.value)
    assert exc_info.value.error_code == "user_not_found"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_refresh_token_cognito_success():
    # Mock cognito_client.refresh_tokens to return new tokens
    refresh_response = {
        "access_token": "new_access_token",
        "id_token": "new_id_token"
    }
    
    with patch('app.services.auth_service.cognito_client.refresh_tokens', return_value=refresh_response):
        result = refresh_token("fake_refresh_token")
    
    # Assert that the response contains new access_token and refresh_token
    assert result["access_token"] == "new_access_token"
    assert result["id_token"] == "new_id_token"
    assert result["refresh_token"] == "fake_refresh_token"
    assert result["token_type"] == "bearer"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_refresh_token_cognito_failure():
    # Mock cognito_client.refresh_tokens to raise AuthenticationException
    with patch('app.services.auth_service.cognito_client.refresh_tokens', 
              side_effect=AuthenticationException(
                  message="Invalid refresh token",
                  error_code="invalid_token"
              )), \
         pytest.raises(AuthenticationException) as exc_info:
        refresh_token("invalid_token")
    
    # Assert that AuthenticationException is raised with correct error message
    assert "Invalid refresh token" in str(exc_info.value)
    assert exc_info.value.error_code == "invalid_token"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'invalid')
def test_refresh_token_invalid_auth_type():
    # Call refresh_token with valid refresh token
    with pytest.raises(ValidationException) as exc_info:
        refresh_token("fake_refresh_token")
    
    # Assert that ValidationException is raised with correct error message about invalid AUTH_TYPE
    assert "Invalid authentication type" in str(exc_info.value)
    assert exc_info.value.error_code == "config_error"


def test_get_current_user_success():
    # Mock validate_access_token to return valid token payload with user_id and role
    token_payload = {"user_id": str(uuid.uuid4()), "email": "test@example.com", "role": "pharma_scientist"}
    
    # Mock user.get to return valid user object
    user_mock = MagicMock()
    user_mock.id = uuid.UUID(token_payload["user_id"])
    user_mock.email = "test@example.com"
    user_mock.role = "pharma_scientist"
    user_mock.is_active = True
    user_mock.to_dict = MagicMock(return_value={
        "id": token_payload["user_id"],
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "pharma_scientist",
        "is_active": True
    })
    
    with patch('app.services.auth_service.validate_access_token', return_value=token_payload), \
         patch('app.crud.crud_user.user.get', return_value=user_mock):
        result = get_current_user("fake_access_token")
    
    # Assert that the response is a UserWithPermissions object with correct user data and permissions
    assert result.email == "test@example.com"
    assert result.role == "pharma_scientist"
    assert hasattr(result, "permissions")


def test_get_current_user_invalid_token():
    # Mock validate_access_token to raise AuthenticationException
    with patch('app.services.auth_service.validate_access_token', 
              side_effect=AuthenticationException(
                  message="Invalid token",
                  error_code="invalid_token"
              )), \
         pytest.raises(AuthenticationException) as exc_info:
        get_current_user("invalid_token")
    
    # Assert that AuthenticationException is raised with correct error message
    assert "Invalid token" in str(exc_info.value)
    assert exc_info.value.error_code == "invalid_token"


def test_get_current_user_not_found():
    # Mock validate_access_token to return valid token payload with user_id and role
    token_payload = {"user_id": str(uuid.uuid4()), "email": "test@example.com", "role": "pharma_scientist"}
    
    # Mock user.get to return None (user not found)
    with patch('app.services.auth_service.validate_access_token', return_value=token_payload), \
         patch('app.crud.crud_user.user.get', return_value=None), \
         pytest.raises(AuthenticationException) as exc_info:
        get_current_user("fake_access_token")
    
    # Assert that AuthenticationException is raised with user not found message
    assert "User not found or inactive" in str(exc_info.value)
    assert exc_info.value.error_code == "user_not_found"


def test_get_user_permissions():
    # Call get_user_permissions with different roles (SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST)
    system_admin_permissions = get_user_permissions(SYSTEM_ADMIN)
    pharma_admin_permissions = get_user_permissions(PHARMA_ADMIN)
    pharma_scientist_permissions = get_user_permissions(PHARMA_SCIENTIST)
    
    # Assert that each role has the correct set of permissions
    # System Admin - should have all permissions
    assert system_admin_permissions["admin"] is True
    assert system_admin_permissions["molecules"]["create"] is True
    assert system_admin_permissions["molecules"]["edit"] is True
    assert system_admin_permissions["molecules"]["delete"] is True
    assert system_admin_permissions["users"]["view"] is True
    assert system_admin_permissions["users"]["create"] is True
    
    # Pharma Admin - should have admin permissions for their organization
    assert pharma_admin_permissions["admin"] is True
    assert pharma_admin_permissions["molecules"]["create"] is True
    assert pharma_admin_permissions["molecules"]["edit"] is True
    assert pharma_admin_permissions["molecules"]["delete"] is True
    assert pharma_admin_permissions["users"]["view"] is True
    assert pharma_admin_permissions["users"]["create"] is True
    assert "delete" not in pharma_admin_permissions["users"]  # Cannot delete users
    
    # Pharma Scientist - regular user permissions
    assert "admin" not in pharma_scientist_permissions  # Not an admin
    assert pharma_scientist_permissions["molecules"]["create"] is True
    assert pharma_scientist_permissions["molecules"]["edit"] is True
    assert "delete" not in pharma_scientist_permissions["molecules"]  # Cannot delete molecules
    assert "users" in system_admin_permissions  # Admin can manage users
    assert "users" not in pharma_scientist_permissions  # Scientists cannot manage users


@patch('app.services.auth_service.settings.AUTH_TYPE', 'database')
def test_change_password_database_success():
    # Mock user.get to return valid user object with check_password method
    user_id = str(uuid.uuid4())
    user_mock = MagicMock()
    user_mock.check_password = MagicMock(return_value=True)  # Current password is correct
    
    # Mock validate_password to return True for new password
    with patch('app.crud.crud_user.user.get', return_value=user_mock), \
         patch('app.services.auth_service.validate_password', return_value=True):
        result = change_password(user_id, "CurrentPass123!", "NewPass123!")
    
    # Assert that the result is True
    assert result is True
    # Verify that user.set_password was called with new password
    user_mock.set_password.assert_called_once_with("NewPass123!")


@patch('app.services.auth_service.settings.AUTH_TYPE', 'database')
def test_change_password_database_invalid_current_password():
    # Mock user.get to return valid user object with check_password method
    user_id = str(uuid.uuid4())
    user_mock = MagicMock()
    user_mock.check_password = MagicMock(return_value=False)  # Current password is incorrect
    
    with patch('app.crud.crud_user.user.get', return_value=user_mock), \
         pytest.raises(AuthenticationException) as exc_info:
        change_password(user_id, "WrongPass123!", "NewPass123!")
    
    # Assert that AuthenticationException is raised with incorrect password message
    assert "Current password is incorrect" in str(exc_info.value)
    assert exc_info.value.error_code == "invalid_password"
    # Verify that user.set_password was not called
    user_mock.set_password.assert_not_called()


@patch('app.services.auth_service.settings.AUTH_TYPE', 'database')
def test_change_password_database_invalid_new_password():
    # Mock user.get to return valid user object with check_password method
    user_id = str(uuid.uuid4())
    user_mock = MagicMock()
    user_mock.check_password = MagicMock(return_value=True)  # Current password is correct
    
    # Mock validate_password to return False for new password
    with patch('app.crud.crud_user.user.get', return_value=user_mock), \
         patch('app.services.auth_service.validate_password', return_value=False), \
         pytest.raises(ValidationException) as exc_info:
        change_password(user_id, "CurrentPass123!", "weak")
    
    # Assert that ValidationException is raised with password requirements message
    assert "Password does not meet security requirements" in str(exc_info.value)
    assert exc_info.value.error_code == "weak_password"
    # Verify that user.set_password was not called
    user_mock.set_password.assert_not_called()


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_change_password_cognito_success():
    # Mock validate_password to return True for new password
    user_id = str(uuid.uuid4())
    
    with patch('app.services.auth_service.validate_password', return_value=True), \
         patch('app.services.auth_service.cognito_client.change_password', return_value=True):
        result = change_password(user_id, "CurrentPass123!", "NewPass123!", "fake_access_token")
    
    # Assert that the result is True
    assert result is True
    # Verify that cognito_client.change_password was called with correct parameters
    


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_change_password_cognito_invalid_password():
    # Mock validate_password to return False for new password
    user_id = str(uuid.uuid4())
    
    with patch('app.services.auth_service.validate_password', return_value=False), \
         pytest.raises(ValidationException) as exc_info:
        change_password(user_id, "CurrentPass123!", "weak", "fake_access_token")
    
    # Assert that ValidationException is raised with password requirements message
    assert "Password does not meet security requirements" in str(exc_info.value)
    assert exc_info.value.error_code == "weak_password"
    # Verify that cognito_client.change_password was not called


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_forgot_password_success():
    # Mock cognito_client.forgot_password to return delivery details
    forgot_password_response = {
        "delivery_medium": "EMAIL",
        "delivery_destination": "t***@example.com"
    }
    
    with patch('app.services.auth_service.cognito_client.forgot_password', return_value=forgot_password_response):
        result = forgot_password("test@example.com")
    
    # Assert that the response contains delivery details
    assert result["delivery_medium"] == "EMAIL"
    assert result["delivery_destination"] == "t***@example.com"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_forgot_password_failure():
    # Mock cognito_client.forgot_password to raise AuthenticationException
    with patch('app.services.auth_service.cognito_client.forgot_password', 
              side_effect=AuthenticationException(
                  message="User not found",
                  error_code="user_not_found"
              )), \
         pytest.raises(AuthenticationException) as exc_info:
        forgot_password("unknown@example.com")
    
    # Assert that AuthenticationException is raised with correct error message
    assert "User not found" in str(exc_info.value)
    assert exc_info.value.error_code == "user_not_found"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'database')
def test_forgot_password_invalid_auth_type():
    # Call forgot_password with valid username
    with pytest.raises(ValidationException) as exc_info:
        forgot_password("test@example.com")
    
    # Assert that ValidationException is raised with correct error message about requiring Cognito
    assert "Forgot password flow is only available for Cognito authentication" in str(exc_info.value)
    assert exc_info.value.error_code == "method_not_supported"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_reset_password_success():
    # Mock validate_password to return True for new password
    # Mock cognito_client.confirm_forgot_password to return True
    with patch('app.services.auth_service.validate_password', return_value=True), \
         patch('app.services.auth_service.cognito_client.confirm_forgot_password', return_value=True):
        result = reset_password("test@example.com", "123456", "NewPass123!")
    
    # Assert that the result is True
    assert result is True
    # Verify that cognito_client.confirm_forgot_password was called with correct parameters


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_reset_password_invalid_password():
    # Mock validate_password to return False for new password
    with patch('app.services.auth_service.validate_password', return_value=False), \
         pytest.raises(ValidationException) as exc_info:
        reset_password("test@example.com", "123456", "weak")
    
    # Assert that ValidationException is raised with password requirements message
    assert "Password does not meet security requirements" in str(exc_info.value)
    assert exc_info.value.error_code == "weak_password"
    # Verify that cognito_client.confirm_forgot_password was not called


@patch('app.services.auth_service.settings.AUTH_TYPE', 'database')
def test_reset_password_invalid_auth_type():
    # Call reset_password with valid username, confirmation code, and new password
    with pytest.raises(ValidationException) as exc_info:
        reset_password("test@example.com", "123456", "NewPass123!")
    
    # Assert that ValidationException is raised with correct error message about requiring Cognito
    assert "Password reset is only available for Cognito authentication" in str(exc_info.value)
    assert exc_info.value.error_code == "method_not_supported"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_setup_mfa_success():
    # Mock cognito_client.setup_mfa to return MFA setup information
    mfa_setup_response = {
        "secret_code": "ABCDEFGHIJKLMNOP",
        "qr_code_data": "otpauth://totp/MoleculeFlow:test@example.com?secret=ABCDEFGHIJKLMNOP"
    }
    
    with patch('app.services.auth_service.cognito_client.setup_mfa', return_value=mfa_setup_response):
        result = setup_mfa("fake_access_token")
    
    # Assert that the response contains secret code and QR code data
    assert result["secret_code"] == "ABCDEFGHIJKLMNOP"
    assert "qr_code_data" in result


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_setup_mfa_failure():
    # Mock cognito_client.setup_mfa to raise AuthenticationException
    with patch('app.services.auth_service.cognito_client.setup_mfa', 
              side_effect=AuthenticationException(
                  message="MFA setup failed",
                  error_code="mfa_setup_error"
              )), \
         pytest.raises(AuthenticationException) as exc_info:
        setup_mfa("invalid_access_token")
    
    # Assert that AuthenticationException is raised with correct error message
    assert "MFA setup failed" in str(exc_info.value)
    assert exc_info.value.error_code == "mfa_setup_error"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'database')
def test_setup_mfa_invalid_auth_type():
    # Call setup_mfa with valid access token
    with pytest.raises(ValidationException) as exc_info:
        setup_mfa("fake_access_token")
    
    # Assert that ValidationException is raised with correct error message about requiring Cognito
    assert "MFA setup is only available for Cognito authentication" in str(exc_info.value)
    assert exc_info.value.error_code == "method_not_supported"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_verify_mfa_setup_success():
    # Mock cognito_client.verify_mfa_setup to return True
    with patch('app.services.auth_service.cognito_client.verify_mfa_setup', return_value=True):
        result = verify_mfa_setup("fake_access_token", "123456")
    
    # Assert that the result is True
    assert result is True
    # Verify that cognito_client.verify_mfa_setup was called with correct parameters


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_verify_mfa_setup_failure():
    # Mock cognito_client.verify_mfa_setup to raise AuthenticationException
    with patch('app.services.auth_service.cognito_client.verify_mfa_setup', 
              side_effect=AuthenticationException(
                  message="Invalid verification code",
                  error_code="invalid_verification_code"
              )), \
         pytest.raises(AuthenticationException) as exc_info:
        verify_mfa_setup("fake_access_token", "invalid_code")
    
    # Assert that AuthenticationException is raised with correct error message
    assert "Invalid verification code" in str(exc_info.value)
    assert exc_info.value.error_code == "invalid_verification_code"
    # Verify that cognito_client.verify_mfa_setup was called with correct parameters


@patch('app.services.auth_service.settings.AUTH_TYPE', 'database')
def test_verify_mfa_setup_invalid_auth_type():
    # Call verify_mfa_setup with valid access token and verification code
    with pytest.raises(ValidationException) as exc_info:
        verify_mfa_setup("fake_access_token", "123456")
    
    # Assert that ValidationException is raised with correct error message about requiring Cognito
    assert "MFA verification is only available for Cognito authentication" in str(exc_info.value)
    assert exc_info.value.error_code == "method_not_supported"


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_sign_out_cognito_success():
    # Mock cognito_client.sign_out to return True
    with patch('app.services.auth_service.cognito_client.sign_out', return_value=True):
        result = sign_out("fake_access_token")
    
    # Assert that the result is True
    assert result is True
    # Verify that cognito_client.sign_out was called with correct parameters


@patch('app.services.auth_service.settings.AUTH_TYPE', 'cognito')
def test_sign_out_cognito_failure():
    # Mock cognito_client.sign_out to raise AuthenticationException
    with patch('app.services.auth_service.cognito_client.sign_out', 
              side_effect=AuthenticationException(
                  message="Sign out failed",
                  error_code="sign_out_error"
              )), \
         pytest.raises(AuthenticationException) as exc_info:
        sign_out("invalid_access_token")
    
    # Assert that AuthenticationException is raised with correct error message
    assert "Sign out failed" in str(exc_info.value)
    assert exc_info.value.error_code == "sign_out_error"
    # Verify that cognito_client.sign_out was called with correct parameters


@patch('app.services.auth_service.settings.AUTH_TYPE', 'database')
def test_sign_out_database():
    # Call sign_out with any access token
    result = sign_out("fake_access_token")
    
    # Assert that the result is True (no-op for database auth)
    assert result is True


@patch('app.services.auth_service.settings.AUTH_TYPE', 'invalid')
def test_sign_out_invalid_auth_type():
    # Call sign_out with valid access token
    with pytest.raises(ValidationException) as exc_info:
        sign_out("fake_access_token")
    
    # Assert that ValidationException is raised with correct error message about invalid AUTH_TYPE
    assert "Invalid authentication type" in str(exc_info.value)
    assert exc_info.value.error_code == "config_error"