import React from 'react'; // React v18.0.0
import { Provider } from 'react-redux'; // react-redux v8.0.0
import { store } from './store';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';

// Internal imports
import AppRoutes from './routes';
import { ThemeProvider as CustomThemeProvider } from './contexts/ThemeContext';
import { AuthProvider } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { AlertProvider } from './contexts/AlertContext';
import ToastNotification from './components/common/ToastNotification';
import AlertDialog from './components/common/AlertDialog';
import ErrorBoundary from './components/common/ErrorBoundary';

/**
 * Main application component that sets up the application structure
 * @returns {JSX.Element} The rendered application with all providers and routes
 */
const App: React.FC = () => {
  // LD1: Wrap the entire application with ErrorBoundary to catch and handle React errors
  return (
    <ErrorBoundary>
      {/* LD1: Provide Redux store using Provider component */}
      <Provider store={store}>
        {/* LD1: Provide theme context using ThemeProvider */}
        <CustomThemeProvider>
          <CssBaseline />
          {/* LD1: Provide authentication context using AuthProvider */}
          <AuthProvider>
            {/* LD1: Provide notification context using NotificationProvider */}
            <NotificationProvider>
              {/* LD1: Provide alert context using AlertProvider */}
              <AlertProvider>
                {/* LD1: Render the AppRoutes component for application routing */}
                <AppRoutes />
                {/* LD1: Render the ToastNotification component for toast notifications */}
                <ToastNotification />
                {/* LD1: Render the AlertDialog component for modal alerts */}
                <AlertDialog />
              </AlertProvider>
            </NotificationProvider>
          </AuthProvider>
        </CustomThemeProvider>
      </Provider>
    </ErrorBoundary>
  );
};

// IE3: Export the main routing component for use in the App component
export default App;