import React, { createContext, useContext, useCallback } from 'react';
import { ToastOptions } from 'react-toastify';
import ToastNotification from '../components/common/ToastNotification';
import { 
  showSuccessNotification, 
  showErrorNotification, 
  showWarningNotification, 
  showInfoNotification, 
  dismissNotification, 
  dismissAllNotifications,
  formatErrorMessage
} from '../utils/notifications';
import { APP_CONFIG } from '../constants/appConfig';

/**
 * Interface defining the shape of the notification context
 * Provides methods for displaying different types of toast notifications
 * and managing their lifecycle
 */
interface NotificationContextType {
  showSuccess: (message: string, options?: ToastOptions) => number | string;
  showError: (message: string | Error, options?: ToastOptions) => number | string;
  showWarning: (message: string, options?: ToastOptions) => number | string;
  showInfo: (message: string, options?: ToastOptions) => number | string;
  dismiss: (toastId: number | string) => void;
  dismissAll: () => void;
}

/**
 * Create the notification context with a default value of undefined
 * This will be properly initialized in the NotificationProvider
 */
export const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

/**
 * NotificationProvider component
 * 
 * Provides notification context and functionality to all child components
 * Includes ToastNotification component for displaying the actual notifications
 * 
 * @param {React.ReactNode} children - Child components that will have access to notification context
 * @returns {JSX.Element} Provider component with notification context
 */
export const NotificationProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
  /**
   * Shows a success notification with the provided message
   * @param message - The message to display
   * @param options - Optional toast configuration options
   * @returns The toast ID that can be used for programmatic dismissal
   */
  const showSuccess = useCallback((message: string, options?: ToastOptions): number | string => {
    return showSuccessNotification(message, options);
  }, []);

  /**
   * Shows an error notification with the provided message
   * @param message - The error message or Error object to display
   * @param options - Optional toast configuration options
   * @returns The toast ID that can be used for programmatic dismissal
   */
  const showError = useCallback((message: string | Error, options?: ToastOptions): number | string => {
    const formattedMessage = message instanceof Error
      ? formatErrorMessage(message)
      : message;
    return showErrorNotification(formattedMessage, options);
  }, []);

  /**
   * Shows a warning notification with the provided message
   * @param message - The warning message to display
   * @param options - Optional toast configuration options
   * @returns The toast ID that can be used for programmatic dismissal
   */
  const showWarning = useCallback((message: string, options?: ToastOptions): number | string => {
    return showWarningNotification(message, options);
  }, []);

  /**
   * Shows an info notification with the provided message
   * @param message - The informational message to display
   * @param options - Optional toast configuration options
   * @returns The toast ID that can be used for programmatic dismissal
   */
  const showInfo = useCallback((message: string, options?: ToastOptions): number | string => {
    return showInfoNotification(message, options);
  }, []);

  /**
   * Dismisses a specific notification by ID
   * @param toastId - The ID of the toast to dismiss
   */
  const dismiss = useCallback((toastId: number | string): void => {
    dismissNotification(toastId);
  }, []);

  /**
   * Dismisses all currently displayed notifications
   */
  const dismissAll = useCallback((): void => {
    dismissAllNotifications();
  }, []);

  // Create the context value object with all notification functions
  const contextValue: NotificationContextType = {
    showSuccess,
    showError,
    showWarning,
    showInfo,
    dismiss,
    dismissAll
  };

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
      <ToastNotification />
    </NotificationContext.Provider>
  );
};

/**
 * Custom hook to use the notification context
 * 
 * @returns The notification context value with all notification functions
 * @throws Error if used outside of NotificationProvider
 */
export const useNotificationContext = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  
  if (context === undefined) {
    throw new Error('useNotificationContext must be used within a NotificationProvider');
  }
  
  return context;
};