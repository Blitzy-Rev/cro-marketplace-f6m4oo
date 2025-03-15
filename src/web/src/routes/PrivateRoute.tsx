import React from 'react'; // ^18.0.0
import { Navigate, Outlet } from 'react-router-dom'; // ^6.4.0
import { useAuth } from '../hooks/useAuth';
import { ROUTES } from '../constants/routes';
import LoadingOverlay from '../components/common/LoadingOverlay';

/**
 * Props for the PrivateRoute component
 */
interface PrivateRouteProps {
  /**
   * Role(s) required to access this route
   */
  requiredRoles?: string | string[];
  
  /**
   * Path to redirect unauthenticated users to
   * @default ROUTES.AUTH.LOGIN
   */
  redirectPath?: string;
}

/**
 * Component that renders child routes only if the user is authenticated and has the required role permissions.
 * Enforces authentication and role-based access control at the route level.
 * 
 * @param props - Component props including required roles and redirect path
 * @returns Either redirects to login/access denied or renders child routes using Outlet
 */
const PrivateRoute: React.FC<PrivateRouteProps> = ({
  requiredRoles,
  redirectPath = ROUTES.AUTH.LOGIN,
}) => {
  // Get authentication state and user information from useAuth hook
  const { isAuthenticated, loading, user, hasPermission } = useAuth();

  // Show loading indicator while authentication state is being determined
  if (loading) {
    return <LoadingOverlay loading={true} message="Verifying authentication..." />;
  }

  // Redirect to login page if user is not authenticated
  if (!isAuthenticated) {
    return <Navigate to={redirectPath} replace />;
  }

  // Check if requiredRoles are specified and user has necessary permissions
  if (requiredRoles && !hasPermission(requiredRoles)) {
    // Redirect to access denied page if user doesn't have required role permissions
    return <Navigate to={ROUTES.ERROR.ACCESS_DENIED} replace />;
  }

  // Render the child routes if authentication and permission checks pass
  return <Outlet />;
};

export default PrivateRoute;