import { AxiosError } from 'axios'; // v1.4.0
import { ApiError, ApiErrorCode } from '../types/api.types';

/**
 * Type guard to check if an error is an API error
 * @param error - Error to check
 * @returns True if the error is an API error, false otherwise
 */
export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'success' in error &&
    typeof (error as ApiError).success === 'boolean' &&
    'message' in error &&
    typeof (error as ApiError).message === 'string' &&
    'error_code' in error &&
    typeof (error as ApiError).error_code === 'string'
  );
}

/**
 * Type guard to check if an error is an Axios error
 * @param error - Error to check
 * @returns True if the error is an Axios error, false otherwise
 */
export function isAxiosError(error: unknown): error is AxiosError {
  return error instanceof AxiosError;
}

/**
 * Format error message for display to users
 * @param error - Error to format
 * @returns Formatted error message
 */
export function formatErrorMessage(error: unknown): string {
  // If error is a string, return it directly
  if (typeof error === 'string') {
    return error;
  }

  // If error is an Error instance, return the message
  if (error instanceof Error) {
    return error.message;
  }

  // Handle API errors
  if (isApiError(error)) {
    if (error.details && Object.keys(error.details).length > 0) {
      return `${error.message}\n${formatValidationErrors(error.details)}`;
    }
    return error.message;
  }

  // Handle Axios errors
  if (isAxiosError(error)) {
    // Check for network errors
    if (error.code === 'ERR_NETWORK') {
      return 'Network error: Please check your connection';
    }

    // Check for timeout errors
    if (error.code === 'ECONNABORTED') {
      return 'Request timeout: Please try again';
    }

    // Extract error from response if available
    if (error.response) {
      const { data, statusText } = error.response;
      
      // If response data contains error message
      if (data) {
        if (typeof data === 'string') {
          return data;
        }
        if (typeof data === 'object' && data !== null) {
          if ('message' in data && typeof data.message === 'string') {
            return data.message;
          }
          if ('error' in data && typeof data.error === 'string') {
            return data.error;
          }
          if (isApiError(data)) {
            return formatErrorMessage(data);
          }
        }
      }
      
      // Fall back to status text
      return statusText || 'An error occurred with the request';
    }
  }

  // Generic error message for unknown errors
  return 'An unexpected error occurred';
}

/**
 * Format validation errors from API response
 * @param details - Validation error details
 * @returns Formatted validation error message
 */
export function formatValidationErrors(details: Record<string, string[]>): string {
  if (!details || Object.keys(details).length === 0) {
    return '';
  }

  const formattedErrors = Object.entries(details)
    .map(([field, errors]) => {
      const fieldName = field
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, (str) => str.toUpperCase());
      
      return `${fieldName}: ${errors.join(', ')}`;
    })
    .join('\n');

  return formattedErrors;
}

/**
 * Display error notification to the user
 * @param message - Error message to display
 */
function showErrorNotificationLocal(message: string): void {
  // Log to console for debugging
  console.error('Error:', message);

  // Check if running in browser environment
  if (typeof window !== 'undefined' && window.document) {
    // Implementation depends on the notification library being used
    // This is a placeholder that can be replaced with actual implementation
    // based on the notification system used in the project (e.g., toast)
    try {
      // Example using a hypothetical toast notification system
      // toast.error(message, {
      //   position: 'top-right',
      //   autoClose: 5000,
      //   closeButton: true,
      // });

      // Since we don't know the exact notification system,
      // this is left as a placeholder for the implementation
      const event = new CustomEvent('app:error', { detail: { message } });
      window.dispatchEvent(event);
    } catch (e) {
      console.error('Failed to show notification:', e);
    }
  }
}

/**
 * Handle API errors with appropriate notifications
 * @param error - Error to handle
 * @param showNotification - Whether to show a notification to the user (default: true)
 */
export function handleApiError(error: unknown, showNotification: boolean = true): void {
  const message = formatErrorMessage(error);
  
  // Log error for debugging
  console.error('API Error:', error);
  
  // Show notification if enabled
  if (showNotification) {
    showErrorNotificationLocal(message);
  }
}

/**
 * Extract HTTP status code from error
 * @param error - Error to extract status code from
 * @returns HTTP status code or null if not available
 */
export function getErrorStatusCode(error: unknown): number | null {
  // Check if it's an Axios error with a response
  if (isAxiosError(error) && error.response) {
    return error.response.status;
  }
  
  // Check if it's an object with a status property
  if (
    typeof error === 'object' &&
    error !== null &&
    'status' in error &&
    typeof (error as any).status === 'number'
  ) {
    return (error as any).status;
  }
  
  return null;
}

/**
 * Extract error code from API error
 * @param error - Error to extract error code from
 * @returns Error code or null if not available
 */
export function getErrorCode(error: unknown): string | null {
  // Check if it's an API error
  if (isApiError(error)) {
    return error.error_code;
  }
  
  // Check if it's an Axios error with response data containing error_code
  if (
    isAxiosError(error) &&
    error.response?.data &&
    typeof error.response.data === 'object' &&
    'error_code' in error.response.data
  ) {
    return error.response.data.error_code as string;
  }
  
  return null;
}