import { createTheme, Theme } from '@mui/material/styles'; // @mui/material/styles ^5.0.0
import { lightPalette, darkPalette } from './palette';
import { typography } from './typography';
import shadows from './shadows';
import { components } from './components';

/**
 * Light theme configuration for the Molecular Data Management and CRO Integration Platform.
 * Implements the design system specifications for light mode.
 * 
 * Combines:
 * - Light color palette (optimized for standard light environments)
 * - Typography system (Roboto font family with defined hierarchy)
 * - Shadow elevation system (for component depth and hierarchy)
 * - Component style overrides (for consistent UI patterns)
 */
export const lightTheme: Theme = createTheme({
  palette: lightPalette,
  typography,
  shadows,
  components,
});

/**
 * Dark theme configuration for the Molecular Data Management and CRO Integration Platform.
 * Implements the design system specifications for dark mode.
 * 
 * Combines:
 * - Dark color palette (optimized for reduced eye strain in low-light environments)
 * - Typography system (shared with light theme)
 * - Shadow elevation system (shared with light theme)
 * - Component style overrides (shared with light theme)
 * 
 * Note: Component styles are shared between themes and will adapt to the palette
 * changes automatically for most components due to Material UI's theming system.
 */
export const darkTheme: Theme = createTheme({
  palette: darkPalette,
  typography,
  shadows,
  components,
});

/**
 * Default export of both theme configurations.
 * This allows for easy theme switching in the application based on:
 * - User preference
 * - System settings (light/dark mode)
 * - Time of day
 * 
 * The application can import this default export and access both themes,
 * or import the individual themes directly as needed.
 */
export default { lightTheme, darkTheme };