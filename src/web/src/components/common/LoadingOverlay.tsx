import React from 'react'; // React ^18.0.0
import { Box, CircularProgress, Typography } from '@mui/material'; // @mui/material ^5.0.0
import { styled } from '@mui/material/styles'; // @mui/material/styles ^5.0.0

/**
 * Props for the LoadingOverlay component
 */
interface LoadingOverlayProps {
  /** Whether the loading overlay should be displayed */
  loading: boolean;
  /** Optional message to display below the spinner */
  message?: string;
  /** Opacity of the overlay background (default: 0.7) */
  opacity?: number;
  /** Z-index of the overlay (default: 1000) */
  zIndex?: number;
  /** Content to render below the overlay */
  children?: React.ReactNode;
}

/**
 * Styled component for the loading overlay background
 */
const StyledOverlay = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'opacity' && prop !== 'zIndex',
})<{ opacity?: number; zIndex?: number }>(({ theme, opacity, zIndex }) => ({
  position: 'absolute',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  backgroundColor: theme.palette.background.paper,
  opacity: opacity || 0.7,
  zIndex: zIndex || 1000,
}));

/**
 * Styled component for wrapping the content below the overlay
 */
const ContentWrapper = styled(Box)({
  position: 'relative',
  width: '100%',
  height: '100%',
});

/**
 * A component that renders a loading spinner with an optional message over content
 */
const LoadingOverlay = ({
  loading,
  message,
  opacity,
  zIndex,
  children,
}: LoadingOverlayProps): JSX.Element | null => {
  // If not loading and no children, just return null
  if (!loading && !children) {
    return null;
  }

  // If not loading but has children, render just the children
  if (!loading && children) {
    return <>{children}</>;
  }

  return (
    <ContentWrapper>
      {loading && (
        <StyledOverlay opacity={opacity} zIndex={zIndex}>
          <CircularProgress size={48} />
          {message && (
            <Typography variant="body1" sx={{ mt: 2 }}>
              {message}
            </Typography>
          )}
        </StyledOverlay>
      )}
      {children}
    </ContentWrapper>
  );
};

export default LoadingOverlay;