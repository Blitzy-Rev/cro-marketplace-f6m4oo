import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'; // ^1.9.5
import { 
  Library, 
  LibraryState, 
  LibraryCreate, 
  LibraryUpdate, 
  LibraryFilter, 
  LibraryWithMolecules,
  MoleculeAddRemove,
  LibraryShareCreate,
  LibraryShareUpdate,
  LibraryResponse
} from '../../types/library.types';
import { PaginationParams } from '../../types/api.types';
import { 
  getLibraries, 
  getMyLibraries, 
  getLibrary, 
  getLibraryWithMolecules, 
  createLibrary, 
  updateLibrary, 
  deleteLibrary, 
  filterLibraries,
  addMoleculesToLibrary,
  removeMoleculesFromLibrary,
  shareLibrary,
  updateLibraryShare,
  removeLibraryShare
} from '../../api/libraryApi';

// Define async thunks for library-related API operations

/**
 * Fetch libraries with pagination and optional filtering
 */
export const fetchLibraries = createAsyncThunk(
  'libraries/fetchLibraries',
  async (params: { pagination: PaginationParams; filters?: LibraryFilter }) => {
    const { pagination, filters } = params;
    const response = await getLibraries(pagination, filters);
    return response;
  }
);

/**
 * Fetch libraries owned by the current user
 */
export const fetchMyLibraries = createAsyncThunk(
  'libraries/fetchMyLibraries',
  async (pagination: PaginationParams) => {
    const response = await getMyLibraries(pagination);
    return response;
  }
);

/**
 * Fetch a single library by ID
 */
export const fetchLibrary = createAsyncThunk(
  'libraries/fetchLibrary',
  async (id: string) => {
    const response = await getLibrary(id);
    return response;
  }
);

/**
 * Fetch a library with its molecules
 */
export const fetchLibraryWithMolecules = createAsyncThunk(
  'libraries/fetchLibraryWithMolecules',
  async (params: { id: string; pagination: PaginationParams }) => {
    const { id, pagination } = params;
    const response = await getLibraryWithMolecules(id, pagination);
    return response;
  }
);

/**
 * Create a new library
 */
export const addLibrary = createAsyncThunk(
  'libraries/addLibrary',
  async (library: LibraryCreate) => {
    const response = await createLibrary(library);
    return response;
  }
);

/**
 * Update an existing library
 */
export const editLibrary = createAsyncThunk(
  'libraries/editLibrary',
  async (params: { id: string; library: LibraryUpdate }) => {
    const { id, library } = params;
    const response = await updateLibrary(id, library);
    return response;
  }
);

/**
 * Delete a library
 */
export const removeLibrary = createAsyncThunk(
  'libraries/removeLibrary',
  async (id: string) => {
    await deleteLibrary(id);
    return id;
  }
);

/**
 * Filter libraries by criteria
 */
export const filterLibrariesThunk = createAsyncThunk(
  'libraries/filterLibraries',
  async (params: { filters: LibraryFilter; pagination: PaginationParams }) => {
    const { filters, pagination } = params;
    const response = await filterLibraries(filters, pagination);
    return response;
  }
);

/**
 * Add molecules to a library
 */
export const addMoleculesToLibraryThunk = createAsyncThunk(
  'libraries/addMolecules',
  async (params: { libraryId: string; molecules: MoleculeAddRemove }) => {
    const { libraryId, molecules } = params;
    const response = await addMoleculesToLibrary(libraryId, molecules);
    return response;
  }
);

/**
 * Remove molecules from a library
 */
export const removeMoleculesFromLibraryThunk = createAsyncThunk(
  'libraries/removeMolecules',
  async (params: { libraryId: string; molecules: MoleculeAddRemove }) => {
    const { libraryId, molecules } = params;
    const response = await removeMoleculesFromLibrary(libraryId, molecules);
    return response;
  }
);

/**
 * Share a library with another user
 */
export const shareLibraryThunk = createAsyncThunk(
  'libraries/shareLibrary',
  async (params: { libraryId: string; shareData: LibraryShareCreate }) => {
    const { libraryId, shareData } = params;
    const response = await shareLibrary(libraryId, shareData);
    return response;
  }
);

/**
 * Update library sharing permissions
 */
export const updateLibraryShareThunk = createAsyncThunk(
  'libraries/updateShare',
  async (params: { libraryId: string; userId: string; shareData: LibraryShareUpdate }) => {
    const { libraryId, userId, shareData } = params;
    const response = await updateLibraryShare(libraryId, userId, shareData);
    return response;
  }
);

/**
 * Remove library sharing permissions
 */
export const removeLibraryShareThunk = createAsyncThunk(
  'libraries/removeShare',
  async (params: { libraryId: string; userId: string }) => {
    const { libraryId, userId } = params;
    await removeLibraryShare(libraryId, userId);
    return { libraryId, userId };
  }
);

