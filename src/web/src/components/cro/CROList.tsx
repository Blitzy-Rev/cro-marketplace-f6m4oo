import React, { useState, useEffect, useCallback } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  IconButton, 
  Tooltip, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Grid, 
  Paper, 
  Chip, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  DialogContentText 
} from '@mui/material';
import { 
  Add, 
  Edit, 
  Delete, 
  CheckCircle, 
  Cancel, 
  FilterList 
} from '@mui/icons-material';

// Internal imports
import { 
  CROService, 
  ServiceType, 
  SERVICE_TYPE_DISPLAY_NAMES, 
  CROServiceFilter 
} from '../../types/cro.types';
import { 
  getCROServices, 
  activateCROService, 
  deactivateCROService, 
  deleteCROService 
} from '../../api/croApi';
import DataTable from '../common/DataTable';
import StatusBadge from '../common/StatusBadge';
import SearchField from '../common/SearchField';
import useAuth from '../../hooks/useAuth';
import usePagination from '../../hooks/usePagination';
import useToast from '../../hooks/useToast';
import { formatCurrency } from '../../utils/formatters';

/**
 * Props for the CROList component
 */
interface CROListProps {
  /** Callback function when a service is selected */
  onServiceSelect?: (service: CROService) => void;
  /** Callback function when edit action is triggered */
  onServiceEdit?: (service: CROService) => void;
  /** Callback function when create action is triggered */
  onServiceCreate?: () => void;
  /** Whether services can be selected */
  selectable?: boolean;
  /** IDs of currently selected services */
  selectedServiceIds?: string[];
  /** Whether to show inactive services */
  showInactive?: boolean;
  /** Additional CSS class name */
  className?: string;
}

/**
 * State for the confirmation dialog
 */
interface ConfirmationDialogState {
  /** Whether the dialog is open */
  open: boolean;
  /** Dialog title */
  title: string;
  /** Dialog message */
  message: string;
  /** Action to perform on confirmation */
  confirmAction: () => void;
  /** ID of the service being acted upon */
  serviceId: string;
}

/**
 * Component that displays a list of CRO services with filtering, sorting, and pagination capabilities.
 * This component allows for browsing and selecting CRO services in both administrative and submission workflows.
 * 
 * @param props Component props
 * @returns The rendered CRO list component
 */
