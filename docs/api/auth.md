# Authentication API

This document describes the authentication endpoints for the Molecular Data Management and CRO Integration Platform API. The platform uses JWT (JSON Web Tokens) for authentication with support for token refresh and multi-factor authentication.

## Base URL

All API endpoints are relative to the base URL: `https://api.moleculeflow.com/api/v1`

## Authentication Flow

The platform supports both database authentication and AWS Cognito authentication, configurable through system settings. The authentication flow consists of the following steps:

1. User registers an account
2. User confirms registration (if using Cognito)
3. User logs in with username and password
4. System returns access and refresh tokens
5. User includes access token in subsequent API requests
6. When access token expires, user can use refresh token to obtain a new access token

For enhanced security, multi-factor authentication (MFA) can be enabled for user accounts.

## Endpoints

### Login

**POST /auth/login**

Authenticate a user and return access and refresh tokens.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Responses:**

*200 OK: Authentication successful*
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "mfa_required": false
}
```

*401 Unauthorized: Authentication failed*
```json
{
  "error_code": "INVALID_CREDENTIALS",
  "message": "Invalid username or password",
  "details": null,
  "status_code": 401
}
```

**Notes:** If MFA is enabled for the user, the response will include `mfa_required: true` and the client should prompt the user for an MFA code.

### Register

**POST /auth/register**

Register a new user in the system.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Smith",
  "role": "pharma_scientist",
  "organization": "PharmaCo"
}
```

**Responses:**

*200 OK: Registration successful*
```json
{
  "status": "success",
  "message": "User registered successfully. Please check your email for confirmation instructions.",
  "data": {
    "email": "user@example.com",
    "requires_confirmation": true
  }
}
```

*400 Bad Request: Invalid registration data*
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid registration data",
  "details": {
    "password": "Password must be at least 12 characters long and include uppercase, lowercase, number, and special character"
  },
  "status_code": 400
}
```

**Notes:** The `role` field is optional and defaults to 'pharma_scientist'. Available roles are: system_admin, pharma_admin, pharma_scientist, cro_admin, cro_technician, auditor.

### Confirm Registration

**POST /auth/confirm-registration**

Confirm user registration with verification code (Cognito authentication only).

**Request:**
```json
{
  "username": "user@example.com",
  "confirmation_code": "123456"
}
```

**Responses:**

*200 OK: Confirmation successful*
```json
{
  "status": "success",
  "message": "User registration confirmed successfully. You can now log in.",
  "data": null
}
```

*400 Bad Request: Invalid confirmation code*
```json
{
  "error_code": "INVALID_CODE",
  "message": "Invalid confirmation code",
  "details": null,
  "status_code": 400
}
```

### Refresh Token

**POST /auth/refresh**

Refresh authentication tokens using a refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Responses:**

*200 OK: Token refresh successful*
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

*401 Unauthorized: Invalid refresh token*
```json
{
  "error_code": "INVALID_TOKEN",
  "message": "Invalid or expired refresh token",
  "details": null,
  "status_code": 401
}
```

**Notes:** Refresh tokens have a longer lifetime than access tokens. Use this endpoint to obtain a new access token without requiring the user to log in again.

### Change Password

**POST /auth/change-password**

Change the password for the authenticated user.

**Request:**
```json
{
  "current_password": "oldpassword123",
  "new_password": "newpassword456"
}
```

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

*200 OK: Password changed successfully*
```json
{
  "status": "success",
  "message": "Password changed successfully",
  "data": null
}
```

*400 Bad Request: Invalid password data*
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid password data",
  "details": {
    "current_password": "Current password is incorrect",
    "new_password": "Password must be at least 12 characters long and include uppercase, lowercase, number, and special character"
  },
  "status_code": 400
}
```

*401 Unauthorized: Unauthorized*
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

**Notes:** This endpoint requires authentication. Include the access token in the Authorization header.

### Forgot Password

**POST /auth/forgot-password**

Initiate forgot password flow (Cognito authentication only).

**Request:**
```json
{
  "username": "user@example.com"
}
```

**Responses:**

*200 OK: Forgot password initiated*
```json
{
  "status": "success",
  "message": "Password reset code sent. Check your email for instructions.",
  "data": {
    "delivery": {
      "destination": "u***@example.com",
      "delivery_medium": "EMAIL",
      "attribute_name": "email"
    }
  }
}
```

*400 Bad Request: User not found*
```json
{
  "error_code": "USER_NOT_FOUND",
  "message": "User not found",
  "details": null,
  "status_code": 400
}
```

