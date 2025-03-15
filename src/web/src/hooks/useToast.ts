import { useCallback } from 'react'; // react v18.0.0
import { ToastOptions } from 'react-toastify'; // react-toastify v9.0.0
import { APP_CONFIG } from '../constants/appConfig';
import {
  showSuccessNotification,
  showErrorNotification,
  showWarningNotification,
  showInfoNotification,
  dismissNotification,
  dismissAllNotifications,
  formatErrorMessage
} from '../utils/notifications';

/**
 * Custom hook that provides a simplified interface for displaying toast notifications
 * in the Molecular Data Management and CRO Integration Platform.
 * 
 * @returns Object containing toast notification methods
 */
const useToast = () => {
  /**
   * Displays a success toast notification
   * @param message - The success message to display
   * @param options - Optional toast configuration options
   * @returns The toast ID that can be used for programmatic dismissal
   */
  const success = useCallback((message: string, options?: ToastOptions): number | string => {
    return showSuccessNotification(message, options);
  }, []);

  /**
   * Displays an error toast notification
   * @param message - The error message to display
   * @param options - Optional toast configuration options
   * @returns The toast ID that can be used for programmatic dismissal
   */
  const error = useCallback((message: string, options?: ToastOptions): number | string => {
    return showErrorNotification(message, options);
  }, []);

  /**
   * Displays a warning toast notification
   * @param message - The warning message to display
   * @param options - Optional toast configuration options
   * @returns The toast ID that can be used for programmatic dismissal
   */
  const warning = useCallback((message: string, options?: ToastOptions): number | string => {
    return showWarningNotification(message, options);
  }, []);

  /**
   * Displays an info toast notification
   * @param message - The informational message to display
   * @param options - Optional toast configuration options
   * @returns The toast ID that can be used for programmatic dismissal
   */
  const info = useCallback((message: string, options?: ToastOptions): number | string => {
    return showInfoNotification(message, options);
  }, []);

  /**
   * Dismisses a specific toast notification by ID
   * @param toastId - The ID of the toast to dismiss
   */
  const dismiss = useCallback((toastId: number | string): void => {
    dismissNotification(toastId);
  }, []);

  /**
   * Dismisses all currently displayed toast notifications
   */
  const dismissAll = useCallback((): void => {
    dismissAllNotifications();
  }, []);

  /**
   * Formats error objects, strings, or unknown values into user-friendly error messages
   * @param error - The error object, string, or unknown value
   * @returns Formatted error message string
   */
  const formatError = useCallback((error: unknown): string => {
    return formatErrorMessage(error);
  }, []);

  return {
    success,
    error,
    warning,
    info,
    dismiss,
    dismissAll,
    formatError
  };
};

export default useToast;