import React from 'react';
import { 
  Box, 
  Button, 
  IconButton, 
  MenuItem, 
  Select, 
  Typography, 
  FormControl, 
  InputLabel 
} from '@mui/material'; // ^5.0.0
import { styled } from '@mui/material/styles'; // ^5.0.0
import { 
  FirstPage, 
  LastPage, 
  NavigateBefore, 
  NavigateNext 
} from '@mui/icons-material'; // ^5.0.0

/**
 * Props for the Pagination component
 */
interface PaginationProps {
  /** Current page number */
  page: number;
  /** Number of items per page */
  pageSize: number;
  /** Total number of items */
  totalCount: number;
  /** Callback when page changes */
  onPageChange: (page: number) => void;
  /** Callback when page size changes */
  onPageSizeChange: (pageSize: number) => void;
  /** Available page size options */
  pageSizeOptions?: number[];
  /** Whether to show first/last page buttons */
  showFirstLastButtons?: boolean;
  /** Whether to show page size selector */
  showPageSizeSelector?: boolean;
  /** Additional CSS class name */
  className?: string;
}

// Styled components for the pagination elements
const PaginationContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: theme.spacing(1, 2),
  borderTop: '1px solid rgba(0, 0, 0, 0.12)',
  [theme.breakpoints.down('sm')]: {
    flexDirection: 'column',
    gap: theme.spacing(1)
  }
}));

const PageNavigation = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  [theme.breakpoints.down('sm')]: {
    width: '100%',
    justifyContent: 'center'
  }
}));

interface PageButtonProps {
  current?: boolean;
}

const PageButton = styled(Button, {
  shouldForwardProp: (prop) => prop !== 'current'
})<PageButtonProps>(({ theme, current }) => ({
  minWidth: '36px',
  height: '36px',
  padding: '0',
  margin: '0 4px',
  backgroundColor: current ? theme.palette.primary.main : 'transparent',
  color: current ? theme.palette.primary.contrastText : 'inherit',
  '&:hover': {
    backgroundColor: current ? theme.palette.primary.dark : 'rgba(0, 0, 0, 0.04)'
  },
  '&.Mui-disabled': {
    color: theme.palette.text.disabled
  }
}));

const PageSizeSelector = styled(FormControl)(({ theme }) => ({
  minWidth: '120px',
  marginLeft: theme.spacing(2),
  [theme.breakpoints.down('sm')]: {
    marginLeft: 0,
    marginTop: theme.spacing(1)
  }
}));

const PaginationSummary = styled(Typography)(({ theme }) => ({
  marginLeft: theme.spacing(2),
  color: theme.palette.text.secondary,
  fontSize: '0.875rem',
  [theme.breakpoints.down('sm')]: {
    marginLeft: 0,
    marginTop: theme.spacing(1)
  }
}));

/**
 * Generates an array of page numbers to display in the pagination component
 * 
 * @param currentPage - The current page number
 * @param totalPages - The total number of pages
 * @returns Array of page numbers and ellipsis indicators
 */
const generatePageNumbers = (currentPage: number, totalPages: number): Array<number | string> => {
  const pageNumbers: Array<number | string> = [];
  
  // Always show the first page
  pageNumbers.push(1);
  
  // We'll use '...' as an ellipsis indicator
  if (currentPage > 3) {
    pageNumbers.push('...');
  }
  
  // Add pages around current page (current ± 1)
  const startPage = Math.max(2, currentPage - 1);
  const endPage = Math.min(totalPages - 1, currentPage + 1);
  
  for (let i = startPage; i <= endPage; i++) {
    // Avoid duplicating the first page
    if (i !== 1) {
      pageNumbers.push(i);
    }
  }
  
  // Add ellipsis before last page if needed
  if (currentPage < totalPages - 2) {
    pageNumbers.push('...');
  }
  
  // Add the last page if different from the first
  if (totalPages > 1) {
    pageNumbers.push(totalPages);
  }
  
  return pageNumbers;
};

/**
 * A component that renders pagination controls for navigating through paginated data
 * 
 * @param props - The component props
 * @returns The rendered pagination component
 */
const Pagination: React.FC<PaginationProps> = ({
  page,
  pageSize,
  totalCount,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 25, 50, 100],
  showFirstLastButtons = true,
  showPageSizeSelector = true,
  className
}) => {
  // Calculate total pages
  const totalPages = Math.ceil(totalCount / pageSize);
  
  // Generate page numbers to display
  const pageNumbers = generatePageNumbers(page, totalPages);
  
  // Calculate range of visible items
  const startItem = totalCount === 0 ? 0 : (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, totalCount);
  
  return (
    <PaginationContainer className={className}>
      <PageNavigation>
        {/* First page button */}
        {showFirstLastButtons && (
          <IconButton 
            onClick={() => onPageChange(1)} 
            disabled={page === 1}
            aria-label="First page"
            size="small"
          >
            <FirstPage />
          </IconButton>
        )}
        
        {/* Previous page button */}
        <IconButton 
          onClick={() => onPageChange(page - 1)} 
          disabled={page === 1}
          aria-label="Previous page"
          size="small"
        >
          <NavigateBefore />
        </IconButton>
        
        {/* Page number buttons */}
        {pageNumbers.map((pageNum, index) => (
          pageNum === '...' ? (
            <Typography 
              key={`ellipsis-${index}`} 
              variant="body2" 
              sx={{ mx: 1 }}
            >
              ...
            </Typography>
          ) : (
            <PageButton 
              key={`page-${pageNum}`}
              current={page === pageNum}
              onClick={() => onPageChange(pageNum as number)}
              aria-label={`Page ${pageNum}`}
              aria-current={page === pageNum ? 'page' : undefined}
              variant={page === pageNum ? 'contained' : 'text'}
              disableElevation
            >
              {pageNum}
            </PageButton>
          )
        ))}
        
        {/* Next page button */}
        <IconButton 
          onClick={() => onPageChange(page + 1)} 
          disabled={page === totalPages}
          aria-label="Next page"
          size="small"
        >
          <NavigateNext />
        </IconButton>
        
        {/* Last page button */}
        {showFirstLastButtons && (
          <IconButton 
            onClick={() => onPageChange(totalPages)} 
            disabled={page === totalPages}
            aria-label="Last page"
            size="small"
          >
            <LastPage />
          </IconButton>
        )}
      </PageNavigation>
      
      {/* Right side controls: page size selector and summary */}
      <Box 
        sx={{ 
          display: 'flex', 
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 2
        }}
      >
        {/* Page size selector */}
        {showPageSizeSelector && (
          <PageSizeSelector size="small">
            <InputLabel id="page-size-selector-label">Items per page</InputLabel>
            <Select
              labelId="page-size-selector-label"
              id="page-size-selector"
              value={pageSize}
              label="Items per page"
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              size="small"
            >
              {pageSizeOptions.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          </PageSizeSelector>
        )}
        
        {/* Pagination summary */}
        <PaginationSummary variant="body2">
          Showing {totalCount > 0 ? `${startItem}-${endItem} of ${totalCount}` : '0'} items
        </PaginationSummary>
      </Box>
    </PaginationContainer>
  );
};

export default Pagination;