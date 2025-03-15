import React from 'react'; // React v18.0.0
import { BrowserRouter } from 'react-router-dom'; // react-router-dom v6.4.0

// Internal imports
import RouteConfig from './RouteConfig';

/**
 * Main routing component that wraps the RouteConfig with BrowserRouter
 * @returns {JSX.Element} The complete routing structure wrapped with BrowserRouter
 */
const AppRoutes: React.FC = () => {
  // IE1: Wrap the RouteConfig component with BrowserRouter to enable client-side routing
  return (
    <BrowserRouter>
      {/* IE1: Import the route configuration component that defines all application routes */}
      <RouteConfig />
    </BrowserRouter>
  );
};

// IE3: Export the main routing component for use in the App component
export default AppRoutes;