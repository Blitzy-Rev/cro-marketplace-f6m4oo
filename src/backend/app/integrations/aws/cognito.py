"""
AWS Cognito Integration Module for the Molecular Data Management and CRO Integration Platform.

This module provides a high-level interface for user authentication, registration, and token 
management using Amazon Cognito service. It implements functionality for user registration, 
authentication, token refresh, and MFA setup required by the Molecular Data Management 
and CRO Integration Platform.
"""

import json
import base64
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional, List

from ...core.config import settings, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
from ...core.logging import get_logger
from ...core.exceptions import IntegrationException, AuthenticationException
from ...constants.error_messages import INTEGRATION_ERRORS, AUTH_ERRORS
from ...core.security import validate_role
from ...constants.user_roles import DEFAULT_ROLE

# Set up logging
logger = get_logger(__name__)

# Global configuration variables
COGNITO_USER_POOL_ID = None  # Set during initialization
COGNITO_CLIENT_ID = None  # Set during initialization
COGNITO_CLIENT_SECRET = None  # Set during initialization


def register_user(username: str, email: str, password: str, role: Optional[str] = None, 
                  attributes: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Register a new user in Cognito user pool.
    
    Args:
        username: User's username
        email: User's email address
        password: User's password
        role: User's role (defaults to DEFAULT_ROLE if not provided)
        attributes: Additional user attributes
        
    Returns:
        User registration response with user attributes
        
    Raises:
        AuthenticationException: If registration fails
    """
    # Validate role if provided
    if role:
        if not validate_role(role):
            raise AuthenticationException(
                message=f"Invalid role: {role}",
                error_code="invalid_role"
            )
    else:
        role = DEFAULT_ROLE
    
    # Create Cognito client
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        # Prepare user attributes
        user_attributes = [
            {'Name': 'email', 'Value': email},
            {'Name': 'email_verified', 'Value': 'true'},
            {'Name': 'custom:role', 'Value': role}
        ]
        
        # Add any additional attributes
        if attributes:
            for key, value in attributes.items():
                if key not in ['email', 'email_verified', 'custom:role']:
                    user_attributes.append({'Name': key, 'Value': value})
        
        logger.info(f"Registering new user: {username}, email: {email}")
        
        # Call Cognito API to create user
        response = cognito_client.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=COGNITO_CLIENT_SECRET,
            Username=username,
            Password=password,
            UserAttributes=user_attributes
        )
        
        logger.info(f"User registration successful: {username}")
        return response
        
    except ClientError as error:
        logger.error(f"User registration failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        if error_code == 'UsernameExistsException':
            raise AuthenticationException(
                message=AUTH_ERRORS.get('EMAIL_ALREADY_EXISTS', error_message),
                error_code="username_exists"
            )
        elif error_code == 'InvalidPasswordException':
            raise AuthenticationException(
                message=AUTH_ERRORS.get('PASSWORD_TOO_WEAK', error_message),
                error_code="invalid_password"
            )
        else:
            raise AuthenticationException(
                message=f"Registration failed: {error_message}",
                error_code=error_code.lower()
            )
    except Exception as error:
        logger.error(f"Unexpected error during user registration: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="registration_error"
        )


def confirm_registration(username: str, confirmation_code: str) -> bool:
    """
    Confirm user registration with verification code.
    
    Args:
        username: User's username
        confirmation_code: Verification code sent to user's email
        
    Returns:
        True if confirmation was successful
        
    Raises:
        AuthenticationException: If confirmation fails
    """
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info(f"Confirming registration for user: {username}")
        
        # Call Cognito API to confirm sign-up
        cognito_client.confirm_sign_up(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=COGNITO_CLIENT_SECRET,
            Username=username,
            ConfirmationCode=confirmation_code
        )
        
        logger.info(f"Registration confirmed for user: {username}")
        return True
        
    except ClientError as error:
        logger.error(f"Registration confirmation failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        raise AuthenticationException(
            message=f"Registration confirmation failed: {error_message}",
            error_code=error_code.lower()
        )
    except Exception as error:
        logger.error(f"Unexpected error during registration confirmation: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="confirmation_error"
        )


def initiate_auth(username: str, password: str) -> Dict[str, Any]:
    """
    Initiate authentication flow with username and password.
    
    Args:
        username: User's username
        password: User's password
        
    Returns:
        Authentication response with tokens or challenge details
        
    Raises:
        AuthenticationException: If authentication fails
    """
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info(f"Initiating authentication for user: {username}")
        
        # Call Cognito API to initiate auth
        response = cognito_client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password,
                'SECRET_HASH': COGNITO_CLIENT_SECRET
            }
        )
        
        # Check for authentication challenges
        if 'ChallengeName' in response:
            challenge_name = response['ChallengeName']
            logger.info(f"Authentication challenge required: {challenge_name} for user: {username}")
            
            # Handle specific challenges
            if challenge_name == 'NEW_PASSWORD_REQUIRED':
                return {
                    'challenge': 'NEW_PASSWORD_REQUIRED',
                    'session': response.get('Session'),
                    'user_attributes': response.get('ChallengeParameters', {})
                }
            elif challenge_name == 'MFA_SETUP':
                return {
                    'challenge': 'MFA_SETUP',
                    'session': response.get('Session')
                }
            elif challenge_name == 'SOFTWARE_TOKEN_MFA':
                return {
                    'challenge': 'SOFTWARE_TOKEN_MFA',
                    'session': response.get('Session')
                }
            else:
                return {
                    'challenge': challenge_name,
                    'session': response.get('Session'),
                    'challenge_parameters': response.get('ChallengeParameters', {})
                }
        
        # Authentication successful
        logger.info(f"Authentication successful for user: {username}")
        return {
            'tokens': response.get('AuthenticationResult', {}),
            'access_token': response.get('AuthenticationResult', {}).get('AccessToken'),
            'id_token': response.get('AuthenticationResult', {}).get('IdToken'),
            'refresh_token': response.get('AuthenticationResult', {}).get('RefreshToken'),
            'expires_in': response.get('AuthenticationResult', {}).get('ExpiresIn')
        }
        
    except ClientError as error:
        logger.error(f"Authentication failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        if error_code == 'NotAuthorizedException':
            raise AuthenticationException(
                message=AUTH_ERRORS.get('INVALID_CREDENTIALS', error_message),
                error_code="invalid_credentials"
            )
        elif error_code == 'UserNotFoundException':
            raise AuthenticationException(
                message=AUTH_ERRORS.get('INVALID_CREDENTIALS', error_message),
                error_code="invalid_credentials"
            )
        elif error_code == 'UserNotConfirmedException':
            raise AuthenticationException(
                message="User is not confirmed",
                error_code="user_not_confirmed"
            )
        else:
            raise AuthenticationException(
                message=f"Authentication failed: {error_message}",
                error_code=error_code.lower()
            )
    except Exception as error:
        logger.error(f"Unexpected error during authentication: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="authentication_error"
        )


def refresh_tokens(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh authentication tokens using a refresh token.
    
    Args:
        refresh_token: Valid refresh token
        
    Returns:
        Authentication response with new tokens
        
    Raises:
        AuthenticationException: If token refresh fails
    """
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info("Refreshing authentication tokens")
        
        # Call Cognito API to refresh tokens
        response = cognito_client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refresh_token,
                'SECRET_HASH': COGNITO_CLIENT_SECRET
            }
        )
        
        logger.info("Token refresh successful")
        return {
            'tokens': response.get('AuthenticationResult', {}),
            'access_token': response.get('AuthenticationResult', {}).get('AccessToken'),
            'id_token': response.get('AuthenticationResult', {}).get('IdToken'),
            'expires_in': response.get('AuthenticationResult', {}).get('ExpiresIn')
        }
        
    except ClientError as error:
        logger.error(f"Token refresh failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        if error_code == 'NotAuthorizedException':
            raise AuthenticationException(
                message=AUTH_ERRORS.get('INVALID_TOKEN', error_message),
                error_code="invalid_token"
            )
        else:
            raise AuthenticationException(
                message=f"Token refresh failed: {error_message}",
                error_code=error_code.lower()
            )
    except Exception as error:
        logger.error(f"Unexpected error during token refresh: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="token_refresh_error"
        )


def respond_to_auth_challenge(username: str, challenge_name: str, 
                              challenge_responses: Dict[str, str],
                              session: Optional[str] = None) -> Dict[str, Any]:
    """
    Respond to an authentication challenge.
    
    Args:
        username: User's username
        challenge_name: Name of the challenge to respond to
        challenge_responses: Responses to the challenge
        session: Session from the previous challenge
        
    Returns:
        Challenge response with tokens or next challenge
        
    Raises:
        AuthenticationException: If challenge response fails
    """
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info(f"Responding to auth challenge: {challenge_name} for user: {username}")
        
        # Prepare challenge responses
        response_params = challenge_responses.copy()
        response_params['USERNAME'] = username
        response_params['SECRET_HASH'] = COGNITO_CLIENT_SECRET
        
        # Call Cognito API to respond to challenge
        response = cognito_client.respond_to_auth_challenge(
            ClientId=COGNITO_CLIENT_ID,
            ChallengeName=challenge_name,
            Session=session,
            ChallengeResponses=response_params
        )
        
        # Check for additional challenges
        if 'ChallengeName' in response:
            next_challenge = response['ChallengeName']
            logger.info(f"Additional challenge required: {next_challenge}")
            
            return {
                'challenge': next_challenge,
                'session': response.get('Session'),
                'challenge_parameters': response.get('ChallengeParameters', {})
            }
        
        # Challenge completed successfully
        logger.info(f"Auth challenge completed for user: {username}")
        return {
            'tokens': response.get('AuthenticationResult', {}),
            'access_token': response.get('AuthenticationResult', {}).get('AccessToken'),
            'id_token': response.get('AuthenticationResult', {}).get('IdToken'),
            'refresh_token': response.get('AuthenticationResult', {}).get('RefreshToken'),
            'expires_in': response.get('AuthenticationResult', {}).get('ExpiresIn')
        }
        
    except ClientError as error:
        logger.error(f"Challenge response failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        raise AuthenticationException(
            message=f"Challenge response failed: {error_message}",
            error_code=error_code.lower()
        )
    except Exception as error:
        logger.error(f"Unexpected error during challenge response: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="challenge_response_error"
        )


def forgot_password(username: str) -> Dict[str, Any]:
    """
    Initiate forgot password flow.
    
    Args:
        username: User's username
        
    Returns:
        Forgot password response with delivery details
        
    Raises:
        AuthenticationException: If forgot password request fails
    """
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info(f"Initiating forgot password flow for user: {username}")
        
        # Call Cognito API to initiate forgot password
        response = cognito_client.forgot_password(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=COGNITO_CLIENT_SECRET,
            Username=username
        )
        
        logger.info(f"Forgot password initiated for user: {username}")
        return {
            'delivery_medium': response.get('CodeDeliveryDetails', {}).get('DeliveryMedium'),
            'delivery_destination': response.get('CodeDeliveryDetails', {}).get('Destination')
        }
        
    except ClientError as error:
        logger.error(f"Forgot password request failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        if error_code == 'UserNotFoundException':
            # Don't reveal user existence for security reasons
            raise AuthenticationException(
                message="If your account exists, a reset code has been sent",
                error_code="password_reset_initiated"
            )
        else:
            raise AuthenticationException(
                message=f"Forgot password request failed: {error_message}",
                error_code=error_code.lower()
            )
    except Exception as error:
        logger.error(f"Unexpected error during forgot password request: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="forgot_password_error"
        )


def confirm_forgot_password(username: str, confirmation_code: str, new_password: str) -> bool:
    """
    Complete forgot password flow with verification code and new password.
    
    Args:
        username: User's username
        confirmation_code: Verification code sent to user's email
        new_password: New password to set
        
    Returns:
        True if password reset was successful
        
    Raises:
        AuthenticationException: If password reset fails
    """
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info(f"Confirming password reset for user: {username}")
        
        # Call Cognito API to confirm forgot password
        cognito_client.confirm_forgot_password(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=COGNITO_CLIENT_SECRET,
            Username=username,
            ConfirmationCode=confirmation_code,
            Password=new_password
        )
        
        logger.info(f"Password reset confirmed for user: {username}")
        return True
        
    except ClientError as error:
        logger.error(f"Password reset confirmation failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        if error_code == 'CodeMismatchException':
            raise AuthenticationException(
                message="Invalid verification code",
                error_code="invalid_code"
            )
        elif error_code == 'InvalidPasswordException':
            raise AuthenticationException(
                message=AUTH_ERRORS.get('PASSWORD_TOO_WEAK', error_message),
                error_code="invalid_password"
            )
        else:
            raise AuthenticationException(
                message=f"Password reset confirmation failed: {error_message}",
                error_code=error_code.lower()
            )
    except Exception as error:
        logger.error(f"Unexpected error during password reset confirmation: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="password_reset_error"
        )


def change_password(access_token: str, previous_password: str, new_password: str) -> bool:
    """
    Change user password.
    
    Args:
        access_token: Valid access token
        previous_password: Current password
        new_password: New password to set
        
    Returns:
        True if password change was successful
        
    Raises:
        AuthenticationException: If password change fails
    """
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info("Changing user password")
        
        # Call Cognito API to change password
        cognito_client.change_password(
            AccessToken=access_token,
            PreviousPassword=previous_password,
            ProposedPassword=new_password
        )
        
        logger.info("Password change successful")
        return True
        
    except ClientError as error:
        logger.error(f"Password change failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        if error_code == 'InvalidPasswordException':
            raise AuthenticationException(
                message=AUTH_ERRORS.get('PASSWORD_TOO_WEAK', error_message),
                error_code="invalid_password"
            )
        elif error_code == 'NotAuthorizedException':
            raise AuthenticationException(
                message="Incorrect previous password",
                error_code="invalid_previous_password"
            )
        else:
            raise AuthenticationException(
                message=f"Password change failed: {error_message}",
                error_code=error_code.lower()
            )
    except Exception as error:
        logger.error(f"Unexpected error during password change: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="password_change_error"
        )


def get_user(access_token: str) -> Dict[str, Any]:
    """
    Get user attributes using access token.
    
    Args:
        access_token: Valid access token
        
    Returns:
        User attributes
        
    Raises:
        AuthenticationException: If user retrieval fails
    """
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info("Getting user attributes")
        
        # Call Cognito API to get user
        response = cognito_client.get_user(
            AccessToken=access_token
        )
        
        # Format user attributes into a dictionary
        user_attributes = {}
        for attr in response.get('UserAttributes', []):
            user_attributes[attr['Name']] = attr['Value']
        
        logger.info(f"User attributes retrieved for: {response.get('Username')}")
        return {
            'username': response.get('Username'),
            'attributes': user_attributes
        }
        
    except ClientError as error:
        logger.error(f"User retrieval failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        if error_code == 'NotAuthorizedException':
            raise AuthenticationException(
                message=AUTH_ERRORS.get('INVALID_TOKEN', error_message),
                error_code="invalid_token"
            )
        else:
            raise AuthenticationException(
                message=f"User retrieval failed: {error_message}",
                error_code=error_code.lower()
            )
    except Exception as error:
        logger.error(f"Unexpected error during user retrieval: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="user_retrieval_error"
        )


def admin_get_user(username: str) -> Dict[str, Any]:
    """
    Get user attributes as admin.
    
    Args:
        username: User's username
        
    Returns:
        User attributes
        
    Raises:
        AuthenticationException: If user retrieval fails
    """
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info(f"Getting user attributes as admin for: {username}")
        
        # Call Cognito API to get user as admin
        response = cognito_client.admin_get_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=username
        )
        
        # Format user attributes into a dictionary
        user_attributes = {}
        for attr in response.get('UserAttributes', []):
            user_attributes[attr['Name']] = attr['Value']
        
        logger.info(f"User attributes retrieved for: {username}")
        return {
            'username': username,
            'user_status': response.get('UserStatus'),
            'enabled': response.get('Enabled', True),
            'user_create_date': response.get('UserCreateDate'),
            'user_last_modified_date': response.get('UserLastModifiedDate'),
            'attributes': user_attributes
        }
        
    except ClientError as error:
        logger.error(f"Admin user retrieval failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        if error_code == 'UserNotFoundException':
            raise AuthenticationException(
                message="User not found",
                error_code="user_not_found"
            )
        else:
            raise AuthenticationException(
                message=f"Admin user retrieval failed: {error_message}",
                error_code=error_code.lower()
            )
    except Exception as error:
        logger.error(f"Unexpected error during admin user retrieval: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="admin_user_retrieval_error"
        )


def admin_update_user_attributes(username: str, attributes: Dict[str, str]) -> bool:
    """
    Update user attributes as admin.
    
    Args:
        username: User's username
        attributes: User attributes to update
        
    Returns:
        True if update was successful
        
    Raises:
        AuthenticationException: If attribute update fails
    """
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info(f"Updating user attributes as admin for: {username}")
        
        # Format attributes for Cognito API
        user_attributes = [
            {'Name': key, 'Value': value} for key, value in attributes.items()
        ]
        
        # Call Cognito API to update user attributes
        cognito_client.admin_update_user_attributes(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=username,
            UserAttributes=user_attributes
        )
        
        logger.info(f"User attributes updated for: {username}")
        return True
        
    except ClientError as error:
        logger.error(f"Admin attribute update failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        if error_code == 'UserNotFoundException':
            raise AuthenticationException(
                message="User not found",
                error_code="user_not_found"
            )
        else:
            raise AuthenticationException(
                message=f"Admin attribute update failed: {error_message}",
                error_code=error_code.lower()
            )
    except Exception as error:
        logger.error(f"Unexpected error during admin attribute update: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="admin_attribute_update_error"
        )


def admin_disable_user(username: str) -> bool:
    """
    Disable a user account as admin.
    
    Args:
        username: User's username
        
    Returns:
        True if disabling was successful
        
    Raises:
        AuthenticationException: If disabling fails
    """
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info(f"Disabling user as admin: {username}")
        
        # Call Cognito API to disable user
        cognito_client.admin_disable_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=username
        )
        
        logger.info(f"User disabled: {username}")
        return True
        
    except ClientError as error:
        logger.error(f"Admin disable user failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        if error_code == 'UserNotFoundException':
            raise AuthenticationException(
                message="User not found",
                error_code="user_not_found"
            )
        else:
            raise AuthenticationException(
                message=f"Admin disable user failed: {error_message}",
                error_code=error_code.lower()
            )
    except Exception as error:
        logger.error(f"Unexpected error during admin disable user: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="admin_disable_user_error"
        )


def admin_enable_user(username: str) -> bool:
    """
    Enable a user account as admin.
    
    Args:
        username: User's username
        
    Returns:
        True if enabling was successful
        
    Raises:
        AuthenticationException: If enabling fails
    """
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info(f"Enabling user as admin: {username}")
        
        # Call Cognito API to enable user
        cognito_client.admin_enable_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=username
        )
        
        logger.info(f"User enabled: {username}")
        return True
        
    except ClientError as error:
        logger.error(f"Admin enable user failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        if error_code == 'UserNotFoundException':
            raise AuthenticationException(
                message="User not found",
                error_code="user_not_found"
            )
        else:
            raise AuthenticationException(
                message=f"Admin enable user failed: {error_message}",
                error_code=error_code.lower()
            )
    except Exception as error:
        logger.error(f"Unexpected error during admin enable user: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="admin_enable_user_error"
        )


def setup_mfa(access_token: str) -> Dict[str, Any]:
    """
    Set up MFA for a user.
    
    Args:
        access_token: Valid access token
        
    Returns:
        MFA setup information including secret code and QR code
        
    Raises:
        AuthenticationException: If MFA setup fails
    """
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info("Setting up MFA")
        
        # Call Cognito API to associate software token
        response = cognito_client.associate_software_token(
            AccessToken=access_token
        )
        
        # Decode the secret code and generate QR code data
        secret_code = response.get('SecretCode')
        
        # Get user info to include in QR code
        user_info = get_user(access_token)
        username = user_info.get('username')
        
        # Create data for QR code (otpauth URL)
        qr_code_data = f"otpauth://totp/{settings.PROJECT_NAME}:{username}?secret={secret_code}&issuer={settings.PROJECT_NAME}"
        
        logger.info("MFA setup initiated")
        return {
            'secret_code': secret_code,
            'qr_code_data': qr_code_data
        }
        
    except ClientError as error:
        logger.error(f"MFA setup failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        raise AuthenticationException(
            message=f"MFA setup failed: {error_message}",
            error_code=error_code.lower()
        )
    except Exception as error:
        logger.error(f"Unexpected error during MFA setup: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="mfa_setup_error"
        )


def verify_mfa_setup(access_token: str, verification_code: str) -> bool:
    """
    Verify MFA setup with a verification code.
    
    Args:
        access_token: Valid access token
        verification_code: TOTP verification code
        
    Returns:
        True if verification was successful
        
    Raises:
        AuthenticationException: If MFA verification fails
    """
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info("Verifying MFA setup")
        
        # Call Cognito API to verify software token
        response = cognito_client.verify_software_token(
            AccessToken=access_token,
            UserCode=verification_code
        )
        
        status = response.get('Status')
        
        if status == 'SUCCESS':
            logger.info("MFA verification successful")
            return True
        else:
            logger.warning(f"MFA verification returned status: {status}")
            raise AuthenticationException(
                message=f"MFA verification failed with status: {status}",
                error_code="mfa_verification_failed"
            )
        
    except ClientError as error:
        logger.error(f"MFA verification failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        if error_code == 'EnableSoftwareTokenMFAException':
            raise AuthenticationException(
                message="Invalid verification code",
                error_code="invalid_verification_code"
            )
        else:
            raise AuthenticationException(
                message=f"MFA verification failed: {error_message}",
                error_code=error_code.lower()
            )
    except Exception as error:
        logger.error(f"Unexpected error during MFA verification: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="mfa_verification_error"
        )


def set_preferred_mfa(access_token: str, mfa_type: str) -> bool:
    """
    Set preferred MFA method for a user.
    
    Args:
        access_token: Valid access token
        mfa_type: MFA type ('SOFTWARE_TOKEN_MFA' or 'NOMFA')
        
    Returns:
        True if setting preferred MFA was successful
        
    Raises:
        AuthenticationException: If setting preferred MFA fails
    """
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info(f"Setting preferred MFA method: {mfa_type}")
        
        # Configure MFA settings based on the selected type
        software_token_mfa_settings = {
            'Enabled': mfa_type == 'SOFTWARE_TOKEN_MFA',
            'PreferredMfa': mfa_type == 'SOFTWARE_TOKEN_MFA'
        }
        
        # Call Cognito API to set MFA preference
        cognito_client.set_user_mfa_preference(
            AccessToken=access_token,
            SoftwareTokenMfaSettings=software_token_mfa_settings
        )
        
        logger.info(f"Preferred MFA method set to: {mfa_type}")
        return True
        
    except ClientError as error:
        logger.error(f"Setting preferred MFA failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        raise AuthenticationException(
            message=f"Setting preferred MFA failed: {error_message}",
            error_code=error_code.lower()
        )
    except Exception as error:
        logger.error(f"Unexpected error during setting preferred MFA: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="set_preferred_mfa_error"
        )


def global_sign_out(access_token: str) -> bool:
    """
    Sign out a user from all devices.
    
    Args:
        access_token: Valid access token
        
    Returns:
        True if sign out was successful
        
    Raises:
        AuthenticationException: If sign out fails
    """
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info("Signing out user from all devices")
        
        # Call Cognito API to sign out
        cognito_client.global_sign_out(
            AccessToken=access_token
        )
        
        logger.info("Global sign out successful")
        return True
        
    except ClientError as error:
        logger.error(f"Global sign out failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        if error_code == 'NotAuthorizedException':
            raise AuthenticationException(
                message=AUTH_ERRORS.get('INVALID_TOKEN', error_message),
                error_code="invalid_token"
            )
        else:
            raise AuthenticationException(
                message=f"Global sign out failed: {error_message}",
                error_code=error_code.lower()
            )
    except Exception as error:
        logger.error(f"Unexpected error during global sign out: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="global_sign_out_error"
        )


def admin_reset_user_password(username: str) -> bool:
    """
    Reset user password as admin.
    
    Args:
        username: User's username
        
    Returns:
        True if password reset was successful
        
    Raises:
        AuthenticationException: If password reset fails
    """
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info(f"Resetting password as admin for user: {username}")
        
        # Call Cognito API to reset password
        cognito_client.admin_reset_user_password(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=username
        )
        
        logger.info(f"Password reset initiated for user: {username}")
        return True
        
    except ClientError as error:
        logger.error(f"Admin password reset failed: {error}")
        error_code = error.response.get('Error', {}).get('Code', 'UnknownError')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        if error_code == 'UserNotFoundException':
            raise AuthenticationException(
                message="User not found",
                error_code="user_not_found"
            )
        else:
            raise AuthenticationException(
                message=f"Admin password reset failed: {error_message}",
                error_code=error_code.lower()
            )
    except Exception as error:
        logger.error(f"Unexpected error during admin password reset: {error}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS.get('EXTERNAL_API_ERROR', str(error)),
            service_name="Cognito",
            error_code="admin_password_reset_error"
        )


class CognitoClient:
    """Client class for interacting with AWS Cognito service with simplified interface and error handling."""
    
    def __init__(self, user_pool_id: str, client_id: str, client_secret: str):
        """
        Initialize Cognito client with AWS credentials from settings.
        
        Args:
            user_pool_id: Cognito user pool ID
            client_id: Cognito client ID
            client_secret: Cognito client secret
        """
        global COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET
        
        # Store configuration
        self._user_pool_id = user_pool_id
        self._client_id = client_id
        self._client_secret = client_secret
        
        # Set global variables for use in functions
        COGNITO_USER_POOL_ID = user_pool_id
        COGNITO_CLIENT_ID = client_id
        COGNITO_CLIENT_SECRET = client_secret
        
        # Initialize boto3 client
        self._client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        logger.info(f"Cognito client initialized for user pool: {user_pool_id}")
    
    def register(self, username: str, email: str, password: str, role: Optional[str] = None, 
                 attributes: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Register a new user in Cognito user pool.
        
        Args:
            username: User's username
            email: User's email address
            password: User's password
            role: User's role (defaults to DEFAULT_ROLE if not provided)
            attributes: Additional user attributes
            
        Returns:
            User registration response
        """
        return register_user(username, email, password, role, attributes)
    
    def confirm_registration(self, username: str, confirmation_code: str) -> bool:
        """
        Confirm user registration with verification code.
        
        Args:
            username: User's username
            confirmation_code: Verification code sent to user's email
            
        Returns:
            True if confirmation was successful
        """
        return confirm_registration(username, confirmation_code)
    
    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user with username and password.
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            Authentication response with tokens
        """
        return initiate_auth(username, password)
    
    def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh authentication tokens.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Authentication response with new tokens
        """
        return refresh_tokens(refresh_token)
    
    def respond_to_challenge(self, username: str, challenge_name: str, 
                           challenge_responses: Dict[str, str],
                           session: Optional[str] = None) -> Dict[str, Any]:
        """
        Respond to an authentication challenge.
        
        Args:
            username: User's username
            challenge_name: Name of the challenge to respond to
            challenge_responses: Responses to the challenge
            session: Session from the previous challenge
            
        Returns:
            Challenge response
        """
        return respond_to_auth_challenge(username, challenge_name, challenge_responses, session)
    
    def forgot_password(self, username: str) -> Dict[str, Any]:
        """
        Initiate forgot password flow.
        
        Args:
            username: User's username
            
        Returns:
            Forgot password response
        """
        return forgot_password(username)
    
    def confirm_forgot_password(self, username: str, confirmation_code: str, new_password: str) -> bool:
        """
        Complete forgot password flow.
        
        Args:
            username: User's username
            confirmation_code: Verification code sent to user's email
            new_password: New password to set
            
        Returns:
            True if password reset was successful
        """
        return confirm_forgot_password(username, confirmation_code, new_password)
    
    def change_password(self, access_token: str, previous_password: str, new_password: str) -> bool:
        """
        Change user password.
        
        Args:
            access_token: Valid access token
            previous_password: Current password
            new_password: New password to set
            
        Returns:
            True if password change was successful
        """
        return change_password(access_token, previous_password, new_password)
    
    def get_user(self, access_token: str) -> Dict[str, Any]:
        """
        Get user attributes.
        
        Args:
            access_token: Valid access token
            
        Returns:
            User attributes
        """
        return get_user(access_token)
    
    def admin_get_user(self, username: str) -> Dict[str, Any]:
        """
        Get user attributes as admin.
        
        Args:
            username: User's username
            
        Returns:
            User attributes
        """
        return admin_get_user(username)
    
    def admin_update_user_attributes(self, username: str, attributes: Dict[str, str]) -> bool:
        """
        Update user attributes as admin.
        
        Args:
            username: User's username
            attributes: User attributes to update
            
        Returns:
            True if update was successful
        """
        return admin_update_user_attributes(username, attributes)
    
    def admin_disable_user(self, username: str) -> bool:
        """
        Disable a user account as admin.
        
        Args:
            username: User's username
            
        Returns:
            True if disabling was successful
        """
        return admin_disable_user(username)
    
    def admin_enable_user(self, username: str) -> bool:
        """
        Enable a user account as admin.
        
        Args:
            username: User's username
            
        Returns:
            True if enabling was successful
        """
        return admin_enable_user(username)
    
    def setup_mfa(self, access_token: str) -> Dict[str, Any]:
        """
        Set up MFA for a user.
        
        Args:
            access_token: Valid access token
            
        Returns:
            MFA setup information
        """
        return setup_mfa(access_token)
    
    def verify_mfa_setup(self, access_token: str, verification_code: str) -> bool:
        """
        Verify MFA setup with a verification code.
        
        Args:
            access_token: Valid access token
            verification_code: TOTP verification code
            
        Returns:
            True if verification was successful
        """
        return verify_mfa_setup(access_token, verification_code)
    
    def set_preferred_mfa(self, access_token: str, mfa_type: str) -> bool:
        """
        Set preferred MFA method for a user.
        
        Args:
            access_token: Valid access token
            mfa_type: MFA type ('SOFTWARE_TOKEN_MFA' or 'NOMFA')
            
        Returns:
            True if setting preferred MFA was successful
        """
        return set_preferred_mfa(access_token, mfa_type)
    
    def sign_out(self, access_token: str) -> bool:
        """
        Sign out a user from all devices.
        
        Args:
            access_token: Valid access token
            
        Returns:
            True if sign out was successful
        """
        return global_sign_out(access_token)
    
    def admin_reset_password(self, username: str) -> bool:
        """
        Reset user password as admin.
        
        Args:
            username: User's username
            
        Returns:
            True if password reset was successful
        """
        return admin_reset_user_password(username)