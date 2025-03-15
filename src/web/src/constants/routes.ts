/**
 * Application Routes
 * 
 * This file defines all application route paths as constants for the Molecular Data Management and CRO Integration Platform.
 * It centralizes route definitions to ensure consistency across the application and prevent hardcoded paths.
 */

// Root path
export const ROOT = '/';

// Authentication routes
export const AUTH = {
  ROOT: '/auth',
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  PASSWORD_RESET: '/auth/password-reset'
};

// Dashboard routes
export const DASHBOARD = {
  ROOT: '/dashboard',
  HOME: '/dashboard'
};

// Molecule management routes
export const MOLECULES = {
  ROOT: '/molecules',
  LIST: '/molecules',
  UPLOAD: '/molecules/upload',
  DETAIL: '/molecules/:id',
  COMPARISON: '/molecules/compare'
};

// Library management routes
export const LIBRARIES = {
  ROOT: '/libraries',
  LIST: '/libraries',
  DETAIL: '/libraries/:id',
  CREATE: '/libraries/create'
};

// CRO submission routes
export const SUBMISSIONS = {
  ROOT: '/submissions',
  LIST: '/submissions',
  CREATE: '/submissions/create',
  DETAIL: '/submissions/:id'
};

// Experimental results routes
export const RESULTS = {
  ROOT: '/results',
  LIST: '/results',
  UPLOAD: '/results/upload',
  DETAIL: '/results/:id'
};

// CRO-specific routes
export const CRO = {
  ROOT: '/cro',
  DASHBOARD: '/cro/dashboard',
  LIST: '/cro/list',
  DETAIL: '/cro/:id'
};

// User profile and settings routes
export const USER = {
  PROFILE: '/user/profile',
  SETTINGS: '/user/settings'
};

// Error page routes
export const ERROR = {
  NOT_FOUND: '/404',
  SERVER_ERROR: '/500',
  ACCESS_DENIED: '/403'
};

// Combined export of all route constants
export const ROUTES = {
  ROOT,
  AUTH,
  DASHBOARD,
  MOLECULES,
  LIBRARIES,
  SUBMISSIONS,
  RESULTS,
  CRO,
  USER,
  ERROR
};

/**
 * Generates a concrete path by replacing route parameters with actual values
 * 
 * @param path - Path with parameters (e.g., '/molecules/:id')
 * @param params - Object containing parameter values to replace
 * @returns The path with parameters replaced by actual values
 */
export const generatePath = (path: string, params: Record<string, string | number>): string => {
  let result = path;
  
  // Replace each parameter (prefixed with ':') with the corresponding value from params object
  Object.entries(params).forEach(([key, value]) => {
    result = result.replace(`:${key}`, String(value));
  });
  
  return result;
};

/**
 * Generates a path to a specific molecule detail page
 * 
 * @param id - Molecule ID
 * @returns The path to the molecule detail page
 */
export const getMoleculeDetailPath = (id: string | number): string => {
  return generatePath(MOLECULES.DETAIL, { id });
};

/**
 * Generates a path to a specific library detail page
 * 
 * @param id - Library ID
 * @returns The path to the library detail page
 */
export const getLibraryDetailPath = (id: string | number): string => {
  return generatePath(LIBRARIES.DETAIL, { id });
};

/**
 * Generates a path to a specific submission detail page
 * 
 * @param id - Submission ID
 * @returns The path to the submission detail page
 */
export const getSubmissionDetailPath = (id: string | number): string => {
  return generatePath(SUBMISSIONS.DETAIL, { id });
};

/**
 * Generates a path to a specific result detail page
 * 
 * @param id - Result ID
 * @returns The path to the result detail page
 */
export const getResultDetailPath = (id: string | number): string => {
  return generatePath(RESULTS.DETAIL, { id });
};

/**
 * Generates a path to a specific CRO detail page
 * 
 * @param id - CRO ID
 * @returns The path to the CRO detail page
 */
export const getCroDetailPath = (id: string | number): string => {
  return generatePath(CRO.DETAIL, { id });
};