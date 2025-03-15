import React from 'react'; // react ^18.0.0
import { Box, Typography } from '@mui/material'; // @mui/material ^5.0.0
import { styled } from '@mui/material/styles'; // @mui/material/styles ^5.0.0

/**
 * Props interface for the TabPanel component
 */
interface TabPanelProps {
  children: React.ReactNode;
  value: number;
  index: number;
  label?: string;
  className?: string;
}

/**
 * Styled component for the tab panel container
 */
const StyledTabPanel = styled(Box)(({ theme }) => ({
  padding: theme.spacing(3),
  width: '100%',
  height: '100%',
}));

/**
 * Helper function that generates accessibility attributes for tabs
 * 
 * @param index - The index of the tab
 * @returns Object containing id and aria-controls attributes for accessibility
 */
export function a11yProps(index: number) {
  return {
    id: `tab-${index}`,
    'aria-controls': `tabpanel-${index}`,
  };
}

/**
 * Accessible tab panel component that displays content based on the selected tab
 * Used throughout the application for tabbed interfaces such as molecule details and submission views
 * 
 * @param props - The component props
 * @returns A tab panel component with proper accessibility attributes
 */
const TabPanel: React.FC<TabPanelProps> = (props) => {
  const { children, value, index, label, className, ...other } = props;
  const selected = value === index;

  return (
    <StyledTabPanel
      role="tabpanel"
      hidden={!selected}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      className={className}
      {...other}
    >
      {selected && (
        <Box>
          {label && (
            <Typography variant="h6" component="div" gutterBottom>
              {label}
            </Typography>
          )}
          {children}
        </Box>
      )}
    </StyledTabPanel>
  );
};

export default TabPanel;