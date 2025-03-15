import type { Config } from 'jest'; // jest v29.5.0

const config: Config = {
  // Use ts-jest preset for TypeScript support
  preset: 'ts-jest',
  
  // Use jsdom for browser environment simulation
  testEnvironment: 'jsdom',
  
  // Setup files to run after Jest is initialized
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  
  // Module name mapping for imports
  moduleNameMapper: {
    // Map @ path alias to src directory
    '^@/(.*)$': '<rootDir>/src/$1',
    
    // Mock CSS/SCSS imports
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    
    // Mock image imports
    '\\.(jpg|jpeg|png|gif|webp|svg)$': '<rootDir>/tests/__mocks__/fileMock.ts',
    
    // Mock ChemDoodle Web for molecular visualization
    '^chemdoodle-web$': '<rootDir>/tests/__mocks__/chemdoodleMock.ts'
  },
  
  // Transform settings for TypeScript
  transform: {
    '^.+\\.tsx?$': ['ts-jest', { tsconfig: 'tsconfig.json' }]
  },
  
  // Test file pattern matching
  testRegex: '(/__tests__/.*|(\\.|/)(test|spec))\\.(jsx?|tsx?)$',
  
  // File extensions to consider
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  
  // Files to collect coverage from
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/types/**/*',
    '!src/index.tsx',
    '!src/react-app-env.d.ts',
    '!src/reportWebVitals.ts',
    '!src/setupTests.ts'
  ],
  
  // Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 75,
      functions: 85,
      lines: 80,
      statements: 80
    },
    // Higher thresholds for critical paths
    './src/components/molecule/': {
      branches: 90,
      functions: 95,
      lines: 95,
      statements: 95
    },
    './src/components/submission/': {
      branches: 90,
      functions: 95,
      lines: 95,
      statements: 95
    }
  },
  
  // Coverage report formats
  coverageReporters: ['text', 'lcov', 'html'],
  
  // Watch plugins for interactive mode
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname'
  ],
  
  // Global settings for ts-jest
  globals: {
    'ts-jest': {
      tsconfig: 'tsconfig.json',
      isolatedModules: true
    }
  },
  
  // Test timeout in milliseconds
  testTimeout: 10000,
  
  // Mock behavior
  clearMocks: true,
  restoreMocks: true,
  resetMocks: true
};

export default config;