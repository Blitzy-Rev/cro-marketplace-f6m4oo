import React from 'react';
import { Box, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import type { SxProps, Theme } from '@mui/system';
import { APP_CONFIG } from '../../constants/appConfig';

/**
 * Props for the Logo component
 */
interface LogoProps {
  /**
   * Determines the color variant of the logo
   * @default "default"
   */
  variant?: 'default' | 'light' | 'dark';
  
  /**
   * Controls the size of the logo
   * @default "medium"
   */
  size?: 'small' | 'medium' | 'large';
  
  /**
   * Whether to show the application name text alongside the logo
   * @default true
   */
  showText?: boolean;
  
  /**
   * Additional styling using Material UI's sx prop system
   * @default {}
   */
  sx?: SxProps<Theme>;
}

/**
 * Definition of logo sizes for different size variants
 */
const logoSizes = {
  small: { width: 24, height: 24 },
  medium: { width: 32, height: 32 },
  large: { width: 48, height: 48 },
};

/**
 * A reusable component that displays the application logo with configurable options
 */
const Logo: React.FC<LogoProps> = ({
  variant = 'default',
  size = 'medium',
  showText = true,
  sx = {},
}) => {
  const theme = useTheme();
  
  // Determine logo src based on variant
  let logoSrc = '/assets/logo.svg';
  
  if (variant === 'light') {
    logoSrc = '/assets/logo-light.svg';
  } else if (variant === 'dark') {
    logoSrc = '/assets/logo-dark.svg';
  }
  
  // Get logo dimensions based on size
  const { width, height } = logoSizes[size];
  
  // Determine text color based on variant
  const textColor = variant === 'light' 
    ? theme.palette.common.white 
    : variant === 'dark' 
      ? theme.palette.common.black 
      : theme.palette.primary.main;
  
  // Merge sx props
  const combinedSx = {
    display: 'flex',
    alignItems: 'center',
    ...sx,
  };
  
  return (
    <Box sx={combinedSx}>
      <img
        src={logoSrc}
        alt={`${APP_CONFIG.app.title} Logo`}
        width={width}
        height={height}
      />
      {showText && (
        <Typography
          variant={size === 'large' ? 'h6' : 'body1'}
          sx={{
            ml: 1,
            fontWeight: 'bold',
            color: textColor,
          }}
        >
          {APP_CONFIG.app.title}
        </Typography>
      )}
    </Box>
  );
};

export default Logo;