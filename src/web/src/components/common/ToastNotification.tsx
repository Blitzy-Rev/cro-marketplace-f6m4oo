import React from 'react';
import { ToastContainer, ToastContainerProps, ToastPosition } from 'react-toastify'; // react-toastify 9.0.0
import { useTheme, Theme } from '@mui/material'; // @mui/material 5.0.0
import styled from '@emotion/styled'; // @emotion/styled 11.0.0
import 'react-toastify/dist/ReactToastify.css';
import { APP_CONFIG } from '../../constants/appConfig';

/**
 * Styled version of the ToastContainer component with custom styling based on the current theme.
 * This applies theme-consistent styling to all toast notifications.
 */
const StyledToastContainer = styled(ToastContainer)<ToastContainerProps & { themeObject: Theme }>`
  // Base styling for all toasts
  .Toastify__toast {
    border-radius: ${({ themeObject }) => themeObject.shape.borderRadius}px;
    font-family: ${({ themeObject }) => themeObject.typography.fontFamily};
    font-size: ${({ themeObject }) => themeObject.typography.body2.fontSize};
    box-shadow: ${({ themeObject }) => themeObject.shadows[3]};
  }

  // Success toast styling
  .Toastify__toast--success {
    background-color: ${({ themeObject }) => themeObject.palette.success.light};
    color: ${({ themeObject }) => themeObject.palette.success.contrastText};
    border-left: 4px solid ${({ themeObject }) => themeObject.palette.success.main};
  }

  // Error toast styling
  .Toastify__toast--error {
    background-color: ${({ themeObject }) => themeObject.palette.error.light};
    color: ${({ themeObject }) => themeObject.palette.error.contrastText};
    border-left: 4px solid ${({ themeObject }) => themeObject.palette.error.main};
  }

  // Warning toast styling
  .Toastify__toast--warning {
    background-color: ${({ themeObject }) => themeObject.palette.warning.light};
    color: ${({ themeObject }) => themeObject.palette.warning.contrastText};
    border-left: 4px solid ${({ themeObject }) => themeObject.palette.warning.main};
  }

  // Info toast styling
  .Toastify__toast--info {
    background-color: ${({ themeObject }) => themeObject.palette.info.light};
    color: ${({ themeObject }) => themeObject.palette.info.contrastText};
    border-left: 4px solid ${({ themeObject }) => themeObject.palette.info.main};
  }

  // Progress bar styling
  .Toastify__progress-bar {
    background: ${({ themeObject }) => themeObject.palette.primary.main};
  }

  // Toast content styling
  .Toastify__toast-body {
    padding: 8px 4px;
  }

  // Close button styling
  .Toastify__close-button {
    color: ${({ themeObject }) => themeObject.palette.text.secondary};
    opacity: 0.7;
    
    &:hover {
      opacity: 1;
    }
  }

  // Animation customization
  .Toastify__toast--enter {
    transform: translateX(100%);
  }
  .Toastify__toast--exit {
    transform: translateX(100%);
  }
`;

/**
 * ToastNotification component
 * 
 * A customized implementation of react-toastify's ToastContainer
 * that adapts to the current theme and uses application configuration.
 * This component provides a standardized way to display toast notifications
 * throughout the application with consistent styling and behavior.
 * 
 * Usage:
 * 1. Include this component once in your application, typically in App.tsx
 * 2. Use toast.success(), toast.error(), etc. from 'react-toastify' to display notifications
 */
const ToastNotification: React.FC = () => {
  const theme = useTheme();
  
  // Ensure theme is either 'light' or 'dark' for react-toastify
  const toastifyTheme = theme.palette.mode === 'dark' ? 'dark' : 'light';
  
  // Default position for toast notifications
  const position: ToastPosition = 'top-right';
  
  return (
    <StyledToastContainer
      themeObject={theme}
      position={position}
      autoClose={APP_CONFIG.ui.toastDuration}
      closeOnClick
      pauseOnHover
      draggable
      theme={toastifyTheme}
      newestOnTop
      limit={3}
    />
  );
};

export default ToastNotification;