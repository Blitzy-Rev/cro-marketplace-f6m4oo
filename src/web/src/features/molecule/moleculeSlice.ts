/**
 * Redux slice for molecule state management in the Molecular Data Management and CRO Integration Platform.
 * 
 * This slice handles all molecule-related state including:
 * - Molecule data loading, filtering, and management
 * - CSV upload and processing
 * - AI property predictions
 * - Library organization
 * - User selection state
 * 
 * @version 1.0.0
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'; // v1.9.5
import { 
  Molecule, 
  MoleculeFilter, 
  MoleculeCreate, 
  MoleculeUpdate, 
  MoleculeBatchCreate, 
  MoleculeCSVMapping, 
  MoleculeCSVProcessResult, 
  MoleculePredictionRequest, 
  MoleculePrediction 
} from '../../types/molecule.types';
import { 
  PaginatedResponse, 
  FileUploadResponse, 
  JobStatusResponse
} from '../../types/api.types';
import { 
  getMolecules, 
  getMolecule, 
  createMolecule, 
  updateMolecule, 
  deleteMolecule, 
  filterMolecules, 
  searchMoleculesBySimilarity, 
  searchMoleculesBySubstructure, 
  uploadMoleculeCSV, 
  getCSVPreview, 
  importMoleculesFromCSV, 
  batchCreateMolecules, 
  addMoleculeToLibrary, 
  removeMoleculeFromLibrary, 
  getMoleculesByLibrary, 
  requestMoleculePredictions, 
  getPredictionStatus, 
  getPredictionResults, 
  getMoleculePredictions 
} from '../../api/moleculeApi';

/**
 * Interface defining the structure of the molecule state in Redux store
 */
export interface MoleculeState {
  // Molecule data
  molecules: Molecule[];
  currentMolecule: Molecule | null;
  selectedMolecules: string[];
  
  // UI state
  loading: boolean;
  error: string | null;
  
  // Filtering and pagination
  filter: MoleculeFilter | null;
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
  
  // CSV processing
  csvUpload: {
    loading: boolean;
    error: string | null;
    storageKey: string | null;
  };
  csvPreview: {
    headers: string[];
    rows: string[][];
  } | null;
  csvImportResult: MoleculeCSVProcessResult | null;
  
  // AI predictions
  predictionJobs: Record<string, JobStatusResponse>;
  predictionResults: Record<string, MoleculePrediction[]>;
  predictionLoading: boolean;
  predictionError: string | null;
}

/**
 * Initial state for the molecule slice
 */
const initialState: MoleculeState = {
  molecules: [],
  currentMolecule: null,
  selectedMolecules: [],
  
  loading: false,
  error: null,
  
  filter: null,
  pagination: {
    page: 1,
    pageSize: 25,
    total: 0,
    totalPages: 0
  },
  
  csvUpload: {
    loading: false,
    error: null,
    storageKey: null
  },
  csvPreview: null,
  csvImportResult: null,
  
  predictionJobs: {},
  predictionResults: {},
  predictionLoading: false,
  predictionError: null
};

/**
 * Async thunk for fetching paginated molecules
 */
export const fetchMolecules = createAsyncThunk(
  'molecules/fetchMolecules',
  async ({ page = 1, pageSize = 25, filter = null }: { page?: number; pageSize?: number; filter?: MoleculeFilter | null }) => {
    const response = await getMolecules(page, pageSize, filter || undefined);
    return response.data;
  }
);

/**
 * Async thunk for fetching a single molecule by ID
 */
export const fetchMolecule = createAsyncThunk(
  'molecules/fetchMolecule',
  async (id: string) => {
    const response = await getMolecule(id);
    return response.data;
  }
);

/**
 * Async thunk for creating a new molecule
 */
export const createNewMolecule = createAsyncThunk(
  'molecules/createMolecule',
  async (molecule: MoleculeCreate) => {
    const response = await createMolecule(molecule);
    return response.data;
  }
);

/**
 * Async thunk for updating an existing molecule
 */
export const updateExistingMolecule = createAsyncThunk(
  'molecules/updateMolecule',
  async ({ id, molecule }: { id: string; molecule: MoleculeUpdate }) => {
    const response = await updateMolecule(id, molecule);
    return response.data;
  }
);

/**
 * Async thunk for deleting a molecule
 */
export const deleteExistingMolecule = createAsyncThunk(
  'molecules/deleteMolecule',
  async (id: string) => {
    await deleteMolecule(id);
    return id;
  }
);

