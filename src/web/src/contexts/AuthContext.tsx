/**
 * Authentication context provider for the Molecular Data Management and CRO Integration Platform.
 * 
 * This context manages the authentication state and provides authentication-related functions
 * throughout the application, including login, logout, registration, password management,
 * and multi-factor authentication.
 * 
 * @version 1.0.0
 */

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { 
  AuthState, 
  AuthContextType, 
  LoginCredentials, 
  RegistrationData, 
  PasswordResetRequest, 
  PasswordResetConfirm,
  MFAVerification 
} from '../types/auth.types';
import { User } from '../types/user.types';
import { 
  login, 
  logout, 
  register, 
  requestPasswordReset, 
  resetPassword, 
  verifyMFA, 
  getCurrentUser 
} from '../api/authApi';
import { 
  setAuthToken, 
  getAuthToken, 
  removeAuthToken, 
  isAuthenticated 
} from '../utils/auth';
import { handleApiError } from '../utils/errorHandler';

/**
 * Initial authentication state with default values
 */
const initialAuthState: AuthState = {
  isAuthenticated: false,
  user: null,
  token: null,
  loading: true,
  error: null,
  mfaRequired: false,
  mfaToken: null
};

/**
 * Authentication context providing authentication state and functions
 */
const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Props for the AuthProvider component
 */
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Authentication provider component that manages authentication state and provides 
 * authentication-related functions to child components.
 */
