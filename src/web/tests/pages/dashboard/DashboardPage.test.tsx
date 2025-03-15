import React from 'react'; // React library for component testing
import { screen, waitFor, fireEvent } from '@testing-library/react'; // Testing utilities for React components
import { act } from 'react-dom/test-utils'; // Test utility for wrapping state updates
import { vi } from 'vitest'; // Mocking functionality for tests

import DashboardPage from '../../src/pages/dashboard/DashboardPage'; // Component under test
import { renderWithProviders, createMockMoleculeArray, createMockLibrary, createMockSubmission } from '../../src/utils/testHelpers'; // Helper function to render components with Redux and other providers
import { USER_ROLES } from '../../src/constants/userRoles'; // Constants for user role types
import { ROUTES } from '../../src/constants/routes'; // Route definitions for navigation testing
import { SubmissionStatus } from '../../src/constants/submissionStatus'; // Enum for submission status values

/**
 * Creates a mock authentication context for testing
 * @param role - User role to assign to the mock user
 * @returns Mock auth context with specified user role
 */
const mockAuthContext = (role: string) => ({
  authState: {
    isAuthenticated: true,
    user: {
      id: 'test-user-id',
      email: 'test@example.com',
      full_name: 'Test User',
      role: role,
      is_active: true,
      is_superuser: false,
      organization_name: 'Test Org',
      organization_id: 'test-org-id',
      last_login: new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    token: {
      access_token: 'test-token',
      refresh_token: 'test-refresh-token',
      token_type: 'Bearer',
      expires_in: 3600
    },
    loading: false,
    error: null,
    mfaRequired: false,
    mfaToken: null
  },
  login: vi.fn(),
  logout: vi.fn(),
  register: vi.fn(),
  resetPassword: vi.fn(),
  confirmPasswordReset: vi.fn(),
  verifyMFA: vi.fn()
});

/**
 * Creates a mock Redux state for testing the dashboard
 * @param userRole - User role to simulate (pharma or CRO)
 * @returns Preloaded state for Redux store
 */
const mockReduxState = (userRole: string) => {
  // Create mock molecules array using createMockMoleculeArray
  const molecules = createMockMoleculeArray(10);

  // Create mock libraries array with createMockLibrary
  const libraries = [
    createMockLibrary({ id: 'lib1', name: 'Library 1' }),
    createMockLibrary({ id: 'lib2', name: 'Library 2' })
  ];

  // Create mock submissions with different statuses using createMockSubmission
  const submissions = [
    createMockSubmission({ id: 'sub1', status: SubmissionStatus.SUBMITTED }),
    createMockSubmission({ id: 'sub2', status: SubmissionStatus.IN_PROGRESS }),
    createMockSubmission({ id: 'sub3', status: SubmissionStatus.RESULTS_UPLOADED }),
    createMockSubmission({ id: 'sub4', status: SubmissionStatus.COMPLETED }),
    createMockSubmission({ id: 'sub5', status: SubmissionStatus.REJECTED })
  ];

  // Create mock status counts for submissions
  const statusCounts = [
    { status: SubmissionStatus.SUBMITTED, count: 1 },
    { status: SubmissionStatus.IN_PROGRESS, count: 1 },
    { status: SubmissionStatus.RESULTS_UPLOADED, count: 1 },
    { status: SubmissionStatus.COMPLETED, count: 1 },
    { status: SubmissionStatus.REJECTED, count: 1 }
  ];

  // Return a complete preloaded state object with all required slices
  return {
    auth: mockAuthContext(userRole).authState,
    molecule: {
      molecules: molecules,
      currentMolecule: null,
      selectedMolecules: [],
      loading: false,
      error: null,
      filter: null,
      pagination: {
        page: 1,
        pageSize: 25,
        total: 10,
        totalPages: 1
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
    },
    libraries: {
      libraries: libraries,
      currentLibrary: null,
      loading: false,
      error: null,
      totalCount: 2,
      currentPage: 1,
      pageSize: 25,
      totalPages: 1
    },
    submission: {
      submissions: submissions,
      selectedSubmission: null,
      documentRequirements: null,
      loading: false,
      error: null,
      totalCount: 5,
      currentPage: 1,
      pageSize: 25,
      totalPages: 1,
      filters: {
        name_contains: null,
        status: null,
        cro_service_id: null,
        active_only: true,
        created_by: null,
        molecule_id: null,
        created_after: null,
        created_before: null
      },
      statusCounts: statusCounts
    }
  };
};

/**
 * Sets up mocks for API calls and navigation
 */
const setupMocks = () => {
  // Mock useNavigate to return a jest function
  const mockNavigate = vi.fn();
  vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom');
    return {
      ...actual,
      useNavigate: () => mockNavigate,
    };
  });

  // Mock API functions used in the dashboard component
  const mockFetchMolecules = vi.fn();
  const mockFetchMyLibraries = vi.fn();
  const mockFetchSubmissions = vi.fn();
  const mockFetchStatusCounts = vi.fn();
  vi.mock('../../src/features/molecule/moleculeSlice', () => ({
    fetchMolecules: () => mockFetchMolecules,
  }));
  vi.mock('../../src/features/library/librarySlice', () => ({
    fetchMyLibraries: () => mockFetchMyLibraries,
  }));
  vi.mock('../../src/features/submission/submissionSlice', () => ({
    fetchSubmissions: () => mockFetchSubmissions,
    fetchStatusCounts: () => mockFetchStatusCounts,
  }));

  // Set up mock implementations for Redux thunks
  mockFetchMolecules.mockImplementation(() => Promise.resolve({ items: [], total: 0, page: 1, pageSize: 25, totalPages: 0 }));
  mockFetchMyLibraries.mockImplementation(() => Promise.resolve({ items: [], total: 0, page: 1, pageSize: 25, totalPages: 0 }));
  mockFetchSubmissions.mockImplementation(() => Promise.resolve({ items: [], total: 0, page: 1, pageSize: 25, totalPages: 0 }));
  mockFetchStatusCounts.mockImplementation(() => Promise.resolve([]));

  return { mockNavigate, mockFetchMolecules, mockFetchMyLibraries, mockFetchSubmissions, mockFetchStatusCounts };
};

