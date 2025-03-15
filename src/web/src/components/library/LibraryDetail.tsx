import React, { useState, useEffect, useCallback, useMemo } from 'react'; // react ^18.0.0
import { useDispatch, useSelector } from 'react-redux'; // react-redux ^8.0.0
import { useParams, useNavigate } from 'react-router-dom'; // react-router-dom ^6.0.0
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Tooltip,
  Divider,
  Chip,
  Grid,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material'; // @mui/material ^5.0.0
import {
  EditIcon,
  DeleteIcon,
  ShareIcon,
  AddIcon,
  RemoveIcon,
  SendIcon,
  FilterListIcon
} from '@mui/icons-material'; // @mui/icons-material ^5.0.0

import {
  Library,
  LibraryCategory,
  LibraryWithMolecules,
  Molecule,
} from '../../types/library.types';
import MoleculeTable from '../molecule/MoleculeTable';
import LibraryForm from './LibraryForm';
import ConfirmDialog from '../common/ConfirmDialog';
import LoadingOverlay from '../common/LoadingOverlay';
import MoleculeFilter from '../molecule/MoleculeFilter';
import {
  fetchLibraryWithMolecules,
  editLibrary,
  removeLibrary,
  addMoleculesToLibraryThunk,
  removeMoleculesFromLibraryThunk,
  selectCurrentLibrary,
  selectLibraryLoading
} from '../../features/library/librarySlice';
import {
  moleculeActions,
  selectSelectedMolecules
} from '../../features/molecule/moleculeSlice';
import useToast from '../../hooks/useToast';
import useMoleculeFilterParams from '../../hooks/useMoleculeFilterParams';
import { formatDate } from '../../utils/dateFormatter';

/**
 * Interface for the LibraryDetail component props
 */
interface LibraryDetailProps {
  libraryId?: string;
  onBack?: () => void;
}

/**
 * Interface for the TabPanel component props
 */
interface TabPanelProps {
  children?: React.ReactNode;
  value: number;
  index: number;
}

/**
 * Component for displaying tab content
 */
