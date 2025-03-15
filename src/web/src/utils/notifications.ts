/**
 * notifications.ts
 * 
 * Utility functions for displaying toast notifications in the Molecular Data Management and CRO Integration Platform.
 * This file provides standardized methods for showing success, error, warning, and info notifications
 * with consistent styling and behavior.
 */

import { toast, ToastOptions } from 'react-toastify'; // react-toastify v9.0.0
import { APP_CONFIG } from '../constants/appConfig';

/**
 * Displays a success toast notification
 * @param message - The message to display
 * @param options - Optional toast configuration options
 * @returns The toast ID that can be used for programmatic dismissal
 */
export const showSuccessNotification = (message: string, options: ToastOptions = {}): number | string => {
  const successOptions: ToastOptions = {
    position: 'top-right',
    autoClose: APP_CONFIG.ui.toastDuration,
    hideProgressBar: false,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
    ...options
  };
  
  return toast.success(message, successOptions);
};

/**
 * Displays an error toast notification
 * @param message - The error message to display
 * @param options - Optional toast configuration options
 * @returns The toast ID that can be used for programmatic dismissal
 */
export const showErrorNotification = (message: string, options: ToastOptions = {}): number | string => {
  const errorOptions: ToastOptions = {
    position: 'top-right',
    autoClose: APP_CONFIG.ui.toastDuration * 1.5, // Longer duration for errors
    hideProgressBar: false,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
    ...options
  };
  
  return toast.error(message, errorOptions);
};

/**
 * Displays a warning toast notification
 * @param message - The warning message to display
 * @param options - Optional toast configuration options
 * @returns The toast ID that can be used for programmatic dismissal
 */
export const showWarningNotification = (message: string, options: ToastOptions = {}): number | string => {
  const warningOptions: ToastOptions = {
    position: 'top-right',
    autoClose: APP_CONFIG.ui.toastDuration,
    hideProgressBar: false,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
    ...options
  };
  
  return toast.warning(message, warningOptions);
};

/**
 * Displays an info toast notification
 * @param message - The informational message to display
 * @param options - Optional toast configuration options
 * @returns The toast ID that can be used for programmatic dismissal
 */
export const showInfoNotification = (message: string, options: ToastOptions = {}): number | string => {
  const infoOptions: ToastOptions = {
    position: 'top-right',
    autoClose: APP_CONFIG.ui.toastDuration,
    hideProgressBar: false,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
    ...options
  };
  
  return toast.info(message, infoOptions);
};

/**
 * Dismisses a specific toast notification by ID
 * @param toastId - The ID of the toast to dismiss
 */
export const dismissNotification = (toastId: number | string): void => {
  toast.dismiss(toastId);
};

/**
 * Dismisses all currently displayed toast notifications
 */
export const dismissAllNotifications = (): void => {
  toast.dismiss();
};

/**
 * Formats error messages for consistent display in notifications
 * @param error - The error object, string, or unknown value
 * @returns Formatted error message
 */
export const formatErrorMessage = (error: unknown): string => {
  // If it's an Error object
  if (error instanceof Error) {
    return error.message;
  }
  
  // If it's a string
  if (typeof error === 'string') {
    return error;
  }
  
  // If it's an object with an error or message property
  if (error !== null && typeof error === 'object') {
    // Check for error.message
    if ('message' in error && typeof (error as { message: unknown }).message === 'string') {
      return (error as { message: string }).message;
    }
    
    // Check for error.error
    if ('error' in error) {
      const errorProp = (error as { error: unknown }).error;
      
      // If error.error is a string
      if (typeof errorProp === 'string') {
        return errorProp;
      }
      
      // If error.error is an object with a message
      if (errorProp !== null && typeof errorProp === 'object' && 
          'message' in errorProp && typeof (errorProp as { message: unknown }).message === 'string') {
        return (errorProp as { message: string }).message;
      }
    }
  }
  
  // Fallback for unknown error formats
  return 'An unexpected error occurred. Please try again or contact support.';
};