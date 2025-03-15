import React from 'react';
import { Box } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import type { SxProps, Theme } from '@mui/system';
import { Link } from 'react-router-dom';
import Logo from '../common/Logo';
import { APP_CONFIG } from '../../constants/appConfig';

/**
 * Maps layout contexts to appropriate logo sizes
 */
const contextSizes: Record<string, "small" | "medium" | "large"> = {
  header: 'medium',
  sidebar: 'large'
};

/**
 * Props for the LayoutLogo component
 */
interface LayoutLogoProps {
  /**
   * Determines the color variant of the logo
   * @default "default"
   */
  variant?: 'default' | 'light' | 'dark';
  
  /**
   * Whether the containing sidebar is collapsed (affects text display)
   * @default false
   */
  collapsed?: boolean;
  
  /**
   * The layout context where the logo is being used
   * @default "header"
   */
  context?: 'header' | 'sidebar';
  
  /**
   * Additional styling using Material UI's sx prop system
   * @default {}
   */
  sx?: SxProps<Theme>;
}

/**
 * A specialized Logo component for use in the application layout (header and sidebar)
 */
const LayoutLogo: React.FC<LayoutLogoProps> = ({
  variant = 'default',
  collapsed = false,
  context = 'header',
  sx = {}
}) => {
  const theme = useTheme();
  
  // Determine if we should show text based on context and collapsed state
  const showText = context === 'header' || !collapsed;
  
  // Determine appropriate size based on context
  const size = contextSizes[context] || 'medium';
  
  // Determine appropriate variant based on theme mode if not explicitly provided
  const logoVariant = variant === 'default' 
    ? theme.palette.mode === 'dark' ? 'light' : 'dark'
    : variant;
  
  // Calculate appropriate spacing and alignment based on context
  const logoSx: SxProps<Theme> = {
    justifyContent: context === 'header' ? 'flex-start' : 'center',
    my: context === 'header' ? 0 : 2,
    ...sx
  };
  
  return (
    <Link 
      to="/" 
      style={{ 
        textDecoration: 'none',
        display: 'block',
        color: 'inherit'
      }}
    >
      <Logo 
        variant={logoVariant} 
        size={size} 
        showText={showText}
        sx={logoSx}
      />
    </Link>
  );
};

export default LayoutLogo;