import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, Box, Paper, Typography } from '@mui/material';
import LoginForm from '../../components/auth/LoginForm';
import Logo from '../../components/layout/Logo';
import { DASHBOARD } from '../../constants/routes';

/**
 * LoginPage component provides the user authentication interface
 * for the Molecular Data Management and CRO Integration Platform.
 * 
 * It renders a centralized login form with the application logo and branding,
 * handles authentication through the LoginForm component, and redirects to
 * the dashboard upon successful login.
 */
const LoginPage: React.FC = () => {
  // Initialize navigation for redirecting after successful login
  const navigate = useNavigate();
  
  /**
   * Handles successful login by redirecting to the dashboard
   */
  const handleLoginSuccess = (): void => {
    navigate(DASHBOARD.ROOT);
  };
  
  return (
    <Container
      maxWidth="sm"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
      }}
    >
      <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 4 }}>
          <Logo variant="default" context="sidebar" />
          <Typography variant="h5" component="h1" gutterBottom align="center" sx={{ mt: 2 }}>
            MoleculeFlow
          </Typography>
        </Box>
        
        <LoginForm 
          onSuccess={handleLoginSuccess} 
          redirectPath={DASHBOARD.ROOT} 
        />
      </Paper>
    </Container>
  );
};

export default LoginPage;