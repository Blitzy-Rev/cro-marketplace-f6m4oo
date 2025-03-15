import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Grid,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  FilterList,
  Clear,
  CalendarToday
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { DatePicker } from '@mui/x-date-pickers';

// Internal components
import ResultsTable from './ResultsTable';
import Pagination from '../common/Pagination';
import SearchField from '../common/SearchField';
import StatusBadge from '../common/StatusBadge';
import LoadingOverlay from '../common/LoadingOverlay';

// Types
import { Result, ResultStatus, ResultFilter } from '../../types/result.types';

// API
import { getResults } from '../../api/resultApi';

// Hooks
import useDebounce from '../../hooks/useDebounce';

// Styled components
const FilterContainer = styled(Box)({
  marginBottom: '16px',
  padding: '16px',
  backgroundColor: '#f5f5f5',
  borderRadius: '4px',
});

const FilterRow = styled(Grid)({
  marginBottom: '8px',
});

const FilterChip = styled(Chip)({
  margin: '4px',
});

// Props interface
interface ResultsListProps {
  submissionId?: string;
  onResultSelect?: (result: Result) => void;
  selectable?: boolean;
  selected?: string[];
  onSelectionChange?: (selected: string[]) => void;
  pagination?: boolean;
  initialPage?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
}

/**
 * Component for displaying a list of experimental results with filtering and pagination
 */
