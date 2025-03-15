import { configureStore, combineReducers, getDefaultMiddleware, Reducer } from '@reduxjs/toolkit'; // v1.9.5
import { 
  apiErrorMiddleware, 
  loggingMiddleware, 
  notificationMiddleware,
  loadingMiddleware 
} from './middleware';
import uiReducer from '../features/ui/uiSlice';
import authReducer from '../features/auth/authSlice';
import moleculeReducer from '../features/molecule/moleculeSlice';
import libraryReducer from '../features/library/librarySlice';
import submissionReducer from '../features/submission/submissionSlice';
import { AuthState } from '../types/auth.types';
import { MoleculeState } from '../features/molecule/moleculeSlice';
import { LibraryState } from '../features/library/librarySlice';
import { SubmissionState } from '../features/submission/submissionSlice';
import { UiState } from '../features/ui/uiSlice';

/**
 * Configures and creates the Redux store with all reducers and middleware
 * @param preloadedState - Optional initial state for the store
 * @returns Configured Redux store
 */
export const configureAppStore = (preloadedState?: Partial<RootState>) => {
  // Create root reducer by combining all feature reducers
  const rootReducer = combineReducers({
    ui: uiReducer,
    auth: authReducer,
    molecule: moleculeReducer,
    libraries: libraryReducer,
    submission: submissionReducer
  });

  // Configure middleware with default middleware and custom middleware
  const middleware = [
    ...getDefaultMiddleware(),
    apiErrorMiddleware,
    loggingMiddleware,
    notificationMiddleware,
    loadingMiddleware
  ];

  // Create and return the Redux store with root reducer, preloaded state, and middleware
  const store = configureStore({
    reducer: rootReducer,
    middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(middleware),
    preloadedState
  });

  return store;
};

// Create the store instance
export const store = configureAppStore();

// Define the RootState type by inferring from the store's state
export type RootState = ReturnType<typeof store.getState>;

// Define the AppDispatch type by inferring from the store's dispatch function
export type AppDispatch = typeof store.dispatch;

// Export the root reducer for testing or other environments
export const rootReducer = combineReducers({
  ui: uiReducer,
  auth: authReducer,
  molecule: moleculeReducer,
  libraries: libraryReducer,
  submission: submissionReducer
});