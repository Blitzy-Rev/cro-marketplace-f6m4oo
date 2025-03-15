import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TableSortLabel,
  Paper, Checkbox, CircularProgress, Typography, Box
} from '@mui/material'; // ^5.0.0
import { styled } from '@mui/material/styles'; // ^5.0.0
import Pagination from './Pagination';
import usePagination from '../../hooks/usePagination';
import { PaginationParams, SortOrder } from '../../types/api.types';

/**
 * Interface defining properties for a table column
 */
interface Column<T> {
  /** Unique identifier for the column, used for sorting and data access */
  id: string;
  /** Display label for the column header */
  label: string;
  /** Whether the column is sortable */
  sortable?: boolean;
  /** Text alignment for the column */
  align?: 'left' | 'right' | 'center';
  /** Width of the column */
  width?: string | number;
  /** Function to format the cell value */
  format?: (value: any, row: T) => React.ReactNode;
  /** Custom cell renderer function */
  renderCell?: (row: T) => React.ReactNode;
}

/**
 * Props for the DataTable component
 */
interface DataTableProps<T> {
  /** Array of column definitions */
  columns: Column<T>[];
  /** Array of data rows */
  data: T[];
  /** Whether the table is in loading state */
  loading?: boolean;
  /** Whether rows can be selected with checkboxes */
  selectable?: boolean;
  /** Array of selected row IDs */
  selected?: string[] | number[];
  /** Callback when selection changes */
  onSelectionChange?: (selected: string[] | number[]) => void;
  /** Callback when a row is clicked */
  onRowClick?: (row: T) => void;
  /** Whether to enable pagination */
  pagination?: boolean;
  /** Total number of items (for pagination) */
  totalCount?: number;
  /** Current page number (for pagination) */
  currentPage?: number;
  /** Number of items per page (for pagination) */
  pageSize?: number;
  /** Callback when page changes */
  onPageChange?: (page: number) => void;
  /** Callback when page size changes */
  onPageSizeChange?: (pageSize: number) => void;
  /** Initial column to sort by */
  initialSortBy?: string;
  /** Initial sort direction */
  initialSortDirection?: 'asc' | 'desc';
  /** Message to display when data is empty */
  emptyMessage?: string;
  /** Additional CSS class name */
  className?: string;
  /** Function to get unique row identifier */
  getRowId?: (row: T) => string | number;
}

/**
 * Styled components for the DataTable
 */
const StyledTableContainer = styled(TableContainer)<{ maxHeight?: string | number }>(({ maxHeight }) => ({
  maxHeight: maxHeight || 'none',
  overflow: 'auto'
}));

const StyledTableCell = styled(TableCell)<{ align?: 'left' | 'right' | 'center', width?: string | number }>(({ align, width }) => ({
  textAlign: align || 'left',
  width: width || 'auto'
}));

const StyledTableRow = styled(TableRow)<{ selected?: boolean; clickable?: boolean }>(({ selected, clickable }) => ({
  cursor: clickable ? 'pointer' : 'default',
  backgroundColor: selected ? 'rgba(25, 118, 210, 0.08)' : 'inherit',
  '&:hover': {
    backgroundColor: 'rgba(0, 0, 0, 0.04)'
  }
}));

const LoadingOverlay = styled(Box)({
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  position: 'absolute',
  top: '0',
  left: '0',
  right: '0',
  bottom: '0',
  backgroundColor: 'rgba(255, 255, 255, 0.7)',
  zIndex: 1
});

const EmptyMessage = styled(Typography)(({ theme }) => ({
  padding: theme.spacing(2),
  textAlign: 'center',
  color: theme.palette.text.secondary
}));

/**
 * Creates a comparator function for sorting table data
 * 
 * @param sortBy - The property name to sort by
 * @param sortDirection - The sort direction (asc or desc)
 * @returns Comparator function for sorting
 */
