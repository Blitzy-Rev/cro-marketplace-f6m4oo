import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Box, CssBaseline } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material';
import { styled } from '@mui/material/styles';
import { useLocation } from 'react-router-dom';

import Header from './Header';
import Sidebar from './Sidebar';
import Footer from './Footer';
import LoadingOverlay from '../common/LoadingOverlay';
import { useAuthContext } from '../../contexts/AuthContext';
import { selectSidebarOpen, toggleSidebar } from '../../features/ui/uiSlice';

/**
 * Interface for the AppLayout props
 */
interface AppLayoutProps {
  /**
   * The content to be rendered in the main content area
   */
  children: React.ReactNode;
  
  /**
   * Whether the application is in a loading state
   */
  loading?: boolean;
}

/**
 * Styled component for the main content area
 */
const MainContent = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'open' && prop !== 'isMobile',
})<{ open: boolean; isMobile: boolean }>(({ theme, open, isMobile }) => ({
  flexGrow: 1,
  padding: theme.spacing(3),
  transition: theme.transitions.create('margin', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  marginLeft: isMobile ? 0 : (open ? 240 : 64), // Adjust margin based on sidebar state
  minHeight: 'calc(100vh - 64px - 48px)', // Adjust for header and footer heights
  display: 'flex',
  flexDirection: 'column',
}));

/**
 * Styled component for the overall layout container
 */
const LayoutContainer = styled(Box)({
  display: 'flex',
  flexDirection: 'column',
  minHeight: '100vh',
  width: '100%',
});

/**
 * Main layout component that provides the structure for all pages
 */
const AppLayout: React.FC<AppLayoutProps> = ({ children, loading = false }) => {
  // Access authentication state
  const { authState } = useAuthContext();

  // Access sidebar state from Redux
  const sidebarOpen = useSelector(selectSidebarOpen);
  const dispatch = useDispatch();

  // Get theme and media query for responsive design
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Determine if sidebar should be permanent or temporary
  const sidebarVariant = isMobile ? 'temporary' : 'permanent';

  // Handler for toggling sidebar
  const handleToggleSidebar = () => {
    dispatch(toggleSidebar());
  };

  // Handler for closing sidebar (for mobile view)
  const handleCloseSidebar = () => {
    if (sidebarOpen) {
      dispatch(toggleSidebar());
    }
  };

  // Get current location
  const location = useLocation();

  // Close sidebar on location change in mobile view
  useEffect(() => {
    if (isMobile && sidebarOpen) {
      dispatch(toggleSidebar());
    }
  }, [location, isMobile, sidebarOpen, dispatch]);

  // If user is not authenticated, don't render the layout structure
  // Just render the children (login page, etc.)
  if (!authState.isAuthenticated && !authState.loading) {
    return <>{children}</>;
  }

  return (
    <LayoutContainer>
      <CssBaseline />
      
      {/* Header with app logo, navigation controls, and user menu */}
      <Header onMenuToggle={handleToggleSidebar} />
      
      {/* Sidebar with navigation options based on user role */}
      <Sidebar 
        open={sidebarOpen} 
        onClose={handleCloseSidebar} 
        variant={sidebarVariant}
      />
      
      {/* Main content area with loading overlay */}
      <MainContent open={sidebarOpen} isMobile={isMobile}>
        <LoadingOverlay loading={loading || authState.loading}>
          {children}
        </LoadingOverlay>
      </MainContent>
      
      {/* Footer with copyright information and links */}
      <Footer />
    </LayoutContainer>
  );
};

export default AppLayout;