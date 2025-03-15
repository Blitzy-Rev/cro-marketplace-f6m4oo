import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  Box, 
  Paper, 
  Typography, 
  Chip, 
  Button, 
  Grid, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  TextField, 
  IconButton, 
  Divider, 
  Tabs, 
  Tab 
} from '@mui/material';
import { FilterList, Clear, Search } from '@mui/icons-material';

// Internal components
import DataTable, { Column } from '../common/DataTable';
import StatusBadge from '../common/StatusBadge';
import Pagination from '../common/Pagination';
import SearchField from '../common/SearchField';
import LoadingOverlay from '../common/LoadingOverlay';

// Types
import { Submission, SubmissionFilter, SubmissionStatus } from '../../types/submission.types';

// Constants and utils
import { getStatusColor, getStatusDisplayName, ACTIVE_STATUSES, TERMINAL_STATUSES } from '../../constants/submissionStatus';
import { 
  fetchSubmissions, 
  setSubmissionFilter, 
  setCurrentPage, 
  setPageSize, 
  selectSubmissions, 
  selectSubmissionLoading, 
  selectPagination, 
  selectFilters, 
  selectStatusCounts 
} from '../../features/submission/submissionSlice';
import { formatDate } from '../../utils/dateFormatter';
import useDebounce from '../../hooks/useDebounce';
import useAuth from '../../hooks/useAuth';

/**
 * Props for the SubmissionList component
 */
interface SubmissionListProps {
  /**
   * Callback function when a submission is clicked
   */
  onSubmissionClick: (submission: Submission) => void;
  
  /**
   * Optional CSS class name for additional styling
   */
  className?: string;
}

/**
 * Column definition for the submission table
 */
interface SubmissionTableColumn extends Column<Submission> {
  id: string;
  label: string;
  width?: string | number;
  align?: 'left' | 'right' | 'center';
  sortable?: boolean;
  format?: (value: any, row: Submission) => React.ReactNode;
}

/**
 * A component that displays a list of CRO submissions with filtering, sorting, and pagination capabilities
 */