/**
 * Async thunk for filtering molecules by complex criteria
 */
export const filterMoleculeList = createAsyncThunk(
  'molecules/filterMolecules',
  async ({ filter, page = 1, pageSize = 25 }: { filter: MoleculeFilter; page?: number; pageSize?: number }) => {
    const response = await filterMolecules(filter, page, pageSize);
    return response.data;
  }
);

/**
 * Async thunk for searching molecules by structural similarity
 */
export const searchBySimilarity = createAsyncThunk(
  'molecules/searchBySimilarity',
  async ({ smiles, threshold = 0.7, page = 1, pageSize = 25 }: 
    { smiles: string; threshold?: number; page?: number; pageSize?: number }) => {
    const response = await searchMoleculesBySimilarity(smiles, threshold, page, pageSize);
    return response.data;
  }
);

/**
 * Async thunk for searching molecules by substructure
 */
export const searchBySubstructure = createAsyncThunk(
  'molecules/searchBySubstructure',
  async ({ smiles, page = 1, pageSize = 25 }: { smiles: string; page?: number; pageSize?: number }) => {
    const response = await searchMoleculesBySubstructure(smiles, page, pageSize);
    return response.data;
  }
);

/**
 * Async thunk for uploading a CSV file with molecular data
 */
export const uploadCSV = createAsyncThunk(
  'molecules/uploadCSV',
  async (file: File) => {
    const response = await uploadMoleculeCSV(file);
    return response.data;
  }
);

/**
 * Async thunk for getting a preview of CSV file contents
 */
export const getCSVPreviewData = createAsyncThunk(
  'molecules/getCSVPreview',
  async (storageKey: string) => {
    const response = await getCSVPreview(storageKey);
    return response.data;
  }
);

/**
 * Async thunk for importing molecules from a CSV file
 */
export const importCSV = createAsyncThunk(
  'molecules/importCSV',
  async ({ storageKey, mapping }: { storageKey: string; mapping: MoleculeCSVMapping }) => {
    const response = await importMoleculesFromCSV(storageKey, mapping);
    return response.data;
  }
);

/**
 * Async thunk for creating multiple molecules in a batch
 */
export const batchCreateMoleculeList = createAsyncThunk(
  'molecules/batchCreate',
  async (batch: MoleculeBatchCreate) => {
    const response = await batchCreateMolecules(batch);
    return response.data;
  }
);

/**
 * Async thunk for adding a molecule to a library
 */
export const addToLibrary = createAsyncThunk(
  'molecules/addToLibrary',
  async ({ moleculeId, libraryId }: { moleculeId: string; libraryId: string }) => {
    await addMoleculeToLibrary(moleculeId, libraryId);
    return { moleculeId, libraryId };
  }
);

/**
 * Async thunk for removing a molecule from a library
 */
export const removeFromLibrary = createAsyncThunk(
  'molecules/removeFromLibrary',
  async ({ moleculeId, libraryId }: { moleculeId: string; libraryId: string }) => {
    await removeMoleculeFromLibrary(moleculeId, libraryId);
    return { moleculeId, libraryId };
  }
);

/**
 * Async thunk for fetching molecules in a specific library
 */
export const fetchMoleculesByLibrary = createAsyncThunk(
  'molecules/fetchByLibrary',
  async ({ libraryId, page = 1, pageSize = 25, filter = null }: 
    { libraryId: string; page?: number; pageSize?: number; filter?: MoleculeFilter | null }) => {
    const response = await getMoleculesByLibrary(libraryId, page, pageSize, filter || undefined);
    return response.data;
  }
);

/**
 * Async thunk for requesting AI property predictions
 */
export const requestPredictions = createAsyncThunk(
  'molecules/requestPredictions',
  async (request: MoleculePredictionRequest) => {
    const response = await requestMoleculePredictions(request);
    return response.data;
  }
);

/**
 * Async thunk for checking prediction job status
 */
export const checkPredictionStatus = createAsyncThunk(
  'molecules/checkPredictionStatus',
  async (jobId: string) => {
    const response = await getPredictionStatus(jobId);
    return response.data;
  }
);

/**
 * Async thunk for fetching prediction results
 */
export const fetchPredictionResults = createAsyncThunk(
  'molecules/fetchPredictionResults',
  async (jobId: string) => {
    const response = await getPredictionResults(jobId);
    return { jobId, results: response.data };
  }
);