const ResultsList = ({
  submissionId,
  onResultSelect,
  selectable = false,
  selected = [],
  onSelectionChange,
  pagination = true,
  initialPage = 1,
  pageSize = 10,
  onPageChange,
  onPageSizeChange,
}: ResultsListProps): JSX.Element => {
  // State for results data
  const [results, setResults] = useState<Result[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(initialPage);
  
  // State for filters
  const [filters, setFilters] = useState<ResultFilter>({
    submission_id: submissionId || null,
    status: null,
    uploaded_after: null,
    uploaded_before: null,
    molecule_id: null,
  });
  
  // State for search term
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useDebounce(searchTerm, 500);
  
  // Fetch results when filters, pagination, or submissionId changes
  useEffect(() => {
    fetchResults();
  }, [debouncedSearchTerm, filters, currentPage, pageSize, submissionId]);
  
  // Update filters if submissionId prop changes
  useEffect(() => {
    if (submissionId !== filters.submission_id) {
      setFilters(prev => ({
        ...prev,
        submission_id: submissionId || null
      }));
    }
  }, [submissionId]);
  
  // Function to fetch results from API
  const fetchResults = async () => {
    setLoading(true);
    try {
      // Prepare filter with search term
      const filterWithSearch = {
        ...filters,
        // Add search logic here if the API supports it
      };
      
      const response = await getResults(filterWithSearch, currentPage, pageSize);
      setResults(response.items);
      setTotalCount(response.total);
    } catch (error) {
      console.error('Error fetching results:', error);
      setResults([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  };
  
  // Handle filter changes
  const handleFilterChange = (name: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
    // Reset to first page when filters change
    setCurrentPage(1);
  };
  
  // Handle search changes
  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
    // Reset to first page when search changes
    setCurrentPage(1);
  };
  
  // Handle status filter changes
  const handleStatusFilterChange = (event: any) => {
    const value = event.target.value as ResultStatus | '';
    handleFilterChange('status', value === '' ? null : value);
  };
  
  // Handle clear filters
  const handleClearFilters = () => {
    setFilters({
      submission_id: submissionId || null,
      status: null,
      uploaded_after: null,
      uploaded_before: null,
      molecule_id: null,
    });
    setSearchTerm('');
    setCurrentPage(1);
  };
  
  // Handle date filter changes
  const handleDateFilterChange = (fieldName: 'uploaded_after' | 'uploaded_before', date: Date | null) => {
    handleFilterChange(fieldName, date ? date.toISOString() : null);
  };
  
  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    if (onPageChange) {
      onPageChange(page);
    }
  };
  
  // Handle page size change
  const handlePageSizeChange = (size: number) => {
    if (onPageSizeChange) {
      onPageSizeChange(size);
    }
  };
  
  // Active filters count
  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (filters.status) count++;
    if (filters.uploaded_after) count++;
    if (filters.uploaded_before) count++;
    if (debouncedSearchTerm) count++;
    return count;
  }, [filters, debouncedSearchTerm]);
  
  return (
    <Box sx={{ position: 'relative' }}>
      <Paper sx={{ mb: 2, p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Experimental Results</Typography>
          <Box>
            <Tooltip title="Filter results">
              <IconButton 
                size="small" 
                aria-label="filter results">
                <FilterList />
              </IconButton>
            </Tooltip>
            {activeFiltersCount > 0 && (
              <Tooltip title="Clear all filters">
                <IconButton 
                  size="small" 
                  aria-label="clear filters"
                  onClick={handleClearFilters}>
                  <Clear />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>
        
        <Divider sx={{ mb: 2 }} />
        
        <FilterContainer>
          <FilterRow container spacing={2}>
            <Grid item xs={12} md={4}>
              <SearchField
                value={searchTerm}
                onChange={handleSearchChange}
                placeholder="Search results..."
                fullWidth
              />
            </Grid>
            
            <Grid item xs={12} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel id="status-filter-label">Status</InputLabel>
                <Select
                  labelId="status-filter-label"
                  id="status-filter"
                  value={filters.status || ''}
                  onChange={handleStatusFilterChange}
                  label="Status"
                >
                  <MenuItem value="">All Statuses</MenuItem>
                  <MenuItem value={ResultStatus.PENDING}>Pending</MenuItem>
                  <MenuItem value={ResultStatus.PROCESSING}>Processing</MenuItem>
                  <MenuItem value={ResultStatus.COMPLETED}>Completed</MenuItem>
                  <MenuItem value={ResultStatus.FAILED}>Failed</MenuItem>
                  <MenuItem value={ResultStatus.REJECTED}>Rejected</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <DatePicker
                  label="From Date"
                  value={filters.uploaded_after ? new Date(filters.uploaded_after) : null}
                  onChange={(newDate) => handleDateFilterChange('uploaded_after', newDate)}
                  slotProps={{ textField: { size: 'small', fullWidth: true } }}
                />
                <DatePicker
                  label="To Date"
                  value={filters.uploaded_before ? new Date(filters.uploaded_before) : null}
                  onChange={(newDate) => handleDateFilterChange('uploaded_before', newDate)}
                  slotProps={{ textField: { size: 'small', fullWidth: true } }}
                />
              </Box>
            </Grid>
          </FilterRow>
          
          {/* Active filters */}
          {activeFiltersCount > 0 && (
            <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap' }}>
              <Typography variant="body2" sx={{ mr: 1, mt: 0.5 }}>
                Active filters:
              </Typography>
              
              {debouncedSearchTerm && (
                <FilterChip
                  label={`Search: ${debouncedSearchTerm}`}
                  onDelete={() => setSearchTerm('')}
                  size="small"
                />
              )}
              
              {filters.status && (
                <FilterChip
                  label={`Status: ${filters.status}`}
                  onDelete={() => handleFilterChange('status', null)}
                  size="small"
                  avatar={<StatusBadge status={filters.status} statusType="custom" size="small" />}
                />
              )}
              
              {filters.uploaded_after && (
                <FilterChip
                  label={`From: ${new Date(filters.uploaded_after).toLocaleDateString()}`}
                  onDelete={() => handleFilterChange('uploaded_after', null)}
                  size="small"
                  icon={<CalendarToday fontSize="small" />}
                />
              )}
              
              {filters.uploaded_before && (
                <FilterChip
                  label={`To: ${new Date(filters.uploaded_before).toLocaleDateString()}`}
                  onDelete={() => handleFilterChange('uploaded_before', null)}
                  size="small"
                  icon={<CalendarToday fontSize="small" />}
                />
              )}
            </Box>
          )}
        </FilterContainer>
        
        <ResultsTable
          results={results}
          loading={loading}
          onResultSelect={onResultSelect}
          selectable={selectable}
          selected={selected}
          onSelectionChange={onSelectionChange}
          pagination={false} // We handle pagination separately
          totalCount={totalCount}
          currentPage={currentPage}
          pageSize={pageSize}
        />
        
        {pagination && (
          <Pagination
            page={currentPage}
            pageSize={pageSize}
            totalCount={totalCount}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
          />
        )}
      </Paper>
      
      {loading && <LoadingOverlay loading={loading} />}
    </Box>
  );
};

export default ResultsList;