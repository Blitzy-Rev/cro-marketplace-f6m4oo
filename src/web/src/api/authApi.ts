/**
 * API client for authentication-related operations in the Molecular Data Management and CRO Integration Platform.
 * This file provides functions for user authentication, registration, password management, and session handling.
 */

import { post, get } from './apiClient'; // v1.4.0
import { API_ENDPOINTS } from '../constants/apiEndpoints';
import { 
  AuthToken, 
  LoginCredentials, 
  RegistrationData, 
  PasswordResetRequest, 
  PasswordResetConfirm,
  MFAVerification 
} from '../types/auth.types';
import { User } from '../types/user.types';

/**
 * Authenticates a user with email and password credentials
 * @param credentials - User login credentials
 * @returns Promise resolving to authentication token and user data
 */
export const login = async (credentials: LoginCredentials): Promise<{ token: AuthToken; user: User }> => {
  return post<{ token: AuthToken; user: User }>(API_ENDPOINTS.AUTH.LOGIN, credentials);
};

/**
 * Registers a new user with the system
 * @param data - User registration data
 * @returns Promise resolving to authentication token and user data
 */
export const register = async (data: RegistrationData): Promise<{ token: AuthToken; user: User }> => {
  return post<{ token: AuthToken; user: User }>(API_ENDPOINTS.USERS.CREATE, data);
};

/**
 * Logs out the current user by invalidating their session
 * @returns Promise resolving when logout is complete
 */
export const logout = async (): Promise<void> => {
  return post<void>(API_ENDPOINTS.AUTH.LOGOUT);
};

/**
 * Refreshes the authentication token using a refresh token
 * @param refreshToken - The refresh token
 * @returns Promise resolving to new authentication token
 */
export const refreshToken = async (refreshToken: string): Promise<AuthToken> => {
  return post<AuthToken>(API_ENDPOINTS.AUTH.REFRESH_TOKEN, { refresh_token: refreshToken });
};

/**
 * Retrieves the current authenticated user's profile
 * @returns Promise resolving to current user data
 */
export const getCurrentUser = async (): Promise<User> => {
  return get<User>(API_ENDPOINTS.USERS.ME);
};

/**
 * Requests a password reset email for the specified email address
 * @param email - Email address for the account to reset
 * @returns Promise resolving to success message
 */
export const requestPasswordReset = async (email: string): Promise<{ message: string }> => {
  const request: PasswordResetRequest = { email };
  return post<{ message: string }>(API_ENDPOINTS.AUTH.PASSWORD_RESET_REQUEST, request);
};

/**
 * Resets a user's password using a reset token
 * @param data - Password reset confirmation data with token and new password
 * @returns Promise resolving to success message
 */
export const resetPassword = async (data: PasswordResetConfirm): Promise<{ message: string }> => {
  return post<{ message: string }>(API_ENDPOINTS.AUTH.PASSWORD_RESET, data);
};

/**
 * Verifies a multi-factor authentication code during login
 * @param data - MFA verification data with token and code
 * @returns Promise resolving to authentication token and user data
 */
export const verifyMFA = async (data: MFAVerification): Promise<{ token: AuthToken; user: User }> => {
  return post<{ token: AuthToken; user: User }>(API_ENDPOINTS.AUTH.VERIFY_MFA, data);
};

/**
 * Changes the current user's password
 * @param currentPassword - User's current password
 * @param newPassword - User's new password
 * @returns Promise resolving to success message
 */
export const changePassword = async (
  currentPassword: string,
  newPassword: string
): Promise<{ message: string }> => {
  return post<{ message: string }>(API_ENDPOINTS.USERS.CHANGE_PASSWORD, {
    current_password: currentPassword,
    new_password: newPassword
  });
};