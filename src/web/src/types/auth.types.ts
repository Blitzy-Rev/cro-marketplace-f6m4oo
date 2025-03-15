/**
 * TypeScript type definitions for authentication-related data structures in the
 * Molecular Data Management and CRO Integration Platform.
 * 
 * This file defines interfaces for authentication state, credentials, tokens, 
 * and JWT payloads used throughout the frontend application.
 */

import { User } from './user.types';

/**
 * Interface for authentication token response from the API.
 * Contains tokens and related information returned after successful authentication.
 */
export interface AuthToken {
  /** JWT access token used for API authorization */
  access_token: string;
  /** Token used to obtain a new access token when the current one expires */
  refresh_token: string;
  /** Type of token, typically "Bearer" */
  token_type: string;
  /** Time in seconds until the access token expires */
  expires_in: number;
}

/**
 * Interface for decoded JWT token payload.
 * Contains claims from the JWT including user identity and permissions.
 */
export interface JWTPayload {
  /** Subject identifier, typically the user ID */
  sub: string;
  /** Expiration timestamp */
  exp: number;
  /** Issued at timestamp */
  iat: number;
  /** User's role in the system */
  role: string;
  /** ID of the organization the user belongs to (may be null) */
  organization_id: string | null;
}

/**
 * Interface for login request payload.
 * Contains credentials required for user authentication.
 */
export interface LoginCredentials {
  /** User's email address */
  email: string;
  /** User's password */
  password: string;
  /** Whether to persist authentication beyond the current session */
  remember_me: boolean;
}

/**
 * Interface for user registration request payload.
 * Contains data required to create a new user account.
 */
export interface RegistrationData {
  /** User's email address */
  email: string;
  /** User's password */
  password: string;
  /** User's full name */
  full_name: string;
  /** Name of the user's organization */
  organization_name: string;
  /** User's role in the system */
  role: string;
}

/**
 * Interface for password reset request payload.
 * Used to initiate the password reset process.
 */
export interface PasswordResetRequest {
  /** Email address for the account to reset */
  email: string;
}

/**
 * Interface for password reset confirmation payload.
 * Used to complete the password reset process.
 */
export interface PasswordResetConfirm {
  /** Reset token received via email */
  token: string;
  /** New password to set */
  new_password: string;
}

/**
 * Interface for multi-factor authentication verification payload.
 * Used when MFA is required during the login process.
 */
export interface MFAVerification {
  /** Temporary token received after initial authentication */
  mfa_token: string;
  /** Verification code from the user's authenticator app or SMS */
  code: string;
}

/**
 * Interface for authentication state in the application.
 * Represents the current state of user authentication.
 */
export interface AuthState {
  /** Whether the user is currently authenticated */
  isAuthenticated: boolean;
  /** Currently authenticated user data, or null if not authenticated */
  user: User | null;
  /** Authentication tokens, or null if not authenticated */
  token: AuthToken | null;
  /** Whether authentication is currently in progress */
  loading: boolean;
  /** Error message from authentication process, or null if no error */
  error: string | null;
  /** Whether multi-factor authentication is required */
  mfaRequired: boolean;
  /** Temporary token for MFA verification, or null if MFA not in progress */
  mfaToken: string | null;
}

/**
 * Interface for authentication context providing auth state and functions.
 * Used to provide authentication functionality throughout the application.
 */
export interface AuthContextType {
  /** Current authentication state */
  authState: AuthState;
  /** Function to authenticate a user with credentials */
  login: (credentials: LoginCredentials) => Promise<void>;
  /** Function to log out the current user */
  logout: () => Promise<void>;
  /** Function to register a new user */
  register: (data: RegistrationData) => Promise<void>;
  /** Function to request a password reset */
  resetPassword: (data: PasswordResetRequest) => Promise<void>;
  /** Function to confirm a password reset */
  confirmPasswordReset: (data: PasswordResetConfirm) => Promise<void>;
  /** Function to verify an MFA code */
  verifyMFA: (data: MFAVerification) => Promise<void>;
}