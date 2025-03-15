import React from 'react';
import { Box, Typography, Link, Divider } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import styled from '@mui/material/styles/styled';
import { Link as RouterLink } from 'react-router-dom';
import { ROUTES } from '../../constants/routes';
import { APP_VERSION, APP_NAME } from '../../constants/appConfig';

/**
 * Interface for Footer component props
 */
interface FooterProps {
  /**
   * Optional CSS class name for styling the footer
   */
  className?: string;
}

/**
 * Styled component for the footer container
 */
const FooterContainer = styled(Box)(({ theme }) => ({
  width: '100%',
  height: '48px',
  backgroundColor: theme.palette.background.paper,
  borderTop: '1px solid',
  borderColor: theme.palette.divider,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: theme.spacing(0, 3),
}));

/**
 * Styled component for the footer content layout
 */
const FooterContent = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isMobile',
})<{ isMobile: boolean }>(({ theme, isMobile }) => ({
  width: '100%',
  maxWidth: '1200px',
  display: 'flex',
  flexDirection: isMobile ? 'column' : 'row',
  alignItems: 'center',
  justifyContent: isMobile ? 'center' : 'space-between',
  gap: theme.spacing(1),
}));

/**
 * Footer links configuration
 */
const FOOTER_LINKS = [
  { label: 'Terms', path: ROUTES.LEGAL.TERMS },
  { label: 'Privacy', path: ROUTES.LEGAL.PRIVACY },
  { label: 'Help', path: ROUTES.LEGAL.HELP },
];

/**
 * The main footer component that displays copyright information, links, and version information
 * 
 * @param props - The component props
 * @returns The rendered footer component
 */
const Footer: React.FC<FooterProps> = ({ className }) => {
  // Get theme and media query for responsive design
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  // Get current year for copyright information
  const currentYear = new Date().getFullYear();

  return (
    // Render footer container with appropriate padding and background
    <FooterContainer className={className}>
      {/* Render content with responsive layout (column on mobile, row on desktop) */}
      <FooterContent isMobile={isMobile}>
        {/* Display copyright information with current year and app name */}
        <Typography variant="body2" color="text.secondary">
          &copy; {currentYear} {APP_NAME}. All rights reserved.
        </Typography>

        {/* Only show divider in desktop view */}
        {!isMobile && <Divider orientation="vertical" flexItem />}

        {/* Display footer links (Terms, Privacy, Help) with appropriate spacing */}
        <Box
          sx={{
            display: 'flex',
            gap: theme.spacing(2),
            justifyContent: 'center',
          }}
        >
          {FOOTER_LINKS.map((link) => (
            <Link
              key={link.label}
              component={RouterLink}
              to={link.path}
              color="text.secondary"
              underline="hover"
              variant="body2"
            >
              {link.label}
            </Link>
          ))}
        </Box>

        {/* Only show divider in desktop view */}
        {!isMobile && <Divider orientation="vertical" flexItem />}

        {/* Display version information with app version number */}
        <Typography variant="body2" color="text.secondary">
          Version {APP_VERSION}
        </Typography>
      </FooterContent>
    </FooterContainer>
  );
};

export default Footer;