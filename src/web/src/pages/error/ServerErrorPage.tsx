import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import { Link, useNavigate } from 'react-router-dom';
import { ROUTES } from '../../constants/routes';

/**
 * Component that displays a 500 Server Error page with recovery options
 * @returns The rendered server error page
 */
const ServerErrorPage: React.FC = () => {
  const navigate = useNavigate();

  // Handler for the "Go Back" button
  const handleGoBack = () => {
    navigate(-1); // Navigate to the previous page in history
  };

  // Handler for the "Refresh Page" button
  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        p: 3
      }}
      role="alert"
      aria-labelledby="server-error-title"
    >
      <Paper
        elevation={3}
        sx={{
          p: 4,
          maxWidth: 500,
          textAlign: 'center',
          borderRadius: 2
        }}
      >
        <ErrorOutlineIcon
          color="error"
          sx={{ fontSize: 72, mb: 2 }}
          aria-hidden="true"
        />
        
        <Typography 
          variant="h4" 
          component="h1" 
          gutterBottom
          color="error"
          id="server-error-title"
        >
          500 - Server Error
        </Typography>
        
        <Typography variant="body1" paragraph>
          We're sorry, but something went wrong on our server. This is not your fault, and our technical team has been notified.
        </Typography>
        
        <Typography variant="body1" paragraph>
          You can try the following actions to recover:
        </Typography>
        
        <Box sx={{ 
          mt: 3, 
          display: 'flex', 
          flexDirection: { xs: 'column', sm: 'row' }, 
          justifyContent: 'center', 
          gap: 2 
        }}>
          <Button 
            component={Link} 
            to={ROUTES.DASHBOARD.ROOT} 
            variant="contained" 
            color="primary"
          >
            Return to Dashboard
          </Button>
          
          <Button 
            variant="outlined" 
            color="primary" 
            onClick={handleGoBack}
          >
            Go Back
          </Button>
          
          <Button 
            variant="outlined" 
            color="primary" 
            onClick={handleRefresh}
          >
            Refresh Page
          </Button>
        </Box>
        
        <Typography variant="body2" sx={{ mt: 4 }}>
          If this problem persists, please contact our support team at{' '}
          <Link 
            href="mailto:support@moleculeflow.com"
            sx={{ fontWeight: 'medium' }}
          >
            support@moleculeflow.com
          </Link>.
        </Typography>
      </Paper>
    </Box>
  );
};

export default ServerErrorPage;