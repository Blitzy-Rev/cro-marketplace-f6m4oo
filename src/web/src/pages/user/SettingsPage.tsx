import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Divider,
  Tab,
  Tabs,
  CircularProgress
} from '@mui/material';
import DashboardLayout from '../../components/layout/DashboardLayout';
import { useAuthContext } from '../../contexts/AuthContext';
import { updateCurrentUser, changePassword } from '../../api/userApi';
import { UserUpdate, PasswordChange } from '../../types/user.types';
import AlertDialog from '../../components/common/AlertDialog';
import useToast from '../../hooks/useToast';

/**
 * Settings page component that allows users to manage their account settings
 * including profile information and password.
 */
const SettingsPage: React.FC = () => {
  // Access authentication context for current user info
  const { authState } = useAuthContext();

  // Access toast notification methods
  const { success, error, formatError } = useToast();

  // State for tab selection
  const [selectedTab, setSelectedTab] = useState<number>(0);

  // State for profile form
  const [profileData, setProfileData] = useState<{
    full_name: string;
    email: string;
    organization_name: string | null;
  }>({
    full_name: '',
    email: '',
    organization_name: null,
  });

  // State for password form
  const [passwordData, setPasswordData] = useState<{
    current_password: string;
    new_password: string;
    confirm_password: string;
  }>({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  // Loading state
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Alert dialog state
  const [alertDialog, setAlertDialog] = useState<{
    open: boolean;
    title: string;
    message: string;
    severity: 'info' | 'warning' | 'error';
  }>({
    open: false,
    title: '',
    message: '',
    severity: 'info',
  });

  // Initialize form data with current user information
  useEffect(() => {
    if (authState.user) {
      setProfileData({
        full_name: authState.user.full_name || '',
        email: authState.user.email || '',
        organization_name: authState.user.organization_name,
      });
    }
  }, [authState.user]);

  /**
   * Handle tab selection change between profile and security tabs
   */
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
  };

  /**
   * Handle changes to profile form input fields
   */
  const handleProfileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setProfileData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  /**
   * Handle changes to password form input fields
   */
  const handlePasswordChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setPasswordData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  /**
   * Handle profile form submission
   */
  const handleProfileSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);

    // Validate form data
    if (!validateProfileForm()) {
      setIsLoading(false);
      return;
    }

    try {
      // Create user update object
      const updateData: UserUpdate = {
        full_name: profileData.full_name,
        organization_name: profileData.organization_name,
      };

      // Call API to update user
      await updateCurrentUser(updateData);

      // Show success notification
      success('Profile updated successfully');
    } catch (err) {
      // Show error notification
      error(`Failed to update profile: ${formatError(err)}`);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle password form submission
   */
  const handlePasswordSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);

    // Validate form data
    if (!validatePasswordForm()) {
      setIsLoading(false);
      return;
    }

    try {
      // Create password change object
      const passwordChangeData: PasswordChange = {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      };

      // Call API to change password
      await changePassword(passwordChangeData);

      // Show success notification
      success('Password changed successfully');

      // Clear password form
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
    } catch (err) {
      // Show error notification
      error(`Failed to change password: ${formatError(err)}`);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Validate profile form data
   */
  const validateProfileForm = (): boolean => {
    if (!profileData.full_name.trim()) {
      // Display error alert
      setAlertDialog({
        open: true,
        title: 'Invalid Form',
        message: 'Full name is required',
        severity: 'error',
      });
      return false;
    }

    // Add more validation as needed for organization name
    return true;
  };

  /**
   * Validate password form data
   */
  const validatePasswordForm = (): boolean => {
    if (!passwordData.current_password) {
      // Display error alert
      setAlertDialog({
        open: true,
        title: 'Invalid Form',
        message: 'Current password is required',
        severity: 'error',
      });
      return false;
    }

    if (!passwordData.new_password) {
      // Display error alert
      setAlertDialog({
        open: true,
        title: 'Invalid Form',
        message: 'New password is required',
        severity: 'error',
      });
      return false;
    }

    // Check password length requirement
    if (passwordData.new_password.length < 12) {
      // Display error alert
      setAlertDialog({
        open: true,
        title: 'Invalid Form',
        message: 'New password must be at least 12 characters long',
        severity: 'error',
      });
      return false;
    }

    // Check password complexity requirements
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\da-zA-Z]).{12,}$/;
    if (!passwordRegex.test(passwordData.new_password)) {
      // Display error alert
      setAlertDialog({
        open: true,
        title: 'Invalid Form',
        message: 'New password must contain at least one uppercase letter, one lowercase letter, one number, and one special character',
        severity: 'error',
      });
      return false;
    }

    // Check if passwords match
    if (passwordData.new_password !== passwordData.confirm_password) {
      // Display error alert
      setAlertDialog({
        open: true,
        title: 'Invalid Form',
        message: 'Passwords do not match',
        severity: 'error',
      });
      return false;
    }

    return true;
  };

  return (
    <DashboardLayout title="Settings">
      <Box sx={{ width: '100%', mb: 4 }}>
        {/* Tab navigation */}
        <Tabs
          value={selectedTab}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}
        >
          <Tab label="Profile" />
          <Tab label="Security" />
        </Tabs>

        {/* Profile Tab */}
        {selectedTab === 0 && (
          <Box component="form" onSubmit={handleProfileSubmit} noValidate>
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" sx={{ mb: 3 }}>
                Personal Information
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    name="full_name"
                    label="Full Name"
                    value={profileData.full_name}
                    onChange={handleProfileChange}
                    fullWidth
                    required
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    name="email"
                    label="Email Address"
                    value={profileData.email}
                    disabled
                    fullWidth
                    helperText="Email cannot be changed"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    name="organization_name"
                    label="Organization"
                    value={profileData.organization_name || ''}
                    onChange={handleProfileChange}
                    fullWidth
                  />
                </Grid>
              </Grid>
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  disabled={isLoading}
                  startIcon={isLoading ? <CircularProgress size={20} /> : null}
                >
                  Save Changes
                </Button>
              </Box>
            </Paper>
          </Box>
        )}

        {/* Security Tab */}
        {selectedTab === 1 && (
          <Box component="form" onSubmit={handlePasswordSubmit} noValidate>
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" sx={{ mb: 3 }}>
                Change Password
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    name="current_password"
                    label="Current Password"
                    type="password"
                    value={passwordData.current_password}
                    onChange={handlePasswordChange}
                    fullWidth
                    required
                  />
                </Grid>
                <Grid item xs={12}>
                  <Divider sx={{ my: 2 }} />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    name="new_password"
                    label="New Password"
                    type="password"
                    value={passwordData.new_password}
                    onChange={handlePasswordChange}
                    fullWidth
                    required
                    helperText="Password must be at least 12 characters long and include uppercase, lowercase, number, and special character"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    name="confirm_password"
                    label="Confirm New Password"
                    type="password"
                    value={passwordData.confirm_password}
                    onChange={handlePasswordChange}
                    fullWidth
                    required
                  />
                </Grid>
              </Grid>
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  disabled={isLoading}
                  startIcon={isLoading ? <CircularProgress size={20} /> : null}
                >
                  Change Password
                </Button>
              </Box>
            </Paper>
          </Box>
        )}
      </Box>

      {/* Alert Dialog for displaying validation errors */}
      <AlertDialog
        open={alertDialog.open}
        title={alertDialog.title}
        message={alertDialog.message}
        severity={alertDialog.severity}
        onClose={() => setAlertDialog({ ...alertDialog, open: false })}
      />
    </DashboardLayout>
  );
};

export default SettingsPage;