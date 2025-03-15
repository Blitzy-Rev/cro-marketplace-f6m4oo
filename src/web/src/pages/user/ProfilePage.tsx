import React, { useState, useCallback, useEffect } from 'react'; // react ^18.0.0
import { Box, Paper, Typography, TextField, Button, Grid, Divider, Tab, Tabs, CircularProgress, InputAdornment, IconButton } from '@mui/material'; // @mui/material ^5.0.0
import { Visibility, VisibilityOff, Save, Lock } from '@mui/icons-material'; // @mui/icons-material ^5.0.0

import DashboardLayout from '../../components/layout/DashboardLayout';
import { useAuthContext } from '../../contexts/AuthContext';
import { updateCurrentUser, changePassword } from '../../api/userApi';
import { UserUpdate, PasswordChange } from '../../types/user.types';
import AlertDialog from '../../components/common/AlertDialog';
import { validateRequired, validateEmail, validateStringLength } from '../../utils/validators';

/**
 * Main component for the user profile page
 * @returns The rendered profile page component
 */
const ProfilePage: React.FC = () => {
  // Get current user data from authentication context
  const { authState } = useAuthContext();
  const user = authState.user;

  // Initialize form state with current user data
  const [tabValue, setTabValue] = useState<number>(0);
  const [profileForm, setProfileForm] = useState({
    full_name: user?.full_name || '',
    email: user?.email || ''
  });
  const [profileErrors, setProfileErrors] = useState({
    full_name: null as string | null,
    email: null as string | null
  });

  // Initialize password form state
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [passwordErrors, setPasswordErrors] = useState({
    current_password: null as string | null,
    new_password: null as string | null,
    confirm_password: null as string | null
  });

  // Password visibility toggle state
  const [showPassword, setShowPassword] = useState({
    current: false,
    new: false,
    confirm: false
  });

  // Loading state for form submissions
  const [loading, setLoading] = useState<boolean>(false);

  // Alert dialog state
  const [alert, setAlert] = useState({
    open: false,
    title: '',
    message: '',
    severity: 'info' as 'info' | 'warning' | 'error' | 'success'
  });

  /**
   * Handles tab change events
   * @param event 
   * @param newValue 
   */
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  /**
   * Handles profile form input changes
   * @param event 
   */
  const handleProfileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setProfileForm(prevState => ({
      ...prevState,
      [name]: value
    }));
    setProfileErrors(prevState => ({
      ...prevState,
      [name]: null
    }));
  };

  /**
   * Handles password form input changes
   * @param event 
   */
  const handlePasswordChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setPasswordForm(prevState => ({
      ...prevState,
      [name]: value
    }));
    setPasswordErrors(prevState => ({
      ...prevState,
      [name]: null
    }));
  };

  /**
   * Toggles password field visibility
   * @param field 
   */
  const togglePasswordVisibility = (field: string) => {
    setShowPassword(prevState => ({
      ...prevState,
      [field]: !prevState[field]
    }));
  };

  /**
   * Validates profile form inputs
   * @returns Whether the form is valid
   */
  const validateProfileForm = (): boolean => {
    const fullNameResult = validateRequired(profileForm.full_name, 'Full Name');
    const emailResult = validateEmail(profileForm.email, 'Email');

    setProfileErrors({
      full_name: fullNameResult.error,
      email: emailResult.error
    });

    return fullNameResult.valid && emailResult.valid;
  };

  /**
   * Validates password form inputs
   * @returns Whether the form is valid
   */
  const validatePasswordForm = (): boolean => {
    const currentPasswordResult = validateRequired(passwordForm.current_password, 'Current Password');
    const newPasswordResult = validatePassword(passwordForm.new_password);
    const confirmPasswordResult = passwordForm.new_password === passwordForm.confirm_password
      ? { valid: true, error: null }
      : { valid: false, error: 'Confirm Password must match New Password' };

    setPasswordErrors({
      current_password: currentPasswordResult.error,
      new_password: newPasswordResult.error,
      confirm_password: confirmPasswordResult.error
    });

    return currentPasswordResult.valid && newPasswordResult.valid && confirmPasswordResult.valid;
  };

  /**
   * Handles profile form submission
   * @param event 
   */
  const handleProfileSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!validateProfileForm()) {
      return;
    }

    setLoading(true);

    try {
      const updateData: UserUpdate = {
        full_name: profileForm.full_name,
        email: profileForm.email
      };
      await updateCurrentUser(updateData);
      setAlert({
        open: true,
        title: 'Profile Updated',
        message: 'Your profile has been updated successfully.',
        severity: 'success'
      });
    } catch (error) {
      setAlert({
        open: true,
        title: 'Error',
        message: 'Failed to update profile. Please try again.',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handles password form submission
   * @param event 
   */
  const handlePasswordSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!validatePasswordForm()) {
      return;
    }

    setLoading(true);

    try {
      const passwordData: PasswordChange = {
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password
      };
      await changePassword(passwordData);
      setAlert({
        open: true,
        title: 'Password Changed',
        message: 'Your password has been changed successfully.',
        severity: 'success'
      });
      setPasswordForm({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
    } catch (error) {
      setAlert({
        open: true,
        title: 'Error',
        message: 'Failed to change password. Please try again.',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handles alert dialog close event
   */
  const handleAlertClose = () => {
    setAlert(prevState => ({ ...prevState, open: false }));
  };

  /**
   * Validates password against complexity requirements
   * @param password 
   * @returns 
   */
  const validatePassword = (password: string): { valid: boolean, error: string | null } => {
    const requiredCheck = validateRequired(password, 'New Password');
    if (!requiredCheck.valid) return requiredCheck;

    const lengthCheck = validateStringLength(password, 'New Password', 12);
    if (!lengthCheck.valid) return lengthCheck;

    if (!/(?=.*[a-z])/.test(password)) {
      return { valid: false, error: 'New Password must contain at least one lowercase letter' };
    }

    if (!/(?=.*[A-Z])/.test(password)) {
      return { valid: false, error: 'New Password must contain at least one uppercase letter' };
    }

    if (!/(?=.*[0-9])/.test(password)) {
      return { valid: false, error: 'New Password must contain at least one number' };
    }

    if (!/(?=.*[!@#$%^&*])/.test(password)) {
      return { valid: false, error: 'New Password must contain at least one special character' };
    }

    return { valid: true, error: null };
  };

  return (
    <DashboardLayout title="My Profile">
      <Paper elevation={2} sx={{ p: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="profile-tabs">
          <Tab label="Profile Information" />
          <Tab label="Change Password" />
        </Tabs>
        {/* Profile Information Tab */}
        {tabValue === 0 && (
          <Box component="form" onSubmit={handleProfileSubmit} mt={3}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Full Name"
                  name="full_name"
                  value={profileForm.full_name}
                  onChange={handleProfileChange}
                  error={!!profileErrors.full_name}
                  helperText={profileErrors.full_name}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Email"
                  name="email"
                  value={profileForm.email}
                  onChange={handleProfileChange}
                  error={!!profileErrors.email}
                  helperText={profileErrors.email}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  disabled={loading}
                  startIcon={<Save />}
                >
                  Save Profile
                  {loading && <CircularProgress size={24} sx={{ position: 'absolute', top: '50%', left: '50%', ml: -1.5 }} />}
                </Button>
              </Grid>
            </Grid>
          </Box>
        )}
        {/* Change Password Tab */}
        {tabValue === 1 && (
          <Box component="form" onSubmit={handlePasswordSubmit} mt={3}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  label="Current Password"
                  name="current_password"
                  type={showPassword.current ? 'text' : 'password'}
                  value={passwordForm.current_password}
                  onChange={handlePasswordChange}
                  error={!!passwordErrors.current_password}
                  helperText={passwordErrors.current_password}
                  required
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          aria-label="toggle password visibility"
                          onClick={() => togglePasswordVisibility('current')}
                          edge="end"
                        >
                          {showPassword.current ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    )
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="New Password"
                  name="new_password"
                  type={showPassword.new ? 'text' : 'password'}
                  value={passwordForm.new_password}
                  onChange={handlePasswordChange}
                  error={!!passwordErrors.new_password}
                  helperText={passwordErrors.new_password}
                  required
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          aria-label="toggle password visibility"
                          onClick={() => togglePasswordVisibility('new')}
                          edge="end"
                        >
                          {showPassword.new ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    )
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Confirm New Password"
                  name="confirm_password"
                  type={showPassword.confirm ? 'text' : 'password'}
                  value={passwordForm.confirm_password}
                  onChange={handlePasswordChange}
                  error={!!passwordErrors.confirm_password}
                  helperText={passwordErrors.confirm_password}
                  required
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          aria-label="toggle password visibility"
                          onClick={() => togglePasswordVisibility('confirm')}
                          edge="end"
                        >
                          {showPassword.confirm ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    )
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  disabled={loading}
                  startIcon={<Lock />}
                >
                  Change Password
                  {loading && <CircularProgress size={24} sx={{ position: 'absolute', top: '50%', left: '50%', ml: -1.5 }} />}
                </Button>
              </Grid>
            </Grid>
          </Box>
        )}
      </Paper>
      <AlertDialog
        open={alert.open}
        title={alert.title}
        message={alert.message}
        severity={alert.severity}
        onClose={handleAlertClose}
      />
    </DashboardLayout>
  );
};

/**
 * Validates password against complexity requirements
 * @param password 
 * @returns 
 */
const validatePassword = (password: string): { valid: boolean, error: string | null } => {
  const requiredCheck = validateRequired(password, 'New Password');
  if (!requiredCheck.valid) return requiredCheck;

  const lengthCheck = validateStringLength(password, 'New Password', 12);
  if (!lengthCheck.valid) return lengthCheck;

  if (!/(?=.*[a-z])/.test(password)) {
    return { valid: false, error: 'New Password must contain at least one lowercase letter' };
  }

  if (!/(?=.*[A-Z])/.test(password)) {
    return { valid: false, error: 'New Password must contain at least one uppercase letter' };
  }

  if (!/(?=.*[0-9])/.test(password)) {
    return { valid: false, error: 'New Password must contain at least one number' };
  }

  if (!/(?=.*[!@#$%^&*])/.test(password)) {
    return { valid: false, error: 'New Password must contain at least one special character' };
  }

  return { valid: true, error: null };
};

export default ProfilePage;