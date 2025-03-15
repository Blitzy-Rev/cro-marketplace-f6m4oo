import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Tooltip,
  SelectChangeEvent
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';

import { Library, LibraryFilter } from '../../types/library.types';
import { 
  fetchLibraries, 
  fetchMyLibraries, 
  selectLibraries, 
  selectLibraryLoading 
} from '../../features/library/librarySlice';
import SearchField from '../common/SearchField';
import LibraryForm from './LibraryForm';
import useDebounce from '../../hooks/useDebounce';

/**
 * Props interface for the LibrarySelector component
 */
interface LibrarySelectorProps {
  /** Currently selected library ID */
  value: string;
  /** Callback function when library selection changes */
  onChange: (libraryId: string) => void;
  /** Label for the select component */
  label?: string;
  /** Placeholder text when no library is selected */
  placeholder?: string;
  /** Flag to show only the current user's libraries */
  showMyLibrariesOnly?: boolean;
  /** Flag to show option to create a new library */
  showCreateOption?: boolean;
  /** Flag to disable the selector */
  disabled?: boolean;
  /** Flag to make the selector take full width */
  fullWidth?: boolean;
  /** Size of the selector component */
  size?: 'small' | 'medium';
  /** Flag to mark the selector as required */
  required?: boolean;
  /** Flag to show error state */
  error?: boolean;
  /** Helper text to display below the selector */
  helperText?: string;
  /** Custom render function for library options */
  renderOption?: (library: Library) => React.ReactNode;
}

/**
 * A dropdown component that allows users to select a molecule library from a list of available libraries.
 * Provides search functionality, displays library metadata, and supports custom rendering of library items.
 */
const LibrarySelector: React.FC<LibrarySelectorProps> = ({
  value,
  onChange,
  label = 'Select Library',
  placeholder = 'Select a library',
  showMyLibrariesOnly = false,
  showCreateOption = true,
  disabled = false,
  fullWidth = false,
  size = 'medium',
  required = false,
  error = false,
  helperText,
  renderOption,
}) => {
  // Local state
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [open, setOpen] = useState(false);
  
  // Redux hooks
  const dispatch = useDispatch();
  const libraries = useSelector(selectLibraries);
  const loading = useSelector(selectLibraryLoading);
  
  // Debounce search term to prevent excessive API calls
  const debouncedSearchTerm = useDebounce(searchTerm, 300);
  
  /**
   * Handles search input changes
   */
  const handleSearch = (value: string) => {
    setSearchTerm(value);
  };
  
  /**
   * Handles library selection changes
   */
  const handleChange = (event: SelectChangeEvent) => {
    const selectedValue = event.target.value;
    
    if (selectedValue === 'create-new') {
      setShowCreateDialog(true);
    } else {
      onChange(selectedValue);
    }
  };
  
  /**
   * Opens the create library dialog
   */
  const handleCreateDialogOpen = () => {
    setShowCreateDialog(true);
  };
  
  /**
   * Closes the create library dialog
   */
  const handleCreateDialogClose = () => {
    setShowCreateDialog(false);
  };
  
  /**
   * Handles successful library creation
   */
  const handleLibraryCreated = (library: Library) => {
    handleCreateDialogClose();
    onChange(library.id);
    fetchLibrariesData(); // Refresh library list
  };
  
  /**
   * Fetches library data based on filters
   */
  const fetchLibrariesData = () => {
    const filter: LibraryFilter = {
      name: debouncedSearchTerm || null,
      category: null,
      owner_id: null,
      is_public: null,
      contains_molecule_id: null
    };
    
    const pagination = {
      page: 1,
      page_size: 50,
      sort_by: null,
      sort_order: null
    };
    
    if (showMyLibrariesOnly) {
      dispatch(fetchMyLibraries(pagination));
    } else {
      dispatch(fetchLibraries({ pagination, filters: filter }));
    }
  };
  
  /**
   * Renders a library option in the dropdown
   */
  const renderLibraryOption = (library: Library) => {
    if (renderOption) {
      return renderOption(library);
    }
    
    return (
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
        <Typography variant="body1">{library.name}</Typography>
        <Typography variant="body2" color="text.secondary">
          {library.molecule_count} molecules
        </Typography>
        {library.description && (
          <Tooltip title={library.description}>
            <Box component="span" sx={{ ml: 1, cursor: 'help' }}>ℹ️</Box>
          </Tooltip>
        )}
      </Box>
    );
  };
  
  // Initial data fetching on component mount
  useEffect(() => {
    fetchLibrariesData();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  
  // Refetch data when search term or filter changes
  useEffect(() => {
    fetchLibrariesData();
  }, [debouncedSearchTerm, showMyLibrariesOnly]); // eslint-disable-line react-hooks/exhaustive-deps
  
  return (
    <Box>
      <FormControl fullWidth={fullWidth} disabled={disabled} error={error} required={required} size={size}>
        <InputLabel id="library-select-label">{label}</InputLabel>
        <Select
          labelId="library-select-label"
          id="library-select"
          value={value}
          onChange={handleChange}
          label={label}
          displayEmpty
          renderValue={(selected) => {
            if (!selected) {
              return <Typography color="text.secondary">{placeholder}</Typography>;
            }
            const library = libraries.find(lib => lib.id === selected);
            return library ? library.name : placeholder;
          }}
          MenuProps={{
            PaperProps: {
              sx: {
                maxHeight: 300
              }
            }
          }}
        >
          {/* Search field at the top of dropdown */}
          <Box sx={{ p: 1, position: "sticky", top: 0, bgcolor: "background.paper", zIndex: 1 }}>
            <SearchField 
              value={searchTerm}
              onChange={handleSearch}
              placeholder="Search libraries..."
              fullWidth
              size="small"
            />
          </Box>
          
          {/* Loading indicator */}
          {loading && (
            <Box sx={{ p: 2, display: "flex", justifyContent: "center" }}>
              <CircularProgress size={24} />
            </Box>
          )}
          
          {/* No libraries found */}
          {!loading && libraries.length === 0 && (
            <MenuItem disabled>
              <Typography variant="body2" color="text.secondary">
                No libraries found
              </Typography>
            </MenuItem>
          )}
          
          {/* Libraries */}
          {libraries.map((library) => (
            <MenuItem key={library.id} value={library.id}>
              {renderLibraryOption(library)}
            </MenuItem>
          ))}
          
          {/* Create new library option */}
          {showCreateOption && (
            <MenuItem value="create-new">
              <Box sx={{ display: "flex", alignItems: "center" }}>
                <AddIcon color="primary" sx={{ mr: 1 }} />
                <Typography color="primary">Create New Library</Typography>
              </Box>
            </MenuItem>
          )}
        </Select>
        {helperText && (
          <Typography variant="caption" color={error ? "error" : "text.secondary"}>
            {helperText}
          </Typography>
        )}
      </FormControl>
      
      {/* Create library dialog */}
      <Dialog open={showCreateDialog} onClose={handleCreateDialogClose} maxWidth="md" fullWidth>
        <DialogTitle>Create New Library</DialogTitle>
        <DialogContent>
          <LibraryForm
            onSubmitSuccess={handleLibraryCreated}
            onCancel={handleCreateDialogClose}
          />
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default LibrarySelector;