const SubmissionList: React.FC<SubmissionListProps> = ({ onSubmissionClick, className }) => {
  const dispatch = useDispatch();
  const { user } = useAuth();
  
  // Redux state
  const submissions = useSelector(selectSubmissions);
  const loading = useSelector(selectSubmissionLoading);
  const { totalCount, currentPage, pageSize, totalPages } = useSelector(selectPagination);
  const filters = useSelector(selectFilters);
  const statusCounts = useSelector(selectStatusCounts);
  
  // Local state
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [filterPanelOpen, setFilterPanelOpen] = useState<boolean>(false);
  const [activeStatusFilter, setActiveStatusFilter] = useState<'active' | 'completed' | 'all'>('active');
  
  // Debounced search term to prevent excessive API calls
  const debouncedSearchTerm = useDebounce(searchTerm, 500);
  
  // Table columns definition
  const columns: SubmissionTableColumn[] = useMemo(() => [
    { 
      id: 'id', 
      label: 'ID', 
      width: '100px',
      format: (value: string) => value.substring(0, 8)
    },
    { 
      id: 'name', 
      label: 'Submission Name', 
      width: '25%'
    },
    { 
      id: 'status', 
      label: 'Status', 
      width: '150px',
      format: (_, submission) => renderStatusCell(submission)
    },
    { 
      id: 'cro_service', 
      label: 'CRO Service', 
      width: '20%',
      format: (_, submission) => renderCROServiceCell(submission)
    },
    { 
      id: 'molecule_count', 
      label: 'Molecules', 
      width: '100px',
      align: 'center',
      format: (_, submission) => renderMoleculeCountCell(submission)
    },
    { 
      id: 'created_at', 
      label: 'Created', 
      width: '150px',
      format: (value) => renderDateCell(value)
    },
    { 
      id: 'updated_at', 
      label: 'Updated', 
      width: '150px',
      format: (value) => renderDateCell(value)
    }
  ], []);
  
  // Fetch submissions on mount and when filters change
  useEffect(() => {
    dispatch(fetchSubmissions({ 
      page: currentPage, 
      size: pageSize, 
      filter: filters 
    }) as any);
  }, [dispatch, currentPage, pageSize, filters]);

  // Update search term filter when debounced value changes
  useEffect(() => {
    if (debouncedSearchTerm !== filters.name_contains) {
      dispatch(setSubmissionFilter({ name_contains: debouncedSearchTerm || null }));
      // Reset to first page when search changes
      dispatch(setCurrentPage(1));
    }
  }, [debouncedSearchTerm, dispatch, filters.name_contains]);

  // Handle search term changes
  const handleSearchChange = useCallback((term: string) => {
    setSearchTerm(term);
  }, []);

  // Toggle filter panel visibility
  const toggleFilterPanel = useCallback(() => {
    setFilterPanelOpen(prev => !prev);
  }, []);

  // Handle filter changes
  const handleFilterChange = useCallback((newFilters: Partial<SubmissionFilter>) => {
    dispatch(setSubmissionFilter(newFilters));
    dispatch(setCurrentPage(1)); // Reset to first page when filters change
  }, [dispatch]);

  // Handle status filter tab changes
  const handleStatusFilterChange = useCallback((filter: 'active' | 'completed' | 'all') => {
    setActiveStatusFilter(filter);
    
    let statusFilter: SubmissionStatus[] | null = null;
    
    if (filter === 'active') {
      statusFilter = ACTIVE_STATUSES;
    } else if (filter === 'completed') {
      statusFilter = TERMINAL_STATUSES;
    }
    
    dispatch(setSubmissionFilter({ status: statusFilter }));
    dispatch(setCurrentPage(1)); // Reset to first page when status filter changes
  }, [dispatch]);

  // Handle specific status chip click
  const handleStatusChipClick = useCallback((status: SubmissionStatus | null) => {
    dispatch(setSubmissionFilter({ 
      status: status ? [status] : null 
    }));
    dispatch(setCurrentPage(1)); // Reset to first page
  }, [dispatch]);

  // Handle page change
  const handlePageChange = useCallback((page: number) => {
    dispatch(setCurrentPage(page));
  }, [dispatch]);

  // Handle page size change
  const handlePageSizeChange = useCallback((size: number) => {
    dispatch(setPageSize(size));
    dispatch(setCurrentPage(1)); // Reset to first page when page size changes
  }, [dispatch]);

  // Handle row click
  const handleRowClick = useCallback((submission: Submission) => {
    onSubmissionClick(submission);
  }, [onSubmissionClick]);

  return (
    <Paper className={className} sx={{ p: 2 }}>
      <LoadingOverlay loading={loading}>
        {/* Header with title and filter toggle */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" component="h1">Submissions</Typography>
          <Box>
            <IconButton 
              onClick={toggleFilterPanel} 
              color={filterPanelOpen ? "primary" : "default"}
              aria-label="Toggle filter panel"
            >
              <FilterList />
            </IconButton>
          </Box>
        </Box>

        {/* Filter panel */}
        {filterPanelOpen && (
          <FilterPanel 
            filters={filters}
            onFilterChange={handleFilterChange}
            statusCounts={statusCounts}
            activeStatusFilter={activeStatusFilter}
            onStatusFilterChange={handleStatusFilterChange}
            searchTerm={searchTerm}
            onSearchChange={handleSearchChange}
          />
        )}

        {/* Status count chips for quick filtering */}
        <Box mb={2} mt={filterPanelOpen ? 2 : 0}>
          <StatusCountChips 
            statusCounts={statusCounts} 
            activeStatus={filters.status?.[0] || null}
            onStatusClick={handleStatusChipClick}
          />
        </Box>

        {/* Submissions data table */}
        <DataTable 
          columns={columns}
          data={submissions}
          loading={loading}
          onRowClick={handleRowClick}
          pagination
          totalCount={totalCount}
          currentPage={currentPage}
          pageSize={pageSize}
          onPageChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
          emptyMessage="No submissions found. Try adjusting your filters."
        />
      </LoadingOverlay>
    </Paper>
  );
};

/**
 * Renders a status badge for a submission
 */
const renderStatusCell = (submission: Submission): JSX.Element => {
  return (
    <StatusBadge 
      status={submission.status} 
      statusType="submission"
    />
  );
};

/**
 * Renders a formatted date cell
 */
const renderDateCell = (dateString: string): string => {
  return dateString ? formatDate(dateString) : '-';
};

/**
 * Renders the CRO service information
 */
const renderCROServiceCell = (submission: Submission): JSX.Element | string => {
  if (!submission.cro_service) {
    return '-';
  }
  
  return (
    <Box>
      <Typography variant="body2" component="span">
        {submission.cro_service.name}
      </Typography>
      {submission.cro_service.service_type && (
        <Typography variant="caption" display="block" color="text.secondary">
          {submission.cro_service.service_type}
        </Typography>
      )}
    </Box>
  );
};

/**
 * Renders the molecule count for a submission
 */
const renderMoleculeCountCell = (submission: Submission): number | string => {
  if (submission.molecule_count !== null && submission.molecule_count !== undefined) {
    return submission.molecule_count;
  }
  
  if (submission.molecules && Array.isArray(submission.molecules)) {
    return submission.molecules.length;
  }
  
  return '-';
};

/**
 * Component for displaying and managing submission filters
 */
const FilterPanel: React.FC<{
  filters: SubmissionFilter;
  onFilterChange: (filters: Partial<SubmissionFilter>) => void;
  statusCounts: Array<{ status: SubmissionStatus; count: number }>;
  activeStatusFilter: 'active' | 'completed' | 'all';
  onStatusFilterChange: (filter: 'active' | 'completed' | 'all') => void;
  searchTerm: string;
  onSearchChange: (term: string) => void;
}> = ({ 
  filters, 
  onFilterChange, 
  statusCounts, 
  activeStatusFilter, 
  onStatusFilterChange,
  searchTerm,
  onSearchChange
}) => {
  return (
    <Box mb={2} p={2} bgcolor="background.default" borderRadius={1}>
      <Grid container spacing={2}>
        {/* Search field */}
        <Grid item xs={12} md={4}>
          <SearchField 
            value={searchTerm}
            onChange={onSearchChange}
            placeholder="Search submissions..."
            fullWidth
          />
        </Grid>
        
        {/* Status filter tabs */}
        <Grid item xs={12} md={8}>
          <Tabs 
            value={activeStatusFilter}
            onChange={(_, value) => onStatusFilterChange(value)}
            indicatorColor="primary"
            textColor="primary"
            aria-label="Status filter tabs"
          >
            <Tab label="Active" value="active" />
            <Tab label="Completed" value="completed" />
            <Tab label="All" value="all" />
          </Tabs>
        </Grid>
        
        {/* CRO service filter */}
        <Grid item xs={12} md={4}>
          <FormControl fullWidth size="small">
            <InputLabel id="cro-service-filter-label">CRO Service</InputLabel>
            <Select
              labelId="cro-service-filter-label"
              id="cro-service-filter"
              value={filters.cro_service_id || ''}
              label="CRO Service"
              onChange={(e) => onFilterChange({ cro_service_id: e.target.value || null })}
              displayEmpty
            >
              <MenuItem value="">All Services</MenuItem>
              {/* CRO service options would be populated here from another selector */}
              <MenuItem value="1">Binding Assay</MenuItem>
              <MenuItem value="2">ADME Panel</MenuItem>
              <MenuItem value="3">Solubility Testing</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12}>
          <Box display="flex" justifyContent="flex-end">
            <Button 
              startIcon={<Clear />}
              onClick={() => onFilterChange({
                name_contains: null,
                cro_service_id: null,
                molecule_id: null,
                created_after: null,
                created_before: null
              })}
              size="small"
            >
              Clear Filters
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

/**
 * Component for displaying status count chips for quick filtering
 */
const StatusCountChips: React.FC<{
  statusCounts: Array<{ status: SubmissionStatus; count: number }>;
  activeStatus: SubmissionStatus | null;
  onStatusClick: (status: SubmissionStatus | null) => void;
}> = ({ statusCounts, activeStatus, onStatusClick }) => {
  return (
    <Box display="flex" flexWrap="wrap" gap={1}>
      <Chip 
        label={`All (${statusCounts.reduce((sum, item) => sum + item.count, 0)})`}
        onClick={() => onStatusClick(null)}
        color={activeStatus === null ? "primary" : "default"}
        variant={activeStatus === null ? "filled" : "outlined"}
      />
      
      {statusCounts
        .filter(item => item.count > 0)
        .sort((a, b) => b.count - a.count) // Sort by count descending
        .map(item => (
          <Chip 
            key={item.status}
            label={`${getStatusDisplayName(item.status)} (${item.count})`}
            onClick={() => onStatusClick(item.status)}
            color={activeStatus === item.status ? "primary" : "default"}
            variant={activeStatus === item.status ? "filled" : "outlined"}
            sx={{ 
              '& .MuiChip-label': { 
                color: activeStatus === item.status ? 'inherit' : getStatusColor(item.status)
              }
            }}
          />
        ))
      }
    </Box>
  );
};

export default SubmissionList;