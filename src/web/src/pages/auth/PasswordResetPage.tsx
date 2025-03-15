import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Box, Container, Paper, Typography } from '@mui/material';
import PasswordResetForm from '../../components/auth/PasswordResetForm';
import { AUTH } from '../../constants/routes';

/**
 * Page component for password reset functionality in the Molecular Data Management and CRO Integration Platform.
 * This page handles both password reset request and confirmation flows based on the presence of a token in the URL.
 */
const PasswordResetPage: React.FC = () => {
  const navigate = useNavigate();
  // Get URL search parameters to extract reset token if present
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  /**
   * Callback function executed after successful password reset
   * Navigates the user to the login page
   */
  const onSuccess = () => {
    navigate(AUTH.LOGIN);
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Typography component="h1" variant="h4" align="center" gutterBottom>
          {token ? 'Reset Your Password' : 'Forgot Password?'}
        </Typography>
        
        <PasswordResetForm
          token={token || undefined}
          onSuccess={onSuccess}
          redirectPath={AUTH.LOGIN}
        />
      </Box>
    </Container>
  );
};

export default PasswordResetPage;