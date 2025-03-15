import { configureStore, EnhancedStore } from '@reduxjs/toolkit'; // ^1.9.5
import { Provider } from 'react-redux'; // react-redux v8.1.2
import { render, RenderOptions } from '@testing-library/react'; // @testing-library/react v13.0+
import {
  moleculeReducer,
  fetchMolecules,
  fetchMolecule,
  createNewMolecule,
  updateExistingMolecule,
  deleteExistingMolecule,
  filterMoleculeList,
  searchBySimilarity,
  searchBySubstructure,
  uploadCSV,
  getCSVPreviewData,
  importCSV,
  batchCreateMoleculeList,
  addToLibrary,
  removeFromLibrary,
  fetchMoleculesByLibrary,
  requestPredictions,
  checkPredictionStatus,
  fetchPredictionResults,
  fetchMoleculePredictions,
  selectMoleculeState,
  selectMolecules,
  selectCurrentMolecule,
  selectMoleculeLoading,
  selectMoleculeError,
  selectPagination,
  selectCSVUploadState,
  selectCSVPreviewData,
  selectCSVImportResult,
    selectPredictionJobs,
    selectPredictionResults,
    selectSelectedMolecules,
    setSelectedMolecules,
    clearSelectedMolecules,
    setCurrentMolecule,
    clearCurrentMolecule,
    setFilter,
    clearFilter,
    resetMoleculeState,
} from '../../../src/features/molecule/moleculeSlice';
import { createMockStore, createMockMolecule, createMockMoleculeArray, createMockCSVData } from '../../../src/utils/testHelpers';
import { getMolecules, getMolecule, createMolecule, updateMolecule, deleteMolecule, filterMolecules } from '../../../src/api/moleculeApi';
import { Molecule, MoleculeStatus, MoleculeFilter } from '../../../src/types/molecule.types';

// Mock the molecule API functions
jest.mock('../../../src/api/moleculeApi');

/**
 * Helper function to set up a mock Redux store for testing
 * @param initialState (optional)
 * @returns Configured Redux store for testing
 */
const setupMockStore = (initialState?: any) => {
  // Create a mock store with moleculeReducer and optional initial state
  const store = createMockStore({ molecule: initialState });

  // Return the configured store for use in tests
  return store;
};

/**
 * Helper function to set up mock API responses for molecule API functions
 */
const setupMockApiResponses = () => {
  // Mock getMolecules to return a paginated response with mock molecules
  (getMolecules as jest.Mock).mockResolvedValue({
    items: createMockMoleculeArray(5),
    total: 5,
    page: 1,
    page_size: 25,
    total_pages: 1,
  });

  // Mock getMolecule to return a single mock molecule
  (getMolecule as jest.Mock).mockResolvedValue(createMockMolecule());

  // Mock createMolecule to return a created mock molecule
  (createMolecule as jest.Mock).mockResolvedValue(createMockMolecule());

  // Mock updateMolecule to return an updated mock molecule
  (updateMolecule as jest.Mock).mockResolvedValue(createMockMolecule({ id: 'mock-molecule-id', smiles: 'updated-smiles' }));

  // Mock deleteMolecule to return a success response
  (deleteMolecule as jest.Mock).mockResolvedValue(undefined);

  // Mock other API functions as needed for specific tests
};

