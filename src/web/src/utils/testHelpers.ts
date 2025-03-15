import React from 'react'; // react v18.0+
import ReactDOM from 'react-dom'; // react-dom v18.0+
import { render, RenderOptions } from '@testing-library/react'; // @testing-library/react v13.0+
import { configureStore, EnhancedStore } from '@reduxjs/toolkit'; // @reduxjs/toolkit v1.9.5
import { Provider } from 'react-redux'; // react-redux v8.1.2
import { ThemeProvider } from '@mui/material'; // @mui/material v5.0+
import { theme } from '@mui/material/styles'; // @mui/material/styles v5.0+
import { MemoryRouter } from 'react-router-dom'; // react-router-dom v6.0+
import { axe, toHaveNoViolations } from 'jest-axe'; // jest-axe v7.0.1
import { store, RootState, AppDispatch, rootReducer } from '../store';
import { Molecule, MoleculeStatus, PropertyType, PropertySource } from '../types/molecule.types';

// Extend Jest expect to include accessibility checks
expect.extend(toHaveNoViolations);

/**
 * Renders a React component with all necessary providers for testing
 * @param ui - React component to render
 * @param options - Optional configuration for testing environment
 * @returns Rendered component with additional test utilities
 */
export function renderWithProviders(
  ui: React.ReactElement,
  options?: {
    preloadedState?: Partial<RootState>;
    store?: EnhancedStore;
    renderOptions?: RenderOptions;
  }
) {
  // LD1: Create a mock store with preloaded state if provided
  const testStore = options?.store ?? createMockStore(options?.preloadedState);

  // LD1: Wrap component with Redux Provider
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <Provider store={testStore}>
      {/* LD1: Wrap component with ThemeProvider for Material UI */}
      <ThemeProvider theme={theme}>
        {/* LD1: Wrap component with MemoryRouter for routing */}
        <MemoryRouter>
          {children}
        </MemoryRouter>
      </ThemeProvider>
    </Provider>
  );

  // LD1: Render the wrapped component
  const renderResult = render(ui, { wrapper, ...options?.renderOptions });

  // LD1: Return rendered component with additional test utilities
  return {
    ...renderResult,
    store: testStore,
  };
}

/**
 * Creates a mock Redux store with optional preloaded state for testing
 * @param preloadedState - Optional initial state for the store
 * @returns Configured Redux store
 */
export const createMockStore = (preloadedState?: Partial<RootState>) => {
  // LD1: Configure store with root reducer
  // LD1: Apply preloaded state if provided
  // LD1: Return configured store
  return configureStore({ 
    reducer: rootReducer,
    preloadedState: preloadedState as RootState
  });
};

/**
 * Creates a mock molecule object for testing
 * @param overrides - Optional overrides for the default molecule properties
 * @returns Mock molecule with default values and overrides
 */
