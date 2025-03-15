/**
 * Global setup file for Jest tests in the web frontend of the 
 * Molecular Data Management and CRO Integration Platform.
 * 
 * This configures the testing environment, sets up mocks for browser APIs,
 * and extends Jest with custom matchers for testing React components with
 * molecular visualization and API interactions.
 */

// Import required testing libraries
import '@testing-library/jest-dom'; // v6.0.0
import 'jest-canvas-mock'; // v2.5.0
import { enableFetchMocks } from 'jest-fetch-mock'; // v3.0.3
import { configureAxe, toHaveNoViolations } from 'jest-axe'; // v7.0.1
// jest-environment-jsdom v29.5.0 is configured in jest.config.js

// Extend the global object type for TypeScript
declare global {
  // Mocks for browser APIs
  var ResizeObserver: { new(): { observe: () => void; unobserve: () => void; disconnect: () => void } };
  var MutationObserver: { new(callback: Function): { observe: () => void; disconnect: () => void } };
  var matchMedia: (query: string) => {
    matches: boolean;
    media: string;
    onchange: null;
    addListener: jest.Mock;
    removeListener: jest.Mock;
    addEventListener: jest.Mock;
    removeEventListener: jest.Mock;
    dispatchEvent: jest.Mock;
  };
  
  // ChemDoodle and WebGL mocks for molecular visualization
  var ChemDoodle: {
    structures: Record<string, any>;
    io: Record<string, any>;
    informatics: Record<string, any>;
    RESIDUE: Record<string, any>;
    lib: Record<string, any>;
    iChemLabs: Record<string, any>;
  };
  var WebGLRenderingContext: any;
  
  // Utility mocks for molecular testing
  var mockSMILESParsing: (smiles: string) => {
    valid: boolean;
    structure: { atoms: any[]; bonds: any[] };
  };
  var mockPropertyCalculation: (property: string, value: number) => {
    property: string;
    value: number;
    unit: string;
    confidence: number;
  };
  
  // Accessibility testing utilities
  var axe: any;
}

/**
 * Extends Jest with DOM testing utilities from @testing-library/jest-dom
 * These utilities provide custom matchers for asserting on DOM elements
 */
const setupJestDom = (): void => {
  // @testing-library/jest-dom extends Jest's expect automatically
  // No additional setup needed as the import above handles it
};

/**
 * Configures fetch mock for API testing
 * Important for mocking API calls to backend services and CRO integrations
 */
const setupFetchMock = (): void => {
  // Enable fetch mocks globally
  enableFetchMocks();
  
  // Configure default fetch mock behavior
  // This will be the default response unless overridden in specific tests
  fetchMock.doMock();
  fetchMock.mockResponse(JSON.stringify({ data: 'mock data' }));
};

/**
 * Sets up canvas mock for molecular visualization testing
 * Critical for testing ChemDoodle Web Components and other visualization tools
 */
const setupCanvasMock = (): void => {
  // jest-canvas-mock is set up via import
  // This is essential for molecular structure rendering which uses Canvas/WebGL
  
  // Additional configuration for specific ChemDoodle canvas requirements
  // can be added here if the default mock doesn't cover all use cases
};

/**
 * Sets up mocks for browser APIs not available in Jest environment
 * These mocks are needed for UI components that rely on modern browser APIs
 */
const setupBrowserMocks = (): void => {
  // Mock ResizeObserver - needed for responsive components and molecule viewers
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };

  // Mock MutationObserver - used by ChemDoodle Web and other dynamic components
  global.MutationObserver = class MutationObserver {
    constructor(callback: Function) {
      this.callback = callback;
    }
    private callback: Function;
    observe() {}
    disconnect() {}
  };

  // Mock matchMedia - required for responsive design testing
  global.matchMedia = jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  }));

  // Mock ChemDoodle for molecular visualization
  // This is a placeholder for the global ChemDoodle object that would be available in browser
  global.ChemDoodle = {
    structures: {},
    io: {},
    informatics: {},
    RESIDUE: {},
    lib: {},
    iChemLabs: {}
  };

  // Mock WebGL context for 3D molecule rendering
  global.WebGLRenderingContext = {};
};

/**
 * Configures accessibility testing with jest-axe
 * This allows for automated a11y testing of React components
 */
const setupAccessibilityTesting = (): void => {
  // Configure axe with platform-specific rules
  const axe = configureAxe({
    rules: {
      // Rules for pharmaceutical application accessibility
      // Ensuring sufficient color contrast for molecule visualization
      'color-contrast': { enabled: true },
      // Ensuring molecule information is accessible to screen readers
      'aria-required-children': { enabled: true },
      'aria-required-parent': { enabled: true }
    }
  });
  
  // Extend Jest's expect with the toHaveNoViolations matcher
  expect.extend(toHaveNoViolations);
  
  // Add to global for easy access in tests
  global.axe = axe;
};

/**
 * Sets up utilities specific to molecule testing
 * These helpers simulate molecular property calculations and structure parsing
 */
const setupMoleculeTestUtils = (): void => {
  // Mock SMILES parsing functionality
  // SMILES (Simplified Molecular Input Line Entry System) is a string notation for molecular structures
  global.mockSMILESParsing = (smiles: string) => ({
    valid: smiles && smiles.length > 0, // Basic validation
    structure: { 
      atoms: [], 
      bonds: [] 
    }
  });
  
  // Mock molecular property calculation
  // This simulates the calculation of properties like molecular weight, LogP, etc.
  global.mockPropertyCalculation = (property: string, value: number) => ({
    property,
    value,
    unit: property === 'molecularWeight' ? 'g/mol' : 
          property === 'logP' ? '' :
          property === 'solubility' ? 'mg/mL' :
          property === 'meltingPoint' ? 'K' : '',
    confidence: 0.95
  });
};

// Initialize all mocks and testing environment before any tests run
beforeAll(() => {
  setupJestDom();
  setupFetchMock();
  setupCanvasMock();
  setupBrowserMocks();
  setupAccessibilityTesting();
  setupMoleculeTestUtils();
});

// Reset mocks and test state after each test
afterEach(() => {
  jest.clearAllMocks();
  fetchMock.resetMocks();
});

// Clean up any resources used during testing
afterAll(() => {
  // Any necessary cleanup would go here
  // Most mocks are automatically cleaned up by the Jest environment
});