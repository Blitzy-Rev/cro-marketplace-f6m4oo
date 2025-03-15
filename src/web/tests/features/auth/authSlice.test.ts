import { configureStore } from '@reduxjs/toolkit'; // ^1.9.5
import { authReducer, loginUser, registerUser, logoutUser, refreshUserToken, fetchCurrentUser, requestPasswordResetEmail, confirmPasswordReset, verifyMFACode, initializeAuth, selectAuth, selectIsAuthenticated, selectCurrentUser, selectAuthLoading, selectAuthError, selectMFARequired, selectMFAToken } from '../../src/features/auth/authSlice';
import { AuthState, LoginCredentials, RegistrationData, PasswordResetRequest, PasswordResetConfirm, MFAVerification, AuthToken } from '../../src/types/auth.types';
import { User } from '../../src/types/user.types';
import { login, register, logout, refreshToken, getCurrentUser, requestPasswordReset, resetPassword, verifyMFA } from '../../src/api/authApi';
import { setAuthToken, getAuthToken, removeAuthToken, isAuthenticated } from '../../src/utils/auth';
import { createMockUser } from '../../src/utils/testHelpers';
import jest from 'jest'; // ^29.0.0

// Mock the API functions
jest.mock('../../src/api/authApi');
jest.mock('../../src/utils/auth');

// Type definitions for mock functions
type Mocked<T> = T extends (...args: any[]) => any ? jest.Mock<ReturnType<T>, Parameters<T>> : T;

const mockedLogin = login as Mocked<typeof login>;
const mockedRegister = register as Mocked<typeof register>;
const mockedLogout = logout as Mocked<typeof logout>;
const mockedRefreshToken = refreshToken as Mocked<typeof refreshToken>;
const mockedGetCurrentUser = getCurrentUser as Mocked<typeof getCurrentUser>;
const mockedRequestPasswordReset = requestPasswordReset as Mocked<typeof requestPasswordReset>;
const mockedResetPassword = resetPassword as Mocked<typeof resetPassword>;
const mockedVerifyMFA = verifyMFA as Mocked<typeof verifyMFA>;

const mockedSetAuthToken = setAuthToken as Mocked<typeof setAuthToken>;
const mockedGetAuthToken = getAuthToken as Mocked<typeof getAuthToken>;
const mockedRemoveAuthToken = removeAuthToken as Mocked<typeof removeAuthToken>;
const mockedIsAuthenticated = isAuthenticated as Mocked<typeof isAuthenticated>;

/**
 * Creates a mock authentication state for testing
 * @param overrides - Optional overrides for the default state
 * @returns Mock authentication state with default values and overrides
 */
const createMockAuthState = (overrides?: Partial<AuthState>): AuthState => {
  const defaultState: AuthState = {
    isAuthenticated: false,
    user: null,
    token: null,
    loading: false,
    error: null,
    mfaRequired: false,
    mfaToken: null,
  };

  return { ...defaultState, ...overrides };
};

/**
 * Creates a mock authentication token for testing
 * @param overrides - Optional overrides for the default token
 * @returns Mock authentication token with default values and overrides
 */
const createMockAuthToken = (overrides?: Partial<AuthToken>): AuthToken => {
  const defaultToken: AuthToken = {
    access_token: 'mock_access_token',
    refresh_token: 'mock_refresh_token',
    token_type: 'Bearer',
    expires_in: 3600,
  };

  return { ...defaultToken, ...overrides };
};

/**
 * Creates a Redux store with auth reducer for testing
 * @param initialState - Optional initial state for the store
 * @returns Configured Redux store
 */
const createTestStore = (initialState?: Partial<AuthState>) => {
  return configureStore({
    reducer: {
      auth: authReducer,
    },
    preloadedState: {
      auth: createMockAuthState(initialState),
    },
  });
};

