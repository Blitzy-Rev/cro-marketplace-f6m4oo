import React, { useState, useEffect, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Tooltip,
  Chip,
  Dialog
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';

import { Library, LibraryCategory } from '../../types/library.types';
import DataTable from '../common/DataTable';
import LibraryForm from './LibraryForm';
import ConfirmDialog from '../common/ConfirmDialog';
import LoadingOverlay from '../common/LoadingOverlay';
import {
  fetchLibraries,
  fetchMyLibraries,
  addLibrary,
  editLibrary,
  removeLibrary
} from '../../features/library/librarySlice';
import useToast from '../../hooks/useToast';
import { formatDate } from '../../utils/dateFormatter';

// Define props interface
interface LibraryListProps {
  showMyLibrariesOnly?: boolean;
  onLibrarySelect?: (library: Library) => void;
  selectable?: boolean;
  loading?: boolean;
  libraries?: Library[];
  pagination?: boolean;
  currentPage?: number;
  pageSize?: number;
  totalCount?: number;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
}

interface RootState {
  library: {
    libraries: Library[];
    loading: boolean;
  }
}

const LibraryList: React.FC<LibraryListProps> = ({
  showMyLibrariesOnly = false,
  onLibrarySelect,
  selectable = false,
  loading: propLoading,
  libraries: propLibraries,
  pagination = false,
  currentPage = 1,
  pageSize = 10,
  totalCount = 0,
  onPageChange,
  onPageSizeChange
}) => {
  // State for tracking selections and dialogs
  const [selectedLibraries, setSelectedLibraries] = useState<string[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [currentLibrary, setCurrentLibrary] = useState<Library | null>(null);

  // Redux hooks
  const dispatch = useDispatch<any>();
  
  // Get libraries from Redux store if not provided via props
  const storeLibraries = useSelector((state: RootState) => state.library.libraries);
  const storeLoading = useSelector((state: RootState) => state.library.loading);
  
  // Use libraries from props if provided, otherwise use from Redux store
  const libraries = propLibraries || storeLibraries;
  const loading = propLoading !== undefined ? propLoading : storeLoading;

  // Get toast notification function
  const toast = useToast();

  // Define the columns for the data table
  const columns = [
    {
      id: 'name',
      label: 'Library Name',
      sortable: true,
      width: '30%'
    },
    {
      id: 'description',
      label: 'Description',
      sortable: false,
      width: '35%',
      format: (value: string | null) => value || 'No description'
    },
    {
      id: 'category',
      label: 'Category',
      sortable: true,
      width: '15%',
      renderCell: (row: Library) => (
        row.category ? (
          <Chip 
            label={row.category.replace(/_/g, ' ')} 
            size="small" 
            color="primary" 
            variant="outlined"
          />
        ) : (
          <span>-</span>
        )
      )
    },
    {
      id: 'molecule_count',
      label: 'Molecules',
      sortable: true,
      width: '10%',
      align: 'right'
    },
    {
      id: 'created_at',
      label: 'Created',
      sortable: true,
      width: '15%',
      format: (value: string) => formatDate(value)
    },
    {
      id: 'actions',
      label: 'Actions',
      sortable: false,
      width: '10%',
      renderCell: (row: Library) => (
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Tooltip title="View Library">
            <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleViewLibrary(row); }}>
              <VisibilityIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Edit Library">
            <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleEditLibrary(row); }}>
              <EditIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete Library">
            <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleDeleteLibrary(row); }}>
              <DeleteIcon fontSize="small" color="error" />
            </IconButton>
          </Tooltip>
        </Box>
      )
    }
  ];

  // Handler functions for library actions
  const handleCreateLibrary = () => {
    setShowCreateDialog(true);
    setCurrentLibrary(null);
  };

  const handleEditLibrary = (library: Library) => {
    setCurrentLibrary(library);
    setShowEditDialog(true);
  };

  const handleDeleteLibrary = (library: Library) => {
    setCurrentLibrary(library);
    setShowDeleteDialog(true);
  };

  const handleViewLibrary = (library: Library) => {
    if (onLibrarySelect) {
      onLibrarySelect(library);
    }
  };

  // Handlers for dialog actions
  const handleCreateDialogClose = () => {
    setShowCreateDialog(false);
  };

  const handleEditDialogClose = () => {
    setShowEditDialog(false);
    setCurrentLibrary(null);
  };

  const handleDeleteDialogClose = () => {
    setShowDeleteDialog(false);
    setCurrentLibrary(null);
  };

  const handleLibraryCreated = (library: Library) => {
    setShowCreateDialog(false);
    toast.success(`Library "${library.name}" created successfully`);
    
    // Refresh libraries
    fetchLibrariesData();
  };

  const handleLibraryUpdated = (library: Library) => {
    setShowEditDialog(false);
    setCurrentLibrary(null);
    toast.success(`Library "${library.name}" updated successfully`);
    
    // Refresh libraries
    fetchLibrariesData();
  };

  const handleConfirmDelete = () => {
    if (currentLibrary) {
      dispatch(removeLibrary(currentLibrary.id))
        .unwrap()
        .then(() => {
          toast.success(`Library "${currentLibrary.name}" deleted successfully`);
          
          // Refresh libraries
          fetchLibrariesData();
        })
        .catch((error) => {
          toast.error(toast.formatError(error));
        });
    }
    
    setShowDeleteDialog(false);
    setCurrentLibrary(null);
  };

  // Handler for library selection
  const handleLibrarySelection = (libraryIds: string[]) => {
    setSelectedLibraries(libraryIds);
  };

  // Handler for row click
  const handleRowClick = (library: Library) => {
    if (onLibrarySelect) {
      onLibrarySelect(library);
    }
  };

  // Fetch libraries on component mount if not provided via props
  const fetchLibrariesData = useCallback(() => {
    if (!propLibraries) {
      const paginationParams = {
        page: currentPage,
        page_size: pageSize,
        sort_by: null,
        sort_order: null
      };

      if (showMyLibrariesOnly) {
        dispatch(fetchMyLibraries(paginationParams));
      } else {
        dispatch(fetchLibraries({ pagination: paginationParams }));
      }
    }
  }, [dispatch, showMyLibrariesOnly, currentPage, pageSize, propLibraries]);

  useEffect(() => {
    fetchLibrariesData();
  }, [fetchLibrariesData]);

  // Render the component
  return (
    <Box>
      <Paper sx={{ position: 'relative', mb: 2 }}>
        <LoadingOverlay loading={loading}>
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" component="h2">
              {showMyLibrariesOnly ? 'My Libraries' : 'All Libraries'}
            </Typography>
            <Button
              variant="contained"
              color="primary"
              startIcon={<AddIcon />}
              onClick={handleCreateLibrary}
            >
              Add Library
            </Button>
          </Box>
          
          <DataTable
            columns={columns}
            data={libraries || []}
            selectable={selectable}
            selected={selectedLibraries}
            onSelectionChange={handleLibrarySelection}
            onRowClick={selectable ? undefined : handleRowClick}
            pagination={pagination}
            currentPage={currentPage}
            pageSize={pageSize}
            totalCount={totalCount}
            onPageChange={onPageChange}
            onPageSizeChange={onPageSizeChange}
            emptyMessage="No libraries found. Create a new library to get started."
            getRowId={(row: Library) => row.id}
          />
        </LoadingOverlay>
      </Paper>

      {/* Create Library Dialog */}
      <Dialog
        open={showCreateDialog}
        onClose={handleCreateDialogClose}
        maxWidth="md"
        fullWidth
        aria-labelledby="create-library-dialog-title"
      >
        <Typography variant="h6" sx={{ px: 3, py: 2 }} id="create-library-dialog-title">
          Create New Library
        </Typography>
        <LibraryForm
          onSubmitSuccess={handleLibraryCreated}
          onCancel={handleCreateDialogClose}
        />
      </Dialog>

      {/* Edit Library Dialog */}
      <Dialog
        open={showEditDialog}
        onClose={handleEditDialogClose}
        maxWidth="md"
        fullWidth
        aria-labelledby="edit-library-dialog-title"
      >
        <Typography variant="h6" sx={{ px: 3, py: 2 }} id="edit-library-dialog-title">
          Edit Library
        </Typography>
        {currentLibrary && (
          <LibraryForm
            library={currentLibrary}
            onSubmitSuccess={handleLibraryUpdated}
            onCancel={handleEditDialogClose}
          />
        )}
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={showDeleteDialog}
        title="Delete Library"
        message={
          currentLibrary ? (
            <>
              <Typography variant="body1" paragraph>
                Are you sure you want to delete the library <strong>{currentLibrary.name}</strong>?
              </Typography>
              <Typography variant="body2" color="text.secondary">
                This action cannot be undone, and all library organization will be lost.
                The molecules themselves will not be deleted.
              </Typography>
            </>
          ) : (
            <Typography variant="body1">
              Are you sure you want to delete this library? This action cannot be undone.
            </Typography>
          )
        }
        confirmButtonText="Delete"
        confirmButtonColor="error"
        onConfirm={handleConfirmDelete}
        onClose={handleDeleteDialogClose}
        showWarningIcon
      />
    </Box>
  );
};

export default LibraryList;