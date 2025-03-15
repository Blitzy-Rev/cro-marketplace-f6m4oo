import { renderHook, act } from '@testing-library/react-hooks'; // ^8.0.1
import { render, screen, waitFor } from '@testing-library/react'; // ^14.0.0
import useAuth from '../../src/hooks/useAuth';
import { 
  AuthContextType, 
  LoginCredentials, 
  RegistrationData, 
  PasswordResetConfirm,
  MFAVerification 
} from '../../src/types/auth.types';
import { User } from '../../src/types/user.types';
import * as authUtils from '../../src/utils/auth';

// Mock the useAuthContext hook
jest.mock('../../src/contexts/AuthContext', () => ({
  useAuthContext: jest.fn()
}));

// Mock the auth utilities
jest.mock('../../src/utils/auth', () => ({
  isAuthenticated: jest.fn(),
  hasPermission: jest.fn()
}));

describe('useAuth', () => {
  // Setup for each test
  const mockAuthState = {
    isAuthenticated: false,
    user: null,
    loading: false,
    error: null,
    mfaRequired: false
  };
  
  const mockLogin = jest.fn();
  const mockLogout = jest.fn();
  const mockRegister = jest.fn();
  const mockResetPassword = jest.fn();
  const mockConfirmPasswordReset = jest.fn();
  const mockVerifyMFA = jest.fn();
  
  // Reset all mocks and set up the mock implementations before each test
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Import the mocked module
    const { useAuthContext } = require('../../src/contexts/AuthContext');
    
    // Setup mock implementation
    useAuthContext.mockReturnValue({
      authState: mockAuthState,
      login: mockLogin,
      logout: mockLogout,
      register: mockRegister,
      resetPassword: mockResetPassword,
      confirmPasswordReset: mockConfirmPasswordReset,
      verifyMFA: mockVerifyMFA
    });
    
    // Mock auth utility functions
    (authUtils.hasPermission as jest.Mock).mockReturnValue(true);
  });
  
  it('should return authentication state and functions', () => {
    const { result } = renderHook(() => useAuth());
    
    // Test that the hook returns the correct state
    expect(result.current.isAuthenticated).toBe(mockAuthState.isAuthenticated);
    expect(result.current.user).toBe(mockAuthState.user);
    expect(result.current.loading).toBe(mockAuthState.loading);
    expect(result.current.error).toBe(mockAuthState.error);
    expect(result.current.mfaRequired).toBe(mockAuthState.mfaRequired);
    
    // Test that the hook returns the correct functions
    expect(result.current.login).toBe(mockLogin);
    expect(result.current.logout).toBe(mockLogout);
    expect(result.current.register).toBe(mockRegister);
    expect(result.current.resetPassword).toBe(mockResetPassword);
    expect(result.current.confirmPasswordReset).toBe(mockConfirmPasswordReset);
    expect(result.current.verifyMFA).toBe(mockVerifyMFA);
    expect(typeof result.current.hasPermission).toBe('function');
  });
  
  it('should call login function with credentials', () => {
    const { result } = renderHook(() => useAuth());
    
    const credentials: LoginCredentials = {
      email: 'test@example.com',
      password: 'password123',
      remember_me: true
    };
    
    // Call the login function
    act(() => {
      result.current.login(credentials);
    });
    
    // Check that the context login function was called with the credentials
    expect(mockLogin).toHaveBeenCalledWith(credentials);
  });
  
  it('should call logout function', () => {
    const { result } = renderHook(() => useAuth());
    
    // Call the logout function
    act(() => {
      result.current.logout();
    });
    
    // Check that the context logout function was called
    expect(mockLogout).toHaveBeenCalled();
  });
  
  it('should call register function with registration data', () => {
    const { result } = renderHook(() => useAuth());
    
    const registrationData: RegistrationData = {
      email: 'test@example.com',
      password: 'password123',
      full_name: 'Test User',
      organization_name: 'Test Org',
      role: 'pharma_scientist'
    };
    
    // Call the register function
    act(() => {
      result.current.register(registrationData);
    });
    
    // Check that the context register function was called with the registration data
    expect(mockRegister).toHaveBeenCalledWith(registrationData);
  });
  
  it('should call resetPassword function with email', () => {
    const { result } = renderHook(() => useAuth());
    
    const email = 'test@example.com';
    
    // Call the resetPassword function
    act(() => {
      result.current.resetPassword(email);
    });
    
    // Check that the context resetPassword function was called with the email
    expect(mockResetPassword).toHaveBeenCalledWith(email);
  });
  
  it('should call confirmPasswordReset function with token and password', () => {
    const { result } = renderHook(() => useAuth());
    
    const resetData: PasswordResetConfirm = {
      token: 'reset-token-123',
      new_password: 'new-password-123'
    };
    
    // Call the confirmPasswordReset function
    act(() => {
      result.current.confirmPasswordReset(resetData);
    });
    
    // Check that the context confirmPasswordReset function was called with the reset data
    expect(mockConfirmPasswordReset).toHaveBeenCalledWith(resetData);
  });
  
  it('should call verifyMFA function with code', () => {
    const { result } = renderHook(() => useAuth());
    
    const code = '123456';
    
    // Call the verifyMFA function
    act(() => {
      result.current.verifyMFA(code);
    });
    
    // Check that the context verifyMFA function was called with the code
    expect(mockVerifyMFA).toHaveBeenCalledWith(code);
  });
  
  it('should call hasPermission function with required roles', () => {
    const { result } = renderHook(() => useAuth());
    
    const requiredRoles = ['pharma_admin', 'pharma_scientist'];
    
    // Configure the mock to return a specific value
    (authUtils.hasPermission as jest.Mock).mockReturnValue(true);
    
    // Call the hasPermission function
    const hasPermission = result.current.hasPermission(requiredRoles);
    
    // Check that the auth utility hasPermission function was called with the required roles
    expect(authUtils.hasPermission).toHaveBeenCalledWith(requiredRoles);
    expect(hasPermission).toBe(true);
  });
  
  it('should memoize functions to prevent unnecessary rerenders', () => {
    const { result, rerender } = renderHook(() => useAuth());
    
    // Store references to the returned functions
    const initialHasPermission = result.current.hasPermission;
    
    // Rerender the hook
    rerender();
    
    // Check that the function references remain the same after rerender
    expect(result.current.hasPermission).toBe(initialHasPermission);
  });
});