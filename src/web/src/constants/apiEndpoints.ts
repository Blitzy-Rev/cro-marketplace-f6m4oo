/**
 * apiEndpoints.ts
 * 
 * Defines all API endpoint URLs used throughout the Molecular Data Management and CRO Integration Platform frontend.
 * This file centralizes endpoint definitions to ensure consistency across API calls and simplify updates when API routes change.
 */

// Import API configuration from app config
import { APP_CONFIG } from './appConfig';

// Base URL for API requests
const BASE_URL = APP_CONFIG.api.baseUrl;

/**
 * API endpoints organized by domain
 */
export const API_ENDPOINTS = {
  /**
   * Authentication-related endpoints
   */
  AUTH: {
    LOGIN: `${BASE_URL}/api/v1/auth/login`,
    LOGOUT: `${BASE_URL}/api/v1/auth/logout`,
    REFRESH_TOKEN: `${BASE_URL}/api/v1/auth/refresh`,
    PASSWORD_RESET_REQUEST: `${BASE_URL}/api/v1/auth/password-reset/request`,
    PASSWORD_RESET: `${BASE_URL}/api/v1/auth/password-reset/confirm`,
    VERIFY_MFA: `${BASE_URL}/api/v1/auth/mfa/verify`,
  },

  /**
   * User management endpoints
   */
  USERS: {
    LIST: `${BASE_URL}/api/v1/users`,
    CREATE: `${BASE_URL}/api/v1/users`,
    GET: `${BASE_URL}/api/v1/users/{id}`,
    UPDATE: `${BASE_URL}/api/v1/users/{id}`,
    DELETE: `${BASE_URL}/api/v1/users/{id}`,
    ME: `${BASE_URL}/api/v1/users/me`,
    UPDATE_PROFILE: `${BASE_URL}/api/v1/users/me`,
    CHANGE_PASSWORD: `${BASE_URL}/api/v1/users/me/password`,
  },

  /**
   * Molecule management endpoints
   */
  MOLECULES: {
    LIST: `${BASE_URL}/api/v1/molecules`,
    CREATE: `${BASE_URL}/api/v1/molecules`,
    GET: `${BASE_URL}/api/v1/molecules/{id}`,
    UPDATE: `${BASE_URL}/api/v1/molecules/{id}`,
    DELETE: `${BASE_URL}/api/v1/molecules/{id}`,
    FILTER: `${BASE_URL}/api/v1/molecules/filter`,
    SEARCH_SIMILARITY: `${BASE_URL}/api/v1/molecules/search/similarity`,
    SEARCH_SUBSTRUCTURE: `${BASE_URL}/api/v1/molecules/search/substructure`,
    UPLOAD_CSV: `${BASE_URL}/api/v1/molecules/upload/csv`,
    CSV_PREVIEW: `${BASE_URL}/api/v1/molecules/upload/csv/{storage_key}/preview`,
    IMPORT_CSV: `${BASE_URL}/api/v1/molecules/upload/csv/{storage_key}/import`,
    BATCH_CREATE: `${BASE_URL}/api/v1/molecules/batch`,
    ADD_TO_LIBRARY: `${BASE_URL}/api/v1/molecules/{molecule_id}/libraries/{library_id}`,
    REMOVE_FROM_LIBRARY: `${BASE_URL}/api/v1/molecules/{molecule_id}/libraries/{library_id}`,
    GET_BY_LIBRARY: `${BASE_URL}/api/v1/libraries/{library_id}/molecules`,
  },

  /**
   * Library management endpoints
   */
  LIBRARIES: {
    LIST: `${BASE_URL}/api/v1/libraries`,
    MY_LIBRARIES: `${BASE_URL}/api/v1/libraries/my`,
    CREATE: `${BASE_URL}/api/v1/libraries`,
    GET: `${BASE_URL}/api/v1/libraries/{id}`,
    UPDATE: `${BASE_URL}/api/v1/libraries/{id}`,
    DELETE: `${BASE_URL}/api/v1/libraries/{id}`,
    FILTER: `${BASE_URL}/api/v1/libraries/filter`,
    ADD_MOLECULE: `${BASE_URL}/api/v1/libraries/{library_id}/molecules/{molecule_id}`,
    REMOVE_MOLECULE: `${BASE_URL}/api/v1/libraries/{library_id}/molecules/{molecule_id}`,
    ADD_MOLECULES: `${BASE_URL}/api/v1/libraries/{library_id}/molecules/batch`,
    REMOVE_MOLECULES: `${BASE_URL}/api/v1/libraries/{library_id}/molecules/batch`,
    GET_MOLECULES: `${BASE_URL}/api/v1/libraries/{library_id}/molecules`,
    CHECK_ACCESS: `${BASE_URL}/api/v1/libraries/{library_id}/access`,
  },

  /**
   * AI prediction endpoints
   */
  PREDICTIONS: {
    REQUEST: `${BASE_URL}/api/v1/predictions`,
    STATUS: `${BASE_URL}/api/v1/predictions/{job_id}/status`,
    RESULTS: `${BASE_URL}/api/v1/predictions/{job_id}/results`,
    BY_MOLECULE: `${BASE_URL}/api/v1/molecules/{molecule_id}/predictions`,
    MODELS: `${BASE_URL}/api/v1/predictions/models`,
  },

  /**
   * CRO service endpoints
   */
  CRO: {
    LIST: `${BASE_URL}/api/v1/cro-services`,
    CREATE: `${BASE_URL}/api/v1/cro-services`,
    GET: `${BASE_URL}/api/v1/cro-services/{id}`,
    UPDATE: `${BASE_URL}/api/v1/cro-services/{id}`,
    DELETE: `${BASE_URL}/api/v1/cro-services/{id}`,
  },

  /**
   * CRO submission endpoints
   */
  SUBMISSIONS: {
    LIST: `${BASE_URL}/api/v1/submissions`,
    CREATE: `${BASE_URL}/api/v1/submissions`,
    GET: `${BASE_URL}/api/v1/submissions/{id}`,
    UPDATE: `${BASE_URL}/api/v1/submissions/{id}`,
    DOCUMENT_REQUIREMENTS: `${BASE_URL}/api/v1/submissions/{id}/document-requirements`,
    PERFORM_ACTION: `${BASE_URL}/api/v1/submissions/{id}/actions`,
    STATUS_COUNTS: `${BASE_URL}/api/v1/submissions/status-counts`,
    BY_MOLECULE: `${BASE_URL}/api/v1/molecules/{molecule_id}/submissions`,
  },

  /**
   * Document management endpoints
   */
  DOCUMENTS: {
    LIST: `${BASE_URL}/api/v1/documents`,
    UPLOAD: `${BASE_URL}/api/v1/documents/upload`,
    GET: `${BASE_URL}/api/v1/documents/{id}`,
    UPDATE: `${BASE_URL}/api/v1/documents/{id}`,
    DELETE: `${BASE_URL}/api/v1/documents/{id}`,
    DOWNLOAD: `${BASE_URL}/api/v1/documents/{id}/download`,
    BY_SUBMISSION: `${BASE_URL}/api/v1/submissions/{submission_id}/documents`,
    SIGNATURE_REQUEST: `${BASE_URL}/api/v1/documents/{id}/signature`,
    SIGNATURE_STATUS: `${BASE_URL}/api/v1/documents/{id}/signature/status`,
  },

  /**
   * Experimental results endpoints
   */
  RESULTS: {
    LIST: `${BASE_URL}/api/v1/results`,
    GET: `${BASE_URL}/api/v1/results/{id}`,
    UPDATE: `${BASE_URL}/api/v1/results/{id}`,
    DELETE: `${BASE_URL}/api/v1/results/{id}`,
    UPLOAD: `${BASE_URL}/api/v1/results/upload`,
    PROCESS: `${BASE_URL}/api/v1/results/upload/{storage_key}/process`,
    BY_MOLECULE: `${BASE_URL}/api/v1/molecules/{molecule_id}/results`,
    BY_SUBMISSION: `${BASE_URL}/api/v1/submissions/{submission_id}/results`,
    UPDATE_STATUS: `${BASE_URL}/api/v1/results/{id}/status`,
  },
};

export default API_ENDPOINTS;