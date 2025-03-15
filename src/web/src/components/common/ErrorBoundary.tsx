import React from 'react'; // ^18.0.0
import { Box, Typography, Button } from '@mui/material'; // ^5.0.0
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'; // ^5.0.0
import { formatErrorMessage } from '../../utils/errorHandler';
import AlertDialog from './AlertDialog';

/**
 * Props for a custom fallback component to display when an error occurs
 */
interface FallbackProps {
  error: Error;
  errorInfo: React.ErrorInfo;
  resetErrorBoundary: () => void;
}

/**
 * Props for the ErrorBoundary component
 */
interface ErrorBoundaryProps {
  /**
   * Child components to be rendered and monitored for errors
   */
  children: React.ReactNode;
  
  /**
   * Optional custom component to render when an error occurs
   */
  FallbackComponent?: React.ComponentType<FallbackProps>;
  
  /**
   * Optional callback function called when an error is caught
   */
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  
  /**
   * Optional callback function called when the error boundary is reset
   */
  onReset?: () => void;
  
  /**
   * Array of values that will cause the error boundary to reset when they change
   */
  resetKeys?: Array<unknown>;
  
  /**
   * Whether to use a dialog to display errors instead of inline UI
   * @default false
   */
  useDialog?: boolean;
}

/**
 * State for the ErrorBoundary component
 */
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

/**
 * React error boundary component that catches JavaScript errors in its child component tree,
 * logs those errors, and displays a fallback UI instead of crashing the entire application.
 * 
 * This component is crucial for graceful error handling in the Molecular Data Management 
 * and CRO Integration Platform.
 */
class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  /**
   * Static lifecycle method called when a child component throws an error.
   * Updates the state to indicate that an error has occurred.
   */
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true };
  }

  /**
   * Lifecycle method called after a child component throws an error.
   * Captures and logs the error details.
   */
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    this.setState({
      error,
      errorInfo
    });

    // Log error details to console for debugging
    console.error('Error caught by ErrorBoundary:', error);
    console.error('Component stack:', errorInfo.componentStack);

    // Call onError callback if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  /**
   * Resets the error boundary state and allows re-rendering the children.
   */
  resetErrorBoundary = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });

    // Call onReset callback if provided
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  /**
   * Checks if resetKeys have changed and resets the error boundary if needed.
   */
  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    const { resetKeys } = this.props;
    
    if (resetKeys && prevProps.resetKeys) {
      const hasChanged = resetKeys.some((key, index) => key !== prevProps.resetKeys?.[index]);
      
      if (hasChanged) {
        this.resetErrorBoundary();
      }
    }
  }

  render(): React.ReactNode {
    const { hasError, error, errorInfo } = this.state;
    const { children, FallbackComponent, useDialog = false } = this.props;

    if (hasError && error) {
      // If a custom fallback component is provided, use it
      if (FallbackComponent) {
        return <FallbackComponent 
          error={error} 
          errorInfo={errorInfo!} 
          resetErrorBoundary={this.resetErrorBoundary} 
        />;
      }

      // If useDialog is true, show AlertDialog
      if (useDialog) {
        const message = (
          <div>
            <Typography variant="body1" gutterBottom>
              {formatErrorMessage(error)}
            </Typography>
            {errorInfo && (
              <Typography 
                variant="body2" 
                sx={{ 
                  fontFamily: 'monospace', 
                  fontSize: '0.8rem',
                  mt: 2, 
                  maxHeight: '200px', 
                  overflow: 'auto',
                  p: 1,
                  bgcolor: 'background.paper',
                  borderRadius: 1 
                }}
              >
                {errorInfo.componentStack}
              </Typography>
            )}
          </div>
        );

        return (
          <AlertDialog
            open={true}
            title="Something went wrong"
            message={message}
            severity="error"
            buttonText="Try Again"
            onClose={this.resetErrorBoundary}
            disableBackdropClick={true}
            disableEscapeKeyDown={true}
          />
        );
      }

      // Default fallback UI (in-page)
      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 3,
            margin: 2,
            border: 1,
            borderColor: 'error.light',
            borderRadius: 1,
            bgcolor: 'rgba(211, 47, 47, 0.1)',
            textAlign: 'center',
          }}
        >
          <ErrorOutlineIcon sx={{ fontSize: 48, mb: 2, color: 'error.main' }} />
          <Typography variant="h5" gutterBottom color="error">
            Something went wrong
          </Typography>
          <Typography variant="body1" sx={{ mb: 2 }}>
            {formatErrorMessage(error)}
          </Typography>
          {errorInfo && (
            <Typography 
              variant="body2" 
              sx={{ 
                fontFamily: 'monospace', 
                fontSize: '0.8rem',
                mb: 2, 
                maxHeight: '150px', 
                overflow: 'auto',
                width: '100%',
                p: 1,
                bgcolor: 'rgba(0, 0, 0, 0.05)',
                borderRadius: 1 
              }}
            >
              {errorInfo.componentStack}
            </Typography>
          )}
          <Button 
            variant="contained" 
            color="error" 
            onClick={this.resetErrorBoundary}
            sx={{ mt: 2 }}
          >
            Try Again
          </Button>
        </Box>
      );
    }

    // If there's no error, render children normally
    return children;
  }
}

export default ErrorBoundary;