function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`library-tabpanel-${index}`}
      aria-labelledby={`library-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          <Typography component="div">{children}</Typography>
        </Box>
      )}
    </div>
  );
}

/**
 * Component that displays detailed information about a molecule library and its contents
 */
const LibraryDetail: React.FC<LibraryDetailProps> = (props) => {
  // Extract libraryId from props or URL params
  const libraryId = props.libraryId || useParams<{ libraryId: string }>().libraryId;

  // Initialize state for UI controls
  const [currentTab, setCurrentTab] = useState(0);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [showAddMoleculesDialog, setShowAddMoleculesDialog] = useState(false);
  const [showFilterDialog, setShowFilterDialog] = useState(false);

  // Initialize state for pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Get dispatch function from useDispatch hook
  const dispatch = useDispatch();

  // Get library data, loading state, and selected molecules from Redux store
  const library = useSelector(selectCurrentLibrary);
  const loading = useSelector(selectLibraryLoading);
  const selectedMoleculeIds = useSelector(selectSelectedMolecules);

  // Get toast notification function from useToast hook
  const toast = useToast();

  // Get molecule filter parameters and handlers from useMoleculeFilterParams hook
  const { filterQueryString } = useMoleculeFilterParams();

  // Get navigation function from useNavigate hook
  const navigate = useNavigate();

  // Fetch library data when component mounts or libraryId changes
  useEffect(() => {
    if (libraryId) {
      dispatch(fetchLibraryWithMolecules({
        id: libraryId,
        pagination: {
          page: currentPage,
          page_size: pageSize,
          sort_by: null,
          sort_order: null
        }
      }));
    }
  }, [dispatch, libraryId, currentPage, pageSize, filterQueryString]);

  // Clear selected molecules when component unmounts
  useEffect(() => {
    return () => {
      dispatch(moleculeActions.clearSelectedMolecules());
    };
  }, [dispatch]);

  // Handlers for library actions
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleEditLibrary = () => {
    setShowEditDialog(true);
  };

  const handleEditDialogClose = () => {
    setShowEditDialog(false);
  };

  const handleLibraryUpdated = (updatedLibrary: Library) => {
    setShowEditDialog(false);
    toast.success('Library updated successfully');
    dispatch(fetchLibraryWithMolecules({
      id: libraryId,
      pagination: {
        page: currentPage,
        page_size: pageSize,
        sort_by: null,
        sort_order: null
      }
    }));
  };

  const handleDeleteLibrary = () => {
    setShowDeleteDialog(true);
  };

  const handleDeleteDialogClose = () => {
    setShowDeleteDialog(false);
  };

  const handleConfirmDelete = () => {
    if (library) {
      dispatch(removeLibrary(library.id))
        .then(() => {
          toast.success('Library deleted successfully');
          navigate('/libraries');
        })
        .catch((error) => {
          toast.error(toast.formatError(error));
        })
        .finally(() => {
          setShowDeleteDialog(false);
        });
    }
  };

  const handleShareLibrary = () => {
    setShowShareDialog(true);
  };

  const handleShareDialogClose = () => {
    setShowShareDialog(false);
  };

  // Handlers for molecule actions
  const handleMoleculeSelection = (moleculeIds: string[]) => {
    dispatch(moleculeActions.setSelectedMolecules(moleculeIds));
  };

  const handleMoleculeClick = (molecule: Molecule) => {
    navigate(`/molecules/${molecule.id}`);
  };

  const handleRemoveMolecules = () => {
    if (library && selectedMoleculeIds.length > 0) {
      dispatch(removeMoleculesFromLibraryThunk({
        libraryId: library.id,
        molecules: {
          molecule_ids: selectedMoleculeIds
        }
      }))
        .then(() => {
          toast.success('Molecules removed from library successfully');
          dispatch(moleculeActions.clearSelectedMolecules());
          dispatch(fetchLibraryWithMolecules({
            id: libraryId,
            pagination: {
              page: currentPage,
              page_size: pageSize,
              sort_by: null,
              sort_order: null
            }
          }));
        })
        .catch((error) => {
          toast.error(toast.formatError(error));
        });
    }
  };

  const handleAddMolecules = () => {
    setShowAddMoleculesDialog(true);
  };

  const handleAddMoleculesDialogClose = () => {
    setShowAddMoleculesDialog(false);
  };

  const handleMoleculesAdded = (addedMoleculeIds: string[]) => {
    setShowAddMoleculesDialog(false);
    toast.success('Molecules added to library successfully');
    dispatch(fetchLibraryWithMolecules({
      id: libraryId,
      pagination: {
        page: currentPage,
        page_size: pageSize,
        sort_by: null,
        sort_order: null
      }
    }));
  };

  const handleSubmitToCRO = () => {
    if (library && selectedMoleculeIds.length > 0) {
      navigate(`/cro-submission?molecules=${selectedMoleculeIds.join(',')}`);
    }
  };

  // Handlers for pagination
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setCurrentPage(1);
  };

  // Handlers for filtering
  const handleShowFilters = () => {
    setShowFilterDialog(true);
  };

  const handleFilterDialogClose = () => {
    setShowFilterDialog(false);
  };

  const handleFilterApplied = () => {
    setShowFilterDialog(false);
    setCurrentPage(1);
  };

  return (
    <Box>
      <LoadingOverlay loading={loading}>
        <Paper sx={{ p: 2 }}>
          <Grid container alignItems="center" justifyContent="space-between">
            <Grid item>
              <Typography variant="h5" component="h2">
                {library?.name}
              </Typography>
            </Grid>
            <Grid item>
              <Box display="flex" gap={1}>
                <Tooltip title="Edit Library">
                  <IconButton onClick={handleEditLibrary} aria-label="edit">
                    <EditIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Delete Library">
                  <IconButton onClick={handleDeleteLibrary} aria-label="delete">
                    <DeleteIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Share Library">
                  <IconButton onClick={handleShareLibrary} aria-label="share">
                    <ShareIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Grid>
          </Grid>
          <Typography variant="subtitle1" color="textSecondary">
            {library?.description || 'No description'}
          </Typography>
          <Chip label={library?.category || 'General'} color="primary" size="small" sx={{ mt: 1 }} />
          <Divider sx={{ my: 2 }} />

          <Tabs value={currentTab} onChange={handleTabChange} aria-label="library tabs">
            <Tab label="Molecules" id="library-tab-0" aria-controls="library-tabpanel-0" />
            <Tab label="Details" id="library-tab-1" aria-controls="library-tabpanel-1" />
          </Tabs>

          <TabPanel value={currentTab} index={0}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="subtitle2">
                {library?.molecule_count} Molecules
              </Typography>
              <Box display="flex" gap={1}>
                <Button variant="contained" startIcon={<AddIcon />} onClick={handleAddMolecules}>
                  Add Molecules
                </Button>
                <Button variant="contained" endIcon={<SendIcon />} onClick={handleSubmitToCRO} disabled={selectedMoleculeIds.length === 0}>
                  Submit to CRO
                </Button>
                <Tooltip title="Filter Molecules">
                  <IconButton onClick={handleShowFilters} aria-label="filter">
                    <FilterListIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Remove Selected Molecules">
                  <IconButton onClick={handleRemoveMolecules} aria-label="remove" disabled={selectedMoleculeIds.length === 0}>
                    <RemoveIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
            <MoleculeTable
              molecules={library?.molecules || []}
              loading={loading}
              selectable
              selected={selectedMoleculeIds}
              onSelectionChange={handleMoleculeSelection}
              onRowClick={handleMoleculeClick}
              pagination
              totalCount={library?.molecule_count}
              currentPage={currentPage}
              pageSize={pageSize}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
            />
          </TabPanel>

          <TabPanel value={currentTab} index={1}>
            <Typography variant="body1">
              Created: {formatDate(library?.created_at)}
            </Typography>
            <Typography variant="body1">
              Updated: {formatDate(library?.updated_at)}
            </Typography>
            {/* Add more details here */}
          </TabPanel>
        </Paper>
      </LoadingOverlay>

      {/* Dialogs */}
      <Dialog open={showEditDialog} onClose={handleEditDialogClose} aria-labelledby="edit-library-dialog">
        <DialogTitle id="edit-library-dialog">Edit Library</DialogTitle>
        <DialogContent>
          <LibraryForm
            library={library}
            onSubmitSuccess={handleLibraryUpdated}
            onCancel={handleEditDialogClose}
          />
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={showDeleteDialog}
        onClose={handleDeleteDialogClose}
        onConfirm={handleConfirmDelete}
        title="Delete Library"
        message="Are you sure you want to delete this library? This action cannot be undone."
      />

      <ConfirmDialog
        open={showShareDialog}
        onClose={handleShareDialogClose}
        onConfirm={() => { }} // Implement share functionality
        title="Share Library"
        message="Sharing functionality is not yet implemented."
      />

      <ConfirmDialog
        open={showAddMoleculesDialog}
        onClose={handleAddMoleculesDialogClose}
        onConfirm={() => { }} // Implement add molecules functionality
        title="Add Molecules"
        message="Add molecules functionality is not yet implemented."
      />

      <Dialog open={showFilterDialog} onClose={handleFilterDialogClose} aria-labelledby="filter-dialog">
        <DialogTitle id="filter-dialog">Filter Molecules</DialogTitle>
        <DialogContent>
          <MoleculeFilter
            onFilterChange={() => { }} // Implement filter change functionality
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleFilterDialogClose} color="primary">
            Cancel
          </Button>
          <Button onClick={handleFilterApplied} color="primary">
            Apply Filters
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LibraryDetail;