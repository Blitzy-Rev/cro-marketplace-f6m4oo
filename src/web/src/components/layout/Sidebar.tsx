import React, { useEffect } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Box,
  Tooltip,
  IconButton,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { styled } from '@mui/material/styles';
import { NavLink, useLocation } from 'react-router-dom';

// Icons
import DashboardIcon from '@mui/icons-material/Dashboard';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CollectionsIcon from '@mui/icons-material/Collections';
import ScienceIcon from '@mui/icons-material/Science';
import SendIcon from '@mui/icons-material/Send';
import AssessmentIcon from '@mui/icons-material/Assessment';
import BusinessIcon from '@mui/icons-material/Business';
import SettingsIcon from '@mui/icons-material/Settings';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';

// Internal imports
import LayoutLogo from './Logo';
import { ROUTES } from '../../constants/routes';
import { useAuthContext } from '../../contexts/AuthContext';
import { 
  isPharmaRole, 
  isCRORole, 
  hasRolePermission,
  SYSTEM_ADMIN,
  PHARMA_ADMIN,
  PHARMA_SCIENTIST,
  CRO_ADMIN,
  CRO_TECHNICIAN,
  AUDITOR
} from '../../constants/userRoles';

// Constants
const DRAWER_WIDTH = 240;
const DRAWER_COLLAPSED_WIDTH = 64;

// Interfaces
interface SidebarProps {
  open: boolean;
  onClose: () => void;
  variant: 'permanent' | 'temporary';
}

interface NavigationItem {
  text: string;
  icon: React.ReactNode;
  path: string;
  roles: string[];
}

// Styled components
const DrawerHeader = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: theme.spacing(0, 1),
  minHeight: '64px',
  borderBottom: `1px solid ${theme.palette.divider}`
}));

// Navigation items definition
const navigationItems: NavigationItem[] = [
  {
    text: 'Dashboard',
    icon: <DashboardIcon />,
    path: ROUTES.DASHBOARD.HOME,
    roles: [SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST, CRO_ADMIN, CRO_TECHNICIAN]
  },
  {
    text: 'Upload',
    icon: <CloudUploadIcon />,
    path: ROUTES.MOLECULES.UPLOAD,
    roles: [SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST]
  },
  {
    text: 'My Libraries',
    icon: <CollectionsIcon />,
    path: ROUTES.LIBRARIES.LIST,
    roles: [SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST]
  },
  {
    text: 'Molecules',
    icon: <ScienceIcon />,
    path: ROUTES.MOLECULES.LIST,
    roles: [SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST]
  },
  {
    text: 'CRO Submissions',
    icon: <SendIcon />,
    path: ROUTES.SUBMISSIONS.LIST,
    roles: [SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST]
  },
  {
    text: 'Results',
    icon: <AssessmentIcon />,
    path: ROUTES.RESULTS.LIST,
    roles: [SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST]
  },
  {
    text: 'CRO Dashboard',
    icon: <BusinessIcon />,
    path: ROUTES.CRO.DASHBOARD,
    roles: [SYSTEM_ADMIN, CRO_ADMIN, CRO_TECHNICIAN]
  },
  {
    text: 'Settings',
    icon: <SettingsIcon />,
    path: ROUTES.USER.SETTINGS,
    roles: [SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST, CRO_ADMIN, CRO_TECHNICIAN]
  }
];

/**
 * Sidebar component that displays navigation options based on user role
 */
const Sidebar: React.FC<SidebarProps> = ({ open, onClose, variant }) => {
  const { authState } = useAuthContext();
  const location = useLocation();
  const theme = useTheme();

  // Get user role from auth state
  const userRole = authState.user?.role;

  // Filter navigation items based on user role
  const filteredNavItems = navigationItems.filter(item => {
    if (!userRole) return false;
    return hasRolePermission(userRole, item.roles);
  });

  // Effect to handle closing drawer on navigation for mobile view
  useEffect(() => {
    if (variant === 'temporary' && open) {
      onClose();
    }
  }, [location, variant, open, onClose]);

  return (
    <Drawer
      variant={variant}
      open={open}
      onClose={onClose}
      sx={{
        width: open ? DRAWER_WIDTH : DRAWER_COLLAPSED_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: open ? DRAWER_WIDTH : DRAWER_COLLAPSED_WIDTH,
          boxSizing: 'border-box',
          overflowX: 'hidden',
          transition: theme.transitions.create(['width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
        },
      }}
    >
      {/* Drawer Header with Logo and toggle button */}
      <DrawerHeader>
        <LayoutLogo variant="default" collapsed={!open} context="sidebar" />
        {variant === 'permanent' && (
          <IconButton onClick={onClose} size="small" aria-label={open ? "Collapse sidebar" : "Expand sidebar"}>
            {theme.direction === 'rtl' ? <ChevronRightIcon /> : <ChevronLeftIcon />}
          </IconButton>
        )}
      </DrawerHeader>
      
      <Divider />
      
      {/* Navigation Items */}
      <List sx={{ pt: 0 }}>
        {filteredNavItems.map((item) => {
          const isActive = location.pathname === item.path || 
            (item.path !== ROUTES.DASHBOARD.HOME && location.pathname.startsWith(item.path));
            
          return (
            <Tooltip
              key={item.text}
              title={open ? '' : item.text}
              placement="right"
              disableHoverListener={open}
            >
              <ListItem
                component={NavLink}
                to={item.path}
                onClick={() => variant === 'temporary' && onClose()}
                sx={{
                  minHeight: 48,
                  px: open ? 2.5 : 1,
                  justifyContent: open ? 'initial' : 'center',
                  bgcolor: isActive ? theme.palette.action.selected : 'transparent',
                  borderLeft: isActive ? `4px solid ${theme.palette.primary.main}` : '4px solid transparent',
                  '&:hover': {
                    bgcolor: theme.palette.action.hover,
                  },
                  '&.active': {
                    bgcolor: theme.palette.action.selected,
                    borderLeft: `4px solid ${theme.palette.primary.main}`,
                  }
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 0,
                    mr: open ? 2 : 'auto',
                    justifyContent: 'center',
                    color: isActive ? theme.palette.primary.main : 'inherit',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.text} 
                  sx={{ 
                    opacity: open ? 1 : 0,
                    display: open ? 'block' : 'none',
                    color: isActive ? theme.palette.primary.main : 'inherit',
                  }} 
                />
              </ListItem>
            </Tooltip>
          );
        })}
      </List>
    </Drawer>
  );
};

export default Sidebar;