function getComparator<T>(
  sortBy: string,
  sortDirection: SortOrder
): (a: T, b: T) => number {
  return (a, b) => {
    // Access the property using the sortBy key
    const aValue = sortBy.split('.').reduce((obj, key) => 
      obj && obj[key] !== undefined ? obj[key] : null, a as any);
    const bValue = sortBy.split('.').reduce((obj, key) => 
      obj && obj[key] !== undefined ? obj[key] : null, b as any);
    
    // Handle null/undefined values
    if ((aValue === null || aValue === undefined) && (bValue === null || bValue === undefined)) return 0;
    if (aValue === null || aValue === undefined) return sortDirection === SortOrder.ASC ? -1 : 1;
    if (bValue === null || bValue === undefined) return sortDirection === SortOrder.ASC ? 1 : -1;
    
    // String comparison
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return aValue.localeCompare(bValue) * (sortDirection === SortOrder.ASC ? 1 : -1);
    }
    
    // Number or other comparison
    return (aValue < bValue ? -1 : aValue > bValue ? 1 : 0) * 
           (sortDirection === SortOrder.ASC ? 1 : -1);
  };
}

/**
 * Sorts an array while maintaining the original order of equal elements
 * 
 * @param array - The array to sort
 * @param comparator - The comparator function
 * @returns Sorted array
 */
function stableSort<T>(array: readonly T[], comparator: (a: T, b: T) => number): T[] {
  const stabilizedThis = array.map((el, index) => [el, index] as [T, number]);
  stabilizedThis.sort((a, b) => {
    const order = comparator(a[0], b[0]);
    if (order !== 0) return order;
    return a[1] - b[1]; // Preserve original order for equal elements
  });
  return stabilizedThis.map((el) => el[0]);
}

/**
 * A reusable table component with sorting, filtering, pagination, and selection capabilities
 * 
 * @param props - Component props
 * @returns The rendered table component
 */
