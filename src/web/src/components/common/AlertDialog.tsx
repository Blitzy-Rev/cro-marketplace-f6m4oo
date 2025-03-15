import React from 'react'; // react ^18.0.0
import { 
  Dialog, 
  DialogActions, 
  DialogContent, 
  DialogContentText, 
  DialogTitle,
  Button,
  IconButton,
  Typography,
  Box
} from '@mui/material'; // @mui/material ^5.0.0
import CloseIcon from '@mui/icons-material/Close'; // @mui/icons-material/Close ^5.0.0
import InfoIcon from '@mui/icons-material/Info'; // @mui/icons-material/Info ^5.0.0
import WarningIcon from '@mui/icons-material/Warning'; // @mui/icons-material/Warning ^5.0.0
import ErrorIcon from '@mui/icons-material/Error'; // @mui/icons-material/Error ^5.0.0
import { palette } from '../../assets/theme/palette';

/**
 * Props interface for the AlertDialog component
 */
export interface AlertDialogProps {
  /**
   * Controls whether the dialog is open or closed
   */
  open: boolean;
  
  /**
   * Title text for the alert dialog
   */
  title: string;
  
  /**
   * Content message of the alert dialog, can be text or React elements
   */
  message: string | React.ReactNode;
  
  /**
   * Text for the acknowledgment button
   * @default "OK"
   */
  buttonText?: string;
  
  /**
   * Callback function called when the dialog is closed
   */
  onClose: () => void;
  
  /**
   * Whether to show the X close button in the top-right corner
   * @default true
   */
  showCloseButton?: boolean;
  
  /**
   * Maximum width of the dialog
   * @default "sm"
   */
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  
  /**
   * Whether the dialog should take up the full width of its container
   * @default true
   */
  fullWidth?: boolean;
  
  /**
   * Whether clicking the backdrop should close the dialog
   * @default false
   */
  disableBackdropClick?: boolean;
  
  /**
   * Whether pressing the Escape key should close the dialog
   * @default false
   */
  disableEscapeKeyDown?: boolean;
  
  /**
   * Severity level of the alert, affects styling and icon
   * @default "info"
   */
  severity?: 'info' | 'warning' | 'error';
}

/**
 * AlertDialog component - A reusable alert dialog that displays important information 
 * with a single acknowledgment button.
 * 
 * Used throughout the application for notifications, warnings, and error messages
 * that require user attention.
 */
const AlertDialog: React.FC<AlertDialogProps> = ({
  open,
  title,
  message,
  buttonText = 'OK',
  onClose,
  showCloseButton = true,
  maxWidth = 'sm',
  fullWidth = true,
  disableBackdropClick = false,
  disableEscapeKeyDown = false,
  severity = 'info'
}) => {
  // Handle dialog close action
  const handleClose = () => {
    onClose();
  };

  // Determine icon and color based on severity
  let icon;
  let color;
  
  switch (severity) {
    case 'error':
      icon = <ErrorIcon fontSize="large" />;
      color = palette.error.main;
      break;
    case 'warning':
      icon = <WarningIcon fontSize="large" />;
      color = palette.warning.main;
      break;
    case 'info':
    default:
      icon = <InfoIcon fontSize="large" />;
      color = palette.info.main;
      break;
  }

  return (
    <Dialog
      open={open}
      onClose={(event, reason) => {
        if (disableBackdropClick && reason === 'backdropClick') {
          return;
        }
        handleClose();
      }}
      aria-labelledby="alert-dialog-title"
      aria-describedby="alert-dialog-description"
      maxWidth={maxWidth}
      fullWidth={fullWidth}
      disableEscapeKeyDown={disableEscapeKeyDown}
    >
      <DialogTitle id="alert-dialog-title" sx={{ pr: showCloseButton ? 6 : 2 }}>
        <Typography variant="h6" component="span">
          {title}
        </Typography>
        {showCloseButton && (
          <IconButton
            aria-label="close"
            onClick={handleClose}
            sx={{
              position: 'absolute',
              right: 8,
              top: 8,
              color: (theme) => theme.palette.grey[500],
            }}
          >
            <CloseIcon />
          </IconButton>
        )}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ mr: 2, color }}>
            {icon}
          </Box>
          <DialogContentText id="alert-dialog-description" component="div">
            {message}
          </DialogContentText>
        </Box>
      </DialogContent>
      <DialogActions sx={{ justifyContent: 'center', pb: 3 }}>
        <Button 
          onClick={handleClose} 
          variant="contained" 
          color={severity}
          autoFocus
          sx={{ 
            minWidth: '100px',
            fontWeight: 'medium'
          }}
        >
          {buttonText}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AlertDialog;