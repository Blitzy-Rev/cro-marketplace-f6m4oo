import React, { useState, useEffect, useCallback, useMemo } from 'react'; // react ^18.0.0
import { useParams, useNavigate, useLocation } from 'react-router-dom'; // react-router-dom ^6.8.0
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Tabs,
  Tab,
  Divider,
  Menu,
  MenuItem,
  Tooltip
} from '@mui/material'; // @mui/material ^5.0.0
import { Add, FilterList, ViewModule, ViewList, MoreVert, Delete, Edit, AddToPhotos, CloudDownload, Share } from '@mui/icons-material'; // @mui/icons-material ^5.0.0
import { styled } from '@mui/material/styles'; // @mui/material/styles ^5.0.0

// Internal imports
import { useAppDispatch, useAppSelector } from '../../store';
import DashboardLayout from '../../components/layout/DashboardLayout';
import MoleculeTable from '../../components/molecule/MoleculeTable';
import MoleculeGrid from '../../components/molecule/MoleculeGrid';
import MoleculeFilter from '../../components/molecule/MoleculeFilter';
import LibrarySelector from '../../components/library/LibrarySelector';
import ConfirmDialog from '../../components/common/ConfirmDialog';
import SearchField from '../../components/common/SearchField';
import LoadingOverlay from '../../components/common/LoadingOverlay';
import ToastNotification from '../../components/common/ToastNotification';
import { Molecule, MoleculeFilter, MoleculeStatus } from '../../types/molecule.types';
import { Library } from '../../types/library.types';
import { 
  fetchMoleculesByLibrary, 
  setSelectedMolecules, 
  clearSelectedMolecules,
  selectMolecules,
  selectMoleculeLoading,
  selectPagination,
  selectSelectedMolecules
} from '../../features/molecule/moleculeSlice';
import { fetchLibraries, fetchLibrary, selectLibraries, selectLibraryLoading } from '../../features/library/librarySlice';
import routes from '../../constants/routes';
import useToast from '../../hooks/useToast';
import useMoleculeFilterParams from '../../hooks/useMoleculeFilterParams';

// Styled components
const PageContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  height: '100%',
  padding: theme.spacing(2),
}));

const HeaderContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: theme.spacing(2),
}));

const LibrarySelectorContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(2),
  minWidth: 300,
}));

const ActionButtonsContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  gap: theme.spacing(1),
}));

const ContentContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  flex: 1,
  overflow: 'hidden',
}));

const FilterContainer = styled(Paper)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  padding: theme.spacing(2),
}));

const ViewToggleContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  marginLeft: 'auto',
}));

const MoleculeListContainer = styled(Paper)(({ theme }) => ({
  flex: 1,
  overflow: 'auto',
  position: 'relative',
}));

const EmptyStateContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: theme.spacing(4),
  height: '100%',
}));

/**
 * Main component for displaying and managing molecules within a library context
 */
