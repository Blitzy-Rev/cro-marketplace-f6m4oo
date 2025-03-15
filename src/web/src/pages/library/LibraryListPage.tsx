import React, { useState, useEffect, useCallback } from 'react'; // react v18.0.0
import { useNavigate } from 'react-router-dom'; // react-router-dom v6.0.0
import { useDispatch, useSelector } from 'react-redux'; // react-redux v8.0.0
import {
  Box,
  Typography,
  Button,
  Paper,
  Grid,
  FormControlLabel,
  Switch,
  Tabs,
  Tab
} from '@mui/material'; // @mui/material v5.0.0

import DashboardLayout from '../../components/layout/DashboardLayout';
import LibraryList from '../../components/library/LibraryList';
import SearchField from '../../components/common/SearchField';
import {
  fetchLibraries,
  fetchMyLibraries,
  libraryActions,
} from '../../features/library/librarySlice';
import {
  selectLibraries,
  selectLibraryLoading,
  selectPagination,
  selectFilters,
} from '../../features/library/librarySlice';
import { LibraryFilter, Library } from '../../types/library.types';
import { ROUTES } from '../../constants/routes';
import useDebounce from '../../hooks/useDebounce';

/**
 * Page component for displaying and managing molecule libraries
 *
 * @returns The rendered library list page
 */
const LibraryListPage: React.FC = () => {
  // Initialize navigate function using useNavigate for navigation
  const navigate = useNavigate();

  // Initialize dispatch function using useDispatch for Redux actions
  const dispatch = useDispatch();

  // Access libraries, loading state, and pagination from Redux store using useSelector
  const libraries = useSelector(selectLibraries);
  const loading = useSelector(selectLibraryLoading);
  const { currentPage, pageSize, totalCount } = useSelector(selectPagination);
  const filters = useSelector(selectFilters);

  // Initialize state for search term, show my libraries toggle, and active tab
  const [searchTerm, setSearchTerm] = useState('');
  const [showMyLibrariesOnly, setShowMyLibrariesOnly] = useState(false);
  const [activeTab, setActiveTab] = useState(0);

  // Create debounced search term using useDebounce hook
  const debouncedSearchTerm = useDebounce(searchTerm, 500);

  /**
   * Handles navigation to library detail page when a library is selected
   * @param library - The selected library
   */
  const handleLibrarySelect = (library: Library) => {
    // Navigate to library detail page using ROUTES.LIBRARIES.DETAIL with library.id
    navigate(ROUTES.LIBRARIES.DETAIL.replace(':id', library.id));
  };

  /**
   * Handles page change in pagination
   * @param page - The new page number
   */
  const handlePageChange = (page: number) => {
    // Dispatch setCurrentPage action with new page number
    dispatch(libraryActions.setCurrentPage(page));
  };

  /**
   * Handles page size change in pagination
   * @param pageSize - The new page size
   */
  const handlePageSizeChange = (pageSize: number) => {
    // Dispatch setPageSize action with new page size
    dispatch(libraryActions.setPageSize(pageSize));
  };

  /**
   * Handles search term change for filtering libraries
   * @param event - The change event from the search input
   */
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    // Update searchTerm state with event.target.value
    setSearchTerm(event.target.value);
  };

  /**
   * Handles toggle between all libraries and user's libraries
   * @param event - The change event from the toggle input
   */
  const handleMyLibrariesToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
    // Update showMyLibrariesOnly state with event.target.checked
    setShowMyLibrariesOnly(event.target.checked);
    // Update activeTab state based on the toggle state
    setActiveTab(event.target.checked ? 1 : 0);
    // Reset pagination by dispatching setCurrentPage with 1
    dispatch(libraryActions.setCurrentPage(1));
  };

  /**
   * Handles tab change between all libraries and my libraries
   * @param event - The synthetic event from the tab change
   * @param newValue - The index of the selected tab
   */
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    // Update activeTab state with newValue
    setActiveTab(newValue);
    // Update showMyLibrariesOnly state based on the tab index
    setShowMyLibrariesOnly(newValue === 1);
    // Reset pagination by dispatching setCurrentPage with 1
    dispatch(libraryActions.setCurrentPage(1));
  };

  /**
   * Fetches library data based on current filters and pagination
   */
  const fetchLibrariesData = useCallback(() => {
    // Create pagination parameters with currentPage and pageSize
    const paginationParams = {
      page: currentPage,
      page_size: pageSize,
      sort_by: null,
      sort_order: null
    };

    // If showMyLibrariesOnly is true, dispatch fetchMyLibraries with pagination
    if (showMyLibrariesOnly) {
      dispatch(fetchMyLibraries(paginationParams));
    } else {
      // Otherwise, dispatch fetchLibraries with pagination and filters
      dispatch(fetchLibraries({ pagination: paginationParams, filters: filters as LibraryFilter }));
    }
  }, [debouncedSearchTerm, dispatch, filters, currentPage, pageSize, showMyLibrariesOnly]);

  // Fetch libraries when component mounts or when filters/pagination changes
  useEffect(() => {
    // Dispatch setFilters action with updated name filter when debouncedSearchTerm changes
    dispatch(libraryActions.setFilters({ ...filters, name: debouncedSearchTerm }));
  }, [debouncedSearchTerm, dispatch, filters]);

  useEffect(() => {
    // Call fetchLibrariesData function to load library data
    fetchLibrariesData();
  }, [fetchLibrariesData]);

  // Render the page with DashboardLayout and filter controls
  return (
    <DashboardLayout title="Molecule Libraries">
      <Box>
        <Grid container spacing={2} alignItems="center" sx={{ mb: 2 }}>
          <Grid item xs={12} md={6}>
            <Tabs value={activeTab} onChange={handleTabChange} aria-label="library tabs">
              <Tab label="All Libraries" />
              <Tab label="My Libraries" />
            </Tabs>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
              <SearchField
                value={searchTerm}
                onChange={handleSearchChange}
                placeholder="Search libraries..."
                fullWidth={false}
                sx={{ mr: 2 }}
              />
              <FormControlLabel
                control={<Switch checked={showMyLibrariesOnly} onChange={handleMyLibrariesToggle} />}
                label="Show My Libraries Only"
              />
            </Box>
          </Grid>
        </Grid>

        {/* Render LibraryList component with libraries data, loading state, and handlers */}
        <LibraryList
          libraries={libraries}
          loading={loading}
          onLibrarySelect={handleLibrarySelect}
          showMyLibrariesOnly={showMyLibrariesOnly}
          pagination={true}
          currentPage={currentPage}
          pageSize={pageSize}
          totalCount={totalCount}
          onPageChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
        />
      </Box>
    </DashboardLayout>
  );
};

export default LibraryListPage;