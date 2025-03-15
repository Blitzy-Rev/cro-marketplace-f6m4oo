import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ApiError } from '../../types/api.types';

/**
 * Notification types used throughout the application
 */
export const NotificationType = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info'
} as const;

// Type alias for notification types
export type NotificationTypeValue = typeof NotificationType[keyof typeof NotificationType];

/**
 * Interface for notification objects
 */
interface Notification {
  id: string;
  type: NotificationTypeValue;
  message: string;
  autoHideDuration?: number;
  timestamp: number;
}

/**
 * Interface for modal state
 */
interface ModalState {
  activeModal: string | null;
  modalProps: Record<string, any>;
}

/**
 * Interface for confirmation dialog state
 */
interface ConfirmDialogState {
  open: boolean;
  title: string;
  message: string;
  confirmAction: (() => void) | null;
  cancelAction: (() => void) | null;
}

/**
 * Interface for the UI state slice
 */
interface UiState {
  loading: Record<string, boolean>;
  notifications: Notification[];
  modals: ModalState;
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  confirmDialog: ConfirmDialogState;
}

/**
 * Initial state for the UI slice
 */
const initialState: UiState = {
  loading: {},
  notifications: [],
  modals: {
    activeModal: null,
    modalProps: {}
  },
  sidebarOpen: true,
  theme: 'light',
  confirmDialog: {
    open: false,
    title: '',
    message: '',
    confirmAction: null,
    cancelAction: null
  }
};

/**
 * UI Redux slice for managing UI-related state across the application
 */
export const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    /**
     * Set a loading state for a specific key
     */
    setLoading: (state, action: PayloadAction<string>) => {
      state.loading[action.payload] = true;
    },
    
    /**
     * Clear a loading state for a specific key
     */
    clearLoading: (state, action: PayloadAction<string>) => {
      delete state.loading[action.payload];
    },
    
    /**
     * Add a notification to the notification queue
     */
    addNotification: (
      state, 
      action: PayloadAction<{
        type: NotificationTypeValue;
        message: string;
        autoHideDuration?: number;
      }>
    ) => {
      const { type, message, autoHideDuration } = action.payload;
      state.notifications.push({
        id: Date.now().toString(),
        type,
        message,
        autoHideDuration: autoHideDuration || 5000, // Default 5 seconds
        timestamp: Date.now()
      });
    },
    
    /**
     * Remove a notification by ID
     */
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(
        notification => notification.id !== action.payload
      );
    },
    
    /**
     * Clear all notifications
     */
    clearNotifications: (state) => {
      state.notifications = [];
    },
    
    /**
     * Open a modal with the provided props
     */
    openModal: (
      state, 
      action: PayloadAction<{
        modalType: string;
        modalProps?: Record<string, any>;
      }>
    ) => {
      state.modals.activeModal = action.payload.modalType;
      state.modals.modalProps = action.payload.modalProps || {};
    },
    
    /**
     * Close the currently active modal
     */
    closeModal: (state) => {
      state.modals.activeModal = null;
      state.modals.modalProps = {};
    },
    
    /**
     * Toggle the sidebar open/closed state
     */
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    
    /**
     * Set the sidebar open/closed state
     */
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },
    
    /**
     * Set the application theme (light/dark)
     */
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload;
    },
    
    /**
     * Open a confirmation dialog
     */
    openConfirmDialog: (
      state,
      action: PayloadAction<{
        title: string;
        message: string;
        confirmAction: () => void;
        cancelAction?: () => void;
      }>
    ) => {
      state.confirmDialog = {
        open: true,
        title: action.payload.title,
        message: action.payload.message,
        confirmAction: action.payload.confirmAction,
        cancelAction: action.payload.cancelAction || null
      };
    },
    
    /**
     * Close the confirmation dialog
     */
    closeConfirmDialog: (state) => {
      state.confirmDialog = {
        ...state.confirmDialog,
        open: false
      };
    }
  }
});

// Action creators
export const { 
  setLoading,
  clearLoading,
  addNotification,
  removeNotification,
  clearNotifications,
  openModal,
  closeModal,
  toggleSidebar,
  setSidebarOpen,
  setTheme,
  openConfirmDialog,
  closeConfirmDialog
} = uiSlice.actions;

// Selectors
/**
 * Selector for checking if a specific operation is loading
 */
export const selectLoading = (state: { ui: UiState }, key: string): boolean => 
  Boolean(state.ui.loading[key]);

/**
 * Selector for accessing the current notifications
 */
export const selectNotifications = (state: { ui: UiState }): Notification[] => 
  state.ui.notifications;

/**
 * Selector for getting the currently active modal and its props
 */
export const selectActiveModal = (state: { ui: UiState }): ModalState => 
  state.ui.modals;

/**
 * Selector for checking if the sidebar is open
 */
export const selectSidebarOpen = (state: { ui: UiState }): boolean => 
  state.ui.sidebarOpen;

/**
 * Selector for getting the current application theme
 */
export const selectTheme = (state: { ui: UiState }): 'light' | 'dark' => 
  state.ui.theme;

/**
 * Selector for accessing the confirmation dialog state
 */
export const selectConfirmDialog = (state: { ui: UiState }): ConfirmDialogState => 
  state.ui.confirmDialog;

/**
 * Helper function to create a notification from an API error
 */
export const createErrorNotification = (error: ApiError | string) => {
  const message = typeof error === 'string' 
    ? error 
    : error.message || 'An unknown error occurred';
    
  return addNotification({
    type: NotificationType.ERROR,
    message,
    autoHideDuration: 8000 // Error messages stay longer
  });
};

/**
 * Helper function to create a success notification
 */
export const createSuccessNotification = (message: string) => {
  return addNotification({
    type: NotificationType.SUCCESS,
    message,
    autoHideDuration: 5000
  });
};

export default uiSlice.reducer;