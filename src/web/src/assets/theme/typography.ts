import { TypographyOptions } from '@mui/material/styles'; // ^5.0.0

/**
 * Typography configuration for the Molecular Data Management and CRO Integration Platform.
 * Implements the design system's typography guidelines with Roboto as the primary font family
 * as specified in the UI/UX requirements.
 */
export const typography: TypographyOptions = {
  // Main font family aligned with design system requirements
  fontFamily: "'Roboto', 'Helvetica', 'Arial', sans-serif",
  // Base font size set to 16px as specified in the design principles
  fontSize: 16,
  // Font weight definitions
  fontWeightLight: 300,
  fontWeightRegular: 400,
  fontWeightMedium: 500,
  fontWeightBold: 700,
  // Heading styles
  h1: {
    fontWeight: 500,
    fontSize: '2.5rem', // 40px
    lineHeight: 1.2,
    letterSpacing: '-0.01562em',
  },
  h2: {
    fontWeight: 500,
    fontSize: '2rem', // 32px
    lineHeight: 1.2,
    letterSpacing: '-0.00833em',
  },
  h3: {
    fontWeight: 500,
    fontSize: '1.75rem', // 28px
    lineHeight: 1.2,
    letterSpacing: '0em',
  },
  h4: {
    fontWeight: 500,
    fontSize: '1.5rem', // 24px - as specified in design principles
    lineHeight: 1.2,
    letterSpacing: '0.00735em',
  },
  h5: {
    fontWeight: 500,
    fontSize: '1.25rem', // 20px - as specified in design principles
    lineHeight: 1.2,
    letterSpacing: '0em',
  },
  h6: {
    fontWeight: 500,
    fontSize: '1.125rem', // 18px - as specified in design principles
    lineHeight: 1.2,
    letterSpacing: '0.0075em',
  },
  // Subtitle styles
  subtitle1: {
    fontWeight: 400,
    fontSize: '1rem', // 16px
    lineHeight: 1.5,
    letterSpacing: '0.00938em',
  },
  subtitle2: {
    fontWeight: 500,
    fontSize: '0.875rem', // 14px
    lineHeight: 1.5,
    letterSpacing: '0.00714em',
  },
  // Body text styles
  body1: {
    fontWeight: 400,
    fontSize: '1rem', // 16px - primary font size as specified
    lineHeight: 1.5,
    letterSpacing: '0.00938em',
  },
  body2: {
    fontWeight: 400,
    fontSize: '0.875rem', // 14px
    lineHeight: 1.5,
    letterSpacing: '0.01071em',
  },
  // Other typography variants
  button: {
    fontWeight: 500,
    fontSize: '0.875rem', // 14px
    lineHeight: 1.75,
    letterSpacing: '0.02857em',
    textTransform: 'none', // Override the default uppercase transform
  },
  caption: {
    fontWeight: 400,
    fontSize: '0.75rem', // 12px
    lineHeight: 1.66,
    letterSpacing: '0.03333em',
  },
  overline: {
    fontWeight: 400,
    fontSize: '0.75rem', // 12px
    lineHeight: 2.66,
    letterSpacing: '0.08333em',
    textTransform: 'uppercase',
  },
};