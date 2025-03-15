import React, { createContext, useState, useContext, useCallback } from 'react';
import AlertDialog from '../components/common/AlertDialog';
import { formatErrorMessage } from '../utils/errorHandler';

/**
 * Interface for the alert state
 */
interface AlertState {
  /** Whether the alert dialog is open */
  open: boolean;
  /** Title of the alert dialog */
  title: string;
  /** Content message of the alert dialog */
  message: string | React.ReactNode;
  /** Severity level of the alert */
  severity: 'error' | 'warning' | 'info' | 'success';
  /** Text for the action button */
  actionText: string;
  /** Optional callback function when alert is closed */
  onClose?: () => void;
}

/**
 * Interface for the alert context
 */
interface AlertContextType {
  /** Current state of the alert */
  alertState: AlertState;
  /** Function to show an alert with custom options */
  showAlert: (options: Omit<AlertState, 'open'>) => void;
  /** Function to hide the current alert */
  hideAlert: () => void;
  /** Function to show an error alert */
  showErrorAlert: (message: string | Error, title?: string, onClose?: () => void) => void;
  /** Function to show a success alert */
  showSuccessAlert: (message: string, title?: string, onClose?: () => void) => void;
  /** Function to show a warning alert */
  showWarningAlert: (message: string, title?: string, onClose?: () => void) => void;
  /** Function to show an info alert */
  showInfoAlert: (message: string, title?: string, onClose?: () => void) => void;
}

// Initial state for the alert
const initialAlertState: AlertState = {
  open: false,
  title: '',
  message: '',
  severity: 'info',
  actionText: 'OK'
};

// Create the alert context with undefined as default value
export const AlertContext = createContext<AlertContextType | undefined>(undefined);

/**
 * Provider component for the AlertContext
 * 
 * This component establishes a global alert system that allows displaying
 * modal alerts with different severity levels throughout the application.
 */
export const AlertProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [alertState, setAlertState] = useState<AlertState>(initialAlertState);

  // Function to show an alert with custom options
  const showAlert = useCallback((options: Omit<AlertState, 'open'>) => {
    setAlertState({ ...options, open: true });
  }, []);

  // Function to hide the current alert
  const hideAlert = useCallback(() => {
    setAlertState((prev) => ({ ...prev, open: false }));
    // Call the onClose callback if provided
    if (alertState.onClose) {
      alertState.onClose();
    }
  }, [alertState.onClose]);

  // Function to handle the alert close event
  const handleAlertClose = useCallback(() => {
    hideAlert();
  }, [hideAlert]);

  // Function to show an error alert
  const showErrorAlert = useCallback((message: string | Error, title = 'Error', onClose?: () => void) => {
    const formattedMessage = message instanceof Error ? formatErrorMessage(message) : message;
    showAlert({
      title,
      message: formattedMessage,
      severity: 'error',
      actionText: 'OK',
      onClose,
    });
  }, [showAlert]);

  // Function to show a success alert
  const showSuccessAlert = useCallback((message: string, title = 'Success', onClose?: () => void) => {
    showAlert({
      title,
      message,
      severity: 'success',
      actionText: 'OK',
      onClose,
    });
  }, [showAlert]);

  // Function to show a warning alert
  const showWarningAlert = useCallback((message: string, title = 'Warning', onClose?: () => void) => {
    showAlert({
      title,
      message,
      severity: 'warning',
      actionText: 'OK',
      onClose,
    });
  }, [showAlert]);

  // Function to show an info alert
  const showInfoAlert = useCallback((message: string, title = 'Information', onClose?: () => void) => {
    showAlert({
      title,
      message,
      severity: 'info',
      actionText: 'OK',
      onClose,
    });
  }, [showAlert]);

  // Create the context value
  const contextValue: AlertContextType = {
    alertState,
    showAlert,
    hideAlert,
    showErrorAlert,
    showSuccessAlert,
    showWarningAlert,
    showInfoAlert,
  };

  return (
    <AlertContext.Provider value={contextValue}>
      {children}
      <AlertDialog
        open={alertState.open}
        title={alertState.title}
        message={alertState.message}
        buttonText={alertState.actionText}
        onClose={handleAlertClose}
        // Map 'success' severity to 'info' as AlertDialog component doesn't support 'success'
        severity={alertState.severity === 'success' ? 'info' : alertState.severity}
      />
    </AlertContext.Provider>
  );
};

/**
 * Custom hook to access the AlertContext
 * 
 * @returns The alert context value
 * @throws Error if used outside of AlertProvider
 */
export const useAlertContext = (): AlertContextType => {
  const context = useContext(AlertContext);
  if (context === undefined) {
    throw new Error('useAlertContext must be used within an AlertProvider');
  }
  return context;
};