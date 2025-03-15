import { PaletteOptions } from '@mui/material/styles'; // @mui/material/styles ^5.0.0

/**
 * Default color palette for the Molecular Data Management and CRO Integration Platform.
 * Defines all colors used throughout the application to ensure visual consistency.
 * This palette follows Material Design color principles.
 */
export const palette: PaletteOptions = {
  primary: {
    main: '#1976d2',      // Primary blue
    light: '#42a5f5',
    dark: '#1565c0',
    contrastText: '#ffffff'
  },
  secondary: {
    main: '#388e3c',      // Secondary green
    light: '#4caf50',
    dark: '#2e7d32',
    contrastText: '#ffffff'
  },
  error: {
    main: '#d32f2f',      // Error red
    light: '#ef5350',
    dark: '#c62828',
    contrastText: '#ffffff'
  },
  warning: {
    main: '#f57c00',      // Warning orange
    light: '#ff9800',
    dark: '#e65100',
    contrastText: '#ffffff'
  },
  info: {
    main: '#0288d1',      // Info light blue
    light: '#03a9f4',
    dark: '#01579b',
    contrastText: '#ffffff'
  },
  success: {
    main: '#388e3c',      // Success green (same as secondary)
    light: '#4caf50',
    dark: '#2e7d32',
    contrastText: '#ffffff'
  },
  grey: {
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#eeeeee',
    300: '#e0e0e0',
    400: '#bdbdbd',
    500: '#9e9e9e',
    600: '#757575',
    700: '#616161',
    800: '#424242',
    900: '#212121',
    A100: '#d5d5d5',
    A200: '#aaaaaa',
    A400: '#303030',
    A700: '#616161'
  },
  background: {
    default: '#f5f5f5',
    paper: '#ffffff'
  },
  text: {
    primary: 'rgba(0, 0, 0, 0.87)',
    secondary: 'rgba(0, 0, 0, 0.6)',
    disabled: 'rgba(0, 0, 0, 0.38)'
  },
  divider: 'rgba(0, 0, 0, 0.12)',
  action: {
    active: 'rgba(0, 0, 0, 0.54)',
    hover: 'rgba(0, 0, 0, 0.04)',
    selected: 'rgba(0, 0, 0, 0.08)',
    disabled: 'rgba(0, 0, 0, 0.26)',
    disabledBackground: 'rgba(0, 0, 0, 0.12)'
  }
};

/**
 * Light theme palette - equivalent to the default palette.
 * Explicitly defined to support theme switching functionality.
 */
export const lightPalette: PaletteOptions = {
  ...palette
};

/**
 * Dark theme palette for the Molecular Data Management and CRO Integration Platform.
 * Provides a dark mode with appropriate color adjustments for reduced eye strain
 * and better visibility in low-light environments.
 */
export const darkPalette: PaletteOptions = {
  mode: 'dark',
  primary: {
    main: '#90caf9',      // Lighter blue for dark theme
    light: '#e3f2fd',
    dark: '#42a5f5',
    contrastText: 'rgba(0, 0, 0, 0.87)'
  },
  secondary: {
    main: '#81c784',      // Lighter green for dark theme
    light: '#e8f5e9',
    dark: '#66bb6a',
    contrastText: 'rgba(0, 0, 0, 0.87)'
  },
  error: {
    main: '#f44336',      // Error red for dark theme
    light: '#e57373',
    dark: '#d32f2f',
    contrastText: '#ffffff'
  },
  warning: {
    main: '#ffb74d',      // Warning orange for dark theme
    light: '#ffd54f',
    dark: '#ff9800',
    contrastText: 'rgba(0, 0, 0, 0.87)'
  },
  info: {
    main: '#4fc3f7',      // Info light blue for dark theme
    light: '#b3e5fc',
    dark: '#29b6f6',
    contrastText: 'rgba(0, 0, 0, 0.87)'
  },
  success: {
    main: '#66bb6a',      // Success green for dark theme
    light: '#a5d6a7',
    dark: '#388e3c',
    contrastText: 'rgba(0, 0, 0, 0.87)'
  },
  background: {
    default: '#121212',   // Dark background
    paper: '#1e1e1e'      // Slightly lighter for paper elements
  },
  text: {
    primary: '#ffffff',
    secondary: 'rgba(255, 255, 255, 0.7)',
    disabled: 'rgba(255, 255, 255, 0.5)'
  },
  divider: 'rgba(255, 255, 255, 0.12)',
  action: {
    active: '#ffffff',
    hover: 'rgba(255, 255, 255, 0.08)',
    selected: 'rgba(255, 255, 255, 0.16)',
    disabled: 'rgba(255, 255, 255, 0.3)',
    disabledBackground: 'rgba(255, 255, 255, 0.12)'
  }
};