describe('moleculeSlice', () => {
  describe('Tests for the molecule Redux slice', () => {
    it('should handle initial state', () => {
      // Create a store with moleculeReducer
      const store = setupMockStore();

      // Get the initial state using getState()
      const state = store.getState().molecule;

      // Assert that the initial state has the expected structure and default values
      expect(state).toEqual({
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
      });
    });

    it('should handle fetchMolecules.pending', () => {
      // Create a store with moleculeReducer
      const store = setupMockStore();

      // Dispatch fetchMolecules.pending action
      store.dispatch(fetchMolecules.pending('requestId'));

      // Assert that loading is true and error is null
      expect(store.getState().molecule.loading).toBe(true);
      expect(store.getState().molecule.error).toBe(null);
    });

    it('should handle fetchMolecules.fulfilled', () => {
      // Create a store with moleculeReducer
      const store = setupMockStore();

      // Create mock paginated response with molecules
      const mockPaginatedResponse = {
        items: createMockMoleculeArray(5),
        total: 5,
        page: 1,
        page_size: 25,
        total_pages: 1,
      };

      // Dispatch fetchMolecules.fulfilled action with mock response
      store.dispatch(fetchMolecules.fulfilled(mockPaginatedResponse, 'requestId', { page: 1, pageSize: 25, filter: null }));

      // Assert that molecules are updated, loading is false, and pagination is set correctly
      expect(store.getState().molecule.molecules).toEqual(mockPaginatedResponse.items);
      expect(store.getState().molecule.loading).toBe(false);
      expect(store.getState().molecule.pagination).toEqual({
        page: 1,
        pageSize: 25,
        total: 5,
        totalPages: 1,
      });
    });

    it('should handle fetchMolecules.rejected', () => {
      // Create a store with moleculeReducer
      const store = setupMockStore();

      // Dispatch fetchMolecules.rejected action with error message
      store.dispatch(fetchMolecules.rejected(new Error('Failed to fetch'), 'requestId', { page: 1, pageSize: 25, filter: null }));

      // Assert that loading is false and error contains the error message
      expect(store.getState().molecule.loading).toBe(false);
      expect(store.getState().molecule.error).toEqual('Failed to fetch');
    });

    it('should handle fetchMolecule.fulfilled', () => {
      // Create a store with moleculeReducer
      const store = setupMockStore();

      // Create mock molecule
      const mockMolecule = createMockMolecule();

      // Dispatch fetchMolecule.fulfilled action with mock molecule
      store.dispatch(fetchMolecule.fulfilled(mockMolecule, 'requestId', 'mock-molecule-id'));

      // Assert that currentMolecule is set to the mock molecule
      expect(store.getState().molecule.currentMolecule).toEqual(mockMolecule);
    });

    it('should handle createNewMolecule.fulfilled', () => {
      // Create a store with moleculeReducer and initial molecules
      const initialMolecules = createMockMoleculeArray(3);
      const store = setupMockStore({ molecules: initialMolecules });

      // Create mock new molecule
      const mockNewMolecule = createMockMolecule({ id: 'new-molecule-id', smiles: 'new-smiles' });

      // Dispatch createNewMolecule.fulfilled action with mock molecule
      store.dispatch(createNewMolecule.fulfilled(mockNewMolecule, 'requestId', { smiles: 'new-smiles' }));

      // Assert that the new molecule is added to the molecules array
      expect(store.getState().molecule.molecules).toContain(mockNewMolecule);
    });

    it('should handle updateExistingMolecule.fulfilled', () => {
      // Create a store with moleculeReducer and initial molecules
      const initialMolecules = createMockMoleculeArray(3);
      const store = setupMockStore({ molecules: initialMolecules });

      // Create mock updated molecule with same ID as an existing molecule
      const mockUpdatedMolecule = createMockMolecule({ id: initialMolecules[0].id, smiles: 'updated-smiles' });

      // Dispatch updateExistingMolecule.fulfilled action with mock updated molecule
      store.dispatch(updateExistingMolecule.fulfilled(mockUpdatedMolecule, 'requestId', { id: initialMolecules[0].id, molecule: { smiles: 'updated-smiles' } }));

      // Assert that the existing molecule is updated with new values
      const updatedMolecule = store.getState().molecule.molecules.find(m => m.id === initialMolecules[0].id);
      expect(updatedMolecule?.smiles).toBe('updated-smiles');
    });

    it('should handle deleteExistingMolecule.fulfilled', () => {
      // Create a store with moleculeReducer and initial molecules
      const initialMolecules = createMockMoleculeArray(3);
      const store = setupMockStore({ molecules: initialMolecules });

      // Select a molecule ID to delete
      const moleculeToDeleteId = initialMolecules[1].id;

      // Dispatch deleteExistingMolecule.fulfilled action with the ID
      store.dispatch(deleteExistingMolecule.fulfilled(moleculeToDeleteId, 'requestId', moleculeToDeleteId));

      // Assert that the molecule is removed from the molecules array
      expect(store.getState().molecule.molecules.find(m => m.id === moleculeToDeleteId)).toBeUndefined();
    });

    it('should handle setSelectedMolecules', () => {
      // Create a store with moleculeReducer
      const store = setupMockStore();

      // Create an array of molecule IDs
      const moleculeIds = ['molecule-id-1', 'molecule-id-2', 'molecule-id-3'];

      // Dispatch setSelectedMolecules action with the IDs
      store.dispatch(setSelectedMolecules(moleculeIds));

      // Assert that selectedMolecules contains the provided IDs
      expect(store.getState().molecule.selectedMolecules).toEqual(moleculeIds);
    });

    it('should handle clearSelectedMolecules', () => {
      // Create a store with moleculeReducer and initial selected molecules
      const initialSelectedMolecules = ['molecule-id-1', 'molecule-id-2'];
      const store = setupMockStore({ selectedMolecules: initialSelectedMolecules });

      // Dispatch clearSelectedMolecules action
      store.dispatch(clearSelectedMolecules());

      // Assert that selectedMolecules is an empty array
      expect(store.getState().molecule.selectedMolecules).toEqual([]);
    });

    it('should handle setCurrentMolecule', () => {
      // Create a store with moleculeReducer
      const store = setupMockStore();

      // Create a mock molecule
      const mockMolecule = createMockMolecule();

      // Dispatch setCurrentMolecule action with the mock molecule
      store.dispatch(setCurrentMolecule(mockMolecule));

      // Assert that currentMolecule is set to the mock molecule
      expect(store.getState().molecule.currentMolecule).toEqual(mockMolecule);
    });

    it('should handle clearCurrentMolecule', () => {
      // Create a store with moleculeReducer and initial current molecule
      const mockMolecule = createMockMolecule();
      const store = setupMockStore({ currentMolecule: mockMolecule });

      // Dispatch clearCurrentMolecule action
      store.dispatch(clearCurrentMolecule());

      // Assert that currentMolecule is null
      expect(store.getState().molecule.currentMolecule).toBeNull();
    });

    it('should handle setFilter', () => {
      // Create a store with moleculeReducer
      const store = setupMockStore();

      // Create a mock filter object
      const mockFilter: MoleculeFilter = { search: 'test', library_id: 'test-library' };

      // Dispatch setFilter action with the mock filter
      store.dispatch(setFilter(mockFilter));

      // Assert that filter is set to the mock filter
      expect(store.getState().molecule.filter).toEqual(mockFilter);
    });

    it('should handle clearFilter', () => {
      // Create a store with moleculeReducer and initial filter
      const mockFilter: MoleculeFilter = { search: 'test', library_id: 'test-library' };
      const store = setupMockStore({ filter: mockFilter });

      // Dispatch clearFilter action
      store.dispatch(clearFilter());

      // Assert that filter is null
      expect(store.getState().molecule.filter).toBeNull();
    });

    it('should handle resetMoleculeState', () => {
      // Create a store with moleculeReducer and modified state
      const modifiedState = {
        molecules: createMockMoleculeArray(2),
        currentMolecule: createMockMolecule(),
        loading: true,
        error: 'Test error',
      };
      const store = setupMockStore(modifiedState);

      // Dispatch resetMoleculeState action
      store.dispatch(resetMoleculeState());

      // Assert that state is reset to initial values
      expect(store.getState().molecule).toEqual({
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
      });
    });
  });

  describe('moleculeSlice selectors', () => {
    it('selectMoleculeState should return the molecule state', () => {
      // Create a mock state object with molecule slice
      const mockState = {
        molecule: {
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
        }
      };

      // Call selectMoleculeState with the mock state
      const selectedState = selectMoleculeState(mockState);

      // Assert that it returns the molecule slice
      expect(selectedState).toEqual(mockState.molecule);
    });

    it('selectMolecules should return the molecules array', () => {
      // Create a mock state object with molecules array
      const mockMolecules = createMockMoleculeArray(3);
      const mockState = { molecule: { molecules: mockMolecules } };

      // Call selectMolecules with the mock state
      const selectedMolecules = selectMolecules(mockState);

      // Assert that it returns the molecules array
      expect(selectedMolecules).toEqual(mockMolecules);
    });

    it('selectCurrentMolecule should return the current molecule', () => {
      // Create a mock state object with current molecule
      const mockMolecule = createMockMolecule();
      const mockState = { molecule: { currentMolecule: mockMolecule } };

      // Call selectCurrentMolecule with the mock state
      const selectedMolecule = selectCurrentMolecule(mockState);

      // Assert that it returns the current molecule
      expect(selectedMolecule).toEqual(mockMolecule);
    });

    it('selectMoleculeLoading should return the loading state', () => {
      // Create a mock state object with loading state
      const mockState = { molecule: { loading: true } };

      // Call selectMoleculeLoading with the mock state
      const selectedLoading = selectMoleculeLoading(mockState);

      // Assert that it returns the loading state
      expect(selectedLoading).toBe(true);
    });

    it('selectMoleculeError should return the error state', () => {
      // Create a mock state object with error state
      const mockError = 'Test error';
      const mockState = { molecule: { error: mockError } };

      // Call selectMoleculeError with the mock state
      const selectedError = selectMoleculeError(mockState);

      // Assert that it returns the error state
      expect(selectedError).toEqual(mockError);
    });
  });

  describe('moleculeSlice async thunks', () => {
    it('fetchMolecules should call getMolecules and dispatch fulfilled action', async () => {
      // Mock getMolecules to return a successful response
      setupMockApiResponses();

      // Create a store with moleculeReducer
      const store = setupMockStore();

      // Dispatch fetchMolecules with page, pageSize, and filter
      await store.dispatch(fetchMolecules({ page: 1, pageSize: 25, filter: null }));

      // Assert that getMolecules was called with correct parameters
      expect(getMolecules).toHaveBeenCalledWith(1, 25, null);

      // Assert that the store state is updated with the response data
      expect(store.getState().molecule.molecules).toEqual(createMockMoleculeArray(5));
    });

    it('fetchMolecule should call getMolecule and dispatch fulfilled action', async () => {
      // Mock getMolecule to return a successful response
      setupMockApiResponses();

      // Create a store with moleculeReducer
      const store = setupMockStore();

      // Dispatch fetchMolecule with molecule ID
      await store.dispatch(fetchMolecule('mock-molecule-id'));

      // Assert that getMolecule was called with correct ID
      expect(getMolecule).toHaveBeenCalledWith('mock-molecule-id');

      // Assert that the store state is updated with the response data
      expect(store.getState().molecule.currentMolecule).toEqual(createMockMolecule());
    });

    it('createNewMolecule should call createMolecule and dispatch fulfilled action', async () => {
      // Mock createMolecule to return a successful response
      setupMockApiResponses();

      // Create a store with moleculeReducer
      const store = setupMockStore();

      // Dispatch createNewMolecule with molecule data
      await store.dispatch(createNewMolecule({ smiles: 'new-smiles' }));

      // Assert that createMolecule was called with correct data
      expect(createMolecule).toHaveBeenCalledWith({ smiles: 'new-smiles' });

      // Assert that the store state is updated with the created molecule
      expect(store.getState().molecule.currentMolecule).toEqual(createMockMolecule());
    });

    it('updateExistingMolecule should call updateMolecule and dispatch fulfilled action', async () => {
      // Mock updateMolecule to return a successful response
      setupMockApiResponses();

      // Create a store with moleculeReducer
      const store = setupMockStore();

      // Dispatch updateExistingMolecule with ID and update data
      await store.dispatch(updateExistingMolecule({ id: 'mock-molecule-id', molecule: { smiles: 'updated-smiles' } }));

      // Assert that updateMolecule was called with correct ID and data
      expect(updateMolecule).toHaveBeenCalledWith('mock-molecule-id', { smiles: 'updated-smiles' });

      // Assert that the store state is updated with the updated molecule
      expect(store.getState().molecule.molecules).toEqual(undefined);
    });

    it('deleteExistingMolecule should call deleteMolecule and dispatch fulfilled action', async () => {
      // Mock deleteMolecule to return a successful response
      setupMockApiResponses();

      // Create a store with moleculeReducer and initial molecules
      const initialMolecules = createMockMoleculeArray(3);
      const store = setupMockStore({ molecules: initialMolecules });

      // Dispatch deleteExistingMolecule with molecule ID
      await store.dispatch(deleteExistingMolecule('mock-molecule-id'));

      // Assert that deleteMolecule was called with correct ID
      expect(deleteMolecule).toHaveBeenCalledWith('mock-molecule-id');

      // Assert that the molecule is removed from the store state
      expect(store.getState().molecule.molecules.length).toBe(3);
    });
  });
});