/**
 * Async thunk for fetching predictions for a specific molecule
 */
export const fetchMoleculePredictions = createAsyncThunk(
  'molecules/fetchMoleculePredictions',
  async (moleculeId: string) => {
    const response = await getMoleculePredictions(moleculeId);
    return { moleculeId, predictions: response.data };
  }
);

/**
 * Redux slice for molecule state management
 */
export const moleculeSlice = createSlice({
  name: 'molecule',
  initialState,
  reducers: {
    /**
     * Set the filter used for molecule queries
     */
    setFilter: (state, action: PayloadAction<MoleculeFilter>) => {
      state.filter = action.payload;
    },
    
    /**
     * Clear the current filter
     */
    clearFilter: (state) => {
      state.filter = null;
    },
    
    /**
     * Set the currently selected molecule
     */
    setCurrentMolecule: (state, action: PayloadAction<Molecule>) => {
      state.currentMolecule = action.payload;
    },
    
    /**
     * Clear the currently selected molecule
     */
    clearCurrentMolecule: (state) => {
      state.currentMolecule = null;
    },
    
    /**
     * Set the list of selected molecule IDs
     */
    setSelectedMolecules: (state, action: PayloadAction<string[]>) => {
      state.selectedMolecules = action.payload;
    },
    
    /**
     * Clear the list of selected molecule IDs
     */
    clearSelectedMolecules: (state) => {
      state.selectedMolecules = [];
    },
    
    /**
     * Reset the entire molecule state to initial values
     */
    resetMoleculeState: (state) => {
      return initialState;
    }
  },
  extraReducers: (builder) => {
    // Fetch molecules
    builder.addCase(fetchMolecules.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchMolecules.fulfilled, (state, action) => {
      state.loading = false;
      state.molecules = action.payload.items;
      state.pagination = {
        page: action.payload.page,
        pageSize: action.payload.page_size,
        total: action.payload.total,
        totalPages: action.payload.total_pages
      };
    });
    builder.addCase(fetchMolecules.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to fetch molecules';
    });
    
    // Fetch single molecule
    builder.addCase(fetchMolecule.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchMolecule.fulfilled, (state, action) => {
      state.loading = false;
      state.currentMolecule = action.payload;
      
      // Also update the molecule in the list if it exists
      const index = state.molecules.findIndex(m => m.id === action.payload.id);
      if (index !== -1) {
        state.molecules[index] = action.payload;
      }
    });
    builder.addCase(fetchMolecule.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to fetch molecule';
    });
    
    // Create molecule
    builder.addCase(createNewMolecule.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(createNewMolecule.fulfilled, (state, action) => {
      state.loading = false;
      state.molecules.push(action.payload);
      state.currentMolecule = action.payload;
    });
    builder.addCase(createNewMolecule.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to create molecule';
    });
    
    // Update molecule
    builder.addCase(updateExistingMolecule.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(updateExistingMolecule.fulfilled, (state, action) => {
      state.loading = false;
      
      // Update in molecules list
      const index = state.molecules.findIndex(m => m.id === action.payload.id);
      if (index !== -1) {
        state.molecules[index] = action.payload;
      }
      
      // Update current molecule if it's the same
      if (state.currentMolecule?.id === action.payload.id) {
        state.currentMolecule = action.payload;
      }
    });
    builder.addCase(updateExistingMolecule.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to update molecule';
    });
    
    // Delete molecule
    builder.addCase(deleteExistingMolecule.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(deleteExistingMolecule.fulfilled, (state, action) => {
      state.loading = false;
      
      // Remove from molecules list
      state.molecules = state.molecules.filter(m => m.id !== action.payload);
      
      // Clear current molecule if it's the same
      if (state.currentMolecule?.id === action.payload) {
        state.currentMolecule = null;
      }
      
      // Remove from selected molecules if present
      state.selectedMolecules = state.selectedMolecules.filter(id => id !== action.payload);
    });
    builder.addCase(deleteExistingMolecule.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to delete molecule';
    });
    
    // Filter molecules - reuses the same pattern as fetchMolecules
    builder.addCase(filterMoleculeList.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(filterMoleculeList.fulfilled, (state, action) => {
      state.loading = false;
      state.molecules = action.payload.items;
      state.pagination = {
        page: action.payload.page,
        pageSize: action.payload.page_size,
        total: action.payload.total,
        totalPages: action.payload.total_pages
      };
    });
    builder.addCase(filterMoleculeList.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to filter molecules';
    });
    
    // Similarity search - reuses the same pattern as fetchMolecules
    builder.addCase(searchBySimilarity.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(searchBySimilarity.fulfilled, (state, action) => {
      state.loading = false;
      state.molecules = action.payload.items;
      state.pagination = {
        page: action.payload.page,
        pageSize: action.payload.page_size,
        total: action.payload.total,
        totalPages: action.payload.total_pages
      };
    });
    builder.addCase(searchBySimilarity.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to perform similarity search';
    });
    
    // Substructure search - reuses the same pattern as fetchMolecules
    builder.addCase(searchBySubstructure.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(searchBySubstructure.fulfilled, (state, action) => {
      state.loading = false;
      state.molecules = action.payload.items;
      state.pagination = {
        page: action.payload.page,
        pageSize: action.payload.page_size,
        total: action.payload.total,
        totalPages: action.payload.total_pages
      };
    });
    builder.addCase(searchBySubstructure.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to perform substructure search';
    });
    
    // CSV upload
    builder.addCase(uploadCSV.pending, (state) => {
      state.csvUpload.loading = true;
      state.csvUpload.error = null;
    });
    builder.addCase(uploadCSV.fulfilled, (state, action) => {
      state.csvUpload.loading = false;
      state.csvUpload.storageKey = action.payload.storage_key;
    });
    builder.addCase(uploadCSV.rejected, (state, action) => {
      state.csvUpload.loading = false;
      state.csvUpload.error = action.error.message || 'Failed to upload CSV file';
    });
    
    // CSV preview
    builder.addCase(getCSVPreviewData.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(getCSVPreviewData.fulfilled, (state, action) => {
      state.loading = false;
      state.csvPreview = action.payload;
    });
    builder.addCase(getCSVPreviewData.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to get CSV preview';
    });
    
    // Import CSV
    builder.addCase(importCSV.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(importCSV.fulfilled, (state, action) => {
      state.loading = false;
      state.csvImportResult = action.payload;
    });
    builder.addCase(importCSV.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to import CSV data';
    });
    
    // Batch create molecules
    builder.addCase(batchCreateMoleculeList.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(batchCreateMoleculeList.fulfilled, (state) => {
      state.loading = false;
      // We don't update the molecules list here because it would require a separate fetch
      // to get the complete molecule objects
    });
    builder.addCase(batchCreateMoleculeList.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to create molecules in batch';
    });
    
    // Add molecule to library
    builder.addCase(addToLibrary.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(addToLibrary.fulfilled, (state, action) => {
      state.loading = false;
      
      // Update molecule in list to include library
      const { moleculeId, libraryId } = action.payload;
      const molecule = state.molecules.find(m => m.id === moleculeId);
      if (molecule) {
        if (!molecule.libraries) {
          molecule.libraries = [libraryId];
        } else if (!molecule.libraries.includes(libraryId)) {
          molecule.libraries.push(libraryId);
        }
      }
      
      // Update current molecule if it's the same
      if (state.currentMolecule?.id === moleculeId) {
        if (!state.currentMolecule.libraries) {
          state.currentMolecule.libraries = [libraryId];
        } else if (!state.currentMolecule.libraries.includes(libraryId)) {
          state.currentMolecule.libraries.push(libraryId);
        }
      }
    });
    builder.addCase(addToLibrary.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to add molecule to library';
    });
    
    // Remove molecule from library
    builder.addCase(removeFromLibrary.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(removeFromLibrary.fulfilled, (state, action) => {
      state.loading = false;
      
      // Update molecule in list to remove library
      const { moleculeId, libraryId } = action.payload;
      const molecule = state.molecules.find(m => m.id === moleculeId);
      if (molecule && molecule.libraries) {
        molecule.libraries = molecule.libraries.filter(id => id !== libraryId);
      }
      
      // Update current molecule if it's the same
      if (state.currentMolecule?.id === moleculeId && state.currentMolecule.libraries) {
        state.currentMolecule.libraries = state.currentMolecule.libraries.filter(id => id !== libraryId);
      }
    });
    builder.addCase(removeFromLibrary.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to remove molecule from library';
    });
    
    // Fetch molecules by library - reuses the same pattern as fetchMolecules
    builder.addCase(fetchMoleculesByLibrary.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchMoleculesByLibrary.fulfilled, (state, action) => {
      state.loading = false;
      state.molecules = action.payload.items;
      state.pagination = {
        page: action.payload.page,
        pageSize: action.payload.page_size,
        total: action.payload.total,
        totalPages: action.payload.total_pages
      };
    });
    builder.addCase(fetchMoleculesByLibrary.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to fetch molecules from library';
    });
    
    // Request predictions
    builder.addCase(requestPredictions.pending, (state) => {
      state.predictionLoading = true;
      state.predictionError = null;
    });
    builder.addCase(requestPredictions.fulfilled, (state, action) => {
      state.predictionLoading = false;
      state.predictionJobs[action.payload.job_id] = action.payload;
    });
    builder.addCase(requestPredictions.rejected, (state, action) => {
      state.predictionLoading = false;
      state.predictionError = action.error.message || 'Failed to request predictions';
    });
    
    // Check prediction status
    builder.addCase(checkPredictionStatus.pending, (state) => {
      state.predictionLoading = true;
      state.predictionError = null;
    });
    builder.addCase(checkPredictionStatus.fulfilled, (state, action) => {
      state.predictionLoading = false;
      state.predictionJobs[action.payload.job_id] = action.payload;
    });
    builder.addCase(checkPredictionStatus.rejected, (state, action) => {
      state.predictionLoading = false;
      state.predictionError = action.error.message || 'Failed to check prediction status';
    });
    
    // Fetch prediction results
    builder.addCase(fetchPredictionResults.pending, (state) => {
      state.predictionLoading = true;
      state.predictionError = null;
    });
    builder.addCase(fetchPredictionResults.fulfilled, (state, action) => {
      state.predictionLoading = false;
      state.predictionResults[action.payload.jobId] = action.payload.results;
    });
    builder.addCase(fetchPredictionResults.rejected, (state, action) => {
      state.predictionLoading = false;
      state.predictionError = action.error.message || 'Failed to fetch prediction results';
    });
    
    // Fetch molecule predictions
    builder.addCase(fetchMoleculePredictions.pending, (state) => {
      state.predictionLoading = true;
      state.predictionError = null;
    });
    builder.addCase(fetchMoleculePredictions.fulfilled, (state, action) => {
      state.predictionLoading = false;
      // Store molecule predictions under a special key format
      state.predictionResults[`molecule_${action.payload.moleculeId}`] = action.payload.predictions;
    });
    builder.addCase(fetchMoleculePredictions.rejected, (state, action) => {
      state.predictionLoading = false;
      state.predictionError = action.error.message || 'Failed to fetch molecule predictions';
    });
  }
});

