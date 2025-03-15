import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { 
  AuthState, 
  LoginCredentials, 
  RegistrationData, 
  PasswordResetRequest, 
  PasswordResetConfirm,
  MFAVerification 
} from '../../types/auth.types';
import { User } from '../../types/user.types';
import { 
  login, 
  register, 
  logout, 
  refreshToken, 
  getCurrentUser,
  requestPasswordReset, 
  resetPassword, 
  verifyMFA 
} from '../../api/authApi';
import { 
  setAuthToken, 
  getAuthToken, 
  removeAuthToken, 
  isAuthenticated 
} from '../../utils/auth';

/**
 * Initial state for authentication
 */
const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  token: null,
  loading: false,
  error: null,
  mfaRequired: false,
  mfaToken: null
};

/**
 * Async thunk for user login
 * Authenticates user and stores JWT token
 */
export const loginUser = createAsyncThunk(
  'auth/login',
  async (credentials: LoginCredentials, { rejectWithValue }) => {
    try {
      const response = await login(credentials);
      setAuthToken(response.token);
      return response;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

/**
 * Async thunk for user registration
 * Creates a new user account and automatically logs in
 */
export const registerUser = createAsyncThunk(
  'auth/register',
  async (data: RegistrationData, { rejectWithValue }) => {
    try {
      const response = await register(data);
      setAuthToken(response.token);
      return response;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

/**
 * Async thunk for user logout
 * Invalidates the session and clears auth state
 */
export const logoutUser = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await logout();
      removeAuthToken();
    } catch (error) {
      // Still remove token even if API call fails
      removeAuthToken();
      return rejectWithValue(error);
    }
  }
);

/**
 * Async thunk for refreshing authentication token
 * Uses refresh token to get a new access token
 */
export const refreshUserToken = createAsyncThunk(
  'auth/refreshToken',
  async (refreshTokenValue: string, { rejectWithValue }) => {
    try {
      const token = await refreshToken(refreshTokenValue);
      setAuthToken(token);
      return token;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

/**
 * Async thunk for fetching current user profile
 * Gets the authenticated user's information
 */
export const fetchCurrentUser = createAsyncThunk(
  'auth/fetchCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      return await getCurrentUser();
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

/**
 * Async thunk for requesting password reset email
 * Initiates the password reset process
 */
export const requestPasswordResetEmail = createAsyncThunk(
  'auth/requestPasswordReset',
  async (data: PasswordResetRequest, { rejectWithValue }) => {
    try {
      return await requestPasswordReset(data.email);
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

/**
 * Async thunk for confirming password reset
 * Completes the password reset process with token and new password
 */
export const confirmPasswordReset = createAsyncThunk(
  'auth/confirmPasswordReset',
  async (data: PasswordResetConfirm, { rejectWithValue }) => {
    try {
      return await resetPassword(data);
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

/**
 * Async thunk for verifying MFA code
 * Completes the multi-factor authentication process
 */
export const verifyMFACode = createAsyncThunk(
  'auth/verifyMFA',
  async (data: MFAVerification, { rejectWithValue }) => {
    try {
      const response = await verifyMFA(data);
      setAuthToken(response.token);
      return response;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

/**
 * Async thunk for initializing authentication state
 * Checks if user is already authenticated and loads profile
 */
export const initializeAuth = createAsyncThunk(
  'auth/initialize',
  async (_, { rejectWithValue }) => {
    try {
      if (isAuthenticated()) {
        try {
          const user = await getCurrentUser();
          return { isAuthenticated: true, user };
        } catch (error) {
          // If getting current user fails, remove token and consider not authenticated
          removeAuthToken();
          return { isAuthenticated: false, user: null };
        }
      }
      return { isAuthenticated: false, user: null };
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

/**
 * Redux slice for authentication state
 */
export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    // Login
    builder
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.mfaRequired = false;
        state.mfaToken = null;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload ? String(action.payload) : action.error.message || null;
        
        // Check if MFA is required from the error response
        const payload = action.payload as any;
        if (payload && typeof payload === 'object' && 'mfa_required' in payload) {
          state.mfaRequired = true;
          state.mfaToken = payload.mfa_token || null;
        }
      });
    
    // Register
    builder
      .addCase(registerUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.token = action.payload.token;
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload ? String(action.payload) : action.error.message || null;
      });
    
    // Logout
    builder
      .addCase(logoutUser.pending, (state) => {
        state.loading = true;
      })
      .addCase(logoutUser.fulfilled, (state) => {
        // Reset to initial state on logout
        return initialState;
      })
      .addCase(logoutUser.rejected, (state) => {
        // Reset to initial state even if logout API fails
        return initialState;
      });
    
    // Refresh Token
    builder
      .addCase(refreshUserToken.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(refreshUserToken.fulfilled, (state, action) => {
        state.loading = false;
        state.token = action.payload;
      })
      .addCase(refreshUserToken.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload ? String(action.payload) : action.error.message || null;
        // If token refresh fails, consider user as not authenticated
        state.isAuthenticated = false;
        state.user = null;
      });
    
    // Fetch Current User
    builder
      .addCase(fetchCurrentUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCurrentUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload;
        state.isAuthenticated = true;
      })
      .addCase(fetchCurrentUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload ? String(action.payload) : action.error.message || null;
        state.isAuthenticated = false;
        state.user = null;
      });
    
    // Password Reset Request
    builder
      .addCase(requestPasswordResetEmail.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(requestPasswordResetEmail.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(requestPasswordResetEmail.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload ? String(action.payload) : action.error.message || null;
      });
    
    // Confirm Password Reset
    builder
      .addCase(confirmPasswordReset.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(confirmPasswordReset.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(confirmPasswordReset.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload ? String(action.payload) : action.error.message || null;
      });
    
    // MFA Verification
    builder
      .addCase(verifyMFACode.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(verifyMFACode.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.mfaRequired = false;
        state.mfaToken = null;
      })
      .addCase(verifyMFACode.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload ? String(action.payload) : action.error.message || null;
      });
    
    // Initialize Auth
    builder
      .addCase(initializeAuth.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(initializeAuth.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = action.payload.isAuthenticated;
        state.user = action.payload.user;
      })
      .addCase(initializeAuth.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload ? String(action.payload) : action.error.message || null;
        state.isAuthenticated = false;
        state.user = null;
      });
  }
});

// Type-safe interface for RootState (would normally be imported from store)
interface RootState {
  auth: AuthState;
}

// Selectors
export const selectAuth = (state: RootState) => state.auth;
export const selectIsAuthenticated = (state: RootState) => state.auth.isAuthenticated;
export const selectCurrentUser = (state: RootState) => state.auth.user;
export const selectAuthLoading = (state: RootState) => state.auth.loading;
export const selectAuthError = (state: RootState) => state.auth.error;
export const selectMFARequired = (state: RootState) => state.auth.mfaRequired;
export const selectMFAToken = (state: RootState) => state.auth.mfaToken;

// Export reducer as default
export default authSlice.reducer;