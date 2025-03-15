import React, { useState, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Link } from 'react-router-dom';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import IconButton from '@mui/material/IconButton';
import Box from '@mui/material/Box';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Avatar from '@mui/material/Avatar';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import MenuIcon from '@mui/icons-material/Menu';
import AccountCircle from '@mui/icons-material/AccountCircle';
import Brightness4 from '@mui/icons-material/Brightness4';
import Brightness7 from '@mui/icons-material/Brightness7';
import Settings from '@mui/icons-material/Settings';
import ExitToApp from '@mui/icons-material/ExitToApp';

import LayoutLogo from './Logo';
import NotificationBadge from '../common/NotificationBadge';
import { useAuthContext } from '../../contexts/AuthContext';
import { useThemeContext } from '../../contexts/ThemeContext';
import { useNotificationContext } from '../../contexts/NotificationContext';
import { selectSidebarOpen, toggleSidebar } from '../../features/ui/uiSlice';
import { ROUTES } from '../../constants/routes';

/**
 * Props for the Header component
 */
interface HeaderProps {
  /**
   * Callback function when the menu button is clicked
   */
  onMenuToggle?: () => void;
}

/**
 * Main header component that displays the application logo, navigation controls, and user menu
 */
const Header: React.FC<HeaderProps> = ({ onMenuToggle }) => {
  // Access auth state from context
  const { authState, logout: handleLogout } = useAuthContext();
  
  // Access theme context for theme toggling
  const { mode, toggleTheme } = useThemeContext();
  
  // Get sidebar state from Redux store
  const sidebarOpen = useSelector(selectSidebarOpen);
  const dispatch = useDispatch();
  
  // State for user profile menu
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  
  // Handler for opening user menu
  const handleUserMenuOpen = useCallback((event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  }, []);
  
  // Handler for closing user menu
  const handleUserMenuClose = useCallback(() => {
    setAnchorEl(null);
  }, []);
  
  // Handler for toggling sidebar
  const handleSidebarToggle = useCallback(() => {
    dispatch(toggleSidebar());
    if (onMenuToggle) {
      onMenuToggle();
    }
  }, [dispatch, onMenuToggle]);
  
  // Handler for navigating to profile page
  const handleProfileClick = useCallback(() => {
    handleUserMenuClose();
    // Navigate to profile page handled by Link component in the menu item
  }, [handleUserMenuClose]);
  
  // Handler for logging out
  const handleLogoutClick = useCallback(() => {
    handleUserMenuClose();
    handleLogout();
  }, [handleUserMenuClose, handleLogout]);
  
  // Handler for toggling theme
  const handleThemeToggle = useCallback(() => {
    toggleTheme();
  }, [toggleTheme]);
  
  // Get current theme and media query for responsive design
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  // User initials for avatar
  const userInitials = authState.user?.full_name 
    ? authState.user.full_name.charAt(0).toUpperCase() 
    : null;
  
  return (
    <AppBar 
      position="fixed" 
      color="default" 
      elevation={1}
      sx={{ 
        zIndex: (theme) => theme.zIndex.drawer + 1,
        backgroundColor: (theme) => theme.palette.background.paper
      }}
    >
      <Toolbar>
        {/* Menu toggle button (visible on mobile) */}
        <IconButton
          edge="start"
          color="inherit"
          aria-label="toggle sidebar"
          onClick={handleSidebarToggle}
          sx={{ 
            mr: 2, 
            display: { xs: 'flex', md: isMobile ? 'flex' : 'none' }
          }}
        >
          <MenuIcon />
        </IconButton>
        
        {/* Application logo */}
        <LayoutLogo context="header" variant="default" />
        
        {/* Spacer to push remaining items to the right */}
        <Box sx={{ flexGrow: 1 }} />
        
        {/* Theme toggle button */}
        <IconButton 
          color="inherit" 
          onClick={handleThemeToggle}
          aria-label={mode === 'dark' ? 'switch to light mode' : 'switch to dark mode'}
          sx={{ mr: 1 }}
        >
          {mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
        </IconButton>
        
        {/* Notification badge */}
        <NotificationBadge 
          sx={{ mr: 1 }} 
          onNotificationClick={() => {
            // Handle notification click if needed
          }} 
        />
        
        {/* User profile button */}
        <IconButton
          edge="end"
          color="inherit"
          aria-label="account of current user"
          aria-controls="user-menu"
          aria-haspopup="true"
          onClick={handleUserMenuOpen}
        >
          <Avatar 
            sx={{ 
              width: 32, 
              height: 32,
              bgcolor: theme.palette.primary.main,
              color: theme.palette.primary.contrastText
            }}
          >
            {userInitials || <AccountCircle />}
          </Avatar>
        </IconButton>
        
        {/* User menu */}
        <Menu
          id="user-menu"
          anchorEl={anchorEl}
          keepMounted
          open={Boolean(anchorEl)}
          onClose={handleUserMenuClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          PaperProps={{
            elevation: 3,
            sx: { minWidth: 200, mt: 1 }
          }}
        >
          {authState.user && (
            <Box sx={{ px: 2, py: 1 }}>
              <Typography variant="subtitle2" noWrap>
                {authState.user.full_name}
              </Typography>
              <Typography variant="caption" color="textSecondary" noWrap>
                {authState.user.email}
              </Typography>
            </Box>
          )}
          
          <Divider />
          
          <MenuItem 
            component={Link} 
            to={ROUTES.USER.PROFILE} 
            onClick={handleProfileClick}
          >
            <AccountCircle fontSize="small" sx={{ mr: 1.5 }} />
            <Typography variant="body2">Profile</Typography>
          </MenuItem>
          
          <MenuItem 
            component={Link} 
            to={ROUTES.USER.SETTINGS} 
            onClick={handleUserMenuClose}
          >
            <Settings fontSize="small" sx={{ mr: 1.5 }} />
            <Typography variant="body2">Settings</Typography>
          </MenuItem>
          
          <Divider />
          
          <MenuItem onClick={handleLogoutClick}>
            <ExitToApp fontSize="small" sx={{ mr: 1.5 }} />
            <Typography variant="body2">Logout</Typography>
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default Header;