describe('authSlice', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should handle initial state', () => {
    const store = createTestStore();
    expect(selectAuth(store.getState())).toEqual(createMockAuthState());
  });

  describe('loginUser', () => {
    it('should set loading to true while pending', () => {
      const store = createTestStore();
      store.dispatch(loginUser({ email: 'test@example.com', password: 'password', remember_me: false }));
      expect(selectAuthLoading(store.getState())).toBe(true);
    });

    it('should set isAuthenticated to true and user on successful login', async () => {
      const mockUser = createMockUser();
      const mockToken = createMockAuthToken();
      mockedLogin.mockResolvedValue({ user: mockUser, token: mockToken });
      mockedSetAuthToken.mockReturnValue(true);

      const store = createTestStore();
      await store.dispatch(loginUser({ email: 'test@example.com', password: 'password', remember_me: false }));

      expect(selectIsAuthenticated(store.getState())).toBe(true);
      expect(selectCurrentUser(store.getState())).toEqual(mockUser);
      expect(selectAuthLoading(store.getState())).toBe(false);
      expect(mockedSetAuthToken).toHaveBeenCalledWith(mockToken);
    });

    it('should set error on rejected login', async () => {
      mockedLogin.mockRejectedValue(new Error('Login failed'));

      const store = createTestStore();
      await store.dispatch(loginUser({ email: 'test@example.com', password: 'password', remember_me: false }));

      expect(selectIsAuthenticated(store.getState())).toBe(false);
      expect(selectAuthError(store.getState())).toBe('Error: Login failed');
      expect(selectAuthLoading(store.getState())).toBe(false);
    });

    it('should handle MFA required error', async () => {
      const mfaToken = 'mock_mfa_token';
      mockedLogin.mockRejectedValue({ mfa_required: true, mfa_token: mfaToken });

      const store = createTestStore();
      await store.dispatch(loginUser({ email: 'test@example.com', password: 'password', remember_me: false }));

      expect(selectMFARequired(store.getState())).toBe(true);
      expect(selectMFAToken(store.getState())).toBe(mfaToken);
    });
  });

  describe('registerUser', () => {
    it('should set loading to true while registering', () => {
      const store = createTestStore();
      store.dispatch(registerUser({ email: 'test@example.com', password: 'password', full_name: 'Test User', organization_name: 'Test Org', role: 'pharma_scientist' }));
      expect(selectAuthLoading(store.getState())).toBe(true);
    });

    it('should set isAuthenticated to true and user on successful registration', async () => {
      const mockUser = createMockUser();
      const mockToken = createMockAuthToken();
      mockedRegister.mockResolvedValue({ user: mockUser, token: mockToken });
      mockedSetAuthToken.mockReturnValue(true);

      const store = createTestStore();
      await store.dispatch(registerUser({ email: 'test@example.com', password: 'password', full_name: 'Test User', organization_name: 'Test Org', role: 'pharma_scientist' }));

      expect(selectIsAuthenticated(store.getState())).toBe(true);
      expect(selectCurrentUser(store.getState())).toEqual(mockUser);
      expect(selectAuthLoading(store.getState())).toBe(false);
      expect(mockedSetAuthToken).toHaveBeenCalledWith(mockToken);
    });

    it('should set error on rejected registration', async () => {
      mockedRegister.mockRejectedValue(new Error('Registration failed'));

      const store = createTestStore();
      await store.dispatch(registerUser({ email: 'test@example.com', password: 'password', full_name: 'Test User', organization_name: 'Test Org', role: 'pharma_scientist' }));

      expect(selectIsAuthenticated(store.getState())).toBe(false);
      expect(selectAuthError(store.getState())).toBe('Error: Registration failed');
      expect(selectAuthLoading(store.getState())).toBe(false);
    });
  });

  describe('logoutUser', () => {
    it('should set loading to true while logging out', () => {
      const store = createTestStore({ isAuthenticated: true, user: createMockUser() });
      store.dispatch(logoutUser());
      expect(selectAuthLoading(store.getState())).toBe(true);
    });

    it('should reset state to initial state on successful logout', async () => {
      mockedLogout.mockResolvedValue(undefined);
      mockedRemoveAuthToken.mockReturnValue(true);

      const store = createTestStore({ isAuthenticated: true, user: createMockUser() });
      await store.dispatch(logoutUser());

      expect(selectIsAuthenticated(store.getState())).toBe(false);
      expect(selectCurrentUser(store.getState())).toBeNull();
      expect(selectAuthLoading(store.getState())).toBe(false);
      expect(mockedRemoveAuthToken).toHaveBeenCalled();
    });

    it('should reset state to initial state even if logout API fails', async () => {
      mockedLogout.mockRejectedValue(new Error('Logout failed'));
      mockedRemoveAuthToken.mockReturnValue(true);

      const store = createTestStore({ isAuthenticated: true, user: createMockUser() });
      await store.dispatch(logoutUser());

      expect(selectIsAuthenticated(store.getState())).toBe(false);
      expect(selectCurrentUser(store.getState())).toBeNull();
      expect(selectAuthLoading(store.getState())).toBe(false);
      expect(mockedRemoveAuthToken).toHaveBeenCalled();
    });
  });

  describe('refreshUserToken', () => {
    it('should set loading to true while refreshing token', () => {
      const store = createTestStore({ token: createMockAuthToken() });
      store.dispatch(refreshUserToken('mock_refresh_token'));
      expect(selectAuthLoading(store.getState())).toBe(true);
    });

    it('should update token on successful refresh', async () => {
      const mockToken = createMockAuthToken({ access_token: 'new_access_token' });
      mockedRefreshToken.mockResolvedValue(mockToken);
      mockedSetAuthToken.mockReturnValue(true);

      const store = createTestStore({ token: createMockAuthToken() });
      await store.dispatch(refreshUserToken('mock_refresh_token'));

      expect(selectAuthLoading(store.getState())).toBe(false);
      expect(selectAuth(store.getState()).token).toEqual(mockToken);
      expect(mockedSetAuthToken).toHaveBeenCalledWith(mockToken);
    });

    it('should set error and reset auth state on rejected refresh', async () => {
      mockedRefreshToken.mockRejectedValue(new Error('Token refresh failed'));
      mockedRemoveAuthToken.mockReturnValue(true);

      const store = createTestStore({ isAuthenticated: true, user: createMockUser(), token: createMockAuthToken() });
      await store.dispatch(refreshUserToken('mock_refresh_token'));

      expect(selectAuthLoading(store.getState())).toBe(false);
      expect(selectAuthError(store.getState())).toBe('Error: Token refresh failed');
      expect(selectIsAuthenticated(store.getState())).toBe(false);
      expect(selectCurrentUser(store.getState())).toBeNull();
      expect(mockedRemoveAuthToken).toHaveBeenCalled();
    });
  });

  describe('fetchCurrentUser', () => {
    it('should set loading to true while fetching current user', () => {
      const store = createTestStore({ isAuthenticated: true });
      store.dispatch(fetchCurrentUser());
      expect(selectAuthLoading(store.getState())).toBe(true);
    });

    it('should set user and isAuthenticated to true on successful fetch', async () => {
      const mockUser = createMockUser();
      mockedGetCurrentUser.mockResolvedValue(mockUser);

      const store = createTestStore({ isAuthenticated: true });
      await store.dispatch(fetchCurrentUser());

      expect(selectAuthLoading(store.getState())).toBe(false);
      expect(selectCurrentUser(store.getState())).toEqual(mockUser);
      expect(selectIsAuthenticated(store.getState())).toBe(true);
    });

    it('should set error and reset auth state on rejected fetch', async () => {
      mockedGetCurrentUser.mockRejectedValue(new Error('Failed to fetch user'));

      const store = createTestStore({ isAuthenticated: true });
      await store.dispatch(fetchCurrentUser());

      expect(selectAuthLoading(store.getState())).toBe(false);
      expect(selectAuthError(store.getState())).toBe('Error: Failed to fetch user');
      expect(selectIsAuthenticated(store.getState())).toBe(false);
      expect(selectCurrentUser(store.getState())).toBeNull();
    });
  });

  describe('requestPasswordResetEmail', () => {
    it('should set loading to true while requesting password reset', () => {
      const store = createTestStore();
      store.dispatch(requestPasswordResetEmail({ email: 'test@example.com' }));
      expect(selectAuthLoading(store.getState())).toBe(true);
    });

    it('should set loading to false on successful request', async () => {
      mockedRequestPasswordReset.mockResolvedValue({ message: 'Password reset email sent' });

      const store = createTestStore();
      await store.dispatch(requestPasswordResetEmail({ email: 'test@example.com' }));

      expect(selectAuthLoading(store.getState())).toBe(false);
    });

    it('should set error on rejected request', async () => {
      mockedRequestPasswordReset.mockRejectedValue(new Error('Failed to request password reset'));

      const store = createTestStore();
      await store.dispatch(requestPasswordResetEmail({ email: 'test@example.com' }));

      expect(selectAuthLoading(store.getState())).toBe(false);
      expect(selectAuthError(store.getState())).toBe('Error: Failed to request password reset');
    });
  });

  describe('confirmPasswordReset', () => {
    it('should set loading to true while confirming password reset', () => {
      const store = createTestStore();
      store.dispatch(confirmPasswordReset({ token: 'mock_token', new_password: 'new_password' }));
      expect(selectAuthLoading(store.getState())).toBe(true);
    });

    it('should set loading to false on successful confirmation', async () => {
      mockedResetPassword.mockResolvedValue({ message: 'Password reset successfully' });

      const store = createTestStore();
      await store.dispatch(confirmPasswordReset({ token: 'mock_token', new_password: 'new_password' }));

      expect(selectAuthLoading(store.getState())).toBe(false);
    });

    it('should set error on rejected confirmation', async () => {
      mockedResetPassword.mockRejectedValue(new Error('Failed to confirm password reset'));

      const store = createTestStore();
      await store.dispatch(confirmPasswordReset({ token: 'mock_token', new_password: 'new_password' }));

      expect(selectAuthLoading(store.getState())).toBe(false);
      expect(selectAuthError(store.getState())).toBe('Error: Failed to confirm password reset');
    });
  });

  describe('verifyMFACode', () => {
    it('should set loading to true while verifying MFA code', () => {
      const store = createTestStore();
      store.dispatch(verifyMFACode({ mfa_token: 'mock_mfa_token', code: '123456' }));
      expect(selectAuthLoading(store.getState())).toBe(true);
    });

    it('should set isAuthenticated to true and user on successful MFA verification', async () => {
      const mockUser = createMockUser();
      const mockToken = createMockAuthToken();
      mockedVerifyMFA.mockResolvedValue({ user: mockUser, token: mockToken });
      mockedSetAuthToken.mockReturnValue(true);

      const store = createTestStore({ mfaRequired: true, mfaToken: 'mock_mfa_token' });
      await store.dispatch(verifyMFACode({ mfa_token: 'mock_mfa_token', code: '123456' }));

      expect(selectIsAuthenticated(store.getState())).toBe(true);
      expect(selectCurrentUser(store.getState())).toEqual(mockUser);
      expect(selectAuthLoading(store.getState())).toBe(false);
      expect(selectMFARequired(store.getState())).toBe(false);
      expect(selectMFAToken(store.getState())).toBeNull();
      expect(mockedSetAuthToken).toHaveBeenCalledWith(mockToken);
    });

    it('should set error on rejected MFA verification', async () => {
      mockedVerifyMFA.mockRejectedValue(new Error('MFA verification failed'));

      const store = createTestStore({ mfaRequired: true, mfaToken: 'mock_mfa_token' });
      await store.dispatch(verifyMFACode({ mfa_token: 'mock_mfa_token', code: '123456' }));

      expect(selectIsAuthenticated(store.getState())).toBe(false);
      expect(selectAuthError(store.getState())).toBe('Error: MFA verification failed');
      expect(selectAuthLoading(store.getState())).toBe(false);
      expect(selectMFARequired(store.getState())).toBe(true);
      expect(selectMFAToken(store.getState())).toBe('mock_mfa_token');
    });
  });

  describe('initializeAuth', () => {
    it('should set loading to true while initializing auth', () => {
      const store = createTestStore();
      store.dispatch(initializeAuth());
      expect(selectAuthLoading(store.getState())).toBe(true);
    });

    it('should set isAuthenticated to true and user if token is valid', async () => {
      const mockUser = createMockUser();
      mockedIsAuthenticated.mockReturnValue(true);
      mockedGetCurrentUser.mockResolvedValue(mockUser);

      const store = createTestStore();
      await store.dispatch(initializeAuth());

      expect(selectAuthLoading(store.getState())).toBe(false);
      expect(selectIsAuthenticated(store.getState())).toBe(true);
      expect(selectCurrentUser(store.getState())).toEqual(mockUser);
    });

    it('should set isAuthenticated to false and clear user if token is invalid', async () => {
      mockedIsAuthenticated.mockReturnValue(false);

      const store = createTestStore({ isAuthenticated: true, user: createMockUser() });
      await store.dispatch(initializeAuth());

      expect(selectAuthLoading(store.getState())).toBe(false);
      expect(selectIsAuthenticated(store.getState())).toBe(false);
      expect(selectCurrentUser(store.getState())).toBeNull();
    });

    it('should handle getCurrentUser failure during initialization', async () => {
      mockedIsAuthenticated.mockReturnValue(true);
      mockedGetCurrentUser.mockRejectedValue(new Error('Failed to get user'));
      mockedRemoveAuthToken.mockReturnValue(true);

      const store = createTestStore({ isAuthenticated: true, user: createMockUser() });
      await store.dispatch(initializeAuth());

      expect(selectAuthLoading(store.getState())).toBe(false);
      expect(selectIsAuthenticated(store.getState())).toBe(false);
      expect(selectCurrentUser(store.getState())).toBeNull();
      expect(mockedRemoveAuthToken).toHaveBeenCalled();
    });
  });
});