const MoleculeLibraryPage: React.FC = () => {
  // Get library ID from URL parameters
  const { id: libraryId } = useParams<{ id: string }>();

  // Local state for view mode, filter, pagination, and action menus
  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table');
  const [actionMenuAnchor, setActionMenuAnchor] = useState<HTMLElement | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showAddToLibraryDialog, setShowAddToLibraryDialog] = useState(false);
  const [targetLibraryId, setTargetLibraryId] = useState<string | null>(null);

  // Get Redux dispatch function
  const dispatch = useAppDispatch();

  // Select molecules, libraries, loading states, and pagination from Redux store
  const molecules = useAppSelector(selectMolecules);
  const libraries = useAppSelector(selectLibraries);
  const moleculeLoading = useAppSelector(selectMoleculeLoading);
  const libraryLoading = useAppSelector(selectLibraryLoading);
  const pagination = useAppSelector(selectPagination);
  const selectedMolecules = useAppSelector(selectSelectedMolecules);

  // Initialize toast notification hook
  const toast = useToast();

  // Initialize molecule filter params hook
  const {
    filters,
    setSearchTerm,
    setPropertyFilter,
    setStatusFilter,
    setLibraryFilter,
    resetFilters,
    filterQueryString
  } = useMoleculeFilterParams({ library_id: libraryId });

  // React Router hooks
  const navigate = useNavigate();
  const location = useLocation();

  // Fetch libraries on component mount
  useEffect(() => {
    dispatch(fetchLibraries({ pagination: { page: 1, page_size: 50, sort_by: null, sort_order: null } }));
  }, [dispatch]);

  // Fetch molecules for the selected library when libraryId changes
  useEffect(() => {
    if (libraryId) {
      dispatch(fetchMoleculesByLibrary({ libraryId, page: pagination.currentPage, pageSize: pagination.pageSize, filter: filters }));
    }
  }, [dispatch, libraryId, pagination.currentPage, pagination.pageSize, filterQueryString]);

  // Handle library selection change
  const handleLibraryChange = useCallback((libraryId: string) => {
    navigate(routes.generatePath(routes.LIBRARIES.DETAIL, { id: libraryId }));
    dispatch(clearSelectedMolecules());
    resetFilters();
  }, [navigate, dispatch, resetFilters]);

  // Handle view mode toggle between table and grid
  const handleViewModeChange = (event: React.SyntheticEvent, newValue: string) => {
    setViewMode(newValue === 'table' ? 'table' : 'grid');
    localStorage.setItem('moleculeViewMode', newValue);
  };

  // Handle molecule click to navigate to detail page
  const handleMoleculeClick = useCallback((molecule: Molecule) => {
    navigate(routes.getMoleculeDetailPath(molecule.id));
  }, [navigate]);

  // Handle filter changes
  const handleFilterChange = useCallback((filter: MoleculeFilter) => {
    dispatch(fetchMoleculesByLibrary({ libraryId, page: 1, pageSize: pagination.pageSize, filter }));
  }, [dispatch, libraryId, pagination.pageSize]);

  // Handle pagination page changes
  const handlePageChange = useCallback((page: number) => {
    dispatch(fetchMoleculesByLibrary({ libraryId, page, pageSize: pagination.pageSize, filter: filters }));
  }, [dispatch, libraryId, pagination.pageSize, filters]);

  // Handle pagination page size changes
  const handlePageSizeChange = useCallback((pageSize: number) => {
    dispatch(fetchMoleculesByLibrary({ libraryId, page: 1, pageSize, filter: filters }));
  }, [dispatch, libraryId, filters]);

  // Handle molecule selection for batch operations
  const handleSelectionChange = useCallback((selectedIds: string[]) => {
    dispatch(setSelectedMolecules(selectedIds));
  }, [dispatch]);

  // Handle batch deletion of selected molecules
  const handleBatchDelete = useCallback(() => {
    setShowDeleteConfirm(true);
  }, []);

  // Handle adding selected molecules to another library
  const handleBatchAddToLibrary = useCallback(() => {
    setShowAddToLibraryDialog(true);
  }, []);

  // Handle exporting selected molecules to CSV
  const handleExportSelected = useCallback(() => {
    // TODO: Implement CSV export logic
    toast.info('Exporting selected molecules to CSV...');
  }, [toast]);

  return (
    <DashboardLayout title="Molecule Library">
      <PageContainer>
        <HeaderContainer>
          <LibrarySelectorContainer>
            <Typography variant="h6">Library:</Typography>
            <LibrarySelector
              value={libraryId || ''}
              onChange={handleLibraryChange}
              label="Select Library"
              placeholder="Select a library"
              showCreateOption
              fullWidth
            />
          </LibrarySelectorContainer>

          <ActionButtonsContainer>
            <Tooltip title="Add Molecule">
              <Button variant="contained" startIcon={<Add />}>
                Add Molecule
              </Button>
            </Tooltip>
            <Tooltip title="Batch Actions">
              <IconButton onClick={(e) => setActionMenuAnchor(e.currentTarget)} aria-label="batch actions">
                <MoreVert />
              </IconButton>
            </Tooltip>
            <Menu
              anchorEl={actionMenuAnchor}
              open={Boolean(actionMenuAnchor)}
              onClose={() => setActionMenuAnchor(null)}
            >
              <MenuItem onClick={handleBatchDelete} disabled={selectedMolecules.length === 0}>
                <Delete sx={{ mr: 1 }} /> Delete Selected
              </MenuItem>
              <MenuItem onClick={handleBatchAddToLibrary} disabled={selectedMolecules.length === 0}>
                <AddToPhotos sx={{ mr: 1 }} /> Add to Library
              </MenuItem>
              <MenuItem onClick={handleExportSelected} disabled={selectedMolecules.length === 0}>
                <CloudDownload sx={{ mr: 1 }} /> Export Selected
              </MenuItem>
              <MenuItem onClick={() => setActionMenuAnchor(null)}>
                <Share sx={{ mr: 1 }} /> Share Library
              </MenuItem>
            </Menu>
          </ActionButtonsContainer>

          <ViewToggleContainer>
            <Tooltip title="Toggle View">
              <IconButton onClick={handleViewModeChange} aria-label="toggle view">
                {viewMode === 'table' ? <ViewModule /> : <ViewList />}
              </IconButton>
            </Tooltip>
          </ViewToggleContainer>
        </HeaderContainer>

        <ContentContainer>
          <FilterContainer>
            <MoleculeFilter
              initialFilters={filters}
              onFilterChange={handleFilterChange}
              libraryOptions={libraries.map(lib => ({ id: lib.id, name: lib.name }))}
            />
          </FilterContainer>

          <MoleculeListContainer>
            {viewMode === 'table' ? (
              <MoleculeTable
                molecules={molecules}
                loading={moleculeLoading}
                onRowClick={handleMoleculeClick}
                pagination
                totalCount={pagination.total}
                currentPage={pagination.currentPage}
                pageSize={pagination.pageSize}
                onPageChange={handlePageChange}
                onPageSizeChange={handlePageSizeChange}
                selectable
                selected={selectedMolecules}
                onSelectionChange={handleSelectionChange}
              />
            ) : (
              <MoleculeGrid
                molecules={molecules}
                loading={moleculeLoading}
                onMoleculeClick={handleMoleculeClick}
                pagination
                totalCount={pagination.total}
                currentPage={pagination.currentPage}
                pageSize={pagination.pageSize}
                onPageChange={handlePageChange}
                onPageSizeChange={handlePageSizeChange}
                selectable
                selected={selectedMolecules}
                onSelectionChange={handleSelectionChange}
              />
            )}
          </MoleculeListContainer>
        </ContentContainer>
      </PageContainer>

      <ConfirmDialog
        open={showDeleteConfirm}
        title="Delete Selected Molecules?"
        message={`Are you sure you want to delete ${selectedMolecules.length} molecules? This action cannot be undone.`}
        onConfirm={() => {
          // TODO: Implement batch delete logic
          toast.success('Deleting selected molecules...');
          setShowDeleteConfirm(false);
        }}
        onClose={() => setShowDeleteConfirm(false)}
      />

      <ConfirmDialog
        open={showAddToLibraryDialog}
        title="Add to Library"
        message="Select a library to add the selected molecules to:"
        onConfirm={() => {
          // TODO: Implement add to library logic
          toast.success('Adding selected molecules to library...');
          setShowAddToLibraryDialog(false);
        }}
        onClose={() => setShowAddToLibraryDialog(false)}
      />

      <ToastNotification />
    </DashboardLayout>
  );
};

export default MoleculeLibraryPage;