// Export actions
export const { 
  setFilter, 
  clearFilter, 
  setCurrentMolecule, 
  clearCurrentMolecule,
  setSelectedMolecules,
  clearSelectedMolecules,
  resetMoleculeState
} = moleculeSlice.actions;

// Selectors
export const selectMoleculeState = (state: { molecule: MoleculeState }) => state.molecule;
export const selectMolecules = (state: { molecule: MoleculeState }) => state.molecule.molecules;
export const selectCurrentMolecule = (state: { molecule: MoleculeState }) => state.molecule.currentMolecule;
export const selectMoleculeLoading = (state: { molecule: MoleculeState }) => state.molecule.loading;
export const selectMoleculeError = (state: { molecule: MoleculeState }) => state.molecule.error;
export const selectPagination = (state: { molecule: MoleculeState }) => state.molecule.pagination;
export const selectCSVUploadState = (state: { molecule: MoleculeState }) => state.molecule.csvUpload;
export const selectCSVPreviewData = (state: { molecule: MoleculeState }) => state.molecule.csvPreview;
export const selectCSVImportResult = (state: { molecule: MoleculeState }) => state.molecule.csvImportResult;
export const selectPredictionJobs = (state: { molecule: MoleculeState }) => state.molecule.predictionJobs;
export const selectPredictionResults = (state: { molecule: MoleculeState }) => state.molecule.predictionResults;
export const selectSelectedMolecules = (state: { molecule: MoleculeState }) => state.molecule.selectedMolecules;
export const selectFilter = (state: { molecule: MoleculeState }) => state.molecule.filter;
export const selectPredictionLoading = (state: { molecule: MoleculeState }) => state.molecule.predictionLoading;
export const selectPredictionError = (state: { molecule: MoleculeState }) => state.molecule.predictionError;

export default moleculeSlice.reducer;