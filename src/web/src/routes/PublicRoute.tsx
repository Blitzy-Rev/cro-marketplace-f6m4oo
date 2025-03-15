import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { ROUTES } from '../constants/routes';
import LoadingOverlay from '../components/common/LoadingOverlay';

/**
 * Props for the PublicRoute component
 */
interface PublicRouteProps {
  /**
   * Optional path to redirect authenticated users to
   */
  redirectPath?: string;
}

/**
 * Component that renders child routes only if the user is not authenticated,
 * otherwise redirects to dashboard or a specified path.
 * 
 * This component is used to protect public routes like login and registration
 * from being accessed by authenticated users, improving user experience by
 * automatically redirecting them to the appropriate protected area.
 */
const PublicRoute: React.FC<PublicRouteProps> = ({ redirectPath }) => {
  // Get authentication state from auth hook
  const { isAuthenticated, loading } = useAuth();

  // Show loading overlay while authentication state is being determined
  if (loading) {
    return <LoadingOverlay loading={true} message="Checking authentication status..." />;
  }

  // If user is authenticated, redirect to dashboard or specified path
  if (isAuthenticated) {
    return <Navigate to={redirectPath || ROUTES.DASHBOARD.ROOT} replace />;
  }

  // Otherwise, render the child routes
  return <Outlet />;
};

export default PublicRoute;