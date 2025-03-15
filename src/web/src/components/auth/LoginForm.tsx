import React, { useState } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom'; // ^6.4.0
import {
  TextField,
  Button,
  FormControlLabel,
  Checkbox,
  Grid,
  Typography,
  Box,
  Paper,
  InputAdornment,
  IconButton,
  CircularProgress,
  Alert
} from '@mui/material'; // ^5.0.0
import { Visibility, VisibilityOff } from '@mui/icons-material'; // ^5.0.0

import { useAuth } from '../../hooks/useAuth';
import { validateEmail, validateRequired } from '../../utils/validators';
import { LoginCredentials } from '../../types/auth.types';
import { AUTH } from '../../constants/routes';

/**
 * Props for the LoginForm component
 */
interface LoginFormProps {
  /** Callback function called after successful login */
  onSuccess?: () => void;
  /** Path to redirect to after successful login */
  redirectPath?: string;
}

/**
 * Login form component that handles user authentication including MFA verification
 * 
 * This component provides a form for users to enter their credentials, handles
 * validation, and supports multi-factor authentication when required.
 */
const LoginForm: React.FC<LoginFormProps> = ({ onSuccess, redirectPath = '/dashboard' }) => {
  // Navigation hook for redirecting after successful login
  const navigate = useNavigate();
  
  // Authentication state and functions from auth hook
  const { login, verifyMFA, mfaRequired, error, loading } = useAuth();
  
  // Form state for login credentials
  const [credentials, setCredentials] = useState<LoginCredentials>({
    email: '',
    password: '',
    remember_me: false
  });
  
  // Form validation errors
  const [errors, setErrors] = useState({
    email: null as string | null,
    password: null as string | null,
    mfaCode: null as string | null
  });
  
  // State for MFA verification code
  const [mfaCode, setMfaCode] = useState('');
  
  // State for password visibility toggle
  const [showPassword, setShowPassword] = useState(false);
  
  /**
   * Validates the login form fields
   * @returns True if form is valid, false otherwise
   */
  const validateForm = (): boolean => {
    const emailValidation = validateEmail(credentials.email, 'Email');
    const passwordValidation = validateRequired(credentials.password, 'Password');
    
    setErrors({
      ...errors,
      email: emailValidation.valid ? null : emailValidation.error,
      password: passwordValidation.valid ? null : passwordValidation.error
    });
    
    return emailValidation.valid && passwordValidation.valid;
  };
  
  /**
   * Handles form submission for login
   * @param event - Form submission event
   */
  const handleSubmit = async (event: React.FormEvent): Promise<void> => {
    event.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    try {
      const success = await login(credentials);
      
      if (success && !mfaRequired) {
        if (onSuccess) {
          onSuccess();
        } else {
          navigate(redirectPath);
        }
      }
    } catch (error) {
      // Error handling is done through the useAuth hook
      // which sets the error state automatically
    }
  };
  
  /**
   * Handles MFA verification code submission
   * @param event - Form submission event
   */
  const handleMFASubmit = async (event: React.FormEvent): Promise<void> => {
    event.preventDefault();
    
    if (!mfaCode) {
      setErrors({
        ...errors,
        mfaCode: 'Verification code is required'
      });
      return;
    }
    
    try {
      const success = await verifyMFA(mfaCode);
      
      if (success) {
        if (onSuccess) {
          onSuccess();
        } else {
          navigate(redirectPath);
        }
      }
    } catch (error) {
      // Error handling is done through the useAuth hook
    }
  };
  
  /**
   * Toggles password field visibility
   */
  const togglePasswordVisibility = (): void => {
    setShowPassword(!showPassword);
  };
  
  return (
    <Paper elevation={3} sx={{ padding: 4, maxWidth: 400, width: '100%' }}>
      <Typography variant="h5" component="h1" align="center" gutterBottom>
        Sign In
      </Typography>
      
      <form onSubmit={mfaRequired ? handleMFASubmit : handleSubmit} noValidate>
        {error && (
          <Alert severity="error" sx={{ marginBottom: 2 }}>
            {error}
          </Alert>
        )}
        
        {mfaRequired ? (
          // MFA verification form
          <>
            <TextField
              label="Verification Code"
              fullWidth
              margin="normal"
              value={mfaCode}
              onChange={(e) => setMfaCode(e.target.value)}
              error={!!errors.mfaCode}
              helperText={errors.mfaCode}
            />
            <Typography variant="body2" color="textSecondary" paragraph>
              Please enter the verification code from your authenticator app.
            </Typography>
          </>
        ) : (
          // Standard login form
          <>
            <TextField
              label="Email"
              type="email"
              fullWidth
              margin="normal"
              value={credentials.email}
              onChange={(e) => setCredentials({...credentials, email: e.target.value})}
              error={!!errors.email}
              helperText={errors.email}
            />
            
            <TextField
              label="Password"
              type={showPassword ? 'text' : 'password'}
              fullWidth
              margin="normal"
              value={credentials.password}
              onChange={(e) => setCredentials({...credentials, password: e.target.value})}
              error={!!errors.password}
              helperText={errors.password}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle password visibility"
                      onClick={togglePasswordVisibility}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            
            <FormControlLabel
              control={
                <Checkbox
                  checked={credentials.remember_me}
                  onChange={(e) => setCredentials({...credentials, remember_me: e.target.checked})}
                  color="primary"
                />
              }
              label="Remember me"
            />
          </>
        )}
        
        <Button
          type="submit"
          fullWidth
          variant="contained"
          color="primary"
          disabled={loading}
          sx={{ mt: 3, mb: 2 }}
        >
          {loading ? (
            <CircularProgress size={24} />
          ) : (
            mfaRequired ? 'Verify' : 'Sign In'
          )}
        </Button>
        
        <Grid container justifyContent="space-between">
          <Grid item>
            <RouterLink to={AUTH.PASSWORD_RESET} style={{ textDecoration: 'none' }}>
              <Typography variant="body2" color="primary">
                Forgot password?
              </Typography>
            </RouterLink>
          </Grid>
          <Grid item>
            <RouterLink to={AUTH.REGISTER} style={{ textDecoration: 'none' }}>
              <Typography variant="body2" color="primary">
                Don't have an account? Sign Up
              </Typography>
            </RouterLink>
          </Grid>
        </Grid>
      </form>
    </Paper>
  );
};

export default LoginForm;