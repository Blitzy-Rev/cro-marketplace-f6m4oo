/**
 * Custom hook that provides authentication functionality for the Molecular Data Management and CRO Integration Platform.
 * 
 * This hook abstracts the authentication context and provides a simplified interface for login, logout, registration,
 * password management, and multi-factor authentication verification.
 */

import { useCallback } from 'react'; // ^18.0.0
import { useAuthContext } from '../contexts/AuthContext';
import { 
  AuthState, 
  LoginCredentials, 
  RegistrationData, 
  PasswordResetConfirm, 
  MFAVerification 
} from '../types/auth.types';
import { User } from '../types/user.types';
import { isAuthenticated, hasPermission } from '../utils/auth';

/**
 * Custom hook that provides authentication functionality for the application.
 * 
 * @returns Object containing authentication state and functions:
 * - isAuthenticated: Boolean indicating if user is authenticated
 * - user: Current user object or null if not authenticated
 * - loading: Boolean indicating if authentication operation is in progress
 * - error: Error message or null if no error
 * - mfaRequired: Boolean indicating if MFA verification is required
 * - login: Function to authenticate with credentials
 * - logout: Function to log out the current user
 * - register: Function to register a new user
 * - resetPassword: Function to request a password reset
 * - confirmPasswordReset: Function to confirm a password reset
 * - verifyMFA: Function to verify MFA code
 * - hasPermission: Function to check if user has required permissions
 */
export function useAuth() {
  // Get authentication context
  const { authState, login, logout, register, resetPassword, confirmPasswordReset, verifyMFA } = useAuthContext();
  
  // Create memoized helper function for permission checks
  const checkPermission = useCallback((requiredRoles: string | string[]): boolean => {
    return hasPermission(requiredRoles);
  }, []);

  // Return authentication state and functions
  return {
    // Auth state
    isAuthenticated: authState.isAuthenticated,
    user: authState.user,
    loading: authState.loading,
    error: authState.error,
    mfaRequired: authState.mfaRequired,
    
    // Auth functions
    login,
    logout,
    register,
    resetPassword,
    confirmPasswordReset,
    verifyMFA,
    
    // Helper functions
    hasPermission: checkPermission,
  };
}