function DataTable<T extends object>(props: DataTableProps<T>): JSX.Element {
  const {
    columns,
    data,
    loading = false,
    selectable = false,
    selected = [],
    onSelectionChange,
    onRowClick,
    pagination = false,
    totalCount,
    currentPage = 1,
    pageSize = 10,
    onPageChange,
    onPageSizeChange,
    initialSortBy,
    initialSortDirection = 'asc',
    emptyMessage = 'No data available',
    className,
    getRowId = (row: any) => row.id
  } = props;

  // State for sorting
  const [sortBy, setSortBy] = useState<string>(initialSortBy || (columns.length > 0 ? columns[0].id : ''));
  const [sortDirection, setSortDirection] = useState<SortOrder>(
    initialSortDirection === 'desc' ? SortOrder.DESC : SortOrder.ASC
  );

  // Handle sort request
  const handleRequestSort = useCallback((columnId: string) => {
    const isAsc = sortBy === columnId && sortDirection === SortOrder.ASC;
    setSortDirection(isAsc ? SortOrder.DESC : SortOrder.ASC);
    setSortBy(columnId);
  }, [sortBy, sortDirection]);

  // Sort data when sort parameters change
  const sortedData = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    // Find the column to sort by
    const sortableColumn = columns.find(col => col.id === sortBy);
    if (!sortableColumn || sortableColumn.sortable === false) return [...data];
    
    return stableSort(data, getComparator(sortBy, sortDirection));
  }, [data, columns, sortBy, sortDirection]);

  // Paginate data if pagination is enabled
  const displayData = useMemo(() => {
    if (!pagination) return sortedData;
    
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    return sortedData.slice(start, Math.min(end, sortedData.length));
  }, [sortedData, pagination, currentPage, pageSize]);

  // Selection handling
  const handleSelectAllClick = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!onSelectionChange) return;
    
    if (event.target.checked) {
      const newSelected = data.map(row => getRowId(row));
      onSelectionChange(newSelected);
    } else {
      onSelectionChange([]);
    }
  };

  const handleRowSelect = (event: React.MouseEvent, id: string | number) => {
    event.stopPropagation(); // Prevent row click event
    if (!onSelectionChange) return;
    
    const selectedIndex = selected.indexOf(id);
    let newSelected: (string | number)[] = [];
    
    if (selectedIndex === -1) {
      // Add to selection
      newSelected = [...selected, id];
    } else {
      // Remove from selection
      newSelected = selected.filter(item => item !== id);
    }
    
    onSelectionChange(newSelected);
  };

  const isSelected = (id: string | number) => selected.indexOf(id) !== -1;

  // Handle row click
  const handleRowClick = (row: T) => {
    if (onRowClick) {
      onRowClick(row);
    }
  };

  return (
    <Paper className={className} sx={{ position: 'relative', width: '100%' }}>
      {loading && (
        <LoadingOverlay>
          <CircularProgress />
        </LoadingOverlay>
      )}
      
      <StyledTableContainer>
        <Table stickyHeader aria-label="data table">
          <TableHead>
            <TableRow>
              {selectable && (
                <TableCell padding="checkbox">
                  <Checkbox
                    indeterminate={selected.length > 0 && selected.length < data.length}
                    checked={data.length > 0 && selected.length === data.length}
                    onChange={handleSelectAllClick}
                    inputProps={{ 'aria-label': 'select all' }}
                  />
                </TableCell>
              )}
              
              {columns.map((column) => (
                <StyledTableCell
                  key={column.id}
                  align={column.align}
                  width={column.width}
                >
                  {column.sortable !== false ? (
                    <TableSortLabel
                      active={sortBy === column.id}
                      direction={sortBy === column.id 
                        ? (sortDirection === SortOrder.ASC ? 'asc' : 'desc') 
                        : 'asc'}
                      onClick={() => handleRequestSort(column.id)}
                    >
                      {column.label}
                      <span className="visually-hidden">
                        {sortDirection === SortOrder.ASC ? 'sorted ascending' : 'sorted descending'}
                      </span>
                    </TableSortLabel>
                  ) : (
                    column.label
                  )}
                </StyledTableCell>
              ))}
            </TableRow>
          </TableHead>
          
          <TableBody>
            {displayData.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={selectable ? columns.length + 1 : columns.length}
                >
                  <EmptyMessage>{emptyMessage}</EmptyMessage>
                </TableCell>
              </TableRow>
            ) : (
              displayData.map((row, index) => {
                const id = getRowId(row);
                const isItemSelected = isSelected(id);
                
                return (
                  <StyledTableRow
                    hover
                    onClick={() => handleRowClick(row)}
                    role={selectable ? "checkbox" : undefined}
                    aria-checked={selectable ? isItemSelected : undefined}
                    tabIndex={-1}
                    key={`row-${id}`}
                    selected={isItemSelected}
                    clickable={!!onRowClick}
                  >
                    {selectable && (
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={isItemSelected}
                          onClick={(e) => handleRowSelect(e, id)}
                          inputProps={{ 'aria-labelledby': `row-${id}` }}
                        />
                      </TableCell>
                    )}
                    
                    {columns.map((column) => {
                      const value = column.id.split('.').reduce(
                        (obj, key) => obj && obj[key] !== undefined ? obj[key] : null, 
                        row as any
                      );
                      
                      return (
                        <TableCell 
                          key={`cell-${id}-${column.id}`} 
                          align={column.align}
                        >
                          {column.renderCell 
                            ? column.renderCell(row) 
                            : column.format 
                              ? column.format(value, row) 
                              : value !== null && value !== undefined 
                                ? value 
                                : ''}
                        </TableCell>
                      );
                    })}
                  </StyledTableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </StyledTableContainer>
      
      {pagination && totalCount !== undefined && (
        <Pagination
          page={currentPage}
          pageSize={pageSize}
          totalCount={totalCount}
          onPageChange={onPageChange || (() => {})}
          onPageSizeChange={onPageSizeChange || (() => {})}
        />
      )}
    </Paper>
  );
}

export default DataTable;