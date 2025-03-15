import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import SearchOffIcon from '@mui/icons-material/SearchOff';
import { Link, useNavigate } from 'react-router-dom';
import { ROUTES } from '../../constants/routes';

/**
 * NotFoundPage component displays a 404 error page when users navigate to a non-existent route.
 * It provides clear feedback and navigation options to help users recover from this error state.
 */
const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  /**
   * Handles navigation back to the previous page in history
   */
  const handleGoBack = () => {
    navigate(-1);
  };

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: 'calc(100vh - 64px)', // Accounting for header height
        padding: 3,
      }}
      role="main"
      aria-labelledby="not-found-title"
    >
      <Paper
        elevation={3}
        sx={{
          maxWidth: 600,
          width: '100%',
          padding: 4,
          textAlign: 'center',
        }}
      >
        <SearchOffIcon
          sx={{
            fontSize: 100,
            color: 'primary.main',
            mb: 2,
          }}
          aria-hidden="true"
        />
        <Typography
          variant="h4"
          component="h1"
          gutterBottom
          fontWeight="bold"
          id="not-found-title"
        >
          404 - Page Not Found
        </Typography>
        <Typography variant="body1" paragraph>
          The page you are looking for doesn't exist or has been moved.
          Please check the URL or use the navigation options below.
        </Typography>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            gap: 2,
            mb: 3,
            flexWrap: 'wrap',
          }}
        >
          <Button
            variant="contained"
            color="primary"
            component={Link}
            to={ROUTES.DASHBOARD.ROOT}
            aria-label="Return to dashboard"
          >
            Go to Dashboard
          </Button>
          <Button
            variant="outlined"
            color="primary"
            onClick={handleGoBack}
            aria-label="Return to previous page"
          >
            Go Back
          </Button>
        </Box>
        <Typography variant="body2" color="text.secondary">
          If you followed a link to get here, please report this issue to help us improve our application.
          You can also try searching for what you're looking for from the dashboard.
        </Typography>
      </Paper>
    </Box>
  );
};

export default NotFoundPage;