// Initial state for the library slice
const initialState: LibraryState = {
  libraries: [],
  currentLibrary: null,
  loading: false,
  error: null,
  totalCount: 0,
  currentPage: 1,
  pageSize: 25,
  totalPages: 0
};

// Create the library slice
export const librarySlice = createSlice({
  name: 'libraries',
  initialState,
  reducers: {
    /**
     * Set the current page for pagination
     */
    setCurrentPage: (state, action: PayloadAction<number>) => {
      state.currentPage = action.payload;
    },
    /**
     * Set the page size for pagination
     */
    setPageSize: (state, action: PayloadAction<number>) => {
      state.pageSize = action.payload;
      // Recalculate total pages when page size changes
      if (state.totalCount > 0) {
        state.totalPages = Math.ceil(state.totalCount / action.payload);
      }
    },
    /**
     * Set filter criteria for libraries
     */
    setFilters: (state, action: PayloadAction<LibraryFilter>) => {
      // Filters are not stored in state directly, but this action can be
      // used in middleware or components to trigger filtering
    },
    /**
     * Clear all filter criteria
     */
    clearFilters: (state) => {
      // Filters are not stored in state directly, but this action can be
      // used in middleware or components to clear filters
    },
    /**
     * Reset library state to initial values
     */
    resetLibraryState: (state) => {
      return initialState;
    }
  },
  extraReducers: (builder) => {
    // Handle fetchLibraries
    builder
      .addCase(fetchLibraries.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchLibraries.fulfilled, (state, action) => {
        state.loading = false;
        state.libraries = action.payload.items;
        state.totalCount = action.payload.total;
        state.currentPage = action.payload.page;
        state.pageSize = action.payload.limit;
        state.totalPages = Math.ceil(action.payload.total / action.payload.limit);
      })
      .addCase(fetchLibraries.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch libraries';
      });

    // Handle fetchMyLibraries
    builder
      .addCase(fetchMyLibraries.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMyLibraries.fulfilled, (state, action) => {
        state.loading = false;
        state.libraries = action.payload.items;
        state.totalCount = action.payload.total;
        state.currentPage = action.payload.page;
        state.pageSize = action.payload.limit;
        state.totalPages = Math.ceil(action.payload.total / action.payload.limit);
      })
      .addCase(fetchMyLibraries.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch your libraries';
      });

    // Handle fetchLibrary
    builder
      .addCase(fetchLibrary.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchLibrary.fulfilled, (state, action) => {
        state.loading = false;
        // Update the library in the libraries array if it exists
        const index = state.libraries.findIndex(lib => lib.id === action.payload.id);
        if (index !== -1) {
          state.libraries[index] = action.payload;
        }
        // Don't set as current library as it doesn't include molecules
      })
      .addCase(fetchLibrary.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch library';
      });

    // Handle fetchLibraryWithMolecules
    builder
      .addCase(fetchLibraryWithMolecules.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchLibraryWithMolecules.fulfilled, (state, action) => {
        state.loading = false;
        state.currentLibrary = action.payload;
        
        // Update the library in the libraries array if it exists
        const index = state.libraries.findIndex(lib => lib.id === action.payload.id);
        if (index !== -1) {
          // Update only the library metadata, not including molecules
          state.libraries[index] = {
            ...action.payload,
            molecules: undefined  // Remove molecules from the libraries array version
          };
        }
      })
      .addCase(fetchLibraryWithMolecules.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch library with molecules';
      });

    // Handle addLibrary
    builder
      .addCase(addLibrary.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(addLibrary.fulfilled, (state, action) => {
        state.loading = false;
        state.libraries.push(action.payload);
        state.totalCount += 1;
        state.totalPages = Math.ceil(state.totalCount / state.pageSize);
      })
      .addCase(addLibrary.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to create library';
      });

    // Handle editLibrary
    builder
      .addCase(editLibrary.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(editLibrary.fulfilled, (state, action) => {
        state.loading = false;
        
        // Update library in libraries array
        const index = state.libraries.findIndex(lib => lib.id === action.payload.id);
        if (index !== -1) {
          state.libraries[index] = action.payload;
        }
        
        // Update currentLibrary if it's the same library
        if (state.currentLibrary && state.currentLibrary.id === action.payload.id) {
          state.currentLibrary = {
            ...state.currentLibrary,
            ...action.payload,
            // Preserve molecules from the current library
            molecules: state.currentLibrary.molecules
          };
        }
      })
      .addCase(editLibrary.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to update library';
      });

    // Handle removeLibrary
    builder
      .addCase(removeLibrary.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(removeLibrary.fulfilled, (state, action) => {
        state.loading = false;
        
        // Remove library from libraries array
        state.libraries = state.libraries.filter(lib => lib.id !== action.payload);
        state.totalCount -= 1;
        state.totalPages = Math.ceil(state.totalCount / state.pageSize);
        
        // Clear currentLibrary if it's the same library
        if (state.currentLibrary && state.currentLibrary.id === action.payload) {
          state.currentLibrary = null;
        }
      })
      .addCase(removeLibrary.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to delete library';
      });

    // Handle filterLibrariesThunk
    builder
      .addCase(filterLibrariesThunk.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(filterLibrariesThunk.fulfilled, (state, action) => {
        state.loading = false;
        state.libraries = action.payload.items;
        state.totalCount = action.payload.total;
        state.currentPage = action.payload.page;
        state.pageSize = action.payload.limit;
        state.totalPages = Math.ceil(action.payload.total / action.payload.limit);
      })
      .addCase(filterLibrariesThunk.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to filter libraries';
      });

    // Handle addMoleculesToLibraryThunk
    builder
      .addCase(addMoleculesToLibraryThunk.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(addMoleculesToLibraryThunk.fulfilled, (state, action) => {
        state.loading = false;
        
        // Update library in libraries array
        const index = state.libraries.findIndex(lib => lib.id === action.payload.id);
        if (index !== -1) {
          state.libraries[index] = {
            ...action.payload,
            molecule_count: action.payload.molecule_count
          };
        }
        
        // Update currentLibrary if it's the same library
        // Note: This doesn't update the molecules array in currentLibrary
        // A separate fetch would be needed to get the updated molecules
        if (state.currentLibrary && state.currentLibrary.id === action.payload.id) {
          state.currentLibrary = {
            ...state.currentLibrary,
            ...action.payload
          };
        }
      })
      .addCase(addMoleculesToLibraryThunk.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to add molecules to library';
      });

    // Handle removeMoleculesFromLibraryThunk
    builder
      .addCase(removeMoleculesFromLibraryThunk.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(removeMoleculesFromLibraryThunk.fulfilled, (state, action) => {
        state.loading = false;
        
        // Update library in libraries array
        const index = state.libraries.findIndex(lib => lib.id === action.payload.id);
        if (index !== -1) {
          state.libraries[index] = {
            ...action.payload,
            molecule_count: action.payload.molecule_count
          };
        }
        
        // Update currentLibrary if it's the same library
        if (state.currentLibrary && state.currentLibrary.id === action.payload.id) {
          // Remove the molecules from the currentLibrary.molecules array
          // This assumes the molecules array exists and the payload includes molecule_ids
          if (state.currentLibrary.molecules && action.meta.arg.molecules.molecule_ids) {
            state.currentLibrary = {
              ...state.currentLibrary,
              ...action.payload,
              molecules: state.currentLibrary.molecules.filter(
                molecule => !action.meta.arg.molecules.molecule_ids.includes(molecule.id)
              )
            };
          } else {
            state.currentLibrary = {
              ...state.currentLibrary,
              ...action.payload
            };
          }
        }
      })
      .addCase(removeMoleculesFromLibraryThunk.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to remove molecules from library';
      });

    // Handle shareLibraryThunk, updateLibraryShareThunk, removeLibraryShareThunk
    // Note: These operations don't directly modify the library state
    // but we handle loading and errors
    builder
      .addCase(shareLibraryThunk.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(shareLibraryThunk.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(shareLibraryThunk.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to share library';
      });

    builder
      .addCase(updateLibraryShareThunk.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateLibraryShareThunk.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(updateLibraryShareThunk.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to update library sharing';
      });

    builder
      .addCase(removeLibraryShareThunk.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(removeLibraryShareThunk.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(removeLibraryShareThunk.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to remove library sharing';
      });
  }
});

// Extract actions from the slice
export const libraryActions = librarySlice.actions;

// Selectors
export const selectLibraries = (state: { libraries: LibraryState }) => state.libraries.libraries;
export const selectCurrentLibrary = (state: { libraries: LibraryState }) => state.libraries.currentLibrary;
export const selectLibraryLoading = (state: { libraries: LibraryState }) => state.libraries.loading;
export const selectLibraryError = (state: { libraries: LibraryState }) => state.libraries.error;
export const selectPagination = (state: { libraries: LibraryState }) => ({
  currentPage: state.libraries.currentPage,
  pageSize: state.libraries.pageSize,
  totalCount: state.libraries.totalCount,
  totalPages: state.libraries.totalPages
});
export const selectFilters = () => ({
  // Filters are not stored in state directly, this is a placeholder
  // In a real implementation, you might store filters in state or use URL params
});

// Export reducer as default
export default librarySlice.reducer;