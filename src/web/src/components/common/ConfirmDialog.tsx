import React from 'react';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import CloseIcon from '@mui/icons-material/Close';
import WarningIcon from '@mui/icons-material/Warning';
import { palette } from '../../assets/theme/palette';

/**
 * Props interface for the ConfirmDialog component
 */
interface ConfirmDialogProps {
  /** Controls whether the dialog is open or closed */
  open: boolean;
  /** Title text for the confirmation dialog */
  title: string;
  /** Content message of the confirmation dialog, can be text or React elements */
  message: string | React.ReactNode;
  /** Text for the confirm button */
  confirmButtonText?: string;
  /** Text for the cancel button */
  cancelButtonText?: string;
  /** Callback function called when the confirm button is clicked */
  onConfirm: () => void;
  /** Callback function called when the dialog is closed or canceled */
  onClose: () => void;
  /** Whether to show the X close button in the top-right corner */
  showCloseButton?: boolean;
  /** Maximum width of the dialog */
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  /** Whether the dialog should take up the full width of its container */
  fullWidth?: boolean;
  /** Whether clicking the backdrop should close the dialog */
  disableBackdropClick?: boolean;
  /** Whether pressing the Escape key should close the dialog */
  disableEscapeKeyDown?: boolean;
  /** Color of the confirm button */
  confirmButtonColor?: 'primary' | 'error' | 'warning' | 'info' | 'success';
  /** Color of the cancel button */
  cancelButtonColor?: 'primary' | 'error' | 'warning' | 'info' | 'success' | 'inherit';
  /** Whether to show a warning icon in the dialog */
  showWarningIcon?: boolean;
}

/**
 * A reusable confirmation dialog component that prompts users to confirm or cancel an action.
 * This component is used throughout the application for potentially destructive or important actions
 * that require explicit user confirmation.
 */
const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  title,
  message,
  confirmButtonText = 'Confirm',
  cancelButtonText = 'Cancel',
  onConfirm,
  onClose,
  showCloseButton = true,
  maxWidth = 'sm',
  fullWidth = true,
  disableBackdropClick = false,
  disableEscapeKeyDown = false,
  confirmButtonColor = 'primary',
  cancelButtonColor = 'inherit',
  showWarningIcon = false,
}) => {
  /**
   * Handles the confirmation action
   */
  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  /**
   * Handles the cancel action
   */
  const handleCancel = () => {
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={(event, reason) => {
        if (disableBackdropClick && reason === 'backdropClick') {
          return;
        }
        handleCancel();
      }}
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-description"
      maxWidth={maxWidth}
      fullWidth={fullWidth}
      disableEscapeKeyDown={disableEscapeKeyDown}
    >
      <DialogTitle id="confirm-dialog-title">
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6" component="div">
            {title}
          </Typography>
          {showCloseButton && (
            <IconButton
              aria-label="close"
              onClick={handleCancel}
              size="small"
              edge="end"
            >
              <CloseIcon />
            </IconButton>
          )}
        </Box>
      </DialogTitle>
      <DialogContent>
        <Box display="flex" alignItems="flex-start" gap={2}>
          {showWarningIcon && (
            <WarningIcon 
              color="warning" 
              fontSize="medium"
              sx={{ mt: 0.5 }}
            />
          )}
          <DialogContentText id="confirm-dialog-description">
            {message}
          </DialogContentText>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button
          onClick={handleCancel}
          color={cancelButtonColor}
          variant="outlined"
          size="medium"
          sx={{ mr: 1 }}
        >
          {cancelButtonText}
        </Button>
        <Button
          onClick={handleConfirm}
          color={confirmButtonColor}
          variant="contained"
          size="medium"
          autoFocus
          sx={confirmButtonColor === 'error' ? {
            bgcolor: palette.error.main,
            '&:hover': {
              bgcolor: palette.error.dark,
            }
          } : {}}
        >
          {confirmButtonText}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConfirmDialog;