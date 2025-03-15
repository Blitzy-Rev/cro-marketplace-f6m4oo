import { Middleware, MiddlewareAPI, Dispatch, AnyAction } from 'redux'; // v4.2.1
import { isRejectedWithValue, isPending, isRejected, isFulfilled } from '@reduxjs/toolkit'; // v1.9.5
import { setLoading, clearLoading, addNotification, NotificationType } from '../features/ui/uiSlice';
import { formatErrorMessage, isApiError } from '../utils/errorHandler';
import { APP_CONFIG } from '../constants/appConfig';

/**
 * Middleware for handling API errors from rejected Redux actions
 * 
 * This middleware intercepts rejected actions with payload values,
 * formats error messages, and dispatches notifications to alert users.
 * 
 * @param store - The Redux store
 * @returns Next middleware function
 */
export const apiErrorMiddleware: Middleware = 
  (store: MiddlewareAPI) => (next: Dispatch) => (action: AnyAction) => {
    // Pass the action to the next middleware first
    const result = next(action);
    
    // Check if the action is a rejected action with a value
    if (isRejectedWithValue(action)) {
      const errorPayload = action.payload;
      
      // Format the error message based on the error payload
      const errorMessage = formatErrorMessage(errorPayload);
      
      // Dispatch an error notification
      store.dispatch(
        addNotification({
          type: NotificationType.ERROR,
          message: errorMessage,
          autoHideDuration: 8000 // Longer duration for error messages
        })
      );
    }
    
    return result;
  };

/**
 * Middleware for logging Redux actions and state changes
 * 
 * This middleware logs actions before they are processed and the
 * resulting state after processing. Only active in development mode.
 * 
 * @param store - The Redux store
 * @returns Next middleware function
 */
export const loggingMiddleware: Middleware = 
  (store: MiddlewareAPI) => (next: Dispatch) => (action: AnyAction) => {
    // Only log in development mode
    if (APP_CONFIG.app.environment === 'development' && APP_CONFIG.features.logging) {
      const actionType = action.type || 'unknown action';
      
      // Log the action type and payload
      console.group(`%c Action: ${actionType}`, 'color: #3498db; font-weight: bold');
      console.log('%c Previous State:', 'color: #9E9E9E; font-weight: bold', store.getState());
      console.log('%c Action:', 'color: #03A9F4; font-weight: bold', action);
    }
    
    // Pass the action to the next middleware
    const result = next(action);
    
    // Continue logging after the state has been updated
    if (APP_CONFIG.app.environment === 'development' && APP_CONFIG.features.logging) {
      console.log('%c New State:', 'color: #4CAF50; font-weight: bold', store.getState());
      console.groupEnd();
    }
    
    return result;
  };

/**
 * Middleware for showing notifications based on Redux actions
 * 
 * This middleware checks for notification metadata on actions and
 * dispatches appropriate notification actions based on type.
 * 
 * @param store - The Redux store
 * @returns Next middleware function
 */
export const notificationMiddleware: Middleware = 
  (store: MiddlewareAPI) => (next: Dispatch) => (action: AnyAction) => {
    // Pass the action to the next middleware and store the result
    const result = next(action);
    
    // Check if the action contains notification metadata
    if (action.notification) {
      const { type, message, duration } = action.notification;
      
      // Dispatch the appropriate notification based on type
      store.dispatch(
        addNotification({
          type,
          message,
          autoHideDuration: duration || undefined
        })
      );
    }
    
    return result;
  };

/**
 * Middleware for tracking loading states of async actions
 * 
 * This middleware tracks pending, fulfilled, and rejected actions to
 * manage loading indicators for asynchronous operations.
 * 
 * @param store - The Redux store
 * @returns Next middleware function
 */
export const loadingMiddleware: Middleware = 
  (store: MiddlewareAPI) => (next: Dispatch) => (action: AnyAction) => {
    // Extract the action type (base type without 'pending', 'fulfilled', etc.)
    const actionType = action.type || '';
    const baseActionType = actionType.replace(/\/pending|\/fulfilled|\/rejected/, '');
    
    // Handle pending actions
    if (isPending(action)) {
      store.dispatch(setLoading(baseActionType));
    }
    
    // Pass the action to the next middleware
    const result = next(action);
    
    // Handle fulfilled or rejected actions
    if (isFulfilled(action) || isRejected(action)) {
      store.dispatch(clearLoading(baseActionType));
    }
    
    return result;
  };