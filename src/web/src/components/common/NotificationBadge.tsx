import React, { useState, useCallback, useEffect } from 'react';
import { useSelector } from 'react-redux';
import Badge from '@mui/material/Badge';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import NotificationsIcon from '@mui/icons-material/Notifications';
import { styled } from '@mui/material/styles';

import { useNotificationContext } from '../../contexts/NotificationContext';
import { selectNotifications, NotificationType } from '../../features/ui/uiSlice';
import { formatDistanceToNow } from '../../utils/dateFormatter';

/**
 * Props for the NotificationBadge component
 */
interface NotificationBadgeProps {
  /** Optional CSS class name for styling the badge */
  className?: string;
  /** Maximum number of notifications to display in the dropdown */
  maxDisplayed?: number;
  /** Optional callback when a notification is clicked */
  onNotificationClick?: (notification: Notification) => void;
}

/**
 * Interface for notification objects
 */
interface Notification {
  /** Unique identifier for the notification */
  id: string;
  /** Type of notification (success, error, warning, info) */
  type: NotificationType;
  /** Notification message content */
  message: string;
  /** When the notification was created */
  timestamp: Date;
  /** Whether the notification has been read */
  read: boolean;
  /** Optional link to navigate to when clicked */
  link?: string;
  /** Optional additional data related to the notification */
  data?: any;
}

// Default maximum number of notifications to display in the dropdown
const DEFAULT_MAX_DISPLAYED = 5;

// Mapping of notification types to theme colors
const NOTIFICATION_TYPE_COLORS: Record<NotificationType, string> = {
  success: 'success.main',
  error: 'error.main',
  warning: 'warning.main',
  info: 'info.main'
};

/**
 * Styled version of Material UI Badge component with custom styling
 */
const StyledBadge = styled(Badge)(({ theme }) => ({
  '& .MuiBadge-badge': {
    backgroundColor: theme.palette.error.main,
    color: theme.palette.error.contrastText,
    fontSize: '0.75rem',
    fontWeight: 'bold',
    minWidth: '18px',
    height: '18px',
    padding: '0 4px',
    boxShadow: `0 0 0 2px ${theme.palette.background.paper}`,
    '&.MuiBadge-invisible': {
      display: 'none'
    }
  },
  '@keyframes pulse': {
    '0%': {
      transform: 'scale(1)'
    },
    '50%': {
      transform: 'scale(1.1)'
    },
    '100%': {
      transform: 'scale(1)'
    }
  },
  '& .MuiBadge-badge:not(.MuiBadge-invisible)': {
    animation: 'pulse 1.5s infinite'
  }
}));

/**
 * Component for rendering individual notification items in the dropdown
 */
const NotificationItem: React.FC<{
  notification: Notification;
  onClick: (notification: Notification) => void;
}> = ({ notification, onClick }) => {
  const handleClick = useCallback(() => {
    onClick(notification);
  }, [notification, onClick]);

  return (
    <MenuItem 
      onClick={handleClick}
      sx={{
        opacity: notification.read ? 0.7 : 1,
        bgcolor: (theme) => notification.read 
          ? 'transparent' 
          : `${theme.palette[notification.type].light}15`, // 15 is for 0.15 opacity in hex
        borderLeft: (theme) => `3px solid ${theme.palette[notification.type].main}`,
        py: 1,
        px: 2
      }}
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%', maxWidth: 300 }}>
        <Typography variant="body2" noWrap fontWeight={notification.read ? 'normal' : 'bold'}>
          {notification.message}
        </Typography>
        <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5 }}>
          {formatDistanceToNow(notification.timestamp)}
        </Typography>
      </Box>
    </MenuItem>
  );
};

/**
 * A component that displays a badge with notification count and a dropdown menu of notifications
 */
const NotificationBadge: React.FC<NotificationBadgeProps> = ({ 
  className, 
  maxDisplayed = DEFAULT_MAX_DISPLAYED,
  onNotificationClick
}) => {
  // Get notifications from Redux store
  const notifications = useSelector(selectNotifications);
  
  // State for the menu anchor element
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  
  // Access notification context for dismissing notifications
  const { dismiss } = useNotificationContext();
  
  // Handler for opening the notification menu
  const handleOpenMenu = useCallback((event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  }, []);
  
  // Handler for closing the notification menu
  const handleCloseMenu = useCallback(() => {
    setAnchorEl(null);
  }, []);
  
  // Calculate unread notification count
  const unreadCount = notifications.filter(notif => !notif.read).length;
  
  // Handler for clicking on a notification
  const handleNotificationClick = useCallback((notification: Notification) => {
    if (onNotificationClick) {
      onNotificationClick(notification);
    }
    
    // If the notification has a link, navigate to it
    if (notification.link) {
      window.location.href = notification.link;
    }
    
    // Mark as read (would typically dispatch an action to Redux)
    // This would be implemented with the appropriate Redux action
    
    handleCloseMenu();
  }, [onNotificationClick, handleCloseMenu]);
  
  // Handler for marking all notifications as read
  const handleMarkAllAsRead = useCallback(() => {
    // Would typically dispatch an action to Redux to mark all as read
    // This would be implemented with the appropriate Redux action
    
    handleCloseMenu();
  }, [handleCloseMenu]);
  
  return (
    <div className={className}>
      <IconButton 
        aria-label="notifications"
        onClick={handleOpenMenu}
        color="inherit"
        size="large"
      >
        <StyledBadge 
          badgeContent={unreadCount} 
          color="error"
          invisible={unreadCount === 0}
        >
          <NotificationsIcon />
        </StyledBadge>
      </IconButton>
      
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleCloseMenu}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        PaperProps={{
          sx: {
            mt: 1,
            width: 320,
            maxHeight: 400,
          }
        }}
      >
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="subtitle1" fontWeight="bold">
            Notifications
          </Typography>
        </Box>
        <Divider />
        
        {notifications.length === 0 ? (
          <MenuItem disabled>
            <Typography variant="body2">No notifications</Typography>
          </MenuItem>
        ) : (
          <>
            {notifications.slice(0, maxDisplayed).map((notification) => (
              <NotificationItem 
                key={notification.id}
                notification={notification}
                onClick={handleNotificationClick}
              />
            ))}
            
            {notifications.length > maxDisplayed && (
              <MenuItem>
                <Typography variant="body2" color="textSecondary" align="center" sx={{ width: '100%' }}>
                  +{notifications.length - maxDisplayed} more notifications
                </Typography>
              </MenuItem>
            )}
            
            <Divider />
            
            <MenuItem onClick={handleMarkAllAsRead} sx={{ justifyContent: 'center' }}>
              <Typography variant="body2" color="primary">
                Mark All as Read
              </Typography>
            </MenuItem>
            
            <MenuItem onClick={handleCloseMenu} sx={{ justifyContent: 'center' }}>
              <Typography variant="body2">
                See All Notifications
              </Typography>
            </MenuItem>
          </>
        )}
      </Menu>
    </div>
  );
};

export default NotificationBadge;