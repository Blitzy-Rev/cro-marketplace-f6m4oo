import React, { useState, useEffect, useCallback } from 'react';
import { 
  Box, Typography, Paper, Grid, Divider, Button, Chip, CircularProgress, Alert,
  Card, CardContent, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, IconButton
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { Edit, CheckCircle, Cancel, ArrowBack } from '@mui/icons-material';
import { CROService, ServiceType, SERVICE_TYPE_DISPLAY_NAMES } from '../../types/cro.types';
import { getCROService, activateCROService, deactivateCROService } from '../../api/croApi';
import StatusBadge from '../common/StatusBadge';
import useAuth from '../../hooks/useAuth';
import useToast from '../../hooks/useToast';
import { formatCurrency } from '../../utils/formatters';
import { formatDate } from '../../utils/dateFormatter';

// Props for the component
interface CRODetailProps {
  serviceId: string;
  onEdit?: (service: CROService) => void;
  onBack?: () => void;
  className?: string;
}

// Interface for confirmation dialog state
interface ConfirmationDialogState {
  open: boolean;
  title: string;
  message: string;
  confirmAction: () => void;
}

// Styled components
const DetailCard = styled(Card)({
  marginBottom: '16px',
  overflow: 'visible'
});

const DetailCardContent = styled(CardContent)({
  padding: '16px'
});

const SectionTitle = styled(Typography)({
  fontWeight: '500',
  marginBottom: '8px'
});

const CRODetail: React.FC<CRODetailProps> = ({ 
  serviceId,
  onEdit,
  onBack,
  className
}) => {
  // State
  const [service, setService] = useState<CROService | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [confirmDialog, setConfirmDialog] = useState<ConfirmationDialogState>({
    open: false,
    title: '',
    message: '',
    confirmAction: () => {}
  });
  
  // Hooks
  const toast = useToast();
  const { hasPermission } = useAuth();
  const canManageCROServices = hasPermission(['SYSTEM_ADMIN', 'CRO_ADMIN']);
  
  // Fetch CRO service details
  const fetchService = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await getCROService(serviceId);
      setService(response.service);
      setLoading(false);
    } catch (err) {
      setError('Failed to load CRO service details');
      setLoading(false);
    }
  }, [serviceId]);

  // Load service when component mounts or serviceId changes
  useEffect(() => {
    fetchService();
  }, [fetchService]);
  
  // Handle edit button click
  const handleEdit = useCallback(() => {
    if (service && onEdit) {
      onEdit(service);
    }
  }, [service, onEdit]);
  
  // Handle activate button click
  const handleActivate = useCallback(async () => {
    if (!service) return;
    
    try {
      const response = await activateCROService(service.id);
      setService(response.service);
      toast.success('CRO service activated successfully');
    } catch (err) {
      toast.error('Failed to activate CRO service');
    }
  }, [service, toast]);
  
  // Handle deactivate button click (shows confirmation dialog)
  const handleDeactivate = useCallback(() => {
    if (!service) return;
    
    setConfirmDialog({
      open: true,
      title: 'Deactivate CRO Service',
      message: `Are you sure you want to deactivate "${service.name}"? This will make it unavailable for new submissions.`,
      confirmAction: () => confirmDeactivate()
    });
  }, [service]);
  
  // Confirm deactivation action
  const confirmDeactivate = useCallback(async () => {
    if (!service) return;
    
    try {
      const response = await deactivateCROService(service.id);
      setService(response.service);
      toast.success('CRO service deactivated successfully');
    } catch (err) {
      toast.error('Failed to deactivate CRO service');
    } finally {
      // Close the dialog
      setConfirmDialog(prev => ({ ...prev, open: false }));
    }
  }, [service, toast]);
  
  // Loading state
  if (loading) {
    return (
      <Box className={className} sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Error state
  if (error || !service) {
    return (
      <Box className={className} sx={{ p: 3 }}>
        <Alert severity="error">
          {error || 'Service not found'}
        </Alert>
        {onBack && (
          <Button 
            startIcon={<ArrowBack />} 
            onClick={onBack} 
            sx={{ mt: 2 }}
          >
            Back
          </Button>
        )}
      </Box>
    );
  }
  
  // Service header component
  const ServiceHeader = ({ service, canEdit, onEdit }: { 
    service: CROService; 
    canEdit: boolean;
    onEdit: ((service: CROService) => void) | undefined;
  }) => (
    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
      <Box sx={{ flex: 1 }}>
        <Typography variant="h4">{service.name}</Typography>
        <Typography variant="subtitle1" color="text.secondary">
          {service.provider}
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <StatusBadge 
          status={service.active ? 'Active' : 'Inactive'} 
          statusType="custom" 
          customColor={service.active ? '#4caf50' : '#f44336'} 
          customLabel={service.active ? 'Active' : 'Inactive'} 
          size="medium"
        />
        {canEdit && onEdit && (
          <IconButton 
            color="primary" 
            onClick={() => onEdit(service)} 
            sx={{ ml: 1 }}
            aria-label="Edit service"
          >
            <Edit />
          </IconButton>
        )}
      </Box>
    </Box>
  );

  // Service details component
  const ServiceDetails = ({ service }: { service: CROService }) => (
    <DetailCard>
      <DetailCardContent>
        <SectionTitle variant="h6">Service Details</SectionTitle>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <Typography variant="body1">
              {service.description || 'No description provided'}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Typography variant="body2" color="text.secondary">Service Type</Typography>
            <Typography variant="body1">
              {service.service_type ? SERVICE_TYPE_DISPLAY_NAMES[service.service_type] : 'Unknown'}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Typography variant="body2" color="text.secondary">Base Price</Typography>
            <Typography variant="body1">
              {formatCurrency(service.base_price, service.price_currency)}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Typography variant="body2" color="text.secondary">Typical Turnaround Time</Typography>
            <Typography variant="body1">
              {service.typical_turnaround_days} days
            </Typography>
          </Grid>
        </Grid>
      </DetailCardContent>
    </DetailCard>
  );

  // Service specifications component
  const ServiceSpecifications = ({ specifications }: { specifications: Record<string, any> | null }) => {
    if (!specifications || Object.keys(specifications).length === 0) {
      return null;
    }
    
    return (
      <DetailCard>
        <DetailCardContent>
          <SectionTitle variant="h6">Service Specifications</SectionTitle>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Parameter</TableCell>
                  <TableCell>Value</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {Object.entries(specifications).map(([key, value]) => (
                  <TableRow key={key}>
                    <TableCell>{key}</TableCell>
                    <TableCell>{String(value)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DetailCardContent>
      </DetailCard>
    );
  };

  // Service statistics component
  const ServiceStatistics = ({ service }: { service: CROService }) => (
    <DetailCard>
      <DetailCardContent>
        <SectionTitle variant="h6">Service Statistics</SectionTitle>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={4}>
            <Typography variant="body2" color="text.secondary">Created</Typography>
            <Typography variant="body1">
              {formatDate(service.created_at)}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Typography variant="body2" color="text.secondary">Last Updated</Typography>
            <Typography variant="body1">
              {formatDate(service.updated_at)}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Typography variant="body2" color="text.secondary">Submission Count</Typography>
            <Typography variant="body1">
              {service.submission_count !== null ? service.submission_count : 'N/A'}
            </Typography>
          </Grid>
        </Grid>
      </DetailCardContent>
    </DetailCard>
  );

  // Confirmation dialog component
  const ConfirmationDialog = ({ 
    open, 
    title, 
    message, 
    onConfirm, 
    onCancel 
  }: {
    open: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
    onCancel: () => void;
  }) => (
    <Dialog open={open} onClose={onCancel}>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <DialogContentText>{message}</DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel} color="primary">
          Cancel
        </Button>
        <Button onClick={onConfirm} color="error" autoFocus>
          Confirm
        </Button>
      </DialogActions>
    </Dialog>
  );
  
  // Main render
  return (
    <Box className={className}>
      {/* Back button */}
      {onBack && (
        <Button 
          startIcon={<ArrowBack />} 
          onClick={onBack} 
          sx={{ mb: 2 }}
        >
          Back
        </Button>
      )}
      
      {/* Service header */}
      <ServiceHeader 
        service={service} 
        canEdit={canManageCROServices} 
        onEdit={onEdit} 
      />
      
      <Divider sx={{ mb: 3 }} />
      
      {/* Service details */}
      <ServiceDetails service={service} />
      
      {/* Service specifications */}
      <ServiceSpecifications specifications={service.specifications} />
      
      {/* Service statistics */}
      <ServiceStatistics service={service} />
      
      {/* Action buttons */}
      {canManageCROServices && (
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
          {service.active ? (
            <Button 
              variant="contained" 
              color="error" 
              startIcon={<Cancel />} 
              onClick={handleDeactivate}
            >
              Deactivate Service
            </Button>
          ) : (
            <Button 
              variant="contained" 
              color="success" 
              startIcon={<CheckCircle />} 
              onClick={handleActivate}
            >
              Activate Service
            </Button>
          )}
        </Box>
      )}
      
      {/* Confirmation dialog */}
      <ConfirmationDialog
        open={confirmDialog.open}
        title={confirmDialog.title}
        message={confirmDialog.message}
        onConfirm={confirmDialog.confirmAction}
        onCancel={() => setConfirmDialog(prev => ({ ...prev, open: false }))}
      />
    </Box>
  );
};

export default CRODetail;