import React, { useState, useEffect, useCallback } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  CardActionArea, 
  Grid, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Divider,
  Chip,
  CircularProgress,
  Alert
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { CROService, ServiceType, SERVICE_TYPE_DISPLAY_NAMES } from '../../types/cro.types';
import { getCROServices } from '../../api/croApi';
import SearchField from '../common/SearchField';
import StatusBadge from '../common/StatusBadge';
import { formatCurrency } from '../../utils/formatters';

/**
 * Props for the CRO Selector component
 */
interface CROSelectorProps {
  /** ID of the currently selected CRO service */
  selectedServiceId?: string | null;
  /** Callback function when a service is selected */
  onServiceSelect: (service: CROService) => void;
  /** Whether the selector is disabled */
  disabled?: boolean;
}

/**
 * Styled Card component for displaying CRO service information
 */
const ServiceCard = styled(Card)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  transition: 'all 0.3s ease',
  '&.selected': {
    border: `2px solid ${theme.palette.primary.main}`,
    boxShadow: `0 4px 8px ${theme.palette.primary.main}20`
  }
}));

/**
 * Styled CardContent component for consistent padding and layout
 */
const ServiceCardContent = styled(CardContent)({
  flexGrow: 1,
  display: 'flex',
  flexDirection: 'column'
});

/**
 * Component for selecting a CRO service during submission creation
 * Displays available CRO services with filtering capabilities, service details,
 * and handles the selection process.
 */
const CROSelector: React.FC<CROSelectorProps> = ({ 
  selectedServiceId = null, 
  onServiceSelect,
  disabled = false
}) => {
  // State for services and loading
  const [services, setServices] = useState<CROService[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // State for filtering
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [serviceType, setServiceType] = useState<ServiceType | ''>('');

  /**
   * Fetch CRO services with optional filtering
   */
  const fetchServices = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Create filter object
      const filters = {
        name_contains: searchQuery || null,
        provider_contains: searchQuery || null,
        service_type: serviceType || null,
        active_only: true
      };
      
      const response = await getCROServices(1, 50, filters);
      setServices(response.items);
    } catch (err) {
      console.error('Error fetching CRO services:', err);
      setError('Failed to load CRO services. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, [searchQuery, serviceType]);

  // Load services on mount and when filters change
  useEffect(() => {
    fetchServices();
  }, [fetchServices]);

  /**
   * Handle search query changes
   */
  const handleSearchChange = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  /**
   * Handle service type filter changes
   */
  const handleServiceTypeChange = useCallback((event: React.ChangeEvent<{ value: unknown }>) => {
    setServiceType(event.target.value as ServiceType | '');
  }, []);

  /**
   * Handle service selection
   */
  const handleServiceSelect = useCallback((service: CROService) => {
    if (!disabled) {
      onServiceSelect(service);
    }
  }, [onServiceSelect, disabled]);

  return (
    <Box sx={{ width: '100%' }}>
      {/* Search and filter controls */}
      <Box sx={{ mb: 3, display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 2 }}>
        <SearchField 
          value={searchQuery}
          onChange={handleSearchChange}
          placeholder="Search by name or provider..."
          disabled={disabled}
          fullWidth
        />
        
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel id="service-type-label">Service Type</InputLabel>
          <Select
            labelId="service-type-label"
            id="service-type-select"
            value={serviceType}
            onChange={handleServiceTypeChange}
            label="Service Type"
            disabled={disabled}
          >
            <MenuItem value="">All Types</MenuItem>
            {Object.entries(SERVICE_TYPE_DISPLAY_NAMES).map(([value, label]) => (
              <MenuItem key={value} value={value}>{label}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* Loading indicator */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Error message */}
      {error && !loading && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Service cards */}
      {!loading && !error && services.length === 0 && (
        <Alert severity="info" sx={{ mb: 3 }}>
          No services found matching your criteria. Please try different search terms.
        </Alert>
      )}

      <Grid container spacing={3}>
        {services.map((service) => (
          <Grid item xs={12} sm={6} md={4} key={service.id}>
            <ServiceCard 
              className={selectedServiceId === service.id ? 'selected' : ''}
              sx={{ cursor: disabled ? 'default' : 'pointer' }}
            >
              <CardActionArea 
                onClick={() => handleServiceSelect(service)}
                disabled={disabled}
                sx={{ height: '100%' }}
              >
                <ServiceCardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Typography variant="h6" component="h2" gutterBottom noWrap title={service.name}>
                      {service.name}
                    </Typography>
                    <StatusBadge 
                      status={service.service_type} 
                      statusType="custom"
                      customLabel={SERVICE_TYPE_DISPLAY_NAMES[service.service_type]}
                      customColor={getServiceTypeColor(service.service_type)}
                      size="small"
                    />
                  </Box>
                  
                  <Typography 
                    variant="body2" 
                    color="text.secondary" 
                    sx={{ mb: 2 }}
                    noWrap
                    title={service.provider}
                  >
                    Provider: {service.provider}
                  </Typography>
                  
                  {service.description && (
                    <Typography 
                      variant="body2" 
                      sx={{ mb: 2, flexGrow: 1 }}
                      style={{
                        display: '-webkit-box',
                        WebkitLineClamp: 3,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis'
                      }}
                    >
                      {service.description}
                    </Typography>
                  )}
                  
                  <Divider sx={{ my: 1 }} />
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 'auto' }}>
                    <Chip 
                      label={`${formatCurrency(service.base_price, service.price_currency)}`}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                    <Chip 
                      label={`${service.typical_turnaround_days} days`}
                      size="small"
                      color="secondary"
                      variant="outlined"
                    />
                  </Box>
                </ServiceCardContent>
              </CardActionArea>
            </ServiceCard>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

/**
 * Helper function to get a color for each service type
 */
function getServiceTypeColor(serviceType: ServiceType): string {
  const colors: Record<ServiceType, string> = {
    [ServiceType.BINDING_ASSAY]: '#2196f3',       // Blue
    [ServiceType.ADME]: '#673ab7',               // Deep Purple
    [ServiceType.SOLUBILITY]: '#009688',         // Teal
    [ServiceType.PERMEABILITY]: '#4caf50',       // Green
    [ServiceType.METABOLIC_STABILITY]: '#ff9800', // Orange
    [ServiceType.TOXICITY]: '#f44336',           // Red
    [ServiceType.CUSTOM]: '#9c27b0',             // Purple
  };
  
  return colors[serviceType] || '#9e9e9e'; // Default to gray
}

export default CROSelector;