const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  // Authentication state management
  const [authState, setAuthState] = useState<AuthState>(initialAuthState);

  // Check for existing authentication on component mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        setAuthState(prevState => ({ ...prevState, loading: true }));
        
        if (isAuthenticated()) {
          // Fetch current user data
          const userData = await getCurrentUser();
          const token = getAuthToken();
          
          setAuthState({
            isAuthenticated: true,
            user: userData,
            token,
            loading: false,
            error: null,
            mfaRequired: false,
            mfaToken: null
          });
        } else {
          // Not authenticated - reset state
          setAuthState({
            isAuthenticated: false,
            user: null,
            token: null,
            loading: false,
            error: null,
            mfaRequired: false,
            mfaToken: null
          });
        }
      } catch (error) {
        handleApiError(error, false);
        
        setAuthState({
          isAuthenticated: false,
          user: null,
          token: null,
          loading: false,
          error: 'Failed to authenticate. Please log in again.',
          mfaRequired: false,
          mfaToken: null
        });
      }
    };

    checkAuth();
  }, []);

  /**
   * Handles user login with provided credentials
   * Manages standard login flow and MFA verification flow
   */
  const handleLogin = async (credentials: LoginCredentials): Promise<boolean> => {
    try {
      setAuthState(prevState => ({ 
        ...prevState, 
        loading: true,
        error: null
      }));

      const response = await login(credentials);

      // Check if MFA is required
      if (response.token && !response.user) {
        setAuthState(prevState => ({
          ...prevState,
          loading: false,
          mfaRequired: true,
          mfaToken: response.token.access_token
        }));
        return true; // MFA verification needed
      }

      // Standard login (no MFA required)
      if (response.token) {
        setAuthToken(response.token);
      }

      setAuthState({
        isAuthenticated: true,
        user: response.user,
        token: response.token,
        loading: false,
        error: null,
        mfaRequired: false,
        mfaToken: null
      });

      return true; // Login successful
    } catch (error) {
      handleApiError(error, true);
      
      setAuthState(prevState => ({
        ...prevState,
        loading: false,
        error: 'Login failed. Please check your credentials and try again.',
        isAuthenticated: false
      }));

      return false; // Login failed
    }
  };

  /**
   * Handles user logout by calling the logout API and clearing auth state
   */
  const handleLogout = async (): Promise<void> => {
    try {
      setAuthState(prevState => ({ ...prevState, loading: true }));
      
      // Call logout API
      await logout();
      
      // Remove token from storage
      removeAuthToken();
      
      // Reset auth state
      setAuthState({
        isAuthenticated: false,
        user: null,
        token: null,
        loading: false,
        error: null,
        mfaRequired: false,
        mfaToken: null
      });
    } catch (error) {
      handleApiError(error, true);
      
      // Force logout even if API call fails
      removeAuthToken();
      
      setAuthState({
        isAuthenticated: false,
        user: null,
        token: null,
        loading: false,
        error: null,
        mfaRequired: false,
        mfaToken: null
      });
    }
  };

  /**
   * Handles user registration with provided data
   */
  const handleRegister = async (data: RegistrationData): Promise<boolean> => {
    try {
      setAuthState(prevState => ({ 
        ...prevState, 
        loading: true,
        error: null
      }));

      const response = await register(data);

      // Store authentication token
      if (response.token) {
        setAuthToken(response.token);
      }

      // Update auth state with user data
      setAuthState({
        isAuthenticated: true,
        user: response.user,
        token: response.token,
        loading: false,
        error: null,
        mfaRequired: false,
        mfaToken: null
      });

      return true; // Registration successful
    } catch (error) {
      handleApiError(error, true);
      
      setAuthState(prevState => ({
        ...prevState,
        loading: false,
        error: 'Registration failed. Please check your information and try again.'
      }));

      return false; // Registration failed
    }
  };

  /**
   * Handles password reset request
   */
  const handleResetPassword = async (email: string): Promise<boolean> => {
    try {
      setAuthState(prevState => ({ 
        ...prevState, 
        loading: true,
        error: null
      }));

      // Request password reset
      await requestPasswordReset(email);

      setAuthState(prevState => ({
        ...prevState,
        loading: false
      }));

      return true; // Request successful
    } catch (error) {
      handleApiError(error, true);
      
      setAuthState(prevState => ({
        ...prevState,
        loading: false,
        error: 'Password reset request failed. Please try again.'
      }));

      return false; // Request failed
    }
  };

  /**
   * Handles password reset confirmation with token and new password
   */
  const handleConfirmPasswordReset = async (data: PasswordResetConfirm): Promise<boolean> => {
    try {
      setAuthState(prevState => ({ 
        ...prevState, 
        loading: true,
        error: null
      }));

      // Confirm password reset
      await resetPassword(data);

      setAuthState(prevState => ({
        ...prevState,
        loading: false
      }));

      return true; // Reset successful
    } catch (error) {
      handleApiError(error, true);
      
      setAuthState(prevState => ({
        ...prevState,
        loading: false,
        error: 'Password reset failed. Please try again.'
      }));

      return false; // Reset failed
    }
  };

  /**
   * Handles MFA verification during login process
   */
  const handleVerifyMFA = async (code: string): Promise<boolean> => {
    try {
      setAuthState(prevState => ({ 
        ...prevState, 
        loading: true,
        error: null
      }));

      // Check if MFA token exists
      if (!authState.mfaToken) {
        throw new Error('MFA token is missing. Please try logging in again.');
      }

      // Create verification data
      const verificationData: MFAVerification = {
        mfa_token: authState.mfaToken,
        code
      };
      
      // Verify MFA code
      const response = await verifyMFA(verificationData);

      // Store authentication token
      if (response.token) {
        setAuthToken(response.token);
      }

      // Update auth state with user data
      setAuthState({
        isAuthenticated: true,
        user: response.user,
        token: response.token,
        loading: false,
        error: null,
        mfaRequired: false,
        mfaToken: null
      });

      return true; // Verification successful
    } catch (error) {
      handleApiError(error, true);
      
      setAuthState(prevState => ({
        ...prevState,
        loading: false,
        error: 'MFA verification failed. Please try again.'
      }));

      return false; // Verification failed
    }
  };

  // Create the context value with auth state and functions
  const contextValue: AuthContextType = {
    authState,
    login: handleLogin,
    logout: handleLogout,
    register: handleRegister,
    resetPassword: handleResetPassword,
    confirmPasswordReset: handleConfirmPasswordReset,
    verifyMFA: handleVerifyMFA
  };

  // Provide the auth context to children
  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Custom hook to access the authentication context
 * 
 * @throws Error if used outside of AuthProvider
 * @returns Authentication context containing state and functions
 */
const useAuthContext = (): AuthContextType => {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  
  return context;
};

export { AuthContext, AuthProvider, useAuthContext };