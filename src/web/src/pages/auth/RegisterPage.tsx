import React from 'react';
import { useNavigate } from 'react-router-dom'; // ^6.4.0
import { Container, Box } from '@mui/material'; // ^5.0.0
import RegisterForm from '../../components/auth/RegisterForm';
import { DASHBOARD } from '../../constants/routes';

/**
 * Registration page component for the Molecular Data Management and CRO Integration Platform.
 * Provides a container for the registration form and handles navigation after successful registration.
 */
const RegisterPage: React.FC = () => {
  const navigate = useNavigate();

  /**
   * Handles successful registration by navigating to the dashboard
   */
  const handleRegistrationSuccess = () => {
    navigate(DASHBOARD.HOME);
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          py: 4
        }}
      >
        <RegisterForm 
          onSuccess={handleRegistrationSuccess} 
          redirectPath={DASHBOARD.HOME} 
        />
      </Box>
    </Container>
  );
};

export default RegisterPage;