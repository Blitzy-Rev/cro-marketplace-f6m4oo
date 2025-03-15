import React, { useState } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom'; // ^6.4.0
import {
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Typography,
  Box,
  Paper,
  InputAdornment,
  IconButton,
  CircularProgress,
  Alert,
  FormHelperText
} from '@mui/material'; // ^5.0.0
import { Visibility, VisibilityOff } from '@mui/icons-material'; // ^5.0.0
import { useAuth } from '../../hooks/useAuth';
import { validateEmail, validateRequired, validateStringLength } from '../../utils/validators';
import { RegistrationData } from '../../types/auth.types';
import { AUTH } from '../../constants/routes';
import { PHARMA_ROLES, CRO_ROLES } from '../../constants/userRoles';

/**
 * Props for the RegisterForm component
 */
interface RegisterFormProps {
  /**
   * Callback function called after successful registration
   */
  onSuccess?: () => void;
  
  /**
   * Path to redirect to after successful registration
   */
  redirectPath?: string;
}

/**
 * A form component that handles user registration for the Molecular Data Management 
 * and CRO Integration Platform.
 * 
 * This component collects user information including email, password, full name, 
 * organization name, and role, validates the inputs, and handles the registration process.
 */
const RegisterForm: React.FC<RegisterFormProps> = ({ onSuccess, redirectPath }) => {
  const navigate = useNavigate();
  const { register, error, loading } = useAuth();
  
  // Form state
  const [formData, setFormData] = useState<RegistrationData>({
    email: '',
    password: '',
    full_name: '',
    organization_name: '',
    role: ''
  });
  
  // Form errors state
  const [errors, setErrors] = useState({
    email: null as string | null,
    password: null as string | null,
    full_name: null as string | null,
    organization_name: null as string | null,
    role: null as string | null
  });
  
  // Password visibility state
  const [showPassword, setShowPassword] = useState(false);
  
  // Role type state (pharma or cro)
  const [roleType, setRoleType] = useState('pharma');
  
  /**
   * Toggles password field visibility
   */
  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };
  
  /**
   * Handles change in role type selection (Pharma or CRO)
   */
  const handleRoleTypeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRoleType(event.target.value);
    // Reset role selection when changing role type
    setFormData({
      ...formData,
      role: ''
    });
    // Clear role validation error when changing role type
    setErrors({
      ...errors,
      role: null
    });
  };
  
  /**
   * Handles change in specific role selection
   */
  const handleRoleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      role: event.target.value
    });
    // Clear role validation error when selecting a role
    setErrors({
      ...errors,
      role: null
    });
  };
  
  /**
   * Validates form inputs before submission
   * @returns True if form is valid, false otherwise
   */
  const validateForm = (): boolean => {
    const newErrors = {
      email: null as string | null,
      password: null as string | null,
      full_name: null as string | null,
      organization_name: null as string | null,
      role: null as string | null
    };
    
    // Validate email
    const emailValidation = validateEmail(formData.email, 'Email');
    if (!emailValidation.valid) {
      newErrors.email = emailValidation.error;
    }
    
    // Validate password (minimum 8 characters)
    const passwordValidation = validateStringLength(formData.password, 'Password', 8);
    if (!passwordValidation.valid) {
      newErrors.password = passwordValidation.error;
    }
    
    // Validate full name
    const fullNameValidation = validateRequired(formData.full_name, 'Full name');
    if (!fullNameValidation.valid) {
      newErrors.full_name = fullNameValidation.error;
    }
    
    // Validate organization name
    const organizationValidation = validateRequired(formData.organization_name, 'Organization name');
    if (!organizationValidation.valid) {
      newErrors.organization_name = organizationValidation.error;
    }
    
    // Validate role
    const roleValidation = validateRequired(formData.role, 'Role');
    if (!roleValidation.valid) {
      newErrors.role = roleValidation.error;
    }
    
    // Update error state
    setErrors(newErrors);
    
    // Form is valid if there are no errors
    return !Object.values(newErrors).some(error => error !== null);
  };
  
  /**
   * Handles form submission for registration
   */
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    // Validate the form
    if (!validateForm()) {
      return;
    }
    
    try {
      // Call register function from useAuth hook
      await register(formData);
      
      // If onSuccess callback is provided, call it
      if (onSuccess) {
        onSuccess();
      } 
      // Otherwise, navigate to redirectPath or default to dashboard
      else if (redirectPath) {
        navigate(redirectPath);
      }
    } catch (err) {
      // Error handling is managed by the useAuth hook
      console.error('Registration error:', err);
    }
  };
  
  return (
    <Paper elevation={3} sx={{ padding: 4, maxWidth: 500, width: '100%' }}>
      <Typography variant="h5" component="h1" align="center" gutterBottom>
        Create Account
      </Typography>
      
      <form onSubmit={handleSubmit} noValidate>
        {/* Display error message if registration fails */}
        {error && (
          <Alert severity="error" sx={{ marginBottom: 2 }}>
            {error}
          </Alert>
        )}
        
        <TextField
          label="Email"
          type="email"
          fullWidth
          margin="normal"
          value={formData.email}
          onChange={e => setFormData({ ...formData, email: e.target.value })}
          error={!!errors.email}
          helperText={errors.email}
        />
        
        <TextField
          label="Password"
          type={showPassword ? 'text' : 'password'}
          fullWidth
          margin="normal"
          value={formData.password}
          onChange={e => setFormData({ ...formData, password: e.target.value })}
          error={!!errors.password}
          helperText={errors.password}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={togglePasswordVisibility}
                  edge="end"
                  aria-label="toggle password visibility"
                >
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
        
        <TextField
          label="Full Name"
          fullWidth
          margin="normal"
          value={formData.full_name}
          onChange={e => setFormData({ ...formData, full_name: e.target.value })}
          error={!!errors.full_name}
          helperText={errors.full_name}
        />
        
        <TextField
          label="Organization Name"
          fullWidth
          margin="normal"
          value={formData.organization_name}
          onChange={e => setFormData({ ...formData, organization_name: e.target.value })}
          error={!!errors.organization_name}
          helperText={errors.organization_name}
        />
        
        <FormControl fullWidth margin="normal">
          <InputLabel id="role-type-label">Organization Type</InputLabel>
          <Select
            labelId="role-type-label"
            value={roleType}
            onChange={handleRoleTypeChange}
            label="Organization Type"
          >
            <MenuItem value="pharma">Pharmaceutical Company</MenuItem>
            <MenuItem value="cro">Contract Research Organization (CRO)</MenuItem>
          </Select>
        </FormControl>
        
        <FormControl fullWidth margin="normal" error={!!errors.role}>
          <InputLabel id="role-label">Role</InputLabel>
          <Select
            labelId="role-label"
            value={formData.role}
            onChange={handleRoleChange}
            label="Role"
          >
            {roleType === 'pharma' ? (
              PHARMA_ROLES.map(role => (
                <MenuItem key={role} value={role}>
                  {role === 'pharma_admin' ? 'Pharmaceutical Administrator' : 'Pharmaceutical Scientist'}
                </MenuItem>
              ))
            ) : (
              CRO_ROLES.map(role => (
                <MenuItem key={role} value={role}>
                  {role === 'cro_admin' ? 'CRO Administrator' : 'CRO Technician'}
                </MenuItem>
              ))
            )}
          </Select>
          {errors.role && <FormHelperText>{errors.role}</FormHelperText>}
        </FormControl>
        
        <Button
          type="submit"
          fullWidth
          variant="contained"
          color="primary"
          disabled={loading}
          sx={{ mt: 3, mb: 2 }}
        >
          {loading ? <CircularProgress size={24} /> : 'Register'}
        </Button>
        
        <Grid container justifyContent="center">
          <Grid item>
            <RouterLink to={AUTH.LOGIN}>
              Already have an account? Sign In
            </RouterLink>
          </Grid>
        </Grid>
      </form>
    </Paper>
  );
};

export default RegisterForm;