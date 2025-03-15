import React, { useMemo } from 'react';
import { Box, Tooltip, Chip } from '@mui/material'; // ^5.0.0
import { useNavigate } from 'react-router-dom'; // ^6.4.0

import DataTable from '../common/DataTable';
import StatusBadge from '../common/StatusBadge';
import { Result, ResultStatus } from '../../types/result.types';
import { formatDateTime } from '../../utils/dateFormatter';
import { ROUTES } from '../../constants/routes';

/**
 * Props for the ResultsTable component
 */
interface ResultsTableProps {
  /** Array of result data to display */
  results: Result[];
  /** Whether results are currently being loaded */
  loading?: boolean;
  /** Callback when a result is selected */
  onResultSelect?: (result: Result) => void;
  /** Whether to enable row selection */
  selectable?: boolean;
  /** Array of selected result IDs */
  selected?: string[];
  /** Callback when selection changes */
  onSelectionChange?: (selected: string[]) => void;
  /** Whether to enable pagination */
  pagination?: boolean;
  /** Total number of results (for pagination) */
  totalCount?: number;
  /** Current page number (for pagination) */
  currentPage?: number;
  /** Number of items per page (for pagination) */
  pageSize?: number;
  /** Callback when page changes */
  onPageChange?: (page: number) => void;
  /** Callback when page size changes */
  onPageSizeChange?: (pageSize: number) => void;
}

/**
 * Component for displaying experimental results in a tabular format
 */
function ResultsTable({
  results,
  loading = false,
  onResultSelect,
  selectable = false,
  selected = [],
  onSelectionChange,
  pagination = false,
  totalCount,
  currentPage = 1,
  pageSize = 10,
  onPageChange,
  onPageSizeChange,
}: ResultsTableProps): JSX.Element {
  const navigate = useNavigate();

  // Define table columns with memoization to prevent unnecessary re-renders
  const columns = useMemo(() => [
    {
      id: 'id',
      label: 'ID',
      sortable: true,
      width: '120px',
    },
    {
      id: 'status',
      label: 'Status',
      sortable: true,
      width: '150px',
      renderCell: (row: Result) => (
        <StatusBadge 
          status={row.status}
          statusType="custom"
          customColor={getStatusColor(row.status)}
          customLabel={getStatusLabel(row.status)}
        />
      ),
    },
    {
      id: 'submission_id',
      label: 'Submission',
      sortable: true,
      width: '150px',
      renderCell: (row: Result) => (
        <Tooltip title="View submission details">
          <Box
            component="span"
            sx={{
              color: 'primary.main',
              cursor: 'pointer',
              '&:hover': {
                textDecoration: 'underline',
              },
            }}
            onClick={(e) => {
              e.stopPropagation();
              navigate(ROUTES.SUBMISSIONS.DETAIL.replace(':id', row.submission_id));
            }}
          >
            {row.submission_id}
          </Box>
        </Tooltip>
      ),
    },
    {
      id: 'uploaded_at',
      label: 'Upload Date',
      sortable: true,
      width: '180px',
      format: (value: string) => formatDateTime(value),
    },
    {
      id: 'uploaded_by',
      label: 'Uploaded By',
      sortable: true,
    },
    {
      id: 'properties',
      label: 'Properties',
      sortable: false,
      width: '120px',
      renderCell: (row: Result) => (
        <Chip 
          label={row.properties.length} 
          size="small" 
          color="info" 
        />
      ),
    },
  ], [navigate]);

  /**
   * Returns the appropriate color for a result status
   */
  const getStatusColor = (status: ResultStatus): string => {
    const colors: Record<ResultStatus, string> = {
      [ResultStatus.PENDING]: '#ff9800',    // Orange
      [ResultStatus.PROCESSING]: '#2196f3', // Blue
      [ResultStatus.COMPLETED]: '#4caf50',  // Green
      [ResultStatus.FAILED]: '#f44336',     // Red
      [ResultStatus.REJECTED]: '#d32f2f',   // Dark Red
    };
    return colors[status] || '#9e9e9e'; // Default to gray
  };

  /**
   * Returns the display label for a result status
   */
  const getStatusLabel = (status: ResultStatus): string => {
    const labels: Record<ResultStatus, string> = {
      [ResultStatus.PENDING]: 'Pending',
      [ResultStatus.PROCESSING]: 'Processing',
      [ResultStatus.COMPLETED]: 'Completed',
      [ResultStatus.FAILED]: 'Failed',
      [ResultStatus.REJECTED]: 'Rejected',
    };
    return labels[status] || status.toString();
  };

  /**
   * Handles row click events - either calls the provided callback or navigates to result details
   */
  const handleRowClick = (row: Result) => {
    if (onResultSelect) {
      onResultSelect(row);
    } else {
      navigate(ROUTES.RESULTS.DETAIL.replace(':id', row.id));
    }
  };

  return (
    <DataTable
      columns={columns}
      data={results}
      loading={loading}
      selectable={selectable}
      selected={selected}
      onSelectionChange={onSelectionChange}
      onRowClick={handleRowClick}
      pagination={pagination}
      totalCount={totalCount}
      currentPage={currentPage}
      pageSize={pageSize}
      onPageChange={onPageChange}
      onPageSizeChange={onPageSizeChange}
      emptyMessage="No experimental results available"
      getRowId={(row: Result) => row.id}
    />
  );
}

export default ResultsTable;