export const createMockMolecule = (overrides?: Partial<Molecule>): Molecule => {
  // LD1: Create default molecule object with required properties
  const defaultMolecule: Molecule = {
    id: 'mock-molecule-id',
    smiles: 'CC(=O)Oc1ccccc1C(=O)O',
    inchi_key: 'mock-inchi-key',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  // LD1: Apply overrides to default molecule
  const mergedMolecule: Molecule = { ...defaultMolecule, ...overrides };

  // LD1: Return merged molecule object
  return mergedMolecule;
};

/**
 * Creates an array of mock molecules for testing
 * @param count - Number of mock molecules to create
 * @param baseOverrides - Optional base overrides for all molecules
 * @returns Array of mock molecules
 */
export const createMockMoleculeArray = (count: number, baseOverrides?: Partial<Molecule>): Molecule[] => {
  // LD1: Create an empty array
  const molecules: Molecule[] = [];

  // LD1: Loop count times to create mock molecules
  for (let i = 0; i < count; i++) {
    // LD1: Apply baseOverrides and index-specific overrides to each molecule
    const molecule = createMockMolecule({
      id: `mock-molecule-id-${i}`,
      ...baseOverrides,
    });
    molecules.push(molecule);
  }

  // LD1: Return array of mock molecules
  return molecules;
};

/**
 * Creates mock CSV data for testing CSV import functionality
 * @param rowCount - Number of rows to generate
 * @param headers - Array of column headers
 * @returns Mock CSV data object with headers and rows
 */
export const createMockCSVData = (rowCount: number, headers?: string[]) => {
  // LD1: Create headers array if not provided
  const defaultHeaders = headers || ['Column 1', 'Column 2', 'Column 3'];

  // LD1: Generate mock rows based on headers and rowCount
  const rows = Array.from({ length: rowCount }, () =>
    defaultHeaders.map((header, index) => `Value ${index + 1}`)
  );

  // LD1: Return object with headers and rows
  return { headers: defaultHeaders, rows };
};

/**
 * Creates a mock library object for testing
 * @param overrides - Optional overrides for the default library properties
 * @returns Mock library with default values and overrides
 */
export const createMockLibrary = (overrides?: any) => {
    // LD1: Create default library object with required properties
    const defaultLibrary = {
      id: 'mock-library-id',
      name: 'Mock Library',
      description: 'This is a mock library for testing',
      owner_id: 'mock-user-id',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      molecule_count: 0
    };
  
    // LD1: Apply overrides to default library
    const mergedLibrary = { ...defaultLibrary, ...overrides };
  
    // LD1: Return merged library object
    return mergedLibrary;
  };
  
  /**
   * Creates a mock submission object for testing
   * @param overrides - Optional overrides for the default submission properties
   * @returns Mock submission with default values and overrides
   */
  export const createMockSubmission = (overrides?: any) => {
    // LD1: Create default submission object with required properties
    const defaultSubmission = {
      id: 'mock-submission-id',
      name: 'Mock Submission',
      cro_service_id: 'mock-cro-service-id',
      description: 'This is a mock submission for testing',
      specifications: {},
      status: 'DRAFT',
      metadata: {},
      created_by: 'mock-user-id',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      submitted_at: null,
      approved_at: null,
      completed_at: null,
      price: null,
      price_currency: null,
      estimated_turnaround_days: null,
      estimated_completion_date: null,
      cro_service: null,
      creator: null,
      molecules: null,
      documents: null,
      results: null,
      status_description: null,
      document_count: null,
      molecule_count: null,
      is_editable: true,
      is_active: true
    };
  
    // LD1: Apply overrides to default submission
    const mergedSubmission = { ...defaultSubmission, ...overrides };
  
    // LD1: Return merged submission object
    return mergedSubmission;
  };
  
  /**
   * Creates a mock user object for testing
   * @param overrides - Optional overrides for the default user properties
   * @returns Mock user with default values and overrides
   */
  export const createMockUser = (overrides?: any) => {
    // LD1: Create default user object with required properties
    const defaultUser = {
      id: 'mock-user-id',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'pharma_scientist',
      is_active: true,
      is_superuser: false,
      organization_name: 'Test Org',
      organization_id: 'mock-org-id',
      last_login: new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
  
    // LD1: Apply overrides to default user
    const mergedUser = { ...defaultUser, ...overrides };
  
    // LD1: Return merged user object
    return mergedUser;
  };
  
  /**
   * Creates a mock prediction object for testing
   * @param overrides - Optional overrides for the default prediction properties
   * @returns Mock prediction with default values and overrides
   */
  export const createMockPrediction = (overrides?: any) => {
    // LD1: Create default prediction object with required properties
    const defaultPrediction = {
      property_name: 'logP',
      value: 2.5,
      confidence: 0.95,
      units: 'log units'
    };
  
    // LD1: Apply overrides to default prediction
    const mergedPrediction = { ...defaultPrediction, ...overrides };
  
    // LD1: Return merged prediction object
    return mergedPrediction;
  };
  
  /**
   * Creates a mock result object for testing
   * @param overrides - Optional overrides for the default result properties
   * @returns Mock result with default values and overrides
   */
  export const createMockResult = (overrides?: any) => {
    // LD1: Create default result object with required properties
    const defaultResult = {
      id: 'mock-result-id',
      submission_id: 'mock-submission-id',
      status: 'complete',
      uploaded_at: new Date().toISOString(),
      uploaded_by: 'mock-user-id'
    };
  
    // LD1: Apply overrides to default result
    const mergedResult = { ...defaultResult, ...overrides };
  
    // LD1: Return merged result object
    return mergedResult;
  };

/**
 * Runs accessibility tests on a rendered component
 * @param container - HTMLElement to test
 * @param options - Optional configuration for axe
 * @returns Promise that resolves when tests complete
 */
export const axeTest = async (container: HTMLElement, options?: any): Promise<void> => {
  // LD1: Run axe accessibility tests on the container
  const results = await axe(container, options);

  // LD1: Assert that there are no accessibility violations
  expect(results).toHaveNoViolations();

  // LD1: Log detailed violation information if tests fail
  if (results.violations.length > 0) {
    console.log('Accessibility Violations:', results.violations);
  }
};