describe('DashboardPage', () => {
  describe('renders pharma user dashboard correctly', () => {
    it('Tests that the pharma user dashboard renders with correct metrics and sections', async () => {
      // Set up mocks for API calls and navigation
      const { mockNavigate } = setupMocks();

      // Create mock Redux state for pharma user
      const preloadedState = mockReduxState(USER_ROLES.PHARMA_USER);

      // Render DashboardPage with providers and preloaded state
      renderWithProviders(<DashboardPage />, { preloadedState });

      // Verify dashboard title is displayed
      expect(screen.getByText('Dashboard')).toBeInTheDocument();

      // Verify metric cards are displayed with correct values
      expect(screen.getByText('Active Molecules')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('Libraries')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('Pending Submissions')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();

      // Verify recent activity section is displayed
      expect(screen.getByText('Recent Activity')).toBeInTheDocument();

      // Verify quick actions section is displayed with pharma-specific buttons
      expect(screen.getByText('Quick Actions')).toBeInTheDocument();
      expect(screen.getByText('Upload Molecules')).toBeInTheDocument();
      expect(screen.getByText('Create Library')).toBeInTheDocument();
      expect(screen.getByText('Submit to CRO')).toBeInTheDocument();
    });
  });

  describe('renders CRO user dashboard correctly', () => {
    it('Tests that the CRO user dashboard renders with correct metrics and sections', async () => {
      // Set up mocks for API calls and navigation
      const { mockNavigate } = setupMocks();

      // Create mock Redux state for CRO user
      const preloadedState = mockReduxState(USER_ROLES.CRO_USER);

      // Render DashboardPage with providers and preloaded state
      renderWithProviders(<DashboardPage />, { preloadedState });

      // Verify dashboard title is displayed
      expect(screen.getByText('Dashboard')).toBeInTheDocument();

      // Verify CRO-specific metric cards are displayed with correct values
      expect(screen.getByText('New Submissions')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('Active Projects')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('Pending Results')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('Completed This Month')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();

      // Verify new submissions table is displayed
      expect(screen.getByText('New Submissions')).toBeInTheDocument();

      // Verify pending results table is displayed
      expect(screen.getByText('Pending Results')).toBeInTheDocument();

      // Verify quick actions section is displayed with CRO-specific buttons
      expect(screen.getByText('Quick Actions')).toBeInTheDocument();
      expect(screen.getByText('Upload Results')).toBeInTheDocument();
    });
  });

  describe('fetches dashboard data on mount', () => {
    it('Tests that the component fetches required data when mounted', async () => {
      // Set up mocks for API calls and navigation
      const { mockFetchMolecules, mockFetchMyLibraries, mockFetchSubmissions, mockFetchStatusCounts } = setupMocks();

      // Create mock Redux state
      const preloadedState = mockReduxState(USER_ROLES.PHARMA_USER);

      // Render DashboardPage with providers and preloaded state
      renderWithProviders(<DashboardPage />, { preloadedState });

      // Verify that fetch functions were called
      expect(mockFetchMolecules).toHaveBeenCalled();
      expect(mockFetchMyLibraries).toHaveBeenCalled();
      expect(mockFetchSubmissions).toHaveBeenCalled();
      expect(mockFetchStatusCounts).toHaveBeenCalled();

      // Verify that fetchMolecules was called with correct parameters
      expect(mockFetchMolecules).toHaveBeenCalledWith({ page: 1, pageSize: 5 });

      // Verify that fetchMyLibraries was called
      expect(mockFetchMyLibraries).toHaveBeenCalledWith({ page: 1, pageSize: 5 });

      // Verify that fetchSubmissions was called with correct parameters
      expect(mockFetchSubmissions).toHaveBeenCalledWith({ page: 1, pageSize: 5, filter: { active_only: true } });

      // Verify that fetchStatusCounts was called
      expect(mockFetchStatusCounts).toHaveBeenCalledWith({});
    });
  });

  describe('navigates to correct routes when quick action buttons are clicked', () => {
    it('Tests that clicking quick action buttons navigates to the correct routes', async () => {
      // Set up mocks for API calls and navigation
      const { mockNavigate } = setupMocks();

      // Create mock Redux state for pharma user
      const preloadedState = mockReduxState(USER_ROLES.PHARMA_USER);

      // Render DashboardPage with providers and preloaded state
      renderWithProviders(<DashboardPage />, { preloadedState });

      // Find and click 'Upload Molecules' button
      const uploadButton = screen.getByText('Upload Molecules');
      await act(() => {
        fireEvent.click(uploadButton);
      });

      // Verify navigation was called with MOLECULE_UPLOAD route
      expect(mockNavigate).toHaveBeenCalledWith(ROUTES.MOLECULE_UPLOAD);

      // Find and click 'Create Library' button
      const createLibraryButton = screen.getByText('Create Library');
      await act(() => {
        fireEvent.click(createLibraryButton);
      });

      // Verify navigation was called with LIBRARY_CREATE route
      expect(mockNavigate).toHaveBeenCalledWith(ROUTES.LIBRARY_CREATE);

      // Find and click 'Submit to CRO' button
      const submitToCROButton = screen.getByText('Submit to CRO');
      await act(() => {
        fireEvent.click(submitToCROButton);
      });

      // Verify navigation was called with SUBMISSION_CREATE route
      expect(mockNavigate).toHaveBeenCalledWith(ROUTES.SUBMISSION_CREATE);
    });
  });

  describe('displays loading state while fetching data', () => {
    it('Tests that loading indicators are displayed while data is being fetched', async () => {
      // Set up mocks for API calls with delayed responses
      const { mockFetchMolecules, mockFetchMyLibraries, mockFetchSubmissions, mockFetchStatusCounts } = setupMocks();
      mockFetchMolecules.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ items: [], total: 0, page: 1, pageSize: 25, totalPages: 0 }), 500)));
      mockFetchMyLibraries.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ items: [], total: 0, page: 1, pageSize: 25, totalPages: 0 }), 500)));
      mockFetchSubmissions.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ items: [], total: 0, page: 1, pageSize: 25, totalPages: 0 }), 500)));
      mockFetchStatusCounts.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve([]), 500)));

      // Create mock Redux state with loading=true
      const preloadedState = {
        ...mockReduxState(USER_ROLES.PHARMA_USER),
        molecule: {
          ...mockReduxState(USER_ROLES.PHARMA_USER).molecule,
          loading: true
        }
      };

      // Render DashboardPage with providers and preloaded state
      renderWithProviders(<DashboardPage />, { preloadedState });

      // Verify loading indicators are displayed in metric cards
      expect(screen.getByRole('progressbar', { name: 'circular-progress' })).toBeVisible();

      // Verify loading indicator is displayed in recent activity section
      expect(screen.getByRole('progressbar', { name: 'circular-progress' })).toBeVisible();

      // Update Redux state to loading=false
      const updatedPreloadedState = mockReduxState(USER_ROLES.PHARMA_USER);
      renderWithProviders(<DashboardPage />, { preloadedState: updatedPreloadedState });

      // Verify loading indicators are replaced with actual content
      expect(screen.getByText('Active Molecules')).toBeInTheDocument();
      expect(screen.getByText('Libraries')).toBeInTheDocument();
      expect(screen.getByText('Pending Submissions')).toBeInTheDocument();
      expect(screen.getByText('Recent Activity')).toBeInTheDocument();
    });
  });

  describe('handles empty data states correctly', () => {
    it('Tests that the dashboard handles cases with no data gracefully', async () => {
      // Set up mocks for API calls
      const { mockFetchMolecules, mockFetchMyLibraries, mockFetchSubmissions, mockFetchStatusCounts } = setupMocks();
      mockFetchMolecules.mockImplementation(() => Promise.resolve({ items: [], total: 0, page: 1, pageSize: 25, totalPages: 0 }));
      mockFetchMyLibraries.mockImplementation(() => Promise.resolve({ items: [], total: 0, page: 1, pageSize: 25, totalPages: 0 }));
      mockFetchSubmissions.mockImplementation(() => Promise.resolve({ items: [], total: 0, page: 1, pageSize: 25, totalPages: 0 }));
      mockFetchStatusCounts.mockImplementation(() => Promise.resolve([]));

      // Create mock Redux state with empty arrays for molecules, libraries, and submissions
      const preloadedState = {
        ...mockReduxState(USER_ROLES.PHARMA_USER),
        molecule: {
          ...mockReduxState(USER_ROLES.PHARMA_USER).molecule,
          molecules: []
        },
        libraries: {
          ...mockReduxState(USER_ROLES.PHARMA_USER).libraries,
          libraries: []
        },
        submission: {
          ...mockReduxState(USER_ROLES.PHARMA_USER).submission,
          submissions: [],
          statusCounts: []
        }
      };

      // Render DashboardPage with providers and preloaded state
      renderWithProviders(<DashboardPage />, { preloadedState });

      // Verify metric cards show zero values
      expect(screen.getByText('0')).toBeVisible();

      // Verify empty state messages are displayed in appropriate sections
      expect(screen.getByText('No recent activity')).toBeInTheDocument();

      // Verify quick action buttons are still accessible
      expect(screen.getByText('Upload Molecules')).toBeInTheDocument();
      expect(screen.getByText('Create Library')).toBeInTheDocument();
      expect(screen.getByText('Submit to CRO')).toBeInTheDocument();
    });
  });
});