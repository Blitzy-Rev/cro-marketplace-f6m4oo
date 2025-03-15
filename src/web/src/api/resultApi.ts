/**
 * API client for experimental results-related operations in the Molecular Data Management and CRO Integration Platform.
 * This file provides functions to interact with the backend results endpoints for retrieving, uploading,
 * processing, and managing experimental results from CROs.
 */

import { get, post, put, delete as deleteRequest, uploadFile } from './apiClient';
import { API_ENDPOINTS } from '../constants/apiEndpoints';
import {
  Result,
  ResultCreate,
  ResultUpdate,
  ResultFilter,
  ResultStatusUpdate,
  ResultCSVMapping,
  ResultCSVProcessResult,
  ResultProcessRequest,
  ResultReviewRequest,
  ResultResponse
} from '../types/result.types';

/**
 * Retrieves a paginated list of experimental results with optional filtering
 * @param filters - Filter parameters for results
 * @param page - Page number (1-based)
 * @param size - Number of items per page
 * @returns Promise resolving to paginated result data
 */
export async function getResults(
  filters: ResultFilter = {},
  page: number = 1,
  size: number = 25
): Promise<ResultResponse> {
  // Construct query parameters
  const queryParams = new URLSearchParams();
  queryParams.append('page', page.toString());
  queryParams.append('size', size.toString());
  
  // Add filters to query parameters
  if (filters.submission_id) {
    queryParams.append('submission_id', filters.submission_id);
  }
  
  if (filters.molecule_id) {
    queryParams.append('molecule_id', filters.molecule_id);
  }
  
  if (filters.status) {
    if (Array.isArray(filters.status)) {
      filters.status.forEach(status => queryParams.append('status', status));
    } else {
      queryParams.append('status', filters.status);
    }
  }
  
  if (filters.uploaded_by) {
    queryParams.append('uploaded_by', filters.uploaded_by);
  }
  
  if (filters.uploaded_after) {
    queryParams.append('uploaded_after', filters.uploaded_after);
  }
  
  if (filters.uploaded_before) {
    queryParams.append('uploaded_before', filters.uploaded_before);
  }
  
  // Make API request
  return get<ResultResponse>(`${API_ENDPOINTS.RESULTS.LIST}?${queryParams.toString()}`);
}

/**
 * Retrieves a single experimental result by ID
 * @param id - ID of the result to retrieve
 * @returns Promise resolving to result details
 */
export async function getResult(id: string): Promise<Result> {
  return get<Result>(API_ENDPOINTS.RESULTS.GET.replace('{id}', id));
}

/**
 * Updates an existing experimental result
 * @param id - ID of the result to update
 * @param result - Result data to update
 * @returns Promise resolving to updated result
 */
export async function updateResult(id: string, result: ResultUpdate): Promise<Result> {
  return put<Result>(API_ENDPOINTS.RESULTS.UPDATE.replace('{id}', id), result);
}

/**
 * Deletes an experimental result
 * @param id - ID of the result to delete
 * @returns Promise resolving when deletion is complete
 */
export async function deleteResult(id: string): Promise<void> {
  return deleteRequest<void>(API_ENDPOINTS.RESULTS.DELETE.replace('{id}', id));
}

/**
 * Uploads a results file (CSV) for processing
 * @param file - The CSV file to upload
 * @param submissionId - ID of the submission this result belongs to
 * @param additionalData - Additional metadata for the upload
 * @returns Promise resolving to storage key for the uploaded file
 */
export async function uploadResultFile(
  file: File,
  submissionId: string,
  additionalData: Record<string, any> = {}
): Promise<{ storage_key: string }> {
  // Create form data with additional fields
  const formData = {
    ...additionalData,
    submission_id: submissionId
  };
  
  // Upload the file
  return uploadFile<{ storage_key: string }>(
    API_ENDPOINTS.RESULTS.UPLOAD,
    file,
    formData
  );
}

/**
 * Processes an uploaded results file with column mapping
 * @param storageKey - Storage key for the previously uploaded file
 * @param mapping - Column mapping configuration
 * @returns Promise resolving to processing result
 */
export async function processResultFile(
  storageKey: string,
  mapping: ResultCSVMapping
): Promise<ResultCSVProcessResult> {
  return post<ResultCSVProcessResult>(
    API_ENDPOINTS.RESULTS.PROCESS.replace('{storage_key}', storageKey),
    mapping
  );
}

/**
 * Retrieves experimental results for a specific molecule
 * @param moleculeId - ID of the molecule
 * @param page - Page number (1-based)
 * @param size - Number of items per page
 * @returns Promise resolving to paginated result data
 */
export async function getResultsByMolecule(
  moleculeId: string,
  page: number = 1,
  size: number = 25
): Promise<ResultResponse> {
  const queryParams = new URLSearchParams();
  queryParams.append('page', page.toString());
  queryParams.append('size', size.toString());
  
  return get<ResultResponse>(
    `${API_ENDPOINTS.RESULTS.BY_MOLECULE.replace('{molecule_id}', moleculeId)}?${queryParams.toString()}`
  );
}

/**
 * Retrieves experimental results for a specific submission
 * @param submissionId - ID of the submission
 * @param page - Page number (1-based)
 * @param size - Number of items per page
 * @returns Promise resolving to paginated result data
 */
export async function getResultsBySubmission(
  submissionId: string,
  page: number = 1,
  size: number = 25
): Promise<ResultResponse> {
  const queryParams = new URLSearchParams();
  queryParams.append('page', page.toString());
  queryParams.append('size', size.toString());
  
  return get<ResultResponse>(
    `${API_ENDPOINTS.RESULTS.BY_SUBMISSION.replace('{submission_id}', submissionId)}?${queryParams.toString()}`
  );
}

/**
 * Updates the status of an experimental result
 * @param id - ID of the result to update
 * @param statusUpdate - Status update data
 * @returns Promise resolving to updated result
 */
export async function updateResultStatus(
  id: string,
  statusUpdate: ResultStatusUpdate
): Promise<Result> {
  return put<Result>(
    API_ENDPOINTS.RESULTS.UPDATE_STATUS.replace('{id}', id),
    statusUpdate
  );
}

/**
 * Processes a result and marks it as processed with quality control information
 * @param processRequest - Process request data
 * @returns Promise resolving to processed result
 */
export async function processResult(
  processRequest: ResultProcessRequest
): Promise<Result> {
  return post<Result>(
    `${API_ENDPOINTS.RESULTS.GET.replace('{id}', processRequest.result_id)}/process`,
    processRequest
  );
}

/**
 * Reviews a result and optionally applies it to molecules
 * @param reviewRequest - Review request data
 * @returns Promise resolving to reviewed result
 */
export async function reviewResult(
  reviewRequest: ResultReviewRequest
): Promise<Result> {
  return post<Result>(
    `${API_ENDPOINTS.RESULTS.GET.replace('{id}', reviewRequest.result_id)}/review`,
    reviewRequest
  );
}