const CROList: React.FC<CROListProps> = ({
  onServiceSelect,
  onServiceEdit,
  onServiceCreate,
  selectable = false,
  selectedServiceIds = [],
  showInactive = false,
  className
}) => {
  // State for services data and loading/error status
  const [services, setServices] = useState<CROService[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // State for filters
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [serviceType, setServiceType] = useState<ServiceType | null>(null);
  const [showInactiveServices, setShowInactiveServices] = useState<boolean>(showInactive);

  // State for confirmation dialog (delete/deactivate)
  const [confirmDialog, setConfirmDialog] = useState<ConfirmationDialogState>({
    open: false,
    title: '',
    message: '',
    confirmAction: () => {},
    serviceId: ''
  });

  // Hooks
  const pagination = usePagination({
    initialPage: 1,
    initialLimit: 10,
    total: 0
  });
  const toast = useToast();
  const { hasPermission } = useAuth();

  // Check permissions for CRO service management
  const canManageCROServices = hasPermission(['system_admin', 'cro_admin']);

  /**
   * Fetches CRO services with pagination and filters
   */
  const fetchServices = useCallback(async () => {
    try {
      setLoading(true);
      
      // Prepare filter params
      const filters: CROServiceFilter = {
        name_contains: searchQuery || null,
        provider_contains: null,
        service_type: serviceType,
        price_min: null,
        price_max: null,
        turnaround_max: null,
        active_only: !showInactiveServices ? true : null
      };
      
      // Fetch services
      const response = await getCROServices(
        pagination.page,
        pagination.limit,
        filters
      );
      
      setServices(response.items);
      pagination.paginationParams.page = response.page;
      pagination.paginationParams.page_size = response.size;
      
      // Update total for pagination
      const total = response.total || 0;
      pagination.totalPages = Math.ceil(total / pagination.limit);
      
      setError(null);
    } catch (err) {
      console.error('Error fetching CRO services:', err);
      setError('Failed to load CRO services. Please try again.');
      toast.error('Failed to load CRO services.');
    } finally {
      setLoading(false);
    }
  }, [
    pagination.page,
    pagination.limit,
    searchQuery,
    serviceType,
    showInactiveServices,
    toast
  ]);

  // Load services on mount and when filters change
  useEffect(() => {
    fetchServices();
  }, [fetchServices]);

  /**
   * Handles search query changes
   */
  const handleSearchChange = (query: string) => {
    setSearchQuery(query);
  };

  /**
   * Handles service type filter changes
   */
  const handleServiceTypeChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setServiceType(event.target.value as ServiceType | null);
  };

  /**
   * Handles inactive services filter toggle
   */
  const handleShowInactiveChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setShowInactiveServices(event.target.checked);
  };

  /**
   * Handles service selection
   */
  const handleServiceSelect = (service: CROService) => {
    if (onServiceSelect) {
      onServiceSelect(service);
    }
  };

  /**
   * Handles service editing
   */
  const handleServiceEdit = (service: CROService) => {
    if (onServiceEdit) {
      onServiceEdit(service);
    }
  };

  /**
   * Opens confirmation dialog for service activation
   */
  const handleActivateService = (serviceId: string) => {
    const service = services.find(s => s.id === serviceId);
    if (!service) return;

    setConfirmDialog({
      open: true,
      title: 'Activate Service',
      message: `Are you sure you want to activate ${service.name}?`,
      confirmAction: async () => {
        try {
          await activateCROService(serviceId);
          toast.success(`Service ${service.name} has been activated.`);
          fetchServices();
        } catch (err) {
          toast.error(`Failed to activate service: ${toast.formatError(err)}`);
        }
        setConfirmDialog(prev => ({ ...prev, open: false }));
      },
      serviceId
    });
  };

  /**
   * Opens confirmation dialog for service deactivation
   */
  const handleDeactivateService = (serviceId: string) => {
    const service = services.find(s => s.id === serviceId);
    if (!service) return;

    setConfirmDialog({
      open: true,
      title: 'Deactivate Service',
      message: `Are you sure you want to deactivate ${service.name}? It will no longer be available for new submissions.`,
      confirmAction: async () => {
        try {
          await deactivateCROService(serviceId);
          toast.success(`Service ${service.name} has been deactivated.`);
          fetchServices();
        } catch (err) {
          toast.error(`Failed to deactivate service: ${toast.formatError(err)}`);
        }
        setConfirmDialog(prev => ({ ...prev, open: false }));
      },
      serviceId
    });
  };

  /**
   * Opens confirmation dialog for service deletion
   */
  const handleDeleteService = (serviceId: string) => {
    const service = services.find(s => s.id === serviceId);
    if (!service) return;

    setConfirmDialog({
      open: true,
      title: 'Delete Service',
      message: `Are you sure you want to permanently delete ${service.name}? This action cannot be undone.`,
      confirmAction: async () => {
        try {
          await deleteCROService(serviceId);
          toast.success(`Service ${service.name} has been deleted.`);
          fetchServices();
        } catch (err) {
          toast.error(`Failed to delete service: ${toast.formatError(err)}`);
        }
        setConfirmDialog(prev => ({ ...prev, open: false }));
      },
      serviceId
    });
  };

  /**
   * Closes the confirmation dialog without taking action
   */
  const handleCancelConfirmation = () => {
    setConfirmDialog(prev => ({ ...prev, open: false }));
  };

  /**
   * Define table columns for CRO services
   */
  const columns = [
    {
      id: 'name',
      label: 'Service Name',
      sortable: true,
      renderCell: (row: CROService) => (
        <Box>
          <Typography variant="body1" fontWeight="medium">{row.name}</Typography>
          <Typography variant="body2" color="text.secondary">{row.provider}</Typography>
        </Box>
      )
    },
    {
      id: 'service_type',
      label: 'Service Type',
      sortable: true,
      renderCell: (row: CROService) => SERVICE_TYPE_DISPLAY_NAMES[row.service_type]
    },
    {
      id: 'base_price',
      label: 'Base Price',
      sortable: true,
      renderCell: (row: CROService) => formatCurrency(row.base_price, row.price_currency)
    },
    {
      id: 'typical_turnaround_days',
      label: 'Turnaround Time',
      sortable: true,
      renderCell: (row: CROService) => `${row.typical_turnaround_days} days`
    },
    {
      id: 'active',
      label: 'Status',
      sortable: true,
      renderCell: (row: CROService) => (
        <StatusBadge 
          status={row.active ? 'ACTIVE' : 'INACTIVE'} 
          statusType="custom"
          customColor={row.active ? '#4caf50' : '#f44336'}
          customLabel={row.active ? 'Active' : 'Inactive'}
        />
      )
    }
  ];

  // Add actions column if user has permissions to manage services
  if (canManageCROServices) {
    columns.push({
      id: 'actions',
      label: 'Actions',
      sortable: false,
      renderCell: (row: CROService) => (
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Tooltip title="Edit Service">
            <IconButton 
              size="small" 
              onClick={(e) => {
                e.stopPropagation();
                handleServiceEdit(row);
              }}
            >
              <Edit fontSize="small" />
            </IconButton>
          </Tooltip>
          
          {row.active ? (
            <Tooltip title="Deactivate Service">
              <IconButton 
                size="small" 
                color="warning"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeactivateService(row.id);
                }}
              >
                <Cancel fontSize="small" />
              </IconButton>
            </Tooltip>
          ) : (
            <Tooltip title="Activate Service">
              <IconButton 
                size="small" 
                color="success"
                onClick={(e) => {
                  e.stopPropagation();
                  handleActivateService(row.id);
                }}
              >
                <CheckCircle fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          
          <Tooltip title="Delete Service">
            <IconButton 
              size="small" 
              color="error"
              onClick={(e) => {
                e.stopPropagation();
                handleDeleteService(row.id);
              }}
            >
              <Delete fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      )
    });
  }

  return (
    <Box className={className}>
      {/* Filter Bar */}
      <FilterBar
        searchQuery={searchQuery}
        onSearchChange={handleSearchChange}
        serviceType={serviceType}
        onServiceTypeChange={handleServiceTypeChange}
        showInactive={showInactiveServices}
        onShowInactiveChange={handleShowInactiveChange}
      />

      {/* Service Table */}
      <Paper sx={{ mt: 2, width: '100%' }}>
        <DataTable
          columns={columns}
          data={services}
          loading={loading}
          selectable={selectable}
          selected={selectedServiceIds}
          onRowClick={handleServiceSelect}
          pagination={true}
          totalCount={pagination.totalPages * pagination.limit}
          currentPage={pagination.page}
          pageSize={pagination.limit}
          onPageChange={pagination.handlePageChange}
          onPageSizeChange={pagination.handleLimitChange}
          emptyMessage="No CRO services found. Please adjust your filters or add a new service."
          getRowId={(row: CROService) => row.id}
        />
      </Paper>

      {/* Add Service Button (Admin only) */}
      {canManageCROServices && onServiceCreate && (
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<Add />}
            onClick={onServiceCreate}
          >
            Add Service
          </Button>
        </Box>
      )}

      {/* Confirmation Dialog */}
      <ConfirmationDialog
        open={confirmDialog.open}
        title={confirmDialog.title}
        message={confirmDialog.message}
        onConfirm={confirmDialog.confirmAction}
        onCancel={handleCancelConfirmation}
      />
    </Box>
  );
};

