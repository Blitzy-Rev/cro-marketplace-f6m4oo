import React, { useState, useEffect, useCallback } from 'react'; // react ^18.0.0
import {
  Box,
  Typography,
  Button,
  Grid,
  Paper,
} from '@mui/material'; // @mui/material ^5.0.0
import {
  Add,
  FilterList,
} from '@mui/icons-material'; // @mui/icons-material ^5.0.0
import {
  useNavigate,
  useLocation,
  useSearchParams,
} from 'react-router-dom'; // react-router-dom ^6.0.0

// Internal components
import DashboardLayout from '../../components/layout/DashboardLayout';
import ResultsList from '../../components/results/ResultsList';

// Constants
import { ROUTES, getResultDetailPath } from '../../constants/routes';

// Types
import { Result, ResultFilter } from '../../types/result.types';

/**
 * Page component for displaying a list of experimental results
 */
const ResultsListPage: React.FC = () => {
  // Initialize state for results pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Initialize state for selected results
  const [selectedResults, setSelectedResults] = useState<string[]>([]);

  // Initialize state for loading status
  const [loading, setLoading] = useState(false);

  // Initialize state for filter criteria
  const [filters, setFilters] = useState<ResultFilter>({
    status: null,
    uploaded_after: null,
    uploaded_before: null,
    submission_id: null,
    molecule_id: null,
  });

  // Get navigation function from useNavigate hook
  const navigate = useNavigate();

  // Get location and search params from React Router hooks
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();

  // Implement useEffect to parse URL search parameters for initial filter state
  useEffect(() => {
    const statusParam = searchParams.get('status');
    const uploadedAfterParam = searchParams.get('uploaded_after');
    const uploadedBeforeParam = searchParams.get('uploaded_before');
    const submissionIdParam = searchParams.get('submission_id');
    const moleculeIdParam = searchParams.get('molecule_id');

    setFilters({
      status: statusParam || null,
      uploaded_after: uploadedAfterParam || null,
      uploaded_before: uploadedBeforeParam || null,
      submission_id: submissionIdParam || null,
      molecule_id: moleculeIdParam || null,
    });

    const pageParam = searchParams.get('page');
    if (pageParam) {
      setCurrentPage(parseInt(pageParam, 10));
    }

    const pageSizeParam = searchParams.get('pageSize');
    if (pageSizeParam) {
      setPageSize(parseInt(pageSizeParam, 10));
    }
  }, [searchParams]);

  // Implement useEffect to update URL when filter changes
  useEffect(() => {
    const params = new URLSearchParams();
    if (filters.status) {
      params.set('status', filters.status);
    }
    if (filters.uploaded_after) {
      params.set('uploaded_after', filters.uploaded_after);
    }
    if (filters.uploaded_before) {
      params.set('uploaded_before', filters.uploaded_before);
    }
    if (filters.submission_id) {
      params.set('submission_id', filters.submission_id);
    }
    if (filters.molecule_id) {
      params.set('molecule_id', filters.molecule_id);
    }
    params.set('page', currentPage.toString());
    params.set('pageSize', pageSize.toString());

    setSearchParams(params);
  }, [filters, currentPage, pageSize, setSearchParams]);

  // Implement handlePageChange function to update pagination state
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // Implement handlePageSizeChange function to update page size
  const handlePageSizeChange = (size: number) => {
    setPageSize(size);
    setCurrentPage(1); // Reset to page 1 when page size changes
  };

  // Implement handleResultSelect function to navigate to result detail page
  const handleResultSelect = useCallback((result: Result) => {
    navigate(getResultDetailPath(result.id));
  }, [navigate]);

  // Implement handleFilterChange function to update filter criteria
  const handleFilterChange = (newFilters: ResultFilter) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to page 1 when filters change
  };

  // Implement handleUploadClick function to navigate to results upload page
  const handleUploadClick = useCallback(() => {
    navigate(ROUTES.RESULTS.UPLOAD);
  }, [navigate]);

  const handleSelectionChange = useCallback((selected: string[]) => {
    setSelectedResults(selected);
  }, []);

  // Styled container for the page header
  const HeaderContainer = styled(Box)({
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  });

  // Styled button for page actions
  const ActionButton = styled(Button)({
    marginLeft: '8px',
  });

  return (
    <DashboardLayout title="Experimental Results" loading={loading}>
      <HeaderContainer>
        <Typography variant="h4">
          Experimental Results
        </Typography>
        <Box>
          <ActionButton
            variant="contained"
            color="primary"
            startIcon={<Add />}
            onClick={handleUploadClick}
          >
            Upload Results
          </ActionButton>
          <ActionButton
            variant="outlined"
            color="primary"
            startIcon={<FilterList />}
          >
            Filter
          </ActionButton>
        </Box>
      </HeaderContainer>
      <ResultsList
        results={[]}
        loading={loading}
        onResultSelect={handleResultSelect}
        selectable
        selected={selectedResults}
        onSelectionChange={handleSelectionChange}
        pagination
        initialPage={currentPage}
        pageSize={pageSize}
        onPageChange={handlePageChange}
        onPageSizeChange={handlePageSizeChange}
      />
    </DashboardLayout>
  );
};

export default ResultsListPage;