### Reset Password

**POST /auth/reset-password**

Reset password with verification code (Cognito authentication only).

**Request:**
```json
{
  "username": "user@example.com",
  "confirmation_code": "123456",
  "new_password": "newpassword456"
}
```

**Responses:**

*200 OK: Password reset successful*
```json
{
  "status": "success",
  "message": "Password reset successfully. You can now log in with your new password.",
  "data": null
}
```

*400 Bad Request: Invalid reset request*
```json
{
  "error_code": "INVALID_REQUEST",
  "message": "Invalid reset request",
  "details": {
    "confirmation_code": "Invalid or expired confirmation code"
  },
  "status_code": 400
}
```

### Setup MFA

**POST /auth/setup-mfa**

Set up multi-factor authentication for a user (Cognito authentication only).

**Request:**
```json
{}
```

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

*200 OK: MFA setup information*
```json
{
  "secret_code": "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567",
  "qr_code_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "instructions": "Scan this QR code with your authenticator app or manually enter the secret code."
}
```

*401 Unauthorized: Unauthorized*
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

**Notes:** This endpoint requires authentication. Include the access token in the Authorization header. After setting up MFA, the user must verify the setup with a verification code.

### Verify MFA Setup

**POST /auth/verify-mfa**

Verify MFA setup with a verification code (Cognito authentication only).

**Request:**
```json
{
  "verification_code": "123456"
}
```

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

*200 OK: MFA verification successful*
```json
{
  "status": "success",
  "message": "MFA setup verified successfully. MFA is now enabled for your account.",
  "data": null
}
```

*400 Bad Request: Invalid verification code*
```json
{
  "error_code": "INVALID_CODE",
  "message": "Invalid verification code",
  "details": null,
  "status_code": 400
}
```

*401 Unauthorized: Unauthorized*
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

**Notes:** This endpoint requires authentication. Include the access token in the Authorization header.

### Sign Out

**POST /auth/sign-out**

Sign out a user from all devices.

**Request:**
```json
{}
```

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

*200 OK: Sign out successful*
```json
{
  "status": "success",
  "message": "Signed out successfully",
  "data": null
}
```

*401 Unauthorized: Unauthorized*
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

**Notes:** This endpoint requires authentication. Include the access token in the Authorization header. For Cognito authentication, this invalidates all refresh tokens for the user.

### Test Token

**POST /auth/test-token**

Test endpoint to verify token authentication.

**Request:**
```json
{}
```

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Responses:**

*200 OK: Token is valid*
```json
{
  "message": "Token is valid"
}
```

*401 Unauthorized: Unauthorized*
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Not authenticated",
  "details": null,
  "status_code": 401
}
```

**Notes:** This endpoint requires authentication. Include the access token in the Authorization header. Use this endpoint to verify that a token is still valid.

## Authentication with API Requests

To authenticate API requests, include the access token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Access tokens are valid for 15 minutes. After expiration, use the refresh token to obtain a new access token.

## Role-Based Access Control

The platform implements role-based access control with the following roles:

- `system_admin`: System administrator with full access to all features
- `pharma_admin`: Pharmaceutical company administrator with management access
- `pharma_scientist`: Pharmaceutical scientist with standard access
- `cro_admin`: CRO administrator with management access
- `cro_technician`: CRO technician with standard access
- `auditor`: Auditor with read-only access for compliance monitoring

Each role has specific permissions that determine what actions the user can perform. The role is included in the JWT token payload and used for authorization checks.

## Security Considerations

- Access tokens are short-lived (15 minutes) to minimize the risk of token theft
- Refresh tokens have a longer lifetime (7 days) but can be revoked
- Passwords must meet complexity requirements (minimum 12 characters, including uppercase, lowercase, numbers, and special characters)
- Multi-factor authentication is available for enhanced security
- All authentication endpoints are rate-limited to prevent brute force attacks
- All communication must use HTTPS to ensure encryption in transit

## Error Handling

Authentication errors return standard error responses with the following structure:

```json
{
  "error_code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": null,
  "status_code": 401
}
```

Common error codes include:

- `UNAUTHORIZED`: Not authenticated or token expired
- `INVALID_CREDENTIALS`: Invalid username or password
- `INVALID_TOKEN`: Invalid or expired token
- `VALIDATION_ERROR`: Invalid request data
- `USER_NOT_FOUND`: User not found
- `INVALID_CODE`: Invalid verification or confirmation code
- `MFA_REQUIRED`: Multi-factor authentication required