/**
 * Component for filtering CRO services
 */
const FilterBar: React.FC<{
  searchQuery: string;
  onSearchChange: (query: string) => void;
  serviceType: ServiceType | null;
  onServiceTypeChange: (event: React.ChangeEvent<{ value: unknown }>) => void;
  showInactive: boolean;
  onShowInactiveChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
}> = ({
  searchQuery,
  onSearchChange,
  serviceType,
  onServiceTypeChange,
  showInactive,
  onShowInactiveChange
}) => {
  return (
    <Paper sx={{ p: 2 }}>
      <Grid container spacing={2} alignItems="center">
        <Grid item xs={12} sm={6} md={4}>
          <SearchField
            value={searchQuery}
            onChange={onSearchChange}
            placeholder="Search services..."
            fullWidth
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <FormControl fullWidth size="small">
            <InputLabel id="service-type-label">Service Type</InputLabel>
            <Select
              labelId="service-type-label"
              id="service-type"
              value={serviceType || ''}
              label="Service Type"
              onChange={onServiceTypeChange as any}
              displayEmpty
            >
              <MenuItem value="">All Types</MenuItem>
              {Object.entries(SERVICE_TYPE_DISPLAY_NAMES).map(([value, label]) => (
                <MenuItem key={value} value={value}>
                  {label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} sm={12} md={4}>
          <Box display="flex" alignItems="center">
            <Chip
              icon={<FilterList />}
              label={showInactive ? "Showing inactive services" : "Hiding inactive services"}
              variant={showInactive ? "filled" : "outlined"}
              color={showInactive ? "primary" : "default"}
              onClick={() => onShowInactiveChange({ target: { checked: !showInactive } } as any)}
              sx={{ mr: 1 }}
            />
          </Box>
        </Grid>
      </Grid>
    </Paper>
  );
};

/**
 * Dialog for confirming destructive actions
 */
const ConfirmationDialog: React.FC<{
  open: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}> = ({
  open,
  title,
  message,
  onConfirm,
  onCancel
}) => {
  return (
    <Dialog
      open={open}
      onClose={onCancel}
      aria-labelledby="confirmation-dialog-title"
      aria-describedby="confirmation-dialog-description"
    >
      <DialogTitle id="confirmation-dialog-title">{title}</DialogTitle>
      <DialogContent>
        <DialogContentText id="confirmation-dialog-description">
          {message}
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>Cancel</Button>
        <Button onClick={onConfirm} color="primary" variant="contained" autoFocus>
          Confirm
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CROList;