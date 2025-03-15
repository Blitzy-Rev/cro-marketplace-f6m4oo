// Import testing libraries
import '@testing-library/jest-dom'; // v6.0.0
import { enableFetchMocks } from 'jest-fetch-mock'; // v3.0.3
import 'jest-canvas-mock'; // v2.5.0
import { configureAxe, toHaveNoViolations } from 'jest-axe'; // v7.0.1

// Setup function for Jest DOM extensions
function setupJestDom(): void {
  // @testing-library/jest-dom is automatically extended via the import
}

// Setup function for fetch mocking
function setupFetchMock(): void {
  // Enable fetch mocks globally
  enableFetchMocks();
  
  // Default fetch mock behavior
  fetchMock.doMock();
  
  // Reset fetch mocks after each test
  afterEach(() => {
    fetchMock.resetMocks();
  });
}

// Setup function for canvas mocking (needed for molecular visualization)
function setupCanvasMock(): void {
  // jest-canvas-mock is automatically configured via the import
  
  // Additional canvas configuration for ChemDoodle if needed
  // This is handled by jest-canvas-mock but can be extended here
}

// Setup function for browser API mocks
function setupBrowserMocks(): void {
  // Mock ResizeObserver
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
  
  // Mock MutationObserver
  global.MutationObserver = class MutationObserver {
    observe() {}
    disconnect() {}
  };
  
  // Mock matchMedia for responsive design testing
  global.matchMedia = jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn()
  }));
  
  // Mock ChemDoodle for molecular visualization testing
  global.ChemDoodle = {
    structures: {},
    io: {},
    informatics: {},
    RESIDUE: {},
    lib: {},
    iChemLabs: {}
  };
}

// Setup function for accessibility testing
function setupAccessibilityTesting(): void {
  // Configure axe for accessibility testing
  const axe = configureAxe({
    rules: {
      // Add specific rule configurations here if needed
    }
  });
  
  // Extend Jest matchers with the accessibility matcher
  expect.extend(toHaveNoViolations);
  
  // Add axe to global for use in tests
  global.axe = axe;
}

// Run all setup functions before any tests
beforeAll(() => {
  setupJestDom();
  setupFetchMock();
  setupCanvasMock();
  setupBrowserMocks();
  setupAccessibilityTesting();
});

// Additional type declarations to avoid TypeScript errors
declare global {
  var axe: ReturnType<typeof configureAxe>;
  var ChemDoodle: {
    structures: any;
    io: any;
    informatics: any;
    RESIDUE: any;
    lib: any;
    iChemLabs: any;
  };
  var ResizeObserver: any;
  var MutationObserver: any;
  var matchMedia: any;
}