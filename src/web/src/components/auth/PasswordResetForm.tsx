import React, { useState } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom'; // ^6.4.0
import {
  TextField,
  Button,
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
import { validateEmail, validateRequired, validateStringLength } from '../../utils/validators';
import { PasswordResetConfirm } from '../../types/auth.types';
import { AUTH } from '../../constants/routes';

/**
 * Props for the PasswordResetForm component
 */
interface PasswordResetFormProps {
  /** Reset token for password confirmation mode */
  token?: string;
  /** Callback function called after successful password reset */
  onSuccess?: () => void;
  /** Path to redirect to after successful password reset */
  redirectPath?: string;
}

/**
 * A form component that handles password reset functionality for the
 * Molecular Data Management and CRO Integration Platform.
 * 
 * This component provides two modes:
 * - Request mode: For initiating a password reset via email (no token)
 * - Confirm mode: For setting a new password using a reset token
 */
const PasswordResetForm: React.FC<PasswordResetFormProps> = ({
  token,
  onSuccess,
  redirectPath
}) => {
  const navigate = useNavigate();
  const { resetPassword, confirmPasswordReset, loading, error } = useAuth();

  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState({
    email: null as string | null,
    password: null as string | null,
    confirmPassword: null as string | null
  });
  const [showPassword, setShowPassword] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  /**
   * Toggles password field visibility
   */
  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  /**
   * Handles form submission for password reset request
   * @param event Form submission event
   */
  const handleRequestSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    // Validate email
    const emailValidation = validateEmail(email, 'Email');
    if (!emailValidation.valid) {
      setErrors({ ...errors, email: emailValidation.error });
      return;
    }

    try {
      // Call API to request password reset
      await resetPassword(email);
      
      // Set success message
      setSuccessMessage('Password reset link has been sent to your email address.');
      
      // Clear form
      setEmail('');
      setErrors({ email: null, password: null, confirmPassword: null });
    } catch (err) {
      // Error handling is done via the useAuth hook which sets the error state
    }
  };

  /**
   * Handles form submission for password reset confirmation
   * @param event Form submission event
   */
  const handleConfirmSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    // Validate password
    const passwordValidation = validatePassword(password);
    if (!passwordValidation.valid) {
      setErrors({ ...errors, password: passwordValidation.error });
      return;
    }

    // Validate confirm password
    if (password !== confirmPassword) {
      setErrors({ 
        ...errors, 
        confirmPassword: 'Passwords do not match' 
      });
      return;
    }

    try {
      if (!token) {
        throw new Error('Reset token is missing');
      }

      // Create confirmation object
      const resetConfirm: PasswordResetConfirm = {
        token,
        new_password: password
      };
      
      // Call API to confirm password reset
      await confirmPasswordReset(resetConfirm);
      
      // Handle success
      if (onSuccess) {
        onSuccess();
      } else if (redirectPath) {
        navigate(redirectPath);
      } else {
        navigate(AUTH.LOGIN);
      }
    } catch (err) {
      // Error handling is done via the useAuth hook which sets the error state
    }
  };

  /**
   * Validates password against complexity requirements
   * @param password Password to validate
   * @returns Validation result with valid flag and error message if invalid
   */
  const validatePassword = (password: string): { valid: boolean, error: string | null } => {
    // Check if password is required
    const requiredCheck = validateRequired(password, 'Password');
    if (!requiredCheck.valid) {
      return requiredCheck;
    }

    // Check password length
    const lengthCheck = validateStringLength(password, 'Password', 12);
    if (!lengthCheck.valid) {
      return lengthCheck;
    }

    // Check for uppercase letter
    if (!/[A-Z]/.test(password)) {
      return { valid: false, error: 'Password must include at least one uppercase letter' };
    }

    // Check for lowercase letter
    if (!/[a-z]/.test(password)) {
      return { valid: false, error: 'Password must include at least one lowercase letter' };
    }

    // Check for number
    if (!/\d/.test(password)) {
      return { valid: false, error: 'Password must include at least one number' };
    }

    // Check for special character
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      return { valid: false, error: 'Password must include at least one special character' };
    }

    return { valid: true, error: null };
  };

  return (
    <Paper elevation={3} sx={{ padding: 4, maxWidth: 400, width: '100%' }}>
      <Typography variant="h5" component="h1" align="center" gutterBottom>
        {token ? 'Reset Your Password' : 'Forgot Password?'}
      </Typography>

      {error && (
        <Alert severity="error" sx={{ marginBottom: 2 }} style={{ display: error ? 'flex' : 'none' }}>
          {error}
        </Alert>
      )}

      {successMessage && (
        <Alert severity="success" sx={{ marginBottom: 2 }} style={{ display: successMessage ? 'flex' : 'none' }}>
          {successMessage}
        </Alert>
      )}

      <form onSubmit={token ? handleConfirmSubmit : handleRequestSubmit} noValidate>
        {!token ? (
          <>
            <TextField
              label="Email"
              type="email"
              fullWidth
              margin="normal"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={!!errors.email}
              helperText={errors.email}
            />
            <Typography variant="body2" color="textSecondary" paragraph sx={{ mt: 1 }}>
              Enter your email address and we'll send you a link to reset your password.
            </Typography>
          </>
        ) : (
          <>
            <TextField
              label="New Password"
              type={showPassword ? 'text' : 'password'}
              fullWidth
              margin="normal"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
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
            <TextField
              label="Confirm Password"
              type={showPassword ? 'text' : 'password'}
              fullWidth
              margin="normal"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              error={!!errors.confirmPassword}
              helperText={errors.confirmPassword}
            />
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              Password must be at least 12 characters and include uppercase, lowercase, number, and special character.
            </Typography>
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
            token ? 'Reset Password' : 'Send Reset Link'
          )}
        </Button>

        <Grid container justifyContent="center">
          <Grid item>
            <RouterLink to={AUTH.LOGIN} style={{ textDecoration: 'none' }}>
              <Typography variant="body2" color="primary">
                Back to Login
              </Typography>
            </RouterLink>
          </Grid>
        </Grid>
      </form>
    </Paper>
  );
};

export default PasswordResetForm;