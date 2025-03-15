import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import BlockIcon from '@mui/icons-material/Block';
import { Link, useNavigate } from 'react-router-dom';
import { ROUTES } from '../../constants/routes';
import { useAuth } from '../../hooks/useAuth';

/**
 * Component that displays a 403 Access Denied error page with navigation options
 * @returns The rendered access denied page
 */
const AccessDeniedPage: React.FC = () => {
  // Get the current user information
  const { user } = useAuth();
  
  // Initialize navigate function for programmatic navigation
  const navigate = useNavigate();
  
  // Handler for the "Go Back" button
  const handleGoBack = () => {
    navigate(-1); // Navigate back in history
  };
  
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      p={3}
    >
      <Paper 
        elevation={3} 
        sx={{ 
          p: 4, 
          maxWidth: 600, 
          width: '100%', 
          textAlign: 'center',
          borderRadius: 2
        }}
      >
        {/* Access Denied Icon */}
        <BlockIcon 
          color="error" 
          sx={{ fontSize: 100, mb: 2 }} 
          aria-hidden="true" 
        />
        
        {/* Error Title */}
        <Typography variant="h4" component="h1" gutterBottom color="error" fontWeight="bold">
          403 - Access Denied
        </Typography>
        
        {/* Personalized Error Message */}
        <Typography variant="body1" paragraph>
          {user ? (
            <>
              Sorry, <strong>{user.full_name}</strong>. You don't have permission to access this resource.
            </>
          ) : (
            'Sorry, you don't have permission to access this resource.'
          )}
        </Typography>
        
        {/* Additional Guidance */}
        <Typography variant="body2" color="textSecondary" paragraph>
          If you believe you should have access, please contact your administrator
          or try logging in with a different account.
        </Typography>
        
        {/* Navigation Buttons */}
        <Box mt={4} display="flex" justifyContent="center" gap={2} flexWrap="wrap">
          <Button 
            variant="contained" 
            color="primary" 
            component={Link} 
            to={ROUTES.DASHBOARD.ROOT}
          >
            Go to Dashboard
          </Button>
          <Button 
            variant="outlined" 
            color="primary" 
            onClick={handleGoBack}
          >
            Go Back
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default AccessDeniedPage;