import React from 'react';
import { Box, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import { styled } from '@mui/material/styles';
import { useLocation, Navigate } from 'react-router-dom';

import AppLayout from './AppLayout';
import { useAuthContext } from '../../contexts/AuthContext';
import { ROUTES } from '../../constants/routes';

/**
 * Interface for the DashboardLayout props
 */
interface DashboardLayoutProps {
  /**
   * The content to be rendered in the dashboard content area
   */
  children: React.ReactNode;
  
  /**
   * The title to display in the dashboard header
   */
  title?: string;
  
  /**
   * Whether the dashboard is in a loading state
   * @default false
   */
  loading?: boolean;
}

/**
 * Styled component for the dashboard header
 */
const DashboardHeader = styled(Box)(({ theme }) => ({
  marginBottom: theme.spacing(3),
  display: 'flex',
  flexDirection: 'row',
  justifyContent: 'space-between',
  alignItems: 'center',
}));

/**
 * Styled component for the dashboard content area
 */
const DashboardContent = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isMobile',
})<{ isMobile: boolean }>(({ theme, isMobile }) => ({
  padding: isMobile ? theme.spacing(2) : theme.spacing(3),
  flexGrow: 1,
  width: '100%',
  maxWidth: '1200px',
  margin: '0 auto',
}));

/**
 * Dashboard-specific layout component that extends the AppLayout with dashboard UI elements
 * 
 * This component provides a specialized layout structure for dashboard views with appropriate
 * spacing, titling, and content organization according to the UI/UX implementation requirements.
 * It also handles authentication checks and responsive design adjustments.
 * 
 * @param props - The component props
 * @returns The rendered dashboard layout component
 */
const DashboardLayout: React.FC<DashboardLayoutProps> = ({ 
  children, 
  title, 
  loading = false 
}) => {
  // Access authentication state to check if user is logged in
  const { authState } = useAuthContext();
  
  // Get current location for redirect after login if needed
  const location = useLocation();
  
  // Get theme and media query for responsive design
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  // If user is not authenticated and not in loading state, redirect to login
  if (!authState.isAuthenticated && !authState.loading) {
    return <Navigate to={ROUTES.AUTH.LOGIN} state={{ from: location }} replace />;
  }
  
  return (
    <AppLayout loading={loading}>
      {/* Render dashboard header with title if provided */}
      {title && (
        <DashboardHeader>
          <Typography variant="h4" component="h1">
            {title}
          </Typography>
          {/* Timestamp display could be added here as shown in wireframes */}
          <Typography variant="body2" color="text.secondary">
            Last updated: {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </Typography>
        </DashboardHeader>
      )}
      
      {/* Dashboard content area with responsive padding */}
      <DashboardContent isMobile={isMobile}>
        {children}
      </DashboardContent>
    </AppLayout>